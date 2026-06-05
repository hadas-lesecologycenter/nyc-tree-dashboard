/**
 * Setup.gs — Creates and formats all spreadsheet tabs.
 * Run from  Tool Library > ⚙️ Initial Setup
 */

function setupSpreadsheet() {
  const ui = SpreadsheetApp.getUi();
  const res = ui.alert(
    'Initial Setup',
    'This will create all required sheets with headers, formatting, and sample data.\n\n' +
    'Existing sheets with the same name will NOT be overwritten — only empty ones will be populated.\n\nContinue?',
    ui.ButtonSet.YES_NO,
  );
  if (res !== ui.Button.YES) return;

  createSettingsSheet();
  createToolsSheet();
  createLoansSheet();
  createBorrowersSheet();
  createDashboardSheet();
  updateDashboard();

  const dash = ss().getSheetByName(SHEET_NAMES.DASHBOARD);
  ss().setActiveSheet(dash);
  ss().moveActiveSheet(1);

  ui.alert(
    '✅ Setup Complete!',
    'All sheets have been created.\n\n' +
    'Next steps:\n' +
    '1. Open the Settings sheet and fill in your org name and admin email\n' +
    '2. Add tools to the "Tools Inventory" sheet\n' +
    '3. Run  Tool Library > Create / Update Checkout Form\n' +
    '4. Run  Tool Library > Create / Update Return Form\n' +
    '5. Run  Tool Library > Setup Daily Reminder Trigger\n' +
    '6. Deploy as a Web App (see README)',
    ui.ButtonSet.OK,
  );
}

function getOrCreateSheet(name) {
  return ss().getSheetByName(name) || ss().insertSheet(name);
}

// ── Settings sheet ────────────────────────────────────────────────────────────

function createSettingsSheet() {
  const sheet = getOrCreateSheet(SHEET_NAMES.SETTINGS);
  if (sheet.getLastRow() > 1) return;

  sheet.clearContents();
  sheet.getRange(1, 1, 1, 3).setValues([['Setting', 'Value', 'Description']])
    .setBackground('#37474F').setFontColor('#FFFFFF').setFontWeight('bold');

  const defaults = [
    ['orgName',              'My Tool Lending Library', 'Your organization name (appears in emails and forms)'],
    ['adminEmail',           Session.getActiveUser().getEmail(), 'Admin email — receives overdue summaries'],
    ['loanPeriodDays',       14,  'Default loan length in days'],
    ['reminderDaysOverdue',  1,   'Send borrower reminder when loan is this many days overdue'],
    ['checkoutFormId',       '',  'Auto-filled when you run Create Checkout Form'],
    ['checkoutFormUrl',      '',  'Auto-filled — share this URL with borrowers'],
    ['checkoutFormEditUrl',  '',  'Auto-filled — admin edit link'],
    ['returnFormId',         '',  'Auto-filled when you run Create Return Form'],
    ['returnFormUrl',        '',  'Auto-filled — share this URL with borrowers'],
    ['returnFormEditUrl',    '',  'Auto-filled — admin edit link'],
  ];

  sheet.getRange(2, 1, defaults.length, 3).setValues(defaults);
  sheet.getRange(2, 1, defaults.length, 1).setFontWeight('bold');
  sheet.setColumnWidths(1, 1, 200);
  sheet.setColumnWidths(2, 1, 350);
  sheet.setColumnWidths(3, 1, 370);
  sheet.setFrozenRows(1);
  sheet.setTabColor('#607D8B');
}

// ── Tools Inventory sheet ─────────────────────────────────────────────────────

function createToolsSheet() {
  const sheet = getOrCreateSheet(SHEET_NAMES.TOOLS);
  const isNew = sheet.getLastRow() === 0;

  if (isNew) {
    sheet.getRange(1, 1, 1, 10).setValues([[
      'Tool ID', 'Tool Name', 'Category', 'Condition', 'Total Quantity',
      'Status', 'Location / Storage Bin',
      'Photo URL (Google Drive "Anyone with link" share URL)', 'Notes', 'Date Added',
    ]]).setBackground('#2E7D32').setFontColor('#FFFFFF').setFontWeight('bold').setWrap(true);

    const today = new Date();
    sheet.getRange(2, 1, 3, 10).setValues([
      ['T001', 'Hammer (16 oz)',         'Hand Tools',     'Good',      3, 'Available', 'Bin A1',  '', 'Standard claw hammer',             today],
      ['T002', 'Cordless Drill',         'Power Tools',    'Excellent', 2, 'Available', 'Shelf B2','', '20V with 2 batteries + charger',   today],
      ['T003', 'Measuring Tape (25 ft)', 'Measuring Tools','Good',      5, 'Available', 'Bin A1',  '', '',                                  today],
    ]);
  }

  applyToolsFormatting(sheet);
  sheet.setTabColor('#4CAF50');
}

