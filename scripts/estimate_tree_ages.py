#!/usr/bin/env python3
"""
Estimate a planting year for every living tree in data/census.json that has
no planting date, and write it back as one field:

  age_est: [best-guess year, earliest plausible, latest plausible, source]

where source is one of the SOURCES codes below (its confidence is in
CONFIDENCE). One packed field rather than five because every visitor
downloads census.json in full on every page load (see fetch_census.py).

The planting date fields themselves (planteddate, tree_cen_date) are never
touched, so the priority tiers in index.html — which read only those — are
unaffected by any of this.

How it works
------------
1. Match: each Forestry tree is paired with the census tree standing at the
   same spot in the 1995, 2005 and 2015 Street Tree Censuses
   (data/census-history/, written by fetch_historic_censuses.py) — nearest
   within a few metres, same genus, and not implausibly fatter back then than
   it is now. Each census tree pairs with at most one Forestry tree.
2. Calibrate growth: a tree matched in two consecutive censuses shows how fast
   its trunk grew in those ten years. The median of that, per species and per
   size class, is the local growth rate. Species with too few matched trees
   fall back to data/growth-rates-published.json, then to their genus, then
   to all trees.
3. Date: the earliest census a tree appears in proves it was planted by then,
   and its diameter in that census, grown back down to planting size at the
   calibrated rate, says how long before. A tree missing from the census
   before is bounded by that census too. Trees in no census (park trees —
   the censuses only cover street trees — and street trees planted since)
   are dated from their current diameter alone, with a wide range.

Runs offline. Re-run after fetch_census.py rewrites census.json.
"""

import json, math, os, statistics, sys
from datetime import date

ROOT        = os.path.join(os.path.dirname(__file__), '..')
CENSUS_PATH = os.path.join(ROOT, 'data', 'census.json')
HISTORY_DIR = os.path.join(ROOT, 'data', 'census-history')
PUBLISHED   = os.path.join(ROOT, 'data', 'growth-rates-published.json')
CALIB_PATH  = os.path.join(ROOT, 'data', 'tree-age-calibration.json')

CENSUS_YEARS = (1995, 2005, 2015)

# Matching radius per census, in metres. The 2015 census was mapped on aerial
# imagery and Forestry Tree Points was seeded from it, so positions agree
# closely; the 1995 census recorded trees by street address and its
# coordinates were geocoded afterwards, so they sit further off.
MATCH_RADIUS_M = {1995: 10.0, 2005: 6.0, 2015: 3.0}

# A census tree can't be much fatter than the tree there now — if it is, the
# spot has been replanted. The slack covers measurement error and the fact
# that a Forestry diameter may have been recorded years ago.
def dbh_plausible(census_dbh, current_dbh):
    if not current_dbh:
        return True
    return census_dbh <= current_dbh + max(4.0, 0.35 * current_dbh)

# Growth calibration
MIN_SPECIES_N = 20      # matched trees needed to trust a species' own rate
MIN_CLASS_N   = 10      # …and to trust its rate within one size class
DBH_CLASSES   = (0, 6, 12, 18, 24, 999)   # inches
RATE_FLOOR, RATE_CEIL = 0.05, 1.5         # in/yr — clip noise, not biology
PUBLISHED_SPREAD = 0.3  # ± fraction used as the range for a published rate

# Census diameters were taped by volunteers and recorded in whole inches, so
# a range built on one should allow for it being off by about this much.
DBH_ERROR_IN = 1.5

# Planting-size fallback if census.json has too few recent plantings to
# measure it: NYC street trees go in at about a 3" caliper.
DEFAULT_PLANTING_DBH = 3.0

# A street tree in no census whose diameter says it could be this young is
# taken to have been planted after the 2015 census.
POST_2015_START = 2016

# A Forestry diameter has no date — it was recorded at planting or at some
# later inspection, mostly since Forestry Tree Points began. Trees dated from
# it alone assume it was measured somewhere in this window.
DBH_MEASURED_FROM = 2015

SOURCES = {
    'c1995': 'In the 1995 census; dated back from its 1995 diameter',
    'c2005': 'First in the 2005 census, not in 1995: planted 1996–2005',
    'c2015': 'First in the 2015 census, not in 2005: planted 2006–2015',
    'c2005m': 'First in the 2005 census; too big to be new, so likely missed in 1995',
    'c2015m': 'First in the 2015 census; too big to be new, so likely missed in 2005',
    'new':   'Street tree in no census and still small: planted after 2015',
    'dbh':   'Current diameter and species growth rate only',
}

