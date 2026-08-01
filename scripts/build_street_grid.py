#!/usr/bin/env python3
"""
Reconstruct CB3's street grid as a set of named centerlines.

Why this exists
---------------
The first two work-cell attempts (build_work_cells.py, build_rect_cells.py)
both cut CB3 into cells that ignore real block boundaries: the blockface
chainer follows sidewalk rows but splits them at arbitrary tree counts, and
the rotated-rectangle grid slices straight through the middle of blocks. A
crew handed either one gets an assignment that can't be described in street
names and doesn't line up with anything you can walk.

This script rebuilds the underlying thing both attempts were missing: where
the streets actually are. Everything downstream (build_subzones.py) then
snaps to these lines, so every boundary in the work plan runs down a street
centerline by construction.

No street-centerline source is reachable
----------------------------------------
data.cityofnewyork.us, tigerweb.geo.census.gov, www2.census.gov,
services*.arcgis.com and the OSM/Overpass endpoints are all blocked by the
sandbox egress policy (only GitHub and the package registries answer). So the
grid is reconstructed from two sources that ARE in this repo, which happen to
have complementary failure modes:

  ANCHORS   data/trees.csv carries a street address for ~1,100 trees, 45+ of
            CB3's named streets among them. Exact where present, absent for
            whole stretches (Chrystie, Forsyth, Allen, Orchard, Ave B, the
            numbered streets above E 11th, most of Two Bridges' N-S streets).

  ROWS      data/census.json's 5,315 CB3 street trees form dense rows along
            every street whether or not any of them is addressed. Complete
            coverage, but anonymous - a row doesn't know its own name.

Anchors name the lines; rows place them. Where a street has both, the row
pair's midpoint wins: it sits on the roadway, whereas an anchor set can be
10m off-center if its trees all happen to be on one side.

Method
------
  1. CB3 is split into four grid REGIONS. This matters: CB3 is not one grid.
     The East Village is the 1811 Manhattan grid; the LES south of Houston
     runs ~7 degrees off it; and below Division St the Two Bridges E-W
     streets swing another 28 degrees while their N-S cross streets barely
     move. Fitting one global angle - what build_rect_cells.py did - is what
     put cell edges through the middle of blocks down there.
  2. Each region's two street families (E-W and N-S) get a bearing, chosen by
     scanning 0-180 degrees for the angle whose perpendicular projection of
     the region's trees is sharpest (sum of squared histogram bins). Scanned
     rather than assumed, then cross-checked against the pooled least-squares
     bearing of that family's addressed trees.
  3. Trees are labelled with a local row orientation (PCA over neighbours
     within 40m) and each family's rows are detected using only the trees
     whose row runs that way. Filtering by orientation first is what makes
     this work - detecting on all of a region's trees at once lets the N-S
     rows smear the E-W histogram and vice versa, which over-detected badly
     in the LES (10 "E-W corridors" for 6 real streets).
  4. Detected rows are SIDEWALKS, not streets. They come in pairs ~10-16m
     apart separated by 60-230m of block, so rows within ROW_CLUSTER_GAP_M of
     each other are clustered into one street candidate whose centerline is
     their weighted mean. Treating raw rows as streets is what put Delancey and
     Broome 39m apart on the first pass: Delancey is wide enough that its
     two sidewalks read as two separate streets.
  5. Named streets are assigned to candidates by a dynamic program that keeps
     geographic order and weighs two kinds of evidence - agreement with the
     street's own anchors, and regularity of the resulting block spacing.
     The spacing prior is what makes sparse anchors safe. The four trees
     addressed "Delancey St" all sit on the Williamsburg Bridge approach
     plaza, ~75m off the roadway; on anchor evidence alone they pull Delancey
     onto the wrong candidate and leave a 207m block beside a 52m one. Judged
     against a uniformity prior that assignment loses to the correct one.

Output: data/cb3-street-grid.json

Caveat: this is a reconstruction, not survey data. Line positions are good to
roughly a sidewalk width, and the housing superblocks (Tompkins Square, Baruch,
Vladeck, Rutgers, Smith) have no interior streets to detect, so they read as
one oversized block. Re-run against real centerlines if they ever land here.
"""

