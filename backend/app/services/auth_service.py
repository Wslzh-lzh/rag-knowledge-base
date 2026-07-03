from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.user import User


class AuthService:
    async def register(self, db: AsyncSession, *, email: str, password: str, display_name: str | None = None) -> User:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise ValueError("email_exists")
        user = User(email=email, password_hash=hash_password(password), display_name=display_name)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user and verify_password(password, user.password_hash):
            return user
        return None

    def create_tokens(self, user_id: str) -> tuple[str, str]:
        return create_access_token(user_id), create_refresh_token(user_id)

    def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        from app.core.security import decode_token

        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("invalid_token_type")
        subject = payload.get("sub")
        if not subject:
            raise ValueError("invalid_token")
        return self.create_tokens(subject)
