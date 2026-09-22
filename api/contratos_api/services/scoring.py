"""The two indices.

Both read the same aggregates. The serious one averages measurable red flags;
the satirical one is a presentation layer on those same numbers, so the joke can
never disagree with the data.

Every scored signal is a **share of euros**. That is the whole point of the unit
rule below: an earlier version averaged "54% of tenders had one bidder" with
"9% of the money skipped a tender", which are not the same quantity and must not
be added together. Count-shaped measures still matter, so they are reported
beside the index as context and never folded into it.

None of this is an accusation. Ajuste direto is a legal procedure; a high score
means "this deserves a look", not "this is a crime".
"""
from __future__ import annotations

from dataclasses import dataclass

from contratos_core import Settings

from ..repositories import MunicipalityRepository

# Scored signals: all of them a percentage of money, all 0-100, all comparable.
# A signal whose value is None (not measurable in this window) is dropped from
# the mean rather than counted as a zero.
SCORED_FLAGS = ("ajuste_direto", "concentracao", "single_bidder",
                "threshold_surf", "newcomer_value")

# Reported, never scored. Either count-shaped (a different unit) or too
# sensitive to how many years happen to be loaded.
CONTEXT_FLAGS = ("ad_contracts", "undisclosed_bidders", "top_supplier",
                 "top3_suppliers", "repeat_winners")

# The satirical index leans on the signals a reader finds damning rather than
# the ones a statistician does. Weights are renormalised over whatever is
# measurable, so a missing signal shifts emphasis instead of scoring zero.
SATIRE_WEIGHTS = {"single_bidder": 0.30, "concentracao": 0.25,
                 "ajuste_direto": 0.20, "threshold_surf": 0.15,
                 "newcomer_value": 0.10}

# The footer disclaimer: provenance and limits, fixed. Nothing here depends on
# the municipality being viewed.
#
# Keys, not prose. The site ships in two languages and the JSON is the same for
# both, so what travels over the wire is a stable identifier; the wording lives
# in the web bundle (DISCLAIMER in messages.ts), in each language.
DISCLAIMER = ("source", "publication_lag", "bidders", "map_overlap", "legal")

# Three bands, aligned to the same cutoffs the severity colours use, so the
# words and the colour can never disagree: below 20 reads clean and green,
# above 45 reads bad and red.
#
# `band` names the verdict, `tone` names the colour. Two fields, because the
# client words the verdict and paints the tone, and neither language's phrasing
# belongs in the API.
VERDICT_BANDS = (
    (20, "clean", "ok"),
    (45, "fishy", "warn"),
    (101, "blatant", "critical"),
)

# Absurd units. Deliberately not per-capita: no population figure ships with the
# contract data, and inventing one would undermine the serious index next to it.
BIFANA = 2.50                    # EUR, a no-nonsense counter price
SALARIO_MINIMO_ANUAL = 870 * 14  # EUR, 14 months


def pct(numerator, denominator) -> float | None:
    numerator, denominator = float(numerator or 0), float(denominator or 0)
    return round(100 * numerator / denominator, 2) if denominator else None


