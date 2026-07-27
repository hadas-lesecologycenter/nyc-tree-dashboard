#!/usr/bin/env python3
"""
Build street-aligned work-plan cells from the CB3 street tree census.

Approach (no street-name data is available — see README note below):
  1. Filter census.json to live ("Full") street trees inside cb3-boundary.json.
  2. Project to local meters. Street trees sit in a row along the sidewalk,
     so every tree gets linked to at most two others — a 'forward' and a
     'backward' neighbor, roughly opposite each other — approximating the
     two directions along the row it's planted in. Edges are accepted
     greedily shortest-first, each tree capped at degree 2, rejecting any
     edge that would close a short loop, so trees chain into blockface-like
     paths without ever forming a hub node.
  3. Long paths get cut into 15-30 tree segments. Short leftover fragments
     (a real gap in the row, a missing tree pit, a plaza) get stitched onto
     the nearest fragment or cell by endpoint distance — capped at
     MERGE_CAP_M so two unrelated nearby blockfaces don't get spliced
     together just because they happen to be close as the crow flies.
     Fragments with no close-enough partner stay their own (undersized) cell
     rather than being forced onto something far away.

Output:
  data/work-cells.geojson  — one LineString feature per cell (walking order)
  data/work-cells.csv      — treeId,cellId,latitude,longitude

NOTE: This is a geometric approximation, not real street topology. NYC's
street centerline dataset would give cleaner, named block boundaries, but
this session had no network access to fetch it (data.cityofnewyork.us is
blocked by the sandbox's egress policy). Re-run against real street data
if/when it's available in this repo.
"""

import json
import math
import os
import csv

TARGET_MIN = 15
TARGET_MAX = 30
TARGET_MID = 22
# Real tree-pit spacing is noisy (missing/dead pits create gaps well past the
# ~8.6m median nearest-neighbor distance), so the chain radius has to be
# generous enough to bridge those gaps. Tuned empirically by sweeping radius/
# angle/merge-cap combinations and checking (a) % of cells landing in
# 15-30 and (b) that per-cell path length stays block-scale (a few hundred
# meters), not sprawling — this combo was the best tradeoff found.
NEIGHBOR_RADIUS_M = 90.0
MIN_OPPOSITE_ANGLE_DEG = 40.0  # how "opposite" the back-neighbor must be from the forward one
MERGE_CAP_M = 65.0  # max endpoint-to-endpoint gap allowed when stitching leftover fragments together

ROOT = os.path.join(os.path.dirname(__file__), '..')
CENSUS_PATH = os.path.join(ROOT, 'data', 'census.json')
BOUNDARY_PATH = os.path.join(ROOT, 'data', 'cb3-boundary.json')
OUT_GEOJSON = os.path.join(ROOT, 'data', 'work-cells.geojson')
OUT_CSV = os.path.join(ROOT, 'data', 'work-cells.csv')


def point_in_poly(x, y, poly):
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi):
            inside = not inside
        j = i
    return inside


def load_trees():
    boundary = json.load(open(BOUNDARY_PATH))
    census = json.load(open(CENSUS_PATH))
    trees = []
    for t in census:
        if t.get('tree_type') != 'street' or t.get('status') != 'Full':
            continue
        try:
            lat = float(t['latitude'])
            lng = float(t['longitude'])
        except (TypeError, ValueError):
            continue
        if point_in_poly(lng, lat, boundary):
            trees.append({'tree_id': t['tree_id'], 'lat': lat, 'lng': lng,
                           'species': t.get('spc_common', '')})
    return trees


def project(trees):
    lat0 = sum(t['lat'] for t in trees) / len(trees)
    lng0 = sum(t['lng'] for t in trees) / len(trees)
    cos0 = math.cos(math.radians(lat0))
    for t in trees:
        t['x'] = (t['lng'] - lng0) * cos0 * 111320.0
        t['y'] = (t['lat'] - lat0) * 110540.0
    return trees


