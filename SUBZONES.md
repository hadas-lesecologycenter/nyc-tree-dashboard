# CB3 Sub-Zones

**Status: all of CB3 is drawn.** Twenty-five sub-zones cover the district —
**all 5,300 CB3 street trees sit in exactly one** (census of 2026-10-12), none
in two, none in neither, and the per-zone totals come out at 2,466 / 1,368 /
1,466, exactly matching the three zones the dashboard reports. The worked
examples of how the method was arrived at below (the address check, the reach
measurement, the corner trees) are figures from the August 2026 build. The 28 mid-block sub-zones this
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
the middle.

**A sub-zone is named for the streets it holds**, avenues first, and the map
says "both sides of every street named". "4th Ave to 1st Ave, E 14th St to
E 11th St" is 4th, 3rd, 2nd and 1st Ave and E 14th down to E 11th St. E 10th
St, which closes 1A, is not in the name, because it belongs to 1D below. The
build writes each name from the blocks the sub-zone actually has. Until
October 2026 the names were written by hand from the edges, and since an edge
street belongs to one side of it only, the name disagreed with the streets
under it in all 25 sub-zones: 1J was "4th Ave to 1st Ave" with the Bowery as
its western street, and 3B and 3E ran "to the East River" without reaching it.

The exception to "both sides" is a street CB3's own boundary runs down: E 14th
St, whose north side is in CB6, and the Bowery and 4th Ave, whose west side is
not CB3. The build finds them, as the streets where for most of their trees
the point 22 m across the street is outside the district, and lists them in
`one_side`; the popup says "CB3 side only" for them.

In the build script each side names the *line* that closes it instead, which
is what makes neighbours abut exactly: 1A's eastern edge and 1B's western edge
are both `1 AVE`, one line, so they can neither gap nor overlap.

## The sub-zones

Sub-zones are laid out in bands running north to south, cut into columns west
to east. A band stops immediately north of the street it is named for, so that
street opens the band below: E 10th St closes 1A–1C by bounding them and then
belongs to 1D–1F. How many columns a band takes depends on the zone — zone 1
uses three throughout, zone 2 four then two, zone 3 two and then three and two
— because the three zones are not the same size or shape.

| ID | Zone | Name: both sides of every street named | CB3 side only | Blocks | Trees | On no block |
|---|---|---|---|---|---|---|
| **1A** | 1 | 4th Ave to 1st Ave, E 14th St to E 11th St | E 14th St and 4th Ave | 25 | 257 | 3 |
| **1B** | 1 | Ave A to Ave B, E 14th St to E 11th St | E 14th St | 16 | 250 | 0 |
| **1C** | 1 | Ave C to FDR Dr, E 14th St to E 11th St | E 14th St | 16 | 158 | 8 |
| **1D** | 1 | 4th Ave to 1st Ave, E 10th St to E 8th St / St Marks Pl | 4th Ave | 19 | 233 | 2 |
| **1E** | 1 | Ave A to Ave B, E 10th St to E 8th St / St Marks Pl | – | 11 | 125 | 0 |
| **1F** | 1 | Ave C to FDR Dr, E 10th St to E 8th St / St Marks Pl | – | 14 | 280 | 0 |
| **1G** | 1 | 4th Ave to 1st Ave, E 7th St to E 5th St | 4th Ave and Bowery | 17 | 175 | 0 |
| **1H** | 1 | Ave A to Ave B, E 7th St to E 5th St | – | 11 | 155 | 0 |
| **1I** | 1 | Ave C to FDR Dr, E 7th St to E 5th St | – | 15 | 247 | 5 |
| **1J** | 1 | Bowery to 1st Ave, E 4th St to E 1st St | Bowery | 17 | 215 | 2 |
| **1K** | 1 | Ave A to Ave B, E 4th St to E 1st St | – | 13 | 175 | 0 |
| **1L** | 1 | Ave C to FDR Dr, E 4th St to E 2nd St | – | 10 | 196 | 2 |
| **2A** | 2 | Chrystie St to Eldridge St, E Houston St to Rivington St | – | 19 | 222 | 2 |
| **2B** | 2 | Allen St to Essex St, E Houston St to Rivington St | – | 25 | 206 | 0 |
| **2C** | 2 | Norfolk St to Clinton St, E Houston St to Rivington St | – | 18 | 204 | 0 |
| **2D** | 2 | Attorney St to Mangin St, E Houston St to Rivington St | – | 33 | 303 | 10 |
| **2E** | 2 | Bowery to Essex St, Delancey St to Broome St | Bowery | 28 | 187 | 9 |
| **2F** | 2 | Norfolk St to Mangin St, Delancey St to Broome St | – | 33 | 246 | 33 |
| **3A** | 3 | Mulberry St to Eldridge St, Grand St to Canal St | – | 19 | 251 | 24 |
| **3B** | 3 | Allen St to Clinton St, Grand St to Canal St | – | 28 | 203 | 9 |
| **3C** | 3 | Catherine St to Pike St, E Broadway to Madison St | – | 14 | 156 | 19 |
| **3D** | 3 | Rutgers St to Montgomery St, E Broadway to Madison St | – | 23 | 231 | 1 |
| **3E** | 3 | Gouverneur St to Jackson St, E Broadway to Madison St | – | 14 | 158 | 6 |
| **3F** | 3 | Catherine St to Pike St, Monroe St to South St | – | 23 | 281 | 9 |
| **3G** | 3 | Rutgers St to Jackson St, Monroe St to South St | – | 34 | 186 | 5 |

