# CB3 Sub-Zones

**Status: being redrawn.** Sub-zone 1A is defined and on the map. The rest of
CB3's divisions are still to come, and `data/subzones.geojson` holds only the
sub-zones that have been defined, so most of the district shows no sub-zone
yet. The 28 mid-block sub-zones this replaces are in the git history.

## The rule

Every edge is a named street, and it runs just outside that street's kerbline:

* the boundary for a **numbered street runs immediately north of it**, so the
  street — roadway and both sidewalks — belongs to the sub-zone on the **south**
  side;
* the boundary for an **avenue runs immediately east of it**, so the avenue
  belongs to the sub-zone on the **west** side.

So a sub-zone owns its northern street and its eastern avenue and neither of
the other two, which tiles the district without ever splitting a street down
the middle. "4th Ave to 1st Ave, E 14th St to E 10th St" means E 14th down to
E 11th, both sides, and 3rd, 2nd and 1st Ave, both sides.

## The sub-zones

| ID | Zone | Bounded by | Works both sides of | Segments | Trees |
|---|---|---|---|---|---|
| **1A** | 1 | 4th Ave to 1st Ave, E 14th St to E 10th St | E 14th St to E 11th St · Bowery / 3rd Ave to 1st Ave | 24 | 259 |

## Where the lines come from

Two anchors are exact, and they are the only exact geometry in this repo.
CB3's official boundary runs down the middle of E 14th St across the top of the
district and down 4th Ave / the Bowery on its west side. A sub-zone that
reaches the edge of the district leaves that side of its window open and lets
the boundary close it, which is why 1A's northern and western edges sit on
those streets exactly.

Everything else is fitted from the tree census. Street trees stand in two rows,
one per sidewalk, and the rows are very straight — a least-squares line through
one comes back with an RMS residual of 0.1–0.5 m. Fitting each row separately
and averaging the pair gives a centreline good to well under a metre. The edge
is that centreline pushed out by half a right of way (30 ft for the numbered
side streets, 50 ft for the avenues) so it lands on the property line, and the
build checks every offset against the sidewalk rows it has to clear.

This is a different construction from the old `cb3-street-grid.json`, which fit
whole families of streets at once. That fit put E 14th St 9.5 m south of the
real street — its north sidewalk is in CB6 and missing from the data, so the
line settled on the south sidewalk instead — and E 10th St 11 m north of it,
having merged both of its sidewalk rows into one. The grid is still used, for
street names and as a starting guess for each fit.

## Files

| File | What it is |
|---|---|
| `data/subzones.geojson` | One polygon per defined sub-zone, clipped to CB3 |
| `data/subzones.csv` | `treeId,subzoneId,zone,latitude,longitude,species` |
| `data/cb3-street-lines.json` | The fitted centrelines, for inspection |
| `data/cb3-street-grid.json` | The older whole-family fit, used for names and seeds |

## Rebuilding

```
python3 scripts/build_subzones.py
```

It prints every fitted centreline with the size and straightness of the two
rows behind it, then each sub-zone with the offset of each of its four edges
and how much clearance that leaves over the street's own sidewalk row. It
checks that no tree lands in two sub-zones and that no edge either cuts into
the street it names or reaches the next street over.

To add a sub-zone, add an entry to `SUBZONES` in that script naming its four
bounding streets and re-run.

## Caveat

No street-centerline dataset is reachable from this repo's build environment
(NYC Open Data, Census TIGER and the OSM endpoints are all blocked), so every
street except E 14th St and 4th Ave / the Bowery is located from the trees
standing along it. Two streets have no two-row fit and cannot be used as
boundaries: E 14th St, for the reason above, and FDR Drive. Housing
superblocks (Tompkins Square, Baruch, Vladeck, Rutgers, Smith) have no interior
streets to detect. If real centerline data ever lands in the repo, the fitting
step is the part to replace.