def build_grid(trees, cell_size):
    grid = {}
    for i, t in enumerate(trees):
        key = (int(t['x'] // cell_size), int(t['y'] // cell_size))
        grid.setdefault(key, []).append(i)
    return grid


def angle_diff_deg(a, b):
    diff = abs(math.degrees(a - b))
    diff = diff % 360
    return diff if diff <= 180 else 360 - diff


def all_candidate_edges(trees, radius):
    grid = build_grid(trees, radius)
    edges = []
    seen = set()
    for (gx, gy), idxs in grid.items():
        neighbor_idxs = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                neighbor_idxs.extend(grid.get((gx + dx, gy + dy), []))
        for i in idxs:
            xi, yi = trees[i]['x'], trees[i]['y']
            for j in neighbor_idxs:
                if j <= i or (i, j) in seen:
                    continue
                seen.add((i, j))
                xj, yj = trees[j]['x'], trees[j]['y']
                d = math.hypot(xi - xj, yi - yj)
                if d <= radius:
                    edges.append((d, i, j))
    return edges


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, a):
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def build_direction_graph(trees, radius, min_opposite_angle):
    """Greedily accept the globally shortest tree-to-tree edges first, each
    capped to degree 2 per tree and rejected if it would close a loop
    (union-find), so trees end up chained into the two directions along the
    sidewalk row they're planted in — 'forward' and 'backward' — without
    ever forming a hub or a short closed loop. A tree's second edge must be
    roughly opposite its first (>= min_opposite_angle) so a node continues
    the row's direction rather than doubling back on itself.

    An earlier version proposed each tree's own top-2 neighbors independently
    and merged the results, which fragmented into hundreds of 2-3 tree
    pieces because many trees only agree with a neighbor's proposal one
    direction at a time. Globally sorting all candidate edges and accepting
    greedily produces much longer, cleaner chains (closer to whole
    blockfaces) since every accepted edge is a genuine mutual best choice
    given what's already been committed."""
    n = len(trees)
    edges = all_candidate_edges(trees, radius)
    edges.sort(key=lambda e: e[0])

    uf = UnionFind(n)
    degree = [0] * n
    bearing = [None] * n  # bearing (radians) of the tree's first accepted edge
    adj = [[] for _ in range(n)]

    for d, i, j in edges:
        if degree[i] >= 2 or degree[j] >= 2:
            continue
        if uf.find(i) == uf.find(j):
            continue  # would close a small loop instead of extending a path
        xi, yi = trees[i]['x'], trees[i]['y']
        xj, yj = trees[j]['x'], trees[j]['y']
        ang_ij = math.atan2(yj - yi, xj - xi)
        ang_ji = ang_ij + math.pi
        if degree[i] == 1 and angle_diff_deg(ang_ij, bearing[i]) < min_opposite_angle:
            continue
        if degree[j] == 1 and angle_diff_deg(ang_ji, bearing[j]) < min_opposite_angle:
            continue
        adj[i].append(j)
        adj[j].append(i)
        if degree[i] == 0:
            bearing[i] = ang_ij
        if degree[j] == 0:
            bearing[j] = ang_ji
        degree[i] += 1
        degree[j] += 1
        uf.union(i, j)

    return adj


def decompose_paths(adj):
    """Break a graph (list-of-neighbors adjacency) into simple paths between
    degree!=2 nodes (endpoints/junctions). Degree-2 chains become one path.
    A second pass breaks any leftover pure cycles (all degree 2) by cutting
    at an arbitrary node, since the direction-aware graph isn't guaranteed
    acyclic the way a spanning tree would be."""
    n = len(adj)
    visited_edges = set()

    def edge_key(a, b):
        return (a, b) if a < b else (b, a)

    def walk_from(start, nxt):
        path = [start]
        prev, cur = start, nxt
        visited_edges.add(edge_key(start, nxt))
        while True:
            path.append(cur)
            if len(adj[cur]) != 2:
                break
            a, b = adj[cur]
            nxt2 = b if a == prev else a
            ek2 = edge_key(cur, nxt2)
            if ek2 in visited_edges:
                break
            visited_edges.add(ek2)
            prev, cur = cur, nxt2
        return path

    paths = []

    # Pass 1: start walks from every non-degree-2 node (endpoints + junctions).
    for start in range(n):
        if len(adj[start]) == 2:
            continue
        for nxt in adj[start]:
            ek = edge_key(start, nxt)
            if ek in visited_edges:
                continue
            paths.append(walk_from(start, nxt))

    # Isolated nodes (degree 0) never entered the loop's inner for-loop.
    for i in range(n):
        if len(adj[i]) == 0:
            paths.append([i])

    # Pass 2: leftover pure cycles (every node degree 2, no junction reached).
    for i in range(n):
        for j in adj[i]:
            ek = edge_key(i, j)
            if ek not in visited_edges:
                paths.append(walk_from(i, j))

    return paths


def split_long_path(path):
    """Cut a path longer than TARGET_MAX into balanced chunks in [TARGET_MIN, TARGET_MAX]."""
    length = len(path)
    n_chunks = max(1, round(length / TARGET_MID))
    while True:
        base = length // n_chunks
        rem = length % n_chunks
        sizes = [base + 1 if i < rem else base for i in range(n_chunks)]
        if all(TARGET_MIN <= s <= TARGET_MAX for s in sizes) or n_chunks > length:
            break
        # nudge chunk count toward a feasible split
        if min(sizes) < TARGET_MIN:
            n_chunks -= 1
        else:
            n_chunks += 1
        if n_chunks < 1:
            n_chunks = 1
            break
    chunks = []
    idx = 0
    for s in sizes:
        chunks.append(path[idx:idx + s])
        idx += s
    return chunks


def endpoints_xy(trees, path):
    a, b = trees[path[0]], trees[path[-1]]
    return (a['x'], a['y']), (b['x'], b['y'])


def stitch(path_a, path_b, mode):
    """Concatenate two tree-index paths end-to-end per the orientation that
    produced the shortest endpoint gap."""
    if mode == 'a_end_b_start':
        return path_a + path_b
    if mode == 'a_end_b_end':
        return path_a + list(reversed(path_b))
    if mode == 'a_start_b_start':
        return list(reversed(path_a)) + path_b
    return list(reversed(path_a)) + list(reversed(path_b))  # a_start_b_end


def best_join(trees, path_a, path_b):
    (a0, a1) = endpoints_xy(trees, path_a)
    (b0, b1) = endpoints_xy(trees, path_b)
    options = [
        (math.hypot(a1[0] - b0[0], a1[1] - b0[1]), 'a_end_b_start'),
        (math.hypot(a1[0] - b1[0], a1[1] - b1[1]), 'a_end_b_end'),
        (math.hypot(a0[0] - b0[0], a0[1] - b0[1]), 'a_start_b_start'),
        (math.hypot(a0[0] - b1[0], a0[1] - b1[1]), 'a_start_b_end'),
    ]
    return min(options, key=lambda o: o[0])


def merge_small_pieces(trees, small_pieces, good_cells, cap):
    """Repeatedly stitch the two geographically closest loose ends together
    (by endpoint distance, not centroid — merging by centroid let two
    unrelated, merely nearby blockfaces get concatenated into one long
    zig-zagging 'cell', since a fragment's centroid says nothing about which
    end is actually close to what). Only stitches within `cap` meters, so a
    fragment with no plausible neighbor stays its own (possibly undersized)
    cell instead of being forced onto something far away.

    Small pieces are tried against each other first, then against the
    already-well-sized cells, since two adjacent leftover crumbs are more
    likely to be parts of the same blockface than a crumb and a full cell."""
    pool = list(small_pieces)
    finalized = []

    while pool:
        best = None  # (dist, kind, i, j, mode) kind: 'pool' or 'cell'
        for i in range(len(pool)):
            for j in range(i + 1, len(pool)):
                d, mode = best_join(trees, pool[i], pool[j])
                if best is None or d < best[0]:
                    best = (d, 'pool', i, j, mode)
        for i in range(len(pool)):
            for j in range(len(good_cells)):
                d, mode = best_join(trees, pool[i], good_cells[j])
                if best is None or d < best[0]:
                    best = (d, 'cell', i, j, mode)

        if best is None or best[0] > cap:
            break

        d, kind, i, j, mode = best
        if kind == 'pool':
            merged = stitch(pool[i], pool[j], mode)
            for idx in sorted((i, j), reverse=True):
                pool.pop(idx)
        else:
            merged = stitch(pool[i], good_cells[j], mode)
            pool.pop(i)
            good_cells.pop(j)

        if len(merged) > TARGET_MAX:
            finalized.extend(split_long_path(merged))
        elif len(merged) >= TARGET_MIN:
            good_cells.append(merged)
        else:
            pool.append(merged)

    # Whatever's left couldn't find a close-enough partner — keep as-is.
    finalized.extend(pool)
    return finalized


def main():
    trees = load_trees()
    project(trees)
    n = len(trees)
    print(f'Loaded {n} live street trees inside CB3 boundary.')

    adj = build_direction_graph(trees, NEIGHBOR_RADIUS_M, MIN_OPPOSITE_ANGLE_DEG)
    degrees = [len(a) for a in adj]
    print(f'Direction graph: degree 0={degrees.count(0)}, 1={degrees.count(1)}, '
          f'2={degrees.count(2)}, 3+={sum(1 for d in degrees if d >= 3)}')

    raw_paths = decompose_paths(adj)
    print(f'{len(raw_paths)} raw blockface-like paths before sizing.')

    good_cells = []  # list of list-of-indices, sized TARGET_MIN..TARGET_MAX
    small_pieces = []
    oversized_final = []
    for path in raw_paths:
        if len(path) > TARGET_MAX:
            oversized_final.extend(split_long_path(path))
        elif len(path) >= TARGET_MIN:
            good_cells.append(path)
        else:
            small_pieces.append(path)

    print(f'{len(small_pieces)} fragments below {TARGET_MIN} trees need stitching '
          f'(within {MERGE_CAP_M}m endpoint gap).')
    stitched_leftovers = merge_small_pieces(trees, small_pieces, good_cells, MERGE_CAP_M)

    final_cells = oversized_final + good_cells + stitched_leftovers

    sizes = [len(c) for c in final_cells]
    print(f'{len(final_cells)} final cells. '
          f'min={min(sizes)} max={max(sizes)} avg={sum(sizes)/len(sizes):.1f}')
    out_of_range = [s for s in sizes if not (TARGET_MIN <= s <= TARGET_MAX)]
    print(f'{len(out_of_range)} cells outside {TARGET_MIN}-{TARGET_MAX}: {sorted(out_of_range)}')

    # ── Write outputs ──────────────────────────────────────────────────────
    features = []
    csv_rows = []
    for cell_id, idxs in enumerate(final_cells, start=1):
        coords = [[trees[i]['lng'], trees[i]['lat']] for i in idxs]
        tree_ids = [trees[i]['tree_id'] for i in idxs]
        features.append({
            'type': 'Feature',
            'properties': {
                'cell_id': cell_id,
                'tree_count': len(idxs),
                'tree_ids': tree_ids,
            },
            'geometry': {
                'type': 'LineString' if len(coords) > 1 else 'MultiPoint',
                'coordinates': coords,
            },
        })
        for i in idxs:
            csv_rows.append((trees[i]['tree_id'], cell_id, trees[i]['lat'], trees[i]['lng'], trees[i]['species']))

    with open(OUT_GEOJSON, 'w') as f:
        json.dump({'type': 'FeatureCollection', 'features': features}, f)
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['treeId', 'cellId', 'latitude', 'longitude', 'species'])
        w.writerows(csv_rows)

    print(f'Wrote {OUT_GEOJSON} and {OUT_CSV}')


if __name__ == '__main__':
    main()
