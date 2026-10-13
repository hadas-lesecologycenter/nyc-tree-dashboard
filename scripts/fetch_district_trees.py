#!/usr/bin/env python3
"""
Build one tree file per Manhattan community district for the map's
"Other Districts" toggle: data/districts/cd101.json … cd112.json.

CB3 (103) is skipped. It loads from data/census.json on every visit and the
rest of the dashboard (stats, zones, Tree Care) is built around it. These
files are fetched only when someone ticks a district, so they never slow the
first load.

Every district goes through the same pipeline as CB3 (fetch_census.py): the
Forestry Tree Points field renames, the street/park join against Planting
Spaces, and the write guard that refuses to replace a district's file with a
fetch that came back badly degraded.

File layout — one row per tree, columns named once in "fields", so a district
is roughly half the size it would be as census.json-style objects:

  {"cd":101,"fields":["tree_id","latitude",…],"boundary":[[[lng,lat],…],…],
   "trees":[
  ["100001",40.703912,-74.012345,"London planetree",…],
  …
  ]}

"boundary" is the district's outer ring(s), for drawing its outline on the map.

Usage:
  python3 scripts/fetch_district_trees.py           # every district
  python3 scripts/fetch_district_trees.py 101 112   # just these
"""

import json, os, sys

import fetch_census as fc
from fetch_cb3_boundary import fetch as fetch_url

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'districts')

# Manhattan community districts as BoroCD codes. 103 is CB3.
DISTRICTS = [101, 102, 104, 105, 106, 107, 108, 109, 110, 111, 112]

# Same sources as fetch_cb3_boundary.py, asking for every district at once.
BOUNDARY_ENDPOINTS = [
    'https://data.cityofnewyork.us/resource/jp9i-3b7y.geojson?$limit=1000',
    (
        'https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services'
        '/NYC_Community_Districts/FeatureServer/0/query'
        '?where=BoroCD%3E%3D101%20AND%20BoroCD%3C%3D112'
        '&outFields=BoroCD&outSR=4326&f=geojson'
    ),
]

# What the map reads, in the column order written to each file — the same
# fields census.json carries. Anything else the fetch brings back stays out.
FIELDS = ['tree_id', 'latitude', 'longitude', 'spc_common', 'spc_latin',
          'tree_dbh', 'health', 'status', 'tree_type', 'planteddate']

# Widen each district's query box a little so a tree sitting exactly on its
# edge is not lost to rounding; the polygon test decides membership anyway.
BOX_PAD = 0.0005


# ── District shapes ───────────────────────────────────────────────────────────

def ring_contains(ring, lng, lat):
    """Even-odd point-in-ring test; ring is [[lng, lat], …]."""
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def ring_bbox(ring):
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


class District:
    """A community district's polygons, with bounding boxes for quick rejects.

    Several Manhattan districts are more than one piece — CB1 takes in
    Governors, Liberty and Ellis Islands, CB8 Roosevelt Island — so each is
    kept as a list of polygons, every polygon an outer ring plus any holes.
    """

    def __init__(self, cd, polygons):
        self.cd = cd
        self.polygons = polygons
        self.parts = [(ring_bbox(rings[0]), rings) for rings in polygons]
        boxes = [box for box, _ in self.parts]
        self.bbox = (min(b[0] for b in boxes), min(b[1] for b in boxes),
                     max(b[2] for b in boxes), max(b[3] for b in boxes))

    def contains(self, lng, lat):
        for (x0, y0, x1, y1), rings in self.parts:
            if not (x0 <= lng <= x1 and y0 <= lat <= y1):
                continue
            if ring_contains(rings[0], lng, lat) and \
                    not any(ring_contains(hole, lng, lat) for hole in rings[1:]):
                return True
        return False

    def outline(self):
        """Outer rings only, rounded to ~10 cm — enough to draw the edge."""
        return [[[round(p[0], 6), round(p[1], 6)] for p in rings[0]]
                for rings in self.polygons]


def district_code(props):
    for key in ('boro_cd', 'BoroCD', 'borocd', 'BORO_CD'):
        value = props.get(key)
        if value not in (None, ''):
            try:
                return int(float(value))
            except (TypeError, ValueError):
                return None
    return None


