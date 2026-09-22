"""What may be held, and for how long.

This lives apart from `app.py` on purpose. `app.py` builds the application at
import time, so anything defined beside it needs a database before it can be
read, and a rule this cheap should be testable without one.
"""
from __future__ import annotations


def cache_control_for(method: str, status: int, path: str, settings) -> str:
    """The Cache-Control for one response. Pure, so it can be tested without a server.

    Three rules, and the last two are the ones that were missing.

    Only a successful GET is cacheable. Everything else is `no-store`: an error
    held at the edge outlives the failure that caused it, and until now a 404 or
    a 500 left the header off entirely, which let Cloudflare apply a default we
    never chose.

    `/health` is never cacheable. It answered with a one hour `max-age` before,
    which is the wrong answer for the one endpoint whose entire job is to say
    what is true right now.

    The rest is the split that matters: a short browser ttl so a reader who
    refreshes sees movement, a long shared ttl so the expensive aggregate is
    served from the edge, and stale-while-revalidate so nobody ever waits for a
    cold one.
    """
    if method != "GET" or status != 200:
        return "no-store"
    if path.rstrip("/").rsplit("/", 1)[-1] == "health":
        return "no-store"
    return (f"public, max-age={settings.cache_browser_seconds}, "
            f"s-maxage={settings.cache_seconds}, "
            f"stale-while-revalidate={settings.cache_stale_while_revalidate}, "
            f"stale-if-error={settings.cache_stale_if_error}")