function applyToolsFormatting(sheet) {
  sheet.setColumnWidths(TC.ID,       1, 80);
  sheet.setColumnWidths(TC.NAME,     1, 210);
  sheet.setColumnWidths(TC.CATEGORY, 1, 140);
  sheet.setColumnWidths(TC.CONDITION,1, 110);
  sheet.setColumnWidths(TC.QUANTITY, 1, 120);
  sheet.setColumnWidths(TC.STATUS,   1, 115);
  sheet.setColumnWidths(TC.LOCATION, 1, 190);
  sheet.setColumnWidths(TC.PHOTO_URL,1, 280);
  sheet.setColumnWidths(TC.NOTES,    1, 220);
  sheet.setColumnWidths(TC.DATE_ADDED,1,110);

  // Dropdowns
  sheet.getRange(2, TC.STATUS,    999, 1)
    .setDataValidation(SpreadsheetApp.newDataValidation()
      .requireValueInList(TOOL_STATUSES).setAllowInvalid(false).build());
  sheet.getRange(2, TC.CONDITION, 999, 1)
    .setDataValidation(SpreadsheetApp.newDataValidation()
      .requireValueInList(CONDITIONS).setAllowInvalid(false).build());
  sheet.getRange(2, TC.CATEGORY,  999, 1)
    .setDataValidation(SpreadsheetApp.newDataValidation()
      .requireValueInList(CATEGORIES).setAllowInvalid(false).build());
  // Quantity must be a positive integer
  sheet.getRange(2, TC.QUANTITY, 999, 1)
    .setDataValidation(SpreadsheetApp.newDataValidation()
      .requireNumberGreaterThan(0).setAllowInvalid(false)
      .setHelpText('Enter the total number of this tool you own').build());

  // Status colour coding
  const statusColors = {
    Available:   { bg: '#E8F5E9', fg: '#1B5E20' },
    Borrowed:    { bg: '#FFF3E0', fg: '#E65100' },
    Maintenance: { bg: '#FFF8E1', fg: '#F57F17' },
    Retired:     { bg: '#ECEFF1', fg: '#546E7A' },
  };
  const statusRange = [sheet.getRange(2, TC.STATUS, 999, 1)];
  sheet.setConditionalFormatRules(
    Object.entries(statusColors).map(([status, c]) =>
      SpreadsheetApp.newConditionalFormatRule()
        .whenTextEqualTo(status).setBackground(c.bg).setFontColor(c.fg)
        .setRanges(statusRange).build()
    )
  );

  sheet.getRange(2, TC.DATE_ADDED, 999, 1).setNumberFormat('MM/dd/yyyy');
  sheet.setFrozenRows(1);
}

// ── Loans sheet ───────────────────────────────────────────────────────────────

function createLoansSheet() {
  const sheet = getOrCreateSheet(SHEET_NAMES.LOANS);
  const isNew = sheet.getLastRow() === 0;

  if (isNew) {
    sheet.getRange(1, 1, 1, 13).setValues([[
      'Loan ID', 'Tool ID', 'Tool Name', 'Qty', 'Borrower Name',
      'Email', 'Phone', 'Borrow Date', 'Due Date',
      'Return Date', 'Return Condition', 'Status', 'Notes',
    ]]).setBackground('#1565C0').setFontColor('#FFFFFF').setFontWeight('bold');
  }

  applyLoansFormatting(sheet);
  sheet.setTabColor('#2196F3');
}

