"""CLI: python -m contratos_ingest {schema,impic,entities,delta,all}"""
from __future__ import annotations

import argparse
import logging
import re
import sys

from contratos_core import (CONCELHOS, Database, concelho_name, dico_for,
                             get_settings)

from .repository import (ContractRepository, EntityRepository,
                         MandateRepository)
from .sources.apiaberta import ApiabertaSource
from .sources.autarquicas import AutarquicasSource
from .sources.impic import ImpicContractSource, ImpicEntitySource

log = logging.getLogger("contratos.ingest")

COMMANDS = ("schema", "impic", "entities", "mandatos", "delta", "all", "nifs")

#: Groupings a person actually asks for, resolved to the concelhos they contain.
#: Districts come from the geometry; the peninsula is a NUTS III unit that the
#: district table does not express, so it is listed by its nine concelhos.
PENINSULA_SETUBAL = (
    "Alcochete", "Almada", "Barreiro", "Moita", "Montijo",
    "Palmela", "Seixal", "Sesimbra", "Setúbal",
)


#: A buyer name that is the câmara itself, and not something else in the same
#: town. `concelho_name` only strips the administrative prefix, so without this
#: "Universidade do Porto" resolved to Porto, "Agrupamento de Escolas de
#: Lousada" to Lousada, and each shadowed the real câmara because it happened to
#: appear first in the file.
_CAMARA = re.compile(r"^\s*(munic[íi]pio|c[âa]mara municipal)\b", re.IGNORECASE)


def _is_camara(name: str | None) -> bool:
    return bool(name and _CAMARA.match(name))


class Ingestor:
    def __init__(self, database: Database, settings) -> None:
        self.db = database
        self.settings = settings
        self.contracts = ContractRepository(database)
        self.entities = EntityRepository(database)
        self.mandates = MandateRepository(database)

    def schema(self) -> None:
        self.db.create_all()
        log.info("schema ready")

    def impic(self) -> int:
        source = ImpicContractSource(self.settings)
        count = self.contracts.bulk_upsert(source.records(), self.settings.batch_size)
        log.info("IMPIC: %s contracts", count)
        return count

    def entities_load(self) -> int:
        count = self.entities.upsert(ImpicEntitySource(self.settings).rows())
        log.info("entities: %s", count)
        return count

    def mandatos(self) -> int:
        """Autárquicas results. Independent of the contract data: it covers all
        308 municípios regardless of which ones have contracts loaded."""
        count = self.mandates.replace_all(AutarquicasSource().records())
        log.info("mandatos: %s", count)
        return count

    def delta(self) -> int:
        known = self.contracts.known_ids()
        log.info("delta: %s contracts already held", len(known))
        source = ApiabertaSource(self.settings, known)
        count = self.contracts.bulk_upsert(source.records(), self.settings.batch_size)
        log.info("apiaberta: %s new contracts", count)
        return count

    def nifs(self, regions: list[str]) -> None:
        """Print the buyer NIFs of every câmara in the named regions.

        Adding a município means knowing its NIF, and the NIFs are already in
        the file the ingest downloads. This reads the most recent year, resolves
        each buyer name to a concelho, and prints the ones asked for as a ready
        MUNICIPALITY_NIFS value. Nothing is hardcoded: pass a district name, or
        "peninsula-setubal", or a concelho.
        """
        wanted: set[str] = set()
        for region in regions:
            key = region.strip().lower()
            if key in ("peninsula-setubal", "margem-sul"):
                wanted.update(PENINSULA_SETUBAL)
                continue
            hits = {row[1] for row in CONCELHOS if row[3].lower() == key}
            if hits:
                wanted.update(hits)
            else:
                wanted.add(region.strip())

        target = {dico_for(name) for name in wanted}
        target.discard(None)
        log.info("looking for %s concelhos", len(target))

        source = ImpicContractSource(self.settings)
        found: dict[str, tuple[str, str]] = {}
        for nif, name in source.buyers().items():
            if not _is_camara(name):
                continue
            code = dico_for(concelho_name(name))
            if code and code in target:
                found.setdefault(code, (nif, name))

        missing = sorted(target - set(found))
        for code, (nif, name) in sorted(found.items(), key=lambda kv: kv[1][1]):
            print(f"{nif}  {name}")
        print()
        print("MUNICIPALITY_NIFS=" + ",".join(sorted(n for n, _ in found.values())))
        print(f"\n{len(found)} found, {len(missing)} with no contracts in this year")
        if missing:
            by_dico = {c[0]: c[1] for c in CONCELHOS}
            print("  missing: " + ", ".join(by_dico.get(d, d) for d in missing))

    def run(self, command: str, regions: list[str] | None = None) -> None:
        if command == "nifs":
            # read-only: it does not touch the schema or the database at all
            self.nifs(regions or [])
            return
        self.schema()
        if command in ("impic", "all"):
            self.impic()
        if command in ("entities", "all"):
            self.entities_load()
        if command in ("mandatos", "all"):
            self.mandatos()
        if command in ("delta", "all"):
            self.delta()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="contratos-ingest")
    parser.add_argument("command", choices=COMMANDS, nargs="?", default="all")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument(
        "regions", nargs="*",
        help='for "nifs": district names, concelho names, or "margem-sul"',
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    settings = get_settings()
    database = Database(settings)
    try:
        Ingestor(database, settings).run(args.command, args.regions)
    finally:
        database.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
