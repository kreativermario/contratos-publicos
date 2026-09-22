"""Bulk persistence.

The ORM owns the schema; loading goes through COPY into unlogged staging tables
followed by an upsert. Pushing millions of rows through ORM instances is roughly
50x slower and buys nothing here.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Iterable, Iterator
from typing import Any

from contratos_core import Database
from sqlalchemy import text

from .sources import ContractRecord

log = logging.getLogger(__name__)

CONTRACT_COLUMNS = [
    "id", "year", "procedure", "contract_types", "object", "buyer_nif", "buyer_name",
    "value", "base_price", "signed_date", "pub_date", "exec_days", "cpv", "cpv_desc",
    "n_bidders", "framework", "justification", "ad_justification", "centralized",
    "green", "criterion", "source", "raw",
]

CHILDREN = (
    ("contract_suppliers", "stage_suppliers", ("contract_id", "nif", "name")),
    ("contract_bidders", "stage_bidders", ("contract_id", "nif", "name")),
    ("contract_locations", "stage_locations", ("contract_id", "country", "district", "municipality")),
)


def _chunked(items: Iterable[ContractRecord], size: int) -> Iterator[list[ContractRecord]]:
    batch: list[ContractRecord] = []
    for item in items:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


class ContractRepository:
    def __init__(self, database: Database) -> None:
        self.db = database

    def known_ids(self) -> set[int]:
        with self.db.engine.connect() as conn:
            return {row[0] for row in conn.execute(text("SELECT id FROM contracts"))}

    def bulk_upsert(self, records: Iterable[ContractRecord], batch_size: int) -> int:
        total = 0
        for batch in _chunked(records, batch_size):
            total += self._write_batch(batch)
            log.info("loaded %s contracts", total)
        return total

    def _write_batch(self, batch: list[ContractRecord]) -> int:
        # One contract can reach the same batch twice: a contract with several
        # adjudicantes is emitted once per municipality in scope, so widening
        # MUNICIPALITY_NIFS makes collisions likely rather than rare. Postgres
        # refuses an ON CONFLICT upsert whose source touches a target row twice
        # ("cannot affect row a second time"), which killed the whole run, so
        # collapse duplicates before staging. Last one wins: repeats are the
        # same contract seen from another buyer, not different versions. The
        # child inserts already SELECT DISTINCT and need nothing here.
        batch = list({record.contract["id"]: record for record in batch}.values())

        raw_conn = self.db.engine.raw_connection()
        try:
            pg = raw_conn.driver_connection
            with pg.cursor() as cur:
                cur.execute("""
                    CREATE TEMP TABLE stage_contracts (LIKE contracts INCLUDING DEFAULTS) ON COMMIT DROP;
                    CREATE TEMP TABLE stage_suppliers (contract_id bigint, nif text, name text) ON COMMIT DROP;
                    CREATE TEMP TABLE stage_bidders   (contract_id bigint, nif text, name text) ON COMMIT DROP;
                    CREATE TEMP TABLE stage_locations (contract_id bigint, country text, district text, municipality text) ON COMMIT DROP;
                """)
                columns = ", ".join(CONTRACT_COLUMNS)
                with cur.copy(f"COPY stage_contracts ({columns}) FROM STDIN") as copy:
                    for record in batch:
                        copy.write_row(self._contract_row(record.contract))
                self._copy_children(cur, batch)

                updates = ", ".join(f"{c}=EXCLUDED.{c}" for c in CONTRACT_COLUMNS if c != "id")
                cur.execute(
                    f"INSERT INTO contracts ({columns}) SELECT {columns} FROM stage_contracts "
                    f"ON CONFLICT (id) DO UPDATE SET {updates}"
                )
                # children carry no version of their own - rebuild them for touched ids
                for table, stage, cols in CHILDREN:
                    col_list = ", ".join(cols)
                    cur.execute(f"DELETE FROM {table} WHERE contract_id IN (SELECT id FROM stage_contracts)")
                    cur.execute(
                        f"INSERT INTO {table} ({col_list}) SELECT DISTINCT {col_list} FROM {stage} "
                        f"WHERE contract_id IN (SELECT id FROM stage_contracts) ON CONFLICT DO NOTHING"
                    )
            raw_conn.commit()
            return len(batch)
        except Exception:
            raw_conn.rollback()
            raise
        finally:
            raw_conn.close()

    @staticmethod
    def _copy_children(cur, batch: list[ContractRecord]) -> None:
        payloads = (
            ("stage_suppliers", "(contract_id, nif, name)", [r for rec in batch for r in rec.suppliers]),
            ("stage_bidders", "(contract_id, nif, name)", [r for rec in batch for r in rec.bidders]),
            ("stage_locations", "(contract_id, country, district, municipality)",
             [r for rec in batch for r in rec.locations]),
        )
        for table, cols, rows in payloads:
            if not rows:
                continue
            with cur.copy(f"COPY {table} {cols} FROM STDIN") as copy:
                for row in rows:
                    copy.write_row(row)

    @staticmethod
    def _contract_row(contract: dict[str, Any]) -> tuple:
        row = dict(contract)
        row["raw"] = json.dumps(row.get("raw"), ensure_ascii=False) if row.get("raw") is not None else None
        return tuple(row[c] for c in CONTRACT_COLUMNS)


class EntityRepository:
    COLUMNS = ("nif", "name", "country", "n_contracts", "n_as_supplier",
               "n_as_buyer", "total_won", "total_spent")

    def __init__(self, database: Database) -> None:
        self.db = database

    def upsert(self, rows: Iterable[dict[str, Any]], batch_size: int = 50_000) -> int:
        total, batch = 0, []
        for row in rows:
            batch.append(tuple(row[c] for c in self.COLUMNS))
            if len(batch) >= batch_size:
                total += self._write(batch)
                batch = []
        if batch:
            total += self._write(batch)
        return total

    def _write(self, batch: list[tuple]) -> int:
        raw_conn = self.db.engine.raw_connection()
        try:
            pg = raw_conn.driver_connection
            columns = ", ".join(self.COLUMNS)
            updates = ", ".join(f"{c}=EXCLUDED.{c}" for c in self.COLUMNS if c != "nif")
            with pg.cursor() as cur:
                cur.execute("CREATE TEMP TABLE stage_entities (LIKE entities) ON COMMIT DROP")
                with cur.copy(f"COPY stage_entities ({columns}) FROM STDIN") as copy:
                    for row in batch:
                        copy.write_row(row)
                cur.execute(
                    f"INSERT INTO entities ({columns}) SELECT {columns} FROM stage_entities "
                    f"ON CONFLICT (nif) DO UPDATE SET {updates}"
                )
            raw_conn.commit()
            return len(batch)
        except Exception:
            raw_conn.rollback()
            raise
        finally:
            raw_conn.close()


class MandateRepository:
    """Who held each câmara, one row per município per election.

    1540 rows for the whole country across five elections, so this goes through
    the ORM rather than COPY. The bulk machinery above exists for millions of
    contracts and would be pure ceremony here.
    """

    def __init__(self, database: Database) -> None:
        self.db = database

    def replace_all(self, records: Iterable[Any]) -> int:
        from contratos_core import Mandate

        # Collapse by the unique key before inserting. Two different names can
        # resolve to one concelho when a source spells it differently, and the
        # whole run should not die on a UniqueViolation; the lookup is where
        # that gets fixed, and a collision here is worth a warning, not a crash.
        deduped = {(r.dico, r.election_date): r for r in records}
        rows = [
            {
                "dico": r.dico,
                "election_date": r.election_date,
                "term_start": r.term_start,
                "term_end": r.term_end,
                "party": r.party,
                "coalition": r.coalition,
                "citizens_group": r.citizens_group,
                "president": r.president,
                "mandates": r.mandates,
                "source": "mai",
            }
            for r in deduped.values()
        ]
        if not rows:
            log.warning("no mandates parsed, leaving the table untouched")
            return 0
        by_election: dict = {}
        for (dico, election) in deduped:
            by_election[election] = by_election.get(election, 0) + 1
        for election, n in sorted(by_election.items()):
            if n != 308:
                log.warning("autárquicas %s: %s municípios, expected 308", election.year, n)

        # Replace wholesale rather than upsert. The source is a handful of static
        # files that are rewritten in place when a count is corrected, so the
        # truth is always "whatever they say now", and a stale row from a shape
        # we no longer parse would otherwise linger forever. Guarded by the
        # emptiness check above so a failed fetch cannot wipe the table.
        with self.db.session() as session:
            session.query(Mandate).delete()
            session.bulk_insert_mappings(Mandate, rows)
        log.info("mandates: %s rows", len(rows))
        return len(rows)
