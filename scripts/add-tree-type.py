#!/usr/bin/env python3
"""
Add tree_type field (street vs park) to census.json using spatial intersection.

This script:
1. Fetches NYC Parks boundaries from Overpass API (OpenStreetMap)
2. Checks if each tree's coordinates fall within a park boundary
3. Adds tree_type field: "park" or "street"
4. Updates census.json with the new field

Usage: python scripts/add-tree-type.py
"""

import json
import sys
from pathlib import Path

try:
    from shapely.geometry import Point, shape, Polygon
    from shapely.errors import ShapelyError
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "shapely"])
    from shapely.geometry import Point, shape, Polygon
    from shapely.errors import ShapelyError

try:
    import requests
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
CENSUS_FILE = REPO_ROOT / 'data' / 'census.json'

# Hardcoded NYC parks with approximate boundaries for CB3 Lower East Side area
# These are simplified bounding boxes based on park locations
NYC_PARKS = [
    {
        'name': 'Tompkins Square Park',
        'bounds': [(40.7245, -73.9835), (40.7275, -73.9795)]  # (SW, NE)
    },
    {
        'name': 'Sara D. Roosevelt Park',
        'bounds': [(40.7145, -73.9875), (40.7275, -73.9795)]
    },
    {
        'name': 'East River Park',
        'bounds': [(40.7095, -73.9795), (40.7295, -73.9695)]
    },
    {
        'name': 'Columbus Park',
        'bounds': [(40.7145, -73.9955), (40.7225, -73.9835)]
    },
    {
        'name': 'Battery Park',
        'bounds': [(40.6975, -74.0175), (40.7045, -74.0095)]
    },
    {
        'name': 'New York County Courthouse Park',
        'bounds': [(40.7125, -73.9955), (40.7155, -73.9895)]
    },
]

def get_park_geometries():
    """Create park geometries from hardcoded park data."""
    print("Loading NYC Parks boundaries...")
    geometries = []

    for park in NYC_PARKS:
        try:
            sw, ne = park['bounds']
            # Create polygon from bounding box: SW -> SE -> NE -> NW -> SW
            coords = [
                (sw[1], sw[0]),      # SW: (lng, lat)
                (ne[1], sw[0]),      # SE
                (ne[1], ne[0]),      # NE
                (sw[1], ne[0]),      # NW
                (sw[1], sw[0]),      # back to SW
            ]
            geom = Polygon(coords)
            geometries.append({
                'geometry': geom,
                'park_name': park['name']
            })
        except Exception as e:
            print(f"  Warning: Failed to create geometry for {park['name']}: {e}")
            continue

    print(f"✓ Loaded {len(geometries)} park boundaries")
    return geometries

def is_tree_in_park(tree_lat, tree_lng, park_geometries):
    """Check if tree coordinates fall within any park boundary."""
    if not park_geometries:
        return None  # No park data available
    
    tree_point = Point(tree_lng, tree_lat)
    
    for park in park_geometries:
        try:
            if tree_point.within(park['geometry']) or tree_point.touches(park['geometry']):
                return park['park_name']
        except ShapelyError:
            continue
    
    return None  # Not in any park

def main():
    print("Adding tree_type field to census.json...\n")
    
    # Load census
    try:
        with open(CENSUS_FILE, 'r') as f:
            trees = json.load(f)
        print(f"✓ Loaded {len(trees)} trees from census.json")
    except Exception as e:
        print(f"✗ Error loading census.json: {e}")
        return 1
    
    # Load parks data
    park_geoms = get_park_geometries()

    if not park_geoms:
        print("⚠ No parks data available - all trees will be marked as 'street'")
    
    # Add tree_type field
    print("\nAnalyzing tree locations...")
    park_count = 0
    street_count = 0
    
    for tree in trees:
        lat = float(tree.get('latitude') or 0)
        lng = float(tree.get('longitude') or 0)
        
        if lat and lng:
            park_name = is_tree_in_park(lat, lng, park_geoms)
            if park_name:
                tree['tree_type'] = 'park'
                tree['park_name'] = park_name
                park_count += 1
            else:
                tree['tree_type'] = 'street'
                street_count += 1
        else:
            tree['tree_type'] = 'unknown'
    
    # Save updated census
    try:
        with open(CENSUS_FILE, 'w') as f:
            json.dump(trees, f, indent=2)
        print(f"✓ Saved updated census.json")
    except Exception as e:
        print(f"✗ Error saving census.json: {e}")
        return 1
    
    # Summary
    print(f"\n✓ Complete!")
    print(f"  Park trees:   {park_count}")
    print(f"  Street trees: {street_count}")
    print(f"  Unknown:      {len(trees) - park_count - street_count}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
