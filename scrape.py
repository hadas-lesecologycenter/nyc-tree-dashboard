"""
LES Ecology Center — Daily Tree Activity Scraper
=================================================
Fetches activities from the NYC Tree Map GraphQL API for group 14
and appends any new ones to data/activities.csv.

Runs daily via GitHub Actions.
"""

import csv
import json
import os
import requests
from datetime import datetime

GROUP_ID     = 14
API_URL      = "https://www.nycgovparks.org/api-treemap/graphql"
OUTPUT_FILE  = "data/activities.csv"
FIELDNAMES   = ["id", "date", "treeId", "species", "address", "activitiesDone", "durationMinutes", "scrapedAt"]
PAGE_SIZE    = 50   # activities per request
MAX_PAGES    = 20   # safety cap: fetches up to 1,000 activities per run

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer":      "https://tree-map.nycgovparks.org/",
    "Origin":       "https://tree-map.nycgovparks.org",
}

# GraphQL query for a page of activity reports for a group
ACTIVITY_QUERY = """
query GroupActivityReports($groupId: Int!, $limit: Int!, $offset: Int!) {
  activityReports(groupId: $groupId, limit: $limit, offset: $offset) {
    id
    date
    treeId
    duration
    stewardshipActivities
    tree {
      closestAddress
      species {
        commonName
      }
    }
  }
}
"""

def format_date(ts):
    if not ts:
        return ""
    try:
        if isinstance(ts, (int, float)):
            return datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d")
        return str(ts)[:10]
    except Exception:
        return str(ts)

def fetch_page(offset):
    """Fetch one page of activity reports from the GraphQL API."""
    payload = {
        "query":     ACTIVITY_QUERY,
        "variables": {"groupId": GROUP_ID, "limit": PAGE_SIZE, "offset": offset},
    }
    resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")
    return data.get("data", {}).get("activityReports", [])

def fetch_all_activities():
    """Page through the API until we run out of results or hit MAX_PAGES."""
    all_activities = []
    scraped_at = datetime.now().strftime("%Y-%m-%d")

    for page in range(MAX_PAGES):
        offset = page * PAGE_SIZE
        print(f"  Fetching page {page + 1} (offset {offset})...")
        rows = fetch_page(offset)
        if not rows:
            print(f"  No more results at offset {offset}.")
            break

        for r in rows:
            tree    = r.get("tree") or {}
            species = tree.get("species") or {}
            all_activities.append({
                "id":              r.get("id", ""),
                "date":            format_date(r.get("date")),
                "treeId":          r.get("treeId", ""),
                "species":         species.get("commonName", ""),
                "address":         tree.get("closestAddress", ""),
                "activitiesDone":  "; ".join(r.get("stewardshipActivities") or []),
                "durationMinutes": r.get("duration", ""),
                "scrapedAt":       scraped_at,
            })

        if len(rows) < PAGE_SIZE:
            # Last page — no need to fetch further
            break

    return all_activities

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
    print(f"Scraping NYC Tree Map group {GROUP_ID} via GraphQL API...")

    try:
        activities = fetch_all_activities()
        print(f"Found {len(activities)} activities from API")

        existing_ids = load_existing_ids()
        print(f"Existing records in CSV: {len(existing_ids)}")

        added = append_new_activities(activities, existing_ids)
        total = count_total()

        print(f"New activities added: {added}")
        print(f"Total activities in CSV: {total}")

        if added == 0:
            print("No new activities since last run.")
        else:
            print(f"Successfully added {added} new activities!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
