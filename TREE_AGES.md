# Estimated Planting Years

Forestry Tree Points records a planting date only for trees planted since
about 2015. About 11,700 of the living trees in `data/census.json` have none.
`scripts/estimate_tree_ages.py` adds an estimate for each of them:

```
"age_est": [1984, 1971, 1990, "c1995"]
            best   earliest latest  source
```

The tree popup shows it as **Planted (est.)**, for example `~1984 (1971–1990) · medium`.
A trunk too big to date shows as `before 1958 · low` instead. Hover over the
estimate to see what it is based on.

The estimate is for display only. Priority tiers, the planting-year filter
and the stats read only the real planting date (`planteddate` / `tree_cen_date`).

## Data used

| Source | What it gives |
|---|---|
| 1995 Street Tree Census, NYC Open Data `kyad-zm4j` | Trees listed by street address in 1995, with trunk diameter (DBH) |
| 2005 Street Tree Census, NYC Open Data `29bw-z7pj` | Same for 2005 |
| 2015 Street Tree Census, NYC Open Data `uvpi-gqnh` | Trees mapped one by one in 2015, with DBH and address |
| Forestry Tree Points, NYC Open Data `hn5i-inap` (`census.json`) | Today's trees: location, species, DBH, and planting date where recorded |
| `data/growth-rates-published.json` | Published growth rates, used only as a fallback (see below) |

`scripts/fetch_historic_censuses.py` saves the CB3 part of each census in
`data/census-history/`. The censuses never change, so this happens once.

The censuses cover **street trees only**. Park trees can only be dated from
their current size.

## Method

1. **Match to 2015 by position.** Forestry Tree Points was seeded from the
   2015 census, so 6,821 of today's trees sit within 3 m of a 2015 census tree
   of the same genus.
2. **Match to 1995 and 2005 by address.** Those censuses recorded trees by
   street address, and every tree at one address was geocoded to the same
   point (up to about 25 trees share one), so their coordinates can't tell the
   trees apart. Instead, a tree's 2015 address is looked up in the older
   census. It is paired with a tree listed at that address, or at a house
   number up to 12 away on the same side of the street. The pair must be the
   same genus, with a diameter that fits the years of growth in between.

   Street names are compared loosely, because the 1995 file truncates some
   (`ALLEN`, `AVENUE OF THE AMER`). *Sophora* counts as *Styphnolobium*, its
   current name.

   Matches found: 2,069 trees in 1995 and 2,739 in 2005.
3. **Measure growth locally.** Growth is measured only where there was nothing
   to choose between, meaning one tree of that genus at the address in both
   censuses: 1,316 trees. Each one gives growth per year from its earliest
   census to 2015. Rates are the 10%-trimmed mean by species and by trunk-size
   class. Species need 20 trees for their own rate, and a size class needs 30.
   Species below that use, in order:
   - the published rate
   - their genus
   - all trees, at 0.24 in/yr

   The ambiguous addresses are then re-matched using these rates.