@dataclass(slots=True)
class ScoringService:
    repo: MunicipalityRepository
    settings: Settings

    def score(self, nif: str, year_from: int | None = None, year_to: int | None = None,
              repeat_min: int = 5, date_from=None, date_to=None) -> dict | None:
        raw = self.repo.score_inputs(
            nif, year_from, year_to, date_from, date_to,
            thresholds=self.settings.thresholds,
            band=self.settings.threshold_surf_band,
            repeat_min=repeat_min,
            newcomer_days=self.settings.newcomer_days,
        )
        if not raw["contracts"]:
            return None

        flags = self._flags(raw)
        scored = [flags[k]["pct"] for k in SCORED_FLAGS if flags[k]["pct"] is not None]
        risk = round(sum(scored) / len(scored), 1) if scored else None
        total = float(raw["total_value"] or 0)

        return {
            "nif": nif,
            "period": {"from": year_from, "to": year_to},
            "totals": {"contracts": raw["contracts"], "value": total,
                       "suppliers": raw["suppliers"]},
            "risk_index": risk,
            "scored_flags": list(SCORED_FLAGS),
            "context_flags": list(CONTEXT_FLAGS),
            "satirical_index": self._satirical_index(flags, total),
            "flags": flags,
            "caveats": self._caveats(raw, flags),
        }

    def _flags(self, raw: dict) -> dict:
        total = raw["total_value"]
        years = max(1.0, self._years_covered(raw))

        # Herfindahl is a fraction in [1/N, 1]; as a percentage it is already the
        # 0-100 scale every other signal uses, and it never needs a cutoff at 3.
        hhi = raw.get("hhi")
        concentracao = round(100 * float(hhi), 2) if hhi is not None else None

        newcomer = (pct(raw["newcomer_value"], total)
                    if raw.get("newcomer_value") is not None else None)

        return {
            # ---- scored: share of euros -------------------------------------
            "ajuste_direto":  {"pct": pct(raw["ad_value"], total),
                               "n": raw["ad_contracts"], "unit": "contratos"},
            "concentracao":   {"pct": concentracao, "n": raw["suppliers"],
                               "unit": "empresas"},
            "single_bidder":  {"pct": pct(raw["single_bidder_value"], raw["disclosed_value"]),
                               "n": raw["single_bidder"], "unit": "contratos",
                               "disclosed": raw["bidders_disclosed"]},
            "threshold_surf": {"pct": pct(raw["surfing_value"], total),
                               "n": raw["surfing_contracts"], "unit": "contratos"},
            "newcomer_value": {"pct": newcomer},
            # ---- context: not in the index ----------------------------------
            "ad_contracts":       {"pct": pct(raw["ad_contracts"], raw["contracts"]),
                                   "n": raw["ad_contracts"], "unit": "contratos"},
            "undisclosed_bidders": {"pct": pct(raw["contracts"] - raw["bidders_disclosed"],
                                               raw["contracts"]),
                                    "n": raw["contracts"] - raw["bidders_disclosed"],
                                    "unit": "contratos"},
            "top_supplier":       {"pct": pct(raw["top_supplier_value"], total)},
            "top3_suppliers":     {"pct": pct(raw["top3_value"], total),
                                   "n": raw["suppliers"], "unit": "empresas"},
            # per year, so five contracts does not mean the same thing over one
            # year as it does over fourteen. `n` is the span itself, in years,
            # and it is fractional: never label it as a count of contracts.
            "repeat_winners":     {"pct": pct(raw["repeat_value"], total),
                                   "n": round(years, 1), "unit": "anos"},
        }

    @staticmethod
    def _years_covered(raw: dict) -> float:
        first, last = raw.get("first_date"), raw.get("last_date")
        if not first or not last:
            return 1.0
        return max(1.0, ((last - first).days + 1) / 365.25)

    @staticmethod
    def _satirical_index(flags: dict, total: float) -> dict:
        """Same numbers as the serious index, worse manners."""
        weighted = [(w, flags[k]["pct"]) for k, w in SATIRE_WEIGHTS.items()
                    if flags.get(k, {}).get("pct") is not None]
        score = (round(sum(w * p for w, p in weighted) / sum(w for w, _ in weighted), 1)
                 if weighted else None)
        band, tone = next(
            ((b, t) for limit, b, t in VERDICT_BANDS if (score or 0) < limit),
            VERDICT_BANDS[-1][1:],
        )
        return {
            "score": score,
            "band": band,
            "tone": tone,
            "units": {
                "bifanas": round(total / BIFANA),
                "salarios_minimos_anuais": round(total / SALARIO_MINIMO_ANUAL, 1),
            },
        }

    def _caveats(self, raw: dict, flags: dict) -> list[str]:
        """The footer disclaimer, as keys the client words in its own language.

        Deliberately not per-query: why a particular signal is unmeasurable
        belongs on that signal's card, where the reader is already looking.
        This is about where the data comes from and what it can and cannot say.
        """
        return list(DISCLAIMER)
