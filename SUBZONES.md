# CB3 Sub-Zones

**Status: all of CB3 is drawn.** Twenty-five sub-zones cover the district —
**all 5,308 CB3 street trees sit in exactly one**, none in two, none in
neither, and the per-zone totals come out at 2,597 / 1,263 / 1,448, exactly
matching the three zones the dashboard reports. The 28 mid-block sub-zones this
replaces are in the git history.

## The rule

Every edge is a named street, and it runs just outside that street's kerbline:

* the boundary for an **east-west street runs immediately north of it**, so the
  street — roadway and both sidewalks — belongs to the sub-zone on the **south**
  side;
* the boundary for a **north-south street runs immediately east of it**, so that
  street belongs to the sub-zone on the **west** side.

In the East Village those are the numbered streets and the avenues; south of
Houston they are named streets both ways, but the rule is the same.

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

Sub-zones are laid out in bands running north to south, cut into columns west
to east. A band stops immediately north of the street it is named for, so that
street opens the band below: E 10th St closes 1A–1C by bounding them and then
belongs to 1D–1F. How many columns a band takes depends on the zone — zone 1
uses three throughout, zone 2 four then two, zone 3 two and then three and two
— because the three zones are not the same size or shape.

| ID | Zone | Named | Works both sides of | Segments | Trees |
|---|---|---|---|---|---|
| **1A** | 1 | 4th Ave to 1st Ave, E 14th St to E 10th St | E 14th St to E 11th St · 4th Ave to 1st Ave | 25 | 259 |
| **1B** | 1 | Ave A to Ave B, E 14th St to E 10th St | E 14th St to E 11th St · Ave A to Ave B | 16 | 250 |
| **1C** | 1 | Ave C to the East River, E 14th St to E 10th St | E 14th St to E 11th St · Ave C to Ave D | 15 | 169 |
| **1D** | 1 | 4th Ave to 1st Ave, E 10th St to E 7th St | E 10th St to E 8th St / St Marks Pl · 4th Ave to 1st Ave | 19 | 232 |
| **1E** | 1 | Ave A to Ave B, E 10th St to E 7th St | E 10th St to E 8th St / St Marks Pl · Ave A to Ave B | 11 | 126 |
| **1F** | 1 | Ave C to the East River, E 10th St to E 7th St | E 10th St to E 8th St / St Marks Pl · Ave C to FDR Dr | 15 | 268 |
| **1G** | 1 | 4th Ave to 1st Ave, E 7th St to E 4th St | E 7th St to E 5th St · 4th Ave to 1st Ave | 19 | 177 |
| **1H** | 1 | Ave A to Ave B, E 7th St to E 4th St | E 7th St to E 5th St · Ave A to Ave B | 11 | 155 |
| **1I** | 1 | Ave C to the East River, E 7th St to E 4th St | E 7th St to E 4th St · Ave C to FDR Dr | 16 | 249 |
| **1J** | 1 | 4th Ave to 1st Ave, E 4th St to E Houston St | E 4th St to E 1st St · Bowery to 1st Ave | 19 | 257 |
| **1K** | 1 | Ave A to Ave B, E 4th St to E Houston St | E 4th St to E 1st St · Ave A to Ave B | 17 | 229 |
| **1L** | 1 | Ave C to the East River, E 4th St to E Houston St | E 4th St to E Houston St · Ave C to FDR Dr | 13 | 226 |
| **2A** | 2 | Chrystie St to Eldridge St, E Houston St to Delancey St | E Houston St to Rivington St · Chrystie St to Eldridge St | 17 | 179 |
| **2B** | 2 | Allen St to Essex St, E Houston St to Delancey St | E Houston St to Rivington St · Allen St to Essex St | 22 | 178 |
| **2C** | 2 | Norfolk St to Clinton St, E Houston St to Delancey St | E Houston St to Rivington St · Norfolk St to Clinton St | 18 | 174 |
| **2D** | 2 | Attorney St to the East River, E Houston St to Delancey St | E Houston St to Rivington St · Attorney St to Mangin St | 29 | 265 |
| **2E** | 2 | Chrystie St to Essex St, Delancey St to Grand St | Delancey St to Grand St · Bowery to Essex St | 37 | 207 |
| **2F** | 2 | Norfolk St to the East River, Delancey St to Grand St | Delancey St to Grand St · Norfolk St to Mangin St | 43 | 260 |
| **3A** | 3 | Bowery to Essex St, Grand St to Division St | Grand St to Division St · Chrystie St to Essex St | 24 | 259 |
| **3B** | 3 | Norfolk St to the East River, Grand St to Division St | Grand St to Division St · Norfolk St to FDR Dr | 29 | 182 |
| **3C** | 3 | Catherine St to Pike St, East Broadway to Monroe St | E Broadway to Monroe St · Catherine St to Pike St | 15 | 152 |
| **3D** | 3 | Rutgers St to Montgomery St, East Broadway to Monroe St | E Broadway to Madison St · Pike St to Montgomery St | 27 | 223 |
| **3E** | 3 | Gouverneur St to the East River, East Broadway to Monroe St | E Broadway to Monroe St · Montgomery St to Jackson St | 16 | 171 |
| **3F** | 3 | Catherine St to Pike St, Monroe St to the waterfront | Monroe St to South St · Catherine St to Pike St | 21 | 268 |
| **3G** | 3 | Rutgers St to the East River, Monroe St to the waterfront | Monroe St to South St · Pike St to Jackson St | 38 | 193 |

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

