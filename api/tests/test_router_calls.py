"""Every `repo.x(...)` call in a router must fit `x`'s signature.

A route that passes a keyword the repository does not accept is a 500 on the
first request and nothing catches it earlier: `svelte-check` only reads the
frontend, and the routers are only imported at runtime. That is how
`contracts() got an unexpected keyword argument 'date_from'` reached
production, after an edit added the parameter to the router and missed the
repository because the two signatures are laid out differently.

This binds each call's keywords against the real signature, with no database
and no server.
"""
from __future__ import annotations

import ast
import inspect
import pathlib

from contratos_api import repositories
from contratos_api.services.scoring import ScoringService

# From the installed package, not from this file's neighbours: in the container
# the tests live at /app/tests while the package sits in site-packages.
ROUTERS = pathlib.Path(repositories.__file__).resolve().parent / "routers"

#: Which object each receiver name refers to, so a call can be checked.
TARGETS = {
    "repo": repositories.MunicipalityRepository,
    "scoring": ScoringService,
}


def _calls(path: pathlib.Path):
    """Every `<receiver>.<method>(...)` call on a known target in one file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not isinstance(fn, ast.Attribute) or not isinstance(fn.value, ast.Name):
            continue
        owner = TARGETS.get(fn.value.id)
        if owner is None:
            continue
        yield path.name, fn.value.id, fn.attr, node, owner


def test_every_router_call_fits_its_repository_method():
    checked = 0
    for filename, receiver, method, node, owner in _calls_all():
        target = getattr(owner, method, None)
        assert target is not None, f"{filename}: {receiver}.{method} does not exist"

        sig = inspect.signature(target)
        positional = [object()] * len(node.args)
        keywords = {}
        for kw in node.keywords:
            if kw.arg is None:          # **kwargs splat: nothing to check
                continue
            keywords[kw.arg] = object()

        try:
            # `self` is bound on an instance call, so stand one in
            sig.bind(object(), *positional, **keywords)
        except TypeError as exc:
            raise AssertionError(
                f"{filename}: {receiver}.{method}(...) does not fit "
                f"{owner.__name__}.{method}{sig}: {exc}"
            ) from exc
        checked += 1

    assert checked > 10, f"only {checked} calls checked; the walker is not finding them"


def _calls_all():
    for path in sorted(ROUTERS.glob("*.py")):
        yield from _calls(path)


def test_the_supplier_id_index_matches_the_expression_the_queries_filter_on():
    """Postgres only uses an expression index for the same expression. If
    `_supplier_id()` ever changes shape and the index does not, every município
    page goes back to scanning the national supplier table, and nothing fails."""
    from contratos_api.repositories import _supplier_id
    from contratos_core.models import ContractSupplier
    from sqlalchemy.dialects import postgresql

    index = next(i for i in ContractSupplier.__table__.indexes if i.name == "ix_suppliers_sid")
    indexed = str(index.expressions[0]).replace(" ", "")
    queried = str(_supplier_id().compile(dialect=postgresql.dialect())).replace(" ", "")
    assert queried.replace("contract_suppliers.", "") == indexed


def test_supplier_debuts_are_built_with_the_same_identity_the_queries_ask_for():
    """The table is looked up by `_supplier_id()`. Built under any other key,
    every lookup misses, every firm reads as unknowable, and nothing errors."""
    from contratos_core import Database
    assert any("coalesce(s.nif, s.name)" in stmt for stmt in Database.REFRESH_SUMMARIES)
    test_the_supplier_id_index_matches_the_expression_the_queries_filter_on()


def test_supplier_aggregates_match_what_the_six_queries_used_to_return():
    from contratos_api.repositories import supplier_aggregates
    rows = [{"v": v, "n": n} for v, n in [(50.0, 6), (30.0, 1), (10.0, 5), (10.0, 2)]]
    got = supplier_aggregates(rows, 100.0, repeat_min=5)
    assert got["top3_value"] == 90.0
    assert got["suppliers"] == 4
    assert got["repeat_value"] == 60.0
    assert got["top_supplier_value"] == 50.0
    assert abs(got["hhi"] - (0.25 + 0.09 + 0.01 + 0.01)) < 1e-12
    empty = supplier_aggregates([], 0.0, repeat_min=5)
    assert empty["hhi"] is None and empty["top_supplier_value"] == 0 and empty["suppliers"] == 0
