"""IMPIC bulk contracts and entities, published on dados.gov.pt.

The authoritative source: 35 fields per contract, 2012 to the current year, no
rate limit. Resource URLs carry a rotating date stamp, so they are always
resolved from the dataset slug rather than hardcoded.
"""
from __future__ import annotations

import io
import logging
import os
import re
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from contratos_core import Settings

from ..http import HttpClient
from ..parsers import (as_list, first, parse_bidder, parse_bool, parse_cpv,
                       parse_date, parse_entity, parse_location,
                       stream_json_array)
from . import ContractRecord, ContractSource

log = logging.getLogger(__name__)
_YEAR_RE = re.compile(r"^contratos(\d{4})\.(zip|json)$", re.IGNORECASE)


class DadosGovCatalog:
    """Resolves a dataset slug to its current resource files."""

    def __init__(self, settings: Settings, client: HttpClient | None = None) -> None:
        self.settings = settings
        self.client = client or HttpClient()

    def resources(self, slug: str) -> dict[str, dict]:
        url = f"{self.settings.dados_gov_api}/datasets/{slug}/"
        payload = self.client.get_json(url)
        return {(r.get("title") or "").lower(): r for r in payload.get("resources", [])}


class ImpicContractSource(ContractSource):
    name = "impic"

    def __init__(self, settings: Settings, catalog: DadosGovCatalog | None = None) -> None:
        super().__init__(settings)
        self.catalog = catalog or DadosGovCatalog(settings)
        self.client = HttpClient()

    def available_years(self, resources: dict[str, dict]) -> list[int]:
        found = sorted(int(m.group(1)) for title in resources if (m := _YEAR_RE.match(title)))
        wanted = self.settings.impic_years
        return [y for y in found if y in wanted] if wanted else found

    def records(self) -> Iterator[ContractRecord]:
        resources = self.catalog.resources(self.settings.impic_dataset_contracts)
        years = self.available_years(resources)
        log.info("IMPIC years=%s scope=%s", years, self.settings.scope_nifs or "NATIONAL")
        for year in years:
            yield from self._records_for_year(resources, year)

    def _records_for_year(self, resources: dict[str, dict], year: int) -> Iterator[ContractRecord]:
        resource = resources.get(f"contratos{year}.zip") or resources.get(f"contratos{year}.json")
        if not resource:
            log.warning("year %s not published, skipping", year)
            return
        for raw in self._raw_rows(resource, year):
            if record := self.to_record(raw):
                yield record

    def _raw_rows(self, resource: dict, year: int) -> Iterator[dict]:
        """Every row of a year file, before any scope filter."""
        path = self._cached(resource, year)
        # The file is the cache and is deliberately kept; see _cached.
        if path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as archive:
                inner = next(n for n in archive.namelist() if n.lower().endswith(".json"))
                with archive.open(inner) as binary:
                    yield from stream_json_array(io.TextIOWrapper(binary, encoding="utf-8"))
        else:
            with path.open(encoding="utf-8") as handle:
                yield from stream_json_array(handle)

    def _cached(self, resource: dict, year: int) -> Path:
        """Download a year file once and keep it.

        Each year is 40+ MB and IMPIC republishes them rarely, so re-fetching
        every run is pure waste: at 2012-2026 that is roughly 600 MB pulled from
        dados.gov.pt on every single run, including the one that fires on each
        deploy.

        The filename carries the publisher's own checksum, which makes the cache
        self-invalidating: a republished file has a new checksum, so it lands
        under a new name and the superseded copy is pruned. Falling back to
        last_modified covers resources that ship no checksum; the size check
        then catches a download that was cut short.
        """
        cache = Path(self.settings.workdir) / "cache"
        cache.mkdir(parents=True, exist_ok=True)

        stamp = ((resource.get("checksum") or {}).get("value")
                 or resource.get("last_modified") or "")
        key = re.sub(r"[^A-Za-z0-9]", "", str(stamp))[:20] or "nokey"
        suffix = Path(resource["url"]).suffix.lower() or ".zip"
        path = cache / f"contratos{year}-{key}{suffix}"

        size = resource.get("filesize")
        if path.exists() and (not size or path.stat().st_size == size):
            log.info("cached %s", path.name)
            return path

        # Download beside the target and rename: /data is shared, so a concurrent
        # run must never read a half-written file. os.replace is atomic.
        tmp = cache / f".{os.getpid()}-{path.name}"
        log.info("downloading %s", path.name)
        self.client.download(resource["url"], tmp)
        os.replace(tmp, path)

        for stale in cache.glob(f"contratos{year}-*"):
            if stale != path:
                stale.unlink(missing_ok=True)
        return path

    def buyers(self, year: int | None = None) -> dict[str, str]:
        """Every buying entity in one year of the bulk file, NIF to name.

        Scope-free on purpose: this is how the scope itself gets decided. Adding
        a município means knowing its NIF, and the NIF is already in the file we
        download anyway, so there is no reason to keep a list of them in code.
        """
        resources = self.catalog.resources(self.settings.impic_dataset_contracts)
        years = self.available_years(resources)
        target = year or (max(years) if years else None)
        if target is None:
            return {}

        found: dict[str, str] = {}
        resource = (resources.get(f"contratos{target}.zip")
                    or resources.get(f"contratos{target}.json"))
        if not resource:
            return found
        for raw in self._raw_rows(resource, target):
            nif, name = parse_entity(first(raw.get("adjudicante")))
            if nif and name:
                found.setdefault(nif, name)
        return found

    def to_record(self, raw: dict[str, Any]) -> ContractRecord | None:
        buyer_nif, buyer_name = parse_entity(first(raw.get("adjudicante")))
        if not self.in_scope(buyer_nif):
            return None
        try:
            contract_id = int(raw["idcontrato"])
        except (KeyError, TypeError, ValueError):
            return None

        cpv_code, cpv_desc = parse_cpv(first(raw.get("cpv")))
        bidders = [b for b in (parse_bidder(x) for x in as_list(raw.get("concorrentes"))) if b[1]]

        contract = {
            "id": contract_id,
            "year": raw.get("Ano"),
            "procedure": raw.get("tipoprocedimento") or None,
            "contract_types": as_list(raw.get("tipoContrato")),
            "object": raw.get("objectoContrato") or raw.get("descContrato") or None,
            "buyer_nif": buyer_nif,
            "buyer_name": buyer_name,
            "value": raw.get("precoContratual"),
            "base_price": raw.get("precoBaseProcedimento"),
            "signed_date": parse_date(raw.get("dataCelebracaoContrato")),
            "pub_date": parse_date(raw.get("dataPublicacao")),
            "exec_days": raw.get("prazoExecucao"),
            "cpv": cpv_code,
            "cpv_desc": cpv_desc,
            "n_bidders": len(bidders) or None,
            "framework": raw.get("numAcordoQuadro") or None,
            "justification": raw.get("fundamentacao") or None,
            "ad_justification": raw.get("fundamentAjusteDireto") or None,
            "centralized": parse_bool(raw.get("ProcedimentoCentralizado")),
            "green": parse_bool(raw.get("ContratEcologico")),
            "criterion": raw.get("TipoCriterioAdjudicacao") or None,
            "source": self.name,
            "raw": raw,
        }
        suppliers = [(contract_id, nif, name)
                     for nif, name in map(parse_entity, as_list(raw.get("adjudicatarios"))) if name]
        locations = {(contract_id, *parse_location(loc)) for loc in as_list(raw.get("localExecucao"))}
        return ContractRecord(
            contract=contract,
            suppliers=suppliers,
            bidders=[(contract_id, nif, name) for nif, name in bidders],
            locations=[loc for loc in locations if any(loc[1:])],
        )


