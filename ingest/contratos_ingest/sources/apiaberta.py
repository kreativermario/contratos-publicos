"""apiaberta live deltas.

A lossy 6-field mirror of base.gov.pt behind 30 req/min, but it refreshes daily -
useful for the window between IMPIC's bulk refreshes. Contracts landed here carry
source='apiaberta' and lack location, CPV and bidders; the next IMPIC run upgrades
them in place.
"""
from __future__ import annotations

import json
import logging
import urllib.error
from collections.abc import Iterator

from contratos_core import Settings

from ..http import HttpClient, RateLimiter
from ..parsers import parse_date, parse_entity
from . import ContractRecord, ContractSource

log = logging.getLogger(__name__)


class ApiabertaSource(ContractSource):
    name = "apiaberta"

    def __init__(self, settings: Settings, known_ids: set[int]) -> None:
        super().__init__(settings)
        self.known_ids = known_ids
        headers = {"X-API-Key": settings.apiaberta_key} if settings.apiaberta_key else {}
        self.client = HttpClient(headers=headers)
        self.limiter = RateLimiter(settings.apiaberta_rate_per_min)

    def _page(self, page: int) -> list[dict]:
        url = f"{self.settings.apiaberta_base}/contracts"
        params = {"limit": self.settings.apiaberta_page_size, "page": page}
        for attempt in range(6):
            self.limiter.wait()
            try:
                return self.client.get_json(url, params).get("data", [])
            except urllib.error.HTTPError as exc:
                if exc.code != 429:
                    raise
                pause = int(exc.headers.get("x-ratelimit-reset") or 60) + 1
                log.warning("429 on page %s, sleeping %ss (attempt %s)", page, pause, attempt + 1)
                import time
                time.sleep(pause)
        raise RuntimeError(f"apiaberta kept rate-limiting page {page}")

    def records(self) -> Iterator[ContractRecord]:
        """The listing is newest-first; stop once we have re-seen enough known ids."""
        seen_known, page = 0, 1
        while seen_known < self.settings.apiaberta_delta_stop_after:
            rows = self._page(page)
            if not rows:
                return
            for raw in rows:
                try:
                    contract_id = int(raw["id"])
                except (KeyError, TypeError, ValueError):
                    continue
                if contract_id in self.known_ids:
                    seen_known += 1
                    continue
                if record := self.to_record(contract_id, raw):
                    yield record
            page += 1

    def to_record(self, contract_id: int, raw: dict) -> ContractRecord | None:
        buyer_nif, buyer_name = parse_entity(raw.get("contractingEntity"))
        if not self.in_scope(buyer_nif):
            return None
        signed = parse_date(raw.get("date"), "%Y-%m-%d")
        supplier_nif, supplier_name = parse_entity(raw.get("awarded"))
        contract = {
            "id": contract_id,
            "year": signed.year if signed else None,
            "procedure": raw.get("type") or None,
            "contract_types": [],
            "object": raw.get("description") or None,
            "buyer_nif": buyer_nif,
            "buyer_name": buyer_name,
            "value": raw.get("value"),
            "base_price": None,
            "signed_date": signed,
            "pub_date": None,
            "exec_days": None,
            "cpv": None,
            "cpv_desc": None,
            "n_bidders": None,
            "framework": None,
            "justification": None,
            "ad_justification": None,
            "centralized": None,
            "green": None,
            "criterion": None,
            "source": self.name,
            "raw": raw,
        }
        return ContractRecord(
            contract=contract,
            suppliers=[(contract_id, supplier_nif, supplier_name)] if supplier_name else [],
        )
