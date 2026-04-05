#!/usr/bin/env python3
"""
Fetch the CB3 street tree inventory from NYC Open Data and save to data/census.json.

Tries the Forestry Tree Points dataset first (continuously updated operational DB),
falls back to the 2015 Street Tree Census if the live data is unavailable or lacks
required fields.

Run manually or via the update-census GitHub Action.
"""

import csv, io, json, sys, urllib.request, urllib.parse, os, time

# ── Config ────────────────────────────────────────────────────────────────────

# Manhattan Community Board 3 bounding box — derived from the exact extent
# of the 4,992 known CB3 street trees in the 2015 census, plus 200m buffer.
CB3_LAT = (40.7073, 40.7360)
CB3_LNG = (-74.0043, -73.9706)
LIMIT   = 50_000       # more than enough for CB3

# NYC Open Data Socrata endpoints
FORESTRY_ID  = 'hn5i-inap'   # Forestry Tree Points — live operational DB
CENSUS_ID    = 'uvpi-gqnh'   # 2015 Street Tree Census
BASE_URL     = 'https://data.cityofnewyork.us/resource/{id}.json'
CSV_URL      = 'https://data.cityofnewyork.us/api/views/{id}/rows.csv?accessType=DOWNLOAD'

OUT_PATH   = os.path.join(os.path.dirname(__file__), '..', 'data', 'census.json')
APP_TOKEN  = os.environ.get('SOCRATA_APP_TOKEN', '')  # optional but avoids rate limits

# Required fields the app depends on (in 2015-census naming)
REQUIRED = {'latitude', 'longitude', 'spc_common'}

# CB3 NTA names — confirmed from existing census data (most precise filter)
CB3_NTA_NAMES = ('Lower East Side', 'East Village', 'Chinatown')

# CB3 filter strategies to try in order (Socrata SoQL $where expressions).
# The real community board column is 'cb_num' (confirmed from API output).
CB3_WHERE_VARIANTS = [
    "cb_num='3' AND borocode='1'",
    "cb_num=3 AND borocode=1",
    "cb_num='3' AND boroname='Manhattan'",
    "nta_name IN ('Lower East Side', 'East Village', 'Chinatown')",
    (f"latitude > {CB3_LAT[0]} AND latitude < {CB3_LAT[1]} "
     f"AND longitude > {CB3_LNG[0]} AND longitude < {CB3_LNG[1]} "
     f"AND boroname='Manhattan'"),
    # Forestry dataset uses 'geometry' as the geo column (confirmed from probe)
    f'within_box(geometry, {CB3_LAT[0]}, {CB3_LNG[0]}, {CB3_LAT[1]}, {CB3_LNG[1]})',
]

# ── Field normalisation maps ──────────────────────────────────────────────────
# Maps Forestry Tree Points field names → 2015 census field names.
# Fields not listed are passed through as-is.
FORESTRY_MAP = {
    # Confirmed column names from hn5i-inap probe (2024):
    # createddate, dbh, genusspecies, geometry, globalid, location,
    # objectid, plantingspaceglobalid, tpcondition, tpstructure, updateddate
    'objectid':           'tree_id',
    'dbh':                'tree_dbh',
    'genusspecies':       'spc_common',   # combined genus+species
    'tpcondition':        'health',
    'tpstructure':        'status',
    # Legacy / 2015-census field names (kept in case dataset schema changes)
    'spc_latin':          'spc_latin',
    'spc_common':         'spc_common',
    'condition':          'health',
    'status':             'status',
    'address':            'address',
    'zipcode':            'zipcode',
    'zip_city':           'zip_city',
    'boroname':           'boroname',
    'nta_name':           'nta_name',
    'nta':                'nta_name',
    'sidewalk':           'sidewalk',
    'guards':             'guards',
    'latitude':           'latitude',
    'longitude':          'longitude',
    'borocode':           'borocode',
    'boro_ct':            'boro_ct',
    'block_id':           'block_id',
    'census_tract':       'boro_ct',
}

