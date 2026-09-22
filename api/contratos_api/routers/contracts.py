"""The full record for a single contract."""
from __future__ import annotations

from contratos_core import Settings
from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_repo, get_settings_dep
from ..repositories import MunicipalityRepository
from ..schemas import ContractDetail
from .municipalities import _near_limit

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("/{contract_id}", response_model=ContractDetail)
def contract(contract_id: int,
             repo: MunicipalityRepository = Depends(get_repo),
             settings: Settings = Depends(get_settings_dep)):
    found = repo.contract(contract_id)
    if not found:
        raise HTTPException(404, f"no contract {contract_id}")
    found["near_limit"] = _near_limit(found.get("value"), settings)
    return found
