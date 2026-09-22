from __future__ import annotations

from datetime import date

from contratos_core import Settings
from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_repo, get_scoring, get_settings_dep
from ..repositories import MunicipalityRepository
from ..schemas import (ContractOut, MandateOut, MapCell, Municipality, Rival,
                       Score, Stats, Supplier)
from ..services.company import is_person_nif, looks_like_person_name
from ..services.scoring import ScoringService

router = APIRouter(prefix="/municipalities", tags=["municipalities"])


def _near_limit(value, settings: Settings) -> float | None:
    """The statutory ceiling this contract sits just under, if any.

    Same rule the threshold_surf indicator uses municipality-wide, applied to one
    row so the reader can see which contract it was talking about. Nothing here
    is an accusation: landing under a ceiling is legal and often unremarkable.
    It is only worth a second look when it keeps happening.
    """
    if value is None:
        return None
    band = settings.threshold_surf_band
    for limit in settings.thresholds:
        if limit * (1 - band) <= float(value) <= limit:
            return limit
    return None


def _is_person(party: dict) -> bool:
    """A natural person behind a contract.

    Two routes, because the record only ever offers one of them. A published
    NIF settles it outright, but IMPIC omits the NIF of a natural person, so
    every one that reaches us starts with a 5 or a 9. In practice the signal is
    a *missing* NIF plus a name that reads as a name.
    """
    nif = party.get("nif")
    if nif:
        return is_person_nif(nif)
    return looks_like_person_name(party.get("name"))


def _flags(row: dict, settings: Settings) -> list[str]:
    """Patterns worth a second look on a single contract row.

    Every one of these is legal. They are shapes that recur in the record, not
    findings: the interface names each one in words and says what it means, and
    a row can carry none, one or several.
    """
    found: list[str] = []

    if row.get("near_limit"):
        found.append("limite")

    # A natural person, read off the NIF, which is what the tax register keys
    # it on: 1 to 3 and 45 are people, 5 is a company, 6 a public body. The
    # first version read the *name* for the absence of a legal form and called
    # "TECNORÉM - Engenharia e Construções, S.A" a person, because "S.A"
    # without the trailing dot was missing from the table.
    #
    # One person invoicing a câmara is legal and routine at small values, so the
    # amount is what makes it worth pointing at.
    value = float(row.get("value") or 0)
    parties = row.get("parties") or []
    if value >= settings.person_flag_min and any(_is_person(p) for p in parties):
        found.append("pessoa")

    # A tender nobody else entered. Not ajuste direto: there the law does not ask
    # for competition, so a single name says nothing.
    procedure = (row.get("procedure") or "").lower()
    if row.get("n_bidders") == 1 and "ajuste direto" not in procedure:
        found.append("sozinho")

    return found


def resolve_nif(nif: str, settings: Settings) -> str:
    """'default' resolves to DEFAULT_MUNICIPALITY_NIF so the frontend hardcodes nothing."""
    if nif != "default":
        return nif
    if not settings.default_municipality_nif:
        raise HTTPException(400, "DEFAULT_MUNICIPALITY_NIF is not configured")
    return settings.default_municipality_nif


@router.get("", response_model=list[Municipality])
def list_municipalities(repo: MunicipalityRepository = Depends(get_repo)):
    return repo.list_all()


@router.get("/{nif}/score", response_model=Score)
def score(nif: str, year_from: int | None = None, year_to: int | None = None,
              date_from: date | None = None, date_to: date | None = None,
          repeat_min: int = Query(5, ge=2),
          scoring: ScoringService = Depends(get_scoring),
          repo: MunicipalityRepository = Depends(get_repo),
          settings: Settings = Depends(get_settings_dep)):
    nif = resolve_nif(nif, settings)
    result = scoring.score(nif, year_from, year_to, repeat_min, date_from, date_to)
    if not result:
        raise HTTPException(404, f"no contracts held for NIF {nif}")
    known = repo.get(nif)
    result["name"] = known["name"] if known else None
    return result