import csv
import collections
import html
import json
import math
import os
import re
import statistics

ROOT = os.path.join(os.path.dirname(__file__), '..')
CENSUS_PATH = os.path.join(ROOT, 'data', 'census.json')
TREES_PATH = os.path.join(ROOT, 'data', 'trees.csv')
BOUNDARY_PATH = os.path.join(ROOT, 'data', 'cb3-boundary.json')
OUT_PATH = os.path.join(ROOT, 'data', 'cb3-street-grid.json')

# Local flat-earth scale for CB3's latitude. Shared with build_subzones.py and
# with the browser (see cb3GridProject in index.html) so all three agree.
REF_LNG, REF_LAT = -73.9850, 40.7200
M_PER_DEG_LNG = 84400.0
M_PER_DEG_LAT = 110540.0

# Region dividers, each expressed as a street line in the same lat = intercept
# + slope * (lng - REF_LNG) form the zone boundaries already use in index.html.
# Houston and Grand are reused verbatim from fit_zone_boundaries.py so regions
# nest inside the existing 3 zones instead of cross-cutting them.
DIV_HOUSTON = (-0.2683, 40.72176)
DIV_GRAND = (-0.2683, 40.71555)
DIV_EBWAY = (0.1101, 40.71467)

ORIENT_RADIUS_M = 40.0      # neighbourhood used to read a tree's row direction
ORIENT_TOL_DEG = 25.0       # how far off-family a row may sit and still count

# Sidewalk-row detection. Bins are fine and the minimum separation is small
# because the target here is a single row of tree pits, not a whole street.
ROW_BIN_M = 2.0
ROW_SMOOTH = 2
ROW_MIN_COUNT = 5
ROW_MIN_SEP_M = 9.0
# Rows this close together are the two sidewalks of one street. Measured pair
# separation across CB3 runs 10-16m. The binding case at the top of the range
# is E 1st St and E Houston, whose facing sidewalks are only ~24m apart - at
# 25m they merged into a single candidate and E 1st St inherited a centerline
# sitting in the middle of Houston.
ROW_CLUSTER_GAP_M = 20.0

ANCHOR_CAP_M = 60.0         # anchor disagreement beyond this costs no extra
ANCHOR_FULL_TREES = 6       # anchor trees needed before an anchor is fully trusted
W_ANCHOR = 2.0              # weight on agreeing with a street's addressed trees
W_GAP = 3.0                 # weight on regular block spacing
W_SKIP = 2.0                # cost of leaving a named street with no candidate
DIVIDER_TOL_M = 30.0        # slack when testing a candidate against a region divider

