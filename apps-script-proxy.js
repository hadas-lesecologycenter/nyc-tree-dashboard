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
 */

var GROUP_ID = 14;
var API_URL  = "https://www.nycgovparks.org/api-treemap/graphql";

var QUERY = '\
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

function doGet(e) {
  try {
    var groupId = (e && e.parameter && e.parameter.groupId)
      ? parseInt(e.parameter.groupId)
      : GROUP_ID;

    // First visit the group page to establish a normal-looking session
    UrlFetchApp.fetch(
      "https://tree-map.nycgovparks.org/tree-map/group/" + groupId,
      { muteHttpExceptions: true, followRedirects: true }
    );

    // Now query the GraphQL API
    var payload = {
      operationName: "activitiesAndUser",
      variables: { id: groupId },
      query: QUERY
    };

    var options = {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify(payload),
      headers: {
        "User-Agent":       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept":           "application/json, text/plain, */*",
        "Referer":          "https://tree-map.nycgovparks.org/tree-map/group/" + groupId,
        "Origin":           "https://tree-map.nycgovparks.org"
      },
      muteHttpExceptions: true
    };

    var response = UrlFetchApp.fetch(API_URL, options);
    var code = response.getResponseCode();
    var body = response.getContentText();

    if (code !== 200) {
      return ContentService
        .createTextOutput(JSON.stringify({ error: "API returned HTTP " + code, body: body }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // Parse the GraphQL response and flatten into a simple array
    var data = JSON.parse(body);
    var group = (data.data || {}).treeGroupById || {};
    var raw = group.recentActivities || [];

    var activities = [];
    for (var i = 0; i < raw.length; i++) {
      var r = raw[i];
      if (!r) continue;
      var tree    = r.tree || {};
      var species = tree.species || {};
      activities.push({
        id:              r.id || "",
        date:            formatDate(r.date),
        treeId:          r.treeId || "",
        species:         species.commonName || "",
        address:         tree.closestAddress || "",
        activitiesDone:  (r.stewardshipActivities || []).join("; "),
        durationMinutes: r.duration || ""
      });
    }

    var result = {
      groupId:    groupId,
      count:      activities.length,
      activities: activities
    };

    return ContentService
      .createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
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
