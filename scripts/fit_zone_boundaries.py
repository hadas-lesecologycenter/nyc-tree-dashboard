#!/usr/bin/env python3
"""
SUPERSEDED by scripts/build_subzones.py, which prints the zone lines index.html
uses under "=== zone lines". Kept for the record; do not re-run it to regenerate
CB3_ZONES.

Two things changed. The lines no longer run down the middle of Houston St and
Grand St - they run immediately north of each, the same rule every sub-zone
boundary follows, so neither street is split between two zones. And they are
fitted from all 5,308 CB3 street trees rather than from the ~12 that carry an
address on those two streets, which also ended the 54-tree disagreement between
the zone a tree was drawn in and the zone it was counted in.

The original note follows.

Fit the CB3 zone boundaries (Houston St and Grand St) to the real street grid.

Why this exists
---------------
CB3's east-west streets do not run along lines of latitude. East Houston St
alone drops roughly 900m of latitude between the Bowery and the East River, so
a single "everything above latitude X is Zone 1" cutoff is correct at one
longitude and hundreds of metres wrong at the other end of the district. That
is what produced the original bug report: the Zone 2/3 line was sitting on
Delancey St rather than Grand St over much of CB3.

Approach
--------
No street-centerline data is available in this repo and data.cityofnewyork.us
is blocked by the sandbox egress policy (same constraint noted in
build_work_cells.py), so the grid is recovered from the street trees that DO
carry a street address in data/trees.csv:

  1. Group addressed trees by street name.
  2. Pooled least-squares fit over the LES grid's east-west streets (Houston,
     Stanton, Rivington, Delancey, Broome, Grand, Hester): one SHARED slope,
     one intercept per street. Sharing a slope is deliberate - it guarantees
     the zone boundaries are parallel and can never cross inside CB3.
  3. Take each boundary street's intercept as the median of its trees'
     intercepts. The median matters for Grand St: the three trees addressed
     "411 Grand" are stacked in longitude and spread 18m in latitude, i.e. a
     north-south row along a walkway rather than the Grand St corridor. The
     mean is dragged ~40m south by them; the median ignores them.

Validation (printed below)
--------------------------
  * All seven LES grid streets must order strictly north -> south under the
    fitted slope. This is the main check that the bearing is right.
  * Streets with a known zone (Stanton/Rivington/Delancey/Broome -> Zone 2,
    Hester -> Zone 3, East Village numbered streets -> Zone 1) must classify
    into that zone.

Only Houston and Grand are needed as internal dividers: Zone 1's northern edge
(14th St) is the CB3 boundary itself, which cb3Contains() already enforces.

Re-run against real street centerline data if it ever lands in this repo.
"""

import csv
import html
import json
import os
import re
import statistics

ROOT = os.path.join(os.path.dirname(__file__), '..')
TREES_PATH = os.path.join(ROOT, 'data', 'trees.csv')
BOUNDARY_PATH = os.path.join(ROOT, 'data', 'cb3-boundary.json')

REF_LNG = -73.9850  # reference meridian the reported latitudes are quoted at

# East-west streets of the LES grid, ordered north -> south.
LES_GRID = ['E HOUSTON ST', 'STANTON ST', 'RIVINGTON ST', 'DELANCEY ST',
            'BROOME ST', 'GRAND ST', 'HESTER ST']

# Streets whose zone is known a priori, used as an independent check.
EXPECTED_ZONE = {
    'STANTON ST': 2, 'RIVINGTON ST': 2, 'DELANCEY ST': 2, 'BROOME ST': 2,
    'HESTER ST': 3,
    'E 2 ST': 1, 'E 3 ST': 1, 'E 4 ST': 1, 'E 5 ST': 1,
    'E 7 ST': 1, 'E 8 ST': 1, 'E 10 ST': 1, 'E 11 ST': 1,
}


def normalize(addr):
    return re.sub(r'\s+', ' ', html.unescape(addr or '').strip()).upper()


