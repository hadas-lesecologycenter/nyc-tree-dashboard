/**
 * NYC Tree Map → GitHub Sync Bookmarklet
 * Fetches group activities + tree coordinates and pushes to GitHub.
 */
(function () {
  'use strict';

  var REPO       = 'hadas-lesecologycenter/nyc-tree-dashboard';
  var ACT_PATH   = 'data/activities.csv';
  var TREES_PATH = 'data/trees.csv';
  var CENSUS_URL = 'https://raw.githubusercontent.com/hadas-lesecologycenter/nyc-tree-dashboard/main/data/census.json';
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
  var token = localStorage.getItem('_ts_tok') || localStorage.getItem('_treeSync_token');
  if (!token) {
    token = prompt(
      'One-time setup: enter your GitHub personal access token.\n\n' +
      '1. github.com → profile photo → Settings\n' +
      '2. Developer settings → Personal access tokens → Tokens (classic)\n' +
      '3. Generate new token → check "repo" → Generate\n\nToken (starts with ghp_):'
    );
    if (!token) { bubble.remove(); return; }
    token = token.trim();
    localStorage.setItem('_ts_tok', token);
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

  // ── Read activities AND tree coords from Apollo cache ────────
  function readFromCache() {
    var client = window.__APOLLO_CLIENT__ || window.apolloClient;
    if (!client) return { activities: null, trees: {} };
    var cache;
    try { cache = client.cache.extract(); } catch (e) { return { activities: null, trees: {} }; }

    var activities = [];
    var trees = {};

    Object.keys(cache).forEach(function (key) {
      var obj = cache[key];
      if (!obj || !obj.id) return;
      var type = (obj.__typename || '').toLowerCase();

      // Collect tree coordinate data — try several possible field name patterns
      if (type === 'tree' || type === 'streettree' || type === 'nyctree') {
        var sp = obj.species;
        if (sp && sp.__ref) sp = cache[sp.__ref] || {};
        var lat = obj.latitude || obj.lat || (obj.location && obj.location.lat) || '';
        var lng = obj.longitude || obj.lng || obj.lon || (obj.location && obj.location.lng) || '';
        if (lat && lng) {
          trees[String(obj.id)] = {
            lat:     lat,
            lng:     lng,
            address: (obj.closestAddress || obj.address || '').replace(/,/g, ' '),
            species: ((sp && sp.commonName) || '').replace(/,/g, ' ')
          };
        }
      }

      // Collect activities
      var isActivity = type.includes('activity') || type.includes('stewardship') || type.includes('report') ||
        (obj.stewardshipActivities !== undefined && obj.treeId !== undefined);
      if (!isActivity) return;

      // Dereference tree __ref and extract coords if not already found
      var tree = obj.tree;
      if (tree && tree.__ref) tree = cache[tree.__ref] || tree;
      if (tree && tree.id && !trees[String(tree.id)]) {
        var sp2 = tree.species;
        if (sp2 && sp2.__ref) sp2 = cache[sp2.__ref] || {};
        var lat2 = tree.latitude || tree.lat || '';
        var lng2 = tree.longitude || tree.lng || tree.lon || '';
        if (lat2 && lng2) {
          trees[String(tree.id)] = {
            lat:     lat2,
            lng:     lng2,
            address: (tree.closestAddress || tree.address || '').replace(/,/g, ' '),
            species: ((sp2 && sp2.commonName) || '').replace(/,/g, ' ')
          };
        }
      }

      activities.push(obj);
    });

    return { activities: activities.length ? activities : null, trees: trees };
  }

  // ── Fetch activities from API (no tree{} to avoid null propagation) ──
  function fetchActivitiesFromAPI() {
    return gql(
      'query{treeGroupById(id:' + GROUP_ID + '){recentActivities(limit:100000){id date treeId duration stewardshipActivities}}}'
    ).then(function (resp) {
      return ((resp.data || {}).treeGroupById || {}).recentActivities || [];
    });
  }

  // ── Batch-fetch tree coordinates — try treeById then tree ────
  function fetchTreeCoords(ids) {
    if (!ids.length) return Promise.resolve({});
    var results = {};
    var batches = [];
    for (var i = 0; i < ids.length; i += BATCH_SIZE) {
      batches.push(ids.slice(i, i + BATCH_SIZE));
    }
    var total = batches.length;
    var done  = 0;

    // Try a single tree first to detect correct field name
    function makeFields(batch, fieldName) {
      return batch.map(function (id, j) {
        return 't' + j + ':' + fieldName + '(id:' + id + '){id latitude longitude closestAddress}';
      }).join(' ');
    }

    // Probe with first id to find working field name
    var fieldName = 'treeById';
    var probeP = gql('{probe:treeById(id:' + ids[0] + '){id latitude longitude}}')
      .then(function (r) {
        if (r.errors && !r.data) fieldName = 'tree'; // treeById failed, try 'tree'
      }).catch(function () { fieldName = 'tree'; });

    return probeP.then(function () {
      return batches.reduce(function (p, batch) {
        return p.then(function () {
          done++;
          status('⏳ Fetching tree locations… (' + done + '/' + total + ')', '#1565c0', true);
          return gql('{' + makeFields(batch, fieldName) + '}').then(function (resp) {
            Object.values(resp.data || {}).forEach(function (t) {
              if (!t || !t.id) return;
              results[String(t.id)] = {
                lat:     t.latitude  || '',
                lng:     t.longitude || '',
                address: (t.closestAddress || '').replace(/,/g, ' '),
                species: ''
              };
            });
          }).catch(function () {});
        });
      }, Promise.resolve());
    }).then(function () { return results; });
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
    function putFile(s) {
      var body = { message: msg, content: btoa(unescape(encodeURIComponent(content))) };
      if (s) body.sha = s;
      return fetch('https://api.github.com/repos/' + REPO + '/contents/' + path, {
        method: 'PUT',
        headers: Object.assign({ 'Content-Type': 'application/json' }, ghHeaders),
        body: JSON.stringify(body)
      });
    }
    return putFile(sha).then(function (r) {
      if (r.status === 409) {
        // SHA conflict — re-fetch current file SHA and retry
        return ghRead(path).then(function (file) {
          return putFile(file ? file.sha : null);
        }).then(function (r2) {
          if (!r2.ok) throw new Error('GitHub push failed: HTTP ' + r2.status + ' (retry after conflict)');
        });
      }
      if (!r.ok) throw new Error('GitHub push failed: HTTP ' + r.status);
    });
  }

  // ── Main ──────────────────────────────────────────────────────
  var cacheData   = readFromCache();
  var activitiesP = cacheData.activities ? Promise.resolve(cacheData.activities) : fetchActivitiesFromAPI();

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

      // Merge coords from Apollo cache first
      var cacheCoords = cacheData.trees || {};
      var newTreeLines = [];
      var stillMissing = [];
      missingIds.forEach(function (id) {
        if (cacheCoords[id] && cacheCoords[id].lat && cacheCoords[id].lng) {
          var t = cacheCoords[id];
          newTreeLines.push([id, t.lat, t.lng, t.address, t.species].join(','));
          knownTreeIds[id] = true;
        } else {
          stillMissing.push(id);
        }
      });

      status('⏳ Cache: ' + newTreeLines.length + ' coords found. Fetching ' + stillMissing.length + ' more…', '#1565c0', true);

      return fetchTreeCoords(stillMissing).then(function (fetched) {
        var apiFound = {};
        var afterAPI = [];
        stillMissing.forEach(function (id) {
          var t = fetched[id];
          if (t && t.lat && t.lng) {
            apiFound[id] = t;
          } else {
            afterAPI.push(id);
          }
        });

        // Fetch census data for species names and coordinates of trees the API missed
        status('⏳ Checking census data for species + ' + afterAPI.length + ' missing trees…', '#1565c0', true);
        return fetch(CENSUS_URL).then(function (r) { return r.json(); }).then(function (census) {
          var byId = {};
          census.forEach(function (t) { if (t.tree_id) byId[String(t.tree_id)] = t; });
          // Backfill species for API-found trees
          Object.keys(apiFound).forEach(function (id) {
            var c = byId[id];
            if (c && c.spc_common) apiFound[id].species = (c.spc_common || '').replace(/,/g, ' ');
          });
          // Use census coords for trees the API couldn't locate
          afterAPI.forEach(function (id) {
            var c = byId[id];
            if (!c || !c.latitude || !c.longitude) return;
            apiFound[id] = {
              lat: c.latitude, lng: c.longitude,
              address: (c.address || '').replace(/,/g, ' '),
              species: (c.spc_common || '').replace(/,/g, ' ')
            };
          });
        }).catch(function () {}).then(function () {
          Object.keys(apiFound).forEach(function (id) {
            var t = apiFound[id];
            newTreeLines.push([id, t.lat, t.lng, t.address, t.species].join(','));
          });
        });
      }).then(function () {

        // Write files sequentially to avoid branch-tip conflicts
        var writeP = Promise.resolve();
        if (newActLines.length > 0) {
          var updAct = actCSV.trimEnd() + '\n' + newActLines.join('\n') + '\n';
          writeP = writeP.then(function () {
            return ghWrite(ACT_PATH, updAct, actSha,
              'Sync ' + TODAY + ' (+' + newActLines.length + ' activities)');
          });
        }
        var updTrees = treesCSV.trimEnd() + (newTreeLines.length ? '\n' + newTreeLines.join('\n') : '') + '\n';
        writeP = writeP.then(function () {
          return ghWrite(TREES_PATH, updTrees, treesSha,
            'Tree coords ' + TODAY + ' (+' + newTreeLines.length + ')');
        });

        return writeP.then(function () {
          var parts = [];
          if (newActLines.length)  parts.push(newActLines.length + ' new activities');
          parts.push(newTreeLines.length + ' of ' + missingIds.length + ' tree locations found');
          status('✅ ' + parts.join(' · '), '#2e7d32');
        });
      });
    })
    .catch(function (err) {
      if (/401|403/.test(String(err))) localStorage.removeItem('_ts_tok');
      status('❌ ' + err.message, '#c62828', true);
    });
})();