# CB3's streets, per region, in geographic order (E-W lists run north to
# south, N-S lists run west to east). Order is the whole point: it is what
# lets an unanchored street inherit a position from the corridor sitting
# between its two placed neighbours. Aliases cover the addresses in
# trees.csv that name the same line two ways.
REGIONS = [
    {
        'id': 'EV',
        'label': 'East Village',
        'zone': 1,
        'ew': [
            ('E 14 ST', []), ('E 13 ST', []), ('E 12 ST', []), ('E 11 ST', []),
            ('E 10 ST', []), ('E 9 ST', []),
            ('E 8 ST / ST MARKS PL', ['E 8 ST', 'ST MARKS PL', 'ST MARKS PLACE']),
            ('E 7 ST', []), ('E 6 ST', []), ('E 5 ST', []), ('E 4 ST', []),
            ('E 3 ST', []), ('E 2 ST', []), ('E 1 ST', []), ('E HOUSTON ST', []),
        ],
        'ns': [
            ('BOWERY / 3 AVE', ['BOWERY', 'BOWERY ST', '3 AVE']),
            ('2 AVE', []), ('1 AVE', []), ('AVE A', []), ('AVE B', []),
            ('AVE C', []), ('AVE D', []), ('FDR DR', ['F D R DRIVE']),
        ],
    },
    {
        'id': 'LES',
        'label': 'Lower East Side',
        'zone': 2,
        'ew': [
            ('E HOUSTON ST', []), ('STANTON ST', []), ('RIVINGTON ST', []),
            ('DELANCEY ST', []), ('BROOME ST', ['BROOME']), ('GRAND ST', []),
        ],
        'ns': [
            ('BOWERY', ['BOWERY ST']), ('CHRYSTIE ST', []), ('FORSYTH ST', []),
            ('ELDRIDGE ST', []), ('ALLEN ST', []), ('ORCHARD ST', []),
            ('LUDLOW ST', []), ('ESSEX ST', []), ('NORFOLK ST', []),
            ('SUFFOLK ST', []), ('CLINTON ST', ['50A CLINTON ST']),
            ('ATTORNEY ST', []), ('RIDGE ST', []), ('PITT ST', ['OPP 115 PITT ST']),
            # Sheriff St is left out on purpose: it was largely demapped for
            # the Baruch Houses, so listing it makes the DP split that
            # superblock's sparse rows into two implausibly narrow blocks.
            ('WILLETT ST / BIALYSTOKER PL', ['BIALYSTOKER PLACE', 'WILLETT ST']),
            ('COLUMBIA ST', []), ('MANGIN ST', []),
            ('FDR DR', ['F D R DRIVE']),
        ],
    },
    {
        'id': 'CH',
        'label': 'Grand to Division',
        'zone': 3,
        # East of Clinton this strip is the Seward Park / Hillman / East River
        # co-op superblocks, so the LES cross streets (Attorney, Ridge, Pitt,
        # Columbia) have no counterpart here and are deliberately absent.
        'ew': [
            ('GRAND ST', []), ('HESTER ST', []), ('CANAL ST', []),
            ('DIVISION ST', []),
        ],
        'ns': [
            ('BOWERY', ['BOWERY ST']), ('CHRYSTIE ST', []), ('FORSYTH ST', []),
            ('ELDRIDGE ST', []), ('ALLEN ST', []), ('ORCHARD ST', []),
            ('LUDLOW ST', []), ('ESSEX ST', []), ('NORFOLK ST', []),
            ('SUFFOLK ST', []), ('CLINTON ST', []), ('MONTGOMERY ST', []),
            ('JACKSON ST', []), ('FDR DR', ['F D R DRIVE']),
        ],
    },
    {
        'id': 'TB',
        'label': 'Two Bridges',
        'zone': 3,
        'ew': [
            ('E BROADWAY', []), ('HENRY ST', []), ('MADISON ST', []),
            ('MONROE ST', []), ('CHERRY ST', []), ('WATER ST', []),
            ('SOUTH ST', []),
        ],
        'ns': [
            ('CATHERINE ST', []), ('MARKET ST', []), ('PIKE ST', []),
            ('RUTGERS ST', []), ('JEFFERSON ST', []), ('CLINTON ST', []),
            ('MONTGOMERY ST', []), ('GOUVERNEUR ST', []),
            ('JACKSON ST', []), ('GRAND ST', []), ('FDR DR', ['F D R DRIVE']),
        ],
    },
]

# Streets that are also zone dividers. Pinning them to the exact lines
# fit_zone_boundaries.py already produced keeps sub-zones nested inside the
# three zones the dashboard shows, instead of drifting a block off them.
PINS = {
    'EV': {'E HOUSTON ST': DIV_HOUSTON},
    'LES': {'E HOUSTON ST': DIV_HOUSTON, 'GRAND ST': DIV_GRAND},
    'CH': {'GRAND ST': DIV_GRAND, 'DIVISION ST': DIV_EBWAY},
    'TB': {'E BROADWAY': DIV_EBWAY},
}


# ---------------------------------------------------------------- geometry --

def to_m(lng, lat):
    return (lng - REF_LNG) * M_PER_DEG_LNG, (lat - REF_LAT) * M_PER_DEG_LAT


