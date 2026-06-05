/**
 * Tool Lending Library — Google Apps Script
 * ==========================================
 * Manages tool inventory, borrower records, checkout/return workflows,
 * Google Form integration, overdue email reminders, and a live dashboard.
 *
 * SETUP: Open the spreadsheet, then run  Tool Library > ⚙️ Initial Setup
 */

// ── Sheet names ───────────────────────────────────────────────────────────────

const SHEET_NAMES = {
  DASHBOARD: 'Dashboard',
  TOOLS:     'Tools Inventory',
  LOANS:     'Loans',
  BORROWERS: 'Borrowers',
  SETTINGS:  'Settings',
};

// ── Column indices (1-based) ──────────────────────────────────────────────────

// Tools Inventory
const TC = {
  ID: 1, NAME: 2, CATEGORY: 3, CONDITION: 4, QUANTITY: 5,
  STATUS: 6, LOCATION: 7, PHOTO_URL: 8, NOTES: 9, DATE_ADDED: 10,
};

// Loans
const LC = {
  ID: 1, TOOL_ID: 2, TOOL_NAME: 3, QTY: 4, BORROWER_NAME: 5,
  EMAIL: 6, PHONE: 7, BORROW_DATE: 8, DUE_DATE: 9,
  RETURN_DATE: 10, RETURN_CONDITION: 11, STATUS: 12, NOTES: 13,
};

// Borrowers
const BC = {
  ID: 1, NAME: 2, EMAIL: 3, PHONE: 4, TOTAL_LOANS: 5, LAST_LOAN_DATE: 6,
};

// ── Lookup lists ──────────────────────────────────────────────────────────────

const TOOL_STATUSES = ['Available', 'Borrowed', 'Maintenance', 'Retired'];
const CONDITIONS    = ['Excellent', 'Good', 'Fair', 'Poor', 'Broken'];
const CATEGORIES    = [
  'Hand Tools', 'Power Tools', 'Garden Tools', 'Measuring Tools',
  'Safety Equipment', 'Ladders', 'Plumbing', 'Electrical', 'Other',
];

// ── Menu ──────────────────────────────────────────────────────────────────────

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🔧 Tool Library')
    .addItem('⚙️ Initial Setup (run first!)', 'setupSpreadsheet')
    .addSeparator()
    .addItem('🔄 Refresh Dashboard', 'updateDashboard')
    .addSeparator()
    .addItem('📋 Create / Update Checkout Form', 'createCheckoutForm')
    .addItem('📋 Create / Update Return Form',   'createReturnForm')
    .addSeparator()
    .addItem('➕ Add New Tool',                  'showAddToolDialog')
    .addItem('📤 Check Out Tool (manual)',        'showCheckoutDialog')
    .addItem('📥 Return Tool (manual)',           'showReturnDialog')
    .addSeparator()
    .addItem('📧 Send Overdue Reminders Now',    'sendOverdueReminders')
    .addItem('⏰ Setup Daily Reminder Trigger',  'setupDailyTrigger')
    .addSeparator()
    .addItem('🌐 Get Web App URL',               'showWebAppUrl')
    .toUi();
}

// ── Settings helpers ──────────────────────────────────────────────────────────

function getSettings() {
  const sheet = ss().getSheetByName(SHEET_NAMES.SETTINGS);
  if (!sheet) return {};
  const s = {};
  sheet.getDataRange().getValues().slice(1).forEach(r => {
    if (r[0]) s[String(r[0]).trim()] = r[1];
  });
  return s;
}

function saveSetting(key, value) {
  const sheet = ss().getSheetByName(SHEET_NAMES.SETTINGS);
  const data  = sheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][0]).trim() === key) {
      sheet.getRange(i + 1, 2).setValue(value);
      return;
    }
  }
  sheet.appendRow([key, value]);
}

// ── ID generation ─────────────────────────────────────────────────────────────

