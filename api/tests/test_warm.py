"""The warmer's one piece of logic worth a test: it must ask for the build id
the site is serving, because that id is half of every cache key. Warm the wrong
one and it faithfully fills entries no reader will ever ask for."""
import json
from contratos_api import warm


class _Resp:
    def __init__(self, body=b"{}", status=200):
        self._body, self.status = body, status
    def read(self): return self._body
    def __enter__(self): return self
    def __exit__(self, *a): return False


def test_build_id_is_read_from_the_running_site(monkeypatch):
    seen = []
    def fake(url, timeout=None):
        seen.append(url)
        return _Resp(json.dumps({"version": "1790424074304"}).encode())
    monkeypatch.setattr(warm.urllib.request, "urlopen", fake)
    assert warm.build_id("http://web:8080", 5) == "1790424074304"
    assert seen == ["http://web:8080/_app/version.json"]


def test_every_warmed_url_carries_that_build_id(monkeypatch):
    asked = []
    def fake(url, timeout=None):
        asked.append(url)
        if url.endswith("version.json"):
            return _Resp(json.dumps({"version": "abc123"}).encode())
        return _Resp(b"[]")
    monkeypatch.setattr(warm.urllib.request, "urlopen", fake)
    assert warm.warm("http://web:8080", 30) == len(warm.PATHS)
    for url in asked[1:]:
        assert url.endswith("?v=abc123"), url


def test_it_warms_nothing_rather_than_the_wrong_thing(monkeypatch):
    """No build id means every key would be a guess, so it does not guess."""
    def fake(url, timeout=None):
        raise OSError("connection refused")
    monkeypatch.setattr(warm.urllib.request, "urlopen", fake)
    assert warm.warm("http://web:8080", 30) == 0


def test_a_slow_endpoint_failing_does_not_stop_the_others(monkeypatch):
    import urllib.error
    def fake(url, timeout=None):
        if url.endswith("version.json"):
            return _Resp(json.dumps({"version": "v1"}).encode())
        if "districts" in url:
            raise urllib.error.HTTPError(url, 504, "gateway timeout", {}, None)
        return _Resp(b"[]")
    monkeypatch.setattr(warm.urllib.request, "urlopen", fake)
    assert warm.warm("http://web:8080", 30) == len(warm.PATHS) - 1
