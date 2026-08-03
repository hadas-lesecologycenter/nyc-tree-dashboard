#!/usr/bin/env python3
"""
Cut CB3's three care zones into sub-zones of roughly ten city blocks.

Every boundary here is a street. That is the whole point, and it is what the
two earlier attempts got wrong: build_work_cells.py cut sidewalk rows at
arbitrary tree counts, and build_rect_cells.py laid a rotated rectangular grid
over the district that sliced through the middle of blocks. Neither produced
an assignment a crew could be told in words or walk without a map.

Boundaries run MID-BLOCK, so both sides of a street stay together
-----------------------------------------------------------------
A sub-zone is a set of whole streets, not an area fenced off by them. Each
CELL is centred on one street and reaches half a block to either side, so a
crew handed "E 4th St to E 3rd St, Bowery to Ave A" works both sidewalks of
both streets across that whole run.

Something has to give: a boundary cannot enclose a region without crossing the
street network somewhere. Cutting along street centrelines separates a street
from its own far sidewalk; cutting mid-block divides the perpendicular streets
part-way along a block. Mid-block turns out to be the cheaper of the two here -
88 of CB3's 509 block segments end up divided, against 106 when the same
sub-zones were bounded by centrelines - because the streets that get divided
are the avenues, and an avenue was already being split lengthwise for its
entire run under the old scheme.

How it works
------------
  1. data/cb3-street-grid.json (from build_street_grid.py) supplies named
     street centerlines per grid region. cell_bands() turns each family of
     streets into cells split by mid-block lines, one street per cell. Cells
     with no trees - parks, water, the inside of a superblock - are dropped.
  2. Cells are grouped into sub-zones by taking a band of consecutive street
     rows and cutting it into runs of consecutive avenue columns, so a
     sub-zone is always a rectangle in grid terms and names the streets it
     contains rather than the ones that fence it in.
  3. Sub-zones nest inside the existing three zones. The zone dividers -
     Houston, Grand, East Broadway - keep their centrelines and bound cells
     rather than sitting inside one, so no tree changes zone and no zone
     total moves. They are the only streets still split down the middle.

Sizing: TARGET_BLOCKS is the knob. At 10 blocks CB3 comes out as 28 sub-zones
of 6-12 block segments (mean 8.6) holding 64-269 trees (mean 190) - a season's
assignment for a crew, not a day's. Lower it for smaller units; none of the
geometry changes.

Output:
  data/subzones.geojson — one Polygon per sub-zone, clipped to CB3
  data/subzones.csv     — treeId,subzoneId,zone,latitude,longitude,species
"""

import collections
import csv
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), '..')
GRID_PATH = os.path.join(ROOT, 'data', 'cb3-street-grid.json')
CENSUS_PATH = os.path.join(ROOT, 'data', 'census.json')
BOUNDARY_PATH = os.path.join(ROOT, 'data', 'cb3-boundary.json')
OUT_GEOJSON = os.path.join(ROOT, 'data', 'subzones.geojson')
OUT_CSV = os.path.join(ROOT, 'data', 'subzones.csv')

TARGET_BLOCKS = 10          # blocks per sub-zone
ROWS_PER_BAND = 2           # street rows a sub-zone spans before it splits sideways

# Half-planes that carve out each grid region, as (divider, keep_south). These
# spell out exactly the same test region_of() applies to a tree, one clause per
# divider, so a sub-zone's polygon covers precisely the trees filed under it.
#
# Listing every divider rather than just the region's own two matters, because
# the dividers are not parallel and two of them cross inside the district:
# Grand St and East Broadway meet near lng -73.9827, and east of there East
# Broadway runs north of Grand. Bounding Two Bridges by East Broadway alone
# therefore let it reach back up over the Lower East Side. Clipping the East
# Village to Houston alone had the mirror problem - its grid sits ~9 degrees
# off Houston's bearing, so the E 2nd St line dives south of Houston at the
# eastern edge and dragged the sub-zone above it along.
REGION_BOUNDS = {
    'EV': [('houston', False)],
    'LES': [('houston', True), ('grand', False)],
    'CH': [('houston', True), ('grand', True), ('eastBroadway', False)],
    'TB': [('houston', True), ('grand', True), ('eastBroadway', True)],
}

