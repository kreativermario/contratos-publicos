"""Patterns worth a second look on one contract, stated as facts.

Every one of these is legal. None of them is a finding. What the reader sees is
never a category name ("fracionamento", "concentração"): it is the fact itself,
with its numbers, because "3 contratos iguais, todos abaixo de 20 000 EUR"
needs no glossary and "às fatias" needs a tooltip to mean anything at all.

So a flag travels as a key plus the numbers its sentence interpolates, and
`messages.ts` holds the sentence in each language. The API still ships no prose,
which is the rule; it just ships enough for the sentence to be specific.

Two kinds of rule live here. Most read one contract row and need nothing else.
The rest need to know something about the supplier across contracts, and those
read it from a `FlagContext` the repository fills once per page rather than once
per row.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from contratos_core import Settings

from .company import is_person_nif, legal_form_from_name, looks_like_person_name


@dataclass(slots=True)
class FlagContext:
    """What the row-level rules cannot see, looked up once for a whole page.

    Empty is a valid context and every rule that needs one is simply silent,
    so a caller that has not built one still gets the row-level flags.
    """
    #: supplier id -> first appearance anywhere in the record, at any buyer
    debut: dict[str, date] = field(default_factory=dict)
    #: supplier id -> (contracts with this buyer, of those, won uncontested)
    here: dict[str, tuple[int, int]] = field(default_factory=dict)
    #: NIFs the company register does not currently list as active
    inactive: set[str] = field(default_factory=set)
    #: contract id -> (contracts in its group, the ceiling they all sit under)
    sliced: dict[int, tuple[int, float]] = field(default_factory=dict)
    #: earliest signed date held at all, so a debut on day one is not "recent"
    dataset_start: date | None = None


def supplier_id(party: dict) -> str | None:
    """A supplier is a NIF, not a name.

    The record spells one firm several ways (EDP appears six times in Loures),
    so every count keyed on the name splits one company into several. Same
    `coalesce(nif, name)` the repository groups by; they must not drift.
    """
    return party.get("nif") or party.get("name") or None


def is_person(party: dict) -> bool:
    """A natural person behind a contract.

    Two routes, because the record only ever offers one of them. A published
    NIF settles it outright, but IMPIC omits the NIF of a natural person, so
    in practice the signal is a *missing* NIF plus a name that reads as a name.
    """
    nif = party.get("nif")
    if nif:
        return is_person_nif(nif)
    return looks_like_person_name(party.get("name"))


def near_limit(value, settings: Settings) -> float | None:
    """The statutory ceiling this contract sits just under, if any.

    Same rule the threshold_surf indicator uses municipality-wide, applied to
    one row so the reader can see which contract it was talking about. Landing
    under a ceiling is legal and often unremarkable. It is only worth a second
    look when it keeps happening.
    """
    if value is None:
        return None
    band = settings.threshold_surf_band
    for limit in settings.thresholds:
        if limit * (1 - band) <= float(value) <= limit:
            return limit
    return None


def _is_ajuste(row: dict) -> bool:
    return "ajuste direto" in (row.get("procedure") or "").lower()


def _months_between(earlier: date | None, later: date | None) -> int | None:
    if not earlier or not later or later < earlier:
        return None
    return max(0, round((later - earlier).days / 30.44))


def flags_for(row: dict, settings: Settings,
              ctx: FlagContext | None = None) -> list[dict]:
    """Every flag this contract earns, each with the numbers its sentence needs.

    Order is deliberate: what the reader most needs to see comes first, because
    the interface shows only the first few. A row wearing seven chips teaches
    nobody anything except to stop reading chips.
    """
    ctx = ctx or FlagContext()
    value = float(row.get("value") or 0)
    parties = row.get("parties") or []
    signed = row.get("signed_date")
    found: list[dict] = []

    # Several contracts to one firm for one kind of thing, each under a ceiling
    # the total clears. Every single one of them is legal on its own, which is
    # exactly why the group is the thing worth showing rather than the row.
    group = ctx.sliced.get(row.get("id"))
    if group:
        n, limit = group
        found.append({"key": "fatias", "data": {"n": n, "limit": limit}})

    # A ceiling six euros above the price is not an accusation, it is a
    # coincidence worth seeing, and the gap is what makes it legible.
    limit = row.get("near_limit")
    if limit:
        found.append({"key": "limite",
                      "data": {"limit": float(limit),
                               "gap": round(float(limit) - value, 2)}})

    # One person invoicing a câmara is legal and routine at small values, so
    # the amount is the whole of what makes it worth pointing at.
    if value >= settings.person_flag_min and any(is_person(p) for p in parties):
        found.append({"key": "pessoa", "data": {"value": value}})

    # A firm whose first appearance ANYWHERE in the public record is recent.
    # Not its founding date: no free source publishes that, and saying "abriu
    # há 4 meses" would be a claim this data cannot support. The sentence says
    # first public contract, because that is the fact we hold.
    debut_months = _recent_debut(parties, signed, settings, ctx)
    if debut_months is not None:
        found.append({"key": "estreante", "data": {"months": debut_months}})

    # Every contract this firm holds with this câmara came without competition.
    uncontested = _never_tendered(parties, settings, ctx)
    if uncontested:
        found.append({"key": "nunca_a_concurso", "data": {"n": uncontested}})

    # A tender nobody else entered. Not ajuste direto: there the law does not
    # ask for competition, so a single name says nothing at all.
    if row.get("n_bidders") == 1 and not _is_ajuste(row):
        found.append({"key": "sozinho", "data": {}})

    # The register does not list the firm as active. It reports status today,
    # never at signing, so the sentence has to be about today.
    if any(p.get("nif") in ctx.inactive for p in parties):
        found.append({"key": "fechada", "data": {}})

    # A company whose only member is one person, above the same amount that
    # makes a natural person worth pointing at.
    if value >= settings.person_flag_min and any(
            (legal_form_from_name(p.get("name")) or "").startswith("Unipessoal")
            for p in parties):
        found.append({"key": "unipessoal", "data": {"value": value}})

    # The law asks for a reason when competition is skipped. The field is blank.
    if (_is_ajuste(row) and value >= settings.person_flag_min
            and not (row.get("ad_justification") or "").strip()):
        found.append({"key": "sem_explicacao", "data": {}})

    return found


def _recent_debut(parties: list[dict], signed, settings: Settings,
                  ctx: FlagContext) -> int | None:
    """Months between a supplier's first ever contract and this one, when recent.

    Censored on purpose: a firm already present on the first day we hold cannot
    be judged new, so a debut inside `newcomer_days` of `dataset_start` says
    nothing about the firm and everything about how much history is loaded.
    """
    if not signed or not ctx.debut:
        return None
    window = settings.newcomer_days
    best = None
    for party in parties:
        seen = ctx.debut.get(supplier_id(party) or "")
        if not seen:
            continue
        if ctx.dataset_start and (seen - ctx.dataset_start).days < window:
            continue  # the record starts too late to tell a debut from a gap
        months = _months_between(seen, signed)
        if months is not None and (signed - seen).days <= window:
            best = months if best is None else min(best, months)
    return best


def _never_tendered(parties: list[dict], settings: Settings,
                    ctx: FlagContext) -> int | None:
    """How many contracts this firm holds here, when not one went to tender."""
    if not ctx.here:
        return None
    for party in parties:
        total, uncontested = ctx.here.get(supplier_id(party) or "", (0, 0))
        if total >= settings.never_tendered_min and total == uncontested:
            return total
    return None


def slice_groups(rows: list[dict], settings: Settings) -> dict[int, tuple[int, float]]:
    """Contracts that sit in a run of similar awards under one ceiling.

    Grouped in Python rather than SQL because the rule is a shape rather than a
    filter: same buyer, same firm, same kind of work, close together in time,
    each one under a ceiling the run as a whole clears. Expressing that as one
    statement makes it unreadable and untestable.

    **`rows` must be every contract those firms hold, not the page on screen.**
    Grouping the page alone made the flag depend on pagination and on the sort:
    three awards split across a page boundary were invisible, and the same
    contract showed the flag under one sort and not another. It never produced a
    false positive, since every condition holds regardless of which rows are in
    front of it, but a chip that comes and goes is worse than a conservative one.

    Each row carries id, signed_date, value, cpv and buyer_nif, plus either a
    `sid` (what the repository selects) or the parties to read one from.
    """
    buckets: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        signed, value = row.get("signed_date"), row.get("value")
        if not signed or value is None:
            continue
        # CPV division: the two leading digits, which is the same granularity
        # the sector table groups by. A finer key would split a run of near
        # identical jobs across codes that differ in their last digits.
        division = (row.get("cpv") or "")[:2]
        # The buyer is part of the key: one firm doing three small jobs for
        # three different câmaras is three ordinary jobs, not a split contract.
        buyer = str(row.get("buyer_nif") or "")
        sids = ([row["sid"]] if row.get("sid")
                else [supplier_id(p) for p in (row.get("parties") or [])])
        for sid in sids:
            if sid:
                buckets[(buyer, sid, division)].append(row)

    out: dict[int, tuple[int, float]] = {}
    for group in buckets.values():
        if len(group) < settings.slice_min_contracts:
            continue
        group = sorted(group, key=lambda r: r["signed_date"])
        for limit in settings.thresholds:
            run = [r for r in group if float(r["value"]) < limit]
            if len(run) < settings.slice_min_contracts:
                continue
            span = (run[-1]["signed_date"] - run[0]["signed_date"]).days
            if span > settings.slice_window_days:
                continue
            # Each one under the ceiling and the run as a whole over it. Without
            # the second half this fires on any firm with a few small jobs.
            if sum(float(r["value"]) for r in run) <= limit:
                continue
            for r in run:
                out[r["id"]] = (len(run), float(limit))
            break
    return out
