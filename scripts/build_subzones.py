#!/usr/bin/env python3
"""
Cut CB3 into sub-zones whose edges lie ON the streets that name them.

What changed and why
--------------------
The previous version of this script ran every sub-zone edge MID-BLOCK, half a
block off the street it was named for. That kept both sides of a street
together but meant no edge on the map lined up with anything you can see out of
a window, and the street centrelines it leaned on were fitted to whole families
of streets at once, so they sat several metres off the real roadway.

Now each edge is a named street, placed by its own two rows of sidewalk trees
and offset to that street's property line:

  * the boundary for a numbered street runs immediately NORTH of it, so the
    street - both sidewalks - belongs to the sub-zone on the south side;
  * the boundary for an avenue runs immediately EAST of it, so the avenue -
    both sidewalks - belongs to the sub-zone on the west side.

A sub-zone therefore owns its northern street and its eastern avenue, and the
rule tiles CB3 without splitting any street down the middle.

How the lines are placed
------------------------
Two anchors are exact, and they are the only geometry in this repo that is:
CB3's official boundary (data/cb3-boundary.json) runs down the middle of E 14th
St across the top of the district and down 4th Ave / Bowery on its west side.
The E 14th St run fixes the bearing of the street grid; both runs are used as
sub-zone edges directly, by leaving those sides of the window open and letting
the CB3 clip close them.

Every other street is fitted from the census. Street trees stand in two rows,
one per sidewalk, and those rows are startlingly straight - a least-squares
line through one comes out with an RMS residual of 0.1-0.5 m. Fitting the two
rows separately and averaging them gives a centreline good to well under a
metre, which is a different thing from the old grid's family fit: that one took
whatever rows it could find, so E 14th St - whose north sidewalk is in CB6 and
absent from the data - landed 9.5 m south of the real street, on top of its own
south sidewalk.

The edge itself is then the centreline offset by half the street's right of
way, which puts it on the property line - "immediately north of E 10th St" in
the literal sense - and nudged further out if a tree stands there, because a
right of way is a constant and a street's planting is not. See EDGE_CLEAR_M.

Twenty-five sub-zones cover all of CB3: 1A-1L the East Village, 2A-2F the Lower
East Side, 3A-3G Grand St south across the Chinatown strip and Two Bridges.
Every CB3 street tree falls in exactly one.

Output:
  data/cb3-street-lines.json — fitted centrelines, for inspection
  data/subzones.geojson      — one Polygon per sub-zone, clipped to CB3
  data/subzones.csv          — treeId,subzoneId,segmentId,zone,lat,lng,species
  data/subzone-segments.geojson — one MultiPoint per block segment: its trees
"""

import collections
import csv
import json
import math
import os

ROOT = os.path.join(os.path.dirname(__file__), '..')
GRID_PATH = os.path.join(ROOT, 'data', 'cb3-street-grid.json')
CENSUS_PATH = os.path.join(ROOT, 'data', 'census.json')
BOUNDARY_PATH = os.path.join(ROOT, 'data', 'cb3-boundary.json')
OUT_LINES = os.path.join(ROOT, 'data', 'cb3-street-lines.json')
OUT_GEOJSON = os.path.join(ROOT, 'data', 'subzones.geojson')
OUT_CSV = os.path.join(ROOT, 'data', 'subzones.csv')
OUT_SEGMENTS = os.path.join(ROOT, 'data', 'subzone-segments.geojson')

REF_LNG, REF_LAT = -73.9850, 40.7200
M_PER_DEG_LNG = 84400.0
M_PER_DEG_LAT = 110540.0

# Index range of the CB3 boundary ring that runs along E 14th St, west to east.
# The ring starts partway along 14th St, so the run wraps past the end.
E14_RUN = [275, 276, 277] + list(range(0, 13))

# How far off its centreline a street's boundary is drawn: far enough to clear
# the whole right of way, so the line lands on the property line and the street
# - roadway, both sidewalks, both rows of trees - sits wholly on one side.
#
# The Commissioners' grid put the numbered side streets at 60 ft and the
# lettered/numbered avenues at 100 ft, and ROW_HALF_M states the ones that are
# certain. Everything else is measured instead: the sidewalk rows are known to
# well under a metre, and a row sits just inside the curb, so half a right of
# way is that row plus a sidewalk. Both routes are checked in validation.
FT = 0.3048
ROW_HALF_M = {
    'E 14 ST': 100 * FT / 2,
    'BOWERY / 3 AVE': 100 * FT / 2,
    '2 AVE': 100 * FT / 2,
    '1 AVE': 100 * FT / 2,
    'E HOUSTON ST': 100 * FT / 2,
}
SIDEWALK_M = 3.5             # curbside tree row to property line
MIN_ROW_HALF_M = 60 * FT / 2  # never draw an edge inside a 60 ft right of way


def row_half(name, fit):
    if name in ROW_HALF_M:
        return ROW_HALF_M[name]
    return max(MIN_ROW_HALF_M, fit['half_row_m'] + SIDEWALK_M)


# Half a right of way is where the boundary WANTS to sit, but it is not always
# where it can. A right of way is a constant and a street's planting is not:
# along E 10th St the north side is an ordinary sidewalk row 5.4 m out as far
# as Ave C, and then the Jacob Riis Houses set their frontage back and plant it
# 8-10 m out, past the property line, on housing-authority ground. A boundary
# held at 9.14 m runs straight down that row and splits it between two
# sub-zones - which is the one thing every rule here exists to avoid.
#
# So each edge is nudged outward until it has clear air: of the offsets between
# half a right of way and EDGE_SEARCH_M beyond it, take the SMALLEST that keeps
# EDGE_CLEAR_M from every tree in the column that edge crosses, and failing
# that the one that keeps the most. Smallest, so the line still hugs its
# street; per column, because the planting changes along the street and a
# single offset cannot suit all of it.
EDGE_CLEAR_M = 1.0       # air a boundary should leave either side of itself
EDGE_SEARCH_M = 6.0      # how far past the right of way it may be nudged


def edge_offset(fit, floor, obstacles):
    """Choose how far off its centreline a boundary sits.

    `obstacles` are distances, in metres, of the trees in this edge's column
    from the centreline, measured on the side the boundary goes. Returns
    (offset, clearance)."""
    near = sorted(d for d in obstacles if 0 < d <= floor + EDGE_SEARCH_M + 4.0)
    top = floor + EDGE_SEARCH_M
    tries = [floor, top] + [(a + b) / 2.0 for a, b in zip(near, near[1:])]
    scored = [(o, min((abs(d - o) for d in near), default=99.0))
              for o in tries if floor <= o <= top]
    clear = [c for c in scored if c[1] >= EDGE_CLEAR_M]
    return min(clear, key=lambda c: c[0]) if clear else max(scored, key=lambda c: c[1])

# How far a fitted centreline may sit from where the old grid put it before the
# fit is treated as having locked onto the wrong pair of rows.
SEED_TOLERANCE_M = 25.0

