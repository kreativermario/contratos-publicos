"""Minimal HTTP helpers: a JSON fetcher, a streaming downloader, a rate limiter."""
from __future__ import annotations

import gzip
import itertools
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Sequence
from pathlib import Path

# dados.gov.pt and apiaberta both sit behind filtering that dislikes scripted
# clients. Rotate a small pool of current desktop Chrome strings; override with
# USER_AGENTS (pipe-separated) without touching code.
DEFAULT_USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
)


class UserAgentPool:
    """Round-robin, not random: reproducible runs, and no clustering on one string."""

    def __init__(self, agents: Sequence[str] | None = None) -> None:
        env_value = os.environ.get("USER_AGENTS", "").strip()
        pool = agents or ([a.strip() for a in env_value.split("|") if a.strip()]
                          or list(DEFAULT_USER_AGENTS))
        self._pool = itertools.cycle(pool)
        self._size = len(pool)

    def __len__(self) -> int:
        return self._size

    def next(self) -> str:
        return next(self._pool)


class RateLimiter:
    """apiaberta allows 30 requests/minute on the free tier; stay under it."""

    def __init__(self, per_minute: int) -> None:
        self._interval = 60.0 / max(per_minute, 1)
        self._last = 0.0

    def wait(self) -> None:
        gap = self._interval - (time.monotonic() - self._last)
        if gap > 0:
            time.sleep(gap)
        self._last = time.monotonic()


class HttpClient:
    def __init__(self, *, timeout: int = 120, headers: dict[str, str] | None = None,
                 agents: UserAgentPool | None = None) -> None:
        self.timeout = timeout
        self.extra_headers = dict(headers or {})
        self.agents = agents or UserAgentPool()

    def _headers(self) -> dict[str, str]:
        """A browser UA with no matching Accept headers is an obvious tell."""
        return {
            "User-Agent": self.agents.next(),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            **self.extra_headers,
        }

    @staticmethod
    def _read(response) -> bytes:
        payload = response.read()
        if response.headers.get("Content-Encoding") == "gzip":
            payload = gzip.decompress(payload)
        return payload

    def get_json(self, url: str, params: dict | None = None) -> dict:
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(self._read(response))

    def download(self, url: str, dest: Path, chunk: int = 1 << 20) -> Path:
        """Streamed, so a 300MB year never lands in memory. No gzip here: these
        files are already compressed and we want them straight to disk."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        headers = self._headers() | {"Accept": "*/*", "Accept-Encoding": "identity"}
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=600) as response, dest.open("wb") as handle:
            while block := response.read(chunk):
                handle.write(block)
        return dest
