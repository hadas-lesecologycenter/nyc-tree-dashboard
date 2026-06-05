/**
 * WebApp.gs — Serves the borrower-facing web app.
 *
 * Deploy: Apps Script → Deploy → New Deployment → Web App
 *   Execute as: Me | Who has access: Anyone
 */

function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle(getSettings()['orgName'] || 'Tool Library')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// ── Public API ────────────────────────────────────────────────────────────────

function getToolCatalog() {
  const settings = getSettings();
  const tools    = toolsSheet().getDataRange().getValues().slice(1).filter(r => r[TC.ID - 1]);
  return {
    orgName:  settings['orgName']               || 'Tool Library',
    loanDays: parseInt(settings['loanPeriodDays']) || 14,
    tools: tools.map(r => {
      const toolId   = r[TC.ID - 1];
      const total    = parseInt(r[TC.QUANTITY - 1]) || 1;
      const avail    = getAvailableQty(toolId);
      const status   = r[TC.STATUS - 1];
      return {
        id:        toolId,
        name:      r[TC.NAME - 1],
        category:  r[TC.CATEGORY - 1],
        condition: r[TC.CONDITION - 1],
        status,
        totalQty:  total,
        availQty:  avail,
        location:  r[TC.LOCATION - 1],
        photoUrl:  toDriveEmbedUrl(r[TC.PHOTO_URL - 1]),
        notes:     r[TC.NOTES - 1],
      };
    }),
  };
}

function submitCheckoutRequest(data) {
  try {
    const settings = getSettings();
    const qty      = Math.max(1, parseInt(data.qty) || 1);
    const tool     = getToolById(data.toolId);
    if (!tool) throw new Error('Tool not found');

    const avail = getAvailableQty(data.toolId);
    if (avail < qty) throw new Error(
      avail === 0
        ? 'Sorry — no units of this tool are currently available'
        : `Only ${avail} available (you requested ${qty})`
    );

    const borrowDate = new Date();
    let dueDate;
    if (data.dueDate) {
      dueDate = new Date(data.dueDate);
    } else {
      dueDate = new Date();
      dueDate.setDate(dueDate.getDate() + (parseInt(settings['loanPeriodDays']) || 14));
    }

    const loanId = checkOutTool(data.toolId, data.name, data.email, data.phone || '', borrowDate, dueDate, qty);

    if (data.email) {
      const dueFmt = Utilities.formatDate(dueDate, Session.getScriptTimeZone(), 'MMMM d, yyyy');
      sendEmail(data.email, '✅ Tool Checked Out: ' + tool.data[TC.NAME - 1],
        `Hi ${data.name},\n\nYour checkout is confirmed!\n\n` +
        `Tool:     ${tool.data[TC.NAME - 1]}\n` +
        `Quantity: ${qty}\n` +
        `Loan ID:  ${loanId}\n` +
        `Due Date: ${dueFmt}\n` +
        `Location: ${tool.data[TC.LOCATION - 1]}\n\n` +
        `Please return by the due date in the same condition.\n\n` +
        `Thank you,\n${settings['orgName'] || 'Tool Library'}`);
    }

    updateDashboard();
    return { success: true, loanId, toolName: tool.data[TC.NAME - 1] };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

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
      qty:        r[LC.QTY - 1] || 1,
      borrowDate: r[LC.BORROW_DATE - 1]
        ? Utilities.formatDate(new Date(r[LC.BORROW_DATE - 1]), tz, 'MM/dd/yyyy') : '',
      dueDate: r[LC.DUE_DATE - 1]
        ? Utilities.formatDate(new Date(r[LC.DUE_DATE - 1]), tz, 'MM/dd/yyyy') : '',
      status: r[LC.STATUS - 1],
    }));
}

function submitReturnRequest(data) {
  try {
    const settings = getSettings();
    returnTool(data.toolId, new Date(), data.condition, data.notes || '');

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
      sendEmail(email, '✅ Tool Returned: ' + (tool ? tool.data[TC.NAME - 1] : data.toolId),
        `Hi ${data.name || 'there'},\n\nWe've logged your tool return.\n\n` +
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
      '4. Who has access: Anyone with a Google account\n' +
      '5. Click Deploy\n\n' +
      'Then run this menu item again to get the URL.',
      ui.ButtonSet.OK);
    return;
  }
  ui.alert('🌐 Web App URL', 'Share this URL with borrowers:\n\n' + url, ui.ButtonSet.OK);
}

// ── Utility ───────────────────────────────────────────────────────────────────

function toDriveEmbedUrl(url) {
  if (!url) return '';
  const match = String(url).match(/\/d\/([a-zA-Z0-9_-]+)/);
  if (match) return 'https://drive.google.com/uc?export=view&id=' + match[1];
  return url;
}
