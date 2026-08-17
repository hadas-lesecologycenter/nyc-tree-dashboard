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
PLANTING_ID  = '82zj-84is'   # Forestry Planting Spaces — has pssite (street/park indicator)
CENSUS_ID    = 'uvpi-gqnh'   # 2015 Street Tree Census
BASE_URL     = 'https://data.cityofnewyork.us/resource/{id}.json'
CSV_URL      = 'https://data.cityofnewyork.us/api/views/{id}/rows.csv?accessType=DOWNLOAD'

OUT_PATH   = os.path.join(os.path.dirname(__file__), '..', 'data', 'census.json')
APP_TOKEN  = os.environ.get('SOCRATA_APP_TOKEN', '')  # optional but avoids rate limits

# Required fields the app depends on (in 2015-census naming)
REQUIRED = {'latitude', 'longitude', 'spc_common'}

# The app's priority tiers are driven entirely by planting year (see calcPriority()
# in index.html): Tier 3 is "planted 2023–2026". Only the live Forestry dataset
# carries a planting date — the 2015 census has no such column — so data without
# it silently collapses the whole tier system into a DBH split with zero Tier 3
# trees. Treat its absence as a failed fetch rather than writing degraded data.
PLANTING_DATE_FIELDS = ('tree_cen_date', 'planteddate')

# Refuse to overwrite census.json if the new fetch returns less than this
# fraction of the trees already on disk — a collapse that large means the
# upstream query degraded, not that CB3 lost thousands of trees.
MIN_TREE_COUNT_RATIO = 0.6

# Fields the dashboard never reads. Every byte here is downloaded by every
# visitor on every page load — index.html appends a cache-busting ?t= to the
# census URL, so nothing is ever served from cache. Dropping these (plus any
# empty values) takes the payload from 9.7 MB to 3.5 MB without losing a single
# tree. 'geometry' and 'location' go too: both are WKT duplicates of the
# latitude/longitude pair the app actually uses.
DROP_FIELDS = {
    'createddate', 'globalid', 'geometry', 'location', 'park_name', 'park_zone',
    'plantingspaceglobalid', 'riskrating', 'riskratingdate', 'stumpdiameter',
    'updateddate',
}

# CB3 NTA names — confirmed from existing census data (most precise filter)
CB3_NTA_NAMES = ('Lower East Side', 'East Village', 'Chinatown')

# CB3 filter strategies to try in order (Socrata SoQL $where expressions).
# The real community board column is 'cb_num' (confirmed from API output).
#
# These are 2015-census columns. The Forestry dataset has none of them — its
# only columns are objectid, dbh, genusspecies, geometry, location, globalid,
# plantingspaceglobalid, tpcondition, tpstructure, createddate, updateddate,
# planteddate — so every one of these returns HTTP 400 against it. Keep the
# two lists separate so neither dataset burns retries on impossible queries.
CENSUS_WHERE_VARIANTS = [
    "cb_num='3' AND borocode='1'",
    "cb_num=3 AND borocode=1",
    "cb_num='3' AND boroname='Manhattan'",
    "nta_name IN ('Lower East Side', 'East Village', 'Chinatown')",
    (f"latitude > {CB3_LAT[0]} AND latitude < {CB3_LAT[1]} "
     f"AND longitude > {CB3_LNG[0]} AND longitude < {CB3_LNG[1]} "
     f"AND boroname='Manhattan'"),
]