def polygons_of(geometry):
    """A GeoJSON Polygon or MultiPolygon as a list of polygons (lists of rings)."""
    if geometry['type'] == 'Polygon':
        return [geometry['coordinates']]
    if geometry['type'] == 'MultiPolygon':
        return geometry['coordinates']
    raise ValueError(f'Unexpected geometry type: {geometry["type"]}')


def fetch_boundaries(wanted):
    """cd → polygons for every wanted district any endpoint could supply."""
    found = {}
    for url in BOUNDARY_ENDPOINTS:
        missing = set(wanted) - set(found)
        if not missing:
            break
        print(f'Trying {url[:80]}…')
        try:
            data = fetch_url(url)
        except Exception as e:
            print(f'  Failed: {e}')
            continue
        for feature in data.get('features', []):
            cd = district_code(feature.get('properties') or {})
            if cd in missing and feature.get('geometry'):
                found[cd] = polygons_of(feature['geometry'])
        print(f'  Have {len(found)}/{len(wanted)} district boundaries.')
    return found


# ── Trees ─────────────────────────────────────────────────────────────────────

# Point columns that have refused a within_box query, so later districts skip
# them instead of burning three retries each on a query that cannot work.
_dead_box_columns = set()


def fetch_box(bbox):
    """Every Forestry Tree Point inside bbox, paging past Socrata's row cap.

    Returns None when no point column answers, which sends the district to the
    bulk CSV fallback — the same order of attempts fetch_census.py uses.
    """
    min_lng, min_lat, max_lng, max_lat = (round(v, 6) for v in bbox)
    for column in ('geometry', 'location'):
        if column in _dead_box_columns:
            continue
        # within_box takes the north-west corner first (see fetch_census.py).
        where = f'within_box({column}, {max_lat}, {min_lng}, {min_lat}, {max_lng})'
        rows, offset = [], 0
        try:
            while True:
                page = fc.fetch(fc.FORESTRY_ID, {
                    '$where': where, '$order': ':id',
                    '$limit': fc.LIMIT, '$offset': offset,
                })
                if not isinstance(page, list):
                    raise ValueError(f'unexpected response: {str(page)[:200]}')
                rows.extend(page)
                if len(page) < fc.LIMIT:
                    break
                offset += fc.LIMIT
        except Exception as e:
            print(f'  within_box on {column} failed: {e}')
            _dead_box_columns.add(column)
            continue
        if rows:
            print(f'  {len(rows)} rows in the box (within_box on {column})')
            return rows
    return None


def raw_point(row):
    """(lat, lng) from a raw Forestry row, or None.

    The point arrives as WKT in the CSV export and may arrive as a GeoJSON
    object from the JSON API; fetch_census.normalise_forestry() reads only the
    former, so the latter is handled here.
    """
    for key in ('geometry', 'location'):
        g = row.get(key)
        if isinstance(g, str) and g.strip():
            lat, lng = fc.parse_wkt_point(g)
            if lat is not None:
                return lat, lng
        elif isinstance(g, dict) and isinstance(g.get('coordinates'), list) \
                and len(g['coordinates']) >= 2:
            try:
                return float(g['coordinates'][1]), float(g['coordinates'][0])
            except (TypeError, ValueError):
                pass
    try:
        lat, lng = float(row.get('latitude') or 0), float(row.get('longitude') or 0)
    except (TypeError, ValueError):
        return None
    return (lat, lng) if lat and lng else None


def trees_in(district, raw_rows):
    trees = []
    for raw in raw_rows:
        point = raw_point(raw)
        if not point or not district.contains(point[1], point[0]):
            continue
        tree = fc.normalise_forestry(raw)
        tree['latitude'], tree['longitude'] = point
        trees.append(tree)
    return trees


def fetch_from_csv(districts):
    """One bulk download of the Forestry export, kept to rows in any district."""
    def in_any(row):
        point = raw_point(row)
        return bool(point) and any(d.contains(point[1], point[0]) for d in districts)
    return fc.download_csv_and_filter(fc.FORESTRY_ID, in_any)


# ── Files ─────────────────────────────────────────────────────────────────────

def out_path(cd):
    return os.path.abspath(os.path.join(OUT_DIR, f'cd{cd}.json'))