**Zone 3 is two street patterns, not one**, so it is divided as two. Grand St
to Division St is the tail of the Lower East Side grid; south of East Broadway,
Two Bridges turns about 35 degrees and runs on its own. They are fitted
separately and cut separately, which is why the sub-zones do not line up across
East Broadway — the streets do not either. The Chinatown strip is thin and
holds 441 trees, so it splits east-west only, on Essex St; Two Bridges holds
1,007 and takes five, three above Monroe St and two below, with Pike St shared
by both bands.

Zone 2's blocks are shorter — its avenues are 70–80 m apart against the East
Village's 215–230 m — so a sub-zone there holds more segments of fewer trees
each: 2F is 41 segments averaging 6 trees, where 1A is 24 averaging 11. That is
the street pattern, not the division.

**Three streets are exceptions to the rule, and they are the dividers.**
Houston St and Grand St carry the split between the three care zones, and they
keep their centrelines: the dashboard reports per-zone totals off those lines,
and pushing one north to keep the street whole would hand every tree on its
north side to the zone below and move those totals. East Broadway keeps its
centreline for a different reason — it is the seam between the Lower East Side
grid and Two Bridges, and has no two-row fit to offset from.

So those three are the only streets the sub-zones split, which is what the
previous scheme did too. The cost is that a divider cannot be nudged off
whatever stands on it: Houston's central plantings leave 0.20 m of air at the
tightest point and East Broadway 0.36 m. The build lists every such edge.

## The road on the western edge

The old grid holds one line called `BOWERY / 3 AVE` and gives it the East
Village avenue bearing. That bearing belongs to **3rd Ave**, which is a
Commissioners' grid avenue like 2nd and 1st and fits as cleanly as they do —
two rows 24 m apart, 216 m west of 2nd Ave, residuals of 31 cm. It does not
belong to the Bowery or to 4th Ave, which keep the old post road's alignment:
0.22 and 0.34 across this frame against the avenues' −0.006, which is why one
straight line through all three ends up as much as 250 m from the road it is
named for.

So the one line is now three. 3rd Ave keeps the fit and takes its own name.
The Bowery and 4th Ave are not fitted from trees at all — CB3's boundary
follows them exactly, and it is the better source. The western run of the
boundary is split at the bend that minimises the worse of the two residuals;
that lands on Cooper Square, where the Bowery becomes 4th Ave, and takes the
residuals from 18.7 m for one line to 6.2 m each.

Each of the three carries a **span**, the stretch of its own run where the road
it models actually exists: 3rd Ave stops at Cooper Square, the Bowery starts
there and ends at Chatham Square, 4th Ave runs from Cooper Square to E 14th St.
Without spans each line goes on claiming frontage along the others' runs, and
every block east of them is counted past three lines where there is only ever
one road. 1A, 1D and 1G now read "4th Ave to 1st Ave" and 1J reads "Bowery to
1st Ave", which is what they are.

## Block segments

