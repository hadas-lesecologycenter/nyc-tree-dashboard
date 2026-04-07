/**
 * LES Ecology Center - Event Workflow Dashboard
 * Google Apps Script Web App
 * =============================================
 * SETUP:
 *   1. Go to https://script.google.com -> New Project
 *   2. Create two files: Code.gs (this) and Index.html
 *   3. Update CONFIG below with your IDs
 *   4. Deploy -> New deployment -> Web app
 *      Execute as: Me | Access: Anyone in your org
 *   5. Embed the URL in your Google Site
 */

var CONFIG = {
  TRACKER_SHEET_ID: '1EKZHAAlNOPPQEgxDgR7IMBKXWY5aR3VEURl4crImsrY',
  BRIEF_FOLDER_ID: '1vAH4OPtWMIkZIBtKRcdKwfbYT4bebfnC',
  TRACKER_SHEET_NAME: 'Sheet1'
};

function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('Index')
    .setTitle('LES Ecology - Event Dashboard')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function addTrackerRow(ev) {
  var ss = SpreadsheetApp.openById(CONFIG.TRACKER_SHEET_ID);
  var sheet = ss.getSheetByName(CONFIG.TRACKER_SHEET_NAME) || ss.getSheets()[0];
  var isPublic = ev.type && ev.type.indexOf('Public') >= 0;
  sheet.appendRow([
    ev.name, ev.owner, ev.date, ev.time||'', ev.location||'',
    (ev.categories||[]).join(', '), ev.type, ev.collab||'', ev.collabNotes||'',
    isPublic?'':'N/A (not a public event)', isPublic?'':'N/A', '',
    isPublic?'':'N/A', false, false, '', false, false, false, '', ''
  ]);
  return {success:true, url:ss.getUrl()};
}

function createEventBrief(ev) {
  if (!CONFIG.BRIEF_FOLDER_ID) return {success:false, error:'No BRIEF_FOLDER_ID in Code.gs'};
  try {
    var folder = DriveApp.getFolderById(CONFIG.BRIEF_FOLDER_ID);
    var doc = DocumentApp.create('Event Brief - ' + ev.name + ' - ' + ev.date);
    var body = doc.getBody();
    body.appendParagraph('STC Event Brief: ' + ev.name).setHeading(DocumentApp.ParagraphHeading.HEADING1).setForegroundColor('#2d6a4f');
    body.appendParagraph('Status: ' + (ev.status||'confirmed').toUpperCase()).setItalic(true);
    body.appendHorizontalRule();
    var fmt = (ev.type&&ev.type.indexOf('Virtual')>=0)?'Virtual':'In-person';
    var partner = ev.collab==='Other Organization'?ev.collabNotes:'N/A';
    var client = (ev.type&&(ev.type.indexOf('Private')>=0||ev.type.indexOf('School')>=0))?ev.collabNotes:'N/A';
    addSec(body,'EVENT OVERVIEW');
    addF(body,'Event Name (Internal)',ev.name); addF(body,'Event Lead',ev.owner);
    addF(body,'On-Site Support',ev.support); addF(body,'Program Category',(ev.categories||[]).join(', '));
    addF(body,'Format',fmt); addF(body,'Date',ev.date); addF(body,'Time',ev.time);
    addF(body,'Location/Venue',ev.location); addF(body,'Partner/s',partner);
    addF(body,'Client/s',client); addF(body,'Primary Audience',(ev.audiences||[]).join(', '));
    addSec(body,'IMPACT');
    addF(body,'Goals',ev.goals); addF(body,'Expected Attendance',ev.attendance); addF(body,'Success Metrics',ev.metrics);
    addSec(body,'COMMS');
    addF(body,'Event Name (External)',ev.extName||ev.name); addF(body,'Description',ev.description);
    addF(body,'Marketing Channels',(ev.marketing||[]).join(', ')); addF(body,'Eventbrite',ev.eventbrite);
    addSec(body,'LOGISTICS');
    addF(body,'Vendors',ev.vendors); addF(body,'Facilities',ev.facilities); addF(body,'Supplies',ev.supplies);
    addF(body,'Equipment',ev.equipment); addF(body,'Compost',ev.compost); addF(body,'Mulch',ev.mulch);
    addF(body,'Expenses',ev.expenses||'NO');
    addSec(body,'RUN OF SHOW'); body.appendParagraph(ev.ros||'TBD');
    addSec(body,'ACCESS NOTES'); body.appendParagraph(ev.access||'TBD');
    doc.saveAndClose();
    var file = DriveApp.getFileById(doc.getId());
    folder.addFile(file); DriveApp.getRootFolder().removeFile(file);
    return {success:true, url:doc.getUrl(), docId:doc.getId()};
  } catch(err) { return {success:false, error:err.message}; }
}

function addSec(body,t) { body.appendParagraph(''); body.appendParagraph(t).setHeading(DocumentApp.ParagraphHeading.HEADING2).setForegroundColor('#2d6a4f'); }
function addF(body,l,v) { var p=body.appendParagraph(''); p.appendText(l+': ').setBold(true); p.appendText(v||'TBD').setBold(false); }

/**
 * Push a list of tasks to Google Calendar as all-day events on the user's
 * default calendar. Each task becomes one all-day event titled "[STC] <title>"
 * with the parent event name + phase in the description.
 */
function pushTasksToCalendar(tasks) {
  try {
    var cal = CalendarApp.getDefaultCalendar();
    var count = 0;
    tasks.forEach(function(t) {
      if (!t.due) return;
      var d = new Date(t.due + 'T12:00:00');
      var title = '[STC] ' + t.title + ' — ' + t.evName;
      var desc = 'Event: ' + t.evName + '\nPhase: ' + t.phase + '\nAssignee: ' + (t.assignee||'') + '\nEvent date: ' + (t.evDate||'');
      cal.createAllDayEvent(title, d, {description: desc});
      count++;
    });
    return {success:true, count:count};
  } catch(e) {
    return {success:false, error:e.message};
  }
}

/**
 * Push tasks to Google Tasks (default task list).
 * REQUIRES: Services panel -> add "Tasks API" (advanced service) before this
 * function will work. If not enabled, the function returns an error message
 * with setup instructions.
 */
function pushTasksToGoogleTasks(tasks) {
  try {
    if (typeof Tasks === 'undefined') {
      return {success:false, error:'Enable Tasks API: Apps Script editor -> Services (+) -> Tasks API'};
    }
    var lists = Tasks.Tasklists.list();
    var listId = lists.items && lists.items.length ? lists.items[0].id : '@default';
    var count = 0;
    tasks.forEach(function(t) {
      if (!t.due) return;
      var dueIso = new Date(t.due + 'T12:00:00').toISOString();
      Tasks.Tasks.insert({
        title: t.title + ' — ' + t.evName,
        notes: 'Phase: ' + t.phase + '\nAssignee: ' + (t.assignee||'') + '\nEvent date: ' + (t.evDate||''),
        due: dueIso
      }, listId);
      count++;
    });
    return {success:true, count:count};
  } catch(e) {
    return {success:false, error:e.message};
  }
}

function testConfig() {
  try { var ss=SpreadsheetApp.openById(CONFIG.TRACKER_SHEET_ID); Logger.log('Sheet OK: '+ss.getName()); } catch(e) { Logger.log('Sheet ERROR: '+e.message); }
  if (CONFIG.BRIEF_FOLDER_ID) { try { var f=DriveApp.getFolderById(CONFIG.BRIEF_FOLDER_ID); Logger.log('Folder OK: '+f.getName()); } catch(e) { Logger.log('Folder ERROR: '+e.message); } }
}