1E is the small one because Tompkins Square Park fills most of Ave A to Ave B
between E 7th and E 10th, and park trees are not street trees.

**Zone 2 is cut differently from zone 1, because it is shaped differently.**
Delancey St is the one street here anybody navigates by and it splits the zone
938 trees to 434, so the north band takes four sub-zones and the south two —
forcing zone 1's three columns onto both would have produced one sub-zone of
about 100 and another of 400. The column lines are Eldridge, Essex and Clinton,
the wide named streets a crew would recognise, and Essex is shared by both
bands so it runs unbroken through the zone. All six land between 187 and 303
trees, against zone 1's 125 to 280.

**Zone 3 is two street patterns, not one**, so it is divided as two. Grand St
to East Broadway is the tail of the Lower East Side grid; south of East Broadway,
Two Bridges turns about 35 degrees and runs on its own. They are fitted
separately and cut separately, which is why the sub-zones do not line up across
East Broadway — the streets do not either. The Chinatown strip is thin and
holds 454 trees, so it splits east-west only, on Eldridge St; Two Bridges holds
1,012 and takes five, three above Monroe St and two below, with Pike St shared
by both bands.

**Until October 2026 the Chinatown strip's north-south streets carried the
names of streets four blocks east.** Its lines were seeded from the old grid,
whose names there were shifted: the line called Essex St met Grand St 1.0 m from
where zone 2's Eldridge St does, and six trees addressed 7–29 Ludlow St were
filed on "Clinton St". The positions were right, so only the names changed,
and every block kept its ID. Eight of the names are checked. Chrystie,
Forsyth, Eldridge, Allen, Orchard, Ludlow, Essex and Clinton St each run on
within 0–4.4 m of the same street in zone 2 (Chrystie 17 m), and the addresses
agree (7–29 Ludlow, 42–48 Hester, 25 Essex, 411 Grand St). Jefferson St meets
East Broadway where Two Bridges' Jefferson St does. The four west of Chrystie
St, **Mulberry, Mott and Elizabeth St and Bowery / Chatham Sq, are named from
the order of the streets alone** and should be checked against a street map.

Zone 2's blocks are shorter — its avenues are 70–80 m apart against the East
Village's 215–230 m — so a sub-zone there holds more segments of fewer trees
each: 2F is 33 segments averaging 6 or 7 trees, where 1A is 25 averaging 10. That is
the street pattern, not the division.

## The zone lines

