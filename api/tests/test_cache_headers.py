"""Cache-Control is a correctness surface, not a performance tweak.

A response held at the edge for an hour is a response that is wrong for an
hour. These tests pin the three rules that were missing: errors are never
cached, /health is never cached, and a successful GET carries the full
browser/shared split rather than one number for both.
"""
from contratos_api.caching import cache_control_for


class FakeSettings:
    cache_browser_seconds = 300
    cache_seconds = 3600
    cache_stale_while_revalidate = 86400
    cache_stale_if_error = 604800


S = FakeSettings()


def test_successful_get_splits_browser_and_shared():
    cc = cache_control_for("GET", 200, "/v1/municipalities/504293125", S)
    assert "max-age=300" in cc, "the browser ttl is the short one"
    assert "s-maxage=3600" in cc, "the CDN holds it far longer than the browser"
    assert "stale-while-revalidate=86400" in cc
    assert "stale-if-error=604800" in cc
    assert cc.startswith("public,")


def test_errors_are_never_cached():
    # Before this existed the header was simply absent on a non-200, which let
    # the CDN pick a default nobody chose. An edge-cached 500 outlives the
    # incident that produced it.
    for status in (304, 400, 404, 429, 500, 502):
        assert cache_control_for("GET", status, "/v1/contracts", S) == "no-store", status


def test_health_is_never_cached():
    # It used to answer with a one hour max-age, which is the wrong answer for
    # the one endpoint whose whole job is to say what is true right now.
    for path in ("/health", "/health/", "/api/health"):
        assert cache_control_for("GET", 200, path, S) == "no-store", path


def test_non_get_is_never_cached():
    for method in ("POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"):
        assert cache_control_for(method, 200, "/v1/contracts", S) == "no-store", method


def test_a_path_merely_containing_health_still_caches():
    # "health" as a substring is not the health endpoint. Guards the matcher
    # against the lazy `"/health" in path` version.
    cc = cache_control_for("GET", 200, "/v1/suppliers/healthcare-lda", S)
    assert cc != "no-store"


# The runner iterates globals() as it executes, so it belongs at the bottom:
# a test added below it would never run and never say that it did not.
