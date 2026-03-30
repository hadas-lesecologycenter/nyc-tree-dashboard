/**
 * NYC Tree Map → GitHub Sync Bookmarklet
 * =======================================
 * Loaded by the bookmarklet when clicked on the NYC Tree Map page.
 * Fetches all group activities and pushes them to data/activities.csv on GitHub.
 */
(function () {
  'use strict';

  var REPO     = 'hadas-lesecologycenter/nyc-tree-dashboard';
  var CSV_PATH = 'data/activities.csv';
  var GROUP_ID = 14;

  // ── Guard: must be on the NYC Tree Map site ──────────────────────────────
  if (!location.hostname.includes('nycgovparks.org')) {
    alert('Please open this page first, then click the bookmark:\nhttps://tree-map.nycgovparks.org/tree-map/group/' + GROUP_ID);
    return;
  }

  // ── Status bubble ────────────────────────────────────────────────────────
  var bubble = document.getElementById('_treeSync');
  if (!bubble) {
    bubble = document.createElement('div');
    bubble.id = '_treeSync';
    bubble.style.cssText = [
      'position:fixed', 'top:20px', 'right:20px', 'z-index:2147483647',
      'padding:14px 20px', 'border-radius:10px', 'font:bold 14px/1.5 sans-serif',
      'color:#fff', 'box-shadow:0 4px 16px rgba(0,0,0,0.3)', 'max-width:320px'
    ].join(';');
    document.body.appendChild(bubble);
  }

  function status(msg, color, persist) {
    bubble.textContent = msg;
    bubble.style.background = color || '#2e7d32';
    if (!persist) setTimeout(function () { bubble.remove(); }, 5000);
  }

  status('⏳ Syncing…', '#1565c0', true);

  // ── GitHub token ─────────────────────────────────────────────────────────
  var token = localStorage.getItem('_treeSync_token');
  if (!token) {
    token = prompt(
      'One-time setup: enter your GitHub personal access token.\n\n' +
      'To create one:\n' +
      '1. Go to github.com → profile photo → Settings\n' +
      '2. Developer settings → Personal access tokens → Tokens (classic)\n' +
      '3. Generate new token → check "repo" → Generate\n\n' +
      'Token (starts with ghp_):'
    );
    if (!token) { bubble.remove(); return; }
    token = token.trim();
    localStorage.setItem('_treeSync_token', token);
  }

  var ghHeaders = {
    'Authorization': 'token ' + token,
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'nyc-tree-bookmarklet'
  };

  // ── Read activities already loaded in the page (Apollo cache) ───────────────
  function readFromApolloCache() {
    try {
      var client = window.__APOLLO_CLIENT__;
      if (!client) return null;
      var cache = client.cache.extract();
      if (!cache) return null;

      // Collect all Activity-shaped objects from the cache
      var activities = [];
      Object.keys(cache).forEach(function (key) {
        var obj = cache[key];
        // Activity records have id, date, treeId, stewardshipActivities
        if (obj && obj.id && obj.date && obj.stewardshipActivities) {
          activities.push(obj);
        }
      });

      if (activities.length === 0) return null;
      console.log('[TreeSync] Apollo cache: found ' + activities.length + ' activities');
      return activities;
    } catch (e) {
      console.warn('[TreeSync] Apollo cache read failed:', e.message);
      return null;
    }
  }

  // ── GraphQL queries (fallback when cache is unavailable) ─────────────────────
  var PAGINATED_QUERY = [
    'query GroupActivityReports($groupId:Int!,$limit:Int!,$offset:Int!){',
    '  activityReports(groupId:$groupId,limit:$limit,offset:$offset){',
    '    id date treeId duration stewardshipActivities',
    '    tree{closestAddress species{commonName}}',
    '  }',
    '}'
  ].join('');

  var HIGH_LIMIT_QUERY = [
    'query activitiesAndUser($id:Int!){',
    '  treeGroupById(id:$id){',
    '    recentActivities(limit:100000){',
    '      id date treeId duration stewardshipActivities',
    '      tree{closestAddress species{commonName}}',
    '    }',
    '  }',
    '}'
  ].join('');

  function gql(query, variables) {
    return fetch('https://www.nycgovparks.org/api-treemap/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query, variables: variables })
    }).then(function (r) { return r.json(); });
  }

  // ── Fetch all activities (API fallback) ───────────────────────────────────
  function fetchActivities() {
    var PAGE = 200;
    var allRows = [];
    var page = 0;

    function nextPage() {
      return gql(PAGINATED_QUERY, { groupId: GROUP_ID, limit: PAGE, offset: page * PAGE })
        .then(function (resp) {
          var rows = (resp.data || {}).activityReports || [];
          if (resp.errors && !resp.data) throw new Error('paginated_unavailable');
          allRows = allRows.concat(rows);
          if (rows.length === PAGE && page < 499) {
            page++;
            return nextPage();
          }
          return allRows;
        });
    }

    return nextPage().catch(function () {
      // Fall back to high-limit single query
      return gql(HIGH_LIMIT_QUERY, { id: GROUP_ID }).then(function (resp) {
        return ((resp.data || {}).treeGroupById || {}).recentActivities || [];
      });
    });
  }

  // ── Format one activity as a CSV row ─────────────────────────────────────
  var TODAY = new Date().toISOString().slice(0, 10);

  function toRow(r) {
    if (!r) return null;
    var date = '';
    if (r.date) {
      try { date = new Date(+r.date).toISOString().slice(0, 10); }
      catch (e) { date = String(r.date).slice(0, 10); }
    }
    var tree    = r.tree || {};
    var species = (tree.species || {}).commonName || '';
    var address = tree.closestAddress || '';
    var acts    = (r.stewardshipActivities || []).join('; ');
    var fields  = [r.id, date, r.treeId || '', species, address, acts, r.duration || '', TODAY];
    return fields.map(function (f) {
      f = String(f == null ? '' : f);
      return /[,"\n]/.test(f) ? '"' + f.replace(/"/g, '""') + '"' : f;
    }).join(',');
  }

  // ── Main sync flow ────────────────────────────────────────────────────────
  // Try Apollo cache first (fastest, most complete), then fall back to API
  var cachedRows = readFromApolloCache();
  var activitiesPromise = cachedRows
    ? Promise.resolve(cachedRows)
    : fetchActivities();

  Promise.all([
    // Load current CSV from GitHub
    fetch('https://api.github.com/repos/' + REPO + '/contents/' + CSV_PATH, { headers: ghHeaders })
      .then(function (r) { return r.json(); })
      .catch(function () { return null; }),
    // Activities from cache or API
    activitiesPromise
  ]).then(function (results) {
    var ghFile    = results[0];
    var rawRows   = results[1];

    status('⏳ Got ' + rawRows.length + ' activities — updating CSV…', '#1565c0', true);

    // Decode existing CSV
    var existing = '';
    var sha      = null;
    if (ghFile && ghFile.content) {
      existing = atob(ghFile.content.replace(/\s/g, ''));
      sha = ghFile.sha;
    } else {
      existing = 'id,date,treeId,species,address,activitiesDone,durationMinutes,scrapedAt\n';
    }

    // Collect existing IDs
    var seenIds = {};
    existing.split('\n').slice(1).forEach(function (line) {
      var id = line.split(',')[0].trim();
      if (id) seenIds[id] = true;
    });

    // Build new rows
    var newLines = [];
    rawRows.forEach(function (r) {
      var id = String(r && r.id || '');
      if (!id || seenIds[id]) return;
      var row = toRow(r);
      if (row) { newLines.push(row); seenIds[id] = true; }
    });

    if (newLines.length === 0) {
      status('✓ Already up to date — nothing new.', '#2e7d32');
      return;
    }

    // Append and push
    var updated = existing.trimEnd() + '\n' + newLines.join('\n') + '\n';
    var body    = {
      message: 'Sync ' + TODAY + ' (+' + newLines.length + ' activities)',
      content: btoa(unescape(encodeURIComponent(updated)))
    };
    if (sha) body.sha = sha;

    return fetch('https://api.github.com/repos/' + REPO + '/contents/' + CSV_PATH, {
      method: 'PUT',
      headers: Object.assign({ 'Content-Type': 'application/json' }, ghHeaders),
      body: JSON.stringify(body)
    }).then(function (r) {
      if (!r.ok) throw new Error('GitHub push failed: HTTP ' + r.status);
      status('✅ ' + newLines.length + ' new activities synced to GitHub!', '#2e7d32');
    });

  }).catch(function (err) {
    // Token might be wrong — clear it so they can re-enter
    if (String(err).includes('401') || String(err).includes('403')) {
      localStorage.removeItem('_treeSync_token');
    }
    status('❌ Error: ' + err.message, '#c62828', true);
  });

})();
