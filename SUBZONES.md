# CB3 Sub-Zones

The three care zones split into 31 sub-zones of roughly ten city blocks each.

**Every sub-zone boundary is a street centerline.** A sub-zone is the area
between two E-W streets and two N-S streets, so it can be handed to a crew in
words - "E 4th to E 2nd, Bowery to Ave B" - and walked without a map. Trees on
a boundary street belong to the sub-zone on their own side of the roadway,
which is the same rule the existing Houston/Grand zone dividers already follow.

Sub-zones nest inside the zones: no sub-zone crosses Houston St or Grand St.

## Files

| File | What it is |
|---|---|
| `data/subzones.geojson` | One polygon per sub-zone, clipped to the CB3 boundary |
| `data/subzones.csv` | `treeId,subzoneId,zone,latitude,longitude,species` for all 5,315 live street trees |
| `data/cb3-street-grid.json` | The named street centerlines everything above is built from |

## Rebuilding

```
python3 scripts/build_street_grid.py   # streets  -> data/cb3-street-grid.json
python3 scripts/build_subzones.py      # subzones -> data/subzones.{geojson,csv}
```

Both print a validation report. `build_subzones.py` checks that every tree
falls inside its own sub-zone polygon and inside no other; that line should
read `0 trees outside ... 0 inside more than one`.

Sub-zone size is `TARGET_BLOCKS` in `scripts/build_subzones.py` (currently 10).

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

| ID | Zone | Blocks | Trees | Bounded by |
|---|---|---|---|---|
| **1A** | 1 | 8 | 183 | E 14th St–E 12th St, CB3 Boundary–Ave A |
| **1B** | 1 | 8 | 158 | E 14th St–E 12th St, Ave A–FDR Dr |
| **1C** | 1 | 8 | 225 | E 12th St–E 10th St, CB3 Boundary–Ave A |
| **1D** | 1 | 8 | 212 | E 12th St–E 10th St, Ave A–FDR Dr |
| **1E** | 1 | 10 | 223 | E 10th St–E 8th St / St Marks Pl, CB3 Boundary–Ave B |
| **1F** | 1 | 7 | 195 | E 10th St–E 8th St / St Marks Pl, Ave B–CB3 Boundary |
| **1G** | 1 | 8 | 181 | E 8th St / St Marks Pl–E 6th St, CB3 Boundary–Ave A |
| **1H** | 1 | 8 | 221 | E 8th St / St Marks Pl–E 6th St, Ave A–CB3 Boundary |
| **1I** | 1 | 8 | 203 | E 6th St–E 4th St, Bowery / 3rd Ave–Ave B |
| **1J** | 1 | 6 | 168 | E 6th St–E 4th St, Ave B–CB3 Boundary |
| **1K** | 1 | 8 | 220 | E 4th St–E 2nd St, Bowery / 3rd Ave–Ave B |
| **1L** | 1 | 7 | 146 | E 4th St–E 2nd St, Ave B–CB3 Boundary |
| **1M** | 1 | 11 | 264 | E 2nd St–E Houston St, Bowery / 3rd Ave–Ave D |
| **2A** | 2 | 12 | 214 | E Houston St–Rivington St, Bowery–Ludlow St |
| **2B** | 2 | 12 | 230 | E Houston St–Rivington St, Ludlow St–Ridge St |
| **2C** | 2 | 10 | 155 | E Houston St–Rivington St, Ridge St–FDR Dr |
| **2D** | 2 | 12 | 195 | Rivington St–Broome St, Bowery–Ludlow St |
| **2E** | 2 | 12 | 180 | Rivington St–Broome St, Ludlow St–Ridge St |
| **2F** | 2 | 9 | 110 | Rivington St–Broome St, Ridge St–FDR Dr |
| **2G** | 2 | 9 | 117 | Broome St–Grand St, Bowery–Suffolk St |
| **2H** | 2 | 8 | 63 | Broome St–Grand St, Suffolk St–FDR Dr |
| **3A** | 3 | 10 | 104 | Grand St–Canal St, Bowery–Suffolk St |
| **3B** | 3 | 9 | 107 | Grand St–Canal St, Suffolk St–CB3 Boundary |
| **3C** | 3 | 13 | 232 | Canal St–Division St, CB3 Boundary–Jackson St |
| **3D** | 3 | 10 | 165 | E Broadway–Madison St, CB3 Boundary–Jefferson St |
| **3E** | 3 | 10 | 261 | E Broadway–Madison St, Jefferson St–FDR Dr |
| **3F** | 3 | 10 | 191 | Madison St–Cherry St, CB3 Boundary–Jefferson St |
| **3G** | 3 | 8 | 96 | Madison St–Cherry St, Jefferson St–FDR Dr |
| **3H** | 3 | 11 | 165 | Cherry St–South St, CB3 Boundary–Clinton St |
| **3I** | 3 | 8 | 73 | Cherry St–South St, Clinton St–FDR Dr |
| **3J** | 3 | 5 | 58 | South St–CB3 Boundary, CB3 Boundary–Gouverneur St |
