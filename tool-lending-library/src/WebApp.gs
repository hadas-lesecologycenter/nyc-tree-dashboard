/**
 * WebApp.gs — Serves the borrower-facing web app and exposes
 * the API endpoints called by the front end via google.script.run.
 *
 * To publish:
 *   Apps Script editor → Deploy → New Deployment → Web App
 *   Execute as: Me | Who has access: Anyone
 */

// ── Entry point ───────────────────────────────────────────────────────────────

function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle(getSettings()['orgName'] || 'Tool Library')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// ── Public API (called by google.script.run) ──────────────────────────────────

/** Returns all tools and org settings for the catalog page. */
function getToolCatalog() {
  const settings = getSettings();
  const tools    = toolsSheet().getDataRange().getValues().slice(1).filter(r => r[TC.ID - 1]);
  return {
    orgName:  settings['orgName']        || 'Tool Library',
    loanDays: parseInt(settings['loanPeriodDays']) || 14,
    tools: tools.map(r => ({
      id:        r[TC.ID - 1],
      name:      r[TC.NAME - 1],
      category:  r[TC.CATEGORY - 1],
      condition: r[TC.CONDITION - 1],
      status:    r[TC.STATUS - 1],
      location:  r[TC.LOCATION - 1],
      photoUrl:  toDriveEmbedUrl(r[TC.PHOTO_URL - 1]),
      notes:     r[TC.NOTES - 1],
    })),
  };
}

/** Processes a checkout submitted from the web app. */
function submitCheckoutRequest(data) {
  try {
    const settings = getSettings();
    const tool     = getToolById(data.toolId);
    if (!tool) throw new Error('Tool not found');
    if (tool.data[TC.STATUS - 1] !== 'Available') throw new Error('This tool is no longer available — someone may have just borrowed it');

    const borrowDate = new Date();
    let dueDate;
    if (data.dueDate) {
      dueDate = new Date(data.dueDate);
    } else {
      dueDate = new Date();
      dueDate.setDate(dueDate.getDate() + (parseInt(settings['loanPeriodDays']) || 14));
    }

    const loanId = checkOutTool(data.toolId, data.name, data.email, data.phone || '', borrowDate, dueDate);

    if (data.email) {
      const dueFmt = Utilities.formatDate(dueDate, Session.getScriptTimeZone(), 'MMMM d, yyyy');
      sendEmail(data.email, '✅ Tool Checked Out: ' + tool.data[TC.NAME - 1],
        `Hi ${data.name},\n\nYour checkout is confirmed!\n\n` +
        `Tool:     ${tool.data[TC.NAME - 1]}\n` +
        `Loan ID:  ${loanId}\n` +
        `Due Date: ${dueFmt}\n` +
        `Location: ${tool.data[TC.LOCATION - 1]}\n\n` +
        `Please return it by the due date in the same condition you received it.\n\n` +
        `Thank you,\n${settings['orgName'] || 'Tool Library'}`);
    }

    updateDashboard();
    return { success: true, loanId, toolName: tool.data[TC.NAME - 1] };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

/** Looks up active loans for a borrower by name or email. */
function lookupActiveLoans(contact) {
  contact = (contact || '').trim().toLowerCase();
  if (!contact) return [];

  const tz   = Session.getScriptTimeZone();
  const data = loansSheet().getDataRange().getValues().slice(1);

  return data
    .filter(r =>
      r[LC.ID - 1] &&
      !r[LC.RETURN_DATE - 1] &&
      (String(r[LC.EMAIL - 1]).toLowerCase()         === contact ||
       String(r[LC.BORROWER_NAME - 1]).toLowerCase() === contact)
    )
    .map(r => ({
      loanId:     r[LC.ID - 1],
      toolId:     r[LC.TOOL_ID - 1],
      toolName:   r[LC.TOOL_NAME - 1],
      borrowDate: r[LC.BORROW_DATE - 1]
        ? Utilities.formatDate(new Date(r[LC.BORROW_DATE - 1]), tz, 'MM/dd/yyyy') : '',
      dueDate: r[LC.DUE_DATE - 1]
        ? Utilities.formatDate(new Date(r[LC.DUE_DATE - 1]), tz, 'MM/dd/yyyy') : '',
      status: r[LC.STATUS - 1],
    }));
}

/** Processes a return submitted from the web app. */
function submitReturnRequest(data) {
  try {
    const settings = getSettings();
    returnTool(data.toolId, new Date(), data.condition, data.notes || '');

    // Find borrower email from the loan record
    const lData = loansSheet().getDataRange().getValues();
    let email = data.email || '';
    if (!email) {
      for (let i = lData.length - 1; i >= 1; i--) {
        if (String(lData[i][LC.TOOL_ID - 1]).trim() === String(data.toolId).trim()) {
          email = lData[i][LC.EMAIL - 1];
          break;
        }
      }
    }

    const tool = getToolById(data.toolId);
    if (email) {
      const name = data.name || 'there';
      sendEmail(email, '✅ Tool Returned: ' + (tool ? tool.data[TC.NAME - 1] : data.toolId),
        `Hi ${name},\n\nWe've logged your tool return.\n\n` +
        `Tool:            ${tool ? tool.data[TC.NAME - 1] : data.toolId}\n` +
        `Return Date:     ${Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'MMMM d, yyyy')}\n` +
        `Condition Noted: ${data.condition}\n\n` +
        `Thank you!\n${settings['orgName'] || 'Tool Library'}`);
    }

    updateDashboard();
    return { success: true, toolName: tool ? tool.data[TC.NAME - 1] : data.toolId };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

// ── Admin menu helper ─────────────────────────────────────────────────────────

function showWebAppUrl() {
  const url = ScriptApp.getService().getUrl();
  const ui  = SpreadsheetApp.getUi();
  if (!url) {
    ui.alert('Web App Not Deployed Yet',
      'To create the web app:\n\n' +
      '1. Click Deploy → New Deployment\n' +
      '2. Set type to Web App\n' +
      '3. Execute as: Me\n' +
      '4. Who has access: Anyone\n' +
      '5. Click Deploy\n\n' +
      'Then run this menu item again to get the URL.',
      ui.ButtonSet.OK);
    return;
  }
  ui.alert('🌐 Web App URL',
    'Share this URL with borrowers:\n\n' + url,
    ui.ButtonSet.OK);
}

// ── Utility ───────────────────────────────────────────────────────────────────

function toDriveEmbedUrl(url) {
  if (!url) return '';
  const match = String(url).match(/\/d\/([a-zA-Z0-9_-]+)/);
  if (match) return 'https://drive.google.com/uc?export=view&id=' + match[1];
  return url;
}
