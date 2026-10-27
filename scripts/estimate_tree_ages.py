#!/usr/bin/env python3
"""
Estimate a planting year for every living tree in data/census.json that has
no planting date, and write it back as one field:

  age_est: [best-guess year, earliest plausible, latest plausible, source]

where source is one of the SOURCES codes below (its confidence is in
CONFIDENCE). A source ending in '>' marks a trunk too big to date: the year is
then "planted before" and the earliest-year slot is null. One packed field rather than five because every visitor
downloads census.json in full on every page load (see fetch_census.py).

The planting date fields themselves (planteddate, tree_cen_date) are never
touched, so the priority tiers in index.html — which read only those — are
unaffected by any of this.

How it works
------------
1. Match: each Forestry tree is paired with the 2015 Street Tree Census tree
   at the same spot (Forestry Tree Points was seeded from that census, so
   they sit within a few metres). The 1995 and 2005 censuses can't be matched
   that way: they were recorded by street address, and every tree at an
   address was geocoded to one shared point. So a tree's 2015 address is
   looked up in those censuses instead, and paired with a tree listed there
   of the same genus whose diameter fits ten or twenty years' growth. Each
   census tree pairs with at most one Forestry tree. (Census files are in
   data/census-history/, written by fetch_historic_censuses.py.)
2. Calibrate growth: a tree matched in an older census and in 2015 shows
   how fast its trunk grew in between. Only matches with nothing to choose
   between (one tree of that genus at the address in both censuses) count, so
   the rates aren't shaped by how candidates were ranked. Their trimmed mean,
   per species and per size class, is the local growth rate. Species with too few matched trees
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

# Matching radius per census, in metres, for matching by position. Only the
# 2015 census is matched that way when addresses are available: it was mapped
# tree by tree and Forestry Tree Points was seeded from it. The 1995/2005
# radii only apply to census files saved without addresses.
MATCH_RADIUS_M = {1995: 10.0, 2005: 6.0, 2015: 3.0}

# Matching by address (1995, 2005). A listed tree must be the same genus and
# its address point no further than this from the tree today — a guard
# against two different streets normalising to the same name.
ADDRESS_MAX_M = 120.0
# A second pass tries nearby house numbers on the same side of the same
# street, for trees credited to the building next door in one census.
NEAR_HOUSE_NUMBERS = 12
# Where an address lists several trees of one genus, candidates are ranked by
# how well their diameters fit the species' growth. This rough rate is used
# for that on the first pass only; growth is then measured from the
# addresses where there was nothing to choose between (one tree of that
# genus in both censuses), and the matching re-run with those rates. Measuring
# growth from ranked matches would just hand this number back.
NOMINAL_RATE = 0.2

# A census tree can't be much fatter than the tree there now — if it is, the
# spot has been replanted. The slack covers measurement error and the fact
# that a Forestry diameter may have been recorded years ago.
def dbh_plausible(census_dbh, current_dbh):
    if not current_dbh:
        return True
    return census_dbh <= current_dbh + max(4.0, 0.35 * current_dbh)

# Growth calibration
MIN_SPECIES_N = 20      # matched trees needed to trust a species' own rate
MIN_CLASS_N   = 30      # …and to trust its rate within one size class
DBH_CLASSES   = (0, 6, 12, 18, 24, 999)   # inches
RATE_FLOOR, RATE_CEIL = 0.05, 1.5         # in/yr — clip noise, not biology

# Growth rates come from street trees, nearly all under ~30". Reading the
# age of a much bigger trunk off them extrapolates far past the data (and
# park trees, with room to grow, grow faster anyway): the first run put a
# 59" Tompkins Square sycamore at 1590. So a trunk bigger than this
# percentile of the measured trees' diameters (per species, or overall) is
# only dated as "planted before" the year a tree of that size would have been.
MAX_DBH_PERCENTILE = 95

# Census diameters were taped by volunteers and recorded in whole inches. A
# diameter within this much of planting size dates a tree only as "planted by
# then", so it is left out of the error measurement below.
DBH_ERROR_IN = 1.5

# Ranges. A tree found in two censuses can be dated from each diameter on its
# own; how far apart the two dates land is a measured error, and it barely
# grows with age (about ±7 years at 10–70 years back). Each run measures it,
# as the ERROR_QUANTILE-th percentile of one estimate's error within each
# band of years-since-planting, and adds RATE_UNCERTAINTY of those years for
# the growth rates themselves being off (the local rates run about 20% below
# the published NYC ones). The two combine as independent errors.
ERROR_QUANTILE = 80
ERROR_BANDS = (0, 20, 45, 70)          # years since planting, band starts
MIN_BAND_PAIRS = 30
RATE_UNCERTAINTY = 0.2
# A range wider than this says little, whatever the source: shown as low
# confidence (index.html's AGE_EST_LOW_IF_WIDER is the same number).
LOW_IF_WIDER_THAN = 30

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
    # Any code + '>': trunk bigger than the growth data covers; the year is
    # "planted before", and the earliest-year slot is null.
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


# Genera renamed since the older censuses were taken.
GENUS_SYNONYMS = {'sophora': 'styphnolobium'}


def genus_of(latin):
    key = species_key(latin)
    if not key:
        return None
    genus = key.split()[0]
    return GENUS_SYNONYMS.get(genus, genus)


def norm_common(name):
    return ''.join(ch for ch in (name or '').lower() if ch.isalpha())


def same_kind(f_genus, f_common, c_genus, c_common):
    if f_genus and c_genus:
        return f_genus == c_genus
    a, b = norm_common(f_common), norm_common(c_common)
    return bool(a) and a == b


# ── Addresses ─────────────────────────────────────────────────────────────────

STREET_WORDS = {
    'E': 'EAST', 'W': 'WEST', 'N': 'NORTH', 'S': 'SOUTH',
    'ST': 'STREET', 'STR': 'STREET', 'AVE': 'AVENUE', 'AV': 'AVENUE', 'AVN': 'AVENUE',
    'PL': 'PLACE', 'BLVD': 'BOULEVARD', 'DR': 'DRIVE', 'RD': 'ROAD', 'LN': 'LANE',
    'SQ': 'SQUARE', 'PKWY': 'PARKWAY', 'TER': 'TERRACE', 'CT': 'COURT', 'SL': 'SLIP',
    'BWAY': 'BROADWAY', 'HWY': 'HIGHWAY',
}
ORDINAL_WORDS = {
    'FIRST': '1', 'SECOND': '2', 'THIRD': '3', 'FOURTH': '4', 'FIFTH': '5', 'SIXTH': '6',
    'SEVENTH': '7', 'EIGHTH': '8', 'NINTH': '9', 'TENTH': '10', 'ELEVENTH': '11',
    'TWELFTH': '12', 'THIRTEENTH': '13', 'FOURTEENTH': '14',
}


# The 1995 file truncates some street names and drops 'STREET' from others
# ('ALLEN', 'AVENUE OF THE AMER', 'MAC DOUGAL'), so streets are compared on a
# compact key: no 'STREET', no spaces, cut to this many characters.
STREET_KEY_LEN = 14


def norm_address(raw):
    """'110 E. 7th St' and '110 EAST 7 STREET' → (110, 'EAST7'); None if unusable."""
    s = (raw or '').upper().replace("'", '').replace('.', ' ')
    head = s.strip().split(None, 1)
    if len(head) < 2:
        return None
    number = head[0].split('-')[0]
    digits = ''.join(ch for ch in number if ch.isdigit())
    if not digits or not number[0].isdigit():
        return None
    words = []
    for i, w in enumerate(''.join(ch if ch.isalnum() else ' ' for ch in head[1]).split()):
        if w[:-2].isdigit() and w[-2:] in ('ST', 'ND', 'RD', 'TH'):
            w = w[:-2]
        elif w in ORDINAL_WORDS:
            w = ORDINAL_WORDS[w]
        elif w == 'ST' and i == 0:
            w = 'SAINT'
        else:
            w = STREET_WORDS.get(w, w)
        words.append(w)
    key = ''.join(w for w in words if w != 'STREET')[:STREET_KEY_LEN]
    return (int(digits), key) if key else None


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
            addr = norm_address(r[idx['address']]) if 'address' in idx else None
            rows.append({'lat': r[idx['lat']], 'lng': r[idx['lng']], 'dbh': float(r[idx['dbh']]),
                         'genus': genus_of(latin), 'common': common, 'addr': addr})
        with_genus = sum(1 for r in rows if r['genus'])
        with_addr = sum(1 for r in rows if r['addr'])
        print(f'  {year} census: {len(rows)} living trees '
              f'({with_genus / max(1, len(rows)):.0%} with a Latin name, '
              f'{with_addr / max(1, len(rows)):.0%} with a usable address)')
        if 'address' in idx:
            unusable = [r[idx['address']] for r, row in zip(data['trees'], rows) if not row['addr']]
            if unusable:
                print(f'    unusable addresses, e.g. {unusable[:5]}')
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


def match_by_address(trees, matched_2015, census, year, rate_of):
    """{tree index: census row} for a census recorded by address.

    Only trees already matched to the 2015 census have an address to look up.
    rate_of(tree index) is the growth (in/yr) used to rank candidates.
    Returns the matches, how many each pass found, and the trees whose match
    was the only possible one (see NOMINAL_RATE).
    """
    by_addr, by_street, old_count, new_count = {}, {}, {}, {}
    for ci, c in enumerate(census):
        if c['addr']:
            by_addr.setdefault(c['addr'], []).append(ci)
            num_, street = c['addr']
            by_street.setdefault((street, num_ % 2), []).append(ci)
            old_count[(c['addr'], c['genus'])] = old_count.get((c['addr'], c['genus']), 0) + 1
    for ti, c15 in matched_2015.items():
        key = (c15.get('addr'), trees[ti]['_genus'])
        new_count[key] = new_count.get(key, 0) + 1
    pts = [xy(c['lat'], c['lng']) for c in census]
    years_back = 2015 - year

    def candidates(ti, c15, cis, house_gap):
        t = trees[ti]
        for ci in cis:
            c = census[ci]
            if not same_kind(t['_genus'], t.get('spc_common'), c['genus'], c['common']):
                continue
            # Compared with the 2015 census diameter, measured at a known date.
            if c['dbh'] > c15['dbh'] + max(3.0, 0.3 * c15['dbh']):
                continue
            if math.hypot(pts[ci][0] - t['_xy'][0], pts[ci][1] - t['_xy'][1]) > ADDRESS_MAX_M:
                continue
            fit = abs((c15['dbh'] - c['dbh']) - rate_of(ti) * years_back)
            yield (house_gap(c), fit, ti, ci)

    out, used_c, passes, unique = {}, set(), [], set()
    for near in (False, True):
        pairs = []
        for ti, c15 in matched_2015.items():
            if ti in out or not c15.get('addr'):
                continue
            num_, street = c15['addr']
            if not near:
                pairs.extend(candidates(ti, c15, by_addr.get(c15['addr'], ()), lambda c: 0))
            else:
                pairs.extend(candidates(
                    ti, c15, by_street.get((street, num_ % 2), ()),
                    lambda c, n=num_: abs(c['addr'][0] - n) if abs(c['addr'][0] - n) <= NEAR_HOUSE_NUMBERS else None))
        pairs = [p for p in pairs if p[0] is not None]
        pairs.sort()
        found = 0
        for gap, fit, ti, ci in pairs:
            if ti in out or ci in used_c:
                continue
            out[ti] = census[ci]
            used_c.add(ci)
            found += 1
            key = (census[ci]['addr'], trees[ti]['_genus'])
            if not near and key[1] and old_count.get(key) == 1 and new_count.get(key) == 1:
                unique.add(ti)
        passes.append(found)
    return out, {'same_address': passes[0], 'nearby_house_number': passes[1]}, unique


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


def trimmed_mean(values, cut=0.1):
    """Mean without the top and bottom tenth. Whole-inch diameters over ten
    years make every increment a multiple of 0.1 in/yr, so a median can only
    land on 0.1, 0.2, 0.3…; this keeps the resolution and still drops the
    worst mismatches."""
    v = sorted(values)
    k = int(len(v) * cut)
    v = v[k:len(v) - k] or v
    return sum(v) / len(v)


def quartiles(values):
    if len(values) < 4:
        m = statistics.median(values)
        return m, m, m
    q = statistics.quantiles(values, n=4)
    return q[0], statistics.median(values), q[2]


class GrowthModel:
    """Trunk growth in inches/year by species and size class."""

    def __init__(self, increments, published):
        # increments: list of (species_key, genus, start_dbh, end_dbh, inches_per_year)
        self.species, self.genus, self.classes = {}, {}, {}
        by_sp, by_genus, by_class, everything = {}, {}, {}, []
        ends_sp, ends_all = {}, []
        for sp, genus, start, end, rate in increments:
            everything.append(rate)
            ends_all.append(end)
            if sp:
                by_sp.setdefault(sp, []).append(rate)
                by_class.setdefault((sp, size_class(start)), []).append(rate)
                ends_sp.setdefault(sp, []).append(end)
            if genus:
                by_genus.setdefault(genus, []).append(rate)

        # The largest trunks the growth data actually covers. Ages are not
        # extrapolated past these — see MAX_DBH_PERCENTILE.
        def p95(values):
            return round(statistics.quantiles(values, n=100)[MAX_DBH_PERCENTILE - 1], 1)
        self.overall_max_dbh = p95(ends_all) if len(ends_all) >= MIN_SPECIES_N else None
        self.max_dbh = {sp: p95(v) for sp, v in ends_sp.items() if len(v) >= MIN_SPECIES_N}

        def summarise(values, source):
            lo, _, hi = quartiles(values)
            mid = clip(trimmed_mean(values))
            return {'rate': round(mid, 4), 'quartiles': [round(lo, 4), round(hi, 4)],
                    'n': len(values), 'source': source}

        self.overall = summarise(everything, 'all census-matched trees') if everything else \
            {'rate': 0.25, 'n': 0, 'source': 'no census matches; nominal 0.25 in/yr'}
        for g, values in by_genus.items():
            if len(values) >= MIN_SPECIES_N:
                self.genus[g] = summarise(values, f'census-matched {g} trees')
        for sp, values in by_sp.items():
            if len(values) >= MIN_SPECIES_N:
                self.species[sp] = summarise(values, 'census-matched trees of this species')
        for sp, entry in published.items():
            if sp not in self.species:
                r = float(entry['in_per_yr'])
                self.species[sp] = {'rate': r, 'n': len(by_sp.get(sp, [])),
                                    'source': 'published: ' + entry['source']}
        for (sp, cls), values in by_class.items():
            if sp in self.species and len(values) >= MIN_CLASS_N \
                    and not self.species[sp]['source'].startswith('published'):
                self.classes[(sp, cls)] = clip(trimmed_mean(values))

    def dbh_limit(self, sp):
        """Largest diameter this species' age can be read from, or None."""
        return self.max_dbh.get(sp, self.overall_max_dbh)

    def lookup(self, sp, genus):
        if sp in self.species:
            return sp, self.species[sp]
        if genus in self.genus:
            return None, self.genus[genus]
        return None, self.overall

    def years_to_grow(self, sp, genus, d_from, d_to):
        """Years to grow from d_from to d_to inches at the measured rates."""
        if d_to <= d_from:
            return 0.0
        sp_used, entry = self.lookup(sp, genus)
        typical = 0.0
        d = d_from
        while d < d_to:
            step = min(1.0, d_to - d)
            rate = self.classes.get((sp_used, size_class(d)), entry['rate']) if sp_used else entry['rate']
            typical += step / rate
            d += step
        return typical


