from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import *  # noqa: F401,F403
from app.db.session import engine
from app.models.common import Base
from app.models.user import User
from sqlalchemy.ext.asyncio import async_sessionmaker


async def init_database() -> None:
    work_dir = Path("work")
    work_dir.mkdir(exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created.")

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as db:
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.email == settings.bootstrap_admin_email))
        if not result.scalar_one_or_none():
            user = User(
                email=settings.bootstrap_admin_email,
                password_hash=hash_password(settings.bootstrap_admin_password),
                display_name="Admin",
                status="active",
                role="admin",
            )
            db.add(user)
            await db.commit()
            print(f"Bootstrap admin created: {settings.bootstrap_admin_email}")
        else:
            print(f"Bootstrap admin already exists: {settings.bootstrap_admin_email}")


def main() -> None:
    asyncio.run(init_database())


if __name__ == "__main__":
    main()
