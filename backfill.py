"""
LES Ecology Center — Historical Activity Backfill
==================================================
One-time script that fetches ALL historical stewardship activities for group 14
from the NYC Tree Map GraphQL API and writes a complete data/activities.csv.

Unlike the daily scraper (which appends incrementally), this script:
  - Pages through the full activity history using offset-based pagination
  - Falls back to the single-shot high-limit query if pagination returns nothing
  - Overwrites data/activities.csv with a fully sorted, deduplicated dataset

Run manually via GitHub Actions (workflow_dispatch in backfill.yml), or
locally once network access to tree-map.nycgovparks.org is available.
"""

import csv
import os
import sys
import time
import requests
from datetime import datetime

GROUP_ID    = 14
API_URL     = "https://www.nycgovparks.org/api-treemap/graphql"
OUTPUT_FILE = "data/activities.csv"
FIELDNAMES  = ["id", "date", "treeId", "species", "address",
               "activitiesDone", "durationMinutes", "scrapedAt"]

# Page size for offset pagination. The NYC Tree Map frontend uses 5–20;
# a larger value reduces round trips but stay well under any server limit.
PAGE_SIZE = 200
# Hard cap: stop after this many pages to avoid infinite loops.
MAX_PAGES = 500

HEADERS = {
    "Content-Type":     "application/json",
    "User-Agent":       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept":           "application/json, text/plain, */*",
    "Accept-Language":  "en-US,en;q=0.9",
    "Referer":          "https://tree-map.nycgovparks.org/tree-map/group/14",
    "Origin":           "https://tree-map.nycgovparks.org",
    "sec-ch-ua":        '"Google Chrome";v="123", "Not:A-Brand";v="8"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest":   "empty",
    "Sec-Fetch-Mode":   "cors",
    "Sec-Fetch-Site":   "same-site",
}

# ── Query A: paginated activityReports (supports offset) ──────────────────────
PAGINATED_QUERY = """
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

# ── Query B: single-shot high-limit (current daily scraper approach) ──────────
HIGH_LIMIT_QUERY = """
query activitiesAndUser($id: Int!) {
  treeGroupById(id: $id) {
    id
    recentActivities(limit: 100000) {
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


def make_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    print("  Visiting group page to establish session cookies...")
    session.get(
        f"https://tree-map.nycgovparks.org/tree-map/group/{GROUP_ID}",
        timeout=30,
    )
    return session


def row_from_record(r, scraped_at):
    """Convert a raw GraphQL activity record to a CSV row dict."""
    if r is None:
        return None
    tree    = r.get("tree") or {}
    species = tree.get("species") or {}
    return {
        "id":              str(r.get("id", "")),
        "date":            format_date(r.get("date")),
        "treeId":          str(r.get("treeId", "")),
        "species":         species.get("commonName", ""),
        "address":         tree.get("closestAddress", ""),
        "activitiesDone":  "; ".join(r.get("stewardshipActivities") or []),
        "durationMinutes": r.get("duration", ""),
        "scrapedAt":       scraped_at,
    }


# ── Strategy A: offset pagination via activityReports ─────────────────────────

def fetch_page_paginated(session, offset, scraped_at):
    """Fetch one page using the paginated activityReports query."""
    payload = {
        "operationName": "GroupActivityReports",
        "query":         PAGINATED_QUERY,
        "variables":     {"groupId": GROUP_ID, "limit": PAGE_SIZE, "offset": offset},
    }
    resp = session.post(API_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "errors" in data and not data.get("data"):
        raise RuntimeError(f"GraphQL errors: {data['errors']}")

    rows = (data.get("data") or {}).get("activityReports") or []
    return [row_from_record(r, scraped_at) for r in rows if r is not None]


def backfill_paginated(session, scraped_at):
    """Page through activityReports until exhausted. Returns list of row dicts."""
    all_rows = []
    for page in range(MAX_PAGES):
        offset = page * PAGE_SIZE
        print(f"  [paginated] page {page + 1}, offset {offset}…", flush=True)
        try:
            rows = fetch_page_paginated(session, offset, scraped_at)
        except Exception as exc:
            print(f"  [paginated] error at offset {offset}: {exc}")
            if page == 0:
                return None   # Signal: this strategy isn't available
            break

        all_rows.extend(rows)
        print(f"    → {len(rows)} records (cumulative: {len(all_rows)})")

        if len(rows) < PAGE_SIZE:
            print("  [paginated] reached last page.")
            break

        # Brief pause to avoid hammering the server
        time.sleep(0.5)

    return all_rows


# ── Strategy B: single high-limit query via recentActivities ──────────────────

def backfill_high_limit(session, scraped_at):
    """Fetch everything in one shot using a very high limit."""
    print("  [high-limit] querying recentActivities(limit=100000)…", flush=True)
    payload = {
        "operationName": "activitiesAndUser",
        "variables":     {"id": GROUP_ID},
        "query":         HIGH_LIMIT_QUERY,
    }
    resp = session.post(API_URL, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    if "errors" in data:
        null_count = len(data["errors"])
        print(f"  [high-limit] {null_count} activities skipped (deleted trees)")

    rows = ((data.get("data") or {})
                .get("treeGroupById") or {})
    rows = rows.get("recentActivities") or []

    result = [row_from_record(r, scraped_at) for r in rows if r is not None]
    print(f"  [high-limit] received {len(result)} records")
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def write_csv(rows):
    """Write rows to CSV, sorted by date then id. Returns count written."""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    def sort_key(r):
        return (r.get("date") or "0000-00-00", r.get("id") or "")

    rows_sorted = sorted(rows, key=sort_key)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows_sorted)
    return len(rows_sorted)


if __name__ == "__main__":
    print(f"Backfilling all historical activities for NYC Tree Map group {GROUP_ID}…")
    scraped_at = datetime.now().strftime("%Y-%m-%d")

    try:
        session = make_session()

        # ── Try Strategy A (paginated) first ──────────────────────────────────
        print("\nStrategy A: offset-based pagination via activityReports…")
        rows = backfill_paginated(session, scraped_at)

        if rows is None:
            print("  activityReports query not available — falling back to Strategy B.")
            rows = []

        # ── If paginated returned nothing, try Strategy B ─────────────────────
        if not rows:
            print("\nStrategy B: single high-limit query via recentActivities…")
            rows = backfill_high_limit(session, scraped_at)

        # ── If both strategies returned results, merge and deduplicate ─────────
        if rows:
            # Deduplicate by activity ID (keep last-seen for each id)
            seen = {}
            for r in rows:
                if r and r.get("id"):
                    seen[r["id"]] = r
            deduped = list(seen.values())
            print(f"\nTotal unique activities after dedup: {len(deduped)}")

            count = write_csv(deduped)
            print(f"Wrote {count} rows to {OUTPUT_FILE} (sorted by date).")
        else:
            print("\nNo activities returned by either strategy.")
            sys.exit(1)

    except Exception as exc:
        print(f"\nFatal error: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
