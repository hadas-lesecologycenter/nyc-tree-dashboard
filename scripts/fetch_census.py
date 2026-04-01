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

# Manhattan Community Board 3 bounding box (fallback if borocd filter unsupported)
CB3_LAT = (40.706, 40.732)
CB3_LNG = (-74.012, -73.965)
BOROCD  = 103          # Manhattan CB3 composite code
LIMIT   = 50_000       # more than enough for CB3

# NYC Open Data Socrata endpoints
FORESTRY_ID  = 'k5ta-2trh'   # Forestry Tree Points — live operational DB
CENSUS_ID    = 'uvpi-gqnh'   # 2015 Street Tree Census
BASE_URL     = 'https://data.cityofnewyork.us/resource/{id}.json'

OUT_PATH   = os.path.join(os.path.dirname(__file__), '..', 'data', 'census.json')
APP_TOKEN  = os.environ.get('SOCRATA_APP_TOKEN', '')  # optional but avoids rate limits

# Required fields the app depends on (in 2015-census naming)
REQUIRED = {'latitude', 'longitude', 'spc_common'}

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
    Plain keys (no $) become simple equality filters (e.g. borocd=103).
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


def borocd_filter(dataset_id):
    """Return True if direct borocd=103 filter works for this dataset."""
    try:
        # Use Socrata simple filter syntax (no $where needed for equality)
        rows = fetch(dataset_id, {'borocd': BOROCD, '$limit': 1})
        return isinstance(rows, list)
    except Exception:
        return False


def bbox_params():
    # $where value is a SoQL expression — build as a plain string; build_url encodes it
    where = (
        f'latitude >= {CB3_LAT[0]} AND latitude <= {CB3_LAT[1]} '
        f'AND longitude >= {CB3_LNG[0]} AND longitude <= {CB3_LNG[1]}'
    )
    return {'$where': where, '$limit': LIMIT}


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
    params = {'$limit': LIMIT}
    if borocd_filter(FORESTRY_ID):
        params['borocd'] = BOROCD   # simple Socrata equality filter
        print(f'  Using borocd={BOROCD} filter')
    else:
        params.update(bbox_params())
        print('  borocd filter unavailable — using lat/lng bounding box')

    rows = fetch(FORESTRY_ID, params)
    if not rows:
        raise ValueError('No rows returned')

    # Print discovered fields from first row
    print(f'  Fields in dataset: {sorted(rows[0].keys())}')

    normalised = [normalise_forestry(r) for r in rows]

    # Validate required fields
    sample = normalised[0]
    missing = REQUIRED - set(sample.keys())
    if missing:
        raise ValueError(f'Missing required fields after normalisation: {missing}')

    return normalised


def fetch_census_2015():
    print('Using 2015 Street Tree Census (fallback)…')
    # Simple equality filter — no $where needed
    params = {'borocd': BOROCD, '$limit': LIMIT}
    return fetch(CENSUS_ID, params)


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
