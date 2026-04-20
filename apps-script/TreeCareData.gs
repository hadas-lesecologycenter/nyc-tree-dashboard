var TREE_CARE_SHEET_ID = 'YOUR_SHEET_ID_HERE';

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

function doPost(e) {
  try {
    var payload = JSON.parse(e.postData.contents);
    var ss = SpreadsheetApp.openById(TREE_CARE_SHEET_ID);
    var ws = ss.getSheetByName(payload.sheet);
    if (!ws) ws = ss.insertSheet(payload.sheet);
    ws.clearContents();
    if (payload.rows && payload.rows.length > 0) {
      ws.getRange(1, 1, payload.rows.length, payload.rows[0].length).setValues(payload.rows);
    }
    return respond({ success: true });
  } catch(err) {
    return respond({ error: err.message });
  }
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