A sub-zone's size is quoted in **block segments**: one street, one block long,
both sides — "E 12th St, 2nd Ave to 1st Ave". That is the unit a crew is
actually handed, so it is drawn as well as counted. The **Block Segments**
layer in the map's Program Layers panel shows all 532 of them.

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
  identity is already on the map as the sub-zone polygon, and twenty-five
  sub-zones is well past what colour can distinguish, so hue is spent on the
  one thing nothing else shows.

Drawing the trees also removes a class of failure: there is no span to trim and
no boundary to clip against, so no segment can come out undrawable. All 532 are
drawn by construction, and the marks on the map are exactly the trees that
carry a `segmentId`.

## Trees on no segment

Every tree in CB3 is in exactly one sub-zone, because a sub-zone is a polygon
and the test is whether the tree is inside it. A **segment** is a stricter
claim — it says which street the tree stands on — and 575 of the 5,308 (10.8%)
cannot be given one. They are counted in their sub-zone's total, listed in
`subzones.csv` with an empty `segmentId`, and named in the sub-zone's popup, so
a crew planning a day is told how many trees it will find off the block faces.

By zone: 2,454 of 2,597 on a segment in zone 1 (94%), 1,127 of 1,263 in zone 2
(89%), 1,152 of 1,448 in zone 3 (80%). The gradient is the housing, not the
method — Baruch, Seward Park, Masaryk, Hillman, Vladeck, Rutgers, Smith and
LaGuardia all plant their frontage on housing-authority ground well inside the
block, and the census still calls those street trees.

A tree is on a street when it stands within that street's **reach** of its
centreline, and the reach is measured rather than assumed: a row of trees is a
spike in the profile of perpendicular distances and interior scatter is a flat
background, so the outermost bin still holding a row's worth of trees is where
the frontage ends. It is measured per side, because streets are not symmetrical
— Delancey St has an ordinary 10 m row on its north side and its widened
bridge-approach side 27 m out — and it is floored at 12 m, ceilinged at 28 m,
and never allowed past 40% of the way to the next parallel street. Measuring it
rather than using a flat 12 m recovered 314 trees: 146 in Two Bridges (East
Broadway 33, South St 32, Pike St 20), 95 on the Lower East Side (E Houston 35,
Delancey 28, Chrystie 19) and 59 in Chinatown, 20 of them on Allen St, which
carries a central mall and stands its sidewalk rows 13 m out.

### Checking it against the addresses

`data/trees.csv` and `data/activities.csv` carry a street address for 430 of
CB3's street trees, which is the only independent check in the repo of which
street a tree is on. Against it, **327 (76%) are assigned exactly the street
their address names**. Of the 71 that differ, 22 stand within 30 m of that
street — corner trees, and frontage the address and the roadway disagree about,
like the ten trees addressed 122 Henry Street that stand in a row along Madison
St. 32 are on no street at all.

What is left is Two Bridges and Chinatown, where a street is not straight. A
line here has one bearing for a whole region, and Henry St bends: its fitted
line is right through the middle of its run and 6 m off at the east end, which
is still inside its reach, but Cherry St and Madison St bend further and lose
their outer stretches. Modelling a curve means giving up the affine frame that
keeps every sub-zone edge a straight line, so it is not done.

## Where the lines come from

Two anchors are exact, and they are the only exact geometry in this repo.
CB3's official boundary runs down the middle of E 14th St across the top of the
district and down 4th Ave / the Bowery on its west side. A sub-zone that
reaches the edge of the district leaves that side of its window open and lets
the boundary close it, which is why 1A's northern and western edges sit on
those streets exactly.

Everything else is fitted from the tree census. Street trees stand in two rows,
one per sidewalk, and the rows are very straight — a least-squares line through
one comes back with an RMS residual of 0.34 m in the East Village, rising to
0.82 m in Two Bridges where the rows are shorter and sparser. Fitting each row
separately and averaging the pair gives a centreline good to well under a
metre. The edge
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
in two sub-zones, and lists any edge left with less than a metre of air as well
as any that had to be nudged out past the property line to find it.

To add a sub-zone, add an entry to `SUBZONES` in that script naming the four
lines that close it and re-run. Reuse the neighbour's line verbatim — give the
sub-zone east of 1B `'west': 'AVE B'`, the same string 1B has for `'east'` —
and the two are guaranteed to meet.

