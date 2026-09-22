"""Pure parsing helpers for the shapes IMPIC and apiaberta actually publish.

No I/O, no database - everything here is unit-testable on its own.
"""
from __future__ import annotations

import html
import json
import re
from collections.abc import Iterator
from datetime import date, datetime
from typing import Any, TextIO

_BIDDER_RE = re.compile(r"^(\d*)\s*-\s*(.+)$")


def _clean(raw: str | None) -> str:
    """IMPIC publishes entity names HTML-escaped: 'ALMEIDA &amp; FILHO, LDA'."""
    return html.unescape((raw or "").strip())


def parse_entity(raw: str | None) -> tuple[str | None, str | None]:
    """'504293125 - Municipio de Odivelas' -> ('504293125', 'Municipio de Odivelas').

    Names legitimately contain the separator ('504615947 - 1 - MEO - SERVICOS, S.A.'),
    so split exactly once. Individuals are published without a NIF ('- - BRUNO ...').
    """
    text = _clean(raw)
    if not text:
        return None, None
    head, sep, tail = text.partition(" - ")
    if not sep:
        return None, text
    nif = head.strip()
    return (nif if nif.isdigit() else None), tail.strip() or None


def parse_bidder(raw: str | None) -> tuple[str | None, str | None]:
    """concorrentes use a tighter shape than adjudicante: '510728189-CLARANET, S.A.'
    and '--Visualforma - Tecnologias, S.A.' when the NIF is missing."""
    text = _clean(raw)
    if not text:
        return None, None
    if match := _BIDDER_RE.match(text):
        return (match.group(1) or None), match.group(2).strip(" -") or None
    return None, text


def parse_location(raw: str | None) -> tuple[str, str, str]:
    """'Portugal, Lisboa, Odivelas' -> (country, district, municipality).

    Empty strings rather than None: these three are a composite primary key.
    """
    parts = [p.strip() for p in (raw or "").split(",") if p.strip()]
    if not parts:
        return "", "", ""
    if len(parts) == 1:
        return parts[0], "", ""
    if len(parts) == 2:
        return parts[0], parts[1], ""
    return parts[0], parts[1], ", ".join(parts[2:])


def parse_date(raw: str | None, fmt: str = "%d/%m/%Y") -> date | None:
    try:
        return datetime.strptime((raw or "").strip(), fmt).date()
    except ValueError:
        return None


def parse_cpv(raw: str | None) -> tuple[str | None, str | None]:
    """'72210000-0 - Servicos de programacao' -> ('72210000-0', 'Servicos de programacao')."""
    code, sep, desc = (raw or "").partition(" - ")
    if not sep:
        return None, (raw or None)
    return code.strip() or None, desc.strip() or None


def parse_bool(raw: str | None) -> bool | None:
    value = (raw or "").strip().lower()
    if value in ("sim", "true", "1"):
        return True
    if value in ("nao", "não", "false", "0"):
        return False
    return None


def first(value: Any) -> Any:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def stream_json_array(fp: TextIO, chunk_size: int = 1 << 20) -> Iterator[dict]:
    """Yield objects from a top-level JSON array without holding the file in RAM.

    ponytail: hand-rolled because json.load() needs roughly 10x the file size in
    memory (a 304MB year -> ~3GB) and would OOM a modest container. Measured at
    177MB peak across the real 2026 file. Swap for ijson if the shape gets richer.

    Separators are re-stripped on every pass: a refill can land ", " at the head of
    an emptied buffer, and raw_decode() will not skip leading whitespace.
    """
    decoder = json.JSONDecoder()
    buf = ""
    started = False
    while True:
        buf = buf.lstrip().lstrip(",").lstrip()
        if not buf:
            more = fp.read(chunk_size)
            if not more:
                return
            buf = more
            continue
        if not started:
            if buf[0] != "[":
                raise ValueError("expected a top-level JSON array")
            buf, started = buf[1:], True
            continue
        if buf[0] == "]":
            return
        try:
            obj, end = decoder.raw_decode(buf)
        except ValueError:          # incomplete object - pull more and retry
            more = fp.read(chunk_size)
            if not more:
                return
            buf += more
            continue
        yield obj
        buf = buf[end:]
