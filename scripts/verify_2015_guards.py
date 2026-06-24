#!/usr/bin/env python3
"""Verify 2015 Street Tree Census (uvpi-gqnh) tree-guard coverage for Manhattan CB3.

Diagnostic only — does NOT modify census.json. Intended to run in CI, because
NYC Open Data is not reachable from the dev sandbox. Reports the coverage
ceiling and spatial-join feasibility for attaching the 2015 census `guards`
status onto the live Forestry Tree Points (which carry no guard field).

Run: python scripts/verify_2015_guards.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
import fetch_census as fc

# CB3 filters that work against the 2015 census schema (cb_num/borocode/nta_name).
# (The forestry within_box(geometry,...) variant is omitted — the 2015 census geo
# column is `the_geom`, not `geometry`.)
CB3_FILTERS = [
    "cb_num='3' AND borocode='1'",
    "cb_num=3 AND borocode=1",
    "cb_num='3' AND boroname='Manhattan'",
    "nta_name IN ('Lower East Side', 'East Village', 'Chinatown')",
]

LIVE_CB3_TREES = 15537  # from the latest forestry sync, for context


def to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    print("Verifying 2015 census (uvpi-gqnh) tree-guard coverage for Manhattan CB3\n")

    # 1. Full schema probe
    probe = fc.fetch(fc.CENSUS_ID, {'$limit': 1})
    cols = sorted(probe[0].keys()) if probe else []
    print(f"Columns ({len(cols)}): {cols}")
    print(f"  has 'guards': {'guards' in cols} | "
          f"has lat/long: {'latitude' in cols and 'longitude' in cols}\n")

    # 2. Fetch all CB3 rows (small dataset, ~5k) via the first filter that works
    rows = used = None
    for where in CB3_FILTERS:
        try:
            r = fc.fetch(fc.CENSUS_ID, {'$where': where, '$limit': 50000})
            if isinstance(r, list) and r:
                rows, used = r, where
                break
        except Exception as e:
            print(f"  filter failed ({where[:40]}): {e}")
    if not rows:
        print("ERROR: no CB3 rows returned from any filter strategy")
        sys.exit(1)
    print(f"CB3 filter used: {used}")
    print(f"Fetched {len(rows)} rows")
    rows = fc.filter_to_cb3(rows)
    print(f"After NTA post-filter: {len(rows)} CB3 trees\n")

    # 3. Distributions
    print(f"Status distribution: {dict(Counter((r.get('status') or '(empty)') for r in rows))}")
    print(f"Guards distribution (raw): {dict(Counter((r.get('guards') or '(empty)') for r in rows))}\n")

    # 4. Guard-present (uses the same present/absent logic as the main pipeline)
    present = [r for r in rows if fc.guard_is_present(r.get('guards'))]
    pct = (100 * len(present) / len(rows)) if rows else 0
    print(f"Guard PRESENT: {len(present)} / {len(rows)} trees ({pct:.1f}%)")
    print(f"  by status: {dict(Counter((r.get('status') or '(empty)') for r in present))}")

    # 5. Spatial-join feasibility — guard rows with usable coordinates
    with_coords = [r for r in present
                   if to_float(r.get('latitude')) and to_float(r.get('longitude'))]
    print(f"  guard-present with valid lat/lng (join anchors): {len(with_coords)}\n")

    # 6. Samples + anchor bbox
    print("Sample guard-present trees:")
    for r in present[:5]:
        print(f"  tree_id={r.get('tree_id')} lat={r.get('latitude')} lng={r.get('longitude')} "
              f"guards={r.get('guards')!r} status={r.get('status')!r} spc={r.get('spc_common')!r}")
    if with_coords:
        lats = [to_float(r['latitude']) for r in with_coords]
        lngs = [to_float(r['longitude']) for r in with_coords]
        print(f"\nGuard-anchor bbox: lat [{min(lats):.4f}, {max(lats):.4f}] "
              f"lng [{min(lngs):.4f}, {max(lngs):.4f}]")

    # 7. Coverage ceiling vs the live tree set
    print("\n=== COVERAGE CEILING ===")
    print(f"At most {len(with_coords)} of the ~{LIVE_CB3_TREES:,} live CB3 trees could "
          f"receive a 2015 guard, before any spatial-match losses.")


if __name__ == '__main__':
    main()
