# Onde Vai Parar

Satirical analytics over Portuguese public contracts, at **ondevaiparar.pt**.
One municipality today (Odivelas by default in `.env.example`), built to take
all 308.

`ondevaiparar.com` is registered and 301s to the `.pt` at Cloudflare. The `.pt`
is canonical everywhere: `PUBLIC_SITE_URL`, the canonical link, the hreflang
pair, the sitemap.

**The repo is called `contratos-publicos`, not the brand.** That is deliberate.
The name describes what the thing reads, so the next rebrand is a copy edit in
`messages.ts` and a DNS record, not a repository rename that breaks every clone,
every image path on GHCR and every link anyone ever posted. The brand lives in
`common.site`; the repo name is allowed to outlive it.

Public on GitHub: <https://github.com/kreativermario/contratos-publicos>.

## Hard rules

**Licensing.** Code is **AGPL-3.0** (`LICENSE`), the content we wrote is
**CC-BY-4.0** (`LICENSE-CONTENT`), and the upstream registers are neither: they
belong to the bodies that publish them and are listed in `NOTICE`.

AGPL was chosen for one specific reason. This project's defence is that its
method is auditable: anybody can check what each number counts. AGPL is the only
copyleft that reaches a *hosted* service, so a modified deployment owes its
readers the same audit. The consequence is section 13: the deployed site must
offer its source to network users, which is why the footer links to the
repository. **That link is not decoration and must not be removed.**

Contributing, reporting and conduct live in `CONTRIBUTING.md`, `SECURITY.md`,
`CODE_OF_CONDUCT.md` and `.github/ISSUE_TEMPLATE/`. Read them rather than
restating them here. The short version worth knowing before touching anything:
a wrong number in the register is not our bug and gets fixed at IMPIC, and a
wrong number in our arithmetic is.

**Language: Portuguese is the source, English is a translation.** It used to be
Portuguese only. Now the site ships in two, Portuguese at `/` and English at
`/en/`.

European Portuguese, **with accents**: `índice`, `análise`, `número`, `média`,
`período`, `código`, `são`, `não`. Post-AO90 spelling: `Arquitetura` not
`Arquitectura`, `ação` not `acção`, `elétrico` not `eléctrico`, `teto`/`limite`
not `tecto`, `setor` not `sector`, `objeto` not `objecto`. The English word
`sector` stays in code identifiers; only the rendered label changes.

**Never use em dashes (—) in user-facing text or in prose.** Use a comma, a
colon, parentheses, or a full stop. For a missing value render `N/A`, never a
dash glyph: `N/A` replaced `s/d`, which readers did not recognise.

**The API carries no prose at all, and this is a rule, not a migration note.**
Anything a reader sees is a key. One JSON payload serves both languages and it
is cached for an hour, so a Portuguese sentence in `/score` prints Portuguese on
the English pages and keeps printing it until the cache expires. The API ships
`clean`, `ok`, `signal.ajuste_direto`; the wording lives in `messages.ts`, in
each language. `api/tests/test_scoring_keys.py` fails if a sentence reappears:
it rejects any value containing a space, a full stop or a comma.

**Nothing is hardcoded.** Every tunable is an environment variable; see
`.env.example`. `MUNICIPALITY_NIFS` scopes ingest and **empty means the whole
country**. No municipality name, NIF, year, legal threshold or hostname belongs
in code.

**Nothing here accuses anyone of a crime.** Ajuste direto is a legal procedure.
The indices measure observable red flags, and the UI says so. The footer
disclaimer is `DISCLAIMER` in `scoring.py`, five keys worded in `messages.ts`:
it covers provenance and limits and is the same for every municipality. Why one
signal is unmeasurable *here* belongs on that signal's card, not in the
disclaimer.

## Layout

```
core/     contratos_core    ORM models, settings, session factory, CPV sectors,
                            concelho/district tables
ingest/   contratos_ingest  sources/{impic,apiaberta,autarquicas}, repository, CLI
api/      contratos_api     routers, services/{scoring,company,flags}, repositories
web/      SvelteKit + ECharts, built static, served by nginx
nginx/    reverse proxy, security headers, SPA fallback
docker/   api.Dockerfile, ingest.Dockerfile, web.Dockerfile
scripts/  build_districts.py
```

Each component is its own build context so its `.dockerignore` applies; shared
`core` and the nginx config arrive via compose `additional_contexts`, and via
`build-contexts` in the deploy workflow, which is the same thing spelled the
Buildx way.

## The two languages

PT at `/`, EN at `/en/`, from one static build and one API payload.

**The route tree is `[[lang=lang]]` at the top**, an optional parameter with a
matcher in `web/src/params/lang.ts` that accepts only `"en"`. The matcher is not
optional: without it SvelteKit binds `lang="faqs"` for `/faqs` and renders the
landing page.

**Every string lives in `web/src/lib/messages.ts`**, two flat objects with the
same keys (521 today), no i18n dependency. One lookup and one `{x}` substitution
is the whole of what this needs; a library would buy pluralisation rules and
message extraction, neither of which this site uses. `t()` reads the page's
language, `tl(lang, key)` forces one, `maybe()` returns empty rather than the
key for optional strings. A missing key falls back to Portuguese and then to the
key itself, which is ugly on screen and therefore gets fixed.

`web/scripts/check-messages.mjs` enforces both halves of that: the two bundles
carry the same keys, and every key the source asks for exists, including the
keys that only ever arrive from the API and are looked up through a template
string. It is wired into `npm run check`, because `svelte-check` reads types,
not strings, and would never notice.

`web/scripts/check-seo.mjs` rides the same hook, over `$lib/seo.ts`: node 24
strips the types, so the check imports the module the site actually ships
rather than a copy of its regex.

