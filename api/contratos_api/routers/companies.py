"""Registry profile for a supplier, by NIF."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_company_lookup
from ..schemas import Company
from ..services.company import CompanyLookup

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/{nif}", response_model=Company)
def company(nif: str, lookup: CompanyLookup = Depends(get_company_lookup)):
    if not nif.isdigit() or len(nif) != 9:
        raise HTTPException(400, "NIF must be nine digits")
    found = lookup.get(nif)
    if not found:
        raise HTTPException(404, f"no registry profile for NIF {nif}")
    return found
