#!/usr/bin/env python3
"""
Cut CB3's three care zones into sub-zones of roughly ten city blocks.

Every boundary here is a street. That is the whole point, and it is what the
two earlier attempts got wrong: build_work_cells.py cut sidewalk rows at
arbitrary tree counts, and build_rect_cells.py laid a rotated rectangular grid
over the district that sliced through the middle of blocks. Neither produced
an assignment a crew could be told in words or walk without a map.

How it works
------------
  1. data/cb3-street-grid.json (from build_street_grid.py) supplies named
     street centerlines per grid region. A BLOCK is one cell of that
     arrangement: the area between two consecutive E-W streets and two
     consecutive N-S streets. Blocks with no trees are not blocks - they are
     parks, water, or the inside of a superblock - and are dropped.
  2. Blocks are grouped into sub-zones by taking a band of consecutive street
     rows and cutting it into runs of consecutive avenue columns. A sub-zone
     is therefore always a rectangle in grid terms, bounded by exactly four
     named streets, which is what makes it describable: "E 4th St-E 2nd St,
     Bowery/3rd Ave-Ave B" rather than "cell 147".
  3. Sub-zones nest inside the existing three zones, because the region
     dividers are pinned to the same Houston/Grand lines index.html already
     draws (see PINS in build_street_grid.py). No sub-zone straddles a zone.

Sizing: TARGET_BLOCKS is the knob. At 10 blocks CB3 comes out as 31 sub-zones
of 5-13 blocks (mean 9.1) holding 58-264 trees (mean 171) - a season's
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


def edge_lines(region, family):
    """A family's streets with an open-ended entry bolted on each side.

    The outermost blocks are bounded on their far side by the district edge,
    not by a grid line, so those entries carry no geometry - only a name. It
    is usually a real street that the grid fit had to drop for want of trees
    to place it with (the Bowery on the west, the FDR on the east); where even
    that is unknown the block is labelled against the CB3 boundary itself."""
    lines = region[family]
    dropped = region.get(family + 'Dropped', [])
    n_streets = len(lines) + len(dropped)
    lead = next((d['name'] for d in dropped if d['before'] == 0), 'CB3 boundary')
    trail = next((d['name'] for d in dropped if d['before'] >= n_streets - 1),
                 'CB3 boundary')
    return ([{'name': lead, 'line': None, 'open': True}]
            + [dict(l, open=False) for l in lines]
            + [{'name': trail, 'line': None, 'open': True}])


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
        ew = edge_lines(region, 'ew')
        ns = edge_lines(region, 'ns')
        real_ew = [l for l in ew if not l['open']]
        real_ns = [l for l in ns if not l['open']]

        # Bucket every tree into a block. A tree's row is how many E-W streets
        # lie north of it; its column, how many N-S streets lie west of it.
        # The +1 shifts past the open-ended entry at index 0.
        blocks = collections.defaultdict(list)
        for t in sub:
            north_of = sum(1 for l in real_ew if t['lat'] <= ew_lat(l['line'], t['lng']))
            west_of = sum(1 for l in real_ns if t['lng'] >= ns_lng(l['line'], t['lat']))
            blocks[(north_of, west_of)].append(t)

        rows = sorted({r for r, _c in blocks})
        print('\n=== %s (%s) zone %d: %d trees, %d occupied blocks across %d rows'
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

            for chunk in chunks:
                r0, r1 = min(band), max(band) + 1
                c0, c1 = min(chunk), max(chunk) + 1
                members = [(r, c) for r in band for c in chunk if (r, c) in blocks]
                tset = [t for rc in members for t in blocks[rc]]
                if not tset:
                    continue

                # An open-ended entry contributes no half-plane; the CB3
                # boundary clip below is what closes that side.
                window = list(bbox)
                if ew[r0]['line']:
                    window = clip_halfplane(window, ew_halfplane(ew[r0]['line'], True))
                if ew[r1]['line']:
                    window = clip_halfplane(window, ew_halfplane(ew[r1]['line'], False))
                if ns[c0]['line']:
                    window = clip_halfplane(window, ns_halfplane(ns[c0]['line'], False))
                if ns[c1]['line']:
                    window = clip_halfplane(window, ns_halfplane(ns[c1]['line'], True))
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
                north, south = pretty(ew[r0]['name']), pretty(ew[r1]['name'])
                west, east = pretty(ns[c0]['name']), pretty(ns[c1]['name'])
                label = '%s–%s, %s–%s' % (north, south, west, east)

                features.append({
                    'type': 'Feature',
                    'properties': {
                        'subzone_id': sid, 'zone': zone, 'region': rid,
                        'region_label': region['label'], 'label': label,
                        'north': north, 'south': south, 'west': west, 'east': east,
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

    with open(OUT_GEOJSON, 'w') as f:
        json.dump({'type': 'FeatureCollection', 'features': features}, f)
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['treeId', 'subzoneId', 'zone', 'latitude', 'longitude', 'species'])
        w.writerows(csv_rows)
    print('\nWrote %s and %s' % (OUT_GEOJSON, OUT_CSV))


if __name__ == '__main__':
    main()
