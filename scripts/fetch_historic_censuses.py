#!/usr/bin/env python3
"""
Fetch the CB3 slice of the 1995, 2005 and 2015 NYC Street Tree Censuses and
save a compact copy of each to data/census-history/<year>.json.

These snapshots are the history estimate_tree_ages.py uses to date trees that
Forestry Tree Points has no planting date for: a tree standing at the same
spot in an earlier census was already planted by then, and its trunk diameter
in that census says roughly how long before.

The censuses never change, so this only needs to run once (or again if the
format below changes). It runs in GitHub Actions — see
.github/workflows/estimate-tree-ages.yml — because it needs NYC Open Data.

File layout — one row per living census tree, columns named once:
  {"year":1995,"source":"kyad-zm4j","format":2,
   "fields":["lat","lng","dbh","latin","common","address"],
   "trees":[[40.71,-73.98,12,"PLATANUS ACERIFOLIA","LONDON PLANETREE","110 EAST 7 STREET"],…]}

The address matters more than the coordinates for 1995 and 2005: those
censuses were recorded by street address and every tree at one address was
geocoded to the same point (up to ~25 trees share one), so only the address
says which trees stood together. It is kept raw; estimate_tree_ages.py
normalises it.

  --if-stale   only fetch years whose file is missing or in an older format
"""

import csv, io, json, os, sys, time, urllib.parse, urllib.request

# Bump when the saved layout changes so --if-stale refetches old files.
FORMAT = 2

# Same CB3 box fetch_census.py uses. Trees just outside it do no harm — the
# age estimator only matches census trees to CB3 Forestry trees a few metres
# away.
CB3_LAT = (40.7073, 40.7360)
CB3_LNG = (-74.0043, -73.9706)

CENSUSES = [
    # year, NYC Open Data dataset id
    (1995, 'kyad-zm4j'),
    (2005, '29bw-z7pj'),
    (2015, 'uvpi-gqnh'),
]

BASE_URL  = 'https://data.cityofnewyork.us/resource/{id}.json'
CSV_URL   = 'https://data.cityofnewyork.us/api/views/{id}/rows.csv?accessType=DOWNLOAD'
APP_TOKEN = os.environ.get('SOCRATA_APP_TOKEN', '')
LIMIT     = 50_000
OUT_DIR   = os.path.join(os.path.dirname(__file__), '..', 'data', 'census-history')

# The three censuses were recorded years apart by different teams and do not
# share column names. Each list is tried in order; the first column present
# wins. The chosen columns are printed so a schema surprise is visible in the
# Actions log.
LAT_COLS    = ('latitude', 'lat', 'y_latitude')
LNG_COLS    = ('longitude', 'lng', 'long', 'x_longitude')
GEOM_COLS   = ('the_geom', 'geometry', 'location', 'location_1', 'geom')
DBH_COLS    = ('tree_dbh', 'diameter', 'dbh')
LATIN_COLS  = ('spc_latin', 'spc_latin_name', 'species_latin', 'latin_name', 'species')
COMMON_COLS = ('spc_common', 'spc_common_name', 'common_name')
STATUS_COLS = ('status', 'condition', 'health')
ADDRESS_COLS = ('address',)
HOUSE_COLS   = ('house_number', 'housenumber')
STREET_COLS  = ('street', 'street_name')

# Census records that are not a living tree. A dead tree or stump still marks
# an occupied spot, but its diameter says nothing about the tree there now.
NOT_ALIVE = ('dead', 'stump', 'shaft', 'vacant', 'planting space')

MIN_TREES = 1000   # CB3 had ~5,000 street trees in 2015; far fewer means a bad fetch


def fetch_json(url):
    headers = {'Accept': 'application/json', 'User-Agent': 'nyc-tree-dashboard/1.0'}
    if APP_TOKEN:
        headers['X-App-Token'] = APP_TOKEN
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt == 2:
                raise
            print(f'  Retry {attempt + 1}/3 after error: {e}')
            time.sleep(5 * (attempt + 1))


def soda_url(dataset_id, params):
    q = '&'.join(f'{k}={urllib.parse.quote(str(v), safe="")}' for k, v in params.items())
    return BASE_URL.format(id=dataset_id) + '?' + q


def pick(cols, candidates):
    return next((c for c in candidates if c in cols), None)


def parse_point(v):
    """(lat, lng) from a Socrata point: GeoJSON dict, WKT string, or None."""
    if isinstance(v, dict):
        coords = v.get('coordinates')
        if coords and len(coords) == 2:
            return float(coords[1]), float(coords[0])
        if 'latitude' in v and 'longitude' in v:
            return float(v['latitude']), float(v['longitude'])
        return None
    if isinstance(v, str) and 'POINT' in v.upper():
        try:
            inner = v[v.index('(') + 1:v.rindex(')')].split()
            return float(inner[1]), float(inner[0])
        except (ValueError, IndexError):
            return None
    return None


def in_box(lat, lng):
    return CB3_LAT[0] < lat < CB3_LAT[1] and CB3_LNG[0] < lng < CB3_LNG[1]


