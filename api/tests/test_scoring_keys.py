"""The API ships keys, never prose.

The site runs in two languages off one JSON payload, so the moment a Portuguese
sentence reappears in `/score` the English pages start printing Portuguese. That
is invisible to every other check here: the shapes stay valid and the types stay
right. This pins the contract instead.
"""
from __future__ import annotations

from contratos_api.services.scoring import DISCLAIMER, VERDICT_BANDS, ScoringService

# Any of these inside a value means somebody wrote a sentence again.
_PROSE = (" ", ".", ",")


def test_the_disclaimer_is_keys():
    assert DISCLAIMER, "the disclaimer must not be empty"
    for key in DISCLAIMER:
        assert isinstance(key, str) and key
        assert not any(ch in key for ch in _PROSE), f"{key!r} reads like prose"


def test_every_band_carries_a_key_and_a_tone():
    tones = {"ok", "warn", "critical"}
    seen = set()
    for limit, band, tone in VERDICT_BANDS:
        assert isinstance(limit, int)
        assert tone in tones, f"unknown tone {tone!r}"
        assert not any(ch in band for ch in _PROSE), f"{band!r} reads like prose"
        seen.add(band)
    assert len(seen) == len(VERDICT_BANDS), "band keys must be distinct"
    assert VERDICT_BANDS[-1][0] > 100, "the last band has to catch every score"


def test_the_satirical_index_carries_no_sentences():
    flags = {k: {"pct": 50.0} for k in
             ("single_bidder", "concentracao", "ajuste_direto",
              "threshold_surf", "newcomer_value")}
    out = ScoringService._satirical_index(flags, 1_000_000.0)
    assert set(out) == {"score", "band", "tone", "units"}, out
    assert out["band"] == "blatant" or out["tone"] in {"ok", "warn", "critical"}
    for key in ("band", "tone"):
        assert not any(ch in out[key] for ch in _PROSE), out


def test_a_missing_score_still_lands_in_a_band():
    out = ScoringService._satirical_index({}, 0.0)
    assert out["score"] is None
    assert out["band"] == VERDICT_BANDS[0][1], "an unscored municipality reads clean"


# The runner iterates globals() as it executes, so it belongs at the bottom:
# a test added below it would never run and never say that it did not.