Three lines carry the split between the care zones: Houston St between zones 1
and 2, Grand St between 2 and 3, and East Broadway, which seams the Lower East
Side grid to Two Bridges inside zone 3. They used to be the one exception to
the rule above — they ran down the middle of their streets, and each of those
three streets was split between two zones.

They were also not parallel to the streets they were named for, which was the
worse half of it. Each was fitted from the handful of trees that carry an
address on it (six on Houston, six on Grand) with a single bearing shared
across the whole Lower East Side grid, and that bearing is not Houston's. The
old Houston line therefore drifted **62 m across a street 32 m wide** over its
1,544 m run: south of all three of Houston's tree rows at the Bowery, north of
all three at the East River. Which zone a Houston St tree was counted in
depended on how far east it stood. 127 of its 211 trees were in zone 1 and 84
in zone 2, and the boundary between those two sets was nothing on the ground.

Now each line is fitted from **every tree on its own street, from both sides**,
and then offset north of it by the same rule as every other boundary here. So
E Houston St sits wholly in zone 2, Grand St wholly in zone 3 and East Broadway
wholly in Two Bridges. No street in CB3 is split by any boundary, sub-zone or
zone.

Each line sits in the **gap between its own street's planting and the block
beyond**, like every other edge: 18.83 m from Houston's centreline, 16.37 m
from Grand's, 13.76 m from East Broadway's — 2.6 to 3.5 m past each street's
outermost tree row. They used to stand 4.1, 5.4 and 8.0 m past it, which put
East Broadway's line most of a sidewalk into the block north of it.

Placing them that way needs to know which trees near a line stand on the
divider street and which stand on the block beyond, and that is only known once
the regions are split and fitted — which needs the line. So it is done twice:
a first pass places each line far enough out to have clear air, which is close
enough to sort the trees, and a second uses the sorting to put the line where
it belongs. The sorting is done against the streets of **both** regions a line
divides, not just the one a tree currently falls in. Otherwise moving the line
moves trees between regions, which changes the streets they are tested against,
which moves the line: Houston oscillated between 19.48 and 20.39 m and never
settled. Testing both sides makes a tree's street the same answer whichever
side of the line it is on, and the second pass is then the last one.

Two more things had to change to make it work at all.

* **A divider street had no centreline, and could not have one.** Each grid
  region sees one side of its own divider, and half a street does not have a
  middle. They are now fitted once, district-wide, from the trees on both
  sides — and not with the two-row search, which cannot read them either.
  E Houston St plants **three** rows: north sidewalk, a planted median, south
  sidewalk, 32 m from the outside of one to the outside of the other. A search
  for the densest pair a roadway apart finds a sidewalk and the median and puts
  the centre 8 m out. So every row is found, and the street is the run of them
  that holds together: 66, 81 and 39 trees on Houston, and the 11-tree scatter
  of the next block over left outside. Grand St has four rows, East Broadway
  two.
* **A zone line is offset once for the whole district**, not per stretch like
  every other edge. An ordinary edge is placed stretch by stretch because the
  planting changes along the street; a zone line is also the test for which
  zone a tree is *in*, and a line that moved along its run would file a tree
  under one zone and draw it inside another.

The dashboard's `getZoneId` carries the same two lines, and the build prints
them in lng/lat under `=== zone lines` to be pasted in. Before this they were
different lines from the ones the sub-zones used — the grid's bearing was
−0.2683 and the dashboard's −0.2891 — and **54 trees were counted in one zone
and drawn in another**. That is now zero of 5,300.

The cost is clearance. Houston's boundary has 0.37 m of air rather than the
metre the rule asks for, and East Broadway's 0.36 m: the trees just north of
Houston are the wedge of short blocks up to E 1st St, which run at the East
Village bearing and so never line up parallel to it, and there is no clean gap
to find. The build lists every edge that ends up under a metre.

What a zone line cannot fix is a corner. In the August 2026 build each still had
trees of other streets inside it — 14 on Houston, 11 on Grand, 4 on East
Broadway — and they are not
there because the line is too far out. They are the corner trees where an
avenue meets the divider, interleaved with the divider's own frontage: on
Houston they run from 14.7 m out, inside Houston's own planting, which reaches
19.3 m. No line parallel to Houston can separate them.

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
layer in the map's Program Layers panel shows all 495 of them.