CONFIDENCE = {'c1995': 'medium', 'c2005': 'high', 'c2015': 'high',
              'c2005m': 'medium', 'c2015m': 'medium', 'new': 'low', 'dbh': 'low'}
PLANTING_DATE_FIELDS = ('tree_cen_date', 'planteddate')


# ── Names ─────────────────────────────────────────────────────────────────────

def species_key(latin):
    """'Gleditsia triacanthos var. inermis' → 'gleditsia triacanthos'."""
    s = (latin or '').lower().replace('×', ' x ')
    if "'" in s:
        s = s[:s.index("'")]
    s = s.split(' var.')[0].split(' - ')[0]
    words = [w for w in s.replace(',', ' ').split() if w]
    if not words or words[0] in ('unknown', 'dead', 'stump'):
        return None
    if len(words) >= 3 and words[1] == 'x':
        return ' '.join(words[:3])
    if len(words) >= 2 and words[1] not in ('sp', 'sp.', 'spp', 'spp.'):
        return ' '.join(words[:2])
    return words[0]


def genus_of(latin):
    key = species_key(latin)
    return key.split()[0] if key else None


def norm_common(name):
    return ''.join(ch for ch in (name or '').lower() if ch.isalpha())


def same_kind(f_genus, f_common, c_genus, c_common):
    if f_genus and c_genus:
        return f_genus == c_genus
    a, b = norm_common(f_common), norm_common(c_common)
    return bool(a) and a == b


# ── Geometry ──────────────────────────────────────────────────────────────────

LAT0 = 40.72
M_PER_DEG_LAT = 110_574.0
M_PER_DEG_LNG = 111_320.0 * math.cos(math.radians(LAT0))
CELL = 10.0   # metres per grid cell; ≥ the largest match radius


def xy(lat, lng):
    return (lng + 74.0) * M_PER_DEG_LNG, (lat - LAT0) * M_PER_DEG_LAT