# Condition/health value normalisation (Forestry uses different strings)
HEALTH_MAP = {
    'excellent': 'Good',
    'good':      'Good',
    'fair':      'Fair',
    'poor':      'Poor',
    'critical':  'Poor',
    'dead':      'Poor',
    'alive':     'Good',
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def build_url(dataset_id, params):
    """Build a Socrata query URL."""
    parts = []
    for k, v in params.items():
        encoded_v = urllib.parse.quote(str(v), safe='')
        parts.append(f'{k}={encoded_v}')
    return BASE_URL.format(id=dataset_id) + '?' + '&'.join(parts)


def fetch(dataset_id, params):
    url = build_url(dataset_id, params)
    print(f'  GET {url[:120]}…')
    headers = {'Accept': 'application/json', 'User-Agent': 'nyc-tree-dashboard/1.0'}
    if APP_TOKEN:
        headers['X-App-Token'] = APP_TOKEN
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt == 2:
                raise
            print(f'  Retry {attempt+1}/3 after error: {e}')
            time.sleep(5 * (attempt + 1))


def try_cb3_filters(dataset_id):
    """Try each CB3 filter strategy in turn; return rows from the first that works."""
    for where in CB3_WHERE_VARIANTS:
        try:
            rows = fetch(dataset_id, {'$where': where, '$limit': LIMIT})
            if isinstance(rows, list) and rows:
                print(f'  Filter worked: {where[:60]}')
                return rows
        except Exception as e:
            print(f'  Filter failed ({where[:50]}): {e}')
    return None


def filter_to_cb3(rows):
    """Post-fetch safety filter: keep only Manhattan CB3 trees by NTA name.
    Falls through unchanged if nta_name is absent.
    """
    if not rows or 'nta_name' not in rows[0]:
        return rows
    before = len(rows)
    kept = [r for r in rows if r.get('nta_name') in CB3_NTA_NAMES]
    if len(kept) != before:
        print(f'  Post-filter: {before} → {len(kept)} trees (kept CB3 NTAs only)')
    return kept


def download_csv_and_filter(dataset_id, is_cb3_fn):
    """Bulk-download the full CSV export and filter rows in Python.
    This works even when the SODA $where API returns 400.
    """
    url = CSV_URL.format(id=dataset_id)
    print(f'  Downloading full CSV from {url[:80]}…')
    headers = {'User-Agent': 'nyc-tree-dashboard/1.0'}
    if APP_TOKEN:
        headers['X-App-Token'] = APP_TOKEN
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = r.read().decode('utf-8-sig')  # BOM-safe
    print(f'  Downloaded {len(raw) / 1024 / 1024:.1f} MB')

    reader = csv.DictReader(io.StringIO(raw))
    # Normalise header names to lowercase with underscores (Socrata CSV headers
    # may use mixed case or spaces)
    reader.fieldnames = [h.lower().strip().replace(' ', '_') for h in reader.fieldnames]

    rows = [row for row in reader if is_cb3_fn(row)]
    print(f'  Filtered to {len(rows)} CB3 rows')
    return rows


def is_cb3_forestry(row):
    """Return True if a Forestry CSV row belongs to Manhattan CB3.

    The forestry dataset has no cb_num/borocode/nta_name columns — location
    is only in a 'geometry' WKT column (POINT lng lat). Filter by CB3 bbox
    with per-band western limits derived from the 2015 census street tree
    extent (which is the ground truth for CB3 boundaries):

      lat > 40.728 (East Village / 14th St area):  lng > -73.993  (≈3rd Ave)
      lat ≤ 40.728 (LES / Chinatown):              lng > -74.003  (≈Broadway)
    """
    geom = row.get('geometry', '')
    if geom:
        lat, lng = parse_wkt_point(geom)
    else:
        try:
            lat = float(row.get('latitude', '') or 0)
            lng = float(row.get('longitude', '') or 0)
        except (ValueError, TypeError):
            return False

    if lat is None or lat == 0:
        return False

    # Eastern / northern / southern limits are the same for all bands
    if not (CB3_LAT[0] < lat < CB3_LAT[1] and lng < CB3_LNG[1]):
        return False

    # Per-band western limit follows the actual CB3 boundary shape
    west_limit = -73.993 if lat > 40.728 else -74.003
    return lng > west_limit


def parse_wkt_point(wkt):
    """Parse a WKT POINT string → (lat, lng) floats, or (None, None)."""
    # WKT format: "POINT (lng lat)" — longitude first
    try:
        inner = wkt.strip()
        for prefix in ('POINT (', 'POINT('):
            if inner.startswith(prefix):
                inner = inner[len(prefix):].rstrip(')')
                break
        parts = inner.split()
        return float(parts[1]), float(parts[0])   # lat, lng
    except Exception:
        return None, None


def normalise_forestry(row):
    """Normalise a Forestry Tree Points row to 2015-census field names."""
    out = {}
    for k, v in row.items():
        mapped = FORESTRY_MAP.get(k, k)
        out[mapped] = v

    # Extract lat/lng from WKT geometry if not already present as separate fields.
    # The forestry dataset stores location only in a 'geometry' column.
    if 'latitude' not in out or not out['latitude']:
        geom = row.get('geometry', '')
        if geom:
            lat, lng = parse_wkt_point(geom)
            if lat is not None:
                out['latitude']  = str(lat)
                out['longitude'] = str(lng)

    # Normalise health/condition values
    h = (out.get('health') or '').lower()
    if h in HEALTH_MAP:
        out['health'] = HEALTH_MAP[h]

    # Ensure tree_id is a string
    if 'tree_id' not in out and 'objectid' in row:
        out['tree_id'] = str(row['objectid'])
    elif 'tree_id' in out:
        out['tree_id'] = str(out['tree_id'])
    return out


def fetch_forestry():
    """Fetch CB3 trees from the Forestry Tree Points live dataset.
    Tries SODA API first, then bulk CSV download as fallback.
    """
    print('Trying Forestry Tree Points (live operational DB)…')

    # ── Attempt 1: SODA $where queries ──
    # Probe: fetch 1 row to confirm SODA access and discover columns.
    soda_works = False
    try:
        probe = fetch(FORESTRY_ID, {'$limit': 1})
        if probe:
            print(f'  Dataset columns: {sorted(probe[0].keys())}')
            soda_works = True
    except Exception as e:
        print(f'  SODA API not available: {e}')

    if soda_works:
        rows = try_cb3_filters(FORESTRY_ID)
        if rows:
            print(f'  SODA query returned {len(rows)} rows')
            normalised = [normalise_forestry(r) for r in rows]
            normalised = filter_to_cb3(normalised)
            if normalised and not (REQUIRED - set(normalised[0].keys())):
                return normalised

    # ── Attempt 2: Bulk CSV download + Python filter ──
    print('  SODA queries failed — trying bulk CSV download…')
    rows = download_csv_and_filter(FORESTRY_ID, is_cb3_forestry)
    if not rows:
        raise ValueError('No CB3 rows found in CSV download')

    print(f'  CSV columns: {list(rows[0].keys())[:15]}…')
    normalised = [normalise_forestry(r) for r in rows]

    # Validate required fields
    sample = normalised[0]
    missing = REQUIRED - set(sample.keys())
    if missing:
        raise ValueError(f'Missing required fields after normalisation: {missing}')

    return normalised


def fetch_census_2015():
    print('Using 2015 Street Tree Census (fallback)…')
    rows = try_cb3_filters(CENSUS_ID)
    if not rows:
        raise ValueError('No rows returned from any filter strategy')
    return filter_to_cb3(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    trees = None

    try:
        trees = fetch_forestry()
        print(f'  Forestry Tree Points: {len(trees)} CB3 trees')
        source = 'Forestry Tree Points (live)'
    except Exception as e:
        print(f'  Forestry fetch failed: {e}')
        print('  Falling back to 2015 census…')
        try:
            trees = fetch_census_2015()
            print(f'  2015 Census: {len(trees)} CB3 trees')
            source = '2015 Street Tree Census'
        except Exception as e2:
            print(f'  Census fetch also failed: {e2}')
            sys.exit(1)

    out_path = os.path.abspath(OUT_PATH)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(trees, f, separators=(',', ':'))

    size_kb = os.path.getsize(out_path) / 1024
    print(f'\nSaved {len(trees)} trees ({size_kb:.0f} KB) to {out_path}')
    print(f'Source: {source}')


if __name__ == '__main__':
    main()
