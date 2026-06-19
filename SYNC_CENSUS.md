# Syncing Census Data

This document explains how to keep the tree census data (`data/census.json`) up-to-date with live NYC Parks data.

## What gets synced?

The sync script pulls the latest tree data from NYC Parks & Recreation's public dataset on NYC Open Data and updates:

- **Planting years** - newly planted trees and 2023+ cohort data
- **Health status** - current condition assessments
- **DBH measurements** - trunk diameter at breast height
- **New trees** - recently added to the inventory
- **Tree location & species** - core tree information

## Automatic syncing (Recommended)

GitHub Actions automatically runs the sync **on the 1st of every month at 2 AM UTC**.

To monitor:
1. Go to the repository on GitHub
2. Click **Actions** tab
3. Look for "Sync Census Data" workflow

## Manual syncing

Run locally when you need fresh data immediately:

```bash
python scripts/sync-census.py
```

### Requirements

```bash
pip install requests
```

### What it does

1. Fetches tree data from NYC Open Data (5bgh-vtsn dataset)
2. Filters to Community Board 3 (Manhattan LES area)
3. Merges with existing census.json, preserving local customizations
4. Saves updated data

### Example output

```
Starting census.json sync...

✓ Loaded existing census.json with 11284 trees
Fetching tree data from NYC Open Data...
✓ Fetched 11356 trees from NYC Open Data

Processing data...
✓ Merged data: 11356 total trees
✓ Saved updated census.json

✓ Sync complete!
  Trees in CB3: 11356
  Timestamp: 2026-06-19T15:30:45.123456
```

## What this fixes

After syncing, these features will have accurate data:

- ✅ Natural language queries ("tier 3 trees", "East 9 trees")
- ✅ Stats tab tier breakdowns and counts
- ✅ Planting year filtering
- ✅ Priority-based tree sorting
- ✅ Tree care targeting by tier/planting year

## Data sources

- **Primary source**: NYC Parks Street Tree Census 2015 with annual updates
- **Live updates**: NYC Open Data (5bgh-vtsn)
- **Local overrides**: Your care activities, tree guards, reservations (separate data sources, not affected by sync)

## Troubleshooting

**Script fails with network error:**
- Check your internet connection
- Verify NYC Open Data is accessible

**Script runs but data doesn't change:**
- The API might not have new data
- This is normal - the sync is working correctly

**Data looks wrong after sync:**
- Review git diff to see what changed
- You can revert with `git checkout data/census.json`

## Disabling automatic syncs

To stop automatic syncing, disable the workflow:

1. Go to **Actions** → **Sync Census Data**
2. Click **...** → **Disable workflow**

Or delete `.github/workflows/sync-census-data.yml`
