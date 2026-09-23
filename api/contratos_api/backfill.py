"""Fill the company cache for the suppliers most worth a lookup.

nif.pt is the only registry here behind a quota: one request a minute, a
hundred a day, a thousand a month on the free key. That rules it out of the
request path entirely, so this one-shot walks the cache instead, paced under
the published ceiling, and a reader only ever gets what is already stored.

Which suppliers? The ones that took money *without competition*, biggest first.
"Without competition" is the project's existing definition and not a new one:
an ajuste direto, or a tender the firm was alone in, the same pair
`repositories.suppliers()` calls a soft win. A quota of ninety a night spent on
the ninety firms the indices already point at is worth more than the same
ninety spent alphabetically.

    python -m contratos_api.backfill [--limit N] [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import sys
import time

from contratos_core import (CompanyProfile, Contract, ContractSupplier,
                            Database, get_settings)
from sqlalchemy import func, or_, select

from .services.company import CompanyLookup, is_person_nif

log = logging.getLogger("contratos.backfill")

#: The same spelling `repositories.py` matches on. Kept in step by the test.
AJUSTE_DIRETO = "%Ajuste Direto%"


def targets(session, limit: int) -> list[tuple[str, float]]:
    """Suppliers with no cached profile, ranked by uncontested money taken.

    A NIF already in `company_profiles` is skipped whether it was a hit or a
    miss: the miss is cached on purpose, and re-asking a quota'd register for a
    NIF it has already denied is the one thing this budget cannot afford.
    """
    soft = or_(Contract.procedure.ilike(AJUSTE_DIRETO), Contract.n_bidders == 1)
    stmt = (
        select(
            ContractSupplier.nif,
            func.sum(Contract.value).filter(soft).label("soft_value"),
        )
        .join(Contract, Contract.id == ContractSupplier.contract_id)
        .where(ContractSupplier.nif.is_not(None))
        .where(~select(CompanyProfile.nif)
               .where(CompanyProfile.nif == ContractSupplier.nif)
               .exists())
        .group_by(ContractSupplier.nif)
        .having(func.sum(Contract.value).filter(soft) > 0)
        .order_by(func.sum(Contract.value).filter(soft).desc())
        .limit(limit * 3)  # slack for the NIFs dropped below
    )
    out = []
    for nif, value in session.execute(stmt):
        # IMPIC never publishes a natural person's NIF, so one reaching here is
        # a bad row rather than a company, and the register has nothing for it.
        if not nif or not nif.isdigit() or len(nif) != 9 or is_person_nif(nif):
            continue
        out.append((nif, float(value or 0)))
        if len(out) >= limit:
            break
    return out


def run(limit: int | None = None, dry_run: bool = False) -> int:
    settings = get_settings()
    if not settings.company_nifpt_key:
        log.error("COMPANY_NIFPT_KEY is empty: nothing to do")
        return 0
    limit = limit if limit is not None else settings.company_nifpt_daily
    database = Database(settings)
    filled = 0
    with database.session() as session:
        queue = targets(session, limit)
        log.info("%s suppliers queued, %.0f s apart", len(queue),
                 settings.company_nifpt_interval)
        if dry_run:
            for nif, value in queue:
                log.info("  %s  %12.2f EUR uncontested", nif, value)
            return len(queue)

        lookup = CompanyLookup(session=session, settings=settings, allow_nifpt=True)
        for i, (nif, value) in enumerate(queue):
            if i:
                time.sleep(settings.company_nifpt_interval)
            profile = lookup.get(nif)
            filled += profile is not None
            log.info("%s/%s %s %s (%.0f EUR uncontested)", i + 1, len(queue), nif,
                     "ok" if profile else "no record", value)
    log.info("backfill: %s of %s found", filled, len(queue))
    return filled


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="contratos-backfill")
    parser.add_argument("--limit", type=int, default=None,
                        help="how many NIFs to look up (default: COMPANY_NIFPT_DAILY)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the queue and touch no register")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        datefmt="%H:%M:%S")
    run(args.limit, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