`web/scripts/prerender.mjs` runs from `npm run build`, after `vite build`. It
reads the municipality list from `PRERENDER_API` and writes one real HTML file
per município per language tree, carrying the title, description, canonical,
hreflang and JSON-LD a crawler needs before any JavaScript runs. It also owns
`sitemap.xml`, because it is the only thing that knows which pages it wrote,
and it asserts that every URL it lists exists on disk.

nginx needs nothing for this: `try_files $uri $uri/ /index.html` already
resolves `/municipio/506811570/` to that directory's `index.html`. Production
is unchanged, the container stays read-only, and there is still no Node runtime
on the box.

Two rules it must keep. The API being unreachable writes the static-only
sitemap, prints a warning and exits 0: a data source being down must not block
a deploy, and a smaller sitemap must never ship in silence. And only
slow-moving facts go in the prerendered head, never a euro total, because these
files are regenerated on deploy and nothing else.

It cannot import `messages.ts` or `format.ts`: both reach `$app/state`, which
does not exist under plain node. It reads the message bundles as text, the way
`check-messages.mjs` does, and `shortMunicipality` lives in `seo.ts` for this
reason rather than in `format.ts` where it belongs by subject.

**What is never translated:** contract descriptions, supplier names, buyer
names, procedure names, council names and CPV labels. They are quoted verbatim
from IMPIC and are rendered verbatim, in Portuguese, on both trees.
`common.verbatim` is where the English pages say so, and it is deliberately
empty in Portuguese so nothing renders.

**FAQs and Termos stay Portuguese** behind `ptOnly.note`. Both are long-form
writing about Portuguese law and about this site; a half translation of the
glossary inside them would be worse than none.

`<html lang>` is set from the route in `+layout.svelte`, because the shell is
one static file for both trees and cannot carry it at build time. Get it wrong
and a screen reader reads the English pages as Portuguese.

## API surface

Everything is served under **`/api/v1/`**. The version prefix is applied in
`create_app` from `API_VERSION_PREFIX`, not in nginx: nginx proxies `/api/`
generically and strips it, so shipping a `/v2` alongside `/v1` is a change in
`app.py` and nowhere else.

`/health` is deliberately outside the prefix and out of the schema. The
container healthcheck is orchestration, not API surface, and must not move when
a new version arrives.

`root_path` comes from `API_ROOT_PATH` so the docs at `/api/docs` request
`/api/openapi.json` rather than `/openapi.json`, which the SPA fallback would
otherwise answer with `index.html`.

## Error pages

Three tiers, because not every failure has a reader.

**Probes get nothing.** Dotfiles, backup extensions, missing hashed assets and
non-GET requests answer with a ten-byte body. `return 404 "";` with a body
bypasses `error_page` entirely, which is the whole trick. A person never sees an
nginx 404 anyway: unknown paths fall through to the SPA.

Two layers remain, because they fail at different moments.

`web/src/routes/[[lang=lang]]/+error.svelte` handles anything the app reaches:
an unknown route (nginx returns the SPA shell with 200, the router then renders
this) or a failed load. It uses the design tokens like any other page.

`web/static/erro-429.html` and `erro-5xx.html` are served by nginx for the only
two failures a person actually lands on: a rate limit and a dead upstream. They
are **standalone on purpose**, carrying their own inline CSS, because an error
page must render when everything else is broken. They are `internal`, so nobody
can navigate to them directly.

`proxy_intercept_errors off` in the `/api/` location is deliberate: a 404 from
the API is JSON and must stay JSON. Only nginx-generated failures, such as a
dead upstream, get the HTML page.

## The two indices

`risk_index` is the unweighted mean of whatever is measurable.
`satirical_index` is the same numbers with the more revealing ones weighted
heavier. They pair on the wire and are computed from the same aggregates, so
the joke can never disagree with the data.

`satirical_index` returns `{score, band, tone, units}` and **no prose**: `band`
is `clean | fishy | blatant`, `tone` is `ok | warn | critical`, and the client
words one and paints the other. Two fields rather than one, so the words and the
colour cannot disagree. Its rendered label is **Malandrómetro**
(`muni.satireIndex`). The word "cunha" survives in body copy on purpose: it is
what a Portuguese reader actually calls the thing.

**Every scored signal is a percentage of the money.** That is what makes the
mean legitimate. An earlier version averaged "54% of tenders had one bidder"
with "9% of the money skipped a tender"; those are different quantities and
adding them produced a number that meant nothing. Count-shaped measures still
matter, so they live in `CONTEXT_FLAGS`, are rendered under "Contexto", and are
never folded into the index.

A signal that is not measurable in the loaded window is `None` and drops out of
the mean. It must never be scored as a zero: a year-to-date extract that stops
in September has no December, and counting that as "0% december rush" silently
deflated the index. Same for the newcomer share before enough years are loaded.

**No statistical term ever appears in the interface.** Every indicator is
explained under `signal.<key>` and `signal.<key>.blurb` in `messages.ts`, in
plain language: what it counts and why it matters. The reader is a resident, not
an economist. The same goes for `CPV`, which is spelled out wherever it is
shown.

Concentration is a Herfindahl index over every supplier, not a top-3 share:
68% held by three of six firms and 68% held by three of 232 are not the same
market, and only HHI says so.

## Contract flags

`services/flags.py`. Patterns worth a second look on one contract row, shown as
chips under the description. Every one of them is legal and none is a finding.

**The chip states the fact, with its numbers. It never names a category.** This
is the rule the module exists to serve, and it was arrived at the hard way: a
chip reading "às fatias" or "fracionamento" tells a reader nothing and sends
them hunting for a tooltip, while "3 contratos, todos abaixo de 20 000 €" is
understood on sight by anybody. So a flag travels as `{key, data}`: the key
picks the sentence out of `messages.ts` and `data` fills its `{placeholders}`.
The API still ships no prose, it ships enough for the sentence to be specific.
The tooltip carries the caveat, never the meaning.

Consequences worth keeping:

