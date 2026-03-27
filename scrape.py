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

HEADERS = {
    "Content-Type":  "application/json",
    "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept":        "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":       "https://tree-map.nycgovparks.org/tree-map/group/14",
    "Origin":        "https://tree-map.nycgovparks.org",
    "sec-ch-ua":     '"Google Chrome";v="123", "Not:A-Brand";v="8"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}

# GraphQL query — mirrors the exact query the NYC Tree Map page uses,
# but with a much higher limit to get all activities not just 5.
ACTIVITY_QUERY = """
query activitiesAndUser($id: Int!) {
  treeGroupById(id: $id) {
    id
    recentActivities(limit: 10000) {
      id
      duration
      treeId
      date
      stewardshipActivities
      tree {
        id
        closestAddress
        species {
          commonName
        }
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

def fetch_all_activities():
    """Fetch all activities for the group in a single GraphQL request."""
    scraped_at = datetime.now().strftime("%Y-%m-%d")

    session = requests.Session()
    session.headers.update(HEADERS)

    # Visit the group page first so the server sees a normal browsing session
    # and sets any cookies it expects before we hit the API.
    print("  Visiting group page to establish session...")
    session.get(
        f"https://tree-map.nycgovparks.org/tree-map/group/{GROUP_ID}",
        timeout=30
    )

    payload = {
        "operationName": "activitiesAndUser",
        "variables":     {"id": GROUP_ID},
        "query":         ACTIVITY_QUERY,
    }
    print("  Querying GraphQL API...")
    resp = session.post(API_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")

    rows = (data.get("data", {})
                .get("treeGroupById", {})
                .get("recentActivities", []))

    activities = []
    for r in rows:
        tree    = r.get("tree") or {}
        species = tree.get("species") or {}
        activities.append({
            "id":              r.get("id", ""),
            "date":            format_date(r.get("date")),
            "treeId":          r.get("treeId", ""),
            "species":         species.get("commonName", ""),
            "address":         tree.get("closestAddress", ""),
            "activitiesDone":  "; ".join(r.get("stewardshipActivities") or []),
            "durationMinutes": r.get("duration", ""),
            "scrapedAt":       scraped_at,
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
