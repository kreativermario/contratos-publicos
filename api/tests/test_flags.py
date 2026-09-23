"""The contract flags, offline. No database, no request, no network.

These rules used to live in a router, where nothing could reach them without a
server and a loaded database, so nothing tested them at all. Every one of them
is a claim about somebody's contract, which is the last place to find out a
boundary was off by one.
"""
from datetime import date, timedelta

from contratos_api.services.flags import (FlagContext, flags_for, near_limit,
                                          slice_groups)
from contratos_core import Settings

S = Settings(DATABASE_URL="postgresql://u:p@h:5432/d")

FIRM = {"name": "Construções Exemplo, Lda", "nif": "501234567"}
SOLO = {"name": "Exemplo Unipessoal Lda", "nif": "502222222"}
PERSON = {"name": "Maria dos Santos Ferreira", "nif": None}


def row(**kw):
    base = {"id": 1, "value": 10_000.0, "signed_date": date(2024, 6, 1),
            "procedure": "Concurso público", "parties": [FIRM],
            "cpv": "45000000", "n_bidders": 3, "ad_justification": "x"}
    return base | kw


def keys(out):
    return [f["key"] for f in out]


def test_a_plain_contract_earns_nothing():
    assert flags_for(row(), S) == []


def test_a_person_only_counts_above_the_amount():
    small = flags_for(row(value=1_000.0, parties=[PERSON]), S)
    assert "pessoa" not in keys(small)
    big = flags_for(row(value=140_000.0, parties=[PERSON]), S)
    assert "pessoa" in keys(big)
    # the sentence states the amount, so the chip needs no tooltip to mean
    # anything: "uma pessoa, 140 000 EUR"
    flag = next(f for f in big if f["key"] == "pessoa")
    assert flag["data"]["value"] == 140_000.0


def test_a_company_is_never_read_as_a_person():
    """TECNORÉM, S.A was called a person once, because "S.A" without the
    trailing dot was missing from the legal-form table."""
    sa = {"name": "TECNORÉM - Engenharia e Construções, S.A", "nif": None}
    assert "pessoa" not in keys(flags_for(row(value=500_000.0, parties=[sa]), S))


def test_unipessoal_above_the_amount():
    out = keys(flags_for(row(value=140_000.0, parties=[SOLO]), S))
    assert "unipessoal" in out and "pessoa" not in out


def test_alone_in_a_tender_but_not_in_an_ajuste_direto():
    """Ajuste direto does not ask for competition, so one name says nothing."""
    assert "sozinho" in keys(flags_for(row(n_bidders=1), S))
    assert "sozinho" not in keys(
        flags_for(row(n_bidders=1, procedure="Ajuste Direto Regime Geral"), S))


def test_an_ajuste_direto_with_no_justification():
    out = keys(flags_for(row(value=140_000.0, procedure="Ajuste Direto",
                             ad_justification="   "), S))
    assert "sem_explicacao" in out
    # and a filled one is unremarkable
    assert "sem_explicacao" not in keys(flags_for(
        row(value=140_000.0, procedure="Ajuste Direto",
            ad_justification="artigo 27.º"), S))


def test_near_limit_reports_the_gap_not_a_verdict():
    limit = S.thresholds[0]
    value = limit - 6
    out = flags_for(row(value=value, near_limit=near_limit(value, S)), S)
    flag = next(f for f in out if f["key"] == "limite")
    assert flag["data"]["limit"] == limit and flag["data"]["gap"] == 6


def test_a_comfortable_price_is_not_near_any_ceiling():
    assert near_limit(1_000.0, S) is None
    assert near_limit(None, S) is None


def test_a_recent_debut_counts_from_the_first_contract_anywhere():
    signed = date(2024, 6, 1)
    ctx = FlagContext(debut={FIRM["nif"]: date(2024, 2, 1)},
                      dataset_start=date(2015, 1, 1))
    flag = next(f for f in flags_for(
        row(signed_date=signed, procedure="Ajuste Direto"), S, ctx)
                if f["key"] == "estreante")
    assert flag["data"]["months"] == 4


def test_a_newcomer_that_won_an_open_tender_is_not_flagged():
    """The condition CLAUDE.md names and the first version of this flag lost.
    A new firm beating other bidders in an open tender is a new firm doing the
    ordinary thing, and flagging it fired on eight of the first forty contracts
    in Odivelas, every one an open concurso público."""
    ctx = FlagContext(debut={FIRM["nif"]: date(2024, 2, 1)},
                      dataset_start=date(2015, 1, 1))
    assert "estreante" not in keys(flags_for(
        row(procedure="Concurso público", n_bidders=None), S, ctx))
    # undisclosed bidders is not the same as being alone: n_bidders is None for
    # most of the record, and reading it as "alone" would flag the register
    assert "estreante" not in keys(flags_for(
        row(procedure="Concurso público", n_bidders=4), S, ctx))
    # an ajuste direto, or a tender it was the only one to enter, does flag
    assert "estreante" in keys(flags_for(row(procedure="Ajuste Direto"), S, ctx))
    assert "estreante" in keys(flags_for(
        row(procedure="Concurso público", n_bidders=1), S, ctx))


