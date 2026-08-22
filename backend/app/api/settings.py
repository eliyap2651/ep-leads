from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.database import get_db
from app.models.setting import Setting
from app.schemas.misc import SettingUpdate

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(require_admin)])


@router.get("")
async def list_settings(db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(Setting))
    return [{"key": s.key, "value": s.value, "description": s.description} for s in result.scalars().all()]


@router.put("")
async def upsert_setting(payload: SettingUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Setting).where(Setting.key == payload.key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = payload.value
    else:
        setting = Setting(key=payload.key, value=payload.value)
        db.add(setting)
    await db.commit()
    return {"key": payload.key, "value": payload.value}
