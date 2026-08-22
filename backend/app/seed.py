"""Creates exactly one Admin user if none exists yet (spec section 50: no fake
leads/companies/tenders/contacts are ever seeded - the DB starts genuinely empty
of business data and only fills up from real scans/imports)."""

import asyncio
import os
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.database import AsyncSessionLocal
from app.models.enums import UserRole
from app.models.user import User


async def main() -> None:
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    full_name = os.environ.get("ADMIN_NAME", "מנהל מערכת")

    if not email or not password:
        print("ADMIN_EMAIL / ADMIN_PASSWORD environment variables are required to seed the admin user.")
        sys.exit(1)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.role == UserRole.ADMIN))
        if result.scalar_one_or_none():
            print("Admin user already exists - skipping.")
            return
        user = User(
            email=email.lower(), hashed_password=hash_password(password), full_name=full_name, role=UserRole.ADMIN
        )
        db.add(user)
        await db.commit()
        print(f"Created admin user: {email}")


if __name__ == "__main__":
    asyncio.run(main())
