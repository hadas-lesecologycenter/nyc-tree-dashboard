/**
 * Admin.gs — Manual admin operations via dialog prompts.
 * Used when the Google Form isn't convenient (e.g., in-person checkouts).
 *
 * Accessible from the  Tool Library  menu.
 */

// ── Add New Tool ──────────────────────────────────────────────────────────────

function showAddToolDialog() {
  const ui = SpreadsheetApp.getUi();

  const name = promptRequired(ui, '➕ Add New Tool — Step 1 of 5', 'Tool Name:');
  if (name === null) return;

  const catLabel = CATEGORIES.map((c, i) => `${i + 1}. ${c}`).join('\n');
  const catInput = promptRequired(ui, 'Category — Step 2 of 5',
    'Choose a category:\n' + catLabel + '\n\nEnter the number:');
  if (catInput === null) return;
  const catNum  = parseInt(catInput);
  const category = (!isNaN(catNum) && catNum >= 1 && catNum <= CATEGORIES.length)
    ? CATEGORIES[catNum - 1] : catInput;

  const condLabel = CONDITIONS.map((c, i) => `${i + 1}. ${c}`).join('\n');
  const condInput = promptRequired(ui, 'Condition — Step 3 of 5',
    'Tool condition:\n' + condLabel + '\n\nEnter the number:');
  if (condInput === null) return;
  const condNum   = parseInt(condInput);
  const condition = CONDITIONS[condNum - 1] || 'Good';

  const location = promptRequired(ui, 'Storage Location — Step 4 of 5',
    'Where is this tool stored?\n(e.g., Bin A1, Shelf B2, Cabinet 3):');
  if (location === null) return;

  const resp = ui.prompt('Photo URL — Step 5 of 5 (optional)',
    'Paste a Google Drive "Anyone with the link" share URL for a photo,\nor leave blank and press OK:',
    ui.ButtonSet.OK_CANCEL);
  if (resp.getSelectedButton() !== ui.Button.OK) return;
  const photoUrl = resp.getResponseText().trim();

  const noteResp = ui.prompt('Notes (optional)',
    'Any additional notes about this tool:', ui.ButtonSet.OK_CANCEL);
  if (noteResp.getSelectedButton() !== ui.Button.OK) return;
  const notes = noteResp.getResponseText().trim();

  const sheet  = toolsSheet();
  const toolId = generateId('T', sheet, TC.ID);
  sheet.appendRow([toolId, name, category, condition, 'Available', location, photoUrl, notes, new Date()]);
  sheet.getRange(sheet.getLastRow(), TC.DATE_ADDED).setNumberFormat('MM/dd/yyyy');
  applyToolsFormatting(sheet);
  updateDashboard();

  ui.alert('✅ Tool Added!',
    `"${name}" (${toolId}) has been added to the inventory.\nStatus: Available\nLocation: ${location}`,
    ui.ButtonSet.OK);
}

// ── Manual Checkout ───────────────────────────────────────────────────────────

function showCheckoutDialog() {
  const ui = SpreadsheetApp.getUi();

  const available = getAvailableTools();
  if (available.length === 0) {
    ui.alert('No Tools Available',
      'All tools are currently checked out or marked unavailable.', ui.ButtonSet.OK);
    return;
  }

  const toolList = available.map((r, i) =>
    `${i + 1}. ${r[TC.NAME - 1]} (${r[TC.ID - 1]}) — ${r[TC.LOCATION - 1] || 'no location'}`
  ).join('\n');

  const toolInput = promptRequired(ui, '📤 Check Out Tool — Step 1 of 4',
    'Available tools:\n' + toolList + '\n\nEnter the number or Tool ID:');
  if (toolInput === null) return;

  let toolId;
  const num = parseInt(toolInput);
  if (!isNaN(num) && num >= 1 && num <= available.length) {
    toolId = available[num - 1][TC.ID - 1];
  } else {
    toolId = toolInput.trim().toUpperCase();
  }

  const borrowerName = promptRequired(ui, 'Borrower — Step 2 of 4', "Borrower's full name:");
  if (borrowerName === null) return;

  const emailResp = ui.prompt('Borrower Email — Step 3 of 4',
    "Borrower's email address (for confirmation and reminders):", ui.ButtonSet.OK_CANCEL);
  if (emailResp.getSelectedButton() !== ui.Button.OK) return;
  const email = emailResp.getResponseText().trim();

  const phoneResp = ui.prompt('Borrower Phone — Step 4 of 4 (optional)',
    "Borrower's phone number:", ui.ButtonSet.OK_CANCEL);
  if (phoneResp.getSelectedButton() !== ui.Button.OK) return;
  const phone = phoneResp.getResponseText().trim();

  const settings  = getSettings();
  const loanDays  = parseInt(settings['loanPeriodDays']) || 14;
  const defaultDue = new Date();
  defaultDue.setDate(defaultDue.getDate() + loanDays);
  const defaultFmt = Utilities.formatDate(defaultDue, Session.getScriptTimeZone(), 'MM/dd/yyyy');

  const dueResp = ui.prompt('Due Date',
    `Default due date (${loanDays} days): ${defaultFmt}\n\nPress OK to accept, or enter a different date (MM/DD/YYYY):`,
    ui.ButtonSet.OK_CANCEL);
  if (dueResp.getSelectedButton() !== ui.Button.OK) return;
  const dueText   = dueResp.getResponseText().trim();
  const dueDate   = dueText ? new Date(dueText) : defaultDue;

  try {
    const loanId = checkOutTool(toolId, borrowerName, email, phone, new Date(), dueDate);
    if (email) {
      const tool    = getToolById(toolId);
      const dueFmt  = Utilities.formatDate(dueDate, Session.getScriptTimeZone(), 'MMMM d, yyyy');
      sendEmail(email, '✅ Tool Checked Out: ' + (tool ? tool.data[TC.NAME - 1] : toolId),
        `Hi ${borrowerName},\n\n` +
        `You've checked out a tool from ${settings['orgName'] || 'the Tool Library'}.\n\n` +
        `Tool:     ${tool ? tool.data[TC.NAME - 1] : toolId}\n` +
        `Loan ID:  ${loanId}\n` +
        `Due Date: ${dueFmt}\n\n` +
        `Thank you!`);
    }
    updateDashboard();
    ui.alert('✅ Checkout Complete!',
      `Loan ID: ${loanId}\nDue: ${Utilities.formatDate(dueDate, Session.getScriptTimeZone(), 'MM/dd/yyyy')}`,
      ui.ButtonSet.OK);
  } catch (err) {
    ui.alert('❌ Error', err.message, ui.ButtonSet.OK);
  }
}

