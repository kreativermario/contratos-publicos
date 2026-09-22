"""Who is this supplier, beyond the contract it just won.

The procurement data answers nothing about a company: no sector, no legal form,
no address, no age. Two outside sources fill part of that gap.

  1. api.ptdata.org  one JSON call, aggregates SICAE and VIES.
  2. sicae.pt        the Ministry of Justice CAE register, the legally
                     authoritative source, served as HTML.

The aggregator is tried first because it answers in one request and carries the
address; SICAE is the fallback because it is the official register and will
outlive any third party. Every answer, including a miss, is cached in Postgres,
so a click on the same node never leaves the building twice.

Capital social and incorporation date are not here because no free source
publishes them. They live in the Certidao Permanente, which is paid.
"""
from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from contratos_core import CompanyProfile, Settings
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")

# <div id="letrasCAE">CAE Principal</div></td><td ...><div ... title="desc">56220</div>
_SICAE_ROW = re.compile(
    r'<div id="letrasCAE">\s*CAE\s+(Principal|Secund[^<]*?)\s*</div>\s*</td>\s*'
    r'<td[^>]*>\s*<div[^>]*title="([^"]*)"[^>]*>\s*(\d{3,6})\s*</div>',
    re.I | re.S,
)
_SICAE_FIRMA = re.compile(r'id="ctl00_MainContent_ipFirma"[^>]*value="([^"]*)"', re.I)

# empresadb renders client-side, but its <meta name="description"> is not, and
# it carries "Constituída em YYYY".
_FOUNDED = re.compile(r'Constitu[ií]da em\s*(\d{4})', re.I)

# The commercial register's published acts start in 2006. A company older than
# that shows up as 2006, which is a floor, not a founding year.
REGISTER_FLOOR = 2006

# Longest first: "unipessoal ... lda" must not be read as a plain "lda".
#
# The short ones carry their own spaces. Without a trailing boundary, " sa"
# matched "dos SAntos" and read Maria dos Santos Ferreira as a Sociedade
# anónima; the normaliser below strips dots, so the needles must not carry any.
_FORMS = (
    ("unipessoal", "Unipessoal por quotas"),
    ("sociedade anonima", "Sociedade anónima"),
    ("sociedade anónima", "Sociedade anónima"),
    ("cooperativa", "Cooperativa"),
    (" crl ", "Cooperativa"),
    ("associação", "Associação"),
    ("associacao", "Associação"),
    ("fundação", "Fundação"),
    ("fundacao", "Fundação"),
    ("município", "Entidade pública"),
    ("municipio", "Entidade pública"),
    ("câmara municipal", "Entidade pública"),
    ("camara municipal", "Entidade pública"),
    ("freguesia", "Entidade pública"),
    (" ace ", "Agrupamento complementar de empresas"),
    (" sa ", "Sociedade anónima"),
    ("limitada", "Sociedade por quotas"),
    (" lda ", "Sociedade por quotas"),
    (" ldª ", "Sociedade por quotas"),
)

#: NIF prefixes the tax register assigns to a natural person. 5 is a company,
#: 6 a public body, 9 another collective; 1 to 3 and 45 are people. This is the
#: authoritative test, and the only one: reading the *name* for the absence of a
#: legal form called TECNORÉM S.A a person, because "S.A" without the trailing
#: dot was not in the table above.
PERSON_NIF_PREFIXES = ("1", "2", "3")
PERSON_NIF_PAIRS = ("45",)


def is_person_nif(nif: str | None) -> bool:
    """Whether a NIF belongs to a natural person rather than to an entity."""
    if not nif or not nif.isdigit() or len(nif) != 9:
        return False
    return nif[0] in PERSON_NIF_PREFIXES or nif[:2] in PERSON_NIF_PAIRS


#: Particles that sit inside a Portuguese name without being a name themselves.
_PARTICLES = {"de", "da", "do", "das", "dos", "e", "du", "del", "van", "von"}

_NAME_WORD = re.compile(r"^[a-zà-öø-ÿ']+$", re.IGNORECASE)

#: Punctuation a trading name uses and a person's name does not. "Signinum,
#: Gestão de Património Cultural" is five plain words once the comma is dropped,
#: so the comma has to be read as the structure it is rather than removed.
_TRADE_PUNCT = re.compile(r"[,&/()\"]")