Where a right-of-way width is not certain the offset is measured instead, as
the street's own sidewalk row plus a sidewalk. Only the streets in `ROW_HALF_M`
are stated outright; that list is the place to add one if a width is known.

## Fitting a grid the frame is not aligned to

The metric frame is aligned to the East Village grid, because that is where its
one exact anchor is — CB3's own E 14th St run. Nothing else in the district
runs that way: the Lower East Side sits about seven degrees off it and Two
Bridges about thirty-five. Four things in the fitting quietly assumed
otherwise:

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
  165 m adrift on the Lower East Side;
* and the bearing scan itself stopped at slope 0.40, which cannot see Two
  Bridges at 0.70. It settled for a spurious alignment scoring less than half
  as well, leaving every Two Bridges avenue unfitted and 77% of its trees on no
  street at all.

Together those took zone 2 from 13 of 22 streets fitted, with half its trees on
no street at all, to 18 of 22, and Two Bridges from 4 of 16 to 10 of 16. Zone
1's sub-zone totals did not move; three trees changed segment.

### When the seed is further off than the search is wide

A street is looked for within 30 m of where the old grid puts it, and any fit
that lands more than 25 m from that seed is thrown out as having locked onto
the wrong pair of rows. Both guards are sound and together they make one street
unfindable: E 1st St. The old grid stands it 42 m below E 2nd St where every
other East Village block is 73–83 m, and its rows are 82 m below E 2nd St —
outside the window, and rejected by the tolerance even if the window reached
them. It stayed on the wrong line, 40 m from its own trees, and 90 of zone 1's
unplaced trees were in that one band.

So a street with no fit is looked for a second time, seeded not from the old
grid but from the **gap its neighbours leave**. Streets come in a known order
and the grid file lists them in it, so the band between the nearest trusted
line either side — one fitted here, or a zone divider taken from the district
boundary — is where the street has to be if it is anywhere. The band is cut
with the bounding lines rather than with two numbers, because a divider keeps
the boundary's own bearing and its position therefore slides along the street;
cutting at a single value of it clipped 11 of E 1st St's 15 southern trees off
the end of the band. Both ends are stepped in by 15 m so the search cannot
simply re-find a neighbour's own sidewalk row, and a repair is only accepted if
it lands 40 m clear of everything already fitted.

E 1st St comes back at 82.6 m below E 2nd St, with rows of 22 and 15 trees at
30 and 53 cm and a half-row of 5.58 m against E 2nd St's 5.60 — a 60 ft street,
which is what it is. Gouverneur St, whose old-grid line was interpolated rather
than measured, moves 102 m. A street with no trusted line on one side is left
alone, which is what protects E 14th St and FDR Drive: they top and tail their
families, have one row of trees each, and with nothing beyond them to close a
band there is nothing to search.

A fifth thing was missing rather than wrong: sub-zones were not clipped to
their grid region, which the mid-block scheme had done. Grand St and East
Broadway cross near lng −73.9827, and east of there East Broadway runs NORTH of
Grand, so bounding Two Bridges by East Broadway alone let 3E reach back over
the Lower East Side and claim 18 trees 2F already held.

## Caveat

No street-centerline dataset is reachable from this repo's build environment
(NYC Open Data, Census TIGER and the OSM endpoints are all blocked), so every
street except E 14th St, the Bowery and 4th Ave is located from the trees
standing along it. Sixteen streets have no two-row fit and cannot be used as
boundaries. In the East Village that is E 14th St, for the reason above, and
FDR Drive; in zone 2, Willett St / Bialystoker Pl and Columbia St, where Baruch
Houses covers most of what would be their frontage. Zone 3 loses the most:
8 of 17 in the Chinatown strip — Chrystie, Forsyth, Eldridge, Orchard, Ludlow,
Clinton, Jackson and FDR Drive — and 4 of 17 in Two Bridges: Catherine,
Rutgers, Jefferson and Clinton. Those streets can still be named
and walked; they simply cannot be used as sub-zone edges, which is why zone 3's
divisions fall on Essex, Monroe, Pike and Montgomery. Housing superblocks (Tompkins Square,
Baruch, Vladeck, Rutgers, Smith, LaGuardia) have no interior streets to
detect. If real centerline data ever lands in the repo, the fitting
step is the part to replace.
