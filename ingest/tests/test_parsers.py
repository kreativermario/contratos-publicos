"""Self-check for the parsing layer: python -m pytest, or just run this file.

Covers the shapes that actually bite - two different 'NIF - Name' conventions,
missing NIFs, names containing the separator, and the streaming array decoder.
"""
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contratos_ingest.parsers import (parse_bidder, parse_bool, parse_cpv,
                                       parse_date, parse_entity,
                                       parse_location, stream_json_array)


def test_parse_entity():
    assert parse_entity("504293125 - Município de Odivelas") == ("504293125", "Município de Odivelas")
    # a real row whose NAME contains the separator - only the first split counts
    assert parse_entity("504615947 - 1 - MEO - SERVIÇOS, S.A.") == ("504615947", "1 - MEO - SERVIÇOS, S.A.")
    # individuals are published without a NIF
    assert parse_entity("- - BRUNO ALEXANDE FRIAS DA ENCARNAÇÃO") == (None, "BRUNO ALEXANDE FRIAS DA ENCARNAÇÃO")
    assert parse_entity("") == (None, None)
    assert parse_entity(None) == (None, None)


def test_html_entities_are_unescaped():
    # real row: IMPIC ships names HTML-escaped, and they reached the UI as "&amp;"
    assert parse_entity("501234567 - MANUEL GOMES DE ALMEIDA &amp; FILHO, LDA")[1] == \
        "MANUEL GOMES DE ALMEIDA & FILHO, LDA"
    assert parse_bidder("510728189-PAREDES &amp; PAREDES, LDA")[1] == "PAREDES & PAREDES, LDA"


def test_parse_bidder():
    # concorrentes use 'NIF-Name' with no spaces - a different shape from adjudicante
    assert parse_bidder("510728189-CLARANET II SOLUTIONS, S.A.") == ("510728189", "CLARANET II SOLUTIONS, S.A.")
    assert parse_bidder("--Visualforma - Tecnologias, S.A.") == (None, "Visualforma - Tecnologias, S.A.")
    assert parse_bidder("") == (None, None)


def test_parse_location():
    assert parse_location("Portugal, Lisboa, Odivelas") == ("Portugal", "Lisboa", "Odivelas")
    assert parse_location("Portugal") == ("Portugal", "", "")
    assert parse_location("") == ("", "", "")
    # a municipality containing a comma must survive intact
    assert parse_location("Portugal, Faro, Vila Real, Santo António")[2] == "Vila Real, Santo António"


def test_scalars():
    assert parse_date("04/12/2025").isoformat() == "2025-12-04"
    assert parse_date("2026-02-23", "%Y-%m-%d").isoformat() == "2026-02-23"
    assert parse_date("") is None and parse_date("garbage") is None
    assert parse_cpv("72210000-0 - Serviços de programação")[0] == "72210000-0"
    assert parse_bool("Não") is False and parse_bool("Sim") is True and parse_bool("") is None


def test_stream_json_array():
    src = [{"idcontrato": str(i), "objectoContrato": "x" * 50, "n": i} for i in range(500)]
    # a chunk far smaller than one record forces every refill path, including the
    # one where the buffer empties exactly on an object boundary
    got = list(stream_json_array(io.StringIO(json.dumps(src)), chunk_size=16))
    assert len(got) == 500, len(got)
    assert got[0]["idcontrato"] == "0" and got[-1]["n"] == 499
    assert list(stream_json_array(io.StringIO("[]"))) == []


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
    print("all passed")