def to_lnglat(x, y):
    return x / M_PER_DEG_LNG + REF_LNG, y / M_PER_DEG_LAT + REF_LAT


def normal_of(bearing_deg, family):
    """Unit normal of a street family, oriented so that a line's offset grows
    in the direction the street list is written: north -> south for the E-W
    family, west -> east for the N-S family.

    The sign flip matters. cos() changes sign either side of 90 degrees, so a
    fixed formula points the E-W normal north in Two Bridges (bearing ~6) and
    south in the East Village (bearing ~151) - which silently reverses that
    region's street list and hands East Broadway the southernmost candidate.
    Forcing the component's sign pins the direction regardless of bearing."""
    a = math.radians(bearing_deg)
    if family == 'ew':
        nx, ny = -math.sin(a), math.cos(a)
        return (-nx, -ny) if ny > 0 else (nx, ny)   # offset grows southward
    nx, ny = math.sin(a), -math.cos(a)
    return (-nx, -ny) if nx < 0 else (nx, ny)       # offset grows eastward


def ew_line_from_offset(offset, nx, ny):
    """Convert an E-W family line (normal + offset, in metres) to the
    lat = intercept + slope * (lng - REF_LNG) form used everywhere else."""
    slope = -M_PER_DEG_LNG * nx / (M_PER_DEG_LAT * ny)
    intercept = REF_LAT + offset / (M_PER_DEG_LAT * ny)
    return [slope, intercept]


def ns_line_from_offset(offset, nx, ny):
    """Same for an N-S family line, as lng = intercept + slope * (lat - REF_LAT)."""
    slope = -M_PER_DEG_LAT * ny / (M_PER_DEG_LNG * nx)
    intercept = REF_LNG + offset / (M_PER_DEG_LNG * nx)
    return [slope, intercept]


def divider_offset(divider, nx, ny, mean_lng):
    """Offset of a zone-divider line in a family's frame, evaluated at the
    region's mean longitude so a small angle mismatch between the divider and
    the family bearing doesn't bias the result."""
    slope, inter = divider
    lat = inter + slope * (mean_lng - REF_LNG)
    x, y = to_m(mean_lng, lat)
    return x * nx + y * ny


def point_in_poly(x, y, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi):
            inside = not inside
        j = i
    return inside


def angle_dist(a, b):
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


# -------------------------------------------------------------------- data --

def street_name_of(addr):
    a = re.sub(r'\s+', ' ', html.unescape(addr or '').strip()).upper()
    a = re.sub(r'^[\*\d\-]+\s+', '', a)
    a = re.sub(r'\bSTREET\b', 'ST', a)
    a = re.sub(r'\bEAST\b', 'E', a)
    a = re.sub(r'\bWEST\b', 'W', a)
    a = re.sub(r'\bAVENUE\b', 'AVE', a)
    return a.strip()


def load_census_trees(boundary):
    trees = []
    for t in json.load(open(CENSUS_PATH)):
        if t.get('tree_type') != 'street' or t.get('status') != 'Full':
            continue
        try:
            lat, lng = float(t['latitude']), float(t['longitude'])
        except (TypeError, ValueError):
            continue
        if not point_in_poly(lng, lat, boundary):
            continue
        x, y = to_m(lng, lat)
        trees.append({'tree_id': t['tree_id'], 'lat': lat, 'lng': lng, 'x': x, 'y': y,
                      'species': t.get('spc_common', '')})
    return trees


def load_anchors(boundary):
    """Addressed trees inside CB3, grouped by normalized street name."""
    out = collections.defaultdict(list)
    for row in csv.DictReader(open(TREES_PATH)):
        if not row.get('latitude') or not row.get('longitude'):
            continue
        lat, lng = float(row['latitude']), float(row['longitude'])
        if not point_in_poly(lng, lat, boundary):
            continue
        name = street_name_of(row.get('address'))
        if name:
            x, y = to_m(lng, lat)
            out[name].append({'lat': lat, 'lng': lng, 'x': x, 'y': y})
    return out


