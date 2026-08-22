import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_manager_or_admin
from app.database import get_db
from app.models.search_query import SearchQuery
from app.schemas.misc import SearchQueryCreate, SearchQueryOut

router = APIRouter(prefix="/search-queries", tags=["search-queries"], dependencies=[Depends(require_manager_or_admin)])


@router.get("", response_model=list[SearchQueryOut])
async def list_queries(db: AsyncSession = Depends(get_db)) -> list[SearchQuery]:
    result = await db.execute(select(SearchQuery).order_by(SearchQuery.text))
    return list(result.scalars().all())


@router.post("", response_model=SearchQueryOut)
async def create_query(payload: SearchQueryCreate, db: AsyncSession = Depends(get_db)) -> SearchQuery:
    query = SearchQuery(**payload.model_dump())
    db.add(query)
    await db.commit()
    await db.refresh(query)
    return query


@router.delete("/{query_id}")
async def delete_query(query_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(SearchQuery).where(SearchQuery.id == query_id))
    query = result.scalar_one_or_none()
    if not query:
        raise HTTPException(status_code=404, detail="שאילתה לא נמצאה")
    await db.delete(query)
    await db.commit()
    return {"status": "deleted"}
