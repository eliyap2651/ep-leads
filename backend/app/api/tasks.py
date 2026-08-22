import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.activity import FollowUpTask
from app.models.enums import TaskStatus
from app.models.user import User
from app.schemas.misc import TaskCreateSchema, TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    mine_only: bool = True,
    include_done: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FollowUpTask]:
    stmt = select(FollowUpTask)
    if mine_only:
        stmt = stmt.where(FollowUpTask.assigned_to_id == current_user.id)
    if not include_done:
        stmt = stmt.where(FollowUpTask.status == TaskStatus.OPEN)
    stmt = stmt.order_by(FollowUpTask.due_date.asc().nulls_last())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=TaskOut)
async def create_task(
    payload: TaskCreateSchema, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> FollowUpTask:
    task = FollowUpTask(
        lead_id=payload.lead_id,
        title=payload.title,
        due_date=payload.due_date,
        assigned_to_id=payload.assigned_to_id or current_user.id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/{task_id}/complete", response_model=TaskOut)
async def complete_task(task_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> FollowUpTask:
    result = await db.execute(select(FollowUpTask).where(FollowUpTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="משימה לא נמצאה")
    task.status = TaskStatus.DONE
    task.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(task)
    return task
