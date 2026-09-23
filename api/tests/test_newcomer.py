"""The newcomer flag is a censored measure; the censoring is the part worth testing.

Three conditions have to hold together, and each one exists because leaving it
out produced a visible wrong answer on the live site.
"""
from datetime import date

from contratos_api.repositories import newcomer_verdict

WINDOW = 365
START = date(2012, 1, 3)
NOW = date(2026, 9, 11)


def test_unknowable_when_the_record_is_too_short():
    # firm debuts before the record covered a full window: cannot tell
    assert newcomer_verdict(date(2012, 6, 1), date(2012, 7, 1), START, WINDOW) is None
    # nothing loaded at all
    assert newcomer_verdict(None, date(2020, 1, 1), START, WINDOW) is None
    assert newcomer_verdict(date(2020, 1, 1), None, START, WINDOW) is None


def test_flags_a_firm_that_wins_soon_after_its_debut():
    assert newcomer_verdict(date(2020, 1, 1), date(2020, 4, 1), START, WINDOW,
                            period_end=date(2020, 6, 1), soft_win=True) is True
    assert newcomer_verdict(date(2020, 1, 1), date(2020, 1, 1), START, WINDOW,
                            period_end=date(2020, 6, 1), soft_win=True) is True


def test_established_firms_are_false_not_none():
    assert newcomer_verdict(date(2015, 1, 1), date(2024, 1, 1), START, WINDOW,
                            period_end=NOW, soft_win=True) is False


def test_the_flag_expires():
    """A debut in 2016 is not news in 2026.

    Without this the flag never aged out, and VITORJRALVES, whose first public
    contract was 2016-11-23, was still being shown as an estreante a decade
    later. Read inside its own period it is correctly a newcomer.
    """
    debut = date(2016, 11, 23)
    assert newcomer_verdict(debut, debut, START, WINDOW,
                            period_end=NOW, soft_win=True) is False
    assert newcomer_verdict(debut, debut, START, WINDOW,
                            period_end=date(2016, 12, 31), soft_win=True) is True


def test_winning_an_open_tender_is_not_a_red_flag():
    """A new firm that beat rivals is new, not suspicious.

    The index only claims to show red flags, so the win has to have been an
    ajuste direto or a tender the firm was alone in.
    """
    assert newcomer_verdict(date(2026, 3, 1), date(2026, 3, 2), START, WINDOW,
                            period_end=NOW, soft_win=True) is True
    assert newcomer_verdict(date(2026, 3, 1), date(2026, 3, 2), START, WINDOW,
                            period_end=NOW, soft_win=False) is False


def test_a_late_first_win_here_is_not_a_debut_here():
    # new to the record in 2026 but only won here much later: not its doorway
    assert newcomer_verdict(date(2026, 1, 1), date(2027, 6, 1), START, WINDOW,
                            period_end=date(2027, 6, 1), soft_win=True) is False
