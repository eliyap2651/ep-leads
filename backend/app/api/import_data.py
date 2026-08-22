import io

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_manager_or_admin
from app.database import get_db
from app.models.enums import RecordType
from app.services.adapters.base import RawFinding
from app.services.ingestion import ingest_finding

router = APIRouter(prefix="/import", tags=["import"], dependencies=[Depends(require_manager_or_admin)])

REQUIRED_COLUMNS = {"title"}


@router.post("/leads")
async def import_leads(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)) -> dict:
    """CSV/Excel import with dedup (spec section 29). Expected columns (Hebrew or
    English headers accepted): title/כותרת, city/עיר, estimated_value/שווי,
    source_url/קישור. Unknown columns are ignored; missing optional columns default
    to 'not found' rather than being invented."""
    content = await file.read()
    try:
        if file.filename and file.filename.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"לא ניתן לקרוא את הקובץ: {exc}") from exc

    column_map = {
        "title": "title", "כותרת": "title",
        "city": "city", "עיר": "city",
        "estimated_value": "estimated_value", "שווי": "estimated_value", "שווי משוער": "estimated_value",
        "source_url": "source_url", "קישור": "source_url", "url": "source_url",
    }
    df = df.rename(columns={c: column_map.get(str(c).strip().lower(), c) for c in df.columns})

    if "title" not in df.columns:
        raise HTTPException(status_code=400, detail="חסרה עמודת כותרת (title/כותרת) בקובץ")

    created, updated = 0, 0
    for _, row in df.iterrows():
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        finding = RawFinding(title=title, source_url=str(row.get("source_url") or "ייבוא ידני"))
        estimated_value = row.get("estimated_value")
        _, is_new = await ingest_finding(
            db,
            finding,
            source_name=f"ייבוא קובץ: {file.filename}",
            record_type=RecordType.TENDER,
            estimated_value=float(estimated_value) if pd.notna(estimated_value) else None,
            city=str(row.get("city")).strip() if pd.notna(row.get("city")) else None,
            source_confidence="medium",
        )
        created += 1 if is_new else 0
        updated += 0 if is_new else 1

    await db.commit()
    return {"created": created, "updated": updated, "total_rows": len(df)}
