"""Comparisons across municípios: by district, and by the party in charge.

Everything here is split at the 2017 Código dos Contratos Públicos revision.
Pooling across it would mostly measure which parties held more câmaras before
the law tightened, not how any of them governed.

None of this claims causation. A municipal procurement index tracks how a câmara
buys, which is driven by its size, its in-house capacity and its local market at
least as much as by who holds the presidency.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import get_repo
from ..repositories import MunicipalityRepository
from ..schemas import DistrictRow, MandateMapRow, PartyRow

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("/parties", response_model=list[PartyRow])
def parties(repo: MunicipalityRepository = Depends(get_repo)):
    return repo.party_ranking()


@router.get("/districts", response_model=list[DistrictRow])
def districts(repo: MunicipalityRepository = Depends(get_repo)):
    return repo.district_ranking()


@router.get("/map", response_model=list[MandateMapRow])
def mandate_map(year: int | None = None,
                repo: MunicipalityRepository = Depends(get_repo)):
    """The political map: who holds each câmara after a given election.

    Defaults to the most recent one. Covers every concelho, including those with
    no contracts loaded, because the election data does.
    """
    return repo.mandate_map(year)


@router.get("/elections", response_model=list[int])
def elections(repo: MunicipalityRepository = Depends(get_repo)):
    return repo.election_years()
