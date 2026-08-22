"""Deterministic duplicate-detection engine (spec section 16).

Rules, in priority order: tender_number match > domain match > phone match >
email match > exact-URL match > fuzzy company-name + city match.
No AI is used here - dedup must be fast, deterministic and explainable.
"""

import re
from difflib import SequenceMatcher
from urllib.parse import urlparse


def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    digits = re.sub(r"[^\d+]", "", phone)
    digits = digits.replace("+972", "0").replace("972", "0", 1) if digits.startswith(("+972", "972")) else digits
    return digits or None


def normalize_email(email: str | None) -> str | None:
    if not email:
        return None
    return email.strip().lower()


def extract_domain(url: str | None) -> str | None:
    if not url:
        return None
    try:
        netloc = urlparse(url if "//" in url else f"//{url}").netloc.lower()
        return netloc.removeprefix("www.") or None
    except ValueError:
        return None


def normalize_company_name(name: str | None) -> str | None:
    if not name:
        return None
    n = name.strip().lower()
    for junk in ["בע\"מ", "בעמ", "ltd", "llc", "inc", '"', "'", "-", "–"]:
        n = n.replace(junk, "")
    return re.sub(r"\s+", " ", n).strip() or None


def fuzzy_match(a: str | None, b: str | None, threshold: float = 0.86) -> bool:
    if not a or not b:
        return False
    return SequenceMatcher(None, a, b).ratio() >= threshold


def build_dedup_key(
    *,
    tender_number: str | None = None,
    domain_website: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    company_name: str | None = None,
    city: str | None = None,
) -> str | None:
    """Best available stable key, prioritized. Used as a fast-path index lookup;
    fuzzy company-name matching is applied separately as a fallback in the dedup service.
    """
    if tender_number:
        return f"tender:{tender_number.strip().lower()}"
    if domain_website:
        d = extract_domain(domain_website)
        if d:
            return f"domain:{d}"
    if phone:
        p = normalize_phone(phone)
        if p:
            return f"phone:{p}"
    if email:
        e = normalize_email(email)
        if e:
            return f"email:{e}"
    if company_name:
        n = normalize_company_name(company_name)
        if n:
            key = f"company:{n}"
            if city:
                key += f":{city.strip().lower()}"
            return key
    return None


def is_probable_duplicate(candidate: dict, existing: dict) -> bool:
    """candidate/existing: dicts with optional keys tender_number, domain_website,
    phone, email, company_name, city, source_url."""
    if candidate.get("tender_number") and existing.get("tender_number"):
        if candidate["tender_number"].strip().lower() == existing["tender_number"].strip().lower():
            return True
    if candidate.get("domain_website") and existing.get("domain_website"):
        if extract_domain(candidate["domain_website"]) == extract_domain(existing["domain_website"]):
            return True
    cp, ep = normalize_phone(candidate.get("phone")), normalize_phone(existing.get("phone"))
    if cp and ep and cp == ep:
        return True
    ce, ee = normalize_email(candidate.get("email")), normalize_email(existing.get("email"))
    if ce and ee and ce == ee:
        return True
    if candidate.get("source_url") and existing.get("source_url"):
        if candidate["source_url"].strip() == existing["source_url"].strip():
            return True
    cn = normalize_company_name(candidate.get("company_name"))
    en = normalize_company_name(existing.get("company_name"))
    if cn and en and fuzzy_match(cn, en):
        same_city = (candidate.get("city") or "").strip().lower() == (existing.get("city") or "").strip().lower()
        if same_city or not candidate.get("city") or not existing.get("city"):
            return True
    return False
