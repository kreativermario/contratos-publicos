"""The additive half of `create_all`, without a database.

`create_all` creates missing tables and ignores a table that exists but has
drifted. That is how `status` and `county` reached production as columns the
ORM had and Postgres did not, and every request that read them answered 500.
The decision of what may be added in place is pure, so it is tested here; the
ALTER itself is two lines around it.
"""
from contratos_core.db import missing_columns, missing_indexes, unaddable
from contratos_core.models import Base, CompanyProfile, Contract
from sqlalchemy import Column, Integer, String, Text


def test_a_table_in_step_needs_nothing():
    table = CompanyProfile.__table__
    have = {c.name for c in table.columns}
    assert missing_columns(table, have) == []


def test_a_drifted_table_reports_exactly_what_it_lacks():
    table = CompanyProfile.__table__
    have = {c.name for c in table.columns} - {"status", "county"}
    assert sorted(c.name for c in missing_columns(table, have)) == ["county", "status"]


def test_a_nullable_column_is_addable():
    assert unaddable(Column("status", String(16))) is None


def test_a_column_with_a_default_is_addable():
    """Postgres has something to put in the existing rows, so it is fine."""
    assert unaddable(Column("found", Integer, nullable=False, default=1)) is None


def test_not_null_with_no_default_is_refused_by_name():
    why = unaddable(Column("county", Text, nullable=False))
    assert why and "NOT NULL" in why


def test_a_primary_key_is_refused():
    why = unaddable(Column("nif", String(20), primary_key=True))
    assert why and "primary key" in why


def test_every_column_the_orm_declares_today_could_be_added_in_place():
    """A guard on the models rather than on the migrator: if a new column would
    need a real migration, this fails in CI rather than mid-deploy."""
    offenders = [
        f"{table.name}.{column.name}: {unaddable(column)}"
        for table in Base.metadata.sorted_tables
        for column in table.columns
        if column.name in ("status", "county") and unaddable(column)
    ]
    assert offenders == []


def test_a_table_whose_indexes_are_all_present_needs_nothing():
    table = Contract.__table__
    have = {i.name for i in table.indexes}
    assert missing_indexes(table, have) == []


def test_an_index_added_to_an_existing_table_is_reported():
    """`create_all` builds a table's indexes with the table and never after.

    So an index added to the ORM later is invisible to it, exactly as a column
    was. The summary index is the one that made this matter: without it the
    município list seq-scanned the national contracts table for 18.8s.
    """
    table = Contract.__table__
    have = {i.name for i in table.indexes} - {"ix_contracts_buyer_summary"}
    assert [i.name for i in missing_indexes(table, have)] == ["ix_contracts_buyer_summary"]


def test_the_summary_index_covers_what_the_aggregate_reads():
    """An index-only scan needs every column the query touches to be in the
    index. Drop one from INCLUDE and Postgres goes back to the heap, silently,
    and the 18.8s comes back."""
    index = next(i for i in Contract.__table__.indexes
                 if i.name == "ix_contracts_buyer_summary")
    assert [c.name for c in index.columns] == ["buyer_nif"]
    assert set(index.dialect_options["postgresql"]["include"]) == {
        "buyer_name", "value", "signed_date"}