REF_LNG, REF_LAT = -73.9850, 40.7200
M_PER_DEG_LNG = 84400.0
M_PER_DEG_LAT = 110540.0


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


def ew_lat(line, lng):
    """E-W street line stored as [slope, intercept]: lat at a given lng."""
    return line[1] + line[0] * (lng - REF_LNG)


def ns_lng(line, lat):
    """N-S street line stored as [slope, intercept]: lng at a given lat."""
    return line[1] + line[0] * (lat - REF_LAT)


def clip_halfplane(poly, coef):
    """Keep the part of `poly` where a*lng + b*lat + c <= 0.

    Sub-zones are built by intersecting half-planes rather than by joining
    four corner points, because neighbouring grid lines are NOT parallel and
    a corner-based quad can fold into a bow-tie. E 2nd St and E Houston really
    do converge - which is why E 1st St stops at Ave A - and their crossing
    inside CB3 turned that band's polygon inside out, so the clipper returned
    nothing and the whole band was silently dropped. Half-plane intersection
    stays convex by construction and degrades to a wedge exactly where the
    streets really do meet."""
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


def ew_halfplane(line, keep_south):
    """Half-plane bounded by an E-W street: lat = intercept + slope*(lng-REF)."""
    slope, inter = line
    # lat - slope*lng - (inter - slope*REF_LNG) <= 0  is "south of"
    a, b, c = -slope, 1.0, -(inter - slope * REF_LNG)
    return (a, b, c) if keep_south else (-a, -b, -c)


def ns_halfplane(line, keep_west):
    """Half-plane bounded by an N-S street: lng = intercept + slope*(lat-REF)."""
    slope, inter = line
    a, b, c = 1.0, -slope, -(inter - slope * REF_LAT)
    return (a, b, c) if keep_west else (-a, -b, -c)


def clip_to_convex(subject, clip):
    """Sutherland-Hodgman, clipping `subject` against convex `clip`.

    Direction matters: the algorithm only requires the CLIP polygon to be
    convex, so CB3's concave boundary goes in as the subject and the sub-zone
    window - convex by construction, being an intersection of half-planes - is
    the clip. Doing it the other way round would mangle the river edge."""
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

    # orient the clip window counter-clockwise so `inside` has a consistent sense
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


# -------------------------------------------------------------------- data --

def load_trees(boundary):
    trees = []
    for t in json.load(open(CENSUS_PATH)):
        if t.get('tree_type') != 'street' or t.get('status') != 'Full':
            continue
        try:
            lat, lng = float(t['latitude']), float(t['longitude'])
        except (TypeError, ValueError):
            continue
        if point_in_poly(lng, lat, boundary):
            trees.append({'tree_id': t['tree_id'], 'lat': lat, 'lng': lng,
                          'species': t.get('spc_common', '')})
    return trees


def midline(line_a, line_b):
    """The line running down the middle of the block between two streets.

    Averaging slope and intercept rather than bisecting properly is fine here:
    neighbouring streets within a region sit within a degree or two of each
    other, so the two constructions differ by centimetres over a block."""
    return [(line_a[0] + line_b[0]) / 2.0, (line_a[1] + line_b[1]) / 2.0]


def cell_bands(region, family):
    """Split a family's streets into cells with one street at the centre of
    each, so that both sides of every street land in the same cell.

    Returns (cuts, centres). Cell k holds the street centres[k] and runs from
    cuts[k] to cuts[k+1]; a cut of None means that side is open and gets closed
    later by the CB3 boundary. Interior cuts are mid-block lines - that is the
    whole point of this function.

    Zone dividers are the exception and stay on their own centreline. Houston,
    Grand and East Broadway carry the three-zone split the dashboard already
    draws, so moving them half a block would shift trees between zones and
    change every zone total. They bound cells instead of sitting inside one,
    which leaves them as the only streets whose two sides are still separated."""
    lines = region[family]
    centres = [l for l in lines if l.get('source') != 'divider']
    if not centres:
        return [], []
    cuts = [None] * (len(centres) + 1)
    for k in range(len(centres) - 1):
        cuts[k + 1] = midline(centres[k]['line'], centres[k + 1]['line'])
    if lines[0].get('source') == 'divider':
        cuts[0] = lines[0]['line']
    if lines[-1].get('source') == 'divider':
        cuts[-1] = lines[-1]['line']
    return cuts, centres


