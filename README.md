# Onde Vai Parar

**[ondevaiparar.pt](https://ondevaiparar.pt)** | [English](https://ondevaiparar.pt/en)

[![Deploy](https://img.shields.io/github/actions/workflow/status/kreativermario/contratos-publicos/deploy.yml?branch=main&label=deploy&logo=github)](https://github.com/kreativermario/contratos-publicos/actions/workflows/deploy.yml)
[![tests](https://img.shields.io/github/actions/workflow/status/kreativermario/contratos-publicos/tests.yml?branch=main&label=tests&logo=github)](https://github.com/kreativermario/contratos-publicos/actions/workflows/tests.yml)
[![secrets](https://img.shields.io/github/actions/workflow/status/kreativermario/contratos-publicos/secrets.yml?branch=main&label=secrets&logo=github)](https://github.com/kreativermario/contratos-publicos/actions/workflows/secrets.yml)
[![code: AGPL-3.0](https://img.shields.io/badge/code-AGPL--3.0-df2225)](LICENSE)
[![content: CC BY 4.0](https://img.shields.io/badge/content-CC%20BY%204.0-007ca6)](LICENSE-CONTENT)
[![last commit](https://img.shields.io/github/last-commit/kreativermario/contratos-publicos?color=a06a00)](https://github.com/kreativermario/contratos-publicos/commits/main)

Who gets the money from Portuguese municipal councils, and by which procedure.
Analytics over the public contract register (Portal BASE / IMPIC), starting
with one município and built to take all 308.

The site reads the official register, scores a handful of observable signals,
and says in plain language what each one counts. It is satirical in tone and
serious about the arithmetic.

**Nothing here accuses anyone of a crime.** Ajuste direto (direct award) is a
legal procedure and often the sensible one. A high score means "worth a look",
not "this is a crime". The interface repeats that on every page; please keep it
there.

The repository is called `contratos-publicos` rather than the brand, on
purpose: the name describes what the thing reads, so the next rebrand is a copy
edit and a DNS record instead of a rename that breaks every clone and every
link.

## Licensing

| | |
|---|---|
| Code | **AGPL-3.0**, see [`LICENSE`](LICENSE) |
| Content we wrote (prose, design, the indicators and how they are calculated) | **CC-BY-4.0**, see [`LICENSE-CONTENT`](LICENSE-CONTENT) |
| The upstream registers | neither. They belong to the bodies that publish them, listed in [`NOTICE`](NOTICE) |

AGPL is a deliberate choice, not a default. This project's defence is that its
method is auditable: anyone can check what each number counts and where it came
from. AGPL is the only copyleft that reaches a *hosted* service, so a modified
deployment owes its readers the same audit.

One practical consequence: under section 13, a deployed instance must offer its
source to the people using it over the network. That is why the site footer
links back here. If you fork and deploy, keep that link pointing at your fork.

## What the data actually supports

Two contract sources, deliberately:

| | IMPIC bulk (dados.gov.pt) | apiaberta |
|---|---|---|
| fields | **35** | 6 |
| coverage | authoritative | lossy (gave 4 469 of Odivelas' 5 321) |
| rate limit | none | 30 req/min |
| refresh | periodic bulk | daily |

IMPIC carries the fields the site is built on: `localExecucao` (99.9%),
`cpv` (100%), `concorrentes` (41.9%, a **named list of bidders**, not a count).
apiaberta fills the gap between bulk refreshes; those rows land thin, with
`source='apiaberta'`, and the next IMPIC run upgrades them in place. That makes
the bulk run a correction pass rather than a bigger delta.

A third source, the autárquicas results from `eleicoes.mai.gov.pt`, answers who
held each câmara when a contract was signed. It covers all 308 municípios
regardless of which ones have contracts loaded.

Known limits, stated here because the interface states them too:

- **The contract data carries no supplier addresses.** `entidades.json`
  publishes country only, and `localExecucao` is where the work happens, not
  where the firm is based. A registered address does exist outside this data;
  see the company lookup below.
- `PrecoTotalEfetivo` is populated for ~6% of contracts, so cost-overrun
  analysis is not possible. It is not in the schema.
- `concorrentes` covers ~42% of contracts. Every single-bidder figure is
  reported against that denominator, never against the full set.
- A contract may span several concelhos, so the map sums to more than total
  spend. The map says so.
- **No incorporation date, capital social or headcount is published anywhere
  free.** All three live in the paid Certidão Permanente. See below for how far
  the free sources actually go.
- The election results are the **provisional** count. The legally official
  record is the CNE Mapa Oficial, published in Diário da República as a PDF.
- The CCP reform of 30 August 2017 moved these numbers more than any election
  did. A timeline that does not say so invites the reader to credit the drop in
  direct awards to whoever took office that October.

## The two indices

Both read the same aggregates, so the joke can never disagree with the data.

**Every scored indicator is a share of the money.** That is what makes averaging
them legitimate. An earlier version mixed "54% of tenders had one bidder" with
"9% of the money skipped a tender"; those are different quantities and adding
them produced a number that meant nothing. Count-shaped measures still matter,
so they are reported beside the index and never folded into it.

| Scored | What it measures |
|---|---|
| Sem concurso | money awarded by ajuste direto |
| Concentração | Herfindahl index over **every** supplier, not a top-3 share |
| Um só concorrente | money in tenders that drew a single bid, over money in tenders that disclosed bidders |
| Encostado ao limite | money in contracts parked just under a statutory ceiling |
| Dinheiro a empresas novas | money to firms new to public contracting |

Shown but not scored: the ajuste-direto share by *contract count*, the share of
contracts that never disclose their bidders, the largest single supplier, the
top three, and repeat winners.

A signal that is not measurable in the loaded window is `null` and **drops out
of the mean rather than counting as zero**. Scoring an unmeasurable signal as 0%
silently deflates the index.

- **`risk_index`**, the unweighted mean of whatever is measurable.
- **`satirical_index`**, the same numbers with the more revealing ones weighted
  heavier and worse manners. Rendered as the **Malandrómetro**. It returns
  `{score, band, tone, units}`: three bands tied to the same cutoffs the
  colours use, so the words and the colour can never disagree.

Ceilings are statutory and get amended, so they are environment variables
(`AD_LIMIT_SERVICES`, `AD_LIMIT_WORKS`, `CONSULTA_PREVIA_LIMIT`), not constants.

## Two languages, one payload

Portuguese at `/`, English at `/en/`. Portuguese is the source language and the
fallback.

Every string lives in `web/src/lib/messages.ts`, two flat objects with the same
keys, no i18n dependency. `web/scripts/check-messages.mjs` fails if the two
bundles drift apart or if the source asks for a key that does not exist; it runs
as part of `npm run check`.

**The API ships keys, never prose.** One JSON payload serves both languages and
it is cached, so a Portuguese sentence in `/score` would print Portuguese on the
English pages until the cache expired. `api/tests/test_scoring_keys.py` fails if
one reappears.

**What is never translated:** contract descriptions, supplier names, council
names, procedure names and CPV labels. They are quoted verbatim from IMPIC and
rendered verbatim, in Portuguese, on both language trees. The FAQs and the terms
page also stay Portuguese, behind an English note: they are long-form writing
about Portuguese law, and a rough translation would be worse than none.

## Company lookup

The procurement data says nothing about a supplier beyond its name and NIF, so
`/api/v1/companies/{nif}` fills part of that gap from outside and caches every
answer, misses included, in Postgres.

| Field | Source | Caveat |
|---|---|---|
| CAE activities | SICAE (Ministry of Justice) | authoritative |
| Registered address | VIES, via aggregator | absent when the VAT number is inactive |
| Forma jurídica | **read off the firm name** | Portuguese names must carry the suffix, so "Unipessoal" is detectable for free |
| Founding year | first published act | see below |
| Capital social, headcount | none | not published free by anyone |

The founding year is the year of the **first act published in the commercial
register, and that register only begins in 2006**. GERTAL, incorporated 1973,
comes back as 2006. So `founded_year <= 2006` means "2006 or earlier", never a
date, and the interface renders it that way. Only 2007 onward is a real
founding year.

The lookup is **off by default** (`COMPANY_LOOKUP_ENABLED=false`) because it
calls out to the internet. It tries the aggregator first, falls back to parsing
SICAE, and a registry being slow or down never blocks the page.

Sources that would give better coverage but whose terms forbid automated access
and redistribution were deliberately not used. `CLAUDE.md` records which ones
and why, so the question does not get relitigated in a pull request.

## API

Everything is served under **`/api/v1/`**. The version prefix is applied in
`create_app` from `API_VERSION_PREFIX`, not in nginx (nginx proxies `/api/`
generically), so shipping a `/v2` alongside `/v1` touches one file.

`/health` sits outside the prefix and outside the schema: the container
healthcheck is orchestration, not API surface, and must not move when a new
version arrives.

Interactive docs at `/api/docs`.

## Layout

```
core/     contratos_core   ORM models, settings, session factory, concelho
                           and district tables, CPV sectors            (shared)
ingest/   contratos_ingest sources/{impic,apiaberta,autarquicas}, repository, CLI
api/      contratos_api    routers, services/{scoring,company}, repositories
web/      SvelteKit + ECharts, built static and served by nginx
nginx/    reverse proxy /api -> api:8000, SPA fallback, security headers
docker/   api.Dockerfile, ingest.Dockerfile, web.Dockerfile
scripts/  build_districts.py
```

Each component is its own build context, so its `.dockerignore` actually
applies: nested ignore files are ignored when the context is the repo root. The
shared `core` package and the nginx config reach their images through compose
`additional_contexts` rather than by widening the context back to the root.

Adding a source means subclassing `ContractSource` and yielding
`ContractRecord`s. Nothing else changes.

The ORM owns the schema; **ingest bulk-loads with `COPY`** into unlogged staging
tables and upserts. Pushing millions of rows through ORM instances is ~50x
slower and buys nothing.

## Running it locally

Development uses docker compose. Production uses podman; see below.

```bash
cp .env.example .env          # set POSTGRES_PASSWORD, MUNICIPALITY_NIFS, IMPIC_YEARS
docker compose up -d db api web
docker compose --profile tools run --rm ingest impic      # bulk history
docker compose --profile tools run --rm ingest entities   # supplier countries
docker compose --profile tools run --rm ingest mandatos   # autárquicas results
docker compose --profile tools run --rm ingest delta      # apiaberta top-up
```

Then open <http://localhost:8080>.

`MUNICIPALITY_NIFS` scopes the ingest and takes a comma-separated list; **empty
means the whole country**. `IMPIC_YEARS` takes `2012-2026` or `2024,2025` or
empty for everything IMPIC publishes. Several indicators need more than one year
to mean anything: with a single year loaded, "dinheiro a empresas novas" is
correctly `N/A` rather than wrong.

To widen the scope, ask the bulk file for the NIFs instead of hunting them:

```bash
docker compose --profile tools run --rm ingest nifs Lisboa Porto peninsula-setubal
```

It reads the most recent IMPIC year, resolves each buyer name to a concelho and
prints a ready `MUNICIPALITY_NIFS=` line. It accepts district names, concelho
names, and `peninsula-setubal` for the nine concelhos of the Península de
Setúbal. It touches neither the schema nor the database.

Tests:

```bash
pip install -e './core[test]' -e ./api -e ./ingest   # once, in a venv
pytest                                               # all three packages
cd web && npm run check        # svelte-check plus the message parity check
```

`test_router_calls.py` binds every `repo.x(...)` call in a router against that
method's real signature, with no database and no server. Run it after touching a
router or a repository: nothing else checks that seam, and a mismatch there once
returned 500 on every contracts request in production.

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first. It is short, and every rule in
it is there because breaking it already produced a wrong number.

```bash
git config core.hooksPath .githooks
```

One command per clone, because git will not enable version-controlled hooks on
its own. The hook refuses a commit that carries a secret, an environment file, a
file over 2 MB, or an em dash in source we wrote ourselves. `gitleaks` runs from
a pinned Docker image when no local binary is on PATH, so there is nothing extra
to install.

The same scan runs in CI over the **full history** on every push and pull
request and weekly on a schedule, because a hook is opt-in per clone and
`--no-verify` bypasses it. CI is what actually gates the branch.
`.gitleaks.toml` extends the bundled rules rather than replacing them, so
upstream keeps adding providers for free. The allowlist is small on purpose:
`.env.example` placeholders, the fonts and geometry, and Portuguese NIFs, which
are public register identifiers and the primary key of this whole project.

Security reports go through GitHub's private vulnerability reporting; see
[`SECURITY.md`](SECURITY.md). A wrong contract in the register is not a security
issue and is not our bug: it gets corrected at IMPIC, and appears here on the
next ingest. A wrong calculation on our side is a bug and we want it.

By opening a pull request you agree your contribution ships under AGPL-3.0 (code)
and CC-BY-4.0 (content). There is no CLA.

## Deployment

Authoritative files, each carrying its reasoning inline:
[`docker-compose.prod.yml`](docker-compose.prod.yml),
[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml),
notes kept privately, since they describe one specific machine.

One small VPS running a distribution with **SELinux
enforcing**, bootstrapped once and then never touched by hand.

**Rootless podman, not docker.** No daemon, no root-owned socket, no
orchestrator or build agent on the box. `podman compose` needs the docker
compose v2 binary as its provider: `podman-compose` does not implement
`depends_on: {condition: service_healthy}` or `service_completed_successfully`,
which is what orders the schema one-shot ahead of the API.

**Zero inbound ports.** `cloudflared` runs as a container in the stack and dials
out, so public traffic returns down that connection. The box holds no
certificate, runs no reverse proxy of its own, and the host firewall answers on SSH
only. Do not add a `ports:` mapping to a production service.

**Images live on GHCR**, built by GitHub-hosted runners and tagged by commit
SHA. Podman runs OCI images and does not care what built them. The deploy is an
SSH session: render the stack `.env` from the GitHub `production` Environment,
pipe it and the compose file to the box, pull the pinned tags, `podman compose
up -d`, then poll the API's health until it is healthy or fail the job.
`up -d` returns as soon as the containers exist, which says nothing about
whether the API can reach the database.

Deploys fire on **`main` only**, plus manual dispatch. Every secret and every
non-secret var lives in the GitHub `production` Environment; the non-secret half
arrives as one block in `vars.APP_ENV`, so adding a tunable is a UI edit rather
than a workflow change.

`restart: always`, not `unless-stopped`: podman has no daemon watching restart
policies, and `podman-restart.service` only picks up `always`.

Every container runs **non-root with a read-only root filesystem**, all
capabilities dropped and `no-new-privileges`. Writes go to tmpfs, except the
ingest's multi-hundred-MB downloads, which use the `ingestdata` volume. SELinux
stays enforcing: every mount is a named volume or a tmpfs, which podman labels
on its own, and any bind mount added later needs `:Z`.

No Node runtime in production: the frontend is a static build served by nginx.

Hardening that is easy to undo by accident:

- **The rate limiter needs the real client IP.** Behind the tunnel every request
  arrives from the cloudflared container, so `limit_req` keyed on
  `$binary_remote_addr` would throttle the entire internet as one visitor.
  `NGINX_TRUSTED_PROXY` is the stack network subnet and nothing else, and
  `NGINX_REAL_IP_HEADER` is `CF-Connecting-IP`. That pair matters: Cloudflare's
  edge always overwrites `CF-Connecting-IP`, so a client cannot forge it, while
  `X-Forwarded-For` is appended to and a client that sends one can walk the
  limiter off any address it likes.
- `nginx/security-headers.conf` is `include`d in **every** location that adds a
  header of its own. nginx's `add_header` replaces the inherited set rather than
  extending it, so deduplicating those includes silently drops the headers.
- Dotfiles and editor leftovers return **404, not 403**, because a 403 confirms
  the path exists, and they answer with a ten-byte body. `return 404 "";` with a
  body bypasses `error_page`, which is what keeps probe traffic cheap. Only the
  two failures a person can actually land on, a rate limit and a dead upstream,
  get a designed page.
- `proxy_intercept_errors off` on `/api/` is deliberate: a 404 from the API is
  JSON and must stay JSON. Only nginx-generated failures get the HTML page.
- `server_tokens off` hides the nginx version, but stock nginx cannot drop the
  `Server` header itself. Cloudflare replaces it with its own on the way out, so
  in production it never reaches a reader. Upstream is already silent: uvicorn
  runs with `--no-server-header`.
- CSP is split: SvelteKit emits the page policy as a meta tag with a hash for its
  one inline bootstrap script (so no `unsafe-inline` for scripts), and nginx adds
  `frame-ancestors`, which a meta tag cannot carry.

Images pin the major/minor and let the Alpine patch float:
`python:3.13-alpine`, `node:24-alpine`, `nginxinc/nginx-unprivileged:1.31-alpine`,
`ghcr.io/astral-sh/uv:0.12.17`, `postgres:18-alpine3.24`.

Postgres mounts its volume at `/var/lib/postgresql` with
`PGDATA=/var/lib/postgresql/pgdata`, not at `/var/lib/postgresql/data`. The
deeper path does not exist in the image, so the volume gets no copy-up, stays
root-owned and uid 70 cannot write to it. That is what an earlier root-owned
init container was papering over.

Python deps install with **uv** in the build stage only; it never reaches the
final image.

`typescript` is pinned `^6.0.3`: `svelte-check@4.7.6` peer-requires `^5 || ^6`,
so bumping to TypeScript 7 breaks `npm ci`.

`SQLAlchemy` is pinned `>=2.0.54,<2.1.0` on purpose: **2.1.0 has no stable
release**, only release candidates, so an automatic bump to `>=2.1.0` makes the
build unresolvable.

The ingest rotates a pool of desktop Chrome user agents with matching `Accept`
headers, overridable via `USER_AGENTS` (pipe-separated).

## Deliberate omissions

- **No Redis.** The dataset moves once a night, so responses carry
  `Cache-Control` and the browser/CDN handle it. Add Redis only if hot keys ever
  outgrow an HTTP header.
- **No Alembic.** The ORM creates the schema and a one-shot runs `create_all` on
  every deploy. Add migrations when the schema first needs to change in place
  with data you care about: `create_all` adds missing tables, never missing
  columns.
- **No real scheduler.** The ingest runs as `while :; do ...; sleep N; done`
  loops in the stack. That cannot express a wall-clock time, it drifts, and a
  restart resets it. The upgrade is podman quadlets driven by systemd timers
  with `OnCalendar` and `Persistent=true`. Do that when the schedule starts
  mattering.
- **No materialized views.** Aggregates run in tens of milliseconds at current
  scale. Add them when a query actually gets slow, not before.
- **No `uv.lock` yet.** uv resolves from the `pyproject.toml` pins at build time.
  Add `uv lock` once you want byte-identical rebuilds.
- **No pagination cursors.** The contracts list pages by `limit`/`offset` and
  dedupes by id on append, which is enough at this scale. Swap for a keyset
  cursor when offsets get deep enough to hurt.
- **No i18n library.** Two flat objects and one `{x}` substitution is the whole
  of what a few hundred strings needs.

## Language and design

Portuguese is the source language, post-AO90 and **with accents** (`setor`,
`objeto`, `ação`). **No em dashes**; a missing value renders `N/A`. No
statistical term ever appears in the interface: every indicator is explained in
plain language, because the reader is a resident, not an economist.

The look is a Portuguese street-festival poster: warm cream ground, azulejo
lattice, hard offset shadows, chunky display type.

The brand palette is not the chart palette. Festival yellow fails as a data
colour on cream (lightness 0.86, contrast 1.4:1), so charts use a separately
validated set in fixed order, never cycled, five then "Outros". Party colours
are exempt, because a reader who follows an election night already knows PS is
rose and PSD is orange. Severity always ships with a written label, never colour
alone, and an unmeasurable signal renders grey with no bar rather than borrowing
the green of a clean one.

`CLAUDE.md` carries the full design system and the reasoning behind each rule.

## Disclaimer

**Nothing here accuses anyone of a crime.** Ajuste direto is a legal procedure
and often the sensible one. The indices measure observable signals, and the
interface says so on every page. The underlying data is the official BASE/IMPIC
register, republished unmodified; errors and omissions in the original appear
here unchanged, and corrections belong with the publishing body.