function applyLoansFormatting(sheet) {
  sheet.setColumnWidths(LC.ID,              1, 80);
  sheet.setColumnWidths(LC.TOOL_ID,         1, 80);
  sheet.setColumnWidths(LC.TOOL_NAME,       1, 190);
  sheet.setColumnWidths(LC.QTY,             1, 60);
  sheet.setColumnWidths(LC.BORROWER_NAME,   1, 160);
  sheet.setColumnWidths(LC.EMAIL,           1, 210);
  sheet.setColumnWidths(LC.PHONE,           1, 130);
  sheet.setColumnWidths(LC.BORROW_DATE,     1, 110);
  sheet.setColumnWidths(LC.DUE_DATE,        1, 110);
  sheet.setColumnWidths(LC.RETURN_DATE,     1, 110);
  sheet.setColumnWidths(LC.RETURN_CONDITION,1, 145);
  sheet.setColumnWidths(LC.STATUS,          1, 100);
  sheet.setColumnWidths(LC.NOTES,           1, 220);

  sheet.getRange(2, LC.BORROW_DATE,  999, 1).setNumberFormat('MM/dd/yyyy');
  sheet.getRange(2, LC.DUE_DATE,     999, 1).setNumberFormat('MM/dd/yyyy');
  sheet.getRange(2, LC.RETURN_DATE,  999, 1).setNumberFormat('MM/dd/yyyy');

  const statusRange = [sheet.getRange(2, LC.STATUS, 999, 1)];
  sheet.setConditionalFormatRules([
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo('Active').setBackground('#E3F2FD').setFontColor('#0D47A1')
      .setRanges(statusRange).build(),
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo('Overdue').setBackground('#FFEBEE').setFontColor('#B71C1C')
      .setRanges(statusRange).build(),
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo('Returned').setBackground('#E8F5E9').setFontColor('#1B5E20')
      .setRanges(statusRange).build(),
  ]);

  sheet.setFrozenRows(1);
}

// ── Borrowers sheet ───────────────────────────────────────────────────────────

function createBorrowersSheet() {
  const sheet = getOrCreateSheet(SHEET_NAMES.BORROWERS);
  const isNew = sheet.getLastRow() === 0;

  if (isNew) {
    sheet.getRange(1, 1, 1, 6).setValues([[
      'Borrower ID', 'Name', 'Email', 'Phone', 'Total Loans', 'Last Loan Date',
    ]]).setBackground('#6A1B9A').setFontColor('#FFFFFF').setFontWeight('bold');
  }

  sheet.setColumnWidths(BC.ID,             1, 110);
  sheet.setColumnWidths(BC.NAME,           1, 180);
  sheet.setColumnWidths(BC.EMAIL,          1, 220);
  sheet.setColumnWidths(BC.PHONE,          1, 130);
  sheet.setColumnWidths(BC.TOTAL_LOANS,    1, 105);
  sheet.setColumnWidths(BC.LAST_LOAN_DATE, 1, 130);
  sheet.getRange(2, BC.LAST_LOAN_DATE, 999, 1).setNumberFormat('MM/dd/yyyy');
  sheet.setFrozenRows(1);
  sheet.setTabColor('#9C27B0');
}

// ── Dashboard shell ───────────────────────────────────────────────────────────

function createDashboardSheet() {
  const sheet = getOrCreateSheet(SHEET_NAMES.DASHBOARD);
  sheet.clearContents();
  sheet.clearFormats();

  sheet.getRange('A1:F1').merge()
    .setValue('🔧 Tool Lending Library — Dashboard')
    .setBackground('#1A237E').setFontColor('#FFFFFF')
    .setFontSize(18).setFontWeight('bold')
    .setHorizontalAlignment('center').setVerticalAlignment('middle');
  sheet.setRowHeight(1, 52);

  sheet.getRange('A2:F2').merge()
    .setBackground('#E8EAF6').setFontColor('#5C6BC0').setFontStyle('italic')
    .setHorizontalAlignment('center');

  sheet.setColumnWidths(1, 1, 220);
  sheet.setColumnWidths(2, 1, 150);
  sheet.setColumnWidths(3, 1, 50);
  sheet.setColumnWidths(4, 1, 220);
  sheet.setColumnWidths(5, 1, 150);
  sheet.setColumnWidths(6, 1, 50);
  sheet.setTabColor('#F44336');
}
