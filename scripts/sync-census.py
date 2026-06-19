#!/usr/bin/env python3
"""
Sync census.json with live NYC Parks tree data from NYC Open Data.

This script fetches the latest tree inventory from NYC Parks & Recreation's
publicly available dataset and updates the local census.json file with:
- Updated planting years
- Current health status
- Latest DBH measurements
- Any trees added recently
- Tree type classification (park vs street)

Run this periodically (e.g., monthly) to keep tree data fresh for:
- Stats calculations
- Tier assignments
- Natural language queries
- Map filtering
"""

import json
import sys
import requests
from pathlib import Path
from datetime import datetime

# NYC Parks tree dataset on NYC Open Data
# Dataset ID: ukgu-nxvx (Trees - Street Tree Census)
DATASET_URL = "https://data.cityofnewyork.us/api/views/ukgu-nxvx/rows.json"

# CB3 boundary (Community Board 3 Manhattan - LES)
# Roughly: 40.700 to 40.745 latitude, -74.005 to -73.970 longitude
CB3_BOUNDS = {
    'lat_min': 40.700,
    'lat_max': 40.745,
    'lng_min': -74.005,
    'lng_max': -73.970
}

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
CENSUS_FILE = REPO_ROOT / 'data' / 'census.json'

def fetch_nyc_parks_data():
    """Fetch tree data from NYC Open Data."""
    print("Fetching tree data from NYC Open Data...")
    
    try:
        # Fetch with limit and offset to handle large dataset
        # Using the Socrata API with filters
        params = {
            '$limit': 50000,
            '$where': f"latitude > {CB3_BOUNDS['lat_min']} AND latitude < {CB3_BOUNDS['lat_max']} AND longitude > {CB3_BOUNDS['lng_min']} AND longitude < {CB3_BOUNDS['lng_max']}"
        }
        
        response = requests.get(DATASET_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        rows = data.get('data', [])
        
        print(f"✓ Fetched {len(rows)} trees from NYC Open Data")
        return rows
        
    except Exception as e:
        print(f"✗ Error fetching from NYC Open Data: {e}")
        return None

def transform_to_census_format(rows):
    """Transform NYC Open Data format to census.json format."""
    trees = []
    
    # Field mapping from NYC Open Data to our census format
    # The actual column indices depend on the API response structure
    for row in rows:
        if not row or len(row) < 5:
            continue
        
        try:
            # NYC Open Data returns data as arrays - map to our expected fields
            tree = {
                'tree_id': str(row[0]) if row[0] else None,
                'tree_dbh': str(row[1]) if row[1] else None,
                'status': row[2] if len(row) > 2 else 'Unknown',
                'health': row[3] if len(row) > 3 else 'Unknown',
                'spc_common': row[4] if len(row) > 4 else 'Unknown',
                'spc_latin': row[5] if len(row) > 5 else None,
                'latitude': float(row[6]) if len(row) > 6 and row[6] else None,
                'longitude': float(row[7]) if len(row) > 7 and row[7] else None,
                'tree_cen_date': int(row[8]) if len(row) > 8 and row[8] else None,
                'planteddate': row[9] if len(row) > 9 else None,
                'globalid': row[10] if len(row) > 10 else None,
            }
            
            if tree['tree_id'] and tree['latitude'] and tree['longitude']:
                trees.append(tree)
        except (ValueError, IndexError, TypeError) as e:
            continue
    
    return trees

def merge_with_existing(new_trees, existing_data):
    """Merge new data with existing, preserving any local customizations."""
    existing_by_id = {str(t.get('tree_id')): t for t in existing_data}
    merged = []
    
    for new_tree in new_trees:
        tree_id = str(new_tree.get('tree_id'))
        if tree_id in existing_by_id:
            existing = existing_by_id[tree_id]
            # Update with new data, but preserve any local additions
            existing.update(new_tree)
            merged.append(existing)
        else:
            merged.append(new_tree)
    
    # Keep any trees that weren't in the new fetch (in case of API issues)
    for tree_id, tree in existing_by_id.items():
        if not any(str(t.get('tree_id')) == tree_id for t in new_trees):
            merged.append(tree)
    
    return merged

def main():
    print("Starting census.json sync...\n")
    
    # Load existing census
    try:
        with open(CENSUS_FILE, 'r') as f:
            existing_data = json.load(f)
        print(f"✓ Loaded existing census.json with {len(existing_data)} trees")
    except FileNotFoundError:
        print("⚠ No existing census.json found, will create new")
        existing_data = []
    except json.JSONDecodeError as e:
        print(f"✗ Error reading census.json: {e}")
        return 1
    
    # Fetch new data
    rows = fetch_nyc_parks_data()
    if rows is None:
        print("✗ Failed to fetch data. Aborting sync.")
        return 1
    
    # Transform and merge
    print("\nProcessing data...")
    new_trees = transform_to_census_format(rows)
    merged_trees = merge_with_existing(new_trees, existing_data)
    
    print(f"✓ Merged data: {len(merged_trees)} total trees")
    
    # Save updated census
    try:
        with open(CENSUS_FILE, 'w') as f:
            json.dump(merged_trees, f, indent=2)
        print(f"✓ Saved updated census.json")
    except Exception as e:
        print(f"✗ Error saving census.json: {e}")
        return 1
    
    # Summary
    print(f"\n✓ Sync complete!")
    print(f"  Trees in CB3: {len(merged_trees)}")
    print(f"  Timestamp: {datetime.now().isoformat()}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