- **Money crosses the wire as a number, never formatted.** `Flags.svelte` knows
  which keys are money (`limit`, `gap`, `value`) and runs `eur()` at render. A
  formatted amount is prose and would print Portuguese euros on the English
  pages, and keep printing them for an hour, like any other cached string.
- **`estreante` counts from the first public contract, not from incorporation.**
  No free source publishes a founding date, so the sentence reads "primeiro
  contrato público há {months} meses" and the tooltip says the firm may be much
  older. "Abriu há 4 meses" would be a claim this data cannot support.
- **`fechada` is about today.** The register reports current status, so the
  sentence must not imply the firm was closed when it signed.
- **The chips are Archivo, not the display face.** They carry sentences now, and
  Bowlby One set small and uppercase was legible as one word and a smudge as
  six. They sit under the description, not in the value column, which is two
  words wide and right-aligned.

**Rules that need more than one row read a `FlagContext`**, filled once per page
by `flag_context` rather than once per row: the supplier's first appearance
anywhere, its record with this buyer, which NIFs the register no longer lists as
active, and the slice groups. `nunca_a_concurso` is scoped to one buyer and is
therefore silent on a supplier's own page, where the rows span every câmara the
firm works for.

`slice_groups` is grouped in Python, not SQL, on purpose: the rule is a shape
(same buyer, same firm, same kind of work, close in time, each under a ceiling
the run as a whole clears) rather than a filter, and as one statement it is
unreadable and untestable. **It reads every contract those firms hold, never the
page on screen.** Grouping the page made the flag depend on pagination and on
the sort: awards either side of a page boundary were invisible, and the same
contract carried the chip under one sort and not another. The buyer belongs in
the key too, or one firm doing three small jobs for three different câmaras
reads as one split contract.

`api/tests/test_flags.py` is the only thing watching any of this. The rules used
to live in a router, where nothing could reach them without a server and a
loaded database, so nothing tested them at all; every one is a claim about
somebody's contract, which is the last place to find a boundary is off by one.

## Data

Two contract sources. **IMPIC bulk** on dados.gov.pt is authoritative: 35
fields, 2012 to now, no rate limit. **apiaberta** is a lossy 6-field mirror
behind 30 req/min, used only for deltas between bulk refreshes. A `delta` row is
thin (no `concorrentes`, no CPV, none of the fields the indices score from), so
`impic` is a correction pass rather than a bigger `delta`.

A third source, **autárquicas results** (`sources/autarquicas.py`), is
independent of the contracts: it covers all 308 municípios regardless of what is
loaded, and answers who held each câmara when a contract was signed.

Limits that must stay visible in the UI:

- **The procurement data has no supplier addresses.** `entidades.json` has
  country only, and `localExecucao` is where the work happens, not where the
  firm is based. A registered address does exist outside this data: VIES
  publishes one, and the company lookup below surfaces it.
- `concorrentes` covers about 42% of contracts. Every single-bidder figure is
  reported against that denominator, never the full set.
- `PrecoTotalEfetivo` is populated for about 6% of rows, so cost-overrun
  analysis is impossible. It is deliberately not in the schema.
- A contract may span several concelhos, so the map sums to more than total
  spend. Say so next to the map.
- **The mandate data is the provisional count.** `eleicoes.mai.gov.pt` publishes
  the escrutínio provisório; the legally official record is the CNE Mapa Oficial
  in Diário da República, as a PDF. The UI has to say which one it is showing.
  There is no documented API and no versioning behind those numbers, which is
  why they are stored rather than fetched live and why every parser fails loudly
  instead of guessing. Five site generations, five shapes.
- **The CCP reform of 2017-08-30 moved the numbers more than any election did.**
  A mandate timeline that does not say so invites the reader to attribute the
  drop in ajuste direto to whoever took office that October.
- **There is no free, official, programmatic route to a company's true
  incorporation date.** The authoritative record is the Certidao Permanente,
  which is paid. `empresadb.pt` gives a year, but it is the year of the *first
  published act*, and the register only starts in **2006**: GERTAL, founded
  1973, comes back as 2006. So `founded_year <= REGISTER_FLOOR` means "2006 or
  earlier", never a date, and the UI renders it as such. Only 2007 onward is a
  real founding year.
- **Employee count is not available for free at all.** Not as a number, not as
  a size band. Racius puts it behind an 11 EUR report, eInforma sells it, and
  IES headcount is published only as INE aggregates under statistical secrecy.
  Do not invent a proxy and call it headcount.
- **There is no automatable per-company source, and this is settled.** Checked
  in full: `racius.com` forbids non-UI access *and redistribution* in its terms
  (its `robots.txt` allows crawlers, which is not what binds); `contribuinte.pt`
  forbids it too and is wrong besides; the `dados.gov.pt` dataset "Atos do
  registo comercial" (DGPJ, CC-BY) looks ideal until you read its schema, which
  is *"Dimensões: Ano, tipo de ato. Métricas: Número de atos"*, with no company
  dimension at all; and `publicacoes.mj.pt`, the official publication of company
  acts and the source those resellers resell, has a NIF search marked "critério
  preferencial" but answers every automated submission with **"Por favor, efetue
  a Validação"**, a human-validation challenge. Defeating it is both an
  anti-automation circumvention and a terms breach. What is left is SICAE plus
  VIES plus **nif.pt**, which has a documented API and issues a free key on
  request. Headcount stays out; so does capital social, see below.
- **nif.pt is the quota'd source and is never in the request path.** It is the
  only free API carrying two things nothing else here does: whether the firm is
  still `active`, and the concelho it is registered in, which is the only
  answer this project has to "local firm or outsider" (the procurement data has
  no supplier address at all). The free key allows 1 request a minute, 100 a
  day, 1000 a month, so a public request must never reach it: it would either
  block for a minute or spend the day's budget on whoever clicked first.
  `CompanyLookup.allow_nifpt` is `False` everywhere except
  `python -m contratos_api.backfill`, which paces itself at
  `COMPANY_NIFPT_INTERVAL` and stops at `COMPANY_NIFPT_DAILY`. Empty key
  disables it entirely.
