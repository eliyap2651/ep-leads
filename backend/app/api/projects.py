from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.enums import ProjectStage
from app.models.project import Project

router = APIRouter(prefix="/projects", tags=["projects"], dependencies=[Depends(get_current_user)])


@router.get("")
async def list_projects(stage: ProjectStage | None = None, db: AsyncSession = Depends(get_db)) -> list[dict]:
    stmt = select(Project)
    if stage:
        stmt = stmt.where(Project.stage == stage)
    result = await db.execute(stmt.order_by(Project.created_at.desc()))
    return [
        {
            "id": str(p.id), "lead_id": str(p.lead_id) if p.lead_id else None, "name": p.name,
            "developer": p.developer, "contractor": p.contractor, "architect": p.architect,
            "project_manager": p.project_manager, "city": p.city,
            "stage": p.stage.value if p.stage else None, "unit_count": p.unit_count,
            "room_count": p.room_count, "source_url": p.source_url,
        }
        for p in result.scalars().all()
    ]
