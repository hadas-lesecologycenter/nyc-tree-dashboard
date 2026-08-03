# CB3 Sub-Zones

The three care zones split into 28 sub-zones of roughly ten block segments each.

**Boundaries run mid-block, so both sides of every street stay in the same
sub-zone.** A sub-zone is a set of whole streets rather than an area fenced off
by them, so it can be handed to a crew in words — "E 4th St to E 3rd St, Bowery
to Ave A, both sides" — and walked without a map.

A boundary has to cross the street network somewhere: cutting along
centrelines separates a street from its own far sidewalk, and cutting
mid-block divides the perpendicular streets part-way along a block. Mid-block
is the cheaper cut here — 88 of CB3's 509 block segments end up divided,
against 106 when the same sub-zones were bounded by centrelines — because what
gets divided is the avenues, and an avenue was previously being split
lengthwise along its entire run.

The three **zone** dividers — Houston St, Grand St and East Broadway — keep
their centrelines, so sub-zones still nest inside the three zones and no zone
total moves. They are the only streets still split down the middle.

## Files

| File | What it is |
|---|---|
| `data/subzones.geojson` | One polygon per sub-zone, clipped to the CB3 boundary |
| `data/subzones.csv` | `treeId,subzoneId,zone,latitude,longitude,species` for all 5,308 live street trees |
| `data/cb3-street-grid.json` | The named street centerlines everything above is built from |

## Rebuilding

```
python3 scripts/build_street_grid.py   # streets  -> data/cb3-street-grid.json
python3 scripts/build_subzones.py      # subzones -> data/subzones.{geojson,csv}
```

Both print a validation report. `build_subzones.py` checks that every tree
falls inside its own sub-zone polygon and inside no other — that line should
read `0 trees outside ... 0 inside more than one` — and reports how many block
segments end up divided between two sub-zones.

Sub-zone size is `TARGET_BLOCKS` in `scripts/build_subzones.py` (currently 10);
`ROWS_PER_BAND` (currently 2) sets how many streets a sub-zone runs across
before it splits sideways instead.

## Caveat

No street-centerline dataset is reachable from this repo's build environment
(NYC Open Data, Census TIGER and the OSM endpoints are all blocked), so the
grid is reconstructed from the tree census itself: sidewalk rows are detected
in the point cloud and named using the ~1,100 trees in `data/trees.csv` that
carry a street address. Lines are good to roughly a sidewalk width. Housing
superblocks (Tompkins Square, Baruch, Vladeck, Rutgers, Smith) have no
interior streets to detect and so read as single oversized blocks. If real
centerline data ever lands in the repo, re-run both scripts against it.

## The sub-zones

Each row lists the streets the crew works, both sides, and the avenues the run
spans. 28 sub-zones, 6-12 block segments (mean 8.6), 64-269 trees (mean 189).

| ID | Zone | Segments | Trees | Streets | Across |
|---|---|---|---|---|---|
| **1A** | 1 | 8 | 156 | E 14th St to E 13th St | Bowery / 3rd Ave to Ave A |
| **1B** | 1 | 7 | 93 | E 14th St to E 13th St | Ave B to FDR Dr |
| **1C** | 1 | 8 | 251 | E 12th St to E 11th St | Bowery / 3rd Ave to Ave A |
| **1D** | 1 | 6 | 135 | E 12th St to E 11th St | Ave B to Ave D |
| **1E** | 1 | 8 | 212 | E 10th St to E 9th St | Bowery / 3rd Ave to Ave A |
| **1F** | 1 | 8 | 227 | E 10th St to E 9th St | Ave B to FDR Dr |
| **1G** | 1 | 8 | 223 | E 8th St / St Marks Pl to E 7th St | Bowery / 3rd Ave to Ave A |
| **1H** | 1 | 6 | 198 | E 8th St / St Marks Pl to E 7th St | Ave B to Ave D |
| **1I** | 1 | 8 | 167 | E 6th St to E 5th St | Bowery / 3rd Ave to Ave A |
| **1J** | 1 | 7 | 197 | E 6th St to E 5th St | Ave B to FDR Dr |
| **1K** | 1 | 8 | 200 | E 4th St to E 3rd St | Bowery / 3rd Ave to Ave A |
| **1L** | 1 | 7 | 202 | E 4th St to E 3rd St | Ave B to FDR Dr |
| **1M** | 1 | 8 | 220 | E 2nd St to E 1st St | Bowery / 3rd Ave to Ave A |
| **1N** | 1 | 6 | 116 | E 2nd St to E 1st St | Ave B to FDR Dr |
| **2A** | 2 | 10 | 269 | Stanton St to Rivington St | Chrystie St to Orchard St |
| **2B** | 2 | 10 | 220 | Stanton St to Rivington St | Ludlow St to Clinton St |
| **2C** | 2 | 10 | 243 | Stanton St to Rivington St | Attorney St to Mangin St |
| **2D** | 2 | 12 | 218 | Delancey St to Broome St | Chrystie St to Ludlow St |
| **2E** | 2 | 12 | 202 | Delancey St to Broome St | Essex St to Ridge St |
| **2F** | 2 | 8 | 111 | Delancey St to Broome St | Pitt St to Mangin St |
| **3A** | 3 | 12 | 262 | Hester St to Canal St | Bowery to Essex St |
| **3B** | 3 | 11 | 179 | Hester St to Canal St | Norfolk St to FDR Dr |
| **3C** | 3 | 10 | 237 | Henry St to Madison St | Catherine St to Jefferson St |
| **3D** | 3 | 8 | 268 | Henry St to Madison St | Clinton St to Jackson St |
| **3E** | 3 | 10 | 177 | Monroe St to Cherry St | Catherine St to Jefferson St |
| **3F** | 3 | 7 | 84 | Monroe St to Cherry St | Clinton St to Jackson St |
| **3G** | 3 | 9 | 177 | Water St to South St | Catherine St to Jefferson St |
| **3H** | 3 | 8 | 64 | Water St to South St | Clinton St to Jackson St |
