from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

engine: AsyncEngine | None = None
async_session: async_sessionmaker[AsyncSession] | None = None


async def connect_to_db(database_url: str) -> None:
    global engine, async_session
    if engine is not None:
        return
    engine = create_async_engine(database_url, echo=False, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)


async def close_db_connection() -> None:
    global engine, async_session
    if engine:
        await engine.dispose()
    engine = None
    async_session = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if async_session is None:
        raise RuntimeError("Database session not initialized")
    session = async_session()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    else:
        await session.commit()
    finally:
        await session.close()

