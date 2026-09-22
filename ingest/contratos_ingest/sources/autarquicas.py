"""Who held each câmara's presidency, from the autárquicas results.

Source: the static JSON the SGMAI results sites ship for their own front ends,
at eleicoes.mai.gov.pt. There is no documented API and no versioning, so this
can break without notice; that is why the result is stored rather than fetched
live, and why every parser here fails loudly instead of guessing.

Three site generations, three shapes, one output:

  2009, 2013  jQuery sites, candidates listed per district, no "elected" filter
  2017        same, but with an ELECTED-TRUE variant
  2021        Angular, lower-case paths, `-1-true` suffix for elected
  2025        Angular 17, `key=value` paths, an {isSuccess, data} envelope, and
              districts nested inside the payload rather than fetched per district

These are the **provisional** count (escrutínio provisório). The legally official
record is the CNE Mapa Oficial, published in Diário da República as a PDF. The
UI has to say which one it is showing.
"""
from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date

from contratos_core import (DISTRICT_PREFIXES, REGION_PREFIXES, canonical_party,
                             clean_person_name, dico_for)

from ..http import HttpClient

log = logging.getLogger(__name__)

BASE = "https://www.eleicoes.mai.gov.pt"

# Territory keys to fetch, as DD in LOCAL-DD0000. The 18 mainland districts come
# from the concelho table rather than a second list that could drift from it.
#
# The archipelagos are the catch: DICO splits them per island (31, 32, 41..49)
# but the election sites publish them as one region each, LOCAL-300000 and
# LOCAL-400000. Fetching per island 404s, which is how 30 municípios went
# quietly missing on the first run.
DISTRICT_CODES = DISTRICT_PREFIXES + REGION_PREFIXES


@dataclass(frozen=True)
class Election:
    year: int
    # Only 2021 and 2025 are sourced from the sites themselves (the 2025 payload
    # names its own date and its predecessor's). The older three are the
    # published polling days and are NOT verified in-tool. An error of a few days
    # only misfiles contracts signed inside the handover fortnight.
    day: date
    generation: str  # "a" | "b" | "c"
    verified: bool


ELECTIONS = (
    Election(2009, date(2009, 10, 11), "a", False),
    Election(2013, date(2013, 9, 29), "a", False),
    Election(2017, date(2017, 10, 1), "a", False),
    Election(2021, date(2021, 9, 26), "b", True),
    Election(2025, date(2025, 10, 12), "c", True),
)


@dataclass(frozen=True)
class MandateRecord:
    dico: str
    election_date: date
    term_start: date
    term_end: date | None
    party: str
    coalition: bool
    citizens_group: bool
    president: str | None
    mandates: int | None


class AutarquicasSource:
    """Yields one MandateRecord per município per election."""

    def __init__(self, client: HttpClient | None = None) -> None:
        self.client = client or HttpClient()

    def records(self) -> Iterator[MandateRecord]:
        # A mandate runs until the next election, so each one needs its successor.
        for election, nxt in zip(ELECTIONS, ELECTIONS[1:] + (None,)):
            end = nxt.day if nxt else None
            seen = 0
            for rec in self._for_election(election, end):
                seen += 1
                yield rec
            log.info("autárquicas %s: %s municípios", election.year, seen)
            if seen < 250:
                # 308 is the whole country; anything far below it means the site
                # changed shape and the parser is silently dropping rows.
                log.warning("autárquicas %s returned only %s municípios, expected 308",
                            election.year, seen)

    def _for_election(self, e: Election, end: date | None) -> Iterator[MandateRecord]:
        if e.generation == "c":
            yield from self._modern(e, end)
        else:
            yield from self._legacy(e, end)

    # ---- 2009 / 2013 / 2017 / 2021 -------------------------------------
    def _legacy(self, e: Election, end: date | None) -> Iterator[MandateRecord]:
        for dd in DISTRICT_CODES:
            url = self._legacy_url(e, f"{dd}0000")
            try:
                payload = self.client.get_json(url)
            except Exception as exc:  # a district that does not exist 404s
                log.debug("autárquicas %s district %s: %s", e.year, dd, exc)
                continue
            for territory in payload.get("electionCandidates", []) or []:
                key = territory.get("territoryKey") or ""
                # LOCAL-111600 -> dico 1116. Trailing "00" is the freguesia level.
                dico = key.removeprefix("LOCAL-")[:4] if key.startswith("LOCAL-") else ""
                if len(dico) != 4 or not dico.isdigit():
                    continue
                for cand in territory.get("candidates", []) or []:
                    if not cand.get("presidents"):
                        continue
                    names = cand.get("effectiveCandidates") or []
                    yield MandateRecord(
                        dico=dico,
                        election_date=e.day,
                        term_start=e.day,
                        term_end=end,
                        party=canonical_party(cand.get("party")),
                        # The legacy payloads carry no party/coalition flag. The
                        # acronyms are separable ("PPD/PSD.CDS-PP" is a coalition,
                        # a dot joins the members) but guessing is worse than
                        # admitting it, so these stay False and the UI says so.
                        coalition=False,
                        citizens_group=False,
                        president=clean_person_name(names[0] if names else None),
                        mandates=cand.get("mandates"),
                    )

    @staticmethod
    def _legacy_url(e: Election, territory: str) -> str:
        if e.generation == "b":
            return (f"{BASE}/autarquicas{e.year}/assets/static/candidates/"
                    f"parties-candidates-CM-LOCAL-{territory}-1-true.json")
        suffix = "-ELECTED-TRUE" if e.year >= 2017 else ""
        return (f"{BASE}/autarquicas{e.year}/static-data/candidates/"
                f"PARTIES-CANDIDATES-CM-LOCAL-{territory}-PAGE-1{suffix}.json")

    # ---- 2025 ----------------------------------------------------------
    def _modern(self, e: Election, end: date | None) -> Iterator[MandateRecord]:
        page = 1
        while True:
            url = (f"{BASE}/autarquicas{e.year}/assets/static/candidate/"
                   f"candidates-electionId=1-territoryId=null-votingOptionName=null"
                   f"-candidatesElected=true-page={page}.json")
            payload = self.client.get_json(url).get("data") or {}
            for district in payload.get("territories", []) or []:
                # 2025 dropped DICO entirely, so the join is by name with the
                # district as tiebreak. That is the same ambiguity the geometry
                # file already documents: there are two Lagoas.
                district_name = district.get("description") or ""
                for town in district.get("territories", []) or []:
                    name = town.get("description") or ""
                    dico = dico_for(name, district_name)
                    if not dico:
                        log.warning("autárquicas 2025: no dico for %r in %r", name, district_name)
                        continue
                    for option in town.get("votingOptions", []) or []:
                        vo = option.get("votingOption") or {}
                        president = next(
                            (c.get("name") for c in option.get("candidates", []) or []
                             if c.get("state") == "President"), None)
                        if not president:
                            continue
                        type_id = vo.get("typeId")
                        yield MandateRecord(
                            dico=dico,
                            election_date=e.day,
                            term_start=e.day,
                            term_end=end,
                            party=canonical_party(vo.get("name")),
                            coalition=type_id == 2,
                            citizens_group=type_id == 3,
                            president=clean_person_name(president),
                            mandates=None,
                        )
            if page >= int(payload.get("numberOfPages") or 1):
                return
            page += 1