def street_of(addr):
    a = normalize(addr)
    a = re.sub(r'^[\*\d\-]+\s+', '', a)          # strip the house number
    a = re.sub(r'\bSTREET\b', 'ST', a)
    a = re.sub(r'\bEAST\b', 'E', a)
    a = re.sub(r'\bWEST\b', 'W', a)
    return a.strip()


def point_in_poly(lng, lat, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i][0], poly[i][1]
        xj, yj = poly[j][0], poly[j][1]
        if (yi > lat) != (yj > lat) and lng < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def load_streets():
    boundary = json.load(open(BOUNDARY_PATH))
    groups = {}
    for row in csv.DictReader(open(TREES_PATH)):
        if not row.get('latitude') or not row.get('longitude'):
            continue
        lat, lng = float(row['latitude']), float(row['longitude'])
        name = street_of(row.get('address'))
        if not name:
            continue
        groups.setdefault(name, []).append((lng, lat, point_in_poly(lng, lat, boundary)))
    return groups


def pooled_slope(groups):
    """One shared slope across the LES grid streets, each free to have its own
    intercept (within-group centering)."""
    num = den = 0.0
    for name in LES_GRID:
        pts = groups.get(name)
        if not pts:
            continue
        mx = sum(p[0] for p in pts) / len(pts)
        my = sum(p[1] for p in pts) / len(pts)
        num += sum((p[0] - mx) * (p[1] - my) for p in pts)
        den += sum((p[0] - mx) ** 2 for p in pts)
    return num / den


def intercepts(groups, slope):
    """Median latitude-at-REF_LNG for each street."""
    out = {}
    for name, pts in groups.items():
        vals = [lat - slope * (lng - REF_LNG) for lng, lat, _ in pts]
        out[name] = statistics.median(vals)
    return out


def main():
    groups = load_streets()
    slope = pooled_slope(groups)
    lat_at_ref = intercepts(groups, slope)

    houston = lat_at_ref['E HOUSTON ST']
    grand = lat_at_ref['GRAND ST']

    def zone_of(lat, lng):
        for zid, edge in ((1, houston), (2, grand)):
            if lat >= edge + slope * (lng - REF_LNG):
                return zid
        return 3

    print('CB3_GRID_SLOPE   = %.4f' % slope)
    print('CB3_GRID_REF_LNG = %.4f' % REF_LNG)
    print('Zone 1/2 divider (E Houston St), lat @ ref = %.5f' % houston)
    print('Zone 2/3 divider (Grand St),     lat @ ref = %.5f' % grand)

    print('\nLES grid ordering (must be strictly north -> south)')
    prev = None
    ordered = True
    for name in LES_GRID:
        if name not in lat_at_ref:
            continue
        v = lat_at_ref[name]
        if prev is not None and v >= prev:
            ordered = False
        gap = '%6.0fm' % ((prev - v) * 111000) if prev is not None else '      -'
        print('  %-14s lat@ref=%.5f  gap=%s  n=%d' % (name, v, gap, len(groups[name])))
        prev = v
    print('  => %s' % ('ORDERED CORRECTLY' if ordered else 'ORDER VIOLATION'))

    print('\nKnown-zone check (CB3 trees only)')
    failures = 0
    for name, expected in sorted(EXPECTED_ZONE.items()):
        pts = [p for p in groups.get(name, []) if p[2]]
        if not pts:
            print('  %-14s  no CB3 trees, skipped' % name)
            continue
        got = {zone_of(lat, lng) for lng, lat, _ in pts}
        ok = got == {expected}
        failures += 0 if ok else 1
        print('  %-14s expected Zone %d, got %-9s %s'
              % (name, expected, sorted(got), 'OK' if ok else 'MISMATCH'))
    print('  => %s' % ('ALL CORRECT' if failures == 0 else '%d MISMATCH(ES)' % failures))


if __name__ == '__main__':
    main()
