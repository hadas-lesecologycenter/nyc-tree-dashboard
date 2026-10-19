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
  TRACKER_SHEET_NAME: 'Sheet1',
  // Google Chat integration - fill in after setting up a webhook in your
  // Street Tree Care Crew space: Space menu -> Apps & integrations ->
  // Manage webhooks -> Add webhook -> copy URL.
  CHAT_WEBHOOK_URL: '',
  // Email addresses of team members (used for Google Tasks delegation
  // and task-mention formatting).
  TEAM: {
    'Maddy': '',
    'Hadas': '',
    'Gretel': ''
  },
  // The Eventbrite private token lives in Script Properties, not here:
  // Project Settings -> Script Properties -> add EVENTBRITE_TOKEN.
  EVENTBRITE_ORG_ID: '13297911311',
  // LESEC Activity Reporting (Responses) - source of actual attendance.
  ACTIVITY_SHEET_ID: '1RqQl5Wx-DUhMDQwTk2APz0VulodV3FaS51Y9WGuYwAs',
  ACTIVITY_SHEET_NAME: 'Form Responses 1',
  // Only report rows whose "Name of staff" mentions one of these count as
  // Street Tree Care events.
  STC_STAFF: ['Maddy', 'Hadas', 'Gretel']
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

/**
 * ========================================================================
 * GOOGLE CHAT SPACE INTEGRATION
 * ========================================================================
 * Posts tasks to the Street Tree Care Crew Google Chat space.
 *
 * Google does not currently expose a public API for creating tasks inside
 * a Chat space's "Tasks" panel (the pink panel with "Add task to space").
 * Instead, this posts formatted task messages via an incoming webhook, so
 * the whole team sees the assignment in the space conversation.
 *
 * SETUP:
 *   1. Open your "Street Tree Care Crew" space in Google Chat
 *   2. Click the space name at the top -> Apps & integrations
 *   3. Manage webhooks -> Add webhook -> give it a name (e.g., "STC Dashboard")
 *   4. Copy the webhook URL
 *   5. Paste it into CONFIG.CHAT_WEBHOOK_URL at the top of this file
 *   6. Also fill in CONFIG.TEAM email addresses (for @mentions)
 */
function pushTasksToChatSpace(tasks) {
  try {
    if (!CONFIG.CHAT_WEBHOOK_URL) {
      return {success:false, error:'Set CHAT_WEBHOOK_URL in Code.gs CONFIG. See setup instructions at the top of pushTasksToChatSpace.'};
    }
    if (!tasks || !tasks.length) return {success:false, error:'No tasks to push'};

    // Group tasks by assignee so each person gets one clean message
    var byAssignee = {};
    tasks.forEach(function(t) {
      var who = t.assignee || 'Unassigned';
      if (!byAssignee[who]) byAssignee[who] = [];
      byAssignee[who].push(t);
    });

    var count = 0;
    Object.keys(byAssignee).forEach(function(who) {
      var list = byAssignee[who];
      var email = CONFIG.TEAM[who] || '';
      // Build a rich card with one "task row" per task
      var widgets = list.map(function(t) {
        var dueLabel = formatDue_(t.due);
        return {
          decoratedText: {
            topLabel: t.phase + ' · ' + (t.evName || 'Event'),
            text: t.title,
            bottomLabel: 'Due: ' + dueLabel + (t.evDate ? ' · Event: ' + t.evDate : ''),
            startIcon: { knownIcon: 'TASK' }
          }
        };
      });

      var mention = email ? '<users/' + email + '>' : who;
      var card = {
        text: 'New tasks assigned to ' + mention + ' (' + list.length + ')',
        cardsV2: [{
          cardId: 'stc_tasks_' + Date.now() + '_' + who.replace(/\s/g,''),
          card: {
            header: {
              title: '🌳 STC Tasks for ' + who,
              subtitle: list.length + ' task' + (list.length>1?'s':'') + ' assigned',
              imageType: 'CIRCLE'
            },
            sections: [
              { header: 'Tasks', widgets: widgets },
              {
                widgets: [{
                  textParagraph: {
                    text: '<i>From the <b>Street Tree Care Event Dashboard</b>. Check off tasks in the dashboard when complete.</i>'
                  }
                }]
              }
            ]
          }
        }]
      };

      var resp = UrlFetchApp.fetch(CONFIG.CHAT_WEBHOOK_URL, {
        method: 'post',
        contentType: 'application/json',
        payload: JSON.stringify(card),
        muteHttpExceptions: true
      });
      if (resp.getResponseCode() >= 200 && resp.getResponseCode() < 300) {
        count += list.length;
      }
    });
    return {success:true, count:count, assignees:Object.keys(byAssignee).length};
  } catch(e) {
    return {success:false, error:e.message};
  }
}

