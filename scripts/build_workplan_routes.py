#!/usr/bin/env python3
"""
Draw each 2027 Work Plan field day as a walk along real streets.

Inputs:
  data/work-plan-2027.json          the field days (not changed here)
  data/subzone-segments.geojson     current block names, to find each block's street
  data/streets/cb3-streets.json     OpenStreetMap streets around CB3, from
                                    scripts/fetch_street_centerlines.py

Output:
  data/work-plan-2027-routes.json   for each day, in the plan's stop order:
    blocks  one street line per stop, corner to corner along the stop's street
    links   the walk from one block to the next, along streets
    pins    where each stop's numbered pin goes

Only streets are used (OpenStreetMap roads people walk along: no footpaths,
service roads or the FDR Drive), so every line on the map runs along a street.
NYC's own centreline file (CSCL) was tried first, but the copy NYC Open Data
returned is missing pieces, such as Stanton St at Willett St. A housing-grounds stop has no block face; the walk
passes the nearest street point and its pin stays on the grounds.

Run: python3 scripts/build_workplan_routes.py
"""
import heapq, json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN = os.path.join(ROOT, 'data', 'work-plan-2027.json')
STREETS = os.path.join(ROOT, 'data', 'streets', 'cb3-streets.json')
SEGMENTS = os.path.join(ROOT, 'data', 'subzone-segments.geojson')
OUT = os.path.join(ROOT, 'data', 'work-plan-2027-routes.json')

REF_LNG, REF_LAT = -73.985, 40.72
M_LNG, M_LAT = 84400.0, 110540.0
TREE_REACH_M = 45      # a tree belongs to a street edge this close to it


def xy(lng, lat):
    return ((lng - REF_LNG) * M_LNG, (lat - REF_LAT) * M_LAT)


def ll(p):
    return [round(REF_LAT + p[1] / M_LAT, 6), round(REF_LNG + p[0] / M_LNG, 6)]


WORDS = {'STREET': 'ST', 'AVENUE': 'AVE', 'PLACE': 'PL', 'DRIVE': 'DR', 'EAST': 'E',
         'WEST': 'W', 'SAINT': 'ST', 'SQUARE': 'SQ', 'SLIP': 'SLIP'}


def norm(name):
    s = re.sub(r'[.]', '', name.upper())
    s = re.sub(r'\b(\d+)(ST|ND|RD|TH)\b', r'\1', s)
    return ' '.join(WORDS.get(w, w) for w in s.split())


ALIASES = {}


def street_names(label_street):
    names = set()
    for part in label_street.split('/'):
        n = norm(part)
        names.add(ALIASES.get(n, n))
    return names


def seg_dist(p, a, b):
    ax, ay = b[0] - a[0], b[1] - a[1]
    L2 = ax * ax + ay * ay
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / L2))
    q = (a[0] + t * ax, a[1] + t * ay)
    return math.hypot(p[0] - q[0], p[1] - q[1]), t, q


class Graph:
    def __init__(self, ways):
        self.node_id, self.nodes, self.edges, self.adj = {}, [], [], []
        key = lambda c: (round(c[0], 7), round(c[1], 7))
        # A way is cut into edges wherever it meets another way.
        uses = {}
        for w in ways:
            for c in w['coords']:
                uses[key(c)] = uses.get(key(c), 0) + 1
        for w in ways:
            name, cs = norm(w.get('name') or ''), w['coords']
            start = 0
            for i in range(1, len(cs)):
                if i == len(cs) - 1 or uses[key(cs[i])] > 1:
                    pts = [xy(*c) for c in cs[start:i + 1]]
                    self.add_edge(self.node(cs[start]), self.node(cs[i]), pts, name)
                    start = i

    def node(self, c):
        k = (round(c[0], 7), round(c[1], 7))
        if k not in self.node_id:
            self.node_id[k] = len(self.nodes)
            self.nodes.append(xy(*k))
            self.adj.append([])
        return self.node_id[k]

    def add_edge(self, u, v, pts, name):
        length = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
        e = len(self.edges)
        self.edges.append((u, v, pts, name, length))
        self.adj[u].append(e)
        self.adj[v].append(e)
        return e

    def nearest_edge(self, p, names=None, reach=TREE_REACH_M):
        best = None
        for e, (u, v, pts, name, _) in enumerate(self.edges):
            if names is not None and name not in names:
                continue
            for i in range(len(pts) - 1):
                d, t, q = seg_dist(p, pts[i], pts[i + 1])
                if d <= reach and (best is None or d < best[0]):
                    best = (d, e, i, q)
        return best

    def split(self, e, i, q):
        """Add a node at point q on edge e (between vertex i and i+1)."""
        u, v, pts, name, _ = self.edges[e]
        n = len(self.nodes)
        self.nodes.append(q)
        self.adj.append([])
        self.add_edge(u, n, pts[:i + 1] + [q], name)
        self.add_edge(n, v, [q] + pts[i + 1:], name)
        return n

    def path(self, s, t, names=None):
        """Shortest path s -> t as (length, [points]); None if unreachable."""
        dist, prev = {s: 0.0}, {}
        h = [(0.0, s)]
        while h:
            d, n = heapq.heappop(h)
            if n == t:
                break
            if d > dist.get(n, 1e18):
                continue
            for e in self.adj[n]:
                u, v, pts, name, L = self.edges[e]
                if names is not None and name not in names:
                    continue
                m = v if n == u else u
                nd = d + L
                if nd < dist.get(m, 1e18):
                    dist[m], prev[m] = nd, (n, e)
                    heapq.heappush(h, (nd, m))
        if t not in dist:
            return None
        pts, n = [], t
        while n != s:
            p, e = prev[n]
            u, v, epts, _, _ = self.edges[e]
            seg = epts if p == u else epts[::-1]
            pts = seg[1:] + pts
            n = p
        return dist[t], [self.nodes[s]] + pts


