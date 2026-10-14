#!/usr/bin/env python3
"""
Fetch the streets around CB3 so the 2027 Work Plan can draw each field day's
walk along them (scripts/build_workplan_routes.py).

The cloud sandbox can't reach OpenStreetMap, so this runs in GitHub Actions
(.github/workflows/fetch-street-centerlines.yml, started by hand) and commits:

  data/streets/cb3-streets.json   OpenStreetMap roads people walk along, via
                                  the Overpass API: name, road type, and the
                                  line as [lng, lat] points

Footpaths, sidewalks, service roads and the FDR Drive are left out, so a route
can only follow a street. NYC's own centreline file (CSCL) was tried first, but
the copy NYC Open Data returned on 2026-10-14 was missing pieces, such as
Stanton St at Willett St.
"""
import json, os, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'streets', 'cb3-streets.json')
# CB3 boundary extent plus about 200 m all round.
S, W, N, E = 40.7062, -74.0024, 40.7362, -73.9692
ROADS = ('primary', 'secondary', 'tertiary', 'residential', 'unclassified', 'living_street',
         'pedestrian', 'primary_link', 'secondary_link', 'tertiary_link')

q = f"""[out:json][timeout:120];
way["highway"~"^({'|'.join(ROADS)})$"]({S},{W},{N},{E});
out tags geom;"""
req = urllib.request.Request('https://overpass-api.de/api/interpreter',
                             data=urllib.parse.urlencode({'data': q}).encode(),
                             headers={'User-Agent': 'lesec-nyc-tree-dashboard'})
with urllib.request.urlopen(req, timeout=180) as r:
    d = json.load(r)
ways = [{'name': e['tags'].get('name'), 'highway': e['tags']['highway'],
         'coords': [[round(p['lon'], 7), round(p['lat'], 7)] for p in e['geometry']]}
        for e in d['elements'] if e.get('geometry')]
if not ways:
    raise SystemExit('Overpass returned no streets')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w') as f:
    json.dump({'source': 'OpenStreetMap contributors (ODbL), via the Overpass API', 'ways': ways},
              f, separators=(',', ':'))
print(f'{len(ways)} streets written to {os.path.relpath(OUT, ROOT)}')
