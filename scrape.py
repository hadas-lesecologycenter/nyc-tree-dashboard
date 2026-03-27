"""
LES Ecology Center — Daily Tree Activity Scraper
=================================================
Fetches the most recent activities from the NYC Tree Map group page
and appends any new ones to data/activities.csv.

Runs daily via GitHub Actions.
"""

import csv
import json
import os
import requests
from datetime import datetime

GROUP_ID = 14
GROUP_URL = f"https://tree-map.nycgovparks.org/tree-map/group/{GROUP_ID}"
OUTPUT_FILE = "data/activities.csv"
FIELDNAMES = ["id", "date", "treeId", "species", "address", "activitiesDone", "durationMinutes", "scrapedAt"]

def format_date(ts):
    if not ts:
        return ""
    try:
        if isinstance(ts, (int, float)):
            return datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d")
        return str(ts)[:10]
    except Exception:
        return str(ts)

def resolve_ref(apollo, ref_obj):
    if isinstance(ref_obj, dict) and "__ref" in ref_obj:
        return apollo.get(ref_obj["__ref"], {})
    return ref_obj or {}

def fetch_group_page():
    """Fetch the group page HTML and extract __NEXT_DATA__."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Referer": "https://tree-map.nycgovparks.org/",
    }
    resp = requests.get(GROUP_URL, headers=headers, timeout=30)
    resp.raise_for_status()

    # Extract __NEXT_DATA__ JSON from HTML
    import re
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        resp.text,
        re.DOTALL
    )
    if not match:
        raise Exception("Could not find __NEXT_DATA__ in page")

    return json.loads(match.group(1))

def extract_activities(next_data):
    """Extract ActivityReport entries from Apollo cache."""
    apollo = next_data.get("props", {}).get("pageProps", {}).get("__APOLLO_STATE__", {})
    activities = []
    scraped_at = datetime.utcnow().strftime("%Y-%m-%d")

    for key, value in apollo.items():
        if not key.startswith("ActivityReport:") or not isinstance(value, dict):
            continue
        tree_ref = value.get("tree", {})
        tree = resolve_ref(apollo, tree_ref)
        species_ref = tree.get("species", {})
        species = resolve_ref(apollo, species_ref)

        activities.append({
            "id": value.get("id", ""),
            "date": format_date(value.get("date")),
            "treeId": value.get("treeId", ""),
            "species": species.get("commonName", ""),
            "address": tree.get("closestAddress", ""),
            "activitiesDone": "; ".join(value.get("stewardshipActivities", [])),
            "durationMinutes": value.get("duration", ""),
            "scrapedAt": scraped_at,
        })

    return activities

def load_existing_ids():
    """Load activity IDs already in the CSV to avoid duplicates."""
    if not os.path.exists(OUTPUT_FILE):
        return set()
    with open(OUTPUT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["id"] for row in reader if row.get("id")}

def append_new_activities(new_activities, existing_ids):
    """Append only new activities to the CSV."""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    file_exists = os.path.exists(OUTPUT_FILE)

    added = 0
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        for act in new_activities:
            act_id = str(act.get("id", ""))
            if act_id and act_id not in existing_ids:
                writer.writerow(act)
                existing_ids.add(act_id)
                added += 1

    return added

def count_total():
    if not os.path.exists(OUTPUT_FILE):
        return 0
    with open(OUTPUT_FILE, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))

if __name__ == "__main__":
    print(f"Scraping NYC Tree Map group {GROUP_ID}...")

    try:
        next_data = fetch_group_page()
        activities = extract_activities(next_data)
        print(f"Found {len(activities)} activities on page")

        existing_ids = load_existing_ids()
        print(f"Existing records in CSV: {len(existing_ids)}")

        added = append_new_activities(activities, existing_ids)
        total = count_total()

        print(f"New activities added: {added}")
        print(f"Total activities in CSV: {total}")

        if added == 0:
            print("No new activities today.")
        else:
            print(f"Successfully added {added} new activities!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