function generateId(prefix, sheet, col) {
  const last = sheet.getLastRow();
  if (last <= 1) return prefix + '001';
  const nums = sheet.getRange(2, col, last - 1, 1).getValues()
    .flat()
    .filter(v => v && String(v).startsWith(prefix))
    .map(v => parseInt(String(v).slice(prefix.length)) || 0);
  return prefix + String((nums.length ? Math.max(...nums) : 0) + 1).padStart(3, '0');
}

// ── Sheet accessors ───────────────────────────────────────────────────────────

function ss()             { return SpreadsheetApp.getActiveSpreadsheet(); }
function toolsSheet()     { return ss().getSheetByName(SHEET_NAMES.TOOLS); }
function loansSheet()     { return ss().getSheetByName(SHEET_NAMES.LOANS); }
function borrowersSheet() { return ss().getSheetByName(SHEET_NAMES.BORROWERS); }

// ── Tool helpers ──────────────────────────────────────────────────────────────

function getToolById(id) {
  const sheet = toolsSheet();
  const data  = sheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][TC.ID - 1]).trim() === String(id).trim())
      return { row: i + 1, data: data[i] };
  }
  return null;
}

function getToolByName(name) {
  const sheet = toolsSheet();
  const data  = sheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][TC.NAME - 1]).trim().toLowerCase() === name.trim().toLowerCase())
      return { row: i + 1, data: data[i] };
  }
  return null;
}

function setToolStatus(toolRow, status) {
  toolsSheet().getRange(toolRow, TC.STATUS).setValue(status);
}

/** Returns how many of a tool are currently available (total minus active loans). */
function getAvailableQty(toolId) {
  const tool  = getToolById(toolId);
  if (!tool) return 0;
  const total = parseInt(tool.data[TC.QUANTITY - 1]) || 1;
  const out   = loansSheet().getDataRange().getValues().slice(1)
    .filter(r => String(r[LC.TOOL_ID - 1]).trim() === String(toolId).trim() && !r[LC.RETURN_DATE - 1])
    .reduce((sum, r) => sum + (parseInt(r[LC.QTY - 1]) || 1), 0);
  return Math.max(0, total - out);
}

function getAvailableTools() {
  const sheet = toolsSheet();
  const data  = sheet.getDataRange().getValues().slice(1).filter(r => r[TC.ID - 1]);
  return data.filter(r => {
    const status = r[TC.STATUS - 1];
    if (status === 'Maintenance' || status === 'Retired') return false;
    return getAvailableQty(r[TC.ID - 1]) > 0;
  });
}

// ── Loan helpers ──────────────────────────────────────────────────────────────

function getActiveLoansForTool(toolId) {
  const sheet = loansSheet();
  const data  = sheet.getDataRange().getValues();
  const result = [];
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][LC.TOOL_ID - 1]).trim() === String(toolId).trim() &&
        !data[i][LC.RETURN_DATE - 1])
      result.push({ row: i + 1, data: data[i] });
  }
  return result;
}

// Returns the most recent active loan for a tool (for single-item returns)
function getActiveLoanForTool(toolId) {
  const loans = getActiveLoansForTool(toolId);
  return loans.length ? loans[loans.length - 1] : null;
}

// ── Borrower helpers ──────────────────────────────────────────────────────────

function findOrCreateBorrower(name, email, phone) {
  const sheet = borrowersSheet();
  const data  = sheet.getDataRange().getValues();
  if (email) {
    for (let i = 1; i < data.length; i++) {
      if (String(data[i][BC.EMAIL - 1]).toLowerCase() === email.toLowerCase()) return i + 1;
    }
  }
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][BC.NAME - 1]).toLowerCase() === name.toLowerCase()) return i + 1;
  }
  const id = generateId('B', sheet, BC.ID);
  sheet.appendRow([id, name, email || '', phone || '', 0, '']);
  return sheet.getLastRow();
}