def region_of(lng, lat):
    for slope, inter, rid in ((DIV_HOUSTON[0], DIV_HOUSTON[1], 'EV'),
                              (DIV_GRAND[0], DIV_GRAND[1], 'LES'),
                              (DIV_EBWAY[0], DIV_EBWAY[1], 'CH')):
        if lat >= inter + slope * (lng - REF_LNG):
            return rid
    return 'TB'


# --------------------------------------------------------------- detection --

def scan_bearing(trees, seed_deg, span_deg=25.0, step=0.5):
    """Pick the bearing near seed_deg whose perpendicular tree projection has
    the sharpest histogram - i.e. the angle at which rows line up into
    corridors. Scanned rather than assumed because CB3's four regions really
    do sit at four different angles."""
    best, best_score = seed_deg, -1.0
    steps = int(span_deg / step)
    for k in range(-steps, steps + 1):
        b = (seed_deg + k * step) % 180.0
        nx, ny = normal_of(b, 'ew')
        vals = [t['x'] * nx + t['y'] * ny for t in trees]
        lo = min(vals)
        nb = int((max(vals) - lo) / ROW_BIN_M) + 2
        hist = [0] * nb
        for v in vals:
            hist[int((v - lo) / ROW_BIN_M)] += 1
        score = sum(c * c for c in hist) / float(len(vals) ** 2)
        if score > best_score:
            best, best_score = b, score
    return best