class ErrorModel:
    """How far either side of an estimate its range reaches, by years since
    planting. See ERROR_QUANTILE."""

    def __init__(self, pairs):
        # pairs: (one estimate's error in years, years since planting)
        def pct(values):
            return statistics.quantiles(values, n=100)[ERROR_QUANTILE - 1]
        self.overall = round(pct([e for e, _ in pairs]), 1) if len(pairs) >= MIN_BAND_PAIRS else 10.0
        self.bands = {}
        for lo, hi in zip(ERROR_BANDS, ERROR_BANDS[1:] + (float('inf'),)):
            values = [e for e, years in pairs if lo <= years < hi]
            self.bands[lo] = round(pct(values), 1) if len(values) >= MIN_BAND_PAIRS else self.overall

    def half_width(self, years):
        band = max(lo for lo in ERROR_BANDS if lo <= max(0.0, years))
        return math.hypot(self.bands[band], RATE_UNCERTAINTY * years)


# ── 3. Date ───────────────────────────────────────────────────────────────────

def estimate(t, seen, growth, spread, d0, years_available, this_year):
    """(est, lo, hi, src, conf) for one tree, or None when nothing to go on."""
    sp, genus = t['_species'], t['_genus']
    limit = growth.dbh_limit(sp)

    def planted_before(measured_year, dbh):
        """For a trunk bigger than any the growth data covers: only that it
        was planted before a tree of the limiting size would have been."""
        before = round(measured_year - growth.years_to_grow(sp, genus, d0, limit))
        return before, None, before

    if seen:
        first = min(seen)
        if limit and seen[first]['dbh'] > limit:
            src = f'c{first}'
            return (*planted_before(first, seen[first]['dbh']), src + '>', CONFIDENCE[src])
        ests = [y - growth.years_to_grow(sp, genus, d0, c['dbh']) for y, c in seen.items()]
        est = min(statistics.median(ests), first)
        half = spread.half_width(first - est)
        lo, hi = est - half, min(first, est + half)

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
        if limit and dbh > limit:
            # The diameter could have been recorded any time up to now.
            return (*planted_before(this_year, dbh), 'dbh>', CONFIDENCE['dbh'])
        years = growth.years_to_grow(sp, genus, d0, dbh)
        half = spread.half_width(years)
        est = (DBH_MEASURED_FROM + this_year) / 2 - years
        lo, hi = DBH_MEASURED_FROM - years - half, this_year - years + half
        if (t.get('tree_type') == 'street' and 2015 in years_available
                and hi >= POST_2015_START - 2):
            est, lo = max(est, POST_2015_START), max(lo, POST_2015_START)
            src = 'new'
        else:
            src = 'dbh'

    # The best guess comes from every census a tree is in, the range from the
    # earliest; widen the range to take the guess in rather than move it.
    est = min(est, this_year)
    lo, hi = math.floor(min(lo, est)), math.ceil(max(min(hi, this_year), est))
    conf = CONFIDENCE[src] if hi - lo <= LOW_IF_WIDER_THAN else 'low'
    return round(est), lo, hi, src, conf


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
    # 2015 by position; the older censuses by the 2015 address where the
    # files carry addresses, by position otherwise.
    def match_all(rate_of):
        matches, method, unique = {}, {}, {}
        if 2015 in history:
            matches[2015] = match_census(trees, history[2015], MATCH_RADIUS_M[2015])
            method['2015'] = 'position'
        for y in years_available:
            if y == 2015:
                continue
            if 2015 in matches and any(c['addr'] for c in history[y]) \
                    and any(c['addr'] for c in history[2015]):
                matches[y], passes, unique[y] = match_by_address(
                    trees, matches[2015], history[y], y, rate_of)
                method[str(y)] = {'address': passes, 'unambiguous': len(unique[y])}
            else:
                matches[y] = match_census(trees, history[y], MATCH_RADIUS_M[y])
                method[str(y)] = 'position'
        sightings = []
        for ti in range(len(trees)):
            seen = {y: matches[y][ti] for y in years_available if ti in matches[y]}
            sightings.append(drop_replanted(seen))
        return matches, method, unique, sightings

    matches, match_method, unique, sightings = match_all(lambda ti: NOMINAL_RATE)

    # 2. Calibrate growth. With addresses: from the unambiguous matches, over
    # each tree's longest span to its 2015 diameter. Without: from every pair
    # of consecutive sightings.
    increments = []
    for ti, seen in enumerate(sightings):
        if unique:
            ys = [y for y in sorted(seen) if ti in unique.get(y, ())]
            if ys and 2015 in seen:
                y = ys[0]
                increments.append((trees[ti]['_species'], trees[ti]['_genus'],
                                   seen[y]['dbh'], seen[2015]['dbh'],
                                   (seen[2015]['dbh'] - seen[y]['dbh']) / (2015 - y)))
            continue
        ys = sorted(seen)
        for a, b in zip(ys, ys[1:]):
            if b - a == 10:
                increments.append((trees[ti]['_species'], trees[ti]['_genus'],
                                   seen[a]['dbh'], seen[b]['dbh'],
                                   (seen[b]['dbh'] - seen[a]['dbh']) / (b - a)))
    growth = GrowthModel(increments, published)

    if unique:
        # Re-match the ambiguous addresses using the measured rates.
        matches, match_method, _, sightings = match_all(
            lambda ti: growth.lookup(trees[ti]['_species'], trees[ti]['_genus'])[1]['rate'])

    recent = [t['_dbh'] for t in trees
              if t.get('status') == 'Full' and t['_dbh'] and (planted_year(t) or 0) >= this_year - 1]
    d0 = statistics.median(recent) if len(recent) >= 20 else DEFAULT_PLANTING_DBH
    print(f'Planting size: {d0}" DBH (median of {len(recent)} trees planted since {this_year - 1})')

    # Trees in two censuses can be dated from each diameter separately; how
    # far apart those two dates land is a direct read on the method's error,
    # and sets the ranges (see ERROR_QUANTILE).
    agreement, pairs = {}, []
    for ti, seen in enumerate(sightings):
        sp, genus = trees[ti]['_species'], trees[ti]['_genus']
        ys = sorted(seen)
        for a, b in zip(ys, ys[1:]):
            if seen[a]['dbh'] <= d0 + DBH_ERROR_IN:
                continue   # still at planting size: its date is just "by then"
            limit = growth.dbh_limit(sp)
            if limit and seen[b]['dbh'] > limit:
                continue   # too big to date (see MAX_DBH_PERCENTILE)
            years_a = growth.years_to_grow(sp, genus, d0, seen[a]['dbh'])
            years_b = growth.years_to_grow(sp, genus, d0, seen[b]['dbh'])
            apart = abs((a - years_a) - (b - years_b))
            agreement.setdefault(f'{a} vs {b}', []).append(apart)
            # Two independent estimates differ by about sqrt(2) times one's error.
            pairs.append((apart / math.sqrt(2), (years_a + years_b) / 2))
    spread = ErrorModel(pairs)

    # 3. Date the living trees with no planting date.
    counts, conf_counts, skipped = {}, {}, 0
    for ti, t in enumerate(trees):
        if t.get('status') != 'Full' or planted_year(t):
            continue
        result = estimate(t, sightings[ti], growth, spread, d0, years_available, this_year)
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
                                                d0, seen[first]['dbh'])
        w = window_checks.setdefault(f'{prev + 1}-{first}', [0, 0])
        w[1] += 1
        if prev - 2 <= dbh_only <= first:
            w[0] += 1

    with open(CENSUS_PATH, 'w') as f:
        json.dump([{k: v for k, v in t.items() if not k.startswith('_')} for t in trees],
                  f, separators=(',', ':'))

    calib = {
        'planting_dbh_in': d0,
        'match_method': match_method,
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
            'first_seen_trees_whose_size_fits_planting_since_previous_census': {
                k: f'{a} of {n} ({a / n:.0%}); the rest are labelled c…m'
                for k, (a, n) in window_checks.items() if n},
            'years_apart_when_dated_from_each_of_two_censuses': {
                k: {'trees': len(v), 'median': round(statistics.median(v), 1),
                    'p80': round(statistics.quantiles(v, n=5)[3], 1) if len(v) >= 5 else None}
                for k, v in sorted(agreement.items())},
        },
        'ranges': {
            'covers': f'about {ERROR_QUANTILE}% of trees, by the cross-census error',
            'one_estimate_error_years_by_years_since_planting': {
                f'{lo}+': v for lo, v in spread.bands.items()},
            'plus_share_of_years_for_growth_rate_error': RATE_UNCERTAINTY,
            'shown_as_low_confidence_when_wider_than_years': LOW_IF_WIDER_THAN,
        },
        'growth_rates_in_per_yr': {
            'overall': growth.overall,
            'species': dict(sorted(growth.species.items())),
            'genus': dict(sorted(growth.genus.items())),
            'largest_datable_dbh_in': {'overall': growth.overall_max_dbh,
                                       **dict(sorted(growth.max_dbh.items()))},
            'species_by_size_class': {f'{sp} | {cls}"+': round(r, 4)
                                      for (sp, cls), r in sorted(growth.classes.items())},
        },
    }
    with open(CALIB_PATH, 'w') as f:
        json.dump(calib, f, indent=1)

    print('\nMatches per census:', calib['matched_forestry_trees'], match_method)
    print(f'Growth increments measured: {len(increments)}; '
          f'species with own rate: {sum(1 for v in growth.species.values() if not v["source"].startswith("published"))}')
    print('Estimates by source:', counts)
    print('Estimates by confidence:', conf_counts)
    print('Checks:', json.dumps(calib['checks'], indent=1))
    print(f'\nWrote {CENSUS_PATH} and {CALIB_PATH}')


if __name__ == '__main__':
    main()
