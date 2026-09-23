"""Env parsing is the layer that broke the first container run: pydantic-settings
JSON-decodes list fields from the environment before validators see them.
Run: python core/tests/test_settings.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contratos_core.settings import Settings

BASE = {"DATABASE_URL": "postgresql://u:p@db:5432/x"}


def build(**env) -> Settings:
    os.environ.clear()
    os.environ.update(BASE | env)
    return Settings(_env_file=None)


def test_bare_values_are_not_json():
    # each of these used to raise SettingsError before NoDecode
    s = build(MUNICIPALITY_NIFS="504293125", API_CORS_ORIGINS="*")
    assert s.municipality_nifs == ["504293125"]
    assert s.api_cors_origins == ["*"]


def test_csv_and_scope():
    s = build(MUNICIPALITY_NIFS="504293125, 501305912")
    assert s.scope_nifs == {"504293125", "501305912"}
    # empty means national, never "no municipalities"
    assert build().scope_nifs == set()


def test_year_ranges():
    assert build(IMPIC_YEARS="2012-2014,2026").impic_years == [2012, 2013, 2014, 2026]
    assert build(IMPIC_YEARS="2026").impic_years == [2026]
    assert build().impic_years == []


def test_database_url_gets_psycopg3_driver():
    # a bare postgresql:// URL makes SQLAlchemy reach for psycopg2, which is not installed
    assert build().database_url.startswith("postgresql+psycopg://")
    assert build(DATABASE_URL="postgres://u:p@h/db").database_url.startswith("postgresql+psycopg://")
    # an explicit driver is left alone
    explicit = "postgresql+psycopg://u:p@h/db"
    assert build(DATABASE_URL=explicit).database_url == explicit


def test_thresholds_are_tunable():
    s = build(AD_LIMIT_SERVICES="25000", CONSULTA_PREVIA_LIMIT="80000")
    assert s.thresholds == (25000.0, 30000.0, 80000.0)