/**
 * Posts a single event summary to the Chat space — useful when a new
 * event is confirmed to give the team a heads-up with key details.
 */
function postEventToChatSpace(ev) {
  try {
    if (!CONFIG.CHAT_WEBHOOK_URL) return {success:false, error:'No webhook configured'};
    var who = ev.owner || 'Unassigned';
    var email = CONFIG.TEAM[who] || '';
    var mention = email ? '<users/' + email + '>' : who;
    var card = {
      text: 'New event assigned to ' + mention,
      cardsV2: [{
        cardId: 'stc_event_' + (ev.id || Date.now()),
        card: {
          header: {
            title: '🌳 ' + ev.name,
            subtitle: (ev.status || 'confirmed').toUpperCase() + ' · Owner: ' + who
          },
          sections: [{
            widgets: [
              { decoratedText: { topLabel: 'Date', text: ev.date + (ev.time ? ' · ' + ev.time : ''), startIcon: { knownIcon: 'INVITE' } } },
              { decoratedText: { topLabel: 'Location', text: ev.location || 'TBD', startIcon: { knownIcon: 'MAP_PIN' } } },
              { decoratedText: { topLabel: 'Type', text: ev.type || '' } },
              { decoratedText: { topLabel: 'Expected attendance', text: ev.attendance || 'TBD' } }
            ]
          }]
        }
      }]
    };
    var resp = UrlFetchApp.fetch(CONFIG.CHAT_WEBHOOK_URL, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(card),
      muteHttpExceptions: true
    });
    return {success: resp.getResponseCode() < 300, code: resp.getResponseCode()};
  } catch(e) {
    return {success:false, error:e.message};
  }
}

function formatDue_(dueStr) {
  if (!dueStr) return 'TBD';
  var d = new Date(dueStr + 'T12:00:00');
  var t = new Date(); t.setHours(0,0,0,0);
  var dd = new Date(d); dd.setHours(0,0,0,0);
  var diff = Math.round((dd - t) / 86400000);
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Tomorrow';
  if (diff === -1) return 'Yesterday';
  if (diff < 0) return Math.abs(diff) + ' days overdue';
  if (diff <= 14) return 'In ' + diff + ' days';
  return d.toLocaleDateString('en-US', {month:'short', day:'numeric', year:'numeric'});
}

/**
 * ========================================================================
 * EVENTBRITE INTEGRATION
 * ========================================================================
 * Creates an Eventbrite event from dashboard event data.
 *
 * SETUP:
 *   1. Go to https://www.eventbrite.com/platform/api-keys
 *   2. Create a new Private Token
 *   3. Project Settings -> Script Properties -> add EVENTBRITE_TOKEN
 */
function ebToken_() {
  return PropertiesService.getScriptProperties().getProperty('EVENTBRITE_TOKEN') || '';
}

function createEventbriteEvent(ev) {
  try {
    if (!ebToken_()) {
      return {success:false, error:'Set EVENTBRITE_TOKEN in Script Properties. Get one at eventbrite.com/platform/api-keys'};
    }
    var startDate = new Date(ev.date + 'T' + (parseTime_(ev.time) || '12:00:00'));
    var endDate = new Date(startDate.getTime() + 2*60*60*1000);
    var payload = {
      event: {
        name: {html: ev.extName || ev.name},
        description: {html: ev.description || 'Join LES Ecology Center for ' + ev.name},
        start: {timezone: 'America/New_York', utc: startDate.toISOString().replace(/\.\d+Z$/,'Z')},
        end: {timezone: 'America/New_York', utc: endDate.toISOString().replace(/\.\d+Z$/,'Z')},
        currency: 'USD',
        online_event: ev.type && ev.type.indexOf('Virtual') >= 0,
        organizer_id: CONFIG.EVENTBRITE_ORG_ID,
        listed: false,
        capacity: parseInt(ev.attendance) || 50
      }
    };
    var resp = UrlFetchApp.fetch('https://www.eventbriteapi.com/v3/organizations/' + CONFIG.EVENTBRITE_ORG_ID + '/events/', {
      method: 'post',
      contentType: 'application/json',
      headers: {'Authorization': 'Bearer ' + ebToken_()},
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });
    var data = JSON.parse(resp.getContentText());
    if (resp.getResponseCode() >= 200 && resp.getResponseCode() < 300) {
      return {success:true, url:data.url, id:data.id};
    }
    return {success:false, error:data.error_description || resp.getContentText()};
  } catch(e) {
    return {success:false, error:e.message};
  }
}

function parseTime_(timeStr) {
  if (!timeStr) return null;
  var m = timeStr.match(/(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM)?/);
  if (!m) return null;
  var h = parseInt(m[1]);
  var min = m[2] ? parseInt(m[2]) : 0;
  if (m[3] && m[3].toLowerCase() === 'pm' && h < 12) h += 12;
  if (m[3] && m[3].toLowerCase() === 'am' && h === 12) h = 0;
  return String(h).padStart(2,'0') + ':' + String(min).padStart(2,'0') + ':00';
}

