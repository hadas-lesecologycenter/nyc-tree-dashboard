# CB3 Sub-Zones

**Status: zone 1 done, zones 2 and 3 to come.** Four bands cover the East
Village from E 14th St to E Houston St — all 2,597 of zone 1's street trees sit
in exactly one sub-zone, so the sub-zone totals add up to the zone total the
dashboard reports. `data/subzones.geojson` holds only what has been defined, so
south of Houston St shows no sub-zone yet. The 28 mid-block sub-zones this
replaces are in the git history.

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

A sub-zone is named for the avenues it holds, so consecutive sub-zones read as
a continuous run — 4th to 1st, then A to B, then C to the river. In the build
script each side names the *line* that closes it instead, which is what makes
neighbours abut exactly: 1A's eastern edge and 1B's western edge are both
`1 AVE`, one line, so they can neither gap nor overlap.

## The sub-zones

Bands run north to south, and within a band the three sub-zones run west to
east on the same three avenue columns. A band stops immediately north of the
street it is named for, so that street opens the band below: E 10th St closes
1A–1C by bounding them and then belongs to 1D–1F.

| ID | Zone | Named | Works both sides of | Segments | Trees |
|---|---|---|---|---|---|
| **1A** | 1 | 4th Ave to 1st Ave, E 14th St to E 10th St | E 14th St to E 11th St · Bowery / 3rd Ave to 1st Ave | 24 | 259 |
| **1B** | 1 | Ave A to Ave B, E 14th St to E 10th St | E 14th St to E 11th St · Ave A to Ave B | 16 | 250 |
| **1C** | 1 | Ave C to the East River, E 14th St to E 10th St | E 14th St to E 11th St · Ave C to Ave D | 15 | 169 |
| **1D** | 1 | 4th Ave to 1st Ave, E 10th St to E 7th St | E 10th St to E 8th St / St Marks Pl · Bowery / 3rd Ave to 1st Ave | 18 | 232 |
| **1E** | 1 | Ave A to Ave B, E 10th St to E 7th St | E 10th St to E 8th St / St Marks Pl · Ave A to Ave B | 11 | 126 |
| **1F** | 1 | Ave C to the East River, E 10th St to E 7th St | E 10th St to E 8th St / St Marks Pl · Ave C to FDR Dr | 15 | 268 |
| **1G** | 1 | 4th Ave to 1st Ave, E 7th St to E 4th St | E 7th St to E 5th St · Bowery / 3rd Ave to 1st Ave | 16 | 177 |
| **1H** | 1 | Ave A to Ave B, E 7th St to E 4th St | E 7th St to E 5th St · Ave A to Ave B | 11 | 155 |
| **1I** | 1 | Ave C to the East River, E 7th St to E 4th St | E 7th St to E 5th St · Ave C to FDR Dr | 15 | 249 |
| **1J** | 1 | 4th Ave to 1st Ave, E 4th St to E Houston St | E 4th St to E Houston St · 2nd Ave to 1st Ave | 18 | 257 |
| **1K** | 1 | Ave A to Ave B, E 4th St to E Houston St | E 4th St to E Houston St · Ave A to Ave B | 16 | 229 |
| **1L** | 1 | Ave C to the East River, E 4th St to E Houston St | E 4th St to E Houston St · Ave C to FDR Dr | 14 | 226 |

1E is the small one because Tompkins Square Park fills most of Ave A to Ave B
between E 7th and E 10th, and park trees are not street trees.

**Houston St is the one exception to the rule.** It is a zone divider, not just
a street, and it keeps its centreline: the dashboard reports per-zone totals off
that line, and pushing it north to keep the street whole would hand every tree
on its north side to zone 2 and move those totals. So 1J–1L stop down the middle
of Houston St, and it is the only street the sub-zones split — which is what the
previous scheme did too. The cost is that the line passes within a metre of
three trees on Houston's central plantings; the build reports them.

