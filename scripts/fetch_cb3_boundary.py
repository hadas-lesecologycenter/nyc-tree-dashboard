#!/usr/bin/env python3
"""Download the official CB3 Manhattan boundary polygon from NYC Open Data.

Tries multiple endpoints in order, saves the outer ring as
data/cb3-boundary.json — a [[lng, lat], ...] array the frontend
uses for point-in-polygon filtering.
"""

import json, os, sys, time, urllib.request, urllib.error

OUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'cb3-boundary.json')

ENDPOINTS = [
    # Socrata GeoJSON API — filtered to CB3
    'https://data.cityofnewyork.us/resource/jp9i-3b7y.geojson?boro_cd=103',
    # Socrata GeoJSON API — all districts (filter in Python)
    'https://data.cityofnewyork.us/resource/jp9i-3b7y.geojson',
    # ArcGIS REST — NYC Community Districts feature service
    (
        'https://services5.arcgis.com/GfwWNkhOj9bNBqoJ/arcgis/rest/services'
        '/NYC_Community_Districts/FeatureServer/0/query'
        '?where=BoroCD%3D103&outFields=BoroCD&outSR=4326&f=geojson'
    ),
]


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'nyc-tree-dashboard/1.0'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if attempt == 2 or e.code < 500:
                raise
            print(f'  Retry {attempt + 1}/3 after {e}')
            time.sleep(5 * (attempt + 1))
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


def find_cb3(data):
    for f in data.get('features', []):
        props = f.get('properties', {})
        borocd = (props.get('BoroCD') or props.get('borocd') or
                  props.get('BORO_CD') or props.get('boro_cd') or '')
        if str(borocd) == '103':
            return f
    return None


def main():
    feature = None
    for url in ENDPOINTS:
        print(f'Trying {url[:80]}…')
        try:
            data = fetch(url)
            feature = find_cb3(data)
            if feature:
                print('  Found CB3 feature.')
                break
            # If filtered endpoint returned nothing, the all-districts one may still work
            if data.get('features'):
                keys = list(data['features'][0]['properties'].keys())
                print(f'  CB3 not found. Property keys: {keys}')
        except Exception as e:
            print(f'  Failed: {e}')

    if not feature:
        print('ERROR: Could not retrieve CB3 boundary from any endpoint.')
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
