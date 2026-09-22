"""Dependency wiring. One Database per process, one Session per request."""
from __future__ import annotations

from collections.abc import Generator

from contratos_core import Database, Settings, get_settings
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from .repositories import MunicipalityRepository
from .services.company import CompanyLookup
from .services.scoring import ScoringService


def get_db(request: Request) -> Database:
    return request.app.state.database


def get_session(database: Database = Depends(get_db)) -> Generator[Session, None, None]:
    with database.session() as session:
        yield session


def get_settings_dep() -> Settings:
    return get_settings()


def get_repo(session: Session = Depends(get_session)) -> MunicipalityRepository:
    return MunicipalityRepository(session)


def get_scoring(repo: MunicipalityRepository = Depends(get_repo),
                settings: Settings = Depends(get_settings_dep)) -> ScoringService:
    return ScoringService(repo=repo, settings=settings)


def get_company_lookup(session: Session = Depends(get_session),
                       settings: Settings = Depends(get_settings_dep)) -> CompanyLookup:
    return CompanyLookup(session=session, settings=settings)