// ── Manual Return ─────────────────────────────────────────────────────────────

function showReturnDialog() {
  const ui = SpreadsheetApp.getUi();

  const lSheet = loansSheet();
  const data   = lSheet.getDataRange().getValues();
  const active = data.slice(1).filter(r => r[LC.ID - 1] && !r[LC.RETURN_DATE - 1]);

  if (active.length === 0) {
    ui.alert('No Active Loans', 'There are no tools currently checked out.', ui.ButtonSet.OK);
    return;
  }

  const loanList = active.map((r, i) =>
    `${i + 1}. ${r[LC.TOOL_NAME - 1]} — borrowed by ${r[LC.BORROWER_NAME - 1]} (Loan: ${r[LC.ID - 1]})`
  ).join('\n');

  const input = promptRequired(ui, '📥 Return Tool — Step 1 of 2',
    'Active loans:\n' + loanList + '\n\nEnter the number or Loan ID:');
  if (input === null) return;

  let toolId;
  const num = parseInt(input);
  if (!isNaN(num) && num >= 1 && num <= active.length) {
    toolId = active[num - 1][LC.TOOL_ID - 1];
  } else {
    const found = active.find(r => String(r[LC.ID - 1]).trim() === input.trim());
    if (!found) {
      ui.alert('❌ Not Found', 'Could not find that loan. Please check the Loans sheet.', ui.ButtonSet.OK);
      return;
    }
    toolId = found[LC.TOOL_ID - 1];
  }

  const condLabel = CONDITIONS.map((c, i) => `${i + 1}. ${c}`).join('\n');
  const condInput = promptRequired(ui, 'Condition on Return — Step 2 of 2',
    'Condition when returned:\n' + condLabel + '\n\nEnter the number:');
  if (condInput === null) return;
  const condNum   = parseInt(condInput);
  const condition = CONDITIONS[condNum - 1] || 'Good';

  const notesResp = ui.prompt('Return Notes (optional)',
    'Describe any damage or issues (or leave blank):', ui.ButtonSet.OK_CANCEL);
  if (notesResp.getSelectedButton() !== ui.Button.OK) return;
  const notes = notesResp.getResponseText().trim();

  try {
    returnTool(toolId, new Date(), condition, notes);
    updateDashboard();
    const tool = getToolById(toolId);
    const name = tool ? tool.data[TC.NAME - 1] : toolId;
    ui.alert('✅ Return Recorded!',
      `${name} has been returned.\nCondition: ${condition}` +
      (condition === 'Broken' || condition === 'Poor'
        ? '\n⚠️ Tool has been moved to Maintenance status.' : ''),
      ui.ButtonSet.OK);
  } catch (err) {
    ui.alert('❌ Error', err.message, ui.ButtonSet.OK);
  }
}

// ── Prompt helper ─────────────────────────────────────────────────────────────

function promptRequired(ui, title, message) {
  const resp = ui.prompt(title, message, ui.ButtonSet.OK_CANCEL);
  if (resp.getSelectedButton() !== ui.Button.OK) return null;
  const val = resp.getResponseText().trim();
  if (!val) {
    ui.alert('Required', 'This field is required. Operation cancelled.', ui.ButtonSet.OK);
    return null;
  }
  return val;
}