@router.get("/{nif}/mandates", response_model=list[MandateOut])
def mandates(nif: str,
             repo: MunicipalityRepository = Depends(get_repo),
             settings: Settings = Depends(get_settings_dep)):
    """Who held the presidency, term by term, with what was contracted under each.

    Deliberately not year-filtered: the point of the timeline is the whole run of
    terms, and narrowing it to the page's period would leave a single bar.
    """
    return repo.mandates(resolve_nif(nif, settings))


@router.get("/{nif}/suppliers", response_model=list[Supplier])
def suppliers(nif: str, limit: int = Query(100, le=1000), offset: int = 0,
              q: str | None = None, sort: str = "total", desc: bool = True,
              form: str | None = None,
              year_from: int | None = None, year_to: int | None = None,
              date_from: date | None = None, date_to: date | None = None,
              repo: MunicipalityRepository = Depends(get_repo),
              settings: Settings = Depends(get_settings_dep)):
    """Sorting and searching happen here, not in the browser: a câmara can have
    thousands of suppliers and the client only ever holds a page of them."""
    return repo.suppliers(resolve_nif(nif, settings), limit, year_from, year_to,
                          date_from, date_to, settings.newcomer_days, q=q, sort=sort, desc=desc,
                          offset=offset, form=form)


@router.get("/{nif}/stats", response_model=Stats)
def stats(nif: str, year_from: int | None = None, year_to: int | None = None,
              date_from: date | None = None, date_to: date | None = None,
          repo: MunicipalityRepository = Depends(get_repo),
          settings: Settings = Depends(get_settings_dep)):
    return repo.stats(resolve_nif(nif, settings), year_from, year_to, date_from, date_to)


@router.get("/{nif}/map", response_model=list[MapCell])
def municipality_map(nif: str, year_from: int | None = None, year_to: int | None = None,
              date_from: date | None = None, date_to: date | None = None,
                     repo: MunicipalityRepository = Depends(get_repo),
                     settings: Settings = Depends(get_settings_dep)):
    """Execution locations of this buyer's contracts, not the country's."""
    return repo.map_cells(resolve_nif(nif, settings), year_from, year_to, date_from, date_to)


@router.get("/{nif}/rivals", response_model=list[Rival])
def rivals(nif: str, limit: int = Query(200, le=2000),
           year_from: int | None = None, year_to: int | None = None,
              date_from: date | None = None, date_to: date | None = None,
           repo: MunicipalityRepository = Depends(get_repo),
           settings: Settings = Depends(get_settings_dep)):
    return repo.rivals(resolve_nif(nif, settings), limit, year_from, year_to, date_from, date_to)


@router.get("/{nif}/contracts", response_model=list[ContractOut])
def contracts(nif: str, q: str | None = None, procedure: str | None = None,
              supplier: str | None = None, min_value: float | None = None,
              year: int | None = None, municipality: str | None = None,
              sector: str | None = None, form: str | None = None,
              sort: str = "value", desc: bool = True,
              year_from: int | None = None, year_to: int | None = None,
              date_from: date | None = None, date_to: date | None = None,
              limit: int = Query(50, le=500), offset: int = 0,
              repo: MunicipalityRepository = Depends(get_repo),
              settings: Settings = Depends(get_settings_dep)):
    rows = repo.contracts(resolve_nif(nif, settings), q=q, procedure=procedure,
                          supplier=supplier, min_value=min_value, year=year,
                          municipality=municipality, sector=sector, form=form,
                          sort=sort, desc=desc,
                          year_from=year_from, year_to=year_to,
                          date_from=date_from, date_to=date_to,
                          limit=limit, offset=offset)
    for row in rows:
        row["suppliers"] = row.get("suppliers") or []
        row["near_limit"] = _near_limit(row.get("value"), settings)
        row["flags"] = _flags(row, settings)
    return rows
