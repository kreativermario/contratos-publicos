# Contributing

Satirical analytics over Portuguese public contracts. Patches welcome,
especially new municipalities, concelho name fixes, and anything that makes an
indicator harder to misread.

## First, enable the hooks

```bash
git config core.hooksPath .githooks
```

**Git will not do this for you on clone.** The pre-commit hook blocks secrets,
staged environment files, anything over 2 MB, and em dashes. The same gitleaks
scan runs in CI over the full history, because the hook is opt in per clone and
`--no-verify` exists.

## Running it

```bash
cp .env.example .env
podman compose up -d db api web
podman compose --profile tools run --rm ingest impic
```

Tests:

```bash
python ingest/tests/test_parsers.py
podman compose run --rm --entrypoint python api /app/tests/test_newcomer.py
podman compose --profile tools run --rm --entrypoint python ingest /app/tests/core/test_settings.py
cd web && npx svelte-check
```

`api/tests/test_router_calls.py` binds every `repo.x(...)` call in a router
against that method's real signature, with no database and no server. Run it
after touching a router or a repository. Nothing else checks that seam, and a
mismatch there once returned 500 on every contracts request in production.

## Hard rules

These are not style preferences. Each one is here because breaking it already
caused a bug or a wrong number.

**European Portuguese, with accents, post-AO90.** `índice`, `análise`,
`número`, `média`. `ação` not `acção`, `setor` not `sector`, `objeto` not
`objecto`. The English word `sector` stays in code identifiers; only the
rendered label changes. English translations live in `web/src/lib/messages.ts`,
never inline.

**Never use an em dash in user-facing text or prose.** Use a comma, a colon,
parentheses or a full stop. For a missing value render `N/A`, never a dash
glyph. The hook enforces this in `web/src`, `api`, `core` and `ingest`. It
deliberately does not cover contract descriptions quoted verbatim from IMPIC,
which may contain one and must not be edited.

**Nothing is hardcoded.** Every tunable is an environment variable, documented
in `.env.example`. No municipality name, NIF, year, legal threshold or hostname
belongs in code.

**Nothing here accuses anyone of a crime.** Ajuste direto is a legal procedure.
The indices measure observable red flags and the interface says so. A patch
that reads as an allegation will be asked to soften, not merged and fixed
later.

**A supplier is a NIF, not a name.** The register spells one firm several ways:
EDP appears six times in Loures. Grouping by name splits a company into
several, which deflates concentration, inflates the supplier count and makes
every new spelling read as a debut. Use `_supplier_id()`.

**Never score an unmeasurable signal as zero.** A signal that cannot be
measured in the loaded window is `None` and drops out of the mean. A year to
date extract that stops in September has no December, and counting that as
"0% december rush" silently deflates the index.

**No statistical term ever appears in the interface.** Every indicator is
explained in plain language under `signal.<key>` in `messages.ts`, in both
languages. The reader is a resident, not an economist. `CPV` is spelled
out wherever it is shown.

`CLAUDE.md` carries the full set, including the data limits that are settled
and should not be relitigated. Read it before proposing a new data source.

## Tests

Non-trivial logic leaves one runnable check behind: the smallest thing that
fails if the logic breaks. No frameworks, no fixtures. A `__main__` test runner
belongs at the **bottom** of its file, because it iterates `globals()` at the
moment it executes, so a test added below it never runs and never reports that
it did not.

## Licensing your contribution

The code is AGPL-3.0 and the content is CC-BY-4.0. By opening a pull request
you agree your contribution ships under those terms. There is no CLA.

AGPL matters here for a specific reason: this project's defence is that its
method is open and checkable. The licence makes that true of anyone who
deploys a modified version too.