# --------------------------------------------------------------- sub-zones --
# Each of the four sides names the street whose boundary line closes it, NOT
# the street the sub-zone starts at. Because every line runs immediately north
# of its numbered street and immediately east of its avenue:
#
#   'north'  the street is INSIDE - it sits south of its own line
#   'south'  the street is OUTSIDE - it belongs to the sub-zone below
#   'east'   the avenue is INSIDE - it sits west of its own line
#   'west'   the avenue is OUTSIDE - it belongs to the sub-zone to the left
#
# So a sub-zone described as "Ave A to Ave B" has 'west': '1 AVE' - the line
# east of 1st Ave is where Ave A's block begins. Naming the line rather than
# the content is what makes neighbours abut exactly: 1A's 'east' and 1B's
# 'west' are the same street, so they share one line and cannot gap or overlap.
#
# CB3_EDGE means that side is the district boundary itself - the exact line -
# rather than a fitted street.
CB3_EDGE = 'CB3'

# The half-planes that carve out each grid region, as (divider, keep_south).
# These spell out exactly the test region_of() applies to a tree, so a sub-zone
# covers precisely the trees filed under its region.
#
# Listing every divider rather than just the region's own two matters, because
# the dividers are not parallel and two of them cross inside the district:
# Grand St and East Broadway meet near lng -73.9827, and east of there East
# Broadway runs NORTH of Grand. Bounding Two Bridges by East Broadway alone
# therefore let 3E reach back up over the Lower East Side and claim 18 trees
# that 2F already held.
REGION_BOUNDS = {
    'EV': [('houston', False)],
    'LES': [('houston', True), ('grand', False)],
    'CH': [('houston', True), ('grand', True), ('eastBroadway', False)],
    'TB': [('houston', True), ('grand', True), ('eastBroadway', True)],
}

# DIVIDER + a key from the grid's `dividers` names one of the three lines that
# split CB3 into its care zones: Houston St, Grand St, East Broadway. These are
# the one exception to the offset rule, and they keep their CENTRELINES.
#
# The reason is that the zone split is older and wider than the sub-zones: the
# dashboard reports per-zone totals off it, and pushing Houston St's line north
# to keep the street whole would hand every tree on its north side to zone 2 and
# move those totals. So Houston stays down the middle, zone 1's sub-zones cover
# exactly zone 1, and Houston St is the only street the sub-zones split - which
# is what the previous scheme did too.
DIVIDER = 'DIVIDER:'

