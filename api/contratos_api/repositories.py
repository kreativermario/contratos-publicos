"""Query layer. Every aggregate the site needs, expressed once."""
from __future__ import annotations

from sqlalchemy import (Numeric, String, and_, case, cast, column, false, func,
                        literal_column, or_, select, values)
from sqlalchemy.orm import Session

from datetime import date

from contratos_core import (CONCELHOS, CPV_SECTORS, CompanyProfile, Contract,
                             ContractBidder, ContractLocation, ContractSupplier,
                             Entity, Mandate, Settings, concelho_name, dico_for,
                             divisions_for, sector_for)
from .services.flags import FlagContext, slice_groups, supplier_id

from .services.company import legal_form_from_name, legal_form_sql

AJUSTE_DIRETO = "%Ajuste Direto%"


def _executed_in(municipality: str):
    """EXISTS over the locations table: a contract can span several concelhos."""
    loc = ContractLocation.__table__.alias("loc_q")
    return (
        select(literal_column("1"))
        .where(loc.c.contract_id == Contract.id, loc.c.municipality == municipality)
        .exists()
    )


def _with_parties(row: dict) -> dict:
    """Split the aggregated {name, nif} objects back into what the schema wants.

    `suppliers` stays a list of names because most of the interface only prints
    them; `parties` carries the NIF so a row can link to the company page.
    """
    parties = [p for p in (row.pop("parties", None) or []) if p and p.get("name")]
    parties.sort(key=lambda p: p["name"])
    row["parties"] = parties
    row["suppliers"] = [p["name"] for p in parties]
    return row


def _term_years(start, end) -> float | None:
    """How long a mandate ran, in years. The current one runs to today."""
    if not start:
        return None
    return round(((end or date.today()) - start).days / 365.25, 1)


def _supplier_form_matches(form: str):
    """EXISTS over the suppliers of a contract, matched on legal form."""
    sup = ContractSupplier.__table__.alias("sup_form")
    return (
        select(literal_column("1"))
        .where(sup.c.contract_id == Contract.id, legal_form_sql(sup.c.name) == form)
        .exists()
    )


def _supplier_matches(term: str):
    """EXISTS over a fresh alias, so the outer join's aggregate stays intact."""
    sup = ContractSupplier.__table__.alias("sup_q")
    return (
        select(literal_column("1"))
        .where(sup.c.contract_id == Contract.id, sup.c.name.ilike(f"%{term}%"))
        .exists()
    )


def newcomer_verdict(first_seen, first_win, dataset_start, newcomer_days: int,
                     period_end=None, soft_win: bool | None = None) -> bool | None:
    """Is this firm new to public contracting, as far as the loaded record can tell?

    No dataset publishes incorporation dates, and no free source does either: the
    commercial register only begins in 2006, so a "founded year" read from it is
    a lower bound, not a date. The debut in the contract record is the only
    proxy available, and three conditions have to hold together for it to mean
    anything.

    1. Knowable. Unless the record already ran a full window before the debut, a
       firm that simply predates the years we hold is indistinguishable from a
       new one, so the answer is None rather than a confident False.
    2. Recent. Measured against the end of the period being read, not against
       the whole record. Without this the flag never expired: a firm whose first
       ever contract was in 2016 stayed an "estreante" in 2026 forever, which is
       how VITORJRALVES came to be labelled one a decade later.
    3. Soft. The win here was an ajuste direto or a tender it was alone in. A new
       firm winning an open tender against rivals is a new firm, not a red flag,
       and this index only claims to show red flags.
    """
    if first_seen is None or first_win is None or dataset_start is None:
        return None
    if (first_seen - dataset_start).days < newcomer_days:
        return None
    if period_end is not None and (period_end - first_seen).days > newcomer_days:
        return False
    if soft_win is False:
        return False
    return (first_win - first_seen).days <= newcomer_days


# IMPIC spells the same buyer several ways ("Município da Amadora", "Municipio
# da Amadora", "Município de Amadora"), so grouping by name as well as NIF split
# one municipality into several rows, each holding part of its contracts. The
# NIF is the identity; the name is only a label, and the most frequent spelling
# is the one to show.
_canonical_buyer_name = func.mode().within_group(Contract.buyer_name)


def _date_window(stmt, start, end):
    """Filter on signed_date, not on year.

    Mandates change hands in late September or October, so a year-based filter
    would put a contract signed in October 2017 in the wrong mandate. The end is
    exclusive: a contract signed on election day belongs to the term beginning
    that day.
    """
    if start is not None:
        stmt = stmt.where(Contract.signed_date >= start)
    if end is not None:
        stmt = stmt.where(Contract.signed_date < end)
    return stmt


def _year_window(stmt, year_from: int | None, year_to: int | None,
                 date_from=None, date_to=None):
    """The page's reading window.

    Years are what the year chips express, but a mandate is not a run of years:
    it starts on election day, in late September or October. Filtering a term by
    year therefore dragged in the previous administration's autumn and dropped
    its own. When exact dates are given they win outright, and `_date_window`'s
    exclusive end keeps election day with the term it begins.
    """
    if date_from is not None or date_to is not None:
        return _date_window(stmt, date_from, date_to)
    if year_from is not None:
        stmt = stmt.where(Contract.year >= year_from)
    if year_to is not None:
        stmt = stmt.where(Contract.year <= year_to)
    return stmt


def _supplier_id():
    """What counts as one firm.

    The record spells the same company several ways: EDP appears six times in
    Loures alone, and "Uniself SA" three. Grouping by name therefore split one
    firm into several, which deflated every concentration measure and inflated
    the supplier count. The NIF is the identity where the record carries one;
    where it does not, the name is all there is.
    """
    return func.coalesce(ContractSupplier.nif, ContractSupplier.name)


class MunicipalityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[dict]:
        stmt = (
            select(
                Contract.buyer_nif.label("nif"),
                _canonical_buyer_name.label("name"),
                func.count().label("contracts"),
                func.sum(Contract.value).label("total"),
                func.min(Contract.signed_date).label("since"),
                func.max(Contract.signed_date).label("latest"),
            )
            .where(Contract.buyer_nif.is_not(None))
            .group_by(Contract.buyer_nif)
            .order_by(func.sum(Contract.value).desc().nulls_last())
        )
        return [row._asdict() for row in self.session.execute(stmt)]

    def get(self, nif: str) -> dict | None:
        stmt = (
            select(
                Contract.buyer_nif.label("nif"),
                _canonical_buyer_name.label("name"),
                func.count().label("contracts"),
                func.sum(Contract.value).label("total"),
                func.min(Contract.signed_date).label("since"),
                func.max(Contract.signed_date).label("latest"),
            )
            .where(Contract.buyer_nif == nif)
            .group_by(Contract.buyer_nif)
        )
        row = self.session.execute(stmt).first()
        return row._asdict() if row else None

    # The Código dos Contratos Públicos was revised by Decreto-Lei 111-B/2017,
    # in force from 1 January 2018 with the bulk of the ajuste direto changes
    # from August 2017. It moves the numbers more than any election does, so any
    # comparison across parties has to be split here rather than pooled.
    CCP_REFORM = date(2017, 8, 30)

    #: Minimum length, in days, for a mandate-era slice to vote on the spread.
    #: Splitting a mandate at the reform leaves slivers: the 2013-2017 term's
    #: "depois" half is the single month between 30 August and 1 October 2017.
    #: A contract count is the wrong guard for that (a busy month clears any
    #: threshold and still produces a 97% share off a month's denominator), so
    #: the guard is duration. Slivers still count towards the totals, which are
    #: value-weighted and immune to this; they just do not get a vote on the
    #: range.
    SPREAD_MIN_DAYS = 180

    def _nif_dico_pairs(self) -> list[tuple[str, str]]:
        """Every loaded município paired with its administrative code.

        Built here rather than stored because the set of loaded municípios is
        whatever the ingest scope happens to be, and a name that cannot be
        resolved unambiguously is dropped rather than guessed.
        """
        pairs = []
        for row in self.list_all():
            dico = dico_for(concelho_name(row.get("name") or ""))
            if dico:
                pairs.append((row["nif"], dico))
        return pairs

    def _per_mandate_era(self) -> list[dict]:
        """One row per município, mandate and era, with what was contracted.

        The unit of observation is a mandate, not a município: a câmara that a
        party held for four terms should weigh four times, and a party that held
        one small câmara once should not be averaged against one that held
        Lisboa for a decade without that being visible.
        """
        pairs = self._nif_dico_pairs()
        if not pairs:
            return []

        pv = values(column("nif", String), column("dico", String),
                    name="loaded").data(pairs)
        era = case((Contract.signed_date < self.CCP_REFORM, "antes"), else_="depois")
        ad = func.coalesce(
            func.sum(Contract.value).filter(Contract.procedure.ilike(AJUSTE_DIRETO)), 0)

        stmt = (
            select(
                pv.c.nif, Mandate.party, Mandate.coalition, Mandate.citizens_group,
                Mandate.term_start, Mandate.term_end, era.label("era"),
                func.count(Contract.id).label("contracts"),
                func.coalesce(func.sum(Contract.value), 0).label("value"),
                ad.label("ad_value"),
            )
            .select_from(pv)
            .join(Mandate, Mandate.dico == pv.c.dico)
            .join(Contract, and_(
                Contract.buyer_nif == pv.c.nif,
                Contract.signed_date >= Mandate.term_start,
                or_(Mandate.term_end.is_(None), Contract.signed_date < Mandate.term_end),
            ))
            .group_by(pv.c.nif, Mandate.party, Mandate.coalition,
                      Mandate.citizens_group, Mandate.term_start, Mandate.term_end,
                      era.label("era"))
        )
        rows = [r._asdict() for r in self.session.execute(stmt)]
        today = date.today()
        for r in rows:
            # How much of this mandate actually falls inside its era.
            start, end = r["term_start"], r["term_end"] or today
            if r["era"] == "antes":
                end = min(end, self.CCP_REFORM)
            else:
                start = max(start, self.CCP_REFORM)
            r["slice_days"] = max(0, (end - start).days)
        return rows

    def party_ranking(self) -> list[dict]:
        """Ajuste direto share by party, split at the 2017 reform.

        Reported with the number of mandates behind it and the spread across
        them, never as a single average. A party average alone would mostly
        measure which parties happened to hold more câmaras before 2017, when
        the law allowed far more ajuste direto.
        """
        rows = self._per_mandate_era()
        buckets: dict[tuple[str, str], dict] = {}
        for r in rows:
            key = (r["party"], r["era"])
            b = buckets.setdefault(key, {
                "party": r["party"], "era": r["era"],
                "coalition": r["coalition"], "citizens_group": r["citizens_group"],
                "mandates": 0, "municipalities": set(), "contracts": 0,
                "value": 0.0, "ad_value": 0.0, "shares": [],
            })
            b["mandates"] += 1
            b["municipalities"].add(r["nif"])
            b["contracts"] += r["contracts"]
            b["value"] += float(r["value"] or 0)
            b["ad_value"] += float(r["ad_value"] or 0)
            if r["value"] and r["slice_days"] >= self.SPREAD_MIN_DAYS:
                b["shares"].append(100 * float(r["ad_value"] or 0) / float(r["value"]))

        out = []
        for b in buckets.values():
            shares = sorted(b["shares"])
            out.append({
                "party": b["party"], "era": b["era"],
                "coalition": b["coalition"], "citizens_group": b["citizens_group"],
                "mandates": b["mandates"],
                "municipalities": len(b["municipalities"]),
                "contracts": b["contracts"],
                "value": round(b["value"], 2),
                # value-weighted: the headline figure
                "ad_pct": round(100 * b["ad_value"] / b["value"], 1) if b["value"] else None,
                # and the spread behind it, so one câmara cannot stand for a party
                "ad_low": round(shares[0], 1) if shares else None,
                "ad_high": round(shares[-1], 1) if shares else None,
                "ad_median": round(shares[len(shares) // 2], 1) if shares else None,
                # how many mandate-slices the range is actually built on
                "spread_n": len(shares),
            })
        out.sort(key=lambda r: (r["era"], -r["value"]))
        return out

    def district_ranking(self) -> list[dict]:
        """The same figures grouped by district, one row per district and era."""
        by_nif_district = {}
        for nif, dico in self._nif_dico_pairs():
            hit = next((c for c in CONCELHOS if c[0] == dico), None)
            if hit:
                by_nif_district[nif] = hit[3]

        buckets: dict[tuple[str, str], dict] = {}
        for r in self._per_mandate_era():
            district = by_nif_district.get(r["nif"])
            if not district:
                continue
            b = buckets.setdefault((district, r["era"]), {
                "district": district, "era": r["era"],
                "municipalities": set(), "contracts": 0, "value": 0.0,
                "ad_value": 0.0, "shares": [],
            })
            b["municipalities"].add(r["nif"])
            b["contracts"] += r["contracts"]
            b["value"] += float(r["value"] or 0)
            b["ad_value"] += float(r["ad_value"] or 0)
            if r["value"] and r["slice_days"] >= self.SPREAD_MIN_DAYS:
                b["shares"].append(100 * float(r["ad_value"] or 0) / float(r["value"]))

        out = []
        for b in buckets.values():
            shares = sorted(b["shares"])
            out.append({
                "district": b["district"], "era": b["era"],
                "municipalities": len(b["municipalities"]),
                "contracts": b["contracts"],
                "value": round(b["value"], 2),
                "ad_pct": round(100 * b["ad_value"] / b["value"], 1) if b["value"] else None,
                "ad_low": round(shares[0], 1) if shares else None,
                "ad_high": round(shares[-1], 1) if shares else None,
                "spread_n": len(shares),
            })
        out.sort(key=lambda r: (r["era"], -r["value"]))
        return out

    def mandate_map(self, election_year: int | None = None) -> list[dict]:
        """Who holds each of the 308 câmaras, for one election.

        Not limited to the municípios with contracts loaded: the election data
        covers the whole country, and a map with nine concelhos coloured and 299
        blank would say nothing. Defaults to the most recent election.
        """
        target_q = select(func.max(Mandate.election_date))
        if election_year:
            target_q = target_q.where(
                func.extract("year", Mandate.election_date) == election_year
            )
        target = self.session.scalar(target_q)
        if not target:
            return []

        by_dico = {c[0]: c for c in CONCELHOS}
        rows = self.session.execute(
            select(Mandate).where(Mandate.election_date == target).order_by(Mandate.dico)
        ).scalars().all()

        # Contracts exist for a handful of câmaras, elections for all 308. The
        # spending is therefore optional on every row, never zero: a câmara we
        # have not loaded has not spent nothing.
        nif_by_dico = {}
        for m in self.list_all():
            code = dico_for(concelho_name(m["name"])) if m.get("name") else None
            if code:
                nif_by_dico[code] = m["nif"]

        out = []
        for m in rows:
            c = by_dico.get(m.dico)
            row = {
                "dico": m.dico,
                "concelho": c[1] if c else m.dico,
                "district": c[3] if c else None,
                "election_date": m.election_date,
                "term_start": m.term_start,
                "term_end": m.term_end,
                "years": _term_years(m.term_start, m.term_end),
                "party": m.party,
                "coalition": m.coalition,
                "citizens_group": m.citizens_group,
                "president": m.president,
                "contracts": None, "value": None, "ad_pct": None,
            }
            nif = nif_by_dico.get(m.dico)
            # The buyer NIF, where this câmara's contracts are loaded. It is what
            # makes a concelho on the map clickable through to its own page, and
            # its absence is what says the page does not exist yet.
            row["nif"] = nif
            if nif:
                row.update(self._term_spend(nif, m.term_start, m.term_end))
            out.append(row)
        return out

    def _term_spend(self, nif: str, term_start, term_end) -> dict:
        """What one câmara contracted between two dates."""
        ad_value = func.coalesce(
            func.sum(Contract.value).filter(Contract.procedure.ilike(AJUSTE_DIRETO)), 0)
        agg = self.session.execute(_date_window(
            select(
                func.count().label("contracts"),
                func.coalesce(func.sum(Contract.value), 0).label("value"),
                ad_value.label("ad_value"),
            ).where(Contract.buyer_nif == nif),
            term_start, term_end,
        )).one()
        total = float(agg.value or 0)
        return {
            "contracts": agg.contracts,
            "value": total,
            "ad_pct": round(100 * float(agg.ad_value or 0) / total, 1) if total else None,
        }

    def election_years(self) -> list[int]:
        rows = self.session.execute(
            select(func.extract("year", Mandate.election_date)).distinct()
            .order_by(func.extract("year", Mandate.election_date).desc())
        ).scalars().all()
        return [int(r) for r in rows]

    def mandates(self, nif: str) -> list[dict]:
        """Who ran this câmara, and what was contracted under each of them.

        Joined on DICO, which neither the contract record nor the election data
        shares directly: the contracts carry a buyer name, the results carry a
        territory code, and the geometry table is what bridges them. A name that
        cannot be resolved unambiguously (there are two Lagoas) yields nothing
        rather than a guess.
        """
        row = self.get(nif)
        if not row or not row.get("name"):
            return []
        dico = dico_for(concelho_name(row["name"]))
        if not dico:
            return []

        terms = self.session.execute(
            select(Mandate).where(Mandate.dico == dico).order_by(Mandate.term_start)
        ).scalars().all()

        out = []
        for t in terms:
            ad_value = func.coalesce(
                func.sum(Contract.value).filter(Contract.procedure.ilike(AJUSTE_DIRETO)), 0)
            agg = self.session.execute(_date_window(
                select(
                    func.count().label("contracts"),
                    func.coalesce(func.sum(Contract.value), 0).label("value"),
                    ad_value.label("ad_value"),
                ).where(Contract.buyer_nif == nif),
                t.term_start, t.term_end,
            )).one()._asdict()
            total = float(agg["value"] or 0)
            out.append({
                "election_date": t.election_date,
                "term_start": t.term_start,
                "term_end": t.term_end,
                "party": t.party,
                "coalition": t.coalition,
                "citizens_group": t.citizens_group,
                "president": t.president,
                "contracts": agg["contracts"],
                "value": total,
                # share of the money that skipped a tender, the one indicator
                # cheap enough to compute per mandate without a second pass
                "ad_pct": round(100 * float(agg["ad_value"] or 0) / total, 1) if total else None,
            })
        return out

    #: Sort keys the suppliers list accepts. Whitelisted rather than passed
    #: through, because this reaches an ORDER BY.
    SUPPLIER_SORTS = {
        "total": func.sum(Contract.value),
        "contracts": func.count(),
        # the share, not the count: the column shows a percentage, and
        # sorting it by how many contracts a firm has would order a
        # different quantity from the one on screen
        "ad_pct": (100.0 * func.count().filter(Contract.procedure.ilike(AJUSTE_DIRETO))
                   / func.count()),
        "last_win": func.max(Contract.signed_date),
        "first_win": func.min(Contract.signed_date),
    }

    def suppliers(self, nif: str, limit: int, year_from=None, year_to=None,
                  date_from=None, date_to=None,
                  newcomer_days: int = 365, q: str | None = None,
                  sort: str = "total", desc: bool = True,
                  offset: int = 0, form: str | None = None) -> list[dict]:
        ad_count = func.count().filter(Contract.procedure.ilike(AJUSTE_DIRETO))
        # "Soft" = won without real competition: an ajuste direto, or a tender
        # this firm was the only one to enter. A new firm that beat rivals in an
        # open tender is not what this index is looking for.
        soft_count = func.count().filter(
            or_(Contract.procedure.ilike(AJUSTE_DIRETO), Contract.n_bidders == 1)
        )
        stmt = (
            select(
                # the most common spelling, since the group now spans several
                func.mode().within_group(ContractSupplier.name).label("name"),
                func.max(ContractSupplier.nif).label("nif"),
                func.count().label("contracts"),
                func.sum(Contract.value).label("total"),
                func.min(Contract.signed_date).label("first_win"),
                func.max(Contract.signed_date).label("last_win"),
                (soft_count > 0).label("soft_win"),
                func.round(cast(100.0 * ad_count / func.count(), Numeric), 1).label("ad_pct"),
                func.max(Entity.country).label("country"),
                # the CPV division this supplier most often contracted under
                func.mode().within_group(Contract.cpv).label("top_cpv"),
            )
            .join(ContractSupplier, ContractSupplier.contract_id == Contract.id)
            .outerjoin(Entity, Entity.nif == ContractSupplier.nif)
            .where(Contract.buyer_nif == nif)
            .group_by(_supplier_id())
        )
        if q:
            # Name or NIF: people paste one as readily as they type the other.
            term = f"%{q.strip()}%"
            stmt = stmt.where(or_(ContractSupplier.name.ilike(term),
                                  ContractSupplier.nif.ilike(term)))
        if form:
            stmt = stmt.where(legal_form_sql(ContractSupplier.name) == form)
        order = self.SUPPLIER_SORTS.get(sort, self.SUPPLIER_SORTS["total"])
        stmt = stmt.order_by(
            (order.desc() if desc else order.asc()).nulls_last()
        ).limit(limit).offset(offset)
        rows = []
        for row in self.session.execute(_year_window(stmt, year_from, year_to, date_from, date_to)):
            data = row._asdict()
            data["sector"] = sector_for(data.pop("top_cpv"))
            # Read off the name, which by law has to carry the suffix. Same
            # reading the filter above uses, so the two can never disagree.
            data["legal_form"] = legal_form_from_name(data.get("name"))
            rows.append(data)
        self._mark_newcomers(rows, newcomer_days, self._period_end(nif, year_from, year_to, date_from, date_to))
        return rows

    def supplier(self, nif: str) -> dict | None:
        """One firm's whole record here, across every câmara loaded.

        Keyed on NIF rather than name: the same firm is spelled several ways
        across the record, and the NIF is what the registry lookup needs anyway.
        """
        ad_count = func.count().filter(Contract.procedure.ilike(AJUSTE_DIRETO))
        row = self.session.execute(
            select(
                func.mode().within_group(ContractSupplier.name).label("name"),
                func.count().label("contracts"),
                func.sum(Contract.value).label("total"),
                func.min(Contract.signed_date).label("first_win"),
                func.max(Contract.signed_date).label("last_win"),
                func.round(cast(100.0 * ad_count / func.count(), Numeric), 1).label("ad_pct"),
                func.count(func.distinct(Contract.buyer_nif)).label("buyers"),
                func.mode().within_group(Contract.cpv).label("top_cpv"),
            )
            .join(ContractSupplier, ContractSupplier.contract_id == Contract.id)
            .where(ContractSupplier.nif == nif)
        ).one_or_none()
        if not row or not row.contracts:
            return None

        data = row._asdict()
        data["nif"] = nif
        data["sector"] = sector_for(data.pop("top_cpv"))
        # Who it sells to, biggest first. A firm that lives off one câmara reads
        # differently from one that sells to fifteen.
        by_dico = {c[0]: c for c in CONCELHOS}
        buyers = [
            r._asdict() for r in self.session.execute(
                select(
                    Contract.buyer_nif.label("nif"),
                    func.mode().within_group(Contract.buyer_name).label("name"),
                    func.count().label("contracts"),
                    func.sum(Contract.value).label("total"),
                )
                .join(ContractSupplier, ContractSupplier.contract_id == Contract.id)
                .where(ContractSupplier.nif == nif)
                .group_by(Contract.buyer_nif)
                .order_by(func.sum(Contract.value).desc().nulls_last())
            )
        ]
        # Resolve each câmara to its territory, so the page can draw them on a
        # map rather than only as a list. A name that cannot be resolved
        # unambiguously yields nothing rather than a guess.
        for b in buyers:
            code = dico_for(concelho_name(b["name"])) if b.get("name") else None
            row = by_dico.get(code) if code else None
            b["dico"] = code
            b["concelho"] = row[1] if row else None
            b["district"] = row[3] if row else None
        data["by_buyer"] = buyers

        # Year by year, so the page can show a shape rather than a single total.
        # A firm that billed steadily for a decade and one that appeared, took
        # everything in one year and vanished have the same total.
        ad_value = func.coalesce(
            func.sum(Contract.value).filter(Contract.procedure.ilike(AJUSTE_DIRETO)), 0)
        data["by_year"] = [
            {
                "label": r.year,
                "contracts": r.contracts,
                "total": float(r.total or 0),
                "ad_pct": (round(100 * float(r.ad_value or 0) / float(r.total), 1)
                           if r.total else None),
            }
            for r in self.session.execute(
                select(
                    Contract.year.label("year"),
                    func.count().label("contracts"),
                    func.coalesce(func.sum(Contract.value), 0).label("total"),
                    ad_value.label("ad_value"),
                )
                .join(ContractSupplier, ContractSupplier.contract_id == Contract.id)
                .where(ContractSupplier.nif == nif, Contract.year.is_not(None))
                .group_by(Contract.year)
                .order_by(Contract.year)
            )
        ]
        return data

    def supplier_contracts(self, nif: str, limit: int, offset: int,
                           q: str | None = None, year: int | None = None,
                           buyer: str | None = None, procedure: str | None = None,
                           sort: str = "signed_date", desc: bool = True) -> list[dict]:
        stmt = (
            select(Contract)
            .join(ContractSupplier, ContractSupplier.contract_id == Contract.id)
            .where(ContractSupplier.nif == nif)
        )
        if q:
            stmt = stmt.where(
                func.to_tsvector("portuguese", func.coalesce(Contract.object, ""))
                .op("@@")(func.plainto_tsquery("portuguese", q))
            )
        if year is not None:
            stmt = stmt.where(Contract.year == year)
        if buyer:
            stmt = stmt.where(Contract.buyer_nif == buyer)
        if procedure:
            stmt = stmt.where(Contract.procedure.ilike(f"%{procedure}%"))
        order = self.CONTRACT_SORTS.get(sort, self.CONTRACT_SORTS["signed_date"])
        rows = self.session.execute(
            stmt.order_by((order.desc() if desc else order.asc()).nulls_last(),
                          Contract.id.desc())
            .limit(limit).offset(offset)
        ).scalars().all()
        # One lookup for the firm's usual spelling, so every row can still name
        # the party it was won by and be flagged on it.
        name = self.session.scalar(
            select(func.mode().within_group(ContractSupplier.name))
            .where(ContractSupplier.nif == nif)
        )
        return [{
            "id": c.id, "object": c.object, "procedure": c.procedure,
            "value": c.value, "signed_date": c.signed_date, "year": c.year,
            "cpv_desc": c.cpv_desc, "n_bidders": c.n_bidders,
            "ad_justification": c.ad_justification,
            # Reading one firm, the other party is the câmara, not the firm
            # itself, so the supplier list is empty and the buyer is named.
            "suppliers": [],
            "parties": ([{"name": name, "nif": nif}] if name else []),
            "buyer_nif": c.buyer_nif,
            "buyer_name": c.buyer_name,
        } for c in rows]

    def contract(self, contract_id: int) -> dict | None:
        """Everything the record holds about one contract.

        The wide fields (base price, criterion, framework, execution window) are
        already in the table and cost nothing extra to read; they only had
        nowhere to be shown until there was a page per contract.
        """
        c = self.session.get(Contract, contract_id)
        if not c:
            return None
        raw = c.raw or {}
        return {
            "id": c.id,
            "object": c.object,
            "procedure": c.procedure,
            "contract_types": c.contract_types or [],
            "value": c.value,
            "base_price": c.base_price,
            "signed_date": c.signed_date,
            "pub_date": c.pub_date,
            "exec_days": c.exec_days,
            "cpv": c.cpv,
            "cpv_desc": c.cpv_desc,
            "sector": sector_for(c.cpv),
            "n_bidders": c.n_bidders,
            "framework": c.framework,
            "justification": c.justification,
            "ad_justification": c.ad_justification,
            "centralized": c.centralized,
            "green": c.green,
            "criterion": c.criterion,
            "buyer_nif": c.buyer_nif,
            "buyer_name": c.buyer_name,
            "suppliers": [{"name": s.name, "nif": s.nif} for s in c.suppliers],
            # name and NIF, so a bidder can be opened like any other company
            "bidders": [{"name": b.name, "nif": b.nif} for b in c.bidders],
            "locations": [loc.municipality for loc in c.locations if loc.municipality],
            # The only two links the record carries. Both are often absent.
            "link_pieces": raw.get("linkPecasProc") or None,
            "link_announcement": raw.get("linkAnuncio") or None,
        }

    def _period_end(self, nif: str, year_from, year_to, date_from=None, date_to=None):
        """Last contract date in the period being read.

        "Recent" has to be measured against what the reader is looking at, not
        against today: viewing 2015 should surface the firms that were new in
        2015, not none at all."""
        stmt = select(func.max(Contract.signed_date)).where(Contract.buyer_nif == nif)
        return self.session.scalar(_year_window(stmt, year_from, year_to, date_from, date_to))

    def _mark_newcomers(self, rows: list[dict], newcomer_days: int,
                        period_end=None) -> None:
        """Flag firms that had barely appeared in public contracting before winning here.

        No procurement dataset carries incorporation dates, so the debut in this
        record is the only available proxy. It is also censored: a firm already
        present on the first day we hold cannot be judged, and gets None rather
        than a confident False.
        """
        if not rows:
            return
        # Keyed the same way the grouping is, or a firm's debut would be read off
        # one of its spellings and the other spellings would look brand new.
        ids = [r.get("nif") or r.get("name") for r in rows if r.get("nif") or r.get("name")]
        debut = dict(
            self.session.execute(
                select(_supplier_id(), func.min(Contract.signed_date))
                .join(Contract, Contract.id == ContractSupplier.contract_id)
                .where(_supplier_id().in_(ids))
                .group_by(_supplier_id())
            ).all()
        ) if ids else {}
        dataset_start = self.session.scalar(select(func.min(Contract.signed_date)))

        for r in rows:
            seen = debut.get(r.get("nif") or r.get("name"))
            first_win = r.get("first_win")
            r["first_seen"] = seen
            r["debut_days"] = (first_win - seen).days if seen and first_win else None
            r["newcomer"] = newcomer_verdict(
                seen, first_win, dataset_start, newcomer_days,
                period_end=period_end, soft_win=r.pop("soft_win", None)
            )

    def flag_context(self, rows: list[dict], settings: Settings,
                     nif: str | None = None) -> FlagContext:
        """Everything the contract flags need that one row cannot see.

        Four lookups for a whole page rather than four per row. A page of fifty
        contracts touches at most a few hundred suppliers, so each of these is
        one indexed query against a small `IN` list.
        """
        ctx = FlagContext(sliced=slice_groups(rows, settings))
        ids = {supplier_id(p) for r in rows for p in (r.get("parties") or [])}
        ids.discard(None)
        if not ids:
            return ctx
        ids = list(ids)

        # First appearance anywhere, at any buyer: a firm that has worked for
        # the next câmara over for a decade is not new, however new it is here.
        ctx.debut = dict(self.session.execute(
            select(_supplier_id(), func.min(Contract.signed_date))
            .join(Contract, Contract.id == ContractSupplier.contract_id)
            .where(_supplier_id().in_(ids))
            .group_by(_supplier_id())
        ).all())
        ctx.dataset_start = self.session.scalar(select(func.min(Contract.signed_date)))

        # Contracts held with THIS buyer, and how many of them came without
        # competition. Scoped to the buyer because "never went to tender" is a
        # statement about this câmara, not about the firm's whole life.
        uncontested = func.count().filter(
            or_(Contract.procedure.ilike(AJUSTE_DIRETO), Contract.n_bidders == 1)
        )
        # Only from a buyer's side. Read from one firm's page the same rows
        # span every câmara it works for, and "nenhum a concurso" across all of
        # them is a different sentence from the one this flag makes.
        ctx.here = {} if not nif else {
            sid: (total, few) for sid, total, few in self.session.execute(
                select(_supplier_id(), func.count(), uncontested)
                .join(Contract, Contract.id == ContractSupplier.contract_id)
                .where(Contract.buyer_nif == nif)
                .where(_supplier_id().in_(ids))
                .group_by(_supplier_id())
            )
        }

        # Status is whatever the register says TODAY, never at signing, and the
        # sentence the reader gets says so.
        ctx.inactive = set(self.session.scalars(
            select(CompanyProfile.nif)
            .where(CompanyProfile.nif.in_(ids))
            .where(CompanyProfile.status.is_not(None))
            .where(CompanyProfile.status != "active")
        ).all())
        return ctx

    def rivals(self, nif: str, limit: int, year_from=None, year_to=None,
               date_from=None, date_to=None) -> list[dict]:
        """Firms that keep turning up in the same tender. Only the ~42% of contracts
        that disclose concorrentes can contribute a row here.

        Takes the same year window as every other read: without it, narrowing the
        page to one year left this panel quietly showing all of them."""
        a, b = ContractBidder.__table__.alias("a"), ContractBidder.__table__.alias("b")
        stmt = (
            select(a.c.name.label("firm_a"), b.c.name.label("firm_b"),
                   # max(), not the grouping key: the pair is grouped by name, and
                   # a firm spelled two ways still resolves to one NIF
                   func.max(a.c.nif).label("nif_a"), func.max(b.c.nif).label("nif_b"),
                   func.count().label("tenders"))
            .select_from(Contract)
            .join(a, a.c.contract_id == Contract.id)
            .join(b, and_(b.c.contract_id == Contract.id, a.c.name < b.c.name))
            .where(Contract.buyer_nif == nif)
            .group_by(a.c.name, b.c.name)
            .having(func.count() > 1)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return [row._asdict()
                for row in self.session.execute(_year_window(stmt, year_from, year_to, date_from, date_to))]

    #: Sort keys the contracts list accepts. Whitelisted: this reaches ORDER BY.
    CONTRACT_SORTS = {
        "value": Contract.value,
        "signed_date": Contract.signed_date,
        "n_bidders": Contract.n_bidders,
        "procedure": Contract.procedure,
        "object": Contract.object,
    }

    def contracts(self, nif: str, *, q: str | None = None, procedure: str | None = None,
                  supplier: str | None = None, min_value: float | None = None,
                  year: int | None = None, municipality: str | None = None,
                  sector: str | None = None, form: str | None = None,
                  year_from: int | None = None, year_to: int | None = None,
                  date_from=None, date_to=None,
                  sort: str = "value", desc: bool = True,
                  limit: int = 50, offset: int = 0) -> list[dict]:
        stmt = (
            select(
                Contract.id, Contract.object, Contract.procedure, Contract.value,
                Contract.signed_date, Contract.year, Contract.cpv_desc,
                # the code as well as its label: slice groups key on its
                # division, and the schema drops it again on the way out
                Contract.cpv,
                Contract.n_bidders, Contract.ad_justification,
                # name and NIF together, not two parallel arrays: a row has to be
                # able to link to the right company page, and two aggregates over
                # the same group are not guaranteed to line up.
                func.array_agg(func.distinct(func.jsonb_build_object(
                    "name", ContractSupplier.name, "nif", ContractSupplier.nif)))
                .filter(ContractSupplier.name.is_not(None)).label("parties"),
            )
            .outerjoin(ContractSupplier, ContractSupplier.contract_id == Contract.id)
            .where(Contract.buyer_nif == nif)
            .group_by(Contract.id)
        )
        if q:
            # One box, two haystacks: the object goes through the Portuguese
            # tsvector index so "refeicoes" finds "refeição", while the supplier
            # is a plain substring match because firm names are not prose.
            stmt = stmt.where(
                or_(
                    func.to_tsvector("portuguese", func.coalesce(Contract.object, ""))
                    .op("@@")(func.plainto_tsquery("portuguese", q)),
                    _supplier_matches(q),
                )
            )
        if procedure:
            stmt = stmt.where(Contract.procedure.ilike(f"%{procedure}%"))
        if supplier:
            # EXISTS, not a filter on the joined row: filtering the join would
            # drop the contract's other suppliers out of the aggregated array.
            stmt = stmt.where(_supplier_matches(supplier))
        if min_value is not None:
            stmt = stmt.where(Contract.value >= min_value)
        # `year` is the table's own one-year facet; year_from/year_to are the
        # page-wide window. They compose: the facet narrows inside the window.
        if year is not None:
            stmt = stmt.where(Contract.year == year)
        stmt = _year_window(stmt, year_from, year_to, date_from, date_to)
        if municipality:
            stmt = stmt.where(_executed_in(municipality))
        if sector:
            # "Outros" is every division the sector table does not name, so it
            # has to be a negation; a named sector is a plain prefix match.
            named = list(CPV_SECTORS)
            divisions = divisions_for(sector)
            division = func.left(Contract.cpv, literal_column("2"))
            stmt = (stmt.where(division.in_(divisions)) if divisions
                    else stmt.where(or_(Contract.cpv.is_(None), division.notin_(named))))
        if form:
            stmt = stmt.where(_supplier_form_matches(form))

        order = self.CONTRACT_SORTS.get(sort, self.CONTRACT_SORTS["value"])
        stmt = stmt.order_by(
            (order.desc() if desc else order.asc()).nulls_last()
        ).limit(limit).offset(offset)
        return [_with_parties(row._asdict()) for row in self.session.execute(stmt)]

    def stats(self, nif: str, year_from=None, year_to=None,
              date_from=None, date_to=None) -> dict:
        """The numbers a table wants: distributions, spreads and the savings gap."""
        scoped = _year_window(
            select(Contract).where(Contract.buyer_nif == nif),
            year_from, year_to, date_from, date_to
        ).subquery()

        headline = self.session.execute(
            select(
                func.count().label("contracts"),
                func.coalesce(func.sum(scoped.c.value), 0).label("total"),
                func.avg(scoped.c.value).label("mean"),
                func.percentile_cont(0.5).within_group(scoped.c.value).label("median"),
                func.percentile_cont(0.9).within_group(scoped.c.value).label("p90"),
                func.max(scoped.c.value).label("largest"),
                func.min(scoped.c.value).label("smallest"),
                func.avg(scoped.c.exec_days).label("mean_exec_days"),
                # the mean is wrecked by multi-year frameworks; the median is not
                func.percentile_cont(0.5).within_group(scoped.c.exec_days).label("median_exec_days"),
                func.coalesce(func.sum(scoped.c.base_price), 0).label("base_total"),
                func.count().filter(scoped.c.base_price.is_not(None)).label("with_base"),
                # a share of the base price, per contract, so two huge contracts
                # cannot speak for the other 259
                func.percentile_cont(0.5).within_group(
                    (100.0 * (scoped.c.base_price - scoped.c.value)
                     / func.nullif(scoped.c.base_price, 0))
                ).label("median_discount_pct"),
                func.count().filter(
                    and_(scoped.c.base_price.is_not(None),
                         scoped.c.base_price > 0,
                         scoped.c.value == scoped.c.base_price)
                ).label("no_discount"),
                func.count(func.distinct(scoped.c.cpv)).label("cpv_codes"),
                func.count().filter(scoped.c.framework != "").label("framework_contracts"),
                func.count().filter(scoped.c.value == 0).label("zero_value"),
            )
        ).one()._asdict()

        by_procedure = [
            r._asdict() for r in self.session.execute(
                select(
                    scoped.c.procedure.label("label"),
                    func.count().label("contracts"),
                    func.coalesce(func.sum(scoped.c.value), 0).label("total"),
                    func.avg(scoped.c.value).label("mean"),
                )
                .group_by(scoped.c.procedure)
                .order_by(func.sum(scoped.c.value).desc().nulls_last())
            )
        ]

        by_year = [
            r._asdict() for r in self.session.execute(
                select(
                    scoped.c.year.label("label"),
                    func.count().label("contracts"),
                    func.coalesce(func.sum(scoped.c.value), 0).label("total"),
                )
                .where(scoped.c.year.is_not(None))
                .group_by(scoped.c.year).order_by(scoped.c.year)
            )
        ]

        # literal_column, not 2: a bind parameter renders as a different $n in the
        # SELECT and the GROUP BY, and Postgres then refuses to match them.
        division = func.left(scoped.c.cpv, literal_column("2"))
        raw_sectors = self.session.execute(
            select(
                division.label("division"),
                func.count().label("contracts"),
                func.coalesce(func.sum(scoped.c.value), 0).label("total"),
            )
            .where(scoped.c.cpv.is_not(None))
            .group_by(division)
        )
        merged: dict[str, dict] = {}
        for row in raw_sectors:
            d = row._asdict()
            name = sector_for(d["division"])
            slot = merged.setdefault(name, {"label": name, "contracts": 0, "total": 0})
            slot["contracts"] += d["contracts"]
            slot["total"] += float(d["total"] or 0)
        by_sector = sorted(merged.values(), key=lambda r: r["total"], reverse=True)

        headline["suppliers_to_half"] = self._suppliers_to_half(scoped)
        by_form = self._by_legal_form(scoped)
        return {"headline": headline, "by_procedure": by_procedure,
                "by_year": by_year, "by_sector": by_sector, "by_form": by_form}

    def _by_legal_form(self, scoped) -> list[dict]:
        """Money by the legal form of the firm that received it.

        Grouped per firm and then per form, not per contract: a contract with
        two suppliers would otherwise have its value counted twice. "Contratos"
        here is therefore the number of firms, which is what the column says.
        """
        per_firm = (
            select(
                legal_form_sql(func.mode().within_group(ContractSupplier.name)).label("form"),
                func.coalesce(func.sum(scoped.c.value), 0).label("v"),
            )
            .join(ContractSupplier, ContractSupplier.contract_id == scoped.c.id)
            .group_by(_supplier_id())
            .subquery()
        )
        rows = self.session.execute(
            select(per_firm.c.form, func.count().label("contracts"),
                   func.sum(per_firm.c.v).label("total"))
            .group_by(per_firm.c.form)
            .order_by(func.sum(per_firm.c.v).desc().nulls_last())
        ).all()
        return [{"label": r.form or "Sem forma no nome", "contracts": r.contracts,
                 "total": float(r.total or 0)} for r in rows]

    def _suppliers_to_half(self, scoped) -> int | None:
        """How few firms it takes to reach half the money. One legible number."""
        rows = self.session.execute(
            select(func.coalesce(func.sum(scoped.c.value), 0).label("v"))
            .join(ContractSupplier, ContractSupplier.contract_id == scoped.c.id)
            .group_by(_supplier_id())
            .order_by(func.sum(scoped.c.value).desc().nulls_last())
        ).all()
        total = sum(float(r.v or 0) for r in rows)
        if total <= 0:
            return None
        running, n = 0.0, 0
        for r in rows:
            running += float(r.v or 0)
            n += 1
            if running >= total / 2:
                return n
        return n

    def map_cells(self, nif: str | None = None, year_from=None, year_to=None,
                  date_from=None, date_to=None) -> list[dict]:
        """Spend by municipality of execution, for one buyer or for the whole country.

        A contract spanning several concelhos is counted in each, so the map total
        can exceed the spend it is drawn from. The UI says so.
        """
        stmt = (
            select(
                ContractLocation.municipality,
                ContractLocation.district,
                func.count(func.distinct(Contract.id)).label("contracts"),
                func.sum(Contract.value).label("total"),
            )
            .join(Contract, Contract.id == ContractLocation.contract_id)
            .where(ContractLocation.municipality != "")
            .group_by(ContractLocation.municipality, ContractLocation.district)
            .order_by(func.sum(Contract.value).desc().nulls_last())
        )
        if nif:
            stmt = stmt.where(Contract.buyer_nif == nif)
        return [row._asdict() for row in self.session.execute(_year_window(stmt, year_from, year_to, date_from, date_to))]

    # ---- raw ingredients for the score -------------------------------------

    def score_inputs(self, nif: str, year_from=None, year_to=None,
                     date_from=None, date_to=None,
                     thresholds: tuple[float, ...] = (), band: float = 0.05,
                     repeat_min: int = 5, newcomer_days: int = 365) -> dict:
        """One pass for the money-shaped aggregates, three small ones per supplier."""
        scoped = _year_window(
            select(Contract).where(Contract.buyer_nif == nif),
            year_from, year_to, date_from, date_to
        ).subquery()

        surfing = or_(*[
            and_(scoped.c.value >= limit * (1 - band), scoped.c.value <= limit)
            for limit in thresholds
        ]) if thresholds else false()

        is_ad = scoped.c.procedure.ilike(AJUSTE_DIRETO)
        totals = self.session.execute(
            select(
                func.count().label("contracts"),
                func.coalesce(func.sum(scoped.c.value), 0).label("total_value"),
                func.coalesce(func.sum(scoped.c.value).filter(is_ad), 0).label("ad_value"),
                func.count().filter(is_ad).label("ad_contracts"),
                func.count().filter(scoped.c.n_bidders == 1).label("single_bidder"),
                func.count().filter(scoped.c.n_bidders.is_not(None)).label("bidders_disclosed"),
                # money, not contracts: the index is a share of euros throughout
                func.coalesce(
                    func.sum(scoped.c.value).filter(scoped.c.n_bidders == 1), 0
                ).label("single_bidder_value"),
                func.coalesce(
                    func.sum(scoped.c.value).filter(scoped.c.n_bidders.is_not(None)), 0
                ).label("disclosed_value"),
                func.coalesce(func.sum(scoped.c.value).filter(surfing), 0).label("surfing_value"),
                func.count().filter(surfing).label("surfing_contracts"),
                func.min(scoped.c.signed_date).label("first_date"),
                func.max(scoped.c.signed_date).label("last_date"),
            )
        ).one()._asdict()

        per_supplier = (
            select(
                _supplier_id().label("sid"),
                func.mode().within_group(ContractSupplier.name).label("name"),
                func.coalesce(func.sum(scoped.c.value), 0).label("v"),
                func.count().label("n"),
                func.min(scoped.c.signed_date).label("first_win"),
                # same "won without competition" test the supplier list uses, so
                # the index and the diamonds in the graph can never disagree
                (func.count().filter(or_(scoped.c.procedure.ilike(AJUSTE_DIRETO),
                                         scoped.c.n_bidders == 1)) > 0).label("soft_win"),
            )
            .join(scoped, scoped.c.id == ContractSupplier.contract_id)
            .group_by(_supplier_id())
            .subquery()
        )
        top3 = (
            select(per_supplier.c.v)
            .order_by(per_supplier.c.v.desc().nulls_last())
            .limit(3).subquery()
        )
        totals["top3_value"] = self.session.execute(
            select(func.coalesce(func.sum(top3.c.v), 0))
        ).scalar()
        totals["suppliers"] = self.session.execute(
            select(func.count()).select_from(per_supplier)
        ).scalar()
        totals["repeat_value"] = self.session.execute(
            select(func.coalesce(func.sum(per_supplier.c.v), 0))
            .where(per_supplier.c.n >= repeat_min)
        ).scalar()
        totals["top_supplier_value"] = self.session.execute(
            select(func.coalesce(func.max(per_supplier.c.v), 0))
        ).scalar()

        # Herfindahl over every supplier, not just three: 68% held by three of
        # six firms and 68% held by three of 232 are not the same market.
        total_value = float(totals["total_value"] or 0)
        if total_value > 0:
            totals["hhi"] = float(self.session.execute(
                select(func.coalesce(
                    func.sum(
                        (cast(per_supplier.c.v, Numeric) / total_value)
                        * (cast(per_supplier.c.v, Numeric) / total_value)
                    ), 0
                ))
            ).scalar() or 0)
        else:
            totals["hhi"] = None

        totals["newcomer_value"] = self._newcomer_value(
            per_supplier, newcomer_days, self._period_end(nif, year_from, year_to, date_from, date_to))
        return totals

    def _newcomer_value(self, per_supplier, newcomer_days: int,
                        period_end=None) -> float | None:
        """Money that went to firms new to public contracting, or None if unknowable."""
        rows = [
            {"sid": r.sid, "first_win": r.first_win, "v": float(r.v or 0),
             "soft_win": r.soft_win}
            for r in self.session.execute(
                select(per_supplier.c.sid, per_supplier.c.v, per_supplier.c.first_win,
                       per_supplier.c.soft_win)
            )
        ]
        if not rows:
            return None
        ids = [r["sid"] for r in rows]
        wins = dict(self.session.execute(
            select(_supplier_id(), func.min(Contract.signed_date))
            .join(Contract, Contract.id == ContractSupplier.contract_id)
            .where(_supplier_id().in_(ids))
            .group_by(_supplier_id())
        ).all())
        dataset_start = self.session.scalar(select(func.min(Contract.signed_date)))
        known, total = False, 0.0
        for r in rows:
            seen = wins.get(r["sid"])
            verdict = newcomer_verdict(seen, r["first_win"], dataset_start, newcomer_days,
                                       period_end=period_end, soft_win=r["soft_win"])
            if verdict is None:
                continue
            known = True
            if verdict:
                total += r["v"]
        return total if known else None
