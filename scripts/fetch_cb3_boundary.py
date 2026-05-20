#!/usr/bin/env python3
"""Download the official CB3 Manhattan boundary polygon from NYC Open Data.

Fetches the NYC Community Districts GeoJSON, extracts the CB3 (BoroCD=103)
feature, and saves its outer ring as data/cb3-boundary.json — a simple
[[lng, lat], ...] array that the frontend loads for point-in-polygon filtering.
"""

import json, os, sys, time, urllib.request

GEOJSON_URL = (
    'https://data.cityofnewyork.us/api/geospatial/jp9i-3b7y'
    '?method=export&type=GeoJSON'
)
OUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cb3-boundary.json')


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'nyc-tree-dashboard/1.0'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt == 2:
                raise
            print(f'  Retry {attempt + 1}/3 after error: {e}')
            time.sleep(5 * (attempt + 1))


def largest_ring(geometry):
    """Return the largest outer ring from a Polygon or MultiPolygon."""
    if geometry['type'] == 'Polygon':
        return geometry['coordinates'][0]
    if geometry['type'] == 'MultiPolygon':
        rings = [coords[0] for coords in geometry['coordinates']]
        return max(rings, key=len)
    raise ValueError(f'Unexpected geometry type: {geometry["type"]}')


def main():
    print('Fetching NYC Community Districts GeoJSON…')
    data = fetch(GEOJSON_URL)

    feature = None
    for f in data.get('features', []):
        props = f.get('properties', {})
        borocd = (props.get('BoroCD') or props.get('borocd') or
                  props.get('BORO_CD') or props.get('boro_cd') or '')
        if str(borocd) == '103':
            feature = f
            break

    if not feature:
        keys = list(data['features'][0]['properties'].keys()) if data.get('features') else []
        print(f'ERROR: CB3 (BoroCD=103) not found. Feature property keys: {keys}')
        sys.exit(1)

    ring = largest_ring(feature['geometry'])
    print(f'CB3 polygon: {len(ring)} vertices')

    out_path = os.path.abspath(OUT_PATH)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(ring, f, separators=(',', ':'))
    print(f'Saved to {out_path}')


if __name__ == '__main__':
    main()
