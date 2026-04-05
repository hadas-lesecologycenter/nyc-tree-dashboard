#!/usr/bin/env python3
"""
Fetch the CB3 street tree inventory from NYC Open Data and save to data/census.json.

Tries the Forestry Tree Points dataset first (continuously updated operational DB),
falls back to the 2015 Street Tree Census if the live data is unavailable or lacks
required fields.

Run manually or via the update-census GitHub Action.
"""

import json, sys, urllib.request, urllib.parse, os, time

# ── Config ────────────────────────────────────────────────────────────────────

# Manhattan Community Board 3 bounding box
CB3_LAT = (40.706, 40.732)
CB3_LNG = (-74.012, -73.965)
LIMIT   = 50_000       # more than enough for CB3

# NYC Open Data Socrata endpoints
FORESTRY_ID  = 'hn5i-inap'   # Forestry Tree Points — live operational DB
CENSUS_ID    = 'uvpi-gqnh'   # 2015 Street Tree Census
BASE_URL     = 'https://data.cityofnewyork.us/resource/{id}.json'

OUT_PATH   = os.path.join(os.path.dirname(__file__), '..', 'data', 'census.json')
APP_TOKEN  = os.environ.get('SOCRATA_APP_TOKEN', '')  # optional but avoids rate limits

# Required fields the app depends on (in 2015-census naming)
REQUIRED = {'latitude', 'longitude', 'spc_common'}

# CB3 NTA names — confirmed from existing census data (most precise filter)
CB3_NTA_NAMES = ('Lower East Side', 'East Village', 'Chinatown')

# CB3 filter strategies to try in order (Socrata SoQL $where expressions).
# The real community board column is 'cb_num' (confirmed from API output).
# nta_name filter is a reliable fallback using confirmed output column values.
CB3_WHERE_VARIANTS = [
    # Best: actual community board column (cb_num=3, Manhattan borocode=1)
    "cb_num='3' AND borocode='1'",
    "cb_num=3 AND borocode=1",
    "cb_num='3' AND boroname='Manhattan'",
    # NTA names confirmed from existing census data
    "nta_name IN ('Lower East Side', 'East Village', 'Chinatown')",
    # Geo bbox — lat/lon columns confirmed present; boroname excludes Brooklyn
    (f"latitude > {CB3_LAT[0]} AND latitude < {CB3_LAT[1]} "
     f"AND longitude > {CB3_LNG[0]} AND longitude < {CB3_LNG[1]} "
     f"AND boroname='Manhattan'"),
    # Socrata built-in geo function (for datasets with geometry column)
    f'within_box(the_geom, {CB3_LAT[0]}, {CB3_LNG[0]}, {CB3_LAT[1]}, {CB3_LNG[1]})',
]

# ── Field normalisation maps ──────────────────────────────────────────────────
# Maps Forestry Tree Points field names → 2015 census field names.
# Fields not listed are passed through as-is.
FORESTRY_MAP = {
    'objectid':       'tree_id',
    'spc_latin':      'spc_latin',
    'spc_common':     'spc_common',
    'condition':      'health',        # ForMS uses 'condition' not 'health'
    'status':         'status',
    'dbh':            'tree_dbh',
    'address':        'address',
    'zipcode':        'zipcode',
    'zip_city':       'zip_city',
    'boroname':       'boroname',
    'nta_name':       'nta_name',
    'nta':            'nta_name',
    'sidewalk':       'sidewalk',
    'guards':         'guards',
    'latitude':       'latitude',
    'longitude':      'longitude',
    'borocode':       'borocode',
    'boro_ct':        'boro_ct',
    'block_id':       'block_id',
    'census_tract':   'boro_ct',
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
    """Build a Socrata query URL.
    Keys starting with $ are SoQL params ($where, $limit, etc.) — keep $ literal.
    Values are fully URL-encoded (spaces → %20, etc.).
    """
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
    Applied when a broad filter (e.g. bbox) may have returned neighbouring CBs.
    Falls through unchanged if nta_name is absent (e.g. Forestry dataset).
    """
    if not rows or 'nta_name' not in rows[0]:
        return rows
    before = len(rows)
    kept = [r for r in rows if r.get('nta_name') in CB3_NTA_NAMES]
    if len(kept) != before:
        print(f'  Post-filter: {before} → {len(kept)} trees (kept CB3 NTAs only)')
    return kept


def normalise_forestry(row):
    """Normalise a Forestry Tree Points row to 2015-census field names."""
    out = {}
    for k, v in row.items():
        mapped = FORESTRY_MAP.get(k, k)
        out[mapped] = v
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
    print('Trying Forestry Tree Points (live operational DB)…')
    rows = try_cb3_filters(FORESTRY_ID)
    if not rows:
        raise ValueError('No rows returned from any filter strategy')

    # Print discovered fields from first row
    print(f'  Fields in dataset: {sorted(rows[0].keys())}')

    normalised = [normalise_forestry(r) for r in rows]
    normalised = filter_to_cb3(normalised)

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