#: A second net, for a trading name that happens to carry no punctuation and no
#: legal form. Not a definition of a company, just the words that never turn up
#: in somebody's name.
_TRADE_WORDS = frozenset("""
gestão gestao serviços servicos sociedade construções construcoes engenharia
comércio comercio indústria industria consultoria transportes imobiliária
imobiliaria tecnologia tecnologias soluções solucoes empresa grupo centro
clínica clinica farmácia farmacia património patrimonio projectos projetos
produções producoes equipamentos materiais distribuição distribuicao
manutenção manutencao instalações instalacoes limpeza segurança seguranca
""".split())


def looks_like_person_name(name: str | None) -> bool:
    """Whether a supplier name reads as a person rather than as a firm.

    Used only alongside a missing NIF, which is the real signal: IMPIC omits the
    NIF of a natural person, so every published one in this record starts with a
    5 or a 9. That leaves the name to separate "Francisco Simões Gomes" from
    "LUBRIFUEL", and three words is the bar, because a Portuguese name in an
    official record is a given name and two surnames. It costs a two-word name
    and buys not calling a two-word trading name a person.
    """
    if not name or legal_form_from_name(name):
        return False
    if _TRADE_PUNCT.search(name) or any(ch.isdigit() for ch in name):
        return False
    words = name.split()
    if any(w.lower() in _TRADE_WORDS for w in words):
        return False
    if not 3 <= len(words) <= 7:
        return False
    real = [w for w in words if w.lower() not in _PARTICLES]
    return len(real) >= 2 and all(_NAME_WORD.match(w) for w in words)



#: Every distinct form the reading above can produce, in the order a reader
#: most likely wants to see them.
LEGAL_FORMS = (
    "Sociedade por quotas",
    "Unipessoal por quotas",
    "Sociedade anónima",
    "Cooperativa",
    "Associação",
    "Fundação",
    "Agrupamento complementar de empresas",
    "Entidade pública",
)


def legal_form_sql(col):
    """The same reading, as a SQL expression.

    Built from the same `_FORMS` tuple as the Python version, in the same order,
    so filtering on a form can never disagree with the form shown next to the
    firm. Doing it in SQL is what lets the list stay paged: filtering in Python
    would mean fetching every supplier to show fifty.
    """
    from sqlalchemy import case, func

    haystack = func.concat(
        " ",
        func.regexp_replace(
            func.regexp_replace(
                func.regexp_replace(func.lower(col), r"\.", "", "g"),
                r"[,\-&/]", " ", "g",
            ),
            r"\s+", " ", "g",
        ),
        " ",
    )
    return case(
        *[(haystack.like(f"%{needle}%"), form) for needle, form in _FORMS],
        else_=None,
    )


def legal_form_from_name(name: str | None) -> str | None:
    """Read the legal form off the firm name.

    Every paid registry reports the same thing, and Portuguese firm names are
    legally required to carry the suffix, so this costs nothing and breaches
    nobody's terms. It is a reading of the name, not a registry lookup, and the
    interface says so.
    """
    if not name:
        return None
    # Dots are deleted, not spaced: the record writes "S.A", "S.A." and "SA" for
    # the same thing, and spacing the dots turns "S.A." into "s a", which
    # matches nothing. Other separators do become spaces.
    haystack = f" {name.lower().strip()} "
    haystack = haystack.replace(".", "")
    haystack = re.sub(r"[,\-&/]", " ", haystack)
    haystack = re.sub(r"\s+", " ", haystack)
    for needle, form in _FORMS:
        if needle in haystack:
            return form
    return None


def parse_founded(page: str) -> int | None:
    """The year of the first published act, or None when the page says nothing."""
    hit = _FOUNDED.search(page or "")
    if not hit:
        return None
    year = int(hit.group(1))
    return year if 1900 <= year <= 2100 else None


def parse_sicae(page: str) -> dict | None:
    """Pull firm name and CAE list out of the SICAE detail page.

    Returns None when the page carries no CAE at all, which is how SICAE
    answers for a NIPC it does not know.
    """
    rows = _SICAE_ROW.findall(page or "")
    if not rows:
        return None
    firma = _SICAE_FIRMA.search(page or "")
    return {
        "sicae_name": html.unescape(firma.group(1)).strip() if firma else None,
        "cae": [
            {
                "code": code,
                "description": html.unescape(desc).strip() or None,
                "type": "principal" if position.lower().startswith("principal") else "secundario",
            }
            for position, desc, code in rows
        ],
    }


