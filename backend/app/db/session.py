from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

_db_pool_size = 20
_db_max_overflow = 10
_db_pool_recycle = 3600

engine = create_async_engine(
    settings.database_url,
    future=True,
    echo=False,
    pool_size=_db_pool_size,
    max_overflow=_db_max_overflow,
    pool_recycle=_db_pool_recycle,
    pool_pre_ping=True,
    pool_use_lifo=True,
)

async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=False,
)
