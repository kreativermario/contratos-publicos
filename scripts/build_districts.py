"""Build a district-level GeoJSON by dissolving the concelho geometry.

The site only ever had one geometry file, the 308 concelhos. Painting every
concelho of a district the same colour looks like a district map until two
neighbouring districts land on the same party, at which point the border between
them disappears and the map lies. Real district polygons are the fix, and they
are derivable: a district is exactly the union of its concelhos.
"""
import json
import sys
from collections import defaultdict

from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

# Enough to swallow the gaps float precision leaves between two concelhos that
# are meant to share an edge, and small enough not to eat a real coastline.
GAP = 0.004
# This map is only ever drawn at country scale, so it can be coarse.
TOLERANCE = 0.0025
# An island worth drawing. Below this it is a rock, or a union artefact.
MIN_PART = 3e-4


def solid(geom):
    """Outer rings only, and only the parts big enough to see.

    A district has no enclaves. Every interior ring here is a sliver left where
    two concelho boundaries failed to coincide exactly, and each one renders as
    a white speck on an otherwise solid district.
    """
    parts = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    kept = [Polygon(p.exterior) for p in parts if p.area >= MIN_PART]
    if not kept:                       # a district of one small island
        kept = [Polygon(max(parts, key=lambda p: p.area).exterior)]
    return kept[0] if len(kept) == 1 else MultiPolygon(kept)


src, dst = sys.argv[1], sys.argv[2]
geo = json.load(open(src, encoding="utf-8"))

groups = defaultdict(list)
for f in geo["features"]:
    district = (f["properties"] or {}).get("district")
    if district:
        # The source has self-touching rings that GEOS refuses to union. Repair
        # each concelho before merging rather than after: one bad ring otherwise
        # poisons the whole district.
        groups[district].append(make_valid(shape(f["geometry"])).buffer(0))

features = []
for district, shapes in sorted(groups.items()):
    merged = unary_union(shapes)
    # Close the gaps first, then simplify, then drop what is left over. Doing it
    # in the other order lets simplification open new gaps that nothing closes.
    merged = merged.buffer(GAP).buffer(-GAP)
    merged = merged.simplify(TOLERANCE, preserve_topology=True)
    merged = solid(merged)
    features.append({
        "type": "Feature",
        "properties": {"name": district, "key": district, "concelhos": len(shapes)},
        "geometry": mapping(merged),
    })

json.dump({"type": "FeatureCollection", "features": features},
          open(dst, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

holes = sum(len(p.interiors)
            for f in features
            for p in ([shape(f["geometry"])] if f["geometry"]["type"] == "Polygon"
                      else shape(f["geometry"]).geoms))
print(f"{len(features)} districts, "
      f"{sum(f['properties']['concelhos'] for f in features)} concelhos, "
      f"{holes} interior rings")

# Run with shapely available, from the repo root:
#
#   python3 -m venv .venv && .venv/bin/pip install shapely
#   .venv/bin/python scripts/build_districts.py \
#       web/static/pt-municipios.geojson web/static/pt-distritos.geojson
#
# The output is committed, so this only has to run when the concelho geometry
# changes. It is not part of the image build.
