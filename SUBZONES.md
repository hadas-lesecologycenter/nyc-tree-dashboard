# CB3 Sub-Zones

**Status: zones 1 and 2 done, zone 3 to come.** Eighteen sub-zones cover the
East Village and the Lower East Side, E 14th St down to Grand St — all 3,860 of
those trees sit in exactly one sub-zone, so the sub-zone totals add up to the
zone totals the dashboard reports. `data/subzones.geojson` holds only what has
been defined, so south of Grand St shows no sub-zone yet. The 28 mid-block
sub-zones this replaces are in the git history.

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
| **2A** | 2 | Chrystie St to Eldridge St, Houston to Delancey | Houston to Rivington St · Chrystie to Eldridge St | 16 | 179 |
| **2B** | 2 | Allen St to Essex St, Houston to Delancey | Houston to Rivington St · Allen to Essex St | 22 | 178 |
| **2C** | 2 | Norfolk St to Clinton St, Houston to Delancey | Houston to Rivington St · Norfolk to Clinton St | 18 | 174 |
| **2D** | 2 | Attorney St to the East River, Houston to Delancey | Houston to Rivington St · Attorney to Mangin St | 29 | 265 |
| **2E** | 2 | Chrystie St to Essex St, Delancey to Grand | Delancey to Grand St · Chrystie to Essex St | 33 | 207 |
| **2F** | 2 | Norfolk St to the East River, Delancey to Grand | Delancey to Grand St · Norfolk to Mangin St | 41 | 260 |

1E is the small one because Tompkins Square Park fills most of Ave A to Ave B
between E 7th and E 10th, and park trees are not street trees.

**Zone 2 is cut differently from zone 1, because it is shaped differently.**
Delancey St is the one street here anybody navigates by and it splits the zone
800 trees to 463, so the north band takes four sub-zones and the south two —
forcing zone 1's three columns onto both would have produced one sub-zone of
about 100 and another of 400. The column lines are Eldridge, Essex and Clinton,
the wide named streets a crew would recognise, and Essex is shared by both
bands so it runs unbroken through the zone. All six land between 174 and 265
trees, inside the range zone 1 settled at.

Zone 2's blocks are shorter — its avenues are 70–80 m apart against the East
Village's 215–230 m — so a sub-zone there holds more segments of fewer trees
each: 2F is 41 segments averaging 6 trees, where 1A is 24 averaging 11. That is
the street pattern, not the division.

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

Every segment carries a **stable identifier** — `1A-03` — so a block can be
assigned, radioed and reported by name. Within a sub-zone they are numbered
streets first, north to south, then avenues west to east. The numbering is by
rank, not by any fitted value, so re-running the fit cannot renumber a crew's
assignment under them. `data/subzones.csv` carries a `segmentId` on every tree,
so "which trees are in 1A-03" is a lookup rather than a guess.

Two things make the segmentation legible rather than merely present:

* **A segment is drawn as its trees.** The layer marks the trees themselves, in
  the segment's colour, and nothing else — the shaded area *is* the set of trees
  in the segment because there is no shaded area, only the trees. Two shapes
  were tried before this and both read as a box sitting on the street rather
  than as the work: a thick bar along the centreline, then a corridor polygon
  wide enough to enclose both sidewalk rows. The trees group themselves anyway —
  a block's trees stand in two rows with nothing in the intersection at either
  end, so the gaps that make the segmentation countable are already in the data.
* **Colour carries how many trees are on the block**, on a single-hue ramp from
  pale (1–4) to navy (30+), with a legend under the layer's checkbox. Sub-zone
  identity is already on the map as the sub-zone polygon, and twelve sub-zones
  is well past what colour can distinguish, so hue is spent on the one thing
  nothing else shows.

Drawing the trees also removes a class of failure: there is no span to trim and
no boundary to clip against, so no segment can come out undrawable. All 348 are
drawn by construction, and the marks on the map are exactly the trees that
carry a `segmentId`.

Zone 2 leaves more trees off a segment than zone 1 — 256 of 1,263 against 218
of 2,597 — because the Lower East Side has more ground with no street through
it: Baruch, Seward Park, Masaryk and Hillman. Those trees belong to a sub-zone
but to no block within it.

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
| `data/subzones.csv` | `treeId,subzoneId,segmentId,zone,latitude,longitude,species` |
| `data/subzone-segments.geojson` | One MultiPoint per block segment — the trees it holds |
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

## Fitting a grid the frame is not aligned to

The metric frame is aligned to the East Village grid, because that is where its
one exact anchor is — CB3's own E 14th St run. Zone 2's grid sits about seven
degrees off it, and three things in the fitting quietly assumed otherwise:

* the row finder started its search from a bearing of zero, which is right in
  the East Village and 0.124 out on the Lower East Side — enough to smear a row
  across the whole search window. The bearing is now measured off the trees
  first, by scanning slopes for the one that makes the de-trended positions
  clump hardest into rows;
* the seed offsets were read off a point on each grid line rather than
  converting the line, which shears the answer by the slope times the distance
  to that point — under 10 m in the East Village, 200 m on the Lower East Side,
  where it rejected every avenue for landing too far from its own seed;
* the search window was tested against the raw coordinate while the values
  collected were de-trended, which is the same thing on an aligned grid and
  165 m adrift on this one.

Together those took zone 2 from 13 of 22 streets fitted, half its trees on no
street at all, to 18 of 22 and 80% placed. Zone 1's sub-zone totals did not
move; three trees changed segment.

## Caveat

No street-centerline dataset is reachable from this repo's build environment
(NYC Open Data, Census TIGER and the OSM endpoints are all blocked), so every
street except E 14th St and 4th Ave / the Bowery is located from the trees
standing along it. Two streets have no two-row fit and cannot be used as
boundaries: E 14th St, for the reason above, and FDR Drive. In zone 2, Willett
St / Bialystoker Pl and Columbia St have no fit either — Baruch Houses covers
most of what would be their frontage. Housing
superblocks (Tompkins Square, Baruch, Vladeck, Rutgers, Smith) have no interior
streets to detect. If real centerline data ever lands in the repo, the fitting
step is the part to replace.
