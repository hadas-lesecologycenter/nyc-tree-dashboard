#!/usr/bin/env python3
"""
Fetch New York State's Disadvantaged Communities (DAC) data for Manhattan's
census tracts, and the shapes of the tracts around CB3, into data/ej/.

DAC is the State's environmental justice measure (Climate Justice Working
Group, final criteria of March 2023): every census tract gets percentile
ranks on 45 indicators, combined into a score. It is published on data.ny.gov
on 2010-vintage tracts (the Census Bureau's 2019 tract file), so the shapes
come from TIGER/Line 2019.

Writes:
  data/ej/dac-catalog.json        every data.ny.gov dataset matching
                                  "disadvantaged communities": id, name,
                                  description, columns
  data/ej/dac-<id>.csv            each of those datasets' Manhattan rows
                                  (GEOIDs starting 36061), geometry columns
                                  dropped
  data/ej/tracts-2019-cb3.geojson the 2019 tracts that reach CB3

The cloud sessions this dashboard is built in cannot reach data.ny.gov, so
.github/workflows/fetch-dac.yml runs this. Needs pyshp (pip install pyshp).
"""

import csv
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import zipfile

import shapefile  # pyshp

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'ej')
CATALOG_URL = 'https://data.ny.gov/api/catalog/v1?' + urllib.parse.urlencode(
    {'q': 'disadvantaged communities', 'limit': 50})
ROWS_URL = 'https://data.ny.gov/api/views/{id}/rows.csv?accessType=DOWNLOAD'
TIGER_URL = 'https://www2.census.gov/geo/tiger/TIGER2019/TRACT/tl_2019_36_tract.zip'
MANHATTAN = '36061'
# CB3's extent (scripts/fetch_census.py) with ~500 m to spare.
LAT = (40.7028, 40.7405)
LNG = (-74.0103, -73.9646)


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'nyc-tree-dashboard'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def fetch_catalog():
    found = []
    for r in json.loads(get(CATALOG_URL))['results']:
        res = r['resource']
        if res.get('type') != 'dataset' or not re.search(r'disadvantaged communit', res['name'], re.I):
            continue
        found.append({
            'id': res['id'],
            'name': res['name'],
            'description': res.get('description', ''),
            'updatedAt': res.get('updatedAt', ''),
            'columns': [{'field': f, 'name': n} for f, n in
                        zip(res.get('columns_field_name', []), res.get('columns_name', []))],
        })
    return found


def fetch_manhattan_rows(dataset_id):
    rows = list(csv.reader(io.StringIO(get(ROWS_URL.format(id=dataset_id)).decode('utf-8-sig'))))
    header, body = rows[0], rows[1:]
    keep = [r for r in body if any(c.startswith(MANHATTAN) for c in r)]
    geom = {i for i in range(len(header))
            if any(re.match(r'\s*(MULTI)?POLYGON', r[i] if i < len(r) else '') for r in keep)}
    cols = [i for i in range(len(header)) if i not in geom]
    return [[header[i] for i in cols]] + [[r[i] if i < len(r) else '' for i in cols] for r in keep]


def fetch_tracts():
    z = zipfile.ZipFile(io.BytesIO(get(TIGER_URL)))
    part = lambda ext: io.BytesIO(z.read(next(n for n in z.namelist() if n.endswith(ext))))
    sf = shapefile.Reader(shp=part('.shp'), dbf=part('.dbf'), shx=part('.shx'))
    features = []
    for sr in sf.iterShapeRecords():
        rec = sr.record.as_dict()
        if rec['COUNTYFP'] != MANHATTAN[2:]:
            continue
        x0, y0, x1, y1 = sr.shape.bbox
        if x1 < LNG[0] or x0 > LNG[1] or y1 < LAT[0] or y0 > LAT[1]:
            continue
        geo = sr.shape.__geo_interface__
        rnd = lambda c: [round(c[0], 6), round(c[1], 6)]
        if geo['type'] == 'Polygon':
            coords = [[rnd(p) for p in ring] for ring in geo['coordinates']]
        else:
            coords = [[[rnd(p) for p in ring] for ring in poly] for poly in geo['coordinates']]
        features.append({
            'type': 'Feature',
            'properties': {k: rec[k] for k in ('GEOID', 'NAMELSAD', 'ALAND', 'AWATER')},
            'geometry': {'type': geo['type'], 'coordinates': coords},
        })
    features.sort(key=lambda f: f['properties']['GEOID'])
    return {'type': 'FeatureCollection', 'features': features}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    catalog = fetch_catalog()
    with open(os.path.join(OUT_DIR, 'dac-catalog.json'), 'w') as f:
        json.dump(catalog, f, indent=1)
    print(f'{len(catalog)} DAC datasets on data.ny.gov')
    for d in catalog:
        print(f"  {d['id']}  {d['name']}  (updated {d['updatedAt'][:10]})")
        print('    ' + ', '.join(c['field'] for c in d['columns']))
        try:
            rows = fetch_manhattan_rows(d['id'])
        except Exception as e:
            print(f'    could not download: {e}')
            continue
        with open(os.path.join(OUT_DIR, f"dac-{d['id']}.csv"), 'w', newline='') as f:
            csv.writer(f).writerows(rows)
        print(f'    {len(rows) - 1} Manhattan rows')

    tracts = fetch_tracts()
    with open(os.path.join(OUT_DIR, 'tracts-2019-cb3.geojson'), 'w') as f:
        json.dump(tracts, f, separators=(',', ':'))
    print(f"{len(tracts['features'])} 2019 tracts reach CB3")

    if not catalog or not tracts['features']:
        sys.exit('Nothing usable fetched')


if __name__ == '__main__':
    main()
