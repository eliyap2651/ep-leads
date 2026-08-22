"""Celery background tasks (spec section 35).

Each task is a thin sync wrapper (`run_async`) around an async implementation so
the same async DB/service layer used by the FastAPI app can be reused without
duplication. Every task that touches an external source is wrapped so that one
failing source/document never blocks the others (spec section 37) - errors are
caught, logged to ScanRun/Source, and processing continues.
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.core.logging import log
from app.models.alert import Alert
from app.models.contact import Contact
from app.models.document import Document
from app.models.enums import (
    AlertChannel,
    AlertType,
    Confidence,
    RecordType,
    ScanFrequency,
    ScanRunStatus,
    SourceStatus,
)
from app.models.lead import Lead
from app.models.links import LeadContact
from app.models.scan_run import ChangeHistory, ScanRun
from app.models.search_query import SearchQuery
from app.models.source import Source
from app.models.tender import Tender
from app.models.user import User
from app.services.adapters import get_adapter_for_source
from app.services.adapters.search_provider import SearchProviderUnavailableError, get_search_provider
from app.services.ai_engine import AIEngine, AIUnavailableError
from app.services.contact_extraction import extract_emails, extract_phones, looks_like_business_whatsapp
from app.services.ingestion import ingest_finding
from app.services.notifications import CHANNEL_SENDERS
from app.services.pdf_parser import extract_text_from_pdf_bytes
from app.services.scoring import ScoreInput, days_until, score_lead
from app.workers.celery_app import celery_app

settings = get_settings()

_worker_engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
_WorkerSession = async_sessionmaker(bind=_worker_engine, expire_on_commit=False)

FREQUENCY_TIMEDELTA = {
    ScanFrequency.HOURLY: timedelta(hours=1),
    ScanFrequency.EVERY_3H: timedelta(hours=3),
    ScanFrequency.EVERY_6H: timedelta(hours=6),
    ScanFrequency.EVERY_12H: timedelta(hours=12),
    ScanFrequency.DAILY: timedelta(days=1),
    ScanFrequency.WEEKLY: timedelta(weeks=1),
}


def run_async(coro):
    return asyncio.run(coro)


async def _crawl_one_source(db: AsyncSession, source: Source) -> None:
    run = ScanRun(source_id=source.id, task_name="crawl_source", status=ScanRunStatus.RUNNING,
                   started_at=datetime.now(timezone.utc))
    db.add(run)
    await db.flush()
    try:
        adapter = get_adapter_for_source(source.source_type, source.url, json.loads(source.config_json) if source.config_json else None)
        findings = await adapter.fetch()
        new_count = 0
        for finding in findings:
            _, is_new = await ingest_finding(db, finding, source_id=source.id, source_name=source.name)
            new_count += 1 if is_new else 0
        source.status = SourceStatus.OK
        source.last_scan_at = datetime.now(timezone.utc)
        source.last_success_at = datetime.now(timezone.utc)
        source.last_error = None
        source.result_count = len(findings)
        run.status = ScanRunStatus.SUCCESS
        run.items_found = len(findings)
        run.new_leads = new_count
    except Exception as exc:  # noqa: BLE001
        source.status = SourceStatus.ERROR
        source.last_scan_at = datetime.now(timezone.utc)
        source.last_error = str(exc)
        run.status = ScanRunStatus.FAILED
        run.error = str(exc)
        log.error("crawl_source_failed", source=source.name, error=str(exc))
    finally:
        run.finished_at = datetime.now(timezone.utc)
        await db.commit()


@celery_app.task(name="app.workers.tasks.crawl_source")
def crawl_source(source_id: str) -> None:
    async def _run():
        async with _WorkerSession() as db:
            result = await db.execute(select(Source).where(Source.id == source_id))
            source = result.scalar_one_or_none()
            if source:
                await _crawl_one_source(db, source)

    run_async(_run())


@celery_app.task(name="app.workers.tasks.run_scheduled_scans")
def run_scheduled_scans() -> None:
    """Beat-triggered: scans every active source whose own scan_frequency interval
    has elapsed, and runs every active search query. Respects per-source cadence
    (spec section 19) instead of blindly scanning everything every hour."""

    async def _run():
        now = datetime.now(timezone.utc)
        async with _WorkerSession() as db:
            result = await db.execute(select(Source).where(Source.is_active == True))  # noqa: E712
            for source in result.scalars().all():
                if source.scan_frequency == ScanFrequency.NONE:
                    continue
                interval = FREQUENCY_TIMEDELTA.get(source.scan_frequency, timedelta(days=1))
                if source.last_scan_at and (now - source.last_scan_at) < interval:
                    continue
                await _crawl_one_source(db, source)

            try:
                provider = get_search_provider()
                q_result = await db.execute(select(SearchQuery).where(SearchQuery.is_active == True))  # noqa: E712
                for query in q_result.scalars().all():
                    findings = await provider.search(query.text)
                    for finding in findings:
                        await ingest_finding(db, finding, source_name=f"חיפוש: {query.text}")
                    query.last_run_at = now
                    query.result_count = len(findings)
                await db.commit()
            except SearchProviderUnavailableError as exc:
                log.warning("search_provider_unavailable", error=str(exc))

    run_async(_run())


@celery_app.task(name="app.workers.tasks.search_web")
def search_web(query_id: str) -> None:
    async def _run():
        async with _WorkerSession() as db:
            result = await db.execute(select(SearchQuery).where(SearchQuery.id == query_id))
            query = result.scalar_one_or_none()
            if not query:
                return
            try:
                provider = get_search_provider()
                findings = await provider.search(query.text)
                for finding in findings:
                    await ingest_finding(db, finding, source_name=f"חיפוש: {query.text}")
                query.last_run_at = datetime.now(timezone.utc)
                query.result_count = len(findings)
                await db.commit()
            except SearchProviderUnavailableError as exc:
                log.warning("search_web_failed", query=query.text, error=str(exc))

    run_async(_run())


@celery_app.task(name="app.workers.tasks.parse_pdf")
def parse_pdf(document_id: str) -> None:
    import httpx

    async def _run():
        async with _WorkerSession() as db:
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()
            if not document or not document.original_url:
                return
            try:
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    resp = await client.get(document.original_url, timeout=60)
                    resp.raise_for_status()
                extracted = extract_text_from_pdf_bytes(resp.content)
                document.extracted_text = extracted.text
                document.page_count = extracted.page_count
                document.ocr_used = extracted.ocr_used
                document.downloaded_at = datetime.now(timezone.utc)
                await db.commit()
            except Exception as exc:  # noqa: BLE001
                log.error("parse_pdf_failed", document_id=document_id, error=str(exc))

    run_async(_run())


@celery_app.task(name="app.workers.tasks.extract_contacts")
def extract_contacts(document_id: str) -> None:
    async def _run():
        async with _WorkerSession() as db:
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()
            if not document or not document.extracted_text or not document.lead_id:
                return
            phones = extract_phones(document.extracted_text)
            emails = extract_emails(document.extracted_text)
            for phone in phones:
                contact = Contact(
                    phone=phone,
                    whatsapp=phone if looks_like_business_whatsapp(phone) else None,
                    source_url=document.original_url,
                    confidence=Confidence.MEDIUM,
                )
                db.add(contact)
                await db.flush()
                db.add(LeadContact(lead_id=document.lead_id, contact_id=contact.id))
            for email in emails:
                contact = Contact(email=email, source_url=document.original_url, confidence=Confidence.MEDIUM)
                db.add(contact)
                await db.flush()
                db.add(LeadContact(lead_id=document.lead_id, contact_id=contact.id))
            await db.commit()

    run_async(_run())


@celery_app.task(name="app.workers.tasks.analyze_with_ai")
def analyze_with_ai(document_id: str) -> None:
    async def _run():
        async with _WorkerSession() as db:
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()
            if not document or not document.extracted_text:
                return
            try:
                engine = AIEngine()
                analysis = engine.analyze_tender_document(document.extracted_text)
            except AIUnavailableError as exc:
                log.warning("analyze_with_ai_unavailable", error=str(exc))
                return

            document.analyzed_at = datetime.now(timezone.utc)
            if document.lead_id:
                t_result = await db.execute(select(Tender).where(Tender.lead_id == document.lead_id))
                tender = t_result.scalar_one_or_none()
                if not tender:
                    tender = Tender(lead_id=document.lead_id)
                    db.add(tender)

                def clean(v):
                    return None if v in (None, "", "לא נמצא") else v

                tender.title = clean(analysis.get("tender_title"))
                tender.tender_number = clean(analysis.get("tender_number"))
                tender.publishing_body = clean(analysis.get("publishing_body"))
                tender.field = clean(analysis.get("field"))
                tender.location = clean(analysis.get("location"))
                tender.contact_name = clean(analysis.get("contact_name"))
                tender.contact_phone = clean(analysis.get("contact_phone"))
                tender.contact_email = clean(analysis.get("contact_email"))
                tender.eligibility_conditions = clean(analysis.get("eligibility_conditions"))
                tender.guarantees = clean(analysis.get("guarantees"))
                tender.quantities = clean(analysis.get("quantities"))
                tender.furniture_items = clean(analysis.get("furniture_items"))
                tender.specifications = clean(analysis.get("specifications"))
                tender.installation_requirements = clean(analysis.get("installation_requirements"))
                tender.delivery_requirements = clean(analysis.get("delivery_requirements"))
                tender.standards = clean(analysis.get("standards"))
                tender.required_documents = clean(analysis.get("required_documents"))
                tender.classification_required = clean(analysis.get("classification_required"))
                tender.competition_level = clean(analysis.get("competition_level_estimate"))
                tender.document_id = document.id
                tender.ai_analysis_raw = json.dumps(analysis, ensure_ascii=False)
            await db.commit()

    run_async(_run())


@celery_app.task(name="app.workers.tasks.calculate_score")
def calculate_score(lead_id: str) -> None:
    async def _run():
        async with _WorkerSession() as db:
            result = await db.execute(select(Lead).where(Lead.id == lead_id))
            lead = result.scalar_one_or_none()
            if not lead:
                return
            contacts_result = await db.execute(
                select(Contact).join(LeadContact, LeadContact.contact_id == Contact.id).where(LeadContact.lead_id == lead.id)
            )
            contacts = contacts_result.scalars().all()
            today = datetime.now(timezone.utc).date()
            score_input = ScoreInput(
                record_type=lead.record_type,
                domain=lead.domain,
                estimated_value=float(lead.estimated_value) if lead.estimated_value else None,
                is_tender=lead.record_type == RecordType.TENDER,
                days_until_deadline=days_until(lead.deadline, today),
                has_contact_name=any(c.name for c in contacts),
                has_phone=any(c.phone for c in contacts),
                has_email=any(c.email for c in contacts),
                is_new_project=lead.record_type == RecordType.PROJECT,
            )
            result_score = score_lead(score_input)
            lead.score = result_score.total
            lead.tier = result_score.tier
            lead.score_breakdown_json = json.dumps(result_score.breakdown, ensure_ascii=False)
            await db.commit()

            if result_score.total >= settings.LEAD_SCORE_THRESHOLD_HOT:
                await _create_alert_for_lead(db, lead, AlertType.HIGH_SCORE, f"ליד חם: {lead.title}", f"הליד קיבל ציון {result_score.total}")

    run_async(_run())


async def _create_alert_for_lead(db: AsyncSession, lead: Lead, alert_type: AlertType, title: str, body: str) -> None:
    users_result = await db.execute(select(User).where(User.is_active == True))  # noqa: E712
    for user in users_result.scalars().all():
        db.add(Alert(lead_id=lead.id, user_id=user.id, alert_type=alert_type, channel=AlertChannel.IN_APP,
                      title=title, body=body))
        if user.notify_email:
            db.add(Alert(lead_id=lead.id, user_id=user.id, alert_type=alert_type, channel=AlertChannel.EMAIL,
                          title=title, body=body))
    await db.commit()


@celery_app.task(name="app.workers.tasks.send_alert")
def send_alert(alert_id: str) -> None:
    async def _run():
        async with _WorkerSession() as db:
            result = await db.execute(select(Alert).where(Alert.id == alert_id))
            alert = result.scalar_one_or_none()
            if not alert or alert.channel == AlertChannel.IN_APP:
                return
            user_result = await db.execute(select(User).where(User.id == alert.user_id))
            user = user_result.scalar_one_or_none()
            if not user:
                return
            sender = CHANNEL_SENDERS.get(alert.channel)
            if not sender:
                return
            target = user.email if alert.channel == AlertChannel.EMAIL else (user.phone or "")
            success, error = await sender(alert, target)
            alert.sent_at = datetime.now(timezone.utc) if success else None
            alert.error = error
            await db.commit()

    run_async(_run())


@celery_app.task(name="app.workers.tasks.check_closing_tenders")
def check_closing_tenders() -> None:
    async def _run():
        async with _WorkerSession() as db:
            today = datetime.now(timezone.utc).date()
            for offset in (0, 1, 3, 7):
                target = today + timedelta(days=offset)
                result = await db.execute(
                    select(Tender).where(Tender.is_open == True, Tender.submission_deadline == target)  # noqa: E712
                )
                for tender in result.scalars().all():
                    if not tender.lead_id:
                        continue
                    lead_result = await db.execute(select(Lead).where(Lead.id == tender.lead_id))
                    lead = lead_result.scalar_one_or_none()
                    if lead:
                        await _create_alert_for_lead(
                            db, lead, AlertType.TENDER_CLOSING_SOON,
                            f"מכרז נסגר בעוד {offset} ימים: {lead.title}",
                            f"מועד הגשה: {tender.submission_deadline}",
                        )

    run_async(_run())


@celery_app.task(name="app.workers.tasks.check_changes_all")
def check_changes_all() -> None:
    """Re-checks each open tender's source URL for a changed deadline (spec section
    18) - a lightweight content-hash-free diff: re-run the AI/adapter extraction is
    expensive, so this pass only flags leads not verified recently for manual re-scan
    priority via is_stale, which the source_manager crawl loop will pick up next run."""

    async def _run():
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        async with _WorkerSession() as db:
            result = await db.execute(select(Lead).where(Lead.last_verified_at < cutoff, Lead.is_stale == False))  # noqa: E712
            for lead in result.scalars().all():
                lead.is_stale = True
            await db.commit()

    run_async(_run())