# Socrata's signature is within_box(geo_col, nwLat, nwLon, seLat, seLon) — the
# north-west corner first, then the south-east. That means the *higher* latitude
# leads. Passing them the other way round describes an inverted box that matches
# nothing, which is what previously pushed every run onto the 2015 fallback.
_NW_LAT, _NW_LNG = CB3_LAT[1], CB3_LNG[0]
_SE_LAT, _SE_LNG = CB3_LAT[0], CB3_LNG[1]
FORESTRY_WHERE_VARIANTS = [
    f'within_box(geometry, {_NW_LAT}, {_NW_LNG}, {_SE_LAT}, {_SE_LNG})',
    f'within_box(location, {_NW_LAT}, {_NW_LNG}, {_SE_LAT}, {_SE_LNG})',
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
    'plantingspaceglobalid': 'plantingspaceglobalid',  # for joining with planting spaces
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

PLANTING_SPACES_MAP = {
    'globalid':           'plantingspaceglobalid',  # for joining with tree points
    'pssite':             'tree_type',              # 'Street' or 'Park' indicator
    'parkname':           'park_name',
    'parkzone':           'park_zone',
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


def try_cb3_filters(dataset_id, variants):
    """Try each CB3 filter strategy in turn; return rows from the first that works."""
    for where in variants:
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

    # Split ForMS "Genus species - Common name" into separate fields.
    # e.g. "Platanus x acerifolia - London planetree"
    sc = out.get('spc_common', '')
    if sc and ' - ' in sc:
        latin, common = sc.split(' - ', 1)
        out['spc_latin'] = latin.strip()
        out['spc_common'] = common.strip()

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
        rows = try_cb3_filters(FORESTRY_ID, FORESTRY_WHERE_VARIANTS)
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


def fetch_planting_spaces(trees):
    """Fetch Planting Spaces for the given trees, to get tree_type (street/park).

    The Planting Spaces dataset has 1.09M rows citywide, so we must NOT just
    grab the first N — we'd miss almost all CB3 spaces. Instead we query only
    the planting spaces our trees reference, batched by globalid.
    """
    print('Fetching Planting Spaces data for tree type information…')

    # Collect the unique planting space IDs our CB3 trees reference
    needed_ids = sorted({
        t.get('plantingspaceglobalid') for t in trees
        if t.get('plantingspaceglobalid')
    })
    if not needed_ids:
        print('  No plantingspaceglobalid values on trees — cannot fetch')
        return []
    print(f'  Need {len(needed_ids)} planting spaces (joining by globalid)…')

    all_rows = []
    CHUNK = 150  # keep the IN(...) URL well under length limits
    for i in range(0, len(needed_ids), CHUNK):
        chunk = needed_ids[i:i + CHUNK]
        # Socrata SoQL: globalid in ('A','B',…)
        id_list = ','.join(f"'{gid}'" for gid in chunk)
        where = f'globalid in ({id_list})'
        try:
            rows = fetch(PLANTING_ID, {'$where': where, '$limit': CHUNK})
            if isinstance(rows, list):
                all_rows.extend(rows)
        except Exception as e:
            print(f'  Warning: chunk {i // CHUNK + 1} failed: {e}')

    print(f'  Fetched {len(all_rows)} planting spaces')

    # Map to our field names
    mapped = []
    for row in all_rows:
        out = {}
        for k, v in row.items():
            mapped_key = PLANTING_SPACES_MAP.get(k, k)
            out[mapped_key] = v
        mapped.append(out)
    return mapped


def join_tree_type_data(trees, planting_spaces):
    """Join tree points with planting spaces to add tree_type and park_name."""
    # Index planting spaces by globalid for fast lookup
    spaces_by_id = {}
    for space in planting_spaces:
        ps_id = space.get('plantingspaceglobalid')
        if ps_id:
            spaces_by_id[ps_id] = space

    matched = unmatched = 0
    # Add tree_type and park info from planting spaces
    for tree in trees:
        ps_id = tree.get('plantingspaceglobalid')
        if ps_id and ps_id in spaces_by_id:
            matched += 1
            space = spaces_by_id[ps_id]
            tree_type = (space.get('tree_type') or '').strip()
            # pssite values: 'Street' or 'Park'
            if tree_type.lower() == 'street':
                tree['tree_type'] = 'street'
            elif tree_type.lower() == 'park':
                tree['tree_type'] = 'park'
                park_name = (space.get('park_name') or '').strip()
                if park_name:
                    tree['park_name'] = park_name
                park_zone = (space.get('park_zone') or '').strip()
                if park_zone:
                    tree['park_zone'] = park_zone
            else:
                tree['tree_type'] = 'unknown'
        else:
            # No planting space found — mark unknown rather than silently 'street'
            unmatched += 1
            tree['tree_type'] = 'unknown'

    print(f'  Join: {matched} matched, {unmatched} unmatched')
    return trees


def fetch_census_2015():
    print('Using 2015 Street Tree Census (fallback)…')
    rows = try_cb3_filters(CENSUS_ID, CENSUS_WHERE_VARIANTS)
    if not rows:
        raise ValueError('No rows returned from any filter strategy')
    return filter_to_cb3(rows)


# ── Write guard ───────────────────────────────────────────────────────────────

def slim_for_web(trees):
    """Drop fields the dashboard never reads, and any empty values.

    Must run before the write guard so the guard measures what actually lands
    on disk. Values are only ever dropped when blank, and the app reads every
    remaining field with `|| ''`-style fallbacks, so an absent key and an empty
    one behave identically in the browser.
    """
    return [
        {
            k: v for k, v in t.items()
            if k not in DROP_FIELDS and str(v if v is not None else '').strip() != ''
        }
        for t in trees
    ]


def count_with_planting_date(trees):
    return sum(
        1 for t in trees
        if any(str(t.get(f) or '').strip() for f in PLANTING_DATE_FIELDS)
    )


def check_not_degraded(trees, out_path):
    """Compare a fetch against the census.json already on disk.

    Returns a list of reasons the new data is worse than what we have. An empty
    list means it is safe to write. The point is that a degraded upstream
    response must fail the job loudly instead of quietly replacing good data —
    the 2015 fallback in particular has no planting date at all, which silently
    zeroes out every Tier 3 tree in the dashboard.
    """
    if not os.path.exists(out_path):
        return []
    try:
        with open(out_path) as f:
            old = json.load(f)
    except Exception as e:
        print(f'  Could not read existing census.json for comparison: {e}')
        return []
    if not old:
        return []

    reasons = []

    floor = int(len(old) * MIN_TREE_COUNT_RATIO)
    if len(trees) < floor:
        reasons.append(
            f'tree count collapsed: {len(trees)} new vs {len(old)} existing '
            f'(floor is {floor})'
        )

    old_dated = count_with_planting_date(old)
    new_dated = count_with_planting_date(trees)
    if old_dated and not new_dated:
        reasons.append(
            f'planting dates disappeared: {old_dated} trees had one '
            f'({" or ".join(PLANTING_DATE_FIELDS)}), now 0 — every Tier 3 '
            f'tree would vanish from the dashboard'
        )

    return reasons


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    trees = None
    source = None

    try:
        trees = fetch_forestry()
        print(f'  Forestry Tree Points: {len(trees)} CB3 trees')
        source = 'Forestry Tree Points (live)'

        # Fetch planting spaces to get tree_type (street/park) information
        planting_spaces = fetch_planting_spaces(trees)
        if planting_spaces:
            print(f'  Joining with {len(planting_spaces)} planting spaces…')
            trees = join_tree_type_data(trees, planting_spaces)
            # Count by type
            street_count = sum(1 for t in trees if t.get('tree_type') == 'street')
            park_count = sum(1 for t in trees if t.get('tree_type') == 'park')
            unknown_count = sum(1 for t in trees if t.get('tree_type') == 'unknown')
            print(f'  Tree types: {street_count} street, {park_count} park, {unknown_count} unknown')
        else:
            print('  Warning: Could not fetch planting spaces — leaving tree_type unset')

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

    before = len(json.dumps(trees, separators=(',', ':')).encode())
    trees = slim_for_web(trees)
    after = len(json.dumps(trees, separators=(',', ':')).encode())
    print(f'  Trimmed payload for the web: {before/1e6:.1f} MB → {after/1e6:.1f} MB')

    problems = check_not_degraded(trees, out_path)
    if problems:
        print(f'\nRefusing to overwrite census.json with data from {source}:')
        for p in problems:
            print(f'  ✗ {p}')
        print('\nThe existing census.json has been left untouched. This usually '
              'means the Forestry Tree Points dataset was unavailable and the '
              'fetch fell back to the 2015 census, which carries no planting '
              'dates. Re-run once NYC Open Data recovers.')
        sys.exit(1)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(trees, f, separators=(',', ':'))

    size_kb = os.path.getsize(out_path) / 1024
    dated = count_with_planting_date(trees)
    print(f'\nSaved {len(trees)} trees ({size_kb:.0f} KB) to {out_path}')
    print(f'  {dated} trees carry a planting date')
    print(f'Source: {source}')


if __name__ == '__main__':
    main()