/**
 * ========================================================================
 * REGISTRATION VS. ATTENDANCE
 * ========================================================================
 * Registered = Eventbrite attendees with status "attending" (cancelled and
 * refunded orders are left out). Attended = headcount from the LESEC
 * Activity Reporting form, matched to the dashboard event by date, then by
 * words the event and the report row have in common.
 */
function getAttendanceStats(evs) {
  try {
    var rows = readStcReports_();
    var ids = evs.map(function(ev) { return ebEventId_(ev.eventbrite); });
    var regs = fetchRegistrations_(ids);
    var out = evs.map(function(ev, i) {
      var m = matchReport_(ev, rows);
      return {id: ev.id, ebId: ids[i], registered: regs[i].count, ebError: regs[i].error,
              candidates: m.candidates, autoKey: m.autoKey, ambiguous: m.ambiguous};
    });
    return {success: true, events: out, fetchedAt: new Date().toISOString()};
  } catch (e) {
    return {success: false, error: e.message};
  }
}

// Eventbrite links end in the numeric event ID (".../e/name-tickets-123456789012").
function ebEventId_(url) {
  var ids = String(url || '').match(/\d{9,}/g);
  return ids ? ids[ids.length - 1] : '';
}

function fetchRegistrations_(ids) {
  var token = ebToken_();
  var res = ids.map(function(id) {
    if (!id) return {count: null, error: 'No event ID in the Eventbrite link'};
    if (!token) return {count: null, error: 'EVENTBRITE_TOKEN not set in Script Properties'};
    return null;
  });
  var pending = [];
  res.forEach(function(r, i) { if (!r) pending.push(i); });
  if (!pending.length) return res;
  var resps = UrlFetchApp.fetchAll(pending.map(function(i) {
    return {url: 'https://www.eventbriteapi.com/v3/events/' + ids[i] + '/attendees/?status=attending',
            headers: {'Authorization': 'Bearer ' + token}, muteHttpExceptions: true};
  }));
  resps.forEach(function(resp, j) {
    var data = {};
    try { data = JSON.parse(resp.getContentText()); } catch (e) {}
    res[pending[j]] = resp.getResponseCode() === 200 && data.pagination
      ? {count: data.pagination.object_count, error: ''}
      : {count: null, error: data.error_description || ('Eventbrite HTTP ' + resp.getResponseCode())};
  });
  return res;
}

// Street Tree Care rows from the activity report: workshops/outreach and
// tree care volunteer events run by CONFIG.STC_STAFF.
function readStcReports_() {
  var ss = SpreadsheetApp.openById(CONFIG.ACTIVITY_SHEET_ID);
  var tz = ss.getSpreadsheetTimeZone();
  var values = ss.getSheetByName(CONFIG.ACTIVITY_SHEET_NAME).getDataRange().getValues();
  var head = values[0].map(function(h) { return String(h).trim(); });
  // Some headers repeat ("Notes", "Number of Participants"); the first match is the one we want.
  function col(name, prefix) {
    var i = head.findIndex(function(h) { return prefix ? h.indexOf(name) === 0 : h === name; });
    if (i < 0) throw new Error('Activity report column not found: ' + name);
    return i;
  }
  var C = {
    ts: col('Timestamp'), staff: col('Name of staff carrying out activity'), type: col('Type of Activity'),
    wDate: col('Date of Activity'), wTitle: col('Workshop/Event Title'), wPlace: col('Workshop/Event Location'),
    wCount: col('Number of Participants'),
    vDate: col('Date of activity'), vType: col('Type of Volunteer Activity'), vCount: col('Number of tree care volunteers'),
    vPlace: col('Event Location', true), vGroup: col('Volunteer Group Name (if applicable)')
  };
  var staffRe = new RegExp(CONFIG.STC_STAFF.join('|'), 'i');
  function day(d) {
    if (d && !(d instanceof Date)) d = new Date(d);
    return d instanceof Date && !isNaN(d) ? Utilities.formatDate(d, tz, 'yyyy-MM-dd') : '';
  }
  var out = [];
  for (var r = 1; r < values.length; r++) {
    var v = values[r], row;
    if (!staffRe.test(String(v[C.staff]))) continue;
    if (v[C.type] === 'Workshop/Outreach') {
      row = {date: day(v[C.wDate]), title: v[C.wTitle], place: v[C.wPlace], count: v[C.wCount], kind: 'Workshop'};
    } else if (v[C.type] === 'Volunteer Activities' && v[C.vType] === 'Tree Care') {
      row = {date: day(v[C.vDate]), title: v[C.vGroup] ? 'Tree care: ' + v[C.vGroup] : 'Tree care',
             place: v[C.vPlace], count: v[C.vCount], kind: 'Tree care'};
    } else {
      continue;
    }
    if (!row.date) continue;
    row.key = v[C.ts] instanceof Date ? String(v[C.ts].getTime()) : 'row' + (r + 1);
    row.staff = String(v[C.staff]).trim();
    row.title = String(row.title || '').trim();
    row.place = String(row.place || '').trim();
    row.count = row.count === '' || row.count === null || isNaN(Number(row.count)) ? null : Number(row.count);
    out.push(row);
  }
  return out;
}

