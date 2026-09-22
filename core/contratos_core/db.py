"""Engine and session factory. One place that knows how to reach Postgres."""
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base
from .settings import Settings


class Database:
    def __init__(self, settings: Settings, *, echo: bool = False) -> None:
        self._settings = settings
        self.engine: Engine = create_engine(
            settings.database_url,
            pool_size=settings.db_pool_max,
            max_overflow=0,
            pool_pre_ping=True,
            future=True,
            echo=echo,
        )
        self._session_factory = sessionmaker(bind=self.engine, expire_on_commit=False, future=True)

    def create_all(self) -> None:
        """Schema is owned by the ORM. Swap for Alembic once it needs to change in place."""
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self.engine.dispose()
