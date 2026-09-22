"""One supplier's whole record, across every câmara loaded.

Separate from `/companies/{nif}`, which is the registry profile fetched from
outside. This one is the procurement side: what the firm actually won here.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from contratos_core import Settings

from ..deps import get_repo, get_settings_dep
from ..repositories import MunicipalityRepository
from ..schemas import ContractOut, SupplierDetail
from .municipalities import _flags, _near_limit

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("/{nif}", response_model=SupplierDetail)
def supplier(nif: str, repo: MunicipalityRepository = Depends(get_repo)):
    found = repo.supplier(nif)
    if not found:
        raise HTTPException(404, f"no contracts for supplier {nif}")
    return found


@router.get("/{nif}/contracts", response_model=list[ContractOut])
def supplier_contracts(nif: str, limit: int = Query(50, le=500), offset: int = 0,
                       q: str | None = None, year: int | None = None,
                       buyer: str | None = None, procedure: str | None = None,
                       sort: str = "signed_date", desc: bool = True,
                       repo: MunicipalityRepository = Depends(get_repo),
                       settings: Settings = Depends(get_settings_dep)):
    """Most recent first by default: reading one firm, the question is what it
    won lately."""
    rows = repo.supplier_contracts(nif, limit, offset, q=q, year=year, buyer=buyer,
                                   procedure=procedure, sort=sort, desc=desc)
    for row in rows:
        row["near_limit"] = _near_limit(row.get("value"), settings)
        row["flags"] = _flags(row, settings)
    return rows
