from __future__ import annotations

from contratos_core import Contract, Settings
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..deps import get_repo, get_session, get_settings_dep
from ..repositories import MunicipalityRepository
from ..schemas import Config, MapCell
from ..services.company import LEGAL_FORMS

router = APIRouter(tags=["meta"])

# Health sits outside the version prefix on purpose: the container healthcheck
# is orchestration, not API surface, and must not move when v2 arrives.
health_router = APIRouter(tags=["meta"], include_in_schema=False)


@health_router.get("/health")
def health(session: Session = Depends(get_session)):
    row = session.execute(
        select(func.count(Contract.id), func.max(Contract.signed_date))
    ).one()
    return {"ok": True, "contracts": row[0], "latest": row[1]}


@router.get("/config", response_model=Config)
def config(repo: MunicipalityRepository = Depends(get_repo),
           settings: Settings = Depends(get_settings_dep)):
    """Runtime config so the frontend never bakes in a NIF."""
    default = repo.get(settings.default_municipality_nif) if settings.default_municipality_nif else None
    return {
        "default": default,
        "cache_seconds": settings.cache_seconds,
        # The ceilings the indicators are measured against. Served rather than
        # written into the page: they are statutory and get amended, and an
        # explainer that quotes a different number from the one the index used
        # is worse than no explainer.
        "limits": {
            "ajuste_direto_servicos": settings.ad_limit_services,
            "ajuste_direto_obras": settings.ad_limit_works,
            "consulta_previa": settings.consulta_previa_limit,
            "banda_limite": settings.threshold_surf_band,
            "dias_estreante": settings.newcomer_days,
        },
        # The forms a firm name can be read as. Served so the filter in the UI
        # offers exactly what the query can match, and nothing else.
        "legal_forms": list(LEGAL_FORMS),
    }


@router.get("/map", response_model=list[MapCell])
def map_data(year_from: int | None = None, year_to: int | None = None,
             repo: MunicipalityRepository = Depends(get_repo)):
    return repo.map_cells(None, year_from, year_to)
