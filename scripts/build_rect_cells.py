#!/usr/bin/env python3
"""
Build rectangular work-plan cells for CB3 street trees.

Same source data as build_work_cells.py (5,315 live street trees inside the
CB3 boundary), but a different shape: a rotated grid rather than lines that
chase individual sidewalk rows. Rectangles are easier to hand out and talk
about ("the cell between X and Y") than a wiggly blockface path, at the cost
of not following real block boundaries exactly.

Approach:
  1. Reuse build_work_cells' tree loader/projection and its direction graph
     (each tree linked to a forward/backward sidewalk neighbor) purely to
     read off the dominant street bearing in CB3's own data — folding edge
     bearings into a 0-90 degree histogram and taking the peak, rather than
     assuming a textbook "Manhattan grid is rotated 29 degrees" figure that
     doesn't hold south of Houston, where CB3's Chinatown/LES streets
     predate the 1811 grid.
  2. Rotate all tree points so that dominant bearing lines up with the axes.
  3. Recursively bisect the point set by the widest-variance axis (a k-d
     tree), splitting only when a group has more than 30 trees. Splitting
     as evenly as possible when a group's size n > 30 guarantees every leaf
     lands in [15, 30]: a group only ever gets left un-split once its size
     is already <= 30, and the only way to *reach* a leaf of size <= 30 is
     by bisecting a parent whose size was in (30, 60] — which puts both
     halves at >= floor(31/2)=15 and <= ceil(60/2)=30. No merge/leftover
     pass is needed, unlike the blockface-chaining approach.
  4. Each leaf's rectangle is the padded bounding box of its points in the
     rotated frame, rotated back to real lng/lat for output.

Output:
  data/work-cells-rect.geojson — one Polygon feature per cell
  data/work-cells-rect.csv     — treeId,cellId,latitude,longitude,species

NOTE: same caveat as build_work_cells.py — no street-name data was
available and this session can't reach NYC's street centerline dataset
(data.cityofnewyork.us blocked by the sandbox's egress policy), so rectangle
edges approximate the street grid rather than tracing real block lines.
"""

import json
import math
import os
import csv
import statistics

from build_work_cells import (
    load_trees, project, build_direction_graph,
    NEIGHBOR_RADIUS_M, MIN_OPPOSITE_ANGLE_DEG,
    TARGET_MIN, TARGET_MAX,
)

RECT_PAD_M = 5.0  # margin added around each leaf's point bounding box

ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT_GEOJSON = os.path.join(ROOT, 'data', 'work-cells-rect.geojson')
OUT_CSV = os.path.join(ROOT, 'data', 'work-cells-rect.csv')


def detect_grid_angle_deg(trees, adj):
    """Histogram the bearing of every tree-to-tree edge, folded into
    [0, 90) degrees (street/avenue families are ~perpendicular, so this
    overlays both onto one axis), and return the peak bin as the dominant
    local street angle."""
    bins = [0] * 90
    for i, neighbors in enumerate(adj):
        for j in neighbors:
            if j <= i:
                continue
            dx = trees[j]['x'] - trees[i]['x']
            dy = trees[j]['y'] - trees[i]['y']
            ang = math.degrees(math.atan2(dy, dx)) % 90
            bins[int(ang) % 90] += 1
    return max(range(90), key=lambda b: bins[b])


def rotate(x, y, angle_deg):
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    return x * ca + y * sa, -x * sa + y * ca


def partition(idxs, rot):
    """Recursively bisect idxs (by the widest-variance rotated axis) until
    every group has <= TARGET_MAX trees. See module docstring for why this
    guarantees every leaf lands in [TARGET_MIN, TARGET_MAX]."""
    if len(idxs) <= TARGET_MAX:
        return [idxs]
    xs = [rot[i][0] for i in idxs]
    ys = [rot[i][1] for i in idxs]
    axis = 0 if statistics.pvariance(xs) >= statistics.pvariance(ys) else 1
    ordered = sorted(idxs, key=lambda i: rot[i][axis])
    mid = len(ordered) // 2
    return partition(ordered[:mid], rot) + partition(ordered[mid:], rot)


def main():
    trees = load_trees()
    lat0, lng0, cos0 = project(trees)
    n = len(trees)
    print(f'Loaded {n} live street trees inside CB3 boundary.')

    adj = build_direction_graph(trees, NEIGHBOR_RADIUS_M, MIN_OPPOSITE_ANGLE_DEG)
    angle = detect_grid_angle_deg(trees, adj)
    print(f'Detected dominant street angle: {angle}\N{DEGREE SIGN} (from tree-row edge bearings).')

    rot = [rotate(t['x'], t['y'], angle) for t in trees]
    leaves = partition(list(range(n)), rot)

    sizes = [len(l) for l in leaves]
    print(f'{len(leaves)} rectangular cells. min={min(sizes)} max={max(sizes)} '
          f'avg={sum(sizes)/len(sizes):.1f}')
    out_of_range = [s for s in sizes if not (TARGET_MIN <= s <= TARGET_MAX)]
    print(f'{len(out_of_range)} cells outside {TARGET_MIN}-{TARGET_MAX}.')

    features = []
    csv_rows = []
    for cell_id, idxs in enumerate(leaves, start=1):
        rxs = [rot[i][0] for i in idxs]
        rys = [rot[i][1] for i in idxs]
        rx0, rx1 = min(rxs) - RECT_PAD_M, max(rxs) + RECT_PAD_M
        ry0, ry1 = min(rys) - RECT_PAD_M, max(rys) + RECT_PAD_M
        ring = []
        for cx, cy in [(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1), (rx0, ry0)]:
            x, y = rotate(cx, cy, -angle)
            lng = x / (cos0 * 111320.0) + lng0
            lat = y / 110540.0 + lat0
            ring.append([lng, lat])

        tree_ids = [trees[i]['tree_id'] for i in idxs]
        features.append({
            'type': 'Feature',
            'properties': {
                'cell_id': cell_id,
                'tree_count': len(idxs),
                'tree_ids': tree_ids,
            },
            'geometry': {'type': 'Polygon', 'coordinates': [ring]},
        })
        for i in idxs:
            csv_rows.append((trees[i]['tree_id'], cell_id, trees[i]['lat'],
                              trees[i]['lng'], trees[i]['species']))

    with open(OUT_GEOJSON, 'w') as f:
        json.dump({'type': 'FeatureCollection', 'features': features}, f)
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['treeId', 'cellId', 'latitude', 'longitude', 'species'])
        w.writerows(csv_rows)

    print(f'Wrote {OUT_GEOJSON} and {OUT_CSV}')


if __name__ == '__main__':
    main()
