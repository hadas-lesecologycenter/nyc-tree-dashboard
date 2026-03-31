/**
 * NYC Tree Map → GitHub Sync Bookmarklet
 * Fetches group activities + tree coordinates and pushes to GitHub.
 */
(function () {
  'use strict';

  var REPO       = 'hadas-lesecologycenter/nyc-tree-dashboard';
  var ACT_PATH   = 'data/activities.csv';
  var TREES_PATH = 'data/trees.csv';
  var GROUP_ID   = 14;
  var BATCH_SIZE = 25;

  if (!location.hostname.includes('nycgovparks.org')) {
    alert('Please open this page first:\nhttps://tree-map.nycgovparks.org/tree-map/group/' + GROUP_ID);
    return;
  }

  // ── Status bubble ─────────────────────────────────────────────
  var bubble = document.getElementById('_treeSync');
  if (!bubble) {
    bubble = document.createElement('div');
    bubble.id = '_treeSync';
    bubble.style.cssText = 'position:fixed;top:20px;right:20px;z-index:2147483647;' +
      'padding:14px 20px;border-radius:10px;font:bold 14px/1.5 sans-serif;' +
      'color:#fff;box-shadow:0 4px 16px rgba(0,0,0,0.3);max-width:380px;white-space:pre-line';
    document.body.appendChild(bubble);
  }
  function status(msg, color, persist) {
    bubble.textContent = msg;
    bubble.style.background = color || '#2e7d32';
    if (!persist) setTimeout(function () { bubble.remove(); }, 9000);
  }
  status('⏳ Syncing…', '#1565c0', true);

  // ── GitHub token ──────────────────────────────────────────────
  var token = localStorage.getItem('_treeSync_token') || localStorage.getItem('_ts_tok');
  if (!token) {
    token = prompt(
      'One-time setup: enter your GitHub personal access token.\n\n' +
      '1. github.com → profile photo → Settings\n' +
      '2. Developer settings → Personal access tokens → Tokens (classic)\n' +
      '3. Generate new token → check "repo" → Generate\n\nToken (starts with ghp_):'
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

  // ── GraphQL helper ────────────────────────────────────────────
  function gql(query) {
    return fetch('/api-treemap/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query })
    }).then(function (r) { return r.json(); });
  }

  // ── Read activities from Apollo cache ─────────────────────────
  function readActivitiesFromCache() {
    var client = window.__APOLLO_CLIENT__ || window.apolloClient;
    if (!client) return null;
    var cache;
    try { cache = client.cache.extract(); } catch (e) { return null; }
    var activities = [];
    Object.keys(cache).forEach(function (key) {
      var obj = cache[key];
      if (!obj || !obj.id) return;
      var type = (obj.__typename || '').toLowerCase();
      var isActivity = type.includes('activity') || type.includes('stewardship') || type.includes('report') ||
        (obj.stewardshipActivities !== undefined && obj.treeId !== undefined);
      if (!isActivity) return;
      activities.push(obj);
    });
    return activities.length ? activities : null;
  }

  // ── Fetch activities from API (no tree{} to avoid null propagation) ──
  function fetchActivitiesFromAPI() {
    return gql(
      'query{treeGroupById(id:' + GROUP_ID + '){recentActivities(limit:100000){id date treeId duration stewardshipActivities}}}'
    ).then(function (resp) {
      return ((resp.data || {}).treeGroupById || {}).recentActivities || [];
    });
  }

  // ── Batch-fetch tree coordinates by ID ────────────────────────
  function fetchTreeCoords(ids) {
    if (!ids.length) return Promise.resolve({});
    var results = {};
    var batches = [];
    for (var i = 0; i < ids.length; i += BATCH_SIZE) {
      batches.push(ids.slice(i, i + BATCH_SIZE));
    }
    var total = batches.length;
    var done  = 0;
    return batches.reduce(function (p, batch) {
      return p.then(function () {
        done++;
        status('⏳ Fetching tree locations… (' + done + '/' + total + ')', '#1565c0', true);
        var fields = batch.map(function (id, j) {
          return 't' + j + ':treeById(id:' + id + '){id latitude longitude closestAddress species{commonName}}';
        }).join(' ');
        return gql('{' + fields + '}').then(function (resp) {
          Object.values(resp.data || {}).forEach(function (t) {
            if (!t || !t.id) return;
            results[String(t.id)] = {
              lat:     t.latitude  || '',
              lng:     t.longitude || '',
              address: (t.closestAddress || '').replace(/,/g, ' '),
              species: ((t.species || {}).commonName || '').replace(/,/g, ' ')
            };
          });
        }).catch(function () {});
      });
    }, Promise.resolve()).then(function () { return results; });
  }

  // ── Format activity as CSV row ────────────────────────────────
  var TODAY = new Date().toISOString().slice(0, 10);
  function actRow(r) {
    var date = '';
    try { date = r.date ? new Date(+r.date).toISOString().slice(0, 10) : ''; } catch (e) {}
    if (!date && r.date) date = String(r.date).slice(0, 10);
    var acts = r.stewardshipActivities || [];
    if (typeof acts === 'string') { try { acts = JSON.parse(acts); } catch (e) { acts = [acts]; } }
    var actsStr = Array.isArray(acts) ? acts.join('; ') : String(acts);
    return [r.id, date, r.treeId || '', '', '', actsStr, r.duration || '', TODAY].map(function (f) {
      f = String(f == null ? '' : f);
      return /[,"\n]/.test(f) ? '"' + f.replace(/"/g, '""') + '"' : f;
    }).join(',');
  }

  // ── GitHub read / write ───────────────────────────────────────
  function ghRead(path) {
    return fetch('https://api.github.com/repos/' + REPO + '/contents/' + path, { headers: ghHeaders })
      .then(function (r) { return r.json(); }).catch(function () { return null; });
  }
  function ghWrite(path, content, sha, msg) {
    var body = { message: msg, content: btoa(unescape(encodeURIComponent(content))) };
    if (sha) body.sha = sha;
    return fetch('https://api.github.com/repos/' + REPO + '/contents/' + path, {
      method: 'PUT',
      headers: Object.assign({ 'Content-Type': 'application/json' }, ghHeaders),
      body: JSON.stringify(body)
    }).then(function (r) { if (!r.ok) throw new Error('GitHub push failed: HTTP ' + r.status); });
  }

  // ── Main ──────────────────────────────────────────────────────
  var cached      = readActivitiesFromCache();
  var activitiesP = cached ? Promise.resolve(cached) : fetchActivitiesFromAPI();

  Promise.all([ghRead(ACT_PATH), ghRead(TREES_PATH), activitiesP])
    .then(function (res) {
      var ghActFile   = res[0];
      var ghTreesFile = res[1];
      var rawRows     = res[2];

      // ── activities.csv ──────────────────────────────────────
      var actCSV = 'id,date,treeId,species,address,activitiesDone,durationMinutes,scrapedAt\n';
      var actSha = null;
      if (ghActFile && ghActFile.content) {
        actCSV = atob(ghActFile.content.replace(/\s/g, ''));
        actSha = ghActFile.sha;
      }
      var seenActIds = {};
      actCSV.split('\n').slice(1).forEach(function (l) {
        var id = l.split(',')[0].trim(); if (id) seenActIds[id] = true;
      });
      var newActLines = [];
      var allTreeIds  = {};
      rawRows.forEach(function (r) {
        var id = String(r.id || '');
        if (r.treeId) allTreeIds[String(r.treeId)] = true;
        if (!id || seenActIds[id]) return;
        newActLines.push(actRow(r));
        seenActIds[id] = true;
      });

      // ── trees.csv ───────────────────────────────────────────
      var treesCSV = 'treeId,latitude,longitude,address,species\n';
      var treesSha = null;
      if (ghTreesFile && ghTreesFile.content) {
        treesCSV = atob(ghTreesFile.content.replace(/\s/g, ''));
        treesSha = ghTreesFile.sha;
      }
      var knownTreeIds = {};
      treesCSV.split('\n').slice(1).forEach(function (l) {
        var id = l.split(',')[0].trim(); if (id) knownTreeIds[id] = true;
      });
      var missingIds = Object.keys(allTreeIds).filter(function (id) { return !knownTreeIds[id]; });

      return fetchTreeCoords(missingIds).then(function (fetched) {
        var newTreeLines = [];
        missingIds.forEach(function (id) {
          var t = fetched[id];
          if (!t || !t.lat || !t.lng) return;
          newTreeLines.push([id, t.lat, t.lng, t.address, t.species].join(','));
        });

        var writes = [];
        if (newActLines.length > 0) {
          var updAct = actCSV.trimEnd() + '\n' + newActLines.join('\n') + '\n';
          writes.push(ghWrite(ACT_PATH, updAct, actSha,
            'Sync ' + TODAY + ' (+' + newActLines.length + ' activities)'));
        }
        if (newTreeLines.length > 0) {
          var updTrees = treesCSV.trimEnd() + '\n' + newTreeLines.join('\n') + '\n';
          writes.push(ghWrite(TREES_PATH, updTrees, treesSha,
            'Tree coords ' + TODAY + ' (+' + newTreeLines.length + ')'));
        }

        return Promise.all(writes).then(function () {
          var parts = [];
          if (newActLines.length)  parts.push(newActLines.length  + ' new activities');
          if (newTreeLines.length) parts.push(newTreeLines.length + ' tree locations saved');
          if (!parts.length) parts.push('nothing new to sync');
          status('✅ ' + parts.join(' · '), '#2e7d32');
        });
      });
    })
    .catch(function (err) {
      if (/401|403/.test(String(err))) localStorage.removeItem('_treeSync_token');
      status('❌ ' + err.message, '#c62828', true);
    });
})();
