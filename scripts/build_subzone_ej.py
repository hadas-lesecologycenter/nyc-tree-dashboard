#!/usr/bin/env python3
"""
Give each sub-zone an environmental justice score from New York State's
Disadvantaged Communities (DAC) data, for the sub-zone colours on the map.

The score is the DAC Combined Score's percentile rank among New York City's
census tracts (Percentile_Rank_Combined_NYC, 0 = least burdened in the city,
100 = most), averaged over the tracts a sub-zone covers, each weighted by how
much of the sub-zone's area it covers. dac_share is the part of the sub-zone's
area in tracts the State designates as disadvantaged communities.

The overlap is measured by laying a GRID_M grid of points over each sub-zone
and finding the tract each point inside it falls in - no geometry library, and
at 5 m a sub-zone of 100,000 m2 gets some 4,000 points, so a tract's share is
good to well under a percentage point.

Reads data/subzones.geojson and what scripts/fetch_dac.py fetched into
data/ej/. Writes data/subzone-ej.json. Run after either changes:

    python3 scripts/build_subzone_ej.py
"""

import csv
import json
import math
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SUBZONES = os.path.join(ROOT, 'data', 'subzones.geojson')
TRACTS = os.path.join(ROOT, 'data', 'ej', 'tracts-2019-cb3.geojson')
DAC_ID = '2e6c-s6fp'
DAC = os.path.join(ROOT, 'data', 'ej', f'dac-{DAC_ID}.csv')
CATALOG = os.path.join(ROOT, 'data', 'ej', 'dac-catalog.json')
OUT = os.path.join(ROOT, 'data', 'subzone-ej.json')

GRID_M = 5.0
M_PER_DEG_LAT = 110540.0
M_PER_DEG_LNG = 84400.0   # at CB3's latitude, as guardMetersApart in index.html


def polygons(geom):
    """A GeoJSON geometry as a list of polygons, each [outer, *holes] of (x, y)."""
    if geom['type'] == 'Polygon':
        return [geom['coordinates']]
    return geom['coordinates']


def in_ring(x, y, ring):
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def contains(polys, x, y):
    return any(in_ring(x, y, p[0]) and not any(in_ring(x, y, h) for h in p[1:]) for p in polys)


def bbox(polys):
    pts = [pt for p in polys for pt in p[0]]
    return (min(p[0] for p in pts), min(p[1] for p in pts),
            max(p[0] for p in pts), max(p[1] for p in pts))


def main():
    subzones = json.load(open(SUBZONES))['features']
    tracts = []
    for f in json.load(open(TRACTS))['features']:
        polys = polygons(f['geometry'])
        tracts.append((f['properties'], polys, bbox(polys)))
    dac = {r['GEOID']: r for r in csv.DictReader(open(DAC))}
    meta = next(d for d in json.load(open(CATALOG)) if d['id'] == DAC_ID)

    dx = GRID_M / M_PER_DEG_LNG
    dy = GRID_M / M_PER_DEG_LAT
    out = {}
    for f in subzones:
        sid = f['properties']['subzone_id']
        polys = polygons(f['geometry'])
        x0, y0, x1, y1 = bbox(polys)
        near = [t for t in tracts if t[2][0] <= x1 and t[2][2] >= x0 and t[2][1] <= y1 and t[2][3] >= y0]
        counts, total, missed = {}, 0, 0
        for i in range(math.ceil((y1 - y0) / dy)):
            y = y0 + (i + 0.5) * dy
            for j in range(math.ceil((x1 - x0) / dx)):
                x = x0 + (j + 0.5) * dx
                if not contains(polys, x, y):
                    continue
                total += 1
                hit = next((t[0]['GEOID'] for t in near if contains(t[1], x, y)), None)
                if hit is None:
                    missed += 1
                else:
                    counts[hit] = counts.get(hit, 0) + 1
        scored = {g: n for g, n in counts.items() if dac.get(g, {}).get('Percentile_Rank_Combined_NYC')}
        weight = sum(scored.values())
        if not weight:
            raise SystemExit(f'{sid}: no DAC-scored tract under it')
        name = {t[0]['GEOID']: t[0]['NAMELSAD'] for t in tracts}
        out[sid] = {
            'nyc_percentile': round(100 * sum(
                n * float(dac[g]['Percentile_Rank_Combined_NYC']) for g, n in scored.items()) / weight, 1),
            'dac_share': round(sum(
                n for g, n in scored.items() if dac[g]['DAC_Designation'] == 'Designated as DAC') / weight, 3),
            'tracts': [{
                'geoid': g,
                'name': name[g],
                'share': round(n / total, 3),
                'nyc_percentile': round(100 * float(dac[g]['Percentile_Rank_Combined_NYC']), 1),
                'dac': dac[g]['DAC_Designation'] == 'Designated as DAC',
            } for g, n in sorted(scored.items(), key=lambda kv: -kv[1])],
        }
        if missed or weight < total:
            print(f'  {sid}: {total - weight} of {total} points in no scored tract')

    doc = {
        'source': {
            'dataset': meta['name'],
            'url': f'https://data.ny.gov/d/{DAC_ID}',
            'updated': meta['updatedAt'][:10],
            'field': 'Percentile_Rank_Combined_NYC',
            'tracts': 'US Census Bureau TIGER/Line 2019 census tracts',
            'method': f'area-weighted average over the tracts each sub-zone covers, {GRID_M:g} m point grid',
        },
        'subzones': out,
    }
    with open(OUT, 'w') as fh:
        json.dump(doc, fh, indent=1)
        fh.write('\n')
    for sid, v in sorted(out.items()):
        print(f"{sid}  NYC percentile {v['nyc_percentile']:5.1f}  DAC area {100 * v['dac_share']:5.1f}%  "
              f"{len(v['tracts'])} tracts")


if __name__ == '__main__':
    main()