def build_grid(points):
    grid = {}
    for i, (x, y) in enumerate(points):
        grid.setdefault((int(x // CELL), int(y // CELL)), []).append(i)
    return grid


def near(grid, x, y):
    cx, cy = int(x // CELL), int(y // CELL)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            yield from grid.get((cx + dx, cy + dy), ())


# ── Loading ───────────────────────────────────────────────────────────────────

def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def planted_year(tree):
    for f in PLANTING_DATE_FIELDS:
        y = int(num(str(tree.get(f) or '')[:4]))
        if y > 1800:
            return y
    return None


def load_history():
    history = {}
    for year in CENSUS_YEARS:
        path = os.path.join(HISTORY_DIR, f'{year}.json')
        if not os.path.exists(path):
            print(f'  {year} census: not found at {os.path.relpath(path, ROOT)} — skipped')
            continue
        with open(path) as f:
            data = json.load(f)
        idx = {name: i for i, name in enumerate(data['fields'])}
        rows = []
        for r in data['trees']:
            latin, common = r[idx['latin']], r[idx['common']]
            rows.append({'lat': r[idx['lat']], 'lng': r[idx['lng']], 'dbh': float(r[idx['dbh']]),
                         'genus': genus_of(latin), 'common': common})
        with_genus = sum(1 for r in rows if r['genus'])
        print(f'  {year} census: {len(rows)} living trees '
              f'({with_genus / max(1, len(rows)):.0%} with a Latin name)')
        history[year] = rows
    return history


# ── 1. Match ──────────────────────────────────────────────────────────────────

def match_census(trees, census, radius):
    """{tree index: census row} — greedy one-to-one, nearest pairs first."""
    pts = [xy(c['lat'], c['lng']) for c in census]
    grid = build_grid(pts)
    pairs = []
    for ti, t in enumerate(trees):
        tx, ty = t['_xy']
        for ci in near(grid, tx, ty):
            c = census[ci]
            d = math.hypot(pts[ci][0] - tx, pts[ci][1] - ty)
            if d > radius:
                continue
            if not same_kind(t['_genus'], t.get('spc_common'), c['genus'], c['common']):
                continue
            if not dbh_plausible(c['dbh'], t['_dbh']):
                continue
            pairs.append((d, ti, ci))
    pairs.sort()
    used_t, used_c, out = set(), set(), {}
    for d, ti, ci in pairs:
        if ti in used_t or ci in used_c:
            continue
        used_t.add(ti)
        used_c.add(ci)
        out[ti] = census[ci]
    return out


def drop_replanted(seen):
    """Remove earlier sightings a later one contradicts.

    A trunk that shrinks by more than measurement error between censuses is a
    different tree on the same spot, so only the later sighting is this tree.
    """
    years = sorted(seen)
    for i in range(len(years) - 1, 0, -1):
        later, earlier = seen[years[i]]['dbh'], seen[years[i - 1]]['dbh']
        if later < earlier - max(3.0, 0.3 * earlier):
            for y in years[:i]:
                seen.pop(y, None)
            break
    return seen


# ── 2. Calibrate growth ───────────────────────────────────────────────────────

def size_class(dbh):
    for lo, hi in zip(DBH_CLASSES, DBH_CLASSES[1:]):
        if lo <= dbh < hi:
            return lo
    return DBH_CLASSES[-2]


def clip(rate):
    return min(RATE_CEIL, max(RATE_FLOOR, rate))


def quartiles(values):
    if len(values) < 4:
        m = statistics.median(values)
        return m, m, m
    q = statistics.quantiles(values, n=4)
    return q[0], statistics.median(values), q[2]


class GrowthModel:
    """Trunk growth in inches/year by species and size class."""

    def __init__(self, increments, published):
        # increments: list of (species_key, genus, start_dbh, inches_per_year)
        self.species, self.genus, self.classes = {}, {}, {}
        by_sp, by_genus, by_class, everything = {}, {}, {}, []
        for sp, genus, start, rate in increments:
            everything.append(rate)
            if sp:
                by_sp.setdefault(sp, []).append(rate)
                by_class.setdefault((sp, size_class(start)), []).append(rate)
            if genus:
                by_genus.setdefault(genus, []).append(rate)

        def summarise(values, source):
            lo, mid, hi = quartiles(values)
            mid = clip(mid)
            # The quartiles of ten-year increments mix real tree-to-tree
            # differences with measurement noise. Keep them as the range, but
            # not so wide that a negative quartile reads as "no growth".
            return {'rate': round(mid, 4),
                    'slow': round(clip(max(lo, 0.5 * mid)), 4),
                    'fast': round(clip(min(max(hi, mid), 2.0 * mid)), 4),
                    'n': len(values), 'source': source}

        self.overall = summarise(everything, 'all census-matched trees') if everything else \
            {'rate': 0.25, 'slow': 0.15, 'fast': 0.4, 'n': 0,
             'source': 'no census matches; nominal 0.25 in/yr'}
        for g, values in by_genus.items():
            if len(values) >= MIN_SPECIES_N:
                self.genus[g] = summarise(values, f'census-matched {g} trees')
        for sp, values in by_sp.items():
            if len(values) >= MIN_SPECIES_N:
                self.species[sp] = summarise(values, 'census-matched trees of this species')
        for sp, entry in published.items():
            if sp not in self.species:
                r = float(entry['in_per_yr'])
                self.species[sp] = {'rate': r, 'slow': round(r * (1 - PUBLISHED_SPREAD), 4),
                                    'fast': round(r * (1 + PUBLISHED_SPREAD), 4),
                                    'n': len(by_sp.get(sp, [])),
                                    'source': 'published: ' + entry['source']}
        for (sp, cls), values in by_class.items():
            if sp in self.species and len(values) >= MIN_CLASS_N \
                    and not self.species[sp]['source'].startswith('published'):
                self.classes[(sp, cls)] = clip(statistics.median(values))

    def lookup(self, sp, genus):
        if sp in self.species:
            return sp, self.species[sp]
        if genus in self.genus:
            return None, self.genus[genus]
        return None, self.overall

    def years_to_grow(self, sp, genus, d_from, d_to):
        """(typical, slow-growth, fast-growth) years to grow from d_from to d_to inches."""
        if d_to <= d_from:
            return 0.0, 0.0, 0.0
        sp_used, entry = self.lookup(sp, genus)
        typical = 0.0
        d = d_from
        while d < d_to:
            step = min(1.0, d_to - d)
            rate = self.classes.get((sp_used, size_class(d)), entry['rate']) if sp_used else entry['rate']
            typical += step / rate
            d += step
        return (typical,
                typical * entry['rate'] / entry['slow'],
                typical * entry['rate'] / entry['fast'])

    def age_range(self, sp, genus, d0, dbh):
        """(typical, oldest, youngest) years since planting for a measured diameter.

        The oldest reading assumes slow growth and a diameter read a little
        low; the youngest, fast growth and a diameter read a little high.
        """
        typical = self.years_to_grow(sp, genus, d0, dbh)[0]
        oldest = self.years_to_grow(sp, genus, d0, dbh + DBH_ERROR_IN)[1]
        youngest = self.years_to_grow(sp, genus, d0, max(d0, dbh - DBH_ERROR_IN))[2]
        return typical, oldest, youngest


# ── 3. Date ───────────────────────────────────────────────────────────────────

def estimate(t, seen, growth, d0, years_available, this_year):
    """(est, lo, hi, src, conf) for one tree, or None when nothing to go on."""
    sp, genus = t['_species'], t['_genus']

    if seen:
        first = min(seen)
        ests = []
        for y, c in seen.items():
            ests.append(y - growth.years_to_grow(sp, genus, d0, c['dbh'])[0])
        est = min(statistics.median(ests), first)
        typical, slow, fast = growth.age_range(sp, genus, d0, seen[first]['dbh'])
        lo, hi = first - slow, min(first, first - fast)

        earlier = [y for y in years_available if y < first]
        if not earlier:
            src = f'c{first}'
        else:
            prev = max(earlier)
            if hi >= prev - 2:
                # Absent last census and small enough to be new since: planted
                # between the two censuses.
                est, lo = max(est, prev + 1), max(lo, prev + 1)
                src = f'c{first}'
            else:
                src = f'c{first}m'
    else:
        dbh = t['_dbh']
        if not dbh:
            return None
        typical, slow, fast = growth.age_range(sp, genus, d0, dbh)
        measured_mid = (DBH_MEASURED_FROM + this_year) / 2
        est = measured_mid - typical
        lo, hi = DBH_MEASURED_FROM - slow, this_year - fast
        if (t.get('tree_type') == 'street' and 2015 in years_available
                and this_year - fast >= POST_2015_START - 2):
            est, lo = max(est, POST_2015_START), max(lo, POST_2015_START)
            src = 'new'
        else:
            src = 'dbh'

    hi = min(hi, this_year)
    est = min(max(est, lo), hi)
    lo, hi = min(lo, est), max(hi, est)
    return round(est), math.floor(lo), math.ceil(hi), src, CONFIDENCE[src]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    this_year = date.today().year
    with open(CENSUS_PATH) as f:
        trees = json.load(f)
    print(f'Loaded {len(trees)} trees from census.json')
    history = load_history()
    if not history:
        print('No census history — run scripts/fetch_historic_censuses.py first.')
        sys.exit(1)
    years_available = sorted(history)
    published = {}
    if os.path.exists(PUBLISHED):
        with open(PUBLISHED) as f:
            published = json.load(f).get('species', {})

    for t in trees:
        t.pop('age_est', None)
        t['_xy'] = xy(num(t.get('latitude')), num(t.get('longitude')))
        t['_dbh'] = num(t.get('tree_dbh'))
        t['_species'] = species_key(t.get('spc_latin'))
        t['_genus'] = genus_of(t.get('spc_latin'))

    # 1. Match every Forestry tree, retired ones included, so a living tree
    # can't claim the census record of the dead tree that stood beside it.
    matches = {y: match_census(trees, history[y], MATCH_RADIUS_M[y]) for y in years_available}
    sightings = []
    for ti in range(len(trees)):
        seen = {y: matches[y][ti] for y in years_available if ti in matches[y]}
        sightings.append(drop_replanted(seen))

    # 2. Calibrate from trees seen in consecutive censuses.
    increments = []
    for ti, seen in enumerate(sightings):
        ys = sorted(seen)
        for a, b in zip(ys, ys[1:]):
            if b - a == 10:
                increments.append((trees[ti]['_species'], trees[ti]['_genus'],
                                   seen[a]['dbh'], (seen[b]['dbh'] - seen[a]['dbh']) / (b - a)))
    growth = GrowthModel(increments, published)

    recent = [t['_dbh'] for t in trees
              if t.get('status') == 'Full' and t['_dbh'] and (planted_year(t) or 0) >= this_year - 1]
    d0 = statistics.median(recent) if len(recent) >= 20 else DEFAULT_PLANTING_DBH
    print(f'Planting size: {d0}" DBH (median of {len(recent)} trees planted since {this_year - 1})')

    # 3. Date the living trees with no planting date.
    counts, conf_counts, skipped = {}, {}, 0
    for ti, t in enumerate(trees):
        if t.get('status') != 'Full' or planted_year(t):
            continue
        result = estimate(t, sightings[ti], growth, d0, years_available, this_year)
        if not result:
            skipped += 1
            continue
        t['age_est'] = list(result[:4])
        counts[result[3]] = counts.get(result[3], 0) + 1
        conf_counts[result[4]] = conf_counts.get(result[4], 0) + 1

    # Checks against trees whose planting year is known (all 2015 or later).
    dated = [(ti, planted_year(t)) for ti, t in enumerate(trees) if planted_year(t)]
    late = [(ti, y) for ti, y in dated if y >= 2017]
    false_2015 = sum(1 for ti, _ in late if 2015 in sightings[ti])
    false_2005 = sum(1 for ti, _ in dated if 2005 in sightings[ti] and planted_year(trees[ti]) >= 2007)

    # Trees bounded between two censuses: how often does the diameter alone
    # put them in that window?
    window_checks = {}
    for ti, seen in enumerate(sightings):
        if not seen:
            continue
        first = min(seen)
        earlier = [y for y in years_available if y < first]
        if not earlier:
            continue
        prev = max(earlier)
        dbh_only = first - growth.years_to_grow(trees[ti]['_species'], trees[ti]['_genus'],
                                                d0, seen[first]['dbh'])[0]
        w = window_checks.setdefault(f'{prev + 1}-{first}', [0, 0])
        w[1] += 1
        if prev - 2 <= dbh_only <= first:
            w[0] += 1

    with open(CENSUS_PATH, 'w') as f:
        json.dump([{k: v for k, v in t.items() if not k.startswith('_')} for t in trees],
                  f, separators=(',', ':'))

    calib = {
        'planting_dbh_in': d0,
        'match_radius_m': {str(y): MATCH_RADIUS_M[y] for y in years_available},
        'census_trees': {str(y): len(history[y]) for y in years_available},
        'matched_forestry_trees': {str(y): len(matches[y]) for y in years_available},
        'growth_increments': len(increments),
        'estimates': {'by_source': counts, 'by_confidence': conf_counts,
                      'living_without_date_or_dbh': skipped},
        'source_codes': SOURCES,
        'checks': {
            'trees_planted_2017_or_later_matched_to_2015_census':
                f'{false_2015} of {len(late)} — these are false matches',
            'trees_planted_2007_or_later_matched_to_2005_census':
                f'{false_2005} of {len(dated)} dated trees — false matches',
            'diameter_alone_lands_in_census_window': {
                k: f'{a} of {n} ({a / n:.0%})' for k, (a, n) in window_checks.items() if n},
        },
        'growth_rates_in_per_yr': {
            'overall': growth.overall,
            'species': dict(sorted(growth.species.items())),
            'genus': dict(sorted(growth.genus.items())),
            'species_by_size_class': {f'{sp} | {cls}"+': round(r, 4)
                                      for (sp, cls), r in sorted(growth.classes.items())},
        },
    }
    with open(CALIB_PATH, 'w') as f:
        json.dump(calib, f, indent=1)

    print('\nMatches per census:', calib['matched_forestry_trees'])
    print(f'Growth increments measured: {len(increments)}; '
          f'species with own rate: {sum(1 for v in growth.species.values() if not v["source"].startswith("published"))}')
    print('Estimates by source:', counts)
    print('Estimates by confidence:', conf_counts)
    print('Checks:', json.dumps(calib['checks'], indent=1))
    print(f'\nWrote {CENSUS_PATH} and {CALIB_PATH}')


if __name__ == '__main__':
    main()
