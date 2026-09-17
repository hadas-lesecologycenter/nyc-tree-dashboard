var TREE_CARE_SHEET_ID = '1pZTLIgHx1HlyuVbZDXg5QRjfqbgy83PDaAdX_XDWLwU';

var SHEETS = ['Reservations', 'TreeGuards', 'CareNeeded', 'CommunityStewardship', 'MissingTrees'];

function doGet(e) {
  try {
    var sheet = e.parameter.sheet;
    if (!sheet) return respond({ error: 'Missing sheet parameter' });
    var ss = SpreadsheetApp.openById(TREE_CARE_SHEET_ID);
    var ws = ss.getSheetByName(sheet);
    if (!ws) return respond({ data: [] });
    var data = ws.getDataRange().getValues();
    return respond({ data: data });
  } catch(err) {
    return respond({ error: err.message });
  }
}

// Sheets whose rows are only ever added or edited, never deleted, and which
// several phones write to on the same afternoon. A write to one of these is
// merged into what is already there, keyed on the first column, instead of
// replacing the table: a device that posts a stale or partial list can no
// longer erase a colleague's field work. Every other sheet still has genuine
// delete flows in the app, so those keep replacing the table wholesale.
var MERGE_SHEETS = ['RiskAssessments'];

function doPost(e) {
  try {
    var payload = JSON.parse(e.postData.contents);
    var ss = SpreadsheetApp.openById(TREE_CARE_SHEET_ID);
    var ws = ss.getSheetByName(payload.sheet);
    if (!ws) ws = ss.insertSheet(payload.sheet);
    var rows = payload.rows || [];
    if (MERGE_SHEETS.indexOf(payload.sheet) !== -1 && rows.length > 1) {
      rows = mergeRows(ws, rows);
    }
    ws.clearContents();
    if (rows.length > 0) {
      ws.getRange(1, 1, rows.length, rows[0].length).setValues(rows);
    }
    return respond({ success: true, rows: Math.max(rows.length - 1, 0) });
  } catch(err) {
    return respond({ error: err.message });
  }
}

// Union of what is on the sheet and what was posted, keyed on the first column
// (the assessment timestamp, which is unique per submission). The posted copy
// of a row wins, so editing an assessment still updates it; rows the caller
// never knew about are kept rather than dropped.
function mergeRows(ws, posted) {
  var header = posted[0];
  var existing = ws.getDataRange().getValues();
  var out = [];
  var index = {};
  function put(row) {
    var k = String(row[0]);
    if (!k) return;
    if (index.hasOwnProperty(k)) out[index[k]] = row;
    else { index[k] = out.length; out.push(row); }
  }
  // Skip the stored header row; the posted header is authoritative.
  for (var i = 1; i < existing.length; i++) put(normalizeRow(existing[i], header.length));
  for (var j = 1; j < posted.length; j++) put(normalizeRow(posted[j], header.length));
  return [header].concat(out);
}

// Keep every row the same width as the header. Sheets stores an ISO string in a
// date cell, so reading it back yields a Date object; re-writing that object
// verbatim is what turned "2026-09-16" into a moving target. Render it back to
// the ISO text the app posted so a row survives any number of round trips
// unchanged.
function normalizeRow(row, width) {
  var out = [];
  for (var i = 0; i < width; i++) {
    var v = (i < row.length && row[i] !== undefined && row[i] !== null) ? row[i] : '';
    if (Object.prototype.toString.call(v) === '[object Date]') {
      v = Utilities.formatDate(v, 'UTC', "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'");
    }
    out.push(v);
  }
  return out;
}

function respond(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function setupSheets() {
  var ss = SpreadsheetApp.openById(TREE_CARE_SHEET_ID);
  var headers = {
    'Reservations': ['id','treeId','name','date','lat','lng','species','address','health','dbh','planted','priority','nta','note','createdAt'],
    'TreeGuards': ['treeId','markedBy','guardType','markedAt','note'],
    'CareNeeded': ['treeId','careNeeds','markedAt','markedBy'],
    'CommunityStewardship': ['treeId','caretaker','activities','markedAt'],
    'MissingTrees': ['treeId','type','note','markedAt']
  };
  SHEETS.forEach(function(name) {
    var ws = ss.getSheetByName(name) || ss.insertSheet(name);
    if (ws.getLastRow() === 0) ws.appendRow(headers[name]);
  });
}
