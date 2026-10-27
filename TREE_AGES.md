# Estimated Planting Years

Forestry Tree Points records a planting date only for trees planted since
about 2015. About 16,000 of the ~18,600 trees in `data/census.json` have none.
For the living ones, `scripts/estimate_tree_ages.py` adds an estimate:

```
"age_est": [1984, 1971, 1990, "c1995"]
            best   earliest latest  source
```

The tree popup shows it as **Planted (est.)**, for example `~1984 (1971–1990) · medium`.
Hover over it to see what the estimate is based on.

The estimate is for display only. Priority tiers, the planting-year filter
and the stats read only the real planting date (`planteddate` / `tree_cen_date`).

## Data used

| Source | What it gives |
|---|---|
| 1995 Street Tree Census, NYC Open Data `kyad-zm4j` | Trees standing in 1995, with trunk diameter (DBH) |
| 2005 Street Tree Census, NYC Open Data `29bw-z7pj` | Same for 2005 |
| 2015 Street Tree Census, NYC Open Data `uvpi-gqnh` | Same for 2015 |
| Forestry Tree Points, NYC Open Data `hn5i-inap` (`census.json`) | Today's trees: location, species, DBH, and planting date where recorded |
| `data/growth-rates-published.json` | Published growth rates, used only as a fallback (see below) |

`scripts/fetch_historic_censuses.py` saves the CB3 part of each census in
`data/census-history/`. The censuses never change, so this happens once.

The censuses cover **street trees only**. Park trees can only be dated from
their current size.

## Method

1. **Match.** Each Forestry tree is paired with the census tree at the same
   spot in each census. To count as a match, the census tree must:
   - be the nearest one within 3 m (2015), 6 m (2005) or 10 m (1995). The 1995
     locations were geocoded from street addresses, so they are less exact.
   - be the same genus.
   - not have been much fatter then than the tree is now. A much fatter tree
     means the spot was replanted.

   Each census tree can be paired with only one Forestry tree.
2. **Measure growth locally.** A tree matched in two censuses ten years apart
   shows how fast its trunk grew. The median of those measurements, by species
   and by trunk-size class, is the growth rate. Species with fewer than 20
   matched trees use, in order:
   - the published rate in `growth-rates-published.json`
   - the genus's local rate
   - the rate across all trees
3. **Date.** The earliest census a tree appears in proves it was planted by
   then. Its diameter in that census, grown back down to planting size (about
   3", measured from recent plantings), says how long before. A tree missing
   from the census before that was most likely planted between the two.

## Source codes and confidence

| Code | Meaning | Confidence |
|---|---|---|
| `c2005` / `c2015` | First seen in that census and not in the one before, so planted between them | high |
| `c1995` | In the 1995 census; dated back from its 1995 diameter | medium |
| `c2005m` / `c2015m` | First seen in that census, but too big to be new, so probably missed in the earlier one | medium |
| `new` | Street tree in no census and still small, so likely planted after 2015 | low |
| `dbh` | Current diameter and growth rate only (mostly park trees) | low |

## Caveats

- **The current diameter has no date.** Trees planted in 2015 still show a
  median DBH of 3" in Forestry Tree Points, so diameters are often not
  re-measured after planting. Estimates from current size alone (`dbh`, `new`)
  assume the diameter was measured some time between 2015 and now, which is
  why their ranges are wide.
- **Growth is not linear.** Rates are measured per trunk-size class where
  there is enough data. Dating a big tree back from its 1995 size still means
  extrapolating, so `c1995` ranges are wide.
- **Census diameters are approximate.** Volunteers recorded them in whole
  inches, so ranges allow ±1.5".
- **Matches can be wrong.** `data/tree-age-calibration.json` reports how
  often trees with a known recent planting date were wrongly matched to an
  older census. It also reports how often a tree's diameter alone puts it
  inside the census window it was found in, and every growth rate used, with
  its sample size and source.

## Running it

Both scripts run in GitHub Actions, because NYC Open Data must be reachable.

- **Estimate Tree Ages** workflow: fetches the census history if it isn't
  saved yet, runs the estimate and commits the results. It runs on its own
  when either script changes, or manually from the Actions tab.
- **Update Tree Census Data** (weekly) and **Sync Census Data** (monthly):
  these rewrite `census.json`, then re-run the estimate from the saved history.

To run it locally once `data/census-history/` exists (no network needed):

```bash
python3 scripts/estimate_tree_ages.py
```
