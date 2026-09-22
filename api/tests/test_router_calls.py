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


if __name__ == "__main__":
    # Defined at the bottom on purpose: it runs whatever is in globals() at the
    # time, so a test added after it would silently never run.
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
    print("all passed")