- **The backfill spends its quota on the suppliers the indices already point
  at**, not alphabetically: uncontested money first, where "uncontested" is the
  project's existing soft-win definition (an ajuste direto, or a tender the firm
  was alone in) and not a new suspicion score invented for this. A NIF already
  in `company_profiles` is skipped whether it was a hit or a miss, because the
  miss is cached on purpose and re-asking a quota'd register for a NIF it has
  already denied is the one thing that budget cannot afford.
- **nif.pt publishes capital social, and we still drop it.** So do the contacts
  it returns. Capital social nothing here scores from, and an email and a phone
  number belong to somebody: storing them would make this a directory of people
  rather than of contracts. Add capital only when a signal actually reads it.
- **Do not scrape racius.com or contribuinte.pt.** Both forbid non-UI access
  and redistribution in their terms, and contribuinte.pt returns `0 EUR` of
  capital social for a company with 9.6M.
- **Do not build anything from the AT or Segurança Social devedores lists.**
  They look ideal (NIF, name, debt band, no auth) but the page itself states,
  under CNPD Autorização 676/2006, that the data must not be "reproduzida ou
  utilizada para fins diferentes... designadamente para a organização de
  ficheiros informáticos". A database is exactly the forbidden use.
- **INE has no per-company data.** Its JSON API is indicator-only: values keyed
  by year, NUTS region and CAE division, with no NIF or entity dimension. The
  same goes for the Justice statistics API, which counts registry *acts*, not
  companies. Worth knowing that the block is institutional rather than legal:
  Lei 22/2008 art. 6.º exempts data on pessoas coletivas from statistical
  secrecy when published in bands, so INE could publish it and simply does not.
- **IMPIC does not publish the NIF of a natural person.** Every NIF that
  reaches us starts with 5 or 9, so `is_person_nif` alone can never fire on this
  data: the people are precisely the suppliers with *no* NIF. The person flag is
  therefore a missing NIF plus a name that reads as a name (`looks_like_person_name`:
  three to seven plain words, no digits, no trading punctuation, no activity
  noun). Oeiras alone has Francisco Simões Gomes at 1,08 M EUR over three
  contracts. The flag says "pessoa" and nothing more, because that is all it
  knows.
- **A person is read off the NIF, never off the name.** The tax register keys
  it: 1 to 3 and 45 are natural persons, 5 a company, 6 a public body. Reading
  the *name* for the absence of a legal form flagged "TECNORÉM, S.A" as a
  person, because `S.A` without the trailing dot was missing from `_FORMS`.
  Worse, the `" sa"` needle had no trailing boundary and matched "dos SAntos",
  so Maria dos Santos Ferreira was read as a Sociedade anónima. The normaliser
  now **deletes** dots rather than spacing them (spacing turns `S.A.` into
  `s a`, which matches nothing) and every short needle carries both spaces.
- Legal form is read off the firm name (`legal_form_from_name`), because
  Portuguese firm names must carry the suffix. It costs nothing and is what the
  paid registries report anyway. "Unipessoal" has to be matched before "Lda".
- **"Empresa nova aqui" needs three conditions together**, in
  `newcomer_verdict`. The firm's first appearance anywhere in the contract
  record must be (1) knowable, (2) recent *relative to the end of the period
  being read*, not to today, and (3) followed by a win here that came without
  competition: an ajuste direto, or a tender it was alone in. The measure stays
  censored: unless the loaded years already covered a full window before the
  debut, the flag is `None`, never `False`, so with a single year ingested every
  firm is correctly `None`. Dropping condition (2) is what left a firm whose
  first contract was in 2016 still labelled an estreante in 2026; dropping (3)
  flagged firms that had simply won an open tender.

The ORM owns the schema. Ingest bulk-loads with `COPY` into unlogged staging
tables and upserts; pushing millions of rows through ORM instances is about 50x
slower and buys nothing.

## Design

Portuguese street-festival poster. Warm cream ground, azulejo lattice, hard
offset shadows, chunky display type, rounded corners (`--radius: .625rem`,
keep the rounding).

```
paper #fff5d8   ink #240706     sangria #df2225
amarelo #f6ce00 azulejo #007ca6 manjerico #11ad32
display: Bowlby One   body: Archivo   (both self-hosted, CSP stays 'self')
```

**The poster system.** Three decisions, made once, applied everywhere:

- **Titles are a block, not an outline.** Cream letters on a solid ink inline
  box with a sangria drop (`.poster > span` in `app.css`). The earlier version
  filled the letters with cream and stroked them, so they came out hollow and
  the drop had no body to sit against. The block is an *inline* box so it wraps
  with the text, which means `box-decoration-break: clone` and enough leading to
  pay for the vertical padding twice: a padded inline box grows past its own line
  box, and at `line-height: 1` the lines of a two-line title sit on each other.
  The drop must also be smaller than the gap the leading opens, or line two's
  block paints over line one's shadow.
- **The divider is the four-colour stripe**, the same one under the nav. The 2px
  ink rule it replaced was too fine to be poster and too heavy to disappear.
- **One ink band per page**, on the section that answers the page's own
  question, with `--paper` and `--paper-3` alternating elsewhere. Everything on
  one cream from top to bottom is what made the pages read as bland. Severity
  and chart colours were validated on cream and are illegible on ink, so the
  dark band carries its own set (`--on-ink-*`).