# The 14th-to-10th band, west to east. Every one of these stops immediately
# north of E 10th St, so E 10th St itself belongs to the band below.
SUBZONES = [
    {
        'id': '1A', 'zone': 1, 'region': 'EV',
        'north': CB3_EDGE,          # E 14th St, and CB3's own northern edge
        'south': 'E 10 ST',
        'west': CB3_EDGE,           # 4th Ave / Bowery, CB3's own western edge
        'east': '1 AVE',
        'bounds': '4th Ave to 1st Ave, E 14th St to E 10th St',
    },
    {
        'id': '1B', 'zone': 1, 'region': 'EV',
        'north': CB3_EDGE,
        'south': 'E 10 ST',
        'west': '1 AVE',            # shared with 1A's eastern edge
        'east': 'AVE B',
        'bounds': 'Ave A to Ave B, E 14th St to E 10th St',
    },
    {
        'id': '1C', 'zone': 1, 'region': 'EV',
        'north': CB3_EDGE,
        'south': 'E 10 ST',
        'west': 'AVE B',            # shared with 1B's eastern edge
        'east': CB3_EDGE,           # the East River, CB3's own eastern edge
        'bounds': 'Ave C to the East River, E 14th St to E 10th St',
    },

    # The 10th-to-7th band. 'E 10 ST' again, now as the northern edge: it is
    # one line, so this band picks up exactly where the one above stops, and
    # E 10th St itself lands here rather than in 1A-1C. Same three avenue
    # columns, so 1D sits under 1A, 1E under 1B, 1F under 1C.
    {
        'id': '1D', 'zone': 1, 'region': 'EV',
        'north': 'E 10 ST',
        'south': 'E 7 ST',
        'west': CB3_EDGE,           # the Bowery / Cooper Sq below Astor Pl
        'east': '1 AVE',
        'bounds': '4th Ave to 1st Ave, E 10th St to E 7th St',
    },
    {
        'id': '1E', 'zone': 1, 'region': 'EV',
        'north': 'E 10 ST',
        'south': 'E 7 ST',
        'west': '1 AVE',
        'east': 'AVE B',
        'bounds': 'Ave A to Ave B, E 10th St to E 7th St',
    },
    {
        'id': '1F', 'zone': 1, 'region': 'EV',
        'north': 'E 10 ST',
        'south': 'E 7 ST',
        'west': 'AVE B',
        'east': CB3_EDGE,
        'bounds': 'Ave C to the East River, E 10th St to E 7th St',
    },

    # The 7th-to-4th band. 'E 7 ST' over the same three columns as above, so
    # each edge is the identical line the band above closed on - including the
    # nudge it needed - and E 7th St lands here.
    {
        'id': '1G', 'zone': 1, 'region': 'EV',
        'north': 'E 7 ST',
        'south': 'E 4 ST',
        'west': CB3_EDGE,
        'east': '1 AVE',
        'bounds': '4th Ave to 1st Ave, E 7th St to E 4th St',
    },
    {
        'id': '1H', 'zone': 1, 'region': 'EV',
        'north': 'E 7 ST',
        'south': 'E 4 ST',
        'west': '1 AVE',
        'east': 'AVE B',
        'bounds': 'Ave A to Ave B, E 7th St to E 4th St',
    },
    {
        'id': '1I', 'zone': 1, 'region': 'EV',
        'north': 'E 7 ST',
        'south': 'E 4 ST',
        'west': 'AVE B',
        'east': CB3_EDGE,
        'bounds': 'Ave C to the East River, E 7th St to E 4th St',
    },

    # The 4th-to-Houston band, and the bottom of zone 1. Its southern edge is
    # the Houston St divider on its centreline rather than a line north of the
    # street, so these three cover zone 1 exactly and the zone totals hold.
    {
        'id': '1J', 'zone': 1, 'region': 'EV',
        'north': 'E 4 ST',
        'south': DIVIDER + 'houston',
        'west': CB3_EDGE,
        'east': '1 AVE',
        'bounds': '4th Ave to 1st Ave, E 4th St to E Houston St',
    },
    {
        'id': '1K', 'zone': 1, 'region': 'EV',
        'north': 'E 4 ST',
        'south': DIVIDER + 'houston',
        'west': '1 AVE',
        'east': 'AVE B',
        'bounds': 'Ave A to Ave B, E 4th St to E Houston St',
    },
    {
        'id': '1L', 'zone': 1, 'region': 'EV',
        'north': 'E 4 ST',
        'south': DIVIDER + 'houston',
        'west': 'AVE B',
        'east': CB3_EDGE,
        'bounds': 'Ave C to the East River, E 4th St to E Houston St',
    },

    # ---- zone 2, the Lower East Side: Houston St down to Grand St ----------
    # Two bands, split on Delancey St, which is the one street here anybody
    # navigates by and which cuts the zone 800 trees to 463. The north band
    # takes four sub-zones and the south two, so all six land in the 150-260
    # range zone 1 settled at rather than forcing the same three columns onto
    # both. The column lines - Allen, Essex, Clinton - are the wide, named
    # streets a crew would recognise, and Essex is shared by both bands so it
    # runs unbroken through the zone.
    {
        'id': '2A', 'zone': 2, 'region': 'LES',
        'north': DIVIDER + 'houston',
        'south': 'DELANCEY ST',
        'west': CB3_EDGE,           # the Bowery, CB3's own western edge
        'east': 'ELDRIDGE ST',
        'bounds': 'Chrystie St to Eldridge St, E Houston St to Delancey St',
    },
    {
        'id': '2B', 'zone': 2, 'region': 'LES',
        'north': DIVIDER + 'houston',
        'south': 'DELANCEY ST',
        'west': 'ELDRIDGE ST',
        'east': 'ESSEX ST',
        'bounds': 'Allen St to Essex St, E Houston St to Delancey St',
    },
    {
        'id': '2C', 'zone': 2, 'region': 'LES',
        'north': DIVIDER + 'houston',
        'south': 'DELANCEY ST',
        'west': 'ESSEX ST',
        'east': 'CLINTON ST',
        'bounds': 'Norfolk St to Clinton St, E Houston St to Delancey St',
    },
    {
        'id': '2D', 'zone': 2, 'region': 'LES',
        'north': DIVIDER + 'houston',
        'south': 'DELANCEY ST',
        'west': 'CLINTON ST',
        'east': CB3_EDGE,
        'bounds': 'Attorney St to the East River, E Houston St to Delancey St',
    },
    {
        'id': '2E', 'zone': 2, 'region': 'LES',
        'north': 'DELANCEY ST',
        'south': DIVIDER + 'grand',
        'west': CB3_EDGE,
        'east': 'ESSEX ST',
        'bounds': 'Chrystie St to Essex St, Delancey St to Grand St',
    },
    {
        'id': '2F', 'zone': 2, 'region': 'LES',
        'north': 'DELANCEY ST',
        'south': DIVIDER + 'grand',
        'west': 'ESSEX ST',
        'east': CB3_EDGE,
        'bounds': 'Norfolk St to the East River, Delancey St to Grand St',
    },

    # ---- zone 3, Grand St south, across two grids --------------------------
    # Zone 3 is two street patterns, not one. Grand St to Division St is the
    # tail of the Lower East Side grid; south of East Broadway, Two Bridges
    # turns about 35 degrees and runs on its own. They are fitted separately
    # and divided separately, which is why the sub-zones do not line up across
    # East Broadway - the streets do not either.
    #
    # The Chinatown strip holds 441 trees and is thin, so it splits east-west
    # only, on Essex St. Two Bridges holds 1,007 and takes five: three between
    # East Broadway and Monroe St, two below it, with Pike St shared by both
    # bands.
    {
        'id': '3A', 'zone': 3, 'region': 'CH',
        'north': DIVIDER + 'grand',
        'south': DIVIDER + 'eastBroadway',
        'west': CB3_EDGE,           # the Bowery, CB3's own western edge
        'east': 'ESSEX ST',
        'bounds': 'Bowery to Essex St, Grand St to Division St',
    },
    {
        'id': '3B', 'zone': 3, 'region': 'CH',
        'north': DIVIDER + 'grand',
        'south': DIVIDER + 'eastBroadway',
        'west': 'ESSEX ST',
        'east': CB3_EDGE,
        'bounds': 'Norfolk St to the East River, Grand St to Division St',
    },
    {
        'id': '3C', 'zone': 3, 'region': 'TB',
        'north': DIVIDER + 'eastBroadway',
        'south': 'MONROE ST',
        'west': CB3_EDGE,
        'east': 'PIKE ST',
        'bounds': 'Catherine St to Pike St, East Broadway to Monroe St',
    },
    {
        'id': '3D', 'zone': 3, 'region': 'TB',
        'north': DIVIDER + 'eastBroadway',
        'south': 'MONROE ST',
        'west': 'PIKE ST',
        'east': 'MONTGOMERY ST',
        'bounds': 'Rutgers St to Montgomery St, East Broadway to Monroe St',
    },
    {
        'id': '3E', 'zone': 3, 'region': 'TB',
        'north': DIVIDER + 'eastBroadway',
        'south': 'MONROE ST',
        'west': 'MONTGOMERY ST',
        'east': CB3_EDGE,
        'bounds': 'Gouverneur St to the East River, East Broadway to Monroe St',
    },
    {
        'id': '3F', 'zone': 3, 'region': 'TB',
        'north': 'MONROE ST',
        'south': CB3_EDGE,          # the East River waterfront
        'west': CB3_EDGE,
        'east': 'PIKE ST',
        'bounds': 'Catherine St to Pike St, Monroe St to the waterfront',
    },
    {
        'id': '3G', 'zone': 3, 'region': 'TB',
        'north': 'MONROE ST',
        'south': CB3_EDGE,
        'west': 'PIKE ST',
        'east': CB3_EDGE,
        'bounds': 'Rutgers St to the East River, Monroe St to the waterfront',
    },
]


# ---------------------------------------------------------------- geometry --

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


def clip_halfplane(poly, coef):
    """Keep the part of `poly` where a*x + b*y + c <= 0."""
    a, b, c = coef
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp = a * p[0] + b * p[1] + c
        fq = a * q[0] + b * q[1] + c
        if fp <= 0:
            out.append(p)
        if (fp < 0) != (fq < 0) and abs(fq - fp) > 1e-18:
            t = fp / (fp - fq)
            out.append([p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])])
    return out


def clip_to_convex(subject, clip):
    """Sutherland-Hodgman, clipping `subject` against convex `clip`.

    CB3's boundary is concave, so it goes in as the subject; the sub-zone
    window is convex by construction and is the clip."""
    def inside(p, a, b):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0

    def cut(s, e, a, b):
        x1, y1, x2, y2 = s[0], s[1], e[0], e[1]
        x3, y3, x4, y4 = a[0], a[1], b[0], b[1]
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-18:
            return e
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return [x1 + t * (x2 - x1), y1 + t * (y2 - y1)]

    area = sum((clip[i][0] * clip[(i + 1) % len(clip)][1]
                - clip[(i + 1) % len(clip)][0] * clip[i][1]) for i in range(len(clip)))
    window = clip if area > 0 else clip[::-1]

    out = list(subject)
    for i in range(len(window)):
        a, b = window[i], window[(i + 1) % len(window)]
        src, out = out, []
        if not src:
            break
        s = src[-1]
        for e in src:
            if inside(e, a, b):
                if not inside(s, a, b):
                    out.append(cut(s, e, a, b))
                out.append(e)
            elif inside(s, a, b):
                out.append(cut(s, e, a, b))
            s = e
    return out


