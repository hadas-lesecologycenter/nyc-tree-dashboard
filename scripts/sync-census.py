#!/usr/bin/env python3
"""
Sync census.json with live NYC Parks tree data.

This script calls fetch_census.py to:
- Fetch Forestry Tree Points (live operational DB)
- Fetch Forestry Planting Spaces (for tree_type classification)
- Join by PlantingSpaceGlobalID
- Add tree_type field from pssite (Street/Park indicator)
- Update census.json with authoritative data

Run this periodically (e.g., monthly) via GitHub Actions.
"""

import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

def main():
    print("Starting census.json sync...\n")

    # Call fetch_census.py to handle all the data fetching and processing
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / 'fetch_census.py')],
        capture_output=False
    )

    return result.returncode

if __name__ == '__main__':
    sys.exit(main())