// Report rows within 3 days of the event are offered as candidates; the
// auto match is the same-day row sharing the most words with the event.
function matchReport_(ev, rows) {
  if (!ev.date) return {candidates: [], autoKey: '', ambiguous: false};
  var evT = Date.parse(ev.date), dayMs = 24 * 60 * 60 * 1000;
  var evWords = wordSet_([ev.name, ev.extName, ev.location, ev.collab].join(' '));
  var cands = [];
  rows.forEach(function(row) {
    var diff = Math.round(Math.abs(Date.parse(row.date) - evT) / dayMs);
    if (diff > 3) return;
    var score = Object.keys(wordSet_(row.title + ' ' + row.place)).filter(function(w) { return evWords[w]; }).length;
    cands.push({row: row, diff: diff, score: score});
  });
  cands.sort(function(a, b) { return a.diff - b.diff || b.score - a.score; });
  var same = cands.filter(function(c) { return c.diff === 0; });
  return {
    candidates: cands.map(function(c) { return Object.assign({}, c.row, {diff: c.diff}); }),
    autoKey: same.length ? same[0].row.key : '',
    ambiguous: same.length > 1 && same[0].score === same[1].score
  };
}

// "tree" and "care" are in nearly every row, so they don't help tell events apart.
var STOP_WORDS_ = {the:1, and:1, with:1, for:1, between:1, street:1, ave:1, avenue:1, new:1, york:1,
                   tree:1, trees:1, care:1, event:1};
function wordSet_(s) {
  var set = {};
  String(s || '').toLowerCase().split(/[^a-z0-9]+/).forEach(function(w) {
    if (w.length >= 3 && !STOP_WORDS_[w]) set[w] = 1;
  });
  return set;
}

// Run from the Apps Script editor to check both data sources: logs the
// latest report rows and registered/attended for the 5 newest Eventbrite events.
function testAttendance() {
  var rows = readStcReports_();
  Logger.log('Activity report: ' + rows.length + ' Street Tree Care rows. Latest: ' + JSON.stringify(rows.slice(-3)));
  var resp = UrlFetchApp.fetch('https://www.eventbriteapi.com/v3/organizations/' + CONFIG.EVENTBRITE_ORG_ID +
    '/events/?order_by=start_desc&page_size=5', {headers: {'Authorization': 'Bearer ' + ebToken_()}, muteHttpExceptions: true});
  if (resp.getResponseCode() !== 200) {
    Logger.log('Eventbrite ERROR ' + resp.getResponseCode() + ': ' + resp.getContentText());
    return;
  }
  var evs = JSON.parse(resp.getContentText()).events.map(function(e) {
    return {id: e.id, name: e.name.text, date: e.start.local.slice(0, 10), eventbrite: e.url};
  });
  var stats = getAttendanceStats(evs);
  if (!stats.success) { Logger.log('ERROR: ' + stats.error); return; }
  stats.events.forEach(function(s, i) {
    var m = s.candidates.filter(function(c) { return c.key === s.autoKey; })[0];
    Logger.log(evs[i].date + ' ' + evs[i].name + ': registered ' + s.registered + (s.ebError ? ' (' + s.ebError + ')' : '') +
      ', attended ' + (m ? m.count + ' (report: "' + m.title + '")' : 'no matching report'));
  });
}

function testConfig() {
  try { var ss=SpreadsheetApp.openById(CONFIG.TRACKER_SHEET_ID); Logger.log('Sheet OK: '+ss.getName()); } catch(e) { Logger.log('Sheet ERROR: '+e.message); }
  if (CONFIG.BRIEF_FOLDER_ID) { try { var f=DriveApp.getFolderById(CONFIG.BRIEF_FOLDER_ID); Logger.log('Folder OK: '+f.getName()); } catch(e) { Logger.log('Folder ERROR: '+e.message); } }
  Logger.log('Chat webhook: ' + (CONFIG.CHAT_WEBHOOK_URL ? 'configured' : 'NOT configured'));
  Logger.log('Eventbrite: ' + (ebToken_() ? 'configured' : 'NOT configured') + ' (org: ' + CONFIG.EVENTBRITE_ORG_ID + ')');
}