function updateBorrowerStats(borrowerRow) {
  const bSheet = borrowersSheet();
  const lSheet = loansSheet();
  const email  = bSheet.getRange(borrowerRow, BC.EMAIL).getValue();
  const name   = bSheet.getRange(borrowerRow, BC.NAME).getValue();
  const loans  = lSheet.getDataRange().getValues().slice(1)
    .filter(r => r[LC.EMAIL - 1] === email || r[LC.BORROWER_NAME - 1] === name);
  bSheet.getRange(borrowerRow, BC.TOTAL_LOANS).setValue(loans.length);
  const dates = loans.map(r => r[LC.BORROW_DATE - 1]).filter(Boolean).map(d => new Date(d));
  if (dates.length)
    bSheet.getRange(borrowerRow, BC.LAST_LOAN_DATE).setValue(new Date(Math.max(...dates)));
}

// ── Core checkout / return logic ──────────────────────────────────────────────

function checkOutTool(toolId, borrowerName, email, phone, borrowDate, dueDate, qty) {
  qty = Math.max(1, parseInt(qty) || 1);

  const tool   = getToolById(toolId);
  if (!tool) throw new Error('Tool not found: ' + toolId);

  const status = tool.data[TC.STATUS - 1];
  if (status === 'Maintenance') throw new Error('This tool is currently in maintenance');
  if (status === 'Retired')     throw new Error('This tool has been retired');

  const avail = getAvailableQty(toolId);
  if (avail < qty) throw new Error(
    avail === 0
      ? 'No units of this tool are currently available'
      : `Only ${avail} available — you requested ${qty}`
  );

  const lSheet = loansSheet();
  const loanId = generateId('L', lSheet, LC.ID);
  lSheet.appendRow([
    loanId, toolId, tool.data[TC.NAME - 1], qty,
    borrowerName, email || '', phone || '',
    borrowDate, dueDate, '', '', 'Active', '',
  ]);
  const newRow = lSheet.getLastRow();
  lSheet.getRange(newRow, LC.BORROW_DATE).setNumberFormat('MM/dd/yyyy');
  lSheet.getRange(newRow, LC.DUE_DATE).setNumberFormat('MM/dd/yyyy');

  // Update tool status to reflect availability
  if (getAvailableQty(toolId) === 0) setToolStatus(tool.row, 'Borrowed');

  updateBorrowerStats(findOrCreateBorrower(borrowerName, email, phone));
  return loanId;
}

function returnTool(toolId, returnDate, returnCondition, notes, loanRow) {
  const tool = getToolById(toolId);
  if (!tool) throw new Error('Tool not found: ' + toolId);

  // If loanRow not specified, use the most recent active loan
  let loan;
  if (loanRow) {
    loan = { row: loanRow, data: loansSheet().getRange(loanRow, 1, 1, 13).getValues()[0] };
  } else {
    loan = getActiveLoanForTool(toolId);
  }
  if (!loan) throw new Error('No active loan found for: ' + tool.data[TC.NAME - 1]);

  const lSheet = loansSheet();
  lSheet.getRange(loan.row, LC.RETURN_DATE).setValue(returnDate).setNumberFormat('MM/dd/yyyy');
  lSheet.getRange(loan.row, LC.RETURN_CONDITION).setValue(returnCondition || '');
  lSheet.getRange(loan.row, LC.STATUS).setValue('Returned');
  if (notes) lSheet.getRange(loan.row, LC.NOTES).setValue(notes);
  if (returnCondition) toolsSheet().getRange(tool.row, TC.CONDITION).setValue(returnCondition);

  // Recalculate status
  const stillOut = getAvailableQty(toolId);  // now updated since loan is returned
  const total    = parseInt(tool.data[TC.QUANTITY - 1]) || 1;
  let newStatus;
  if (returnCondition === 'Broken') {
    newStatus = 'Maintenance';
  } else if (getAvailableQty(toolId) > 0) {
    newStatus = 'Available';
  } else {
    newStatus = 'Borrowed';
  }
  setToolStatus(tool.row, newStatus);

  return loan.data[LC.ID - 1];
}

// ── Email utility ─────────────────────────────────────────────────────────────

function sendEmail(to, subject, body) {
  try {
    if (!to || !to.includes('@')) return;
    GmailApp.sendEmail(to, subject, body);
  } catch (e) {
    Logger.log('sendEmail error: ' + e.toString());
  }
}