**And the plate fills are a third set.** A row of totals reads as one object
only if every label is the same colour, and the label has to be white because
sangria and azulejo cannot hold ink. Festival yellow holds white at 1.53:1, so
the yellow plate is `--plate-amber` (`#a06a00`, the project's own `--sev-warn`)
and the green is manjerico taken down to `#0a7a24`. All four clear 4.5:1 with
white. Do not put `--amarelo` or `--manjerico` behind white text.

**The brand palette is not the chart palette.** Festival yellow fails as a data
colour on cream (lightness 0.86, contrast 1.4:1). Charts use a separately
validated set, fixed order, never cycled, max five then "Outros":

```
#c1121f  #0077b6  #a06a00  #8e3bb0  #0a6e3a
```

Before changing any chart colour, re-run the validator:
`node <dataviz skill>/scripts/validate_palette.js "<hex,…>" --mode light --surface "#fff5d8"`.
Green and amber collide under protanopia; do not put them adjacent.

**Party colours are exempt**, in `web/src/lib/parties.ts`. A reader who follows
an election night already knows PS is rose and PSD is orange, and inventing
different hues would cost more in recognition than it could gain in harmony.
They are darkened enough to hold on cream; the pale originals, CDS sky blue in
particular, fail badly on `#fff5d8`. The chart palette exists for series that
carry no prior meaning, which these do.

Severity is `ok / warn / serious / critical` and always ships with a written
label, never colour alone. A signal with no value renders "não medível" in grey
with no bar: an unmeasurable signal must never borrow the green of a clean one.

The Malandrómetro verdict carries its own `tone` so the words and the colour
cannot disagree: clean reads green and says so, blatant reads red. Money is also
counted in bifanas, at `BIFANA` euros each, and in annual minimum wages.
Deliberately not per capita: no population figure ships with the contract data,
and inventing one would undermine the serious index next to it. Newcomer
suppliers are drawn as diamonds in the graph for the same reason the verdict
carries a tone.

Bowlby One carries no `€` glyph, so a currency string set in the display face
splits mid-run and the symbol lands in the fallback. `eurShortParts()` returns
the amount and the unit separately; the unit goes in a `.unit` span (Archivo
800). There is no decorative emoji layer; it was tried and removed.

## Gotchas that already bit

- **`postgres:18-alpine` declares its VOLUME at `/var/lib/postgresql`, not
  `/var/lib/postgresql/data`.** A fresh named volume inherits the ownership and
  mode of the image directory it mounts over, so mounting the deeper path, which
  the image does not have, skips the copy-up: the volume stays `root:root 0755`,
  uid 70 cannot write, and postgres will not start. That is what the old root
  `db-init` one-shot was papering over. Mount at the declared path with
  `PGDATA=/var/lib/postgresql/pgdata` and the volume arrives owned 70:70. This is
  engine independent, so dev (docker) and prod (podman) both got the same fix and
  cannot drift.
- **Behind a tunnel, every request arrives from one address.** nginx `limit_req`
  keys on `$binary_remote_addr`, so without the real_ip module it throttles all
  visitors as a single client: the door is held open for the first arrival and
  shut on everyone else. Trust the stack subnet **exactly**, never `0.0.0.0/0`,
  and read `CF-Connecting-IP`. The header choice is the security half:
  Cloudflare's edge always *overwrites* `CF-Connecting-IP`, so a client cannot
  forge it, while `X-Forwarded-For` is *appended* to, and with
  `real_ip_recursive` a client that sends one can walk the limiter off any
  address it likes.
- **The API is not worth protecting from scrapers; `/companies/` is.** The
  contract register is IMPIC's open data and the bulk file is faster to download
  than this API is to walk, so there is nothing there to steal, and AGPL plus an
  auditable method is the whole argument the project rests on: an API people can
  query is part of that, not a hole in it. `/api/*/companies/` is the exception.
  On a cache miss it fetches `sicae.pt` and `empresadb.pt` **synchronously, on a
  public unauthenticated request**, so somebody walking NIFs does not take our
  data, they make us hammer a public register from our address until it bans us
  from a source the site depends on. It carries its own `limit_req` zone,
  `30r/m` against the general `5r/s`. That zone is a `map` on `$uri` rather than
  a second `location`, because an **empty** key is not accounted by `limit_req`:
  every other URI maps to `""` and passes through, so one directive in the
  shared `/api/` block covers one path prefix without duplicating the proxy
  config. The version segment in the pattern is a wildcard, so a `/v2` is
  covered without editing nginx. `API_CORS_ORIGINS=*` defends nothing either
  way: CORS is a browser rule and every scraper ignores it.
- **A tab in a query parameter re-runs `load`.** SvelteKit tracks the whole URL
  as a dependency the moment a `load` reads `url.searchParams`, and the
  município page reads it for the year window. So `goto` on a tab switch
  refetched score, 120 suppliers, rivals, contracts, map cells, stats, mandates,
  the municipality list and the config, and blocked the navigation until all
  nine returned: the Rede tab looked like it was hanging. Tabs choose which
  already-loaded data to show and are not an input to any of it, so they use
  **shallow routing** (`replaceState` from `$app/navigation`), which updates
  `page.url` without re-running `load`. A deep link still reads the param on a
  real navigation.
- **A chart that is unsized when its option arrives never draws.** `Chart.svelte`
  refuses `setOption` on a box with no width or height, because zrender inverts
  the geo transform on every resize and `invert()` returns null for the singular
  matrix a collapsed box produces. Nothing retried, so a panel that was unsized
  at that moment kept an empty chart for good. The ResizeObserver is the only
  thing that knows when the box gained a size, so it now draws as well as
  resizes.
- **One static shell cannot carry a canonical link.** `app.html` is served for
  every route, so a canonical baked there told the index that `/panorama`,
  every município and every empresa page were all the same URL as `/`. The
  canonical and the hreflang pair are per route, in `+layout.svelte`, from
  `seoUrls()`. The og tags stay in the shell: unfurlers never run JS, and one
  preview for the whole site is the deliberate trade.
- **`build/index.html` is the fallback for every unresolved route**, which is
  the rule `web/scripts/prerender.mjs` is built around. It gets the site-wide
  `Organization` and `WebSite` graph and nothing else: no canonical, no route
  title, because it answers for `/empresa/500123456` and `/contrato/99` too.
  `build/en/index.html` is different and may be specific, because nginx resolves
  `/en` to it via `$uri/` and falls back to the root shell for anything deeper.
- **Prerendering turned paths into directories, and nginx redirects to those.**
  `try_files $uri $uri/ /index.html` served every unknown path the SPA shell
  because nothing matched. Once `prerender.mjs` writes
  `build/municipio/<nif>/index.html`, `$uri/` matches a *directory*, and nginx
  answers a directory with a **301 to the trailing-slash form** before serving
  its index. A reader refreshing `/municipio/505307685` was handed
  `http://ondevaiparar.com:8080/municipio/505307685/`: the internal listen port
  and whichever Host arrived, in a URL nothing answers on, because an absolute
  redirect is built from `$scheme://$host:$server_port`. Two fixes, both
  needed. `$uri/index.html` goes **before** `$uri/`, which serves the file with
  no redirect at all and keeps the one spelling the sitemap and the canonical
  already use, without the trailing slash. And `absolute_redirect off`, because
  any redirect this container generates behind a tunnel leaks 8080 the same
  way, and the next one will not be noticed either.
- **A `<button onclick>` is not a link, and that was the whole SEO problem.**
  The município picker rendered each council as a button, so there was no path
  a crawler could follow from the homepage to any `/municipio/<nif>`, and the
  sitemap listed four static paths. Those pages did not exist as far as an index
  was concerned. They are anchors now (`Landing.svelte`), which also buys
  `data-sveltekit-preload-data="hover"` for free. The supplier and contract
  tables were already anchors, so the crawl graph flows from there.
- **The `.com` default outlived its fix.** `vite.config.ts` was corrected to
  the `.pt`, and `docker/web.Dockerfile` and `deploy.yml` were not, so every
  production build baked the redirecting domain into every canonical, the
  sitemap and robots.txt. There is no `PUBLIC_SITE_URL` in the production
  environment, so those defaults are what actually shipped. Three places carry
  this default. Change one, check the other two.
- The favicon is `static/favicon.svg`, the poster gauge, and
  `apple-touch-icon.png` is that same file rasterised at 180px. They were an
  emoji data URI and an unrelated red gauge; a browser tab and an iOS home
  screen showing two different marks is the one place the brand is seen most.
- The default `PUBLIC_SITE_URL` in `vite.config.ts` is the **`.pt`**. A bare
  `npm run build` with the `.com` there baked the redirecting domain into every
  canonical, the sitemap and robots.txt.
- **BSD sed has no `\b`.** A word-boundary pattern silently no-ops on macOS
  rather than erroring, so a bulk rename looks like it worked and leaves every
  reference behind. Use literal patterns, or `[[:<:]]` / `[[:>:]]`.
- **`git mv` stages immediately.** A later `git commit` after `git add <specific
  paths>` still sweeps in whatever else is sitting in the index, including
  another process's staged renames. It matters when more than one agent works
  the same tree: check `git diff --cached --name-only` before committing.
- `pydantic-settings` JSON-decodes list fields from the env before validators
  run, so `API_CORS_ORIGINS=*` crashes. List fields use `NoDecode`.
- SQLAlchemy maps a bare `postgresql://` URL to psycopg2, which is not shipped.
  `Settings` rewrites it to `postgresql+psycopg://`.
- `func.left(col, 2)` renders a different bind parameter in SELECT and GROUP BY,
  and Postgres then refuses to group. Use `literal_column("2")`.
- Concelho names are not unique (Lagoa is in Faro *and* the Azores) and 87 of
  308 differ only by particle casing. The geometry file carries `key`/`dkey` for
  joining and a disambiguated `name` for ECharts.
- DICO splits the archipelagos per island (31, 32, 41..49) but the election
  sites publish each as one region, `LOCAL-300000` and `LOCAL-400000`. Fetching
  per island 404s, which is how 30 municípios went quietly missing on the first
  mandate run.
- tmpfs mounts and named volumes are created root-owned, and containers run as a
  non-root uid, so a tmpfs a container must write to needs `mode=1777`. **Not**
  `uid=`/`gid=`: those are Docker options, and podman's compose API rejects them
  with `unknown mount option "uid=70"` and never creates the container. Sticky
  and world-writable gets there anyway, since each uid writes its own files and
  cannot remove another's. A named volume needs none of this under rootless
  podman, which chowns a fresh one to the container's uid on first mount.
- `SQLAlchemy 2.1.0` has no stable release; pinned `>=2.0.54,<2.1.0`.
- `typescript` is pinned `^6`: `svelte-check@4` peers `^5 || ^6`, so TS 7 breaks
  `npm ci`.
- Multiple `ingest` runs share `/data`; downloads are named per PID so one run
  cannot delete another's file mid-read.
- FastAPI's `response_model` silently drops any field the schema does not
  declare. A new column reached the JSON as a missing key and the tile rendered
  `0 €`. Add it to `schemas.py` in the same commit as the query.
- A `<table>` keeps its min-content width even when its rows are `display:block`,
  so a mobile "stacked" table still scrolls sideways. The table and tbody both
  need `display:block`, and any `white-space: nowrap` on cell content has to be
  confined to the wide breakpoint.
- FastAPI behind nginx: `/api/` is proxied with the prefix stripped, so the
  docs page asked for `/openapi.json`, the SPA fallback answered with
  `index.html`, and Swagger UI reported "no valid version field". Fixed with
  `root_path` from `API_ROOT_PATH`.
- `Cache-Control: public, max-age=3600` is right for data that moves nightly
  and wrong the moment a deploy changes the JSON shape: a cached response
  without the new keys renders as zeros and empty sections. Every API request
  carries the SvelteKit build id so a new bundle never reads an old one's cache.
  The same cache is why the API must ship keys and not prose.
- **`create_all` creates missing *tables*, not missing *columns*.** On its own
  it silently ignores a table that exists but has drifted, which is how `status`
  and `county` reached production as columns the ORM had and Postgres did not,
  500ing every request that read them. `Database.create_all` now follows it with
  `add_missing_columns`, so the `migrate` one-shot the prod stack already runs
  ahead of the API brings columns up too, and there is no server to log into.
  It is **additive only** and refuses anything else by name: a NOT NULL column
  with no default has nothing to put in the existing rows, and a primary key
  cannot be introduced after the fact. A rename, a type change or a drop is
  still a real migration, and that is the point at which this gets swapped for
  Alembic. `core/tests/test_schema_sync.py` tests the decision without a
  database; the ALTER itself is two lines around it.
- `server_tokens off` hides the nginx *version*, but stock nginx cannot drop the
  `Server` header itself; that needs `headers_more`. In production Cloudflare
  replaces it with its own on the way out, so it never reaches a reader.
  Upstream is already silent: uvicorn runs with `--no-server-header` and nginx
  also `proxy_hide_header`s it.
- Google's Bowlby One ships 13 glyphs whose stored bounding box disagrees with
  the outline, which Firefox logs on every page load. The file in `web/static/fonts`
  has been re-saved with `recalcBBoxes`; do not replace it with a fresh download
  without redoing that.
- `sicae.pt` refuses port 443 outright. The lookup speaks plain HTTP to it by
  necessity; it carries no credentials and asks a public register a public
  question.
- `CompanyLookup` caches misses too, so a NIF that failed once will not be
  refetched for `COMPANY_CACHE_DAYS`. Delete the row before retesting a fetch
  path, or you will be testing the cache.
- **A scoped rule outranks a shared one.** Svelte compiles `.x` to
  `.x.svelte-hash`, specificity (0,2,0), which beats anything single-class in
  `app.css`. A scoped `.stats div > span { color: ink-soft }` repainted the
  labels on the red and blue plates dark-on-dark. A component must not set a
  colour that the shared component it wraps is already deciding.
- Svelte scopes component CSS but not class *names*. A chip carrying `class="cunha"`
  picked up `display: grid` from the indices wrapper of the same name, and one
  carrying `verdict` picked up its 1rem padding. Modifier classes on small
  components need their own prefix.
- **A supplier is a NIF, not a name.** The record spells one firm several ways:
  EDP appears six times in Loures, Uniself three. Grouping by name split one
  company into several, which deflated HHI and top-supplier, inflated the
  supplier count, and made every new *spelling* of an old firm read as a debut
  (Odivelas: 2677 suppliers -> 1497, concentration 1.44 -> 4.42, newcomer money
  5.74% -> 0.25%). `_supplier_id()` is `coalesce(nif, name)` and every place
  that counts firms has to use it: `suppliers()`, `per_supplier`,
  `_suppliers_to_half`, and both newcomer debut lookups.
- Svelte's `{@const}` is only legal as the immediate child of a block
  (`{#if}`, `{#each}`, `{#snippet}`, a component). Inside a plain `<div>` it is a
  compile error; hoist it to the block or make it a `$derived` in the script.
- A "change of hands" in a mandate needs both the list and the person to change.
  Independent movements re-register under a new name almost every cycle (IN-OV
  becomes INOV25) with the same president continuing, and comparing party
  strings alone flagged that as a change.

## Commit hooks

`git config core.hooksPath .githooks` enables them; git will not do it for you
on clone. `.githooks/pre-commit` blocks secrets (gitleaks, from a pinned Docker
image when no binary is on PATH), staged environment files, anything over 2 MB,
and em dashes in `web/src`, `api`, `core` and `ingest` source.

The em dash check deliberately covers only files we write. A contract
description quoted verbatim from IMPIC may contain one and must not be edited.

The same gitleaks scan runs in CI over the full history
(`.github/workflows/secrets.yml`), on every push and PR and weekly on a cron,
because the hook is opt-in per clone and `--no-verify` exists. CI is what
actually gates the branch.

## Running

Development is still plain docker compose. Production is podman; see below.

```bash
cp .env.example .env
docker compose up -d db api web
docker compose --profile tools run --rm ingest impic      # bulk history
docker compose --profile tools run --rm ingest entities   # supplier countries
docker compose --profile tools run --rm ingest mandatos   # autárquicas results
docker compose --profile tools run --rm ingest delta      # apiaberta top-up

# company profiles, quota'd: run it nightly, it paces itself and exits
docker compose run --rm --entrypoint python api -m contratos_api.backfill --dry-run
docker compose run --rm --entrypoint python api -m contratos_api.backfill
```

Then <http://localhost:8080>. CLI commands are
`schema, impic, entities, mandatos, delta, all, nifs`.

**pytest, and nothing but pytest.** No fixtures, no plugins, no conftest beyond
the three lines that set a `DATABASE_URL` nothing connects to: every test here
is a plain function full of bare asserts, which is what pytest collects anyway.
It replaced a hand-rolled `__main__` runner per file that iterated `globals()`,
so a test written below the runner never ran and never said it had not. The
suite needs no database and no container, so it runs on a venv in about a
second; `pytest.ini` holds the paths so a bare `pytest` finds all three
packages and does not go walking into `web/node_modules`.

`api/tests/test_router_calls.py` binds every `repo.x(...)` call in a router
against that method's real signature, with no database and no server. Nothing
else checks the Python: `svelte-check` reads only the frontend, and a router is
imported for the first time when a request arrives. That is how
`contracts() got an unexpected keyword argument 'date_from'` reached production
and 500'd every contracts request, after an edit added the parameter to the
router and missed the repository because the two signatures wrap differently.

`api/tests/test_scoring_keys.py` is the other seam nothing else watches: it
fails if the API starts shipping sentences again. The shapes stay valid and the
types stay right when that happens, so only this catches it.

Tests:

```bash
pip install -e './core[test]' -e ./api -e ./ingest   # once, in a venv
pytest                                               # all three packages
cd web && npm run check        # svelte-check plus the message parity check
```

`.github/workflows/tests.yml` runs every one of those on CI, and **the deploy
job needs it**: `tests` is a `workflow_call` job that `build-and-push` depends
on, so nothing reaches GHCR or the VPS from a red suite. The Python half needs
no database, only a syntactically valid `DATABASE_URL`, because `Settings`
demands one and nothing in the suite connects; the root `conftest.py` supplies
it, so CI and a laptop run the identical command. The runtime images no longer
carry `/app/tests`: the suite runs on a venv, and an image with no pytest in it
could not have run them anyway. It has no `push: main` trigger
of its own; the deploy already carries it on main, and a second copy would just
run the same minute twice.

Every container is rootless with a read-only root filesystem, all capabilities
dropped and `no-new-privileges`. nginx speaks plain HTTP on 8080 in both
environments.

## Deployment

The stack runs three loops beside the API: `ingest-delta`, `ingest-bulk` and
**`empresas`**, the company backfill. That last one is on `API_IMAGE` rather
than `INGEST_IMAGE`, because the lookup and its cache live in `contratos_api`,
and it is the only thing in the stack allowed to spend the nif.pt quota. It
paces itself and stops at `COMPANY_NIFPT_DAILY`, so its `sleep` decides only how
often it goes looking, never how hard it hits the register. With no key it logs
that and exits, which is the right behaviour for a stack that has not been given
one.

`docker-compose.prod.yml` and `.github/workflows/deploy.yml` are authoritative
and carry the reasoning inline.
The shape:

**One small VPS**, sized for the municipality count currently loaded, running a
distribution with **SELinux enforcing**. Host bootstrap (swap, firewall, deploy
user, unattended security updates) is deliberately kept out of this repository:
it documents one specific machine and nothing here needs it to build or run.

**Rootless podman, not docker.** No daemon, no root-owned socket, no
orchestrator on the box. `podman compose` needs the docker compose v2 binary as
its provider, because `podman-compose` does not implement
`depends_on: {condition: service_healthy}` or `service_completed_successfully`,
which is what orders the schema one-shot ahead of the API.

**Zero inbound ports.** `cloudflared` runs inside the stack and dials out, so
public traffic returns down that connection. The box holds no certificate, and
the OVH edge firewall now refuses everything inbound: established TCP, a few UDP
source ports and ICMP are all that pass, so the public address answers on
nothing, SSH included. Do not add a `ports:` mapping to any prod service: the
firewall expects nothing there, so a published port is a hole nobody is
watching.

**Images on GHCR**, built by GitHub-hosted runners with Buildx and tagged by
commit SHA. Podman runs OCI images and does not care what built them.

**The deploy is an SSH session over the NetBird mesh.** Since the edge was
closed there is no route to port 22 on the public address, so the job enrols the
runner as an ephemeral peer in the `ci-runners` group and talks to the box's
NetBird address (`vars.DEPLOY_HOST`). The peer NAME does not work from a
runner: the agent connects but never takes over the runner's resolver, and
`ci-runners` is in no nameserver group, so `.netbird.selfhosted` does not
resolve there. Re-enrolling the VPS changes that address and breaks the
deploy until the variable is updated. That group is defined in the homelab terraform,
not here, and reaches tcp/22 on this one host and nothing else; `bidirectional`
is off, so the box has no path back to the runner. The peer deletes itself
minutes after the job ends, which is why the workflow has no teardown step. Then
the session does what it always did: render `.env` from the GitHub Environment,
pipe it and the compose file to the box, `podman compose pull && up -d`, then
poll the API's health until it is healthy or fail the job. `up -d` returns as
soon as the containers exist, which says nothing about whether the API can reach
the database, and without the gate a broken rollout reports success and the
first person to find out is a reader.

Deploys fire on **`main` only**, plus `workflow_dispatch`. Secrets and non-secret
vars both live in the GitHub `production` Environment; the non-secret half
arrives as one block in `vars.APP_ENV`, so adding a tunable is a UI edit rather
than a change to the workflow.

`restart: always`, not `unless-stopped`. Podman has no daemon watching restart
policies: containers come back after a reboot because `podman-restart.service`
runs `podman start --all --filter restart-policy=always`, and an
`unless-stopped` container would stay down until somebody logged in. `linger`
on the deploy user is the other half: without it systemd tears down
`/run/user/$uid` when the SSH session ends and takes the socket and the
containers with it.

The host enforces SELinux and the stack does not touch it. Every mount in the stack is a named
volume or a tmpfs, which podman labels on its own. **Any bind mount added later
needs `:Z`** or the container reads its own files as permission denied.

**Harbor, Vault, Dockhand and haproxy are gone.** Do not reintroduce them in
documentation or config.

## Adding municipalities

`MUNICIPALITY_NIFS` scopes the ingest, and its production value lives in
`vars.APP_ENV` in the GitHub `production` environment, not in the repo. To widen
it, ask the bulk file for the NIFs rather than hunting them:

```bash
docker compose --profile tools run --rm ingest nifs Lisboa Porto peninsula-setubal
```

It reads the most recent IMPIC year, resolves every buyer name to a concelho and
prints a ready `MUNICIPALITY_NIFS=` line, plus the concelhos it could not find.
It touches neither the schema nor the database. Accepts district names, concelho
names, and `peninsula-setubal` (or `margem-sul`) for the nine concelhos of the
Península de Setúbal, which is a NUTS III unit the district table cannot
express.

It only accepts a buyer whose name begins with "Município" or "Câmara
Municipal". Without that check `concelho_name` happily resolved "Universidade do
Porto" to Porto and "Agrupamento de Escolas de Lousada" to Lousada, and because
the first match per concelho wins, each shadowed the real câmara.
