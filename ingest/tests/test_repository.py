"""Self-check for the upsert guards: python -m pytest, or just run this file.

Needs no database. The rule being tested is a property of the batch handed to
Postgres, not of what Postgres does with it, and the failure it prevents
("ON CONFLICT DO UPDATE command cannot affect row a second time") aborts the
whole statement rather than skipping a row, so it takes a national ingest down
with it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contratos_ingest.repository import EntityRepository


def _row(nif, name, total=0.0):
    """A row in COLUMNS order: nif, name, country, and five counters."""
    return (nif, name, "PT", 1, 1, 0, total, 0.0)


def test_dedupe_collapses_a_repeated_nif():
    batch = [_row("500051070", "Lisboa"), _row("501442600", "Porto"),
             _row("500051070", "Município de Lisboa")]
    out = EntityRepository._dedupe(batch)
    assert len(out) == 2
    assert len({row[0] for row in out}) == 2


def test_dedupe_keeps_the_last_spelling():
    # Repeats are the same entity seen again, so the later row wins.
    out = EntityRepository._dedupe([_row("500051070", "LISBOA"), _row("500051070", "Município de Lisboa")])
    assert out == [_row("500051070", "Município de Lisboa")]


def test_dedupe_leaves_a_clean_batch_alone():
    batch = [_row("500051070", "Lisboa"), _row("501442600", "Porto")]
    assert EntityRepository._dedupe(batch) == batch


def test_dedupe_is_empty_safe():
    assert EntityRepository._dedupe([]) == []
