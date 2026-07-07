from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

_db_pool_size = 20
_db_max_overflow = 10
_db_pool_recycle = 3600


def _create_engine():
    engine_kwargs = {
        "future": True,
        "echo": False,
    }
    if settings.database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs.update(
            {
                "pool_size": _db_pool_size,
                "max_overflow": _db_max_overflow,
                "pool_recycle": _db_pool_recycle,
                "pool_pre_ping": True,
                "pool_use_lifo": True,
            }
        )
    return create_async_engine(settings.database_url, **engine_kwargs)


engine = _create_engine()

async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=False,
)