def poly_area_m2(ring):
    if len(ring) < 3:
        return 0.0
    total = 0.0
    for i in range(len(ring)):
        x1 = (ring[i][0] - REF_LNG) * M_PER_DEG_LNG
        y1 = (ring[i][1] - REF_LAT) * M_PER_DEG_LAT
        x2 = (ring[(i + 1) % len(ring)][0] - REF_LNG) * M_PER_DEG_LNG
        y2 = (ring[(i + 1) % len(ring)][1] - REF_LAT) * M_PER_DEG_LAT
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


# ------------------------------------------------------------------ frame ---

class Frame(object):
    """Local metric frame aligned to the street grid.

    u runs along the streets, positive east-south-east; n runs across them,
    positive SOUTH, and is zero on CB3's own E 14th St line. Both are metres,
    and the mapping to lng/lat is affine, so straight edges stay straight."""

    def __init__(self, boundary):
        pts = [self._xy(boundary[i]) for i in E14_RUN]
        k = len(pts)
        sx = sum(p[0] for p in pts)
        sy = sum(p[1] for p in pts)
        sxx = sum(p[0] ** 2 for p in pts)
        sxy = sum(p[0] * p[1] for p in pts)
        slope = (k * sxy - sx * sy) / (k * sxx - sx * sx)
        inter = (sy - slope * sx) / k
        self.e14_rms = math.sqrt(
            sum((p[1] - (slope * p[0] + inter)) ** 2 for p in pts) / k)
        h = math.hypot(1.0, slope)
        self.ux, self.uy = 1.0 / h, slope / h
        self.nx, self.ny = -self.uy, self.ux
        self.d14 = inter * self.ny
        self.bearing = math.degrees(math.atan(slope))

    @staticmethod
    def _xy(pt):
        return ((pt[0] - REF_LNG) * M_PER_DEG_LNG, (pt[1] - REF_LAT) * M_PER_DEG_LAT)

    def to_un(self, lng, lat):
        x, y = self._xy((lng, lat))
        return (x * self.ux + y * self.uy, self.d14 - (x * self.nx + y * self.ny))

    def to_lnglat(self, u, n):
        d = self.d14 - n
        x = u * self.ux + d * self.nx
        y = u * self.uy + d * self.ny
        return [REF_LNG + x / M_PER_DEG_LNG, REF_LAT + y / M_PER_DEG_LAT]


# ----------------------------------------------------------------- fitting --

def linefit(pairs):
    """Least squares b-on-a over (a, b) pairs: b = m*a + c."""
    k = len(pairs)
    sa = sum(p[0] for p in pairs)
    sb = sum(p[1] for p in pairs)
    saa = sum(p[0] ** 2 for p in pairs)
    sab = sum(p[0] * p[1] for p in pairs)
    den = k * saa - sa * sa
    if abs(den) < 1e-9:
        return 0.0, sb / k
    m = (k * sab - sa * sb) / den
    return m, (sb - m * sa) / k


