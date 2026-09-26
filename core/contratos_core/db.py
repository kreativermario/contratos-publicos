"""Engine and session factory. One place that knows how to reach Postgres."""
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Column, Engine, Table, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateColumn, CreateIndex

from .models import Base
from .settings import Settings


def missing_columns(table: Table, have: set[str]) -> list[Column]:
    """Columns the ORM declares that the live table does not carry."""
    return [c for c in table.columns if c.name not in have]


def unaddable(column: Column) -> str | None:
    """Why this column cannot simply be appended to a table with rows in it.

    Postgres has to put *something* in the new column for every existing row.
    NOT NULL with no default leaves it nothing to put, and a primary key cannot
    be introduced after the fact at all. Both mean the change is a real
    migration, not a column add, so say so by name instead of letting Postgres
    fail with its own wording halfway through a deploy.
    """
    if column.primary_key:
        return "it is a primary key"
    if not column.nullable and column.server_default is None and column.default is None:
        return "it is NOT NULL with no server default, so existing rows have no value"
    return None


def missing_indexes(table: Table, have: set[str]) -> list:
    """Indexes the ORM declares that the live table does not carry.

    The mirror of `missing_columns`, and needed for the same reason:
    `create_all` builds a table's indexes when it builds the table, and does
    nothing at all for an index added to a table that already exists.
    """
    return [i for i in table.indexes if i.name not in have]


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
        """Bring the database up to the ORM: missing tables, then missing columns.

        `create_all` on its own creates missing *tables* and silently ignores a
        table that exists but has drifted, which is how a new column reached
        production as a missing column and 500'd every request that read it.
        The deploy runs this as a one-shot the API waits on, so this is the
        right place for it and there is no server to log into.

        Additive only, deliberately. It adds nullable columns and refuses
        anything else rather than guessing: see `unaddable` below. Indexes are
        additive by nature, so they need no such guard.
        """
        Base.metadata.create_all(self.engine)
        self.add_missing_columns()
        self.add_missing_indexes()

    def add_missing_columns(self) -> None:
        """ALTER TABLE ADD COLUMN for every column the ORM has and the database
        does not. Idempotent, so every deploy runs it and almost every deploy
        finds nothing to do."""
        inspector = inspect(self.engine)
        present = set(inspector.get_table_names())
        for table in Base.metadata.sorted_tables:
            if table.name not in present:
                continue  # create_all just made it, with every column
            have = {c["name"] for c in inspector.get_columns(table.name)}
            for column in missing_columns(table, have):
                why = unaddable(column)
                if why:
                    raise RuntimeError(
                        f"{table.name}.{column.name} cannot be added in place: {why}. "
                        "This is the change that needs Alembic rather than this."
                    )
                ddl = CreateColumn(column).compile(self.engine).string
                with self.engine.begin() as conn:
                    conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN {ddl}'))

    def add_missing_indexes(self) -> None:
        """CREATE INDEX for every index the ORM declares and the database lacks.

        Idempotent, like `add_missing_columns`, so every deploy runs it and
        almost every deploy finds nothing to do.

        Not CONCURRENTLY, deliberately. CONCURRENTLY cannot run inside a
        transaction and leaves an INVALID index behind when it fails, which is
        a worse thing to discover on a box with no shell. This runs in the
        `migrate` one-shot that the API waits on, so there is no traffic to
        protect from the lock: the cost is that the first deploy introducing an
        index on a large table takes minutes, which is why the deploy's health
        gate is generous.
        """
        inspector = inspect(self.engine)
        present = set(inspector.get_table_names())
        for table in Base.metadata.sorted_tables:
            if table.name not in present:
                continue  # create_all just made it, with every index
            have = {i["name"] for i in inspector.get_indexes(table.name)}
            for index in missing_indexes(table, have):
                with self.engine.begin() as conn:
                    conn.execute(CreateIndex(index, if_not_exists=True))

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
