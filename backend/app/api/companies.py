from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.database import get_db
from app.models.company import Company

router = APIRouter(prefix="/companies", tags=["companies"], dependencies=[Depends(get_current_user)])


@router.get("")
async def list_companies(db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(Company).order_by(Company.name).limit(500))
    return [
        {
            "id": str(c.id), "name": c.name, "city": c.city, "category": c.category.value if c.category else None,
            "phone": c.phone, "email": c.email, "website": c.website,
        }
        for c in result.scalars().all()
    ]