def local_row_bearings(trees, radius=ORIENT_RADIUS_M):
    """Direction of the sidewalk row each tree sits in, as the principal axis
    of its neighbours. None where a tree is too isolated to tell."""
    grid = collections.defaultdict(list)
    for i, t in enumerate(trees):
        grid[(int(t['x'] // radius), int(t['y'] // radius))].append(i)
    out = []
    for i, t in enumerate(trees):
        gx, gy = int(t['x'] // radius), int(t['y'] // radius)
        near = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in grid.get((gx + dx, gy + dy), ()):
                    if j != i and math.hypot(trees[j]['x'] - t['x'], trees[j]['y'] - t['y']) <= radius:
                        near.append(j)
        if len(near) < 2:
            out.append(None)
            continue
        pts = near + [i]
        mx = sum(trees[j]['x'] for j in pts) / len(pts)
        my = sum(trees[j]['y'] for j in pts) / len(pts)
        sxx = syy = sxy = 0.0
        for j in pts:
            dx, dy = trees[j]['x'] - mx, trees[j]['y'] - my
            sxx += dx * dx
            syy += dy * dy
            sxy += dx * dy
        out.append(math.degrees(0.5 * math.atan2(2 * sxy, sxx - syy)) % 180.0)
    return out


def detect_rows(offsets):
    """Peaks of a smoothed offset histogram: one peak per row of tree pits,
    i.e. one per sidewalk, two per street."""
    if not offsets:
        return []
    lo = min(offsets) - ROW_BIN_M
    nb = int((max(offsets) - lo) / ROW_BIN_M) + 3
    hist = [0] * nb
    for v in offsets:
        hist[int((v - lo) / ROW_BIN_M)] += 1
    sm = [sum(hist[max(0, i - ROW_SMOOTH):i + ROW_SMOOTH + 1]) for i in range(nb)]
    picked = []
    for i in sorted(range(nb), key=lambda i: -sm[i]):
        if sm[i] < ROW_MIN_COUNT:
            break
        c = lo + (i + 0.5) * ROW_BIN_M
        if all(abs(c - p) >= ROW_MIN_SEP_M for p, _ in picked):
            picked.append((c, sm[i]))
    return sorted(picked)


def cluster_rows(rows):
    """Group sidewalk rows into street candidates. A candidate's centerline is
    the tree-count-weighted mean of its rows, which lands between the two
    sidewalks - where the roadway actually is."""
    out = []
    group = []
    for row in rows:
        if group and row[0] - group[-1][0] > ROW_CLUSTER_GAP_M:
            out.append(group)
            group = []
        group.append(row)
    if group:
        out.append(group)
    cands = []
    for g in out:
        weight = sum(n for _c, n in g)
        center = sum(c * n for c, n in g) / weight
        cands.append({'offset': center, 'weight': weight, 'rows': len(g),
                      'span': g[-1][0] - g[0][0]})
    return cands


# ----------------------------------------------------------------- placing --

def assign_streets(streets, anchors, cands, expected_gap):
    """Assign named streets to street candidates, in order, by dynamic program.

    dp[i][j] = best cost for a solution in which street i takes candidate j.
    Transitions run from an earlier street p < i on an earlier candidate
    q < j, so geographic order can never invert. Streets skipped between p
    and i pay W_SKIP each and get interpolated afterwards.

    Cost has two terms:
      anchor  how far candidate j sits from street i's addressed trees,
              saturating at ANCHOR_CAP_M and scaled by how many anchor trees
              back it up, so one stray address can bend the fit but not break
              it;
      gap     how far the implied block spacing strays from expected_gap,
              which is what rescues streets whose only anchors are bad.
    """
    n, m = len(streets), len(cands)
    if not m:
        return {}, {}

    def anchor_cost(i, j):
        vals = anchors.get(streets[i][0])
        if not vals:
            return 0.0
        med = statistics.median(vals)
        conf = min(len(vals), ANCHOR_FULL_TREES) / float(ANCHOR_FULL_TREES)
        return W_ANCHOR * conf * min(abs(med - cands[j]['offset']), ANCHOR_CAP_M) / ANCHOR_CAP_M

    def gap_cost(q, j, steps):
        want = expected_gap * steps
        return W_GAP * abs((cands[j]['offset'] - cands[q]['offset']) - want) / max(want, 1.0)

    INF = float('inf')
    dp = [[INF] * m for _ in range(n)]
    back = [[None] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            # start the chain at street i: every earlier street is skipped
            dp[i][j] = W_SKIP * i + anchor_cost(i, j)
            for p in range(i):
                for q in range(j):
                    if dp[p][q] == INF:
                        continue
                    c = (dp[p][q] + W_SKIP * (i - p - 1)
                         + gap_cost(q, j, i - p) + anchor_cost(i, j))
                    if c < dp[i][j]:
                        dp[i][j] = c
                        back[i][j] = (p, q)

    best, best_c = None, INF
    for i in range(n):
        for j in range(m):
            c = dp[i][j] + W_SKIP * (n - 1 - i)
            if c < best_c:
                best, best_c = (i, j), c

    placed, source = {}, {}
    node = best
    while node is not None:
        i, j = node
        placed[i] = cands[j]['offset']
        source[i] = 'anchor+row' if anchors.get(streets[i][0]) else 'row'
        node = back[i][j]
    return placed, source


def interpolate_unplaced(streets, placed, source):
    """Fill in streets the DP left unassigned - typically ones whose block has
    no trees at all (a park edge, the inside of a housing superblock) - by
    spacing them evenly between their placed neighbours.

    Interpolation only, never extrapolation. A street outside the range the
    data supports is simply dropped: guessing past the last candidate put the
    Bowery 2.5km west of Chinatown on an earlier pass, since nothing in the
    region's trees contradicted it. Dropping a street just merges two blocks,
    which is a far smaller error than inventing a boundary."""
    lo_known = min(placed, default=None)
    hi_known = max(placed, default=None)
    if lo_known is None:
        return
    for idx in range(len(streets)):
        if idx in placed or not (lo_known < idx < hi_known):
            continue
        lo_i = max(i for i in placed if i < idx)
        hi_i = min(i for i in placed if i > idx)
        frac = (idx - lo_i) / float(hi_i - lo_i)
        placed[idx] = placed[lo_i] + frac * (placed[hi_i] - placed[lo_i])
        source[idx] = 'interpolated'


# -------------------------------------------------------------------- main --

def main():
    boundary = json.load(open(BOUNDARY_PATH))
    trees = load_census_trees(boundary)
    anchors = load_anchors(boundary)
    print('Loaded %d live CB3 street trees and %d addressed anchor trees.'
          % (len(trees), sum(len(v) for v in anchors.values())))

    for t in trees:
        t['region'] = region_of(t['lng'], t['lat'])
    by_region = collections.defaultdict(list)
    for t in trees:
        by_region[t['region']].append(t)

    out = {
        'ref': {'lng': REF_LNG, 'lat': REF_LAT,
                'mPerDegLng': M_PER_DEG_LNG, 'mPerDegLat': M_PER_DEG_LAT},
        'dividers': {'houston': DIV_HOUSTON, 'grand': DIV_GRAND, 'eastBroadway': DIV_EBWAY},
        'regions': [],
    }

    for spec in REGIONS:
        rid = spec['id']
        sub = by_region.get(rid, [])
        print('\n=== %s (%s) - zone %d - %d trees' % (rid, spec['label'], spec['zone'], len(sub)))
        if len(sub) < 50:
            print('  too few trees, skipped')
            continue

        # Seed each region's scan from the divider that bounds it, and keep the
        # window tight. Grand-to-Division is a transitional strip where both
        # grids are present; given a wide window its scan defects to the Two
        # Bridges angle even though Grand, Hester and Canal are LES-aligned.
        seed_div = DIV_EBWAY if rid == 'TB' else DIV_HOUSTON
        seed_ew = math.degrees(math.atan2(seed_div[0] * M_PER_DEG_LAT, M_PER_DEG_LNG)) % 180
        ew_brg = scan_bearing(sub, seed_ew, span_deg=10.0 if rid == 'CH' else 25.0)
        ns_brg = scan_bearing(sub, (ew_brg + 90.0) % 180.0)
        print('  bearings: E-W %.1f deg, N-S %.1f deg (cross angle %.1f)'
              % (ew_brg, ns_brg, angle_dist(ew_brg, ns_brg)))

        rows = local_row_bearings(sub)
        region_out = {'id': rid, 'label': spec['label'], 'zone': spec['zone'],
                      'ewBearing': ew_brg, 'nsBearing': ns_brg, 'ew': [], 'ns': []}

        for family, brg in (('ew', ew_brg), ('ns', ns_brg)):
            nx, ny = normal_of(brg, family)
            oriented = [t for t, rb in zip(sub, rows)
                        if rb is not None and angle_dist(rb, brg) < ORIENT_TOL_DEG]
            detected = detect_rows([t['x'] * nx + t['y'] * ny for t in oriented])
            cands = cluster_rows(detected)

            anc = {}
            for name, aliases in spec[family]:
                vals = []
                for key in [name] + list(aliases):
                    for p in anchors.get(key, []):
                        if region_of(p['lng'], p['lat']) == rid:
                            vals.append(p['x'] * nx + p['y'] * ny)
                if vals:
                    anc[name] = vals

            mean_lng = sum(t['lng'] for t in sub) / len(sub)
            pins = {}
            for name, divider in PINS.get(rid, {}).items():
                if any(name == s for s, _al in spec[family]):
                    pins[name] = divider_offset(divider, nx, ny, mean_lng)
                    # A pin is ground truth, so it enters the DP as a maximally
                    # confident anchor to steer neighbouring assignments, then
                    # gets written back exactly once the DP has run.
                    anc[name] = [pins[name]] * ANCHOR_FULL_TREES

            # Drop candidates that fall outside the region's own dividers. A
            # divider street's sidewalk rows straddle the line, so the far-side
            # row shows up as a candidate the region has no street for - and
            # the DP will happily spend a real name on it. That is how E 1st St
            # ended up centered in the middle of Houston. The tolerance absorbs
            # the divider not being parallel to this family's bearing.
            if pins:
                lo = min(pins.values()) - DIVIDER_TOL_M
                hi = max(pins.values()) + DIVIDER_TOL_M
                if len(pins) == 1:      # one-sided bound: which side is the region on?
                    only = list(pins.values())[0]
                    inside_below = sum(1 for c in cands if c['offset'] < only)
                    inside_above = len(cands) - inside_below
                    lo, hi = ((-1e9, only + DIVIDER_TOL_M) if inside_below > inside_above
                              else (only - DIVIDER_TOL_M, 1e9))
                kept = [c for c in cands if lo <= c['offset'] <= hi]
                if len(kept) != len(cands):
                    print('      (%d candidate(s) outside the region dividers dropped)'
                          % (len(cands) - len(kept)))
                cands = kept

            # Two passes: the first uses a crude pitch estimate purely to get a
            # provisional assignment, the second re-runs against the median
            # block gap that assignment implies. One refinement is enough - the
            # crude estimate is skewed by outlying candidates (a lone row out on
            # a pier or a housing-project path), the refined one is not.
            span = cands[-1]['offset'] - cands[0]['offset'] if len(cands) > 1 else 1.0
            expected = max(span / max(len(spec[family]) - 1, 1), 1.0)
            for _ in range(2):
                placed, source = assign_streets(spec[family], anc, cands, expected)
                gaps = [b - a for a, b in zip(sorted(placed.values()),
                                              sorted(placed.values())[1:])]
                if gaps:
                    expected = max(statistics.median(gaps), 1.0)
            interpolate_unplaced(spec[family], placed, source)
            for idx, (name, _al) in enumerate(spec[family]):
                if name in pins:
                    placed[idx] = pins[name]
                    source[idx] = 'divider'
            for a, b in zip(sorted(placed), sorted(placed)[1:]):
                if placed[a] >= placed[b]:
                    print('      ! order violation: %s vs %s'
                          % (spec[family][a][0], spec[family][b][0]))

            print('  %s: %d oriented trees, %d rows -> %d street candidates, '
                  '%d/%d streets placed (%d anchored), median block %.0fm'
                  % (family.upper(), len(oriented), len(detected), len(cands),
                     len(placed), len(spec[family]), len(anc), expected))

            lines = []
            dropped = []
            for idx, (name, _al) in enumerate(spec[family]):
                if idx not in placed:
                    # Recorded, not forgotten: these are almost always CB3's
                    # own edges (the Bowery, the FDR), and build_subzones.py
                    # uses the names to label the outermost blocks, whose far
                    # side is the district boundary rather than a grid line.
                    dropped.append({'name': name, 'before': idx})
                    print('      - %-28s dropped (outside the range trees support)' % name)
                    continue
                # A divider keeps its own geometry rather than being flattened
                # onto the family bearing. E Houston runs at the LES angle,
                # ~9 degrees off the East Village streets it bounds, so forcing
                # it parallel to E 1st St would swing it a block out of place
                # at the far end of the region.
                if name in pins:
                    geom = list(PINS[rid][name])
                elif family == 'ew':
                    geom = ew_line_from_offset(placed[idx], nx, ny)
                else:
                    geom = ns_line_from_offset(placed[idx], nx, ny)
                lines.append({'name': name, 'offset': placed[idx],
                              'source': source[idx], 'line': geom})
            lines.sort(key=lambda d: d['offset'])
            for a, b in zip(lines, lines[1:]):
                if b['offset'] - a['offset'] < 25.0:
                    print('      ! %s and %s only %.0fm apart'
                          % (a['name'], b['name'], b['offset'] - a['offset']))
            for d in lines:
                tag = {'anchor+row': 'A+R', 'row': 'R ', 'interpolated': 'I ', 'divider': 'D '}[d['source']]
                print('      %s %-28s %8.1f m' % (tag, d['name'], d['offset']))
            region_out[family] = lines
            region_out[family + 'Normal'] = [nx, ny]
            region_out[family + 'Dropped'] = dropped

        out['regions'].append(region_out)

    out['boundary'] = boundary
    with open(OUT_PATH, 'w') as f:
        json.dump(out, f)
    print('\nWrote %s' % OUT_PATH)


if __name__ == '__main__':
    main()