def compact_row(tree):
    row = []
    for key in FIELDS:
        value = tree.get(key)
        if value is None or str(value).strip() == '':
            row.append(None)
        elif key in ('latitude', 'longitude'):
            row.append(round(float(value), 6))
        elif key == 'planteddate':
            # '2015-10-23 04:00:00.0000000' → '2015-10-23'; the map only ever
            # reads the year out of it.
            row.append(str(value).strip()[:10])
        else:
            row.append(str(value).strip())
    return row


def tree_id_order(row):
    tree_id = str(row[0])
    return (0, int(tree_id), '') if tree_id.isdigit() else (1, 0, tree_id)


def load_existing(path):
    """A district file already on disk, expanded back into tree dicts."""
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            data = json.load(f)
        fields = data['fields']
        return [{k: v for k, v in zip(fields, row) if v is not None}
                for row in data['trees']]
    except Exception as e:
        print(f'  Could not read {path} for comparison: {e}')
        return []


def write_district(path, district, rows):
    # One tree per line keeps each week's git diff down to the trees that
    # actually changed.
    head = json.dumps({'cd': district.cd, 'fields': FIELDS,
                       'boundary': district.outline()}, separators=(',', ':'))
    body = ',\n'.join(json.dumps(r, separators=(',', ':')) for r in rows)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(head[:-1] + ',"trees":[\n' + body + '\n]}\n')


def build_district(district, raw_rows):
    trees = trees_in(district, raw_rows)
    if not trees:
        raise ValueError('no trees inside the district boundary')
    print(f'  {len(trees)} trees inside CD {district.cd}')

    spaces = fc.fetch_planting_spaces(trees)
    if spaces:
        fc.join_tree_type_data(trees, spaces)
    else:
        print('  Warning: no planting spaces — leaving tree_type unset')

    path = out_path(district.cd)
    old = load_existing(path)
    problems = fc.degradation_reasons(old, trees) if old else []
    if problems:
        raise ValueError('; '.join(problems) + ' — kept the existing file')

    rows = sorted((compact_row(t) for t in trees), key=tree_id_order)
    write_district(path, district, rows)
    print(f'  Saved {len(rows)} trees ({os.path.getsize(path) / 1024:.0f} KB) to {path}')
    return len(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

def main(argv):
    try:
        wanted = [int(a) for a in argv] or DISTRICTS
    except ValueError:
        sys.exit(f'District codes must be numbers like 101; got {argv}')
    unknown = [cd for cd in wanted if cd not in DISTRICTS]
    if unknown:
        sys.exit(f'Unknown district(s) {unknown}; choose from {DISTRICTS}')

    failed = {}
    shapes = fetch_boundaries(wanted)
    for cd in wanted:
        if cd not in shapes:
            failed[cd] = 'no boundary from any endpoint'
    districts = [District(cd, shapes[cd]) for cd in wanted if cd in shapes]

    raw_by_cd = {}
    for d in districts:
        print(f'\nCD {d.cd}: Forestry Tree Points inside {[round(v, 4) for v in d.bbox]}…')
        pad = (-BOX_PAD, -BOX_PAD, BOX_PAD, BOX_PAD)
        rows = fetch_box(tuple(v + p for v, p in zip(d.bbox, pad)))
        if rows:
            raw_by_cd[d.cd] = rows

    pending = [d for d in districts if d.cd not in raw_by_cd]
    if pending:
        print(f'\nBox queries failed for {[d.cd for d in pending]} — '
              f'trying the bulk CSV download…')
        try:
            rows = fetch_from_csv(pending)
            for d in pending:
                raw_by_cd[d.cd] = rows   # trees_in() keeps each to its own polygon
        except Exception as e:
            print(f'  CSV download failed: {e}')
            for d in pending:
                failed[d.cd] = f'no tree data ({e})'

    saved = {}
    for d in districts:
        if d.cd not in raw_by_cd:
            continue
        print(f'\nCD {d.cd}: building file…')
        try:
            saved[d.cd] = build_district(d, raw_by_cd[d.cd])
        except Exception as e:
            print(f'  ✗ {e}')
            failed[d.cd] = str(e)

    print('\nSummary:')
    for cd in wanted:
        if cd in saved:
            print(f'  ✓ CD {cd}: {saved[cd]} trees')
        else:
            print(f'  ✗ CD {cd}: {failed.get(cd, "not built")}')
    # A failed district keeps its previous file. Exit non-zero so the workflow
    # run shows red, while the districts that did build still get committed.
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv[1:])