Every segment carries a **stable identifier** — `1A-03` — so a block can be
assigned, radioed and reported by name. Within a sub-zone they were first
numbered streets first, north to south, then avenues west to east, by rank
rather than by any fitted value. Rank alone does not hold an ID to its block
from one build to the next: it rests on whichever of a segment's trees comes
last in the census, which comes back reshuffled every week, and on the first
rebuild the north and south sidewalks of E 5th St east of Cooper Square,
1G-07 and 1G-06, would have swapped numbers. So **every ID ever issued is
kept in `data/segment-ids.json`**, against the segment's sub-zone, street and
two cross streets — by the build's own street names and by the printed label,
so a change in how labels are printed does not lose it (a street renamed in the
build's grid itself gets new IDs, its old numbers kept out of use). A segment
the ledger knows keeps
its ID, even after builds it was missing from (a block whose only tree dies
and is replanted comes back under its old number). A segment it has never
seen gets its sub-zone's next number, after the highest that sub-zone has
ever issued, so a number is never handed to a different block; the build
stops, naming the file, if the ledger is damaged rather than renumber. Replaying
every weekly census since August through the build ends on exactly today's
IDs. `data/subzones.csv` carries a `segmentId` on every tree, so "which trees
are in 1A-03" is a lookup rather than a guess.

The build fits its street frame to CB3's own E 14th St boundary and takes the
Bowery and 4th Ave from its western boundary. Those runs are found by the
coordinates of the vertices they start and end on, not by their index in the
ring: the census workflow refetches `data/cb3-boundary.json`, and on
2026-08-24 seven vertices on the ring's East River side were replaced by
fifteen, moving every index past them by eight. A rebuild on the old indices
would have fitted the frame 4° off. The walk also always starts the ring at the
vertex it started on in August, whatever a refetched ring starts on: the first
fit counted that vertex twice, and counting another one twice turns the frame
by hundredths of a degree, enough to move a hundred trees. The build stops
rather than fit the wrong run if either end vertex goes missing, if a run goes
more than half way round the ring (a ring stored the other way round), or if
the frame comes out at any bearing but the one it has always had.

A street with no two-row fit of its own — Mulberry, Mott, Elizabeth, Chrystie,
Forsyth, Ludlow, Jefferson and Clinton St in Chinatown; Catherine, Rutgers,
Jefferson and Clinton in Two Bridges; Columbia St; E 14th St and the FDR in the
East Village — is seeded from the old grid. It used to take the fitted slope of
its family through the old grid's offset, and an offset is where the line
crosses E 14th St, nearly 2 km north of Chinatown, so the 2026-10-12 census,
which tipped the Chinatown avenues by 0.0048, slid Forsyth and Chrystie St 9 m
across their blocks and would have emptied 3A-07 and 3B-24. **Those lines are
now pinned in `data/pinned-street-lines.json`**: the first build to place a
seeded line records it there, and every later build draws it exactly there,
whatever the census does. The pins were taken from the 2026-09-28 build, which
the pinned build reproduces byte for byte. To move one on purpose, delete its
entry and rebuild. Against that build, the 2026-10-12 census moves 4 corner
trees (at Canal and Eldridge, and Canal and Allen St) and retires 3A-07, whose
only tree now counts on Eldridge St; its number stays reserved.

Two things make the segmentation legible rather than merely present:

* **A segment is drawn as bands lying under its trees.** One band per row of
  trees — two for an ordinary block face, three where a street has a mall —
  in a pane below the markers, so every tree keeps its own colour. That is the
  point of the shape: the map's whole job on the same screen is to say what
  *tier* each tree is, and the layer used to paint the trees themselves in the
  segment colour, which covered exactly that.

  A band is the rectangle, lined up with its row, from the row's first tree to
  its last and from its innermost tree to its outermost, drawn with a thick
  rounded stroke so it pads every tree by the same margin. So **every tree on
  a segment is inside its band at every zoom**. An earlier band was a line
  down the middle of the row, and any tree a metre or two off that line hung
  over its edge once the map was zoomed in.

  The rows are found against the **street's own direction**, which the build
  writes on each segment (`bearing`, from the street's fitted centreline) —
  never against the trees' spread alone. Read off the trees, a short or
  unevenly planted block tips tens of degrees off its street, and bands crossed
  the roadway on the diagonal and each other in an X. But a fitted line is one
  bearing for a whole street, and on Water St, South St, Pitt St and Allen St
  the planted rows run 4–8° off it; so a segment of five or more trees is
  turned, by up to 10°, to the angle that best lines all its trees up with
  each other, at a small cost per degree so a block whose trees say little
  stays on its street. Then the trees are split at the widest gap across the
  street until no row is wider than 5 m (the closest kerb rows in CB3, on Pike
  St, are 7.2 m apart), and a row is cut wherever 40 m pass without a tree.
  Where a street bends inside one segment — E Houston St swinging down to the
  FDR — the trees left in short pieces get a turn of their own, kept only if it
  joins them into fewer, thin rows.

  Hovering and clicking a band is done by hit-testing the map's own pointer
  events rather than by binding to the shape. A band is drawn below the tree
  markers, and those are on a canvas covering the whole viewport that takes
  every pointer event before anything underneath sees it — hover a band and
  `document.elementFromPoint` returns the canvas. Leaflet's canvas renderer
  only swallows a click that lands on a marker, so everything else reaches the
  map, which gives exactly the split the layer wants: a click on a tree opens
  the tree, a click on the band beside it opens the segment. The bands are
  opaque inside a pane that is faded as a whole — so an overlap is the colour
  of the band on top rather than a darker patch that reads as more trees — and
  hover names that top band. Busy rows are drawn first and lone trees last.

  Its width is measured against the **tree markers**, not the street, because
  lying under them it is only visible in the margin it leaves around them. A
  band as wide as the row of dots is perfectly hidden by it — at the default
  zoom the markers are 9 px and touching, and a 9 px band disappeared wherever
  a block was fully planted, which is everywhere it matters. So the stroke is
  the marker's own diameter plus 11 px, widening to plus 21 px at z19.

  Each segment's ID label sits on the middle of its busiest band that does not
  land on a label already placed at z18, so it is always on its own segment.
* **Colour carries how many trees are on the block**, on a single-hue ramp from
  pale (1–4) to navy (30+), with a legend under the layer's checkbox. Sub-zone
  identity is already on the map as the sub-zone polygon, and twenty-five
  sub-zones is well past what colour can distinguish, so hue is spent on the
  one thing nothing else shows. The ramp is blue and the tiers are red, orange
  and green, so a band never reads as a tier.

Drawing bands from the trees removes a class of failure too: there is no span
to trim and no boundary to clip against, so no segment can come out undrawable.
All of them are drawn by construction, as bands and dots, and every tree that
carries a `segmentId` lies inside one.

### One block face, one sub-zone

A tree is put on a street when it stands within that street's reach (see
below), and a sub-zone edge is drawn just past the street's own planting, so
the two did not always agree. A corner tree can be nearer the cross street, and
set-back planting stands past the edge. Each of those came out as a second,
smaller copy of a block in the next sub-zone: 19 block faces were split, so two
crews could be sent to the same one. E 10th St from Ave D to the FDR had 18
trees in 1C, the Riis Houses frontage 12–30 m north of the street, and 22 in
1F, under the same name.

So **each block face belongs to the sub-zone holding most of its trees**.

* A tree of it in another sub-zone goes on the nearest street whose block is
  that sub-zone's own: the cross street, for a corner tree. Failing that, it
  goes on the nearest block of the same street the sub-zone owns, if one of
  that block's trees is within 20 m (the tree just round the corner). That
  moved 16 trees.
* Where five or more have nowhere to go, as with a set-back row, the edge
  between the two sub-zones **steps out round them** instead. It goes out along
  the cross street past the first tree, along the street past the furthest, and
  back. Where that would leave a sliver against the district boundary, it runs
  out to the boundary. The whole row then joins its block in the other
  sub-zone. Both sub-zones' outlines get the same points, so they still meet
  without a gap or an overlap. This happens twice: E 10th St, Ave D to FDR Dr
  (18 trees, 1C to 1F), and Monroe St west of Catherine St (6 trees, 3C to 3F).
* One tree, on Pike St between Madison and Monroe St in 3D, is left on no
  block.

No block face is split now. The 19 IDs that went out of use stay reserved in
the ledger.

### Where a block ends

A block runs between two cross streets. A block at the end of its region has
no cross street beyond it, and was printed as running "to the district edge".
37 of those were wrong, because the block stops at a zone line: Ludlow St south
of Broome St stops at Grand St. The build now follows the street's line out
from its last tree until it leaves the sub-zone. If it is still inside CB3
there, the end is named after the zone line it crossed: "Ludlow St, Broome St
to Grand St". Where both ends come out the same, as with Forsyth St's corner
trees on the north side of E Houston St, the block is printed "Forsyth St at
E Houston St". The 20 that still say "to the district edge" do reach it. Only
the printed label changed: the ID ledger still keys on the old form, so every
ID stays on its block.

## Trees on no segment

Every tree in CB3 is in exactly one sub-zone, because a sub-zone is a polygon
and the test is whether the tree is inside it. A **segment** is a stricter
claim — it says which street the tree stands on — and 149 of the 5,300 (2.8%)
cannot be given one. They are counted in their sub-zone's total, listed in
`subzones.csv` with an empty `segmentId`, and named in the sub-zone's popup, so
a crew planning a day is told how many trees it will find off the block faces.

The sub-zone popup also gives the share of its trees that are on a block and
lists its blocks, busiest first, each with its tree count. Clicking a block's ID
turns on the Block Segments layer and zooms to that block.

By zone: 2,444 of 2,466 on a segment in zone 1 (99%), 1,314 of 1,368 in zone 2
(96%), 1,393 of 1,466 in zone 3 (95%). What gradient is left is the housing, not
the method — Baruch, Seward Park, Masaryk, Hillman, Vladeck, Rutgers, Smith and
LaGuardia all plant their frontage on housing-authority ground well inside the
block, and the census still calls those street trees.

Two streets are given more reach than the measurement finds, in
`REACH_OVERRIDE_M`: South St, 60 m either side (its esplanade trees and the
set-back rows of the Smith Houses and Lands End, spread too evenly to read as
one row), and Madison St, 32 m on its south side (the set-back planting at 200
Madison St and along the Rutgers and LaGuardia frontage). That put 86 trees on
a segment that had none and moved none that had one.

Past every street's measured reach, a tree is still put on the **nearest
street's block if it stands within 30 m of that street** (`LOOSE_TREE_M`):
set-back rows in front of housing, the inner rows of the Allen St mall. It
only joins a block that already has trees of its own, or one that at least five
such trees start together (`LOOSE_BLOCK_MIN`), so the rule adds no one-tree
segments. Beyond 30 m a tree is in a courtyard or a superblock interior and
stays on no block. On the 2026-10-12 census this put 265 trees on a block
(3A 78 to 25 loose, 2F 58 to 33, 3F 34 to 9, 3C 33 to 19), moved none that had
one, and started one segment, 1C-17 (E 10th St, Ave D to FDR Dr, 18 trees),
for 513 in all. (1C-17 has since joined 1F-03; see One block face, one
sub-zone.) A set-back tree too few to start its own street's block goes on the
next street within 30 m whose block the sub-zone already has, which at a corner
is the cross street. That put 7 more trees on a block in October 2026. Of the 14 addressed trees it placed, 12 land on the street
their address names; the other two, at 24 Columbia St and 25 Bialystoker Pl,
land on the neighbouring street.

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
street a tree is on. Against it, **331 (77%) are assigned exactly the street
their address names**. Of the 69 that differ, 21 stand within 30 m of that
street — corner trees, and frontage the address and the roadway disagree about,
like the ten trees addressed 122 Henry Street that stand in a row along Madison
St. 30 are on no street at all.

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
side streets, 50 ft for the avenues) so it lands on the property line. That
distance is measured square to the street. On a street that runs at an angle to
the frame, moving the line that far moves its intercept further, by the
hypotenuse of its slope; until October 2026 the build moved the intercept by
the distance itself, so Two Bridges edges sat 18% closer to their streets than
intended and split blocks there. Fixing it moved 9 trees between sub-zones.