def robust_line(pairs, iters=3):
    """Least squares with a couple of rounds of outlier trimming."""
    for _ in range(iters):
        m, c = linefit(pairs)
        res = [abs(p[1] - (m * p[0] + c)) for p in pairs]
        med = sorted(res)[len(res) // 2]
        keep = max(1.5, 2.5 * (med or 1.0))
        trimmed = [p for p, r in zip(pairs, res) if r <= keep]
        if len(trimmed) < 6 or len(trimmed) == len(pairs):
            break
        pairs = trimmed
    m, c = linefit(pairs)
    rms = math.sqrt(sum((p[1] - (m * p[0] + c)) ** 2 for p in pairs) / len(pairs))
    return m, c, len(pairs), rms


HALF_WINDOW_M = 30.0     # how far either side of the seed to look for the rows
ROW_KERNEL_M = 2.0       # a sidewalk row is this thick
SEP_MIN_M, SEP_MAX_M = 8.0, 28.0   # plausible distance between the two rows


def find_rows(pts, seed, slope):
    """Locate a street's two sidewalk rows inside a window around `seed`.

    Gap-splitting the sorted offsets is the obvious way to do this and it is
    not reliable: E 10th St has enough stragglers between its two rows to join
    them into one 18 m-wide "row", which then fits as a line down the middle of
    the roadway. Instead both rows are found at once, as the pair of density
    peaks - a plausible roadway apart - that between them cover the most trees.
    That pair is what a street looks like from above, and nothing in between
    can merge them.

    `pts` are (along, across) metre pairs; `slope` is the bearing to de-trend
    by. Returns the two row centres in de-trended terms, or None.

    Both the window and the values are de-trended. Testing the RAW coordinate
    against the seed while reporting the de-trended one is the same thing on a
    grid the frame is aligned to, and 165 m adrift on one that is not - it put
    every Lower East Side avenue two blocks west of itself."""
    sel = [d for d in (p[1] - slope * p[0] for p in pts)
           if abs(d - seed) <= HALF_WINDOW_M]
    if len(sel) < 12:
        return None
    lo, hi = min(sel), max(sel)
    steps = int((hi - lo) / 0.5) + 1
    grid = [lo + i * 0.5 for i in range(steps)]
    dens = [sum(1 for v in sel if abs(v - g) <= ROW_KERNEL_M) for g in grid]
    best = None
    for i, gi in enumerate(grid):
        for j in range(i + 1, len(grid)):
            d = grid[j] - gi
            if d < SEP_MIN_M:
                continue
            if d > SEP_MAX_M:
                break
            score = dens[i] + dens[j]
            if best is None or score > best[0]:
                best = (score, gi, grid[j])
    if best is None:
        return None
    centres = [best[1], best[2]]
    for _ in range(3):                       # settle each peak onto its own mean
        moved = []
        for c in centres:
            near = [v for v in sel if abs(v - c) <= ROW_KERNEL_M]
            moved.append(sum(near) / len(near) if len(near) >= 5 else c)
        if max(abs(a - b) for a, b in zip(centres, moved)) < 0.01:
            centres = moved
            break
        centres = moved
    a, b = sorted(centres)
    if not SEP_MIN_M <= b - a <= SEP_MAX_M:
        return None
    return a, b


def fit_street(pts, seed, slope, free_slope):
    """Fit one street's centreline from its two rows of sidewalk trees.

    `pts` are (along, across) metre pairs; `across` is the coordinate the
    street is located BY (n for a numbered street, u for an avenue) and `along`
    the one it runs in. `slope` is the bearing to de-trend by while hunting for
    the rows; when `free_slope` each row is then re-fitted with a slope of its
    own, which is how the family bearing gets measured in the first place.

    Corner trees are the thing to keep out: a tree on the cross street near the
    junction sits at almost the same `across` as the sidewalk row but is not
    part of it, and a handful of them pull the fit off by a metre or two. They
    are dropped by the caller, which passes only mid-block stretches."""
    found = find_rows(pts, seed, slope)
    if found is None:
        return None
    rows = []
    for centre in found:
        members = [p for p in pts
                   if abs((p[1] - slope * p[0]) - centre) <= ROW_KERNEL_M
                   and abs((p[1] - slope * p[0]) - seed)
                   <= HALF_WINDOW_M + ROW_KERNEL_M]
        if len(members) < 5:
            return None
        if free_slope:
            m, c, kept, rms = robust_line(members)
        else:
            # slope is fixed to the family bearing, so only the offset is fitted
            m = slope
            resid = sorted(p[1] - slope * p[0] for p in members)
            mid = resid[len(resid) // 2]
            keep = [r for r in resid if abs(r - mid) <= 2.0]
            c = sum(keep) / len(keep)
            kept = len(keep)
            rms = math.sqrt(sum((r - c) ** 2 for r in keep) / kept)
        rows.append((m, c, kept, rms))
    rows.sort(key=lambda r: r[1])
    fa, fb = rows
    return {
        'slope': (fa[0] + fb[0]) / 2.0,
        'offset': (fa[1] + fb[1]) / 2.0,
        'half_row_m': (fb[1] - fa[1]) / 2.0,
        'rows': [{'slope': f[0], 'offset': f[1], 'trees': f[2], 'rms_m': round(f[3], 3)}
                 for f in (fa, fb)],
    }


def median(vals):
    s = sorted(vals)
    k = len(s)
    return s[k // 2] if k % 2 else (s[k // 2 - 1] + s[k // 2]) / 2.0


def family_slope(pts, axis):
    """The bearing a region's streets run at, measured off the trees.

    The row finder de-trends by this before looking for rows, and it cannot
    start from zero: the frame is aligned to the East Village grid, so zero is
    right there and nowhere else. The Lower East Side sits 7 degrees off it -
    slope -0.124 - which smears a row across 60 m of the search window and
    leaves the fit with nothing to lock onto. Half of zone 2's trees ended up
    on no street at all.

    Scored by how sharply the cross-coordinate clusters once de-trended: at the
    true bearing every row collapses to a spike, so the sum of squared bin
    counts peaks. Coarse pass then a fine one."""
    def score(slope):
        vals = [(n - slope * u) if axis == 'ew' else (u - slope * n) for u, n in pts]
        hist = collections.Counter(int(v // 1.0) for v in vals)
        return sum(c * c for c in hist.values())

    # The range has to cover every bearing CB3 actually contains. Two Bridges
    # runs at slope 0.70 in this frame - its streets meet the East Village grid
    # at about 35 degrees - and a search that stopped at 0.40 could not see it,
    # so it settled for a spurious alignment scoring less than half as well and
    # left every Two Bridges avenue unfitted.
    coarse = max((score(k / 1000.0), k / 1000.0) for k in range(-850, 851, 2))[1]
    return max((score(coarse + d / 10000.0), coarse + d / 10000.0)
               for d in range(-20, 21))[1]


def line_to_frame(frame, line, axis):
    """A grid line stored as [slope, intercept] in lng/lat, in frame terms.

    Sample two points and refit. The frame mapping is affine, so a line stays a
    line and this is exact, not an approximation."""
    slope, inter = line
    if axis == 'ew':
        pts = [frame.to_un(REF_LNG + d, inter + slope * d) for d in (-0.02, 0.02)]
        (a1, b1), (a2, b2) = pts
    else:
        pts = [frame.to_un(inter + slope * d, REF_LAT + d) for d in (-0.01, 0.01)]
        (b1, a1), (b2, a2) = pts
    s = (b2 - b1) / (a2 - a1)
    return s, b1 - s * a1


def fit_region_lines(frame, trees_un, grid_region, log):
    """Fit every named street and avenue in a grid region.

    Three passes. The first uses the old grid's lines as seeds, masks out
    corner trees with those same rough positions, and lets every row find its
    own bearing. The bearings that come back agree to within 0.03 degrees
    across a whole family - 35 cm over a 700 m street - so the second pass
    fixes each family to its median bearing, which stops a short or sparsely
    planted street (E 1st St, with 8 trees on one side) from fitting a wild
    slope through its own noise. The third pass re-masks the corner trees with
    the fitted positions; it moves the answers by centimetres."""
    ew_names = [s['name'] for s in grid_region['ew'] if s.get('source') != 'divider']
    ns_names = [s['name'] for s in grid_region['ns'] if s.get('source') != 'divider']
    ew_seed = {s['name']: s for s in grid_region['ew']}
    ns_seed = {s['name']: s for s in grid_region['ns']}

    # Seeds in frame coordinates. The grid stores each line as [slope,
    # intercept] in lng/lat, and it has to be converted as a LINE, not by
    # evaluating it at some reference point: an offset is the coordinate where
    # the line crosses the frame's origin axis, and reading it off a point
    # hundreds of metres away shears it by slope times that distance. In the
    # East Village, where the frame is aligned to the grid and the slopes are
    # near zero, that error was under 10 m and the row search absorbed it. On
    # the Lower East Side, at slope 0.128, it was 200 m and every single avenue
    # was rejected for landing too far from its own seed.
    streets = {n: line_to_frame(frame, ew_seed[n]['line'], 'ew')[1] for n in ew_names}
    avenues = {n: line_to_frame(frame, ns_seed[n]['line'], 'ns')[1] for n in ns_names}
    fitted_ew, fitted_ns = {}, {}
    ew_slope = family_slope(trees_un, 'ew')
    ns_slope = family_slope(trees_un, 'ns')
    log.append('  bearings off the tree rows: streets %+.5f, avenues %+.5f'
               % (ew_slope, ns_slope))

    for stage in (1, 2, 3):
        free = (stage == 1)
        mask_n = [fitted_ew[n]['offset'] if n in fitted_ew else streets[n] for n in ew_names]
        mask_u = [fitted_ns[n]['offset'] if n in fitted_ns else avenues[n] for n in ns_names]

        for name in ew_names:
            pts = [(u, n) for u, n in trees_un
                   if not any(abs(u - m) < 26.0 for m in mask_u)]
            got = fit_street(pts, streets[name], ew_slope, free)
            if got:
                got['name'] = name
                got['axis'] = 'ew'
                fitted_ew[name] = got

        for name in ns_names:
            pts = [(n, u) for u, n in trees_un
                   if not any(abs(n - m) < 20.0 for m in mask_n)]
            got = fit_street(pts, avenues[name], ns_slope, free)
            if got:
                got['name'] = name
                got['axis'] = 'ns'
                fitted_ns[name] = got

        if stage == 1:
            if fitted_ew:
                ew_slope = median([f['slope'] for f in fitted_ew.values()])
            if fitted_ns:
                ns_slope = median([f['slope'] for f in fitted_ns.values()])
            log.append('  family bearings: streets %+.5f, avenues %+.5f (rise per metre)'
                       % (ew_slope, ns_slope))
            fitted_ew, fitted_ns = {}, {}

    for name in ew_names:
        if name not in fitted_ew:
            log.append('  no two-row fit for %s (kept out of the boundary set)' % name)
        elif abs(fitted_ew[name]['offset'] - streets[name]) > SEED_TOLERANCE_M:
            log.append('  %s fitted %.1f m from its seed - rejected'
                       % (name, fitted_ew[name]['offset'] - streets[name]))
            del fitted_ew[name]
    for name in ns_names:
        if name not in fitted_ns:
            log.append('  no two-row fit for %s (kept out of the boundary set)' % name)
        elif abs(fitted_ns[name]['offset'] - avenues[name]) > SEED_TOLERANCE_M:
            log.append('  %s fitted %.1f m from its seed - rejected'
                       % (name, fitted_ns[name]['offset'] - avenues[name]))
            del fitted_ns[name]

    fitted = {}
    fitted.update(fitted_ew)
    fitted.update(fitted_ns)

    # A second, looser set covering every named street, fitted where possible
    # and seeded from the old grid where not. Nothing is cut with these - they
    # exist so a tree can be told which street it is on, which only has to be
    # right to within half a block.
    walk = dict(fitted)
    for names, axis, seeds, slope in ((ew_names, 'ew', streets, ew_slope),
                                      (ns_names, 'ns', avenues, ns_slope)):
        for name in names:
            if name not in walk:
                walk[name] = {'name': name, 'axis': axis, 'slope': slope,
                              'offset': seeds[name], 'half_row_m': 0.0,
                              'rows': [], 'seeded': True}

    # The zone dividers belong here too. They are not fitted and never bound a
    # cell, but a sub-zone at the bottom of a zone holds one side of one, and
    # without a line to match against, every tree on it reads as standing on no
    # street at all - which left E Houston St out of the contents of the three
    # sub-zones that work it.
    for entries, axis in ((grid_region['ew'], 'ew'), (grid_region['ns'], 'ns')):
        for s in entries:
            if s.get('source') != 'divider':
                continue
            slope, offset = line_to_frame(frame, s['line'], axis)
            walk[s['name']] = {'name': s['name'], 'axis': axis, 'slope': slope,
                               'offset': offset, 'half_row_m': 0.0, 'rows': [],
                               'seeded': True, 'divider': True}
    return fitted, walk


def nearest_line(walk, u, n):
    """Name of the street a tree stands on, and which family it belongs to.

    None for a tree that is not on any street: a few hundred trees in the
    census stand in courtyards, on housing-estate paths and inside the
    superblocks, and the nearest street can be 30 m away. Left unfiltered they
    put E 10th St in the contents of a sub-zone that stops a block short of
    it."""
    best = None
    for name, g in walk.items():
        d = (abs(n - (g['slope'] * u + g['offset'])) if g['axis'] == 'ew'
             else abs(u - (g['slope'] * n + g['offset'])))
        if d <= row_half(name, g) and (best is None or d < best[0]):
            best = (d, name, g['axis'])
    return (best[1], best[2]) if best else (None, None)


# ---------------------------------------------------------------- segments --
# A sub-zone's size is quoted in block segments: one street, one block long,
# both sides. That is the unit a crew is handed - "E 12th St, 2nd Ave to 1st
# Ave" - so it is worth drawing, not just counting.
#
# A segment is drawn AS ITS TREES, and its geometry is a MultiPoint of them.
# Two shapes were tried before this and both read as a box balanced on the
# street rather than as the work: a thick line along the centreline, then a
# corridor polygon wide enough to enclose both sidewalk rows. Neither is what a
# crew goes out to do. The trees are, and they group themselves - a block's
# trees stand in two rows with nothing in the intersection at either end, so
# the gaps that make the segmentation countable are already in the data.
#
# It also removes a whole class of failure. There is no span to trim, no
# boundary to clip against and no way for a segment to come out undrawable, so
# every counted segment is drawn by construction.


def segment_feature(members, walk, ordered, name, axis, step, spec, seg_id):
    cross_axis = 'ns' if axis == 'ew' else 'ew'
    names = ordered[cross_axis]
    ends = [pretty(names[step - 1]) if step > 0 else 'the district edge',
            pretty(names[step]) if step < len(names) else 'the district edge']
    return {
        'type': 'Feature',
        'properties': {
            'segment_id': seg_id,
            'subzone_id': spec['id'],
            'zone': spec['zone'],
            'street': pretty(name),
            'from': ends[0],
            'to': ends[1],
            'label': '%s, %s to %s' % (pretty(name), ends[0], ends[1]),
            'tree_count': len(members),
        },
        'geometry': {
            'type': 'MultiPoint',
            'coordinates': [[round(t['lng'], 6), round(t['lat'], 6)] for t in members],
        },
    }


# ------------------------------------------------------------------ naming --

ORDINAL = {'1': 'st', '2': 'nd', '3': 'rd'}
KEEP_UPPER = {'FDR', 'CB3'}
SUFFIX = {'ST': 'St', 'AVE': 'Ave', 'PL': 'Pl', 'DR': 'Dr'}


def pretty(name):
    """'E 8 ST / ST MARKS PL' -> 'E 8th St / St Marks Pl'."""
    def word(w):
        if w in KEEP_UPPER:
            return w
        if w.isdigit():
            return w + ('th' if 11 <= int(w) % 100 <= 13 else ORDINAL.get(w[-1], 'th'))
        if w in SUFFIX:
            return SUFFIX[w]
        return w if len(w) == 1 else w.capitalize()
    return ' '.join(word(w) for w in name.split())


def name_span(names):
    if not names:
        return ''
    first, last = pretty(names[0]), pretty(names[-1])
    return first if first == last else '%s to %s' % (first, last)


# -------------------------------------------------------------------- main --

def main():
    boundary = json.load(open(BOUNDARY_PATH))
    grid = json.load(open(GRID_PATH))
    regions = {r['id']: r for r in grid['regions']}
    divs = grid['dividers']

    frame = Frame(boundary)
    print('Grid frame from CB3\'s own E 14th St run: bearing %.4f deg, '
          'straight to %.2f m RMS over %d boundary vertices'
          % (frame.bearing, frame.e14_rms, len(E14_RUN)))

    trees = []
    for t in json.load(open(CENSUS_PATH)):
        if t.get('tree_type') != 'street' or t.get('status') != 'Full':
            continue
        try:
            lat, lng = float(t['latitude']), float(t['longitude'])
        except (TypeError, ValueError):
            continue
        if point_in_poly(lng, lat, boundary):
            u, n = frame.to_un(lng, lat)
            trees.append({'tree_id': t['tree_id'], 'lat': lat, 'lng': lng,
                          'species': t.get('spc_common', ''), 'u': u, 'n': n})
    print('Loaded %d live CB3 street trees.' % len(trees))

    def region_of(lng, lat):
        for key, rid in (('houston', 'EV'), ('grand', 'LES'), ('eastBroadway', 'CH')):
            slope, inter = divs[key]
            if lat >= inter + slope * (lng - REF_LNG):
                return rid
        return 'TB'

    for t in trees:
        t['region'] = region_of(t['lng'], t['lat'])

    # Only regions that a sub-zone actually names need fitting.
    wanted = sorted({z['region'] for z in SUBZONES})
    lines, walk_lines = {}, {}
    for rid in wanted:
        log = []
        sub = [(t['u'], t['n']) for t in trees if t['region'] == rid]
        print('\n=== %s (%s): fitting street centrelines from %d trees'
              % (rid, regions[rid]['label'], len(sub)))
        got, walk = fit_region_lines(frame, sub, regions[rid], log)
        for line in log:
            print(line)
        for name in sorted(walk, key=lambda k: (walk[k]['axis'], walk[k]['offset'])):
            f = walk[name]
            if f.get('seeded'):
                print('  %-20s %s %8.2f            seeded from the old grid, '
                      'not used as a boundary'
                      % (name, 'n=' if f['axis'] == 'ew' else 'u=', f['offset']))
                continue
            print('  %-20s %s %8.2f + %+.5f   half-row %5.2f m   rows %d/%d '
                  'trees, rms %.2f/%.2f m'
                  % (name, 'n=' if f['axis'] == 'ew' else 'u=', f['offset'], f['slope'],
                     f['half_row_m'], f['rows'][0]['trees'], f['rows'][1]['trees'],
                     f['rows'][0]['rms_m'], f['rows'][1]['rms_m']))
        lines[rid] = got
        walk_lines[rid] = walk

    json.dump({'frame': {'refLng': REF_LNG, 'refLat': REF_LAT,
                         'mPerDegLng': M_PER_DEG_LNG, 'mPerDegLat': M_PER_DEG_LAT,
                         'bearingDeg': frame.bearing, 'anchor': 'CB3 boundary, E 14th St'},
               'regions': walk_lines},
              open(OUT_LINES, 'w'), indent=1)
    print('\nwrote %s' % os.path.relpath(OUT_LINES, ROOT))

    # The zone dividers, carried into the frame. They are stored in lng/lat, so
    # sample two points and refit; the mapping is affine, so the line stays a
    # line and this is exact.
    divider_lines = {}
    for key, line in divs.items():
        slope, offset = line_to_frame(frame, line, 'ew')
        divider_lines[key] = {'name': key, 'axis': 'ew', 'slope': slope,
                              'offset': offset, 'half_row_m': 0.0, 'rows': []}

    # ---- build each sub-zone from its four named edges ---------------------
    BIG = 4000.0
    features, csv_rows, edge_records, segments = [], [], [], []
    tree_segment = {}
    print('\n=== sub-zones')
    for spec in SUBZONES:
        rid = spec['region']
        region_lines = lines[rid]
        region_trees = [t for t in trees if t['region'] == rid]
        window = [[-BIG, -BIG], [BIG, -BIG], [BIG, BIG], [-BIG, BIG]]  # (u, n)
        used = {}

        def named_line(name):
            """The line a side names: a fitted street, a zone divider, or None
            for the district boundary."""
            if name == CB3_EDGE:
                return None, 0.0
            if name.startswith(DIVIDER):
                return divider_lines[name[len(DIVIDER):]], 0.0
            f = region_lines.get(name)
            if f is None:
                raise SystemExit('sub-zone %s: no fitted line for %s' % (spec['id'], name))
            return f, row_half(name, f)

        def column(sides):
            """Extent of this sub-zone along the axis an edge runs in.

            An edge's offset is chosen from the trees it actually crosses, so
            it needs to know how far the sub-zone reaches sideways. The two
            perpendicular edges give that - close enough to say which trees are
            in the column, which is all it is for. Two sub-zones bounded by the
            same street over the same column therefore get the same offset,
            which is what keeps 1C and 1F, or 1A and 1D, sharing one line.

            The two axes take opposite signs: an avenue's line is EAST of its
            centreline and a street's is NORTH of it, and north is where n gets
            smaller."""
            sign = -1.0 if sides[0] == 'north' else 1.0
            bounds = []
            for side in sides:
                f, half = named_line(spec[side])
                bounds.append(None if f is None else f['offset'] + sign * half)
            lo = bounds[0] if bounds[0] is not None else -BIG
            hi = bounds[1] if bounds[1] is not None else BIG
            return (lo, hi) if lo <= hi else (hi, lo)

        def edge(side):
            """Half-plane for one named edge, or None for a CB3 edge.

            CB3 edges are left open on purpose: clipping the district boundary
            against the window afterwards reproduces the official line exactly,
            which is more accurate than anything fitted from trees."""
            name = spec[side]
            f, floor = named_line(name)
            if f is None:
                return None
            if name.startswith(DIVIDER):
                # A zone divider is fixed: it sits on its centreline and is not
                # nudged, so report the air it happens to have and move on.
                lo, hi = column(('west', 'east'))
                clear = min((abs(f['offset'] + f['slope'] * t['u'] - t['n'])
                             for t in region_trees if lo <= t['u'] <= hi), default=99.0)
                used[side] = (name[len(DIVIDER):] + ' (zone divider)', f, 0.0, clear, 0.0)
                return f, 0.0
            if f['axis'] == 'ew':
                lo, hi = column(('west', 'east'))
                obst = [f['offset'] + f['slope'] * t['u'] - t['n'] for t in region_trees
                        if lo <= t['u'] <= hi]
            else:
                lo, hi = column(('north', 'south'))
                lo, hi = (lo, hi) if lo <= hi else (hi, lo)
                obst = [t['u'] - (f['offset'] + f['slope'] * t['n']) for t in region_trees
                        if lo <= t['n'] <= hi]
            half, clear = edge_offset(f, floor, obst)
            used[side] = (name, f, half, clear, floor)
            return f, half

        # north / south: n = slope*u + offset, boundary offset NORTH by half a
        # right-of-way, so the street sits south of its own boundary.
        # west / east: u = slope*n + offset, offset EAST, so the avenue sits
        # west of its own boundary.
        south = edge('south')
        if south:
            f, half = south
            # keep n <= slope*u + offset - half   ->   n - slope*u - (offset-half) <= 0
            window = clip_halfplane(window, (-f['slope'], 1.0, -(f['offset'] - half)))
        north = edge('north')
        if north:
            f, half = north
            window = clip_halfplane(window, (f['slope'], -1.0, (f['offset'] - half)))
        east = edge('east')
        if east:
            f, half = east
            # keep u <= slope*n + offset + half
            window = clip_halfplane(window, (1.0, -f['slope'], -(f['offset'] + half)))
        west = edge('west')
        if west:
            f, half = west
            window = clip_halfplane(window, (-1.0, f['slope'], (f['offset'] + half)))

        for div_key, keep_south in REGION_BOUNDS[rid]:
            if len(window) < 3:
                break
            g = divider_lines[div_key]
            window = clip_halfplane(window, (g['slope'], -1.0, g['offset'])
                                    if keep_south
                                    else (-g['slope'], 1.0, -g['offset']))

        if len(window) < 3:
            raise SystemExit('sub-zone %s: empty window' % spec['id'])

        ring = clip_to_convex(boundary, [frame.to_lnglat(u, n) for u, n in window])
        if len(ring) < 3:
            raise SystemExit('sub-zone %s: window misses CB3' % spec['id'])
        ring = ring + [ring[0]]

        inside = [t for t in trees if point_in_poly(t['lng'], t['lat'], ring)]

        # Which streets the sub-zone contains, read off the trees rather than
        # off the polygon. Two streets that bound sub-zones have no fitted
        # centreline of their own - E 14th St, whose north sidewalk is in CB6,
        # and Bowery / 3rd Ave, which is one name over two differently aligned
        # roads - and testing the polygon against fitted lines would drop them
        # from the label of a sub-zone that plainly holds them. Nearest-line
        # assignment only has to beat a 60-70 m block, so the old grid's rough
        # line is a perfectly good stand-in where a fitted one is missing.
        walk = walk_lines[rid]
        ordered = {ax: [n for n, g in sorted(walk.items(), key=lambda kv: kv[1]['offset'])
                        if g['axis'] == ax] for ax in ('ew', 'ns')}
        held_ew, held_ns = set(), set()
        segs = collections.defaultdict(list)
        for t in inside:
            name, axis = nearest_line(walk, t['u'], t['n'])
            if name is None:
                continue
            (held_ew if axis == 'ew' else held_ns).add(name)
            cross = 'ns' if axis == 'ew' else 'ew'
            # How far along its street the tree is, counted in cross streets
            # passed. Lines within a family are near-parallel, so counting them
            # and ordering them by offset agree, and the two lines bracketing
            # the tree are ordered[cross][step-1] and ordered[cross][step].
            step = sum(1 for g in walk.values() if g['axis'] == cross
                       and (t['u'] >= g['slope'] * t['n'] + g['offset'] if cross == 'ns'
                            else t['n'] >= g['slope'] * t['u'] + g['offset']))
            segs[(name, axis, step)].append(t)

        # A stable identifier per segment: streets first, north to south, then
        # avenues west to east, numbered within the sub-zone. Ordering is by
        # RANK - which street comes before which - not by any fitted value, so
        # re-running the fit cannot renumber a crew's assignment under them.
        def seg_order(key):
            name, axis, step = key
            return (0 if axis == 'ew' else 1, walk[name]['offset'], step)

        for i, key in enumerate(sorted(segs, key=seg_order), start=1):
            name, axis, step = key
            members = segs[key]
            seg_id = '%s-%02d' % (spec['id'], i)
            for t in members:
                tree_segment[t['tree_id']] = seg_id
            segments.append(segment_feature(members, walk, ordered, name, axis,
                                            step, spec, seg_id))

        def in_order(names, axis):
            return [n for n, g in sorted(walk.items(), key=lambda kv: kv[1]['offset'])
                    if g['axis'] == axis and n in names]

        streets_txt = name_span(in_order(held_ew, 'ew'))
        avenues_txt = name_span(in_order(held_ns, 'ns'))
        props = {
            'subzone_id': spec['id'],
            'zone': spec['zone'],
            'region': rid,
            'region_label': regions[rid]['label'],
            'label': spec['bounds'],
            'bounds': spec['bounds'],
            'streets': streets_txt,
            'avenues': avenues_txt,
            'contains': ', '.join(x for x in (streets_txt, avenues_txt) if x),
            'blocks': len(segs),
            'tree_count': len(inside),
            'area_m2': round(poly_area_m2(ring[:-1])),
        }
        features.append({'type': 'Feature', 'properties': props,
                         'geometry': {'type': 'Polygon', 'coordinates': [ring]}})
        for t in inside:
            csv_rows.append((t['tree_id'], spec['id'], tree_segment.get(t['tree_id'], ''),
                             spec['zone'], t['lat'], t['lng'], t['species']))

        print('  %-4s %2d blocks %4d trees   bounds: %s' % (spec['id'], len(segs),
                                                            len(inside), spec['bounds']))
        print('       contains: %s' % props['contains'])
        for side in ('north', 'south', 'west', 'east'):
            if side in used:
                name, f, half, clear, floor = used[side]
                edge_records.append((spec['id'], side, name, half, clear, floor))
                note = '' if half <= floor + 0.01 else ' (nudged out from %.2f)' % floor
                if clear < EDGE_CLEAR_M:
                    note += '  <- no clear band; nearest tree %.2f m' % clear
                print('       %-5s edge %-14s offset %5.2f m, %.2f m clear%s'
                      % (side, pretty(name), half, clear, note))
            else:
                print('       %-5s edge %s' % (side, 'CB3 district boundary'))

    # ---- validation --------------------------------------------------------
    print('\n=== validation')
    problems = 0
    rings = {f['properties']['subzone_id']: f['geometry']['coordinates'][0]
             for f in features}
    multi = 0
    for t in trees:
        hits = [s for s, r in rings.items() if point_in_poly(t['lng'], t['lat'], r)]
        if len(hits) > 1:
            multi += 1
    print('trees inside more than one sub-zone: %d' % multi)
    problems += multi

    # Every edge should have air either side of it. Ones that do not are listed
    # rather than counted as faults: a zone divider is pinned to its centreline
    # and cannot be nudged off whatever stands there, and inside a housing
    # superblock there is sometimes no line that clears anything.
    tight = sorted((rec for rec in edge_records if rec[4] < EDGE_CLEAR_M),
                   key=lambda r: r[4])
    if tight:
        print('edges with less than %.1f m of air:' % EDGE_CLEAR_M)
        for sid, side, name, half, clear, floor in tight:
            print('  %-4s %-5s %-22s %.2f m from the nearest tree'
                  % (sid, side, pretty(name), clear))
    else:
        print('every edge has at least %.1f m of air' % EDGE_CLEAR_M)
    nudged = [r for r in edge_records if r[3] > r[5] + 0.01]
    if nudged:
        print('edges nudged out past the property line to find air:')
        for sid, side, name, half, clear, floor in nudged:
            print('  %-4s %-5s %-22s %.2f m (from %.2f), %.2f m clear'
                  % (sid, side, pretty(name), half, floor, clear))
    print('%s' % ('no overlaps' if problems == 0 else '%d problem(s)' % problems))

    with open(OUT_GEOJSON, 'w') as fh:
        json.dump({'type': 'FeatureCollection', 'features': features}, fh)
    with open(OUT_SEGMENTS, 'w') as fh:
        json.dump({'type': 'FeatureCollection', 'features': segments}, fh)
    with open(OUT_CSV, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['treeId', 'subzoneId', 'segmentId', 'zone',
                    'latitude', 'longitude', 'species'])
        w.writerows(csv_rows)
    print('\nwrote %s (%d sub-zones), %s (%d trees) and %s (%d segments)'
          % (os.path.relpath(OUT_GEOJSON, ROOT), len(features),
             os.path.relpath(OUT_CSV, ROOT), len(csv_rows),
             os.path.relpath(OUT_SEGMENTS, ROOT), len(segments)))


if __name__ == '__main__':
    main()