1J's contents read "2nd Ave to 1st Ave" rather than naming the Bowery, because
`BOWERY / 3 AVE` in the old grid is a single straight line standing in for two
roads that diverge by up to 170 m — it tracks 3rd Ave in the north and misses
the Bowery in the south. This affects only the wording and the segment count.
1J's western edge is CB3's own boundary, which follows the Bowery exactly.

## Block segments

A sub-zone's size is quoted in **block segments**: one street, one block long,
both sides — "E 12th St, 2nd Ave to 1st Ave". That is the unit a crew is
actually handed, so it is drawn as well as counted. The **Block Segments**
layer in the map's Program Layers panel shows all 189 of them.

Two things make the segmentation legible rather than just present:

* **Each segment stops at the cross street's property line**, so it covers the
  block *face* and the intersections are left blank. Drawn end to end they were
  one unbroken line down E 12th St and no colour told you it was four blocks of
  work; with the gaps you can count them.
* **Colour carries how many trees are on the block**, on a single-hue ramp from
  pale (1–4) to navy (30+), with a legend under the layer's checkbox. Sub-zone
  identity is already on the map as the sub-zone polygon, and twelve sub-zones
  is well past what colour can distinguish, so hue is spent on the one thing
  nothing else shows. Which segment is which comes from the geometry, the hover
  tooltip, and a count badge that appears on each segment from zoom 17 in.

Each segment sits on its own street's fitted centreline under a white casing,
so it stays legible over the basemap's roads and over a sub-zone wash.

2,379 of zone 1's 2,597 street trees sit on a segment. The other 218 stand
where there is no street line to put them on — inside housing superblocks, in
courtyards and on paths — so they belong to a sub-zone but to no segment
within it.

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
side streets, 50 ft for the avenues) so it lands on the property line.

Half a right of way is where a boundary wants to sit, but not always where it
can, because a right of way is a constant and a street's planting is not. As
far as Ave C the north side of E 10th St is an ordinary sidewalk row 5.4 m out;
east of it the Jacob Riis Houses set their frontage back and plant it 8–10 m
out, past the property line. A boundary held at 9.14 m ran straight down that
row. So each edge is nudged outward until it has clear air: the smallest offset
that keeps a metre from every tree in the column that edge crosses. The nudge
is per column, since a single offset cannot suit the whole street, which is why
the E 10th St boundary steps out by 5 m at Ave B.

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
| `data/subzone-segments.geojson` | One LineString per block segment, for the map layer |
| `data/cb3-street-lines.json` | The fitted centrelines, for inspection |
| `data/cb3-street-grid.json` | The older whole-family fit, used for names and seeds |

## Rebuilding

```
python3 scripts/build_subzones.py
```

It prints every fitted centreline with the size and straightness of the two
rows behind it, then each sub-zone with the offset of each of its four edges,
how much air that leaves either side of the line, and whether the edge had to
be nudged out past the property line to find it. It checks that no tree lands
in two sub-zones and that no edge either cuts into the street it names or
reaches the next street over.

To add a sub-zone, add an entry to `SUBZONES` in that script naming the four
lines that close it and re-run. Reuse the neighbour's line verbatim — give the
sub-zone east of 1B `'west': 'AVE B'`, the same string 1B has for `'east'` —
and the two are guaranteed to meet.

Where a right-of-way width is not certain the offset is measured instead, as
the street's own sidewalk row plus a sidewalk. Only the streets in `ROW_HALF_M`
are stated outright; that list is the place to add one if a width is known.

## Caveat

No street-centerline dataset is reachable from this repo's build environment
(NYC Open Data, Census TIGER and the OSM endpoints are all blocked), so every
street except E 14th St and 4th Ave / the Bowery is located from the trees
standing along it. Two streets have no two-row fit and cannot be used as
boundaries: E 14th St, for the reason above, and FDR Drive. Housing
superblocks (Tompkins Square, Baruch, Vladeck, Rutgers, Smith) have no interior
streets to detect. If real centerline data ever lands in the repo, the fitting
step is the part to replace.