# -------------------------------------------------------------------- main --

def zone_letter(n):
    return chr(ord('A') + n) if n < 26 else chr(ord('A') + n // 26 - 1) + chr(ord('A') + n % 26)


ORDINAL = {'1': 'st', '2': 'nd', '3': 'rd'}
KEEP_UPPER = {'FDR', 'CB3'}
SUFFIX = {'ST': 'St', 'AVE': 'Ave', 'PL': 'Pl', 'DR': 'Dr'}


def pretty(name):
    """Turn a grid street name into something that reads like an address:
    'E 8 ST / ST MARKS PL' -> 'E 8th St / St Marks Pl'."""
    def word(w):
        if w in KEEP_UPPER:
            return w
        if w.isdigit():
            return w + ('th' if 11 <= int(w) % 100 <= 13
                        else ORDINAL.get(w[-1], 'th'))
        if w in SUFFIX:
            return SUFFIX[w]
        return w if len(w) == 1 else w.capitalize()

    return ' '.join(word(w) for w in name.split())


def name_span(names):
    """'E 14 ST', ..., 'E 13 ST' -> 'E 14th St to E 13th St'."""
    first, last = pretty(names[0]), pretty(names[-1])
    return first if first == last else '%s to %s' % (first, last)


def main():
    boundary = json.load(open(BOUNDARY_PATH))
    grid = json.load(open(GRID_PATH))
    trees = load_trees(boundary)
    print('Loaded %d live CB3 street trees.' % len(trees))

    # Region membership must match build_street_grid.py exactly, or a tree can
    # land in a block belonging to a grid it was never fitted against.
    divs = grid['dividers']

    def region_of(lng, lat):
        for key, rid in (('houston', 'EV'), ('grand', 'LES'), ('eastBroadway', 'CH')):
            slope, inter = divs[key]
            if lat >= inter + slope * (lng - REF_LNG):
                return rid
        return 'TB'

    regions = {r['id']: r for r in grid['regions']}
    for t in trees:
        t['region'] = region_of(t['lng'], t['lat'])

    pad = 0.01
    lngs = [p[0] for p in boundary]
    lats = [p[1] for p in boundary]
    bbox = [[min(lngs) - pad, min(lats) - pad], [max(lngs) + pad, min(lats) - pad],
            [max(lngs) + pad, max(lats) + pad], [min(lngs) - pad, max(lats) + pad]]

    features = []
    csv_rows = []
    summary = []
    per_zone_count = collections.Counter()

    for rid in ('EV', 'LES', 'CH', 'TB'):
        region = regions.get(rid)
        if not region:
            continue
        sub = [t for t in trees if t['region'] == rid]
        ew_cuts, ew_streets = cell_bands(region, 'ew')
        ns_cuts, ns_streets = cell_bands(region, 'ns')
        if not ew_streets or not ns_streets:
            continue

        # Bucket every tree into a cell. A cell is centred on one street and
        # reaches half a block either side, so a tree's row is how many
        # mid-block lines lie north of it. Only interior cuts count here: the
        # outer two are the region's own dividers, which no tree crosses.
        cells = collections.defaultdict(list)
        for t in sub:
            row = sum(1 for c in ew_cuts[1:-1] if t['lat'] <= ew_lat(c, t['lng']))
            col = sum(1 for c in ns_cuts[1:-1] if t['lng'] >= ns_lng(c, t['lat']))
            cells[(row, col)].append(t)
        blocks = cells   # kept as `blocks` below: one cell is one block segment of work

        rows = sorted({r for r, _c in blocks})
        print('\n=== %s (%s) zone %d: %d trees, %d occupied cells across %d street rows'
              % (rid, region['label'], region['zone'], len(sub), len(blocks), len(rows)))

        # Bands of consecutive rows, then cut each band into runs of columns
        # whose block count comes closest to TARGET_BLOCKS.
        for band_start in range(0, len(rows), ROWS_PER_BAND):
            band = rows[band_start:band_start + ROWS_PER_BAND]
            cols = sorted({c for r, c in blocks if r in band})
            counts = [sum(1 for r in band if (r, c) in blocks) for c in cols]
            total = sum(counts)
            if not total:
                continue
            n_cuts = max(1, int(round(total / float(TARGET_BLOCKS))))
            # Rounding alone lets a 14-block band through as one sub-zone,
            # which is half again the target. Force another cut past that.
            if total / float(n_cuts) > TARGET_BLOCKS * 1.3:
                n_cuts += 1
            per = total / float(n_cuts)

            chunks, cur, cur_n, taken = [], [], 0, 0
            for c, k in zip(cols, counts):
                cur.append(c)
                cur_n += k
                taken += k
                # close the chunk once it has covered its share, unless doing
                # so would leave too few columns for the chunks still to come
                remaining_chunks = n_cuts - len(chunks) - 1
                if (cur_n >= per and remaining_chunks > 0
                        and len(cols) - cols.index(c) - 1 >= remaining_chunks):
                    chunks.append(cur)
                    cur, cur_n = [], 0
            if cur:
                chunks.append(cur)

            for ci, chunk in enumerate(chunks):
                r0, r1 = min(band), max(band) + 1
                c0, c1 = min(chunk), max(chunk) + 1
                members = [(r, c) for r in band for c in chunk if (r, c) in blocks]
                tset = [t for rc in members for t in blocks[rc]]
                if not tset:
                    continue

                # Names come from the cells that actually hold trees; the
                # polygon runs to the region edge. Rows and columns at the
                # rim are often empty - the FDR frontage, the far side of a
                # park - and stopping the geometry there leaves bare gaps in
                # the middle of a zone that look like something went wrong.
                g_r0 = 0 if band_start == 0 else r0
                g_r1 = len(ew_cuts) - 1 if band_start + ROWS_PER_BAND >= len(rows) else r1
                g_c0 = 0 if ci == 0 else c0
                g_c1 = len(ns_cuts) - 1 if ci == len(chunks) - 1 else c1

                # A None cut is an open side; the CB3 boundary clip below is
                # what closes it.
                window = list(bbox)
                if ew_cuts[g_r0]:
                    window = clip_halfplane(window, ew_halfplane(ew_cuts[g_r0], True))
                if ew_cuts[g_r1]:
                    window = clip_halfplane(window, ew_halfplane(ew_cuts[g_r1], False))
                if ns_cuts[g_c0]:
                    window = clip_halfplane(window, ns_halfplane(ns_cuts[g_c0], False))
                if ns_cuts[g_c1]:
                    window = clip_halfplane(window, ns_halfplane(ns_cuts[g_c1], True))
                for div_key, keep_south in REGION_BOUNDS[rid]:
                    if len(window) < 3:
                        break
                    window = clip_halfplane(window, ew_halfplane(divs[div_key], keep_south))
                if len(window) < 3:
                    continue
                ring = clip_to_convex(boundary, window)
                if len(ring) < 3:
                    continue
                ring = ring + [ring[0]]

                zone = region['zone']
                per_zone_count[zone] += 1
                sid = '%d%s' % (zone, zone_letter(per_zone_count[zone] - 1))
                # A sub-zone is named for the streets it CONTAINS, not the
                # ones that bound it - which is the point of moving the edges
                # mid-block. "E 14th St to E 13th St, Bowery to Ave A" means
                # both sides of both streets, all the way across.
                streets = name_span([s['name'] for s in ew_streets[r0:r1]])
                avenues = name_span([s['name'] for s in ns_streets[c0:c1]])
                label = '%s, %s' % (streets, avenues)

                features.append({
                    'type': 'Feature',
                    'properties': {
                        'subzone_id': sid, 'zone': zone, 'region': rid,
                        'region_label': region['label'], 'label': label,
                        'streets': streets, 'avenues': avenues,
                        'blocks': len(members), 'tree_count': len(tset),
                        'area_m2': round(poly_area_m2(ring[:-1])),
                    },
                    'geometry': {'type': 'Polygon', 'coordinates': [ring]},
                })
                for t in tset:
                    csv_rows.append((t['tree_id'], sid, zone, t['lat'], t['lng'], t['species']))
                summary.append((sid, len(members), len(tset), label))
                print('  %-4s %2d blocks %4d trees   %s' % (sid, len(members), len(tset), label))

    assigned = sum(f['properties']['tree_count'] for f in features)
    blocks_all = [f['properties']['blocks'] for f in features]
    trees_all = [f['properties']['tree_count'] for f in features]
    print('\n%d sub-zones, %d/%d trees assigned' % (len(features), assigned, len(trees)))
    print('blocks per sub-zone : min %d  max %d  mean %.1f'
          % (min(blocks_all), max(blocks_all), sum(blocks_all) / len(blocks_all)))
    print('trees  per sub-zone : min %d  max %d  mean %.0f'
          % (min(trees_all), max(trees_all), sum(trees_all) / len(trees_all)))
    for z in (1, 2, 3):
        n = [f for f in features if f['properties']['zone'] == z]
        print('  zone %d: %2d sub-zones, %4d trees'
              % (z, len(n), sum(f['properties']['tree_count'] for f in n)))

    if assigned != len(trees):
        print('WARNING: %d trees fell outside every sub-zone' % (len(trees) - assigned))

    # The assignment above is index arithmetic; the polygons are geometry. They
    # are meant to describe the same thing, so check that they do - every tree
    # must sit inside the polygon of the sub-zone it was filed under, and
    # inside no other. Disagreement means a grid line and its half-plane have
    # drifted apart, which no amount of eyeballing the map would catch.
    rings = {f['properties']['subzone_id']: f['geometry']['coordinates'][0]
             for f in features}
    by_tree = {row[0]: row[1] for row in csv_rows}
    coords = {t['tree_id']: (t['lng'], t['lat']) for t in trees}
    outside = overlapping = 0
    for tid, sid in by_tree.items():
        lng, lat = coords[tid]
        if not point_in_poly(lng, lat, rings[sid]):
            outside += 1
        if sum(1 for s, r in rings.items() if point_in_poly(lng, lat, r)) > 1:
            overlapping += 1
    print('validation: %d trees outside their own sub-zone polygon, '
          '%d inside more than one' % (outside, overlapping))

    # What the mid-block boundaries cost. Every street now sits wholly inside
    # one sub-zone, both sides together - but the boundary has to cross the
    # network somewhere, and with the edges mid-block it crosses the streets
    # running perpendicular to it, part-way along a block. Count the block
    # segments that end up divided so the trade is visible rather than implied.
    seg_of = {}
    for rid in ('EV', 'LES', 'CH', 'TB'):
        region = regions.get(rid)
        if not region:
            continue
        for t in (x for x in trees if x['region'] == rid):
            best = None
            for family, lines in (('ew', region['ew']), ('ns', region['ns'])):
                for idx, l in enumerate(lines):
                    if family == 'ew':
                        d = abs(t['lat'] - ew_lat(l['line'], t['lng'])) * M_PER_DEG_LAT
                    else:
                        d = abs(t['lng'] - ns_lng(l['line'], t['lat'])) * M_PER_DEG_LNG
                    if best is None or d < best[0]:
                        best = (d, family, idx)
            _d, family, idx = best
            cross = region['ns'] if family == 'ew' else region['ew']
            if family == 'ew':
                along = sum(1 for l in cross if t['lng'] >= ns_lng(l['line'], t['lat']))
            else:
                along = sum(1 for l in cross if t['lat'] <= ew_lat(l['line'], t['lng']))
            seg_of[t['tree_id']] = (rid, family, idx, along)

    by_seg = collections.defaultdict(set)
    seg_trees = collections.Counter()
    for tid, sid in by_tree.items():
        by_seg[seg_of[tid]].add(sid)
        seg_trees[seg_of[tid]] += 1
    split = [s for s, ids in by_seg.items() if len(ids) > 1]
    split_trees = sum(seg_trees[s] for s in split)
    print('block segments: %d total, %d divided between two sub-zones '
          '(%d trees, %.1f%%)'
          % (len(by_seg), len(split), split_trees, 100.0 * split_trees / len(trees)))

    with open(OUT_GEOJSON, 'w') as f:
        json.dump({'type': 'FeatureCollection', 'features': features}, f)
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['treeId', 'subzoneId', 'zone', 'latitude', 'longitude', 'species'])
        w.writerows(csv_rows)
    print('\nWrote %s and %s' % (OUT_GEOJSON, OUT_CSV))


if __name__ == '__main__':
    main()