def parse_aggregator(payload: dict) -> dict | None:
    """Normalise the aggregator's envelope into our own shape."""
    data = (payload or {}).get("data") or {}
    if not data.get("nif"):
        return None
    cae = [
        {"code": str(c.get("code") or ""),
         "description": c.get("description") or None,
         "type": c.get("type") or None}
        for c in (data.get("cae_codes") or [])
        if c.get("code")
    ]
    if not cae and not data.get("name"):
        return None
    return {
        "name": data.get("name") or None,
        "sicae_name": data.get("sicae_name") or None,
        "legal_type": data.get("type") or None,
        "address": data.get("address") or None,
        "cae": cae,
    }


@dataclass(slots=True)
class CompanyLookup:
    session: Session
    settings: Settings

    def get(self, nif: str) -> dict | None:
        """Cached profile for a NIF, fetching from the registries on a miss."""
        cached = self.session.get(CompanyProfile, nif)
        if cached and not self._stale(cached):
            return self._as_dict(cached) if cached.found else None
        if not self.settings.company_lookup_enabled:
            return self._as_dict(cached) if cached and cached.found else None

        fetched = self._fetch(nif)
        self._store(nif, fetched)
        if not fetched:
            return None
        year = fetched.get("founded_year")
        return fetched | {
            "nif": nif,
            "founded_exact": bool(year and year > REGISTER_FLOOR),
        }

    def _stale(self, row: CompanyProfile) -> bool:
        if row.fetched_at is None:
            return True
        age = datetime.now(timezone.utc) - row.fetched_at
        return age > timedelta(days=self.settings.company_cache_days)

    def _fetch(self, nif: str) -> dict | None:
        base = self.settings.company_api_base.rstrip("/")
        profile = None
        raw = self._read(f"{base}/companies/{nif}")
        if raw:
            try:
                parsed = parse_aggregator(json.loads(raw))
            except (ValueError, TypeError):
                parsed = None
            if parsed:
                profile = parsed | {"source": "ptdata"}

        if not profile:
            sicae = self._read(
                f"{self.settings.company_sicae_base.rstrip('/')}/Detalhe.aspx?NIPC={nif}"
            )
            parsed = parse_sicae(sicae) if sicae else None
            if parsed:
                profile = parsed | {"name": parsed.get("sicae_name"), "source": "sicae"}
        if not profile:
            return None

        profile["legal_form"] = legal_form_from_name(
            profile.get("sicae_name") or profile.get("name")
        )
        profile["founded_year"] = self._founded(nif)
        return profile

    def _founded(self, nif: str) -> int | None:
        base = self.settings.company_founded_base.rstrip("/")
        if not base:
            return None
        return parse_founded(self._read(f"{base}/empresa/{nif}") or "")

    def _read(self, url: str) -> str | None:
        """One request, short timeout, never raising: a registry being down must
        not take a page of the site down with it."""
        request = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "application/json, text/html;q=0.9",
            "Accept-Language": "pt-PT,pt;q=0.9",
        })
        try:
            with urllib.request.urlopen(request, timeout=self.settings.company_timeout) as r:
                return r.read(2_000_000).decode("utf-8", "replace")
        except (urllib.error.URLError, OSError, TimeoutError):
            return None

    def _store(self, nif: str, data: dict | None) -> None:
        values = {
            "nif": nif,
            "name": (data or {}).get("name"),
            "sicae_name": (data or {}).get("sicae_name"),
            "legal_type": (data or {}).get("legal_type"),
            "address": (data or {}).get("address"),
            "cae": (data or {}).get("cae"),
            "founded_year": (data or {}).get("founded_year"),
            "legal_form": (data or {}).get("legal_form"),
            "source": (data or {}).get("source"),
            "found": data is not None,
            "fetched_at": datetime.now(timezone.utc),
        }
        stmt = insert(CompanyProfile).values(**values)
        self.session.execute(stmt.on_conflict_do_update(
            index_elements=[CompanyProfile.nif],
            set_={k: v for k, v in values.items() if k != "nif"},
        ))
        self.session.commit()

    @staticmethod
    def _as_dict(row: CompanyProfile) -> dict:
        return {
            "nif": row.nif,
            "name": row.name,
            "sicae_name": row.sicae_name,
            "legal_type": row.legal_type,
            "address": row.address,
            "cae": row.cae or [],
            "founded_year": row.founded_year,
            # below the floor the register simply has nothing, so the year is a
            # bound, not a fact, and the interface must not print it as one
            "founded_exact": bool(row.founded_year and row.founded_year > REGISTER_FLOOR),
            "legal_form": row.legal_form,
            "source": row.source,
        }