Half a right of way is where a boundary wants to sit, but not always where it
can, because a right of way is a constant and a street's planting is not. As
far as Ave C the north side of E 10th St is an ordinary sidewalk row 5.4 m out;
east of it the Jacob Riis Houses set their frontage back and plant it 8–10 m
out, past the property line. A boundary held at 9.14 m ran straight down that
row.

So an edge is placed in the **gap between the trees standing on its own street
and the trees standing on the block beyond it** — both of which are known,
because every tree has already been told which street it is on. Half a right of
way is used when the gap has room for it, and the middle of the gap otherwise.
That is what keeps a boundary from cutting a block face in two, and it is not
the same as hunting outward for clear air, which is what this did before:
Delancey St plants its north row 9.7 m out, adding a sidewalk width put the
floor at 13.2 m — past the corner trees of the avenues at 11.5 and 13.0 m — and
the hunt for air then pushed the line to 15.6 m. It stood 6 m inside the blocks
north of Delancey and clipped a tree or two off the end of ten avenue block
faces. The gap it should have used, between Delancey's own row at 10.0 m and
the first avenue tree at 11.5 m, is 1.5 m wide and no outward search starting
at 13.2 m can find it.

The offset is worked out per **stretch** of a street, not for the street as a
whole, because the planting changes along it: E 10th St stands at 9.14 m west
of Ave B and 10.19 m east of it. But two sub-zones that share a boundary have
to share the offset, and they do not always have the same column — north of
Delancey the band is cut into 2C (Essex to Clinton) and 2D (Clinton to the
river), while 2F runs the whole way below it. Computing each one over its own
column put 15.17 m, 15.63 m and 15.30 m on the same boundary: the line stepped
twice, and 2D reached 33 cm further into the block than 2F gave up. So columns
that **overlap** share one offset, worked out over the union of them; columns
that merely touch — 1A's and 1B's on E 10th St, which meet on 1st Ave — do not,
which is what keeps the Riis nudge local to the sub-zones that need it.

