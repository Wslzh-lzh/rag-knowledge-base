from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import async_session_factory
from app.models.user import User


async def ensure_bootstrap_admin() -> None:
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.email == settings.bootstrap_admin_email))
        if result.scalar_one_or_none():
            return

        user = User(
            email=settings.bootstrap_admin_email,
            password_hash=hash_password(settings.bootstrap_admin_password),
            display_name="Admin",
            status="active",
            role="admin",
        )
        db.add(user)
        await db.commit()


def main() -> None:
    asyncio.run(ensure_bootstrap_admin())


if __name__ == "__main__":
    main()
