/**
 * NYC Tree Map GraphQL Proxy — Google Apps Script
 * ================================================
 * Proxies requests to the NYC Tree Map API so the dashboard can fetch
 * stewardship activities from the user's browser without CORS issues
 * or IP blocking.
 *
 * SETUP:
 *   1. Go to https://script.google.com → New Project
 *   2. Replace the contents of Code.gs with this entire file
 *   3. Click Deploy → New deployment
 *   4. Type: Web app
 *   5. Execute as: Me
 *   6. Who has access: Anyone
 *   7. Click Deploy, authorize when prompted, and copy the URL
 *   8. Paste the URL into the dashboard where indicated
 *
 * REDEPLOYING AFTER UPDATES:
 *   Go to Deploy → Manage deployments → edit the existing deployment
 *   and set Version to "New version", then click Deploy.
 */

var GROUP_ID  = 14;
var API_URL   = "https://www.nycgovparks.org/api-treemap/graphql";
var PAGE_SIZE = 200;   // activities per page for paginated strategy
var MAX_PAGES = 500;   // safety cap — 500 × 200 = up to 100,000 activities

// ── Strategy A: paginated via activityReports ─────────────────────────────────
var PAGINATED_QUERY = '\
query GroupActivityReports($groupId: Int!, $limit: Int!, $offset: Int!) {\
  activityReports(groupId: $groupId, limit: $limit, offset: $offset) {\
    id\
    date\
    treeId\
    duration\
    stewardshipActivities\
    tree {\
      closestAddress\
      species {\
        commonName\
      }\
    }\
  }\
}';

// ── Strategy B: single high-limit via recentActivities ────────────────────────
var HIGH_LIMIT_QUERY = '\
query activitiesAndUser($id: Int!) {\
  treeGroupById(id: $id) {\
    id\
    recentActivities(limit: 100000) {\
      id\
      duration\
      treeId\
      date\
      stewardshipActivities\
      tree {\
        id\
        closestAddress\
        species {\
          commonName\
        }\
      }\
    }\
  }\
}';

function makeHeaders(groupId) {
  return {
    "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept":        "application/json, text/plain, */*",
    "Referer":       "https://tree-map.nycgovparks.org/tree-map/group/" + groupId,
    "Origin":        "https://tree-map.nycgovparks.org"
  };
}

function rowFromRecord(r) {
  if (!r) return null;
  var tree    = r.tree || {};
  var species = tree.species || {};
  return {
    id:              String(r.id || ""),
    date:            formatDate(r.date),
    treeId:          String(r.treeId || ""),
    species:         species.commonName || "",
    address:         tree.closestAddress || "",
    activitiesDone:  (r.stewardshipActivities || []).join("; "),
    durationMinutes: r.duration || ""
  };
}

// ── Strategy A: page through activityReports ──────────────────────────────────
function fetchAllPaginated(groupId) {
  var allRows = [];
  var headers = makeHeaders(groupId);

  for (var page = 0; page < MAX_PAGES; page++) {
    var offset = page * PAGE_SIZE;
    var payload = {
      operationName: "GroupActivityReports",
      query: PAGINATED_QUERY,
      variables: { groupId: groupId, limit: PAGE_SIZE, offset: offset }
    };
    var options = {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify(payload),
      headers: headers,
      muteHttpExceptions: true
    };

    var resp = UrlFetchApp.fetch(API_URL, options);
    if (resp.getResponseCode() !== 200) {
      Logger.log("Paginated: HTTP " + resp.getResponseCode() + " at offset " + offset);
      return null; // signal: strategy not available
    }

    var data = JSON.parse(resp.getContentText());

    // If the query itself isn't supported, the API returns errors with no data
    if (data.errors && !data.data) {
      Logger.log("Paginated: GraphQL errors at offset " + offset + " — strategy unavailable");
      return null;
    }

    var rows = (data.data || {}).activityReports || [];
    Logger.log("Paginated page " + (page + 1) + ": " + rows.length + " records");

    for (var i = 0; i < rows.length; i++) {
      var row = rowFromRecord(rows[i]);
      if (row) allRows.push(row);
    }

    if (rows.length < PAGE_SIZE) break; // last page
    Utilities.sleep(300); // brief pause between pages
  }

  return allRows;
}

// ── Strategy B: single high-limit query ───────────────────────────────────────
function fetchHighLimit(groupId) {
  var payload = {
    operationName: "activitiesAndUser",
    variables: { id: groupId },
    query: HIGH_LIMIT_QUERY
  };
  var options = {
    method: "post",
    contentType: "application/json",
    payload: JSON.stringify(payload),
    headers: makeHeaders(groupId),
    muteHttpExceptions: true
  };

  var resp = UrlFetchApp.fetch(API_URL, options);
  var code = resp.getResponseCode();
  if (code !== 200) throw new Error("API returned HTTP " + code);

  var data = JSON.parse(resp.getContentText());
  var raw = ((data.data || {}).treeGroupById || {}).recentActivities || [];

  Logger.log("High-limit: " + raw.length + " records");

  var rows = [];
  for (var i = 0; i < raw.length; i++) {
    var row = rowFromRecord(raw[i]);
    if (row) rows.push(row);
  }
  return rows;
}

// ── Main handler ──────────────────────────────────────────────────────────────
function doGet(e) {
  try {
    var groupId = (e && e.parameter && e.parameter.groupId)
      ? parseInt(e.parameter.groupId)
      : GROUP_ID;

    // Warm up the session
    UrlFetchApp.fetch(
      "https://tree-map.nycgovparks.org/tree-map/group/" + groupId,
      { muteHttpExceptions: true, followRedirects: true }
    );

    var rows = null;
    var strategy = "";

    // Try Strategy A first
    Logger.log("Trying Strategy A: paginated activityReports...");
    rows = fetchAllPaginated(groupId);
    if (rows && rows.length > 0) {
      strategy = "paginated";
      Logger.log("Strategy A succeeded: " + rows.length + " total records");
    } else {
      // Fall back to Strategy B
      Logger.log("Strategy A unavailable. Trying Strategy B: high-limit recentActivities...");
      rows = fetchHighLimit(groupId);
      strategy = "high-limit";
    }

    // Deduplicate by id
    var seen = {};
    var deduped = [];
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      if (r.id && !seen[r.id]) {
        seen[r.id] = true;
        deduped.push(r);
      }
    }

    var result = {
      groupId:    groupId,
      count:      deduped.length,
      strategy:   strategy,
      activities: deduped
    };

    Logger.log("Returning " + deduped.length + " activities via " + strategy);

    return ContentService
      .createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    Logger.log("Error: " + err.message);
    return ContentService
      .createTextOutput(JSON.stringify({ error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function formatDate(ts) {
  if (!ts) return "";
  try {
    var d = new Date(typeof ts === "number" ? ts : parseInt(ts));
    if (isNaN(d.getTime())) return String(ts).substring(0, 10);
    return Utilities.formatDate(d, "America/New_York", "yyyy-MM-dd");
  } catch (e) {
    return String(ts).substring(0, 10);
  }
}