Some gaps are narrow. The build lists every edge that ends up with less than a
metre of air, and the tightest are the ones where a wide street meets blocks
that are not parallel to it: E Houston St at 0.55 m, Delancey St at 0.74 m,
E 10th St at 0.35 m. No tree is cut by any of them.

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
| `data/segment-ids.json` | Every segment ID ever issued; commit it with the data |
| `data/pinned-street-lines.json` | Where each seeded street is drawn; commit it with the data |

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
standing along it. Fifteen streets have no two-row fit and cannot be used as
boundaries. In the East Village that is E 14th St, for the reason above, and
FDR Drive; in zone 2 only Columbia St, where Baruch Houses covers most of what
would be its frontage. Zone 3 loses the most: 8 of 17 in the Chinatown strip —
Mulberry, Mott, Elizabeth, Chrystie, Forsyth, Ludlow, Jefferson and Clinton St —
and 4 of 17 in Two Bridges: Catherine, Rutgers, Jefferson and Clinton. Those
streets can still be named and walked; they simply cannot be used as sub-zone
edges, which is why zone 3's divisions fall on Eldridge, Monroe, Pike and
Montgomery. Housing superblocks (Tompkins Square,
Baruch, Vladeck, Rutgers, Smith, LaGuardia) have no interior streets to
detect. If real centerline data ever lands in the repo, the fitting
step is the part to replace.