4. **Date.**
   - **Found in a census:** the earliest census a tree appears in proves it
     was planted by then. Its diameter then, grown back down to planting size
     (3", the median of recent plantings), says roughly how long before.
   - **Missing from the census before:** if the tree is small enough to be
     new, it was planted between the two censuses.
   - **In no census:** dated from its current diameter alone.

## Measured growth rates (in/yr of trunk diameter)

| Species | Rate | Trees | Published figure |
|---|---|---|---|
| Japanese zelkova | 0.34 | 34 | |
| Pin oak | 0.32 | 67 | |
| Japanese pagoda tree | 0.29 | 88 | |
| Honeylocust | 0.29 | 287 | 0.36 (NYC study) |
| Callery pear | 0.29 | 217 | |
| Green ash | 0.25 | 21 | |
| Littleleaf linden | 0.18 | 88 | 0.33 (growth-factor table) |
| Ginkgo | 0.16 | 226 | |
| London planetree | 0.13 | 165 | 0.16 (NYC study) |

The full table, with size-class rates and sources, is in
`data/tree-age-calibration.json`.

## Ranges

Each range is meant to hold the true planting year for about 4 in 5 trees.
Its width comes from two measured numbers:

- **How far the estimates scatter.** A tree found in two censuses can be
  dated from each diameter on its own, so the two dates show the error of one
  estimate. That error barely grows with age: about ±7 years for trees
  planted up to 70 years before the census, and ±11 for older ones.
- **How far the growth rates could be off.** Measured rates run about 20%
  below the published NYC ones, so the range adds ±20% of the years since
  planting.

The two are combined as independent errors and measured again on every run
(`ranges` in `data/tree-age-calibration.json`). Typical widths:
- a tree boxed in between two censuses: 8 years
- a tree in the 1995 census: 16 years
- a tree dated from current size only: 30 years

Any range wider than 30 years is shown as low confidence, whatever it is
based on.

## Source codes and confidence

Confidence below is for ranges up to 30 years wide; wider ones are low.

| Code | Meaning | Confidence | Trees |
|---|---|---|---|
| `c2005` / `c2015` | First seen in that census and not in the one before, so planted between them | high | 2,563 |
| `c1995` | In the 1995 census; dated back from its 1995 diameter | medium | 1,607 |
| `c2005m` / `c2015m` | First seen in that census, but too big to be new, so probably missed in the earlier one | medium | 1,104 |
| `new` | Street tree in no census and still small, so likely planted after 2015 | low | 1,273 |
| `dbh` | Current diameter and growth rate only (mostly park trees) | low | 3,940 |
| any code + `>` | Trunk bigger than the growth data covers: "planted before" the year shown | as its code | 1,228 |

## How accurate is it?

- **Two independent dates disagree by several years.** A tree found in two
  censuses can be dated from each diameter separately. Those two dates differ
  by a median of 4–7 years, and 80% are within 10–20 years. So a single
  estimate is typically off by a few years, and by much more for old trees.
  The `c2005`/`c2015` ones are boxed in by two censuses and are the most
  reliable.
- **False matches are rare.** Of 2,241 trees with a recorded planting date of
  2017 or later, 17 were wrongly matched to a 2015 census tree.
- **The rates run below the published figures.** Measured rates for
  honeylocust and London planetree are about 20% below the published NYC
  figures, which would make estimates somewhat too old.
- **Growth looks slower after 2005.** For the 400 trees matched unambiguously
  in all three censuses, growth was 0.27 in/yr over 1995→2005 but 0.18 in/yr
  over 2005→2015. Either the trees slowed down or the 2005 diameters run high,
  and the data can't tell which.
- **Big trunks aren't extrapolated.** Rates come from street trees, nearly all
  under about 20". A trunk bigger than the 95th percentile of the measured
  trees (per species, or 19" overall) only gets "planted before". Before this
  limit was added, a 59" Tompkins Square sycamore was dated to 1590.
- **The current diameter has no date.** Trees planted in 2015 still show a
  median DBH of 3" in Forestry Tree Points, so diameters are often not
  re-measured. Dating from current size alone (`dbh`, `new`) assumes the
  diameter was taken some time between 2015 and now, which widens those ranges.

## Running it

Both scripts run in GitHub Actions, because NYC Open Data must be reachable.

- **Estimate Tree Ages** workflow: fetches any census file that is missing or
  saved in an older format, runs the estimate and commits the results. It runs
  on its own when either script changes, or manually from the Actions tab
  (tick *refetch* to download the censuses again). It only writes
  `census.json` on the default branch. On any other branch it commits the
  census history and calibration report only, so a branch never carries its
  own copy of `census.json` and never conflicts with the weekly update.
- **Update Tree Census Data** (weekly) and **Sync Census Data** (monthly):
  these rewrite `census.json`, then re-run the estimate from the saved history.

To run it locally (no network needed):

```bash
python3 scripts/estimate_tree_ages.py
```