def test_an_old_firm_is_not_a_newcomer():
    ctx = FlagContext(debut={FIRM["nif"]: date(2013, 1, 1)},
                      dataset_start=date(2012, 1, 1))
    assert "estreante" not in keys(flags_for(row(), S, ctx))


def test_a_debut_on_the_first_day_held_says_nothing():
    """A firm present when the record starts has no knowable debut: the window
    is a fact about how many years are loaded, not about the firm."""
    start = date(2024, 1, 1)
    ctx = FlagContext(debut={FIRM["nif"]: start}, dataset_start=start)
    assert "estreante" not in keys(flags_for(row(), S, ctx))


def test_never_tendered_needs_enough_contracts_to_mean_anything():
    few = FlagContext(here={FIRM["nif"]: (2, 2)})
    assert "nunca_a_concurso" not in keys(flags_for(row(), S, few))
    many = FlagContext(here={FIRM["nif"]: (12, 12)})
    flag = next(f for f in flags_for(row(), S, many) if f["key"] == "nunca_a_concurso")
    assert flag["data"]["n"] == 12
    # one tender among them and the sentence is no longer true
    mixed = FlagContext(here={FIRM["nif"]: (12, 11)})
    assert "nunca_a_concurso" not in keys(flags_for(row(), S, mixed))


def test_an_inactive_company_is_flagged_by_nif():
    ctx = FlagContext(inactive={FIRM["nif"]})
    assert "fechada" in keys(flags_for(row(), S, ctx))


def _run(n, value, cpv="45000000", step=30, party=FIRM, buyer="504293125"):
    start = date(2024, 1, 1)
    return [row(id=i, value=value, cpv=cpv, parties=[party], buyer_nif=buyer,
                signed_date=start + timedelta(days=i * step)) for i in range(n)]


def test_a_run_of_awards_under_one_ceiling():
    limit = S.thresholds[0]
    rows = _run(3, limit - 500)
    groups = slice_groups(rows, S)
    assert len(groups) == 3
    n, hit = next(iter(groups.values()))
    assert n == 3 and hit == limit


def test_two_contracts_are_a_coincidence_not_a_pattern():
    assert slice_groups(_run(2, S.thresholds[0] - 500), S) == {}


def test_a_run_whose_total_stays_under_the_ceiling_is_not_one():
    """Three small jobs are three small jobs. The point is the ceiling the run
    as a whole clears while every row stays below it."""
    assert slice_groups(_run(3, 100.0), S) == {}


def test_a_run_spread_over_years_is_not_one():
    assert slice_groups(_run(3, S.thresholds[0] - 500, step=400), S) == {}


def test_different_kinds_of_work_are_not_one_run():
    rows = (_run(2, S.thresholds[0] - 500, cpv="45000000")
            + _run(2, S.thresholds[0] - 500, cpv="79000000"))
    for i, r in enumerate(rows):
        r["id"] = i
    assert slice_groups(rows, S) == {}


def test_the_same_firm_at_three_councils_is_not_one_run():
    """Three small jobs for three different câmaras are three ordinary jobs.
    Without the buyer in the key they read as one split contract."""
    rows = (_run(1, S.thresholds[0] - 500, buyer="a")
            + _run(1, S.thresholds[0] - 500, buyer="b")
            + _run(1, S.thresholds[0] - 500, buyer="c"))
    for i, r in enumerate(rows):
        r["id"] = i
    assert slice_groups(rows, S) == {}


def test_a_run_reads_a_supplier_id_straight_off_the_row():
    """What the repository selects: one row per (contract, supplier) with the
    id already resolved, rather than the nested parties the API shapes."""
    rows = [{"id": i, "sid": FIRM["nif"], "buyer_nif": "504293125",
             "cpv": "45000000", "value": S.thresholds[0] - 500,
             "signed_date": date(2024, 1, 1) + timedelta(days=i * 30)}
            for i in range(3)]
    assert len(slice_groups(rows, S)) == 3


def test_a_run_is_keyed_on_the_nif_not_the_spelling():
    """One firm spelled two ways is one firm. Keying on the name splits it and
    the run disappears, which is the same bug that deflated HHI."""
    other = {"name": "CONSTRUCOES EXEMPLO LDA", "nif": FIRM["nif"]}
    rows = _run(2, S.thresholds[0] - 500) + _run(1, S.thresholds[0] - 500, party=other)
    for i, r in enumerate(rows):
        r["id"] = i
    assert len(slice_groups(rows, S)) == 3
