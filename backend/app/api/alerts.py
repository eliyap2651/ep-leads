import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.misc import AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertOut])
async def list_alerts(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Alert]:
    stmt = select(Alert).where(Alert.user_id == current_user.id).order_by(Alert.created_at.desc()).limit(200)
    if unread_only:
        stmt = stmt.where(Alert.is_read == False)  # noqa: E712
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/{alert_id}/read")
async def mark_read(alert_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="התראה לא נמצאה")
    alert.is_read = True
    await db.commit()
    return {"status": "ok"}
