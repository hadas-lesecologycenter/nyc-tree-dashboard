#!/usr/bin/env python3
"""
Fetch real street centrelines around CB3 so the 2027 Work Plan can draw each
field day's walk along streets.

The cloud sandbox can't reach data.cityofnewyork.us or OpenStreetMap, so this
runs in GitHub Actions (.github/workflows/fetch-street-centerlines.yml) and
commits what it gets:

  data/streets/cscl-raw.geojson  NYC Street Centerline (CSCL), NYC Open Data
  data/streets/osm-raw.json      OpenStreetMap streets, via the Overpass API

Each source is tried on its own; the run fails only if both fail.
"""
import json, os, sys, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'streets')
# CB3 boundary extent plus about 200 m all round.
S, W, N, E = 40.7062, -74.0024, 40.7362, -73.9692

def get(url, data=None, timeout=180):
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'lesec-nyc-tree-dashboard'})
    token = os.environ.get('SOCRATA_APP_TOKEN')
    if token and 'cityofnewyork' in url:
        req.add_header('X-App-Token', token)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def fetch_cscl():
    where = f"within_box(the_geom, {N}, {W}, {S}, {E})"
    url = 'https://data.cityofnewyork.us/resource/inkn-q76z.geojson?' + urllib.parse.urlencode(
        {'$where': where, '$limit': 50000})
    body = get(url)
    gj = json.loads(body)
    n = len(gj.get('features', []))
    if not n:
        raise RuntimeError('no features')
    with open(os.path.join(OUT, 'cscl-raw.geojson'), 'w') as f:
        json.dump(gj, f)
    print(f'CSCL: {n} features; first properties: {json.dumps(gj["features"][0]["properties"])[:800]}')

def fetch_osm():
    q = f"""[out:json][timeout:120];
way["highway"~"^(primary|secondary|tertiary|residential|unclassified|living_street|pedestrian|service|footway|path|primary_link|secondary_link|tertiary_link)$"]({S},{W},{N},{E});
out tags geom;"""
    body = get('https://overpass-api.de/api/interpreter', data=urllib.parse.urlencode({'data': q}).encode())
    d = json.loads(body)
    n = len(d.get('elements', []))
    if not n:
        raise RuntimeError('no ways')
    with open(os.path.join(OUT, 'osm-raw.json'), 'w') as f:
        json.dump(d, f)
    print(f'OSM: {n} ways')

os.makedirs(OUT, exist_ok=True)
ok = 0
for name, fn in (('CSCL', fetch_cscl), ('OSM', fetch_osm)):
    try:
        fn(); ok += 1
    except Exception as e:
        print(f'{name} failed: {e}', file=sys.stderr)
sys.exit(0 if ok else 1)