def stop_block(g, stop, labels):
    """Corner-to-corner street line for a block-face stop: (start node, end node, points)."""
    # The current block name; some plan labels predate the sub-zone renames.
    street = labels.get(stop['seg'], stop['label']).split(', ', 1)[0].split(' at ', 1)[0]
    names = street_names(street)
    trees = [xy(t[2], t[1]) for t in stop['trees']]
    hits = [g.nearest_edge(p, names) for p in trees]
    if sum(1 for h in hits if h) * 2 < len(hits):
        # Most trees aren't on the named street (or it isn't in CSCL there):
        # use the nearest street the trees share most.
        hits = [g.nearest_edge(p) for p in trees]
        counts = {}
        for h in hits:
            if h:
                counts[g.edges[h[1]][3]] = counts.get(g.edges[h[1]][3], 0) + 1
        if not counts:
            return None
        names = {max(counts, key=counts.get)}
        hits = [g.nearest_edge(p, names) for p in trees]
    ends = set()
    for h in hits:
        if h:
            u, v = g.edges[h[1]][:2]
            ends.update((u, v))
    ends = list(ends)
    # The two corners farthest apart that the street itself joins directly (a
    # divided street like Allen St has two carriageways; don't loop round).
    pairs = sorted(((x, y) for i, x in enumerate(ends) for y in ends[i + 1:]),
                   key=lambda q: -math.dist(g.nodes[q[0]], g.nodes[q[1]]))
    for a, b in pairs:
        r = g.path(a, b, names)
        if r and r[0] <= 1.3 * math.dist(g.nodes[a], g.nodes[b]) + 20:
            return a, b, r[1]
    return None


def stop_point(g, stop):
    n = len(stop['trees'])
    c = xy(sum(t[2] for t in stop['trees']) / n, sum(t[1] for t in stop['trees']) / n)
    h = g.nearest_edge(c, reach=400)
    return g.split(h[1], h[2], h[3]) if h else None


def main():
    if not os.path.exists(STREETS):
        sys.exit(f'{STREETS} is missing; run scripts/fetch_street_centerlines.py (in GitHub Actions).')
    g = Graph(json.load(open(STREETS))['ways'])
    plan = json.load(open(PLAN))
    labels = {f['properties']['segment_id']: f['properties']['label']
              for f in json.load(open(SEGMENTS))['features']}
    out_days, unrouted = [], []
    for day in plan['days']:
        stops = []
        for s in day['stops']:
            blk = None if '-off' in s['seg'] else stop_block(g, s, labels)
            if blk:
                stops.append({'a': blk[0], 'b': blk[1], 'pts': blk[2]})
            else:
                n = stop_point(g, s)
                if n is None:
                    unrouted.append((day['date'], s['seg']))
                    stops.append(None)
                    continue
                k = len(s['trees'])
                pin = xy(sum(t[2] for t in s['trees']) / k, sum(t[1] for t in s['trees']) / k)
                stops.append({'a': n, 'b': n, 'pts': [g.nodes[n]], 'pin': pin, 'grounds': True})

        def walk(x, y):
            r = g.path(x, y)
            return r if r else (1e18, None)

        # Turn the first block toward the second, then each block so it starts
        # at the end the walk reaches first.
        real = [s for s in stops if s]
        if len(real) > 1:
            f, nx = real[0], real[1]
            if min(walk(f['a'], nx['a'])[0], walk(f['a'], nx['b'])[0]) < \
               min(walk(f['b'], nx['a'])[0], walk(f['b'], nx['b'])[0]):
                f['a'], f['b'], f['pts'] = f['b'], f['a'], f['pts'][::-1]
        links, prev = [], None
        for s in stops:
            if s is None:
                continue
            if prev is not None:
                da, db = walk(prev['b'], s['a']), walk(prev['b'], s['b'])
                if db[0] < da[0]:
                    s['a'], s['b'], s['pts'] = s['b'], s['a'], s['pts'][::-1]
                    da = db
                if da[1] and len(da[1]) > 1:
                    links.append([ll(p) for p in da[1]])
            prev = s
        out_days.append({
            'date': day['date'],
            'blocks': [[ll(p) for p in s['pts']] if s else None for s in stops],
            'pins': [ll(s.get('pin') or s['pts'][0]) if s else None for s in stops],
            'links': links,
        })
    out = {
        'generated_from': 'data/work-plan-2027.json',
        'streets': 'OpenStreetMap contributors (ODbL)',
        'days': out_days,
    }
    with open(OUT, 'w') as f:
        json.dump(out, f, separators=(',', ':'))
    print(f'{len(out_days)} days written to {os.path.relpath(OUT, ROOT)}')
    if unrouted:
        print('Stops with no street nearby:', unrouted)


if __name__ == '__main__':
    main()