def fetch_rows(dataset_id):
    """Rows of one census inside the CB3 box, as a list of dicts.

    Probes one row to learn the columns, then tries a server-side box filter,
    falling back to the bulk CSV filtered here when the API won't take it.
    """
    probe = fetch_json(soda_url(dataset_id, {'$limit': 1}))
    cols = set(probe[0].keys()) if probe else set()
    print(f'  Columns: {sorted(cols)}')

    lat_c, lng_c, geom_c = pick(cols, LAT_COLS), pick(cols, LNG_COLS), pick(cols, GEOM_COLS)
    wheres = []
    if lat_c and lng_c:
        wheres.append(f'{lat_c} > {CB3_LAT[0]} AND {lat_c} < {CB3_LAT[1]} '
                      f'AND {lng_c} > {CB3_LNG[0]} AND {lng_c} < {CB3_LNG[1]}')
    if geom_c:
        # within_box takes the north-west corner first (see fetch_census.py).
        wheres.append(f'within_box({geom_c}, {CB3_LAT[1]}, {CB3_LNG[0]}, '
                      f'{CB3_LAT[0]}, {CB3_LNG[1]})')
    for where in wheres:
        try:
            rows = fetch_json(soda_url(dataset_id, {'$where': where, '$limit': LIMIT}))
            if isinstance(rows, list) and len(rows) >= MIN_TREES:
                print(f'  Filter worked: {where[:70]} → {len(rows)} rows')
                return rows
            print(f'  Filter returned {len(rows) if isinstance(rows, list) else "?"} rows: {where[:70]}')
        except Exception as e:
            print(f'  Filter failed ({where[:50]}): {e}')

    print('  Falling back to bulk CSV download…')
    req = urllib.request.Request(CSV_URL.format(id=dataset_id),
                                 headers={'User-Agent': 'nyc-tree-dashboard/1.0',
                                          **({'X-App-Token': APP_TOKEN} if APP_TOKEN else {})})
    with urllib.request.urlopen(req, timeout=600) as r:
        raw = r.read().decode('utf-8-sig')
    print(f'  Downloaded {len(raw) / 1e6:.0f} MB')
    reader = csv.DictReader(io.StringIO(raw))
    reader.fieldnames = [h.lower().strip().replace(' ', '_') for h in reader.fieldnames]
    print(f'  CSV columns: {reader.fieldnames}')
    return [row for row in reader if (ll := row_latlng(row)) and in_box(*ll)]


def row_latlng(row):
    cols = row.keys()
    lat_c, lng_c = pick(cols, LAT_COLS), pick(cols, LNG_COLS)
    if lat_c and lng_c:
        try:
            lat, lng = float(row[lat_c]), float(row[lng_c])
            if lat and lng:
                return lat, lng
        except (TypeError, ValueError):
            pass
    geom_c = pick(cols, GEOM_COLS)
    return parse_point(row.get(geom_c)) if geom_c else None


def compact(rows):
    """Living trees with a location and diameter → [lat, lng, dbh, latin, common, address]."""
    if not rows:
        return []
    cols = set().union(*(r.keys() for r in rows[:50]))
    dbh_c, latin_c = pick(cols, DBH_COLS), pick(cols, LATIN_COLS)
    common_c, status_c = pick(cols, COMMON_COLS), pick(cols, STATUS_COLS)
    addr_c, house_c, street_c = pick(cols, ADDRESS_COLS), pick(cols, HOUSE_COLS), pick(cols, STREET_COLS)
    print(f'  Using dbh={dbh_c} latin={latin_c} common={common_c} status={status_c} '
          f'address={addr_c or (house_c, street_c)}')
    if not dbh_c or not (latin_c or common_c):
        raise ValueError(f'no diameter or species column among {sorted(cols)}')

    statuses = {}
    out = []
    for r in rows:
        status = str(r.get(status_c) or '').strip()
        statuses[status] = statuses.get(status, 0) + 1
        if any(word in status.lower() for word in NOT_ALIVE):
            continue
        ll = row_latlng(r)
        if not ll or not in_box(*ll):
            continue
        try:
            dbh = float(r.get(dbh_c) or 0)
        except ValueError:
            continue
        if dbh <= 0:
            continue
        address = str(r.get(addr_c) or '').strip()
        if not any(ch.isdigit() for ch in address) and house_c and street_c:
            address = f'{r.get(house_c) or ""} {r.get(street_c) or ""}'.strip()
        out.append([round(ll[0], 7), round(ll[1], 7), dbh,
                    str(r.get(latin_c) or '').strip(), str(r.get(common_c) or '').strip(), address])
    print(f'  Status values: {dict(sorted(statuses.items(), key=lambda kv: -kv[1]))}')
    print(f'  Sample addresses: {[t[5] for t in out[:8]]}')
    return out


def is_current(path):
    try:
        with open(path) as f:
            return json.load(f).get('format') == FORMAT
    except (OSError, ValueError):
        return False


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    if_stale = '--if-stale' in sys.argv[1:]
    failed = []
    for year, dataset_id in CENSUSES:
        path = os.path.join(OUT_DIR, f'{year}.json')
        if if_stale and is_current(path):
            print(f'\n{year}: {os.path.relpath(path)} is current — skipped')
            continue
        print(f'\n{year} Street Tree Census ({dataset_id})')
        try:
            trees = compact(fetch_rows(dataset_id))
            if len(trees) < MIN_TREES:
                raise ValueError(f'only {len(trees)} living trees in the CB3 box')
        except Exception as e:
            print(f'  ✗ {e}')
            failed.append(year)
            continue
        with open(path, 'w') as f:
            json.dump({'year': year, 'source': dataset_id, 'format': FORMAT,
                       'fields': ['lat', 'lng', 'dbh', 'latin', 'common', 'address'],
                       'trees': trees}, f, separators=(',', ':'))
        print(f'  Saved {len(trees)} living trees to {os.path.relpath(path)}')

    if failed:
        print(f'\nFailed: {failed}. Files for those years were left as they were.')
        sys.exit(1)


if __name__ == '__main__':
    main()
