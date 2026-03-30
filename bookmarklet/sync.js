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

  // ── Status bubble ─────────────────────────────────────────────────────────
  var bubble = document.getElementById('_treeSync');
  if (!bubble) {
    bubble = document.createElement('div');
    bubble.id = '_treeSync';
    bubble.style.cssText = [
      'position:fixed', 'top:20px', 'right:20px', 'z-index:2147483647',
      'padding:14px 20px', 'border-radius:10px', 'font:bold 14px/1.5 sans-serif',
      'color:#fff', 'box-shadow:0 4px 16px rgba(0,0,0,0.3)', 'max-width:360px',
      'white-space:pre-line'
    ].join(';');
    document.body.appendChild(bubble);
  }

  function status(msg, color, persist) {
    bubble.textContent = msg;
    bubble.style.background = color || '#2e7d32';
    if (!persist) setTimeout(function () { bubble.remove(); }, 8000);
  }

  status('⏳ Syncing…', '#1565c0', true);

  // ── GitHub token ──────────────────────────────────────────────────────────
  var token = localStorage.getItem('_treeSync_token');
  if (!token) {
    token = prompt(
      'One-time setup: enter your GitHub personal access token.\n\n' +
      'To create one:\n' +
      '1. github.com → profile photo → Settings\n' +
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

  // ── Read activities from Apollo InMemoryCache ─────────────────────────────
  function readFromApolloCache() {
    var debug = [];

    // Try several common Apollo client variable names
    var client = window.__APOLLO_CLIENT__ || window.apolloClient || window.apollo;
    if (!client) {
      debug.push('No Apollo client found on window');
      return { activities: null, debug: debug };
    }
    debug.push('Apollo client found');

    var cache;
    try { cache = client.cache.extract(); } catch(e) {
      debug.push('cache.extract() failed: ' + e.message);
      return { activities: null, debug: debug };
    }

    var keys = Object.keys(cache);
    debug.push('Cache keys: ' + keys.length);

    // Collect unique __typename values to help diagnose structure
    var types = {};
    keys.forEach(function(k) {
      var t = (cache[k] || {}).__typename;
      if (t) types[t] = (types[t] || 0) + 1;
    });
    debug.push('Types: ' + JSON.stringify(types));

    // Find activity records — try multiple typename patterns
    var activities = [];
    keys.forEach(function(key) {
      var obj = cache[key];
      if (!obj || !obj.id) return;
      var type = (obj.__typename || '').toLowerCase();
      var looksLikeActivity = (
        type.includes('activity') ||
        type.includes('stewardship') ||
        type.includes('report') ||
        (obj.stewardshipActivities !== undefined && obj.treeId !== undefined) ||
        (obj.stewardshipActivities !== undefined && obj.date !== undefined)
      );
      if (!looksLikeActivity) return;

      // Dereference tree and species __ref links
      var tree = obj.tree;
      if (tree && tree.__ref) tree = cache[tree.__ref] || tree;
      var species = tree && tree.species;
      if (species && species.__ref) species = cache[species.__ref] || species;
      if (tree) tree = Object.assign({}, tree, { species: species || {} });

      activities.push(Object.assign({}, obj, { tree: tree || {} }));
    });

    debug.push('Activities found in cache: ' + activities.length);
    return { activities: activities.length > 0 ? activities : null, debug: debug };
  }

  // ── GraphQL API fallback ──────────────────────────────────────────────────
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
    }).then(function(r) { return r.json(); });
  }

  function fetchFromAPI() {
    return gql(PAGINATED_QUERY, { groupId: GROUP_ID, limit: 200, offset: 0 })
      .then(function(resp) {
        var rows = (resp.data || {}).activityReports;
        if (rows && rows.length > 0) return rows;
        throw new Error('paginated unavailable');
      })
      .catch(function() {
        return gql(HIGH_LIMIT_QUERY, { id: GROUP_ID }).then(function(resp) {
          return ((resp.data || {}).treeGroupById || {}).recentActivities || [];
        });
      });
  }

  // ── Format one activity as a CSV row ──────────────────────────────────────
  var TODAY = new Date().toISOString().slice(0, 10);

  function toRow(r) {
    if (!r) return null;
    var date = '';
    if (r.date) {
      try { date = new Date(+r.date).toISOString().slice(0, 10); }
      catch(e) { date = String(r.date).slice(0, 10); }
    }
    var tree    = r.tree || {};
    var species = (tree.species || {}).commonName || '';
    var address = tree.closestAddress || '';
    // stewardshipActivities may be an array or a JSON string in the cache
    var acts = r.stewardshipActivities || [];
    if (typeof acts === 'string') { try { acts = JSON.parse(acts); } catch(e) { acts = [acts]; } }
    var actsStr = Array.isArray(acts) ? acts.join('; ') : String(acts);
    var fields = [r.id, date, r.treeId || '', species, address, actsStr, r.duration || '', TODAY];
    return fields.map(function(f) {
      f = String(f == null ? '' : f);
      return /[,"\n]/.test(f) ? '"' + f.replace(/"/g, '""') + '"' : f;
    }).join(',');
  }

  // ── Main ──────────────────────────────────────────────────────────────────
  var cacheResult = readFromApolloCache();
  var debugLines  = cacheResult.debug;

  var activitiesPromise = cacheResult.activities
    ? Promise.resolve(cacheResult.activities)
    : fetchFromAPI().then(function(rows) {
        debugLines.push('API returned: ' + rows.length);
        return rows;
      });

  Promise.all([
    fetch('https://api.github.com/repos/' + REPO + '/contents/' + CSV_PATH, { headers: ghHeaders })
      .then(function(r) { return r.json(); }).catch(function() { return null; }),
    activitiesPromise
  ]).then(function(results) {
    var ghFile  = results[0];
    var rawRows = results[1];

    debugLines.push('Total fetched: ' + rawRows.length);

    // Decode existing CSV
    var existing = 'id,date,treeId,species,address,activitiesDone,durationMinutes,scrapedAt\n';
    var sha = null;
    if (ghFile && ghFile.content) {
      existing = atob(ghFile.content.replace(/\s/g, ''));
      sha = ghFile.sha;
    }

    var seenIds = {};
    existing.split('\n').slice(1).forEach(function(line) {
      var id = line.split(',')[0].trim();
      if (id) seenIds[id] = true;
    });
    debugLines.push('Already in CSV: ' + Object.keys(seenIds).length);

    var newLines = [];
    rawRows.forEach(function(r) {
      var id = String(r && r.id || '');
      if (!id || seenIds[id]) return;
      var row = toRow(r);
      if (row) { newLines.push(row); seenIds[id] = true; }
    });
    debugLines.push('New to add: ' + newLines.length);

    if (newLines.length === 0) {
      status('ℹ️ Nothing new.\n\n' + debugLines.join('\n'), '#555', true);
      return;
    }

    var updated = existing.trimEnd() + '\n' + newLines.join('\n') + '\n';
    var body = {
      message: 'Sync ' + TODAY + ' (+' + newLines.length + ')',
      content: btoa(unescape(encodeURIComponent(updated)))
    };
    if (sha) body.sha = sha;

    return fetch('https://api.github.com/repos/' + REPO + '/contents/' + CSV_PATH, {
      method: 'PUT',
      headers: Object.assign({ 'Content-Type': 'application/json' }, ghHeaders),
      body: JSON.stringify(body)
    }).then(function(r) {
      if (!r.ok) throw new Error('GitHub push failed: HTTP ' + r.status);
      status('✅ ' + newLines.length + ' activities synced!', '#2e7d32');
    });

  }).catch(function(err) {
    if (String(err).includes('401') || String(err).includes('403')) {
      localStorage.removeItem('_treeSync_token');
    }
    status('❌ ' + err.message + '\n\n' + debugLines.join('\n'), '#c62828', true);
  });

})();
