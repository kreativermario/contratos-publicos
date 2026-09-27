"""Fill nginx's API cache from inside the stack, so no reader ever waits.

ponytail: this is scaffolding with a known ceiling, not the fix. The fix is to
stop asking the database to aggregate millions of rows on a page load, by
precomputing the per-mandate figures during ingest. Delete this module the day
/rankings answers in under a second on its own.

The problem it solves is specific. /rankings/districts takes over 100 seconds,
which is Cloudflare's limit for an origin response, so a reader gets a 524 and
nginx never receives a response to store. The cache can therefore never fill,
and every subsequent reader repeats the same two-minute failure: a slow endpoint
whose cache cannot fill is a permanently dead one.

A request from inside the stack goes straight to nginx and never meets
Cloudflare, so it gets nginx's own (generous) timeout and its answer lands in
the same cache a reader reads. The reader then gets a HIT in milliseconds.

The cache key includes the SvelteKit build id, which is how a new bundle is
stopped from reading the previous shape's entries. So the warmer has to ask for
the id the site is actually serving rather than inventing one, or it would
faithfully warm entries nobody ever asks for.
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request

log = logging.getLogger("warm")

#: Only the endpoints that are too slow to serve cold. Everything else answers
#: fast enough that warming it would just be load.
PATHS = (
    "/api/v1/municipalities",
    "/api/v1/rankings/districts",
    "/api/v1/rankings/parties",
    "/api/v1/rankings/map",
    "/api/v1/rankings/elections",
)


def build_id(base: str, timeout: float) -> str | None:
    """The version the site is serving, which is half of every cache key."""
    try:
        with urllib.request.urlopen(f"{base}/_app/version.json", timeout=timeout) as r:
            return json.load(r).get("version")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        log.warning("could not read the build id: %s", exc)
        return None


def warm(base: str, timeout: float) -> int:
    version = build_id(base, timeout=15)
    if not version:
        return 0
    done = 0
    for path in PATHS:
        url = f"{base}{path}?v={version}"
        started = time.monotonic()
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                status = r.status
                r.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
        except (urllib.error.URLError, OSError) as exc:
            log.warning("%s failed: %s", path, exc)
            continue
        took = time.monotonic() - started
        log.info("%s -> %s in %.1fs", path, status, took)
        if status == 200:
            done += 1
    return done


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    base = os.environ.get("WARM_TARGET", "http://web:8080").rstrip("/")
    timeout = float(os.environ.get("WARM_TIMEOUT", "300"))
    done = warm(base, timeout)
    log.info("warmed %s of %s", done, len(PATHS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