class ImpicEntitySource:
    """entidades.json - 214k entities, and the only published source of country."""

    def __init__(self, settings: Settings, catalog: DadosGovCatalog | None = None) -> None:
        self.settings = settings
        self.catalog = catalog or DadosGovCatalog(settings)
        self.client = HttpClient()

    def rows(self) -> Iterator[dict[str, Any]]:
        resource = self.catalog.resources(self.settings.impic_dataset_entities).get("entidades.json")
        if not resource:
            log.warning("entidades.json not published")
            return
        path = self.client.download(
            resource["url"], Path(self.settings.workdir) / f"{os.getpid()}-entidades.json")
        try:
            with path.open(encoding="utf-8") as handle:
                for raw in stream_json_array(handle):
                    nif = (raw.get("nifEntidade") or "").strip()
                    if not nif.isdigit():
                        continue
                    yield {
                        "nif": nif,
                        "name": raw.get("desigEntidade"),
                        "country": raw.get("descPais") or None,
                        "n_contracts": raw.get("numContratos"),
                        "n_as_supplier": raw.get("totAdjudicatario"),
                        "n_as_buyer": raw.get("totAdjudicante"),
                        "total_won": raw.get("totValorContratIni"),
                        "total_spent": raw.get("totAdjudicanteValorContratIni"),
                    }
        finally:
            path.unlink(missing_ok=True)
