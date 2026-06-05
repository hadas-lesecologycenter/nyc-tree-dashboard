/**
 * Dashboard.gs — Refreshes the Dashboard tab with live stats.
 */

function updateDashboard() {
  const sheet = ss().getSheetByName(SHEET_NAMES.DASHBOARD);
  if (!sheet) return;

  syncLoanStatuses();

  const tools     = toolsSheet().getDataRange().getValues().slice(1).filter(r => r[TC.ID - 1]);
  const allLoans  = loansSheet().getDataRange().getValues().slice(1).filter(r => r[LC.ID - 1]);
  const borrowers = borrowersSheet().getDataRange().getValues().slice(1).filter(r => r[BC.ID - 1]);
  const now       = new Date();

  // Inventory stats — count individual units, not just tool types
  const totalUnits     = tools.reduce((s, r) => s + (parseInt(r[TC.QUANTITY - 1]) || 1), 0);
  const availableUnits = tools.reduce((s, r) => {
    if (r[TC.STATUS - 1] === 'Maintenance' || r[TC.STATUS - 1] === 'Retired') return s;
    return s + getAvailableQty(r[TC.ID - 1]);
  }, 0);
  const borrowedUnits  = allLoans
    .filter(r => !r[LC.RETURN_DATE - 1])
    .reduce((s, r) => s + (parseInt(r[LC.QTY - 1]) || 1), 0);
  const maintenanceUnits = tools
    .filter(r => r[TC.STATUS - 1] === 'Maintenance')
    .reduce((s, r) => s + (parseInt(r[TC.QUANTITY - 1]) || 1), 0);
  const retiredUnits   = tools
    .filter(r => r[TC.STATUS - 1] === 'Retired')
    .reduce((s, r) => s + (parseInt(r[TC.QUANTITY - 1]) || 1), 0);

  const stats = {
    toolTypes:   tools.length,
    totalUnits,
    availableUnits,
    borrowedUnits,
    maintenanceUnits,
    retiredUnits,
    activeLoans:   allLoans.filter(r => r[LC.STATUS - 1] === 'Active').length,
    overdueLoans:  allLoans.filter(r => r[LC.STATUS - 1] === 'Overdue').length,
    totalLoans:    allLoans.length,
    totalBorrowers:borrowers.length,
  };

  if (sheet.getLastRow() > 2)
    sheet.getRange(3, 1, sheet.getLastRow() - 2, 6).clearContent().clearFormat();

  let row = 3;

  // ── Inventory summary ────────────────────────────────────────────────────
  row = writeSectionHeader(sheet, row, '📦  INVENTORY SUMMARY');
  writeStat(sheet, row, 1, 'Tool Types',        stats.toolTypes,        '#1A237E');
  writeStat(sheet, row, 4, 'Total Units',        stats.totalUnits,       '#1A237E');
  row++;
  writeStat(sheet, row, 1, 'Units Available',    stats.availableUnits,   '#1B5E20');
  writeStat(sheet, row, 4, 'Units Borrowed',     stats.borrowedUnits,    '#E65100');
  row++;
  writeStat(sheet, row, 1, 'In Maintenance',     stats.maintenanceUnits, '#F57F17');
  writeStat(sheet, row, 4, 'Retired',            stats.retiredUnits,     '#78909C');
  row += 2;

  // ── Loans summary ────────────────────────────────────────────────────────
  row = writeSectionHeader(sheet, row, '📋  LOANS SUMMARY');
  writeStat(sheet, row, 1, 'Active Loans',         stats.activeLoans,      '#1565C0');
  writeStat(sheet, row, 4, 'Overdue Loans',         stats.overdueLoans,     '#B71C1C');
  row++;
  writeStat(sheet, row, 1, 'All-time Total Loans',  stats.totalLoans,       '#37474F');
  writeStat(sheet, row, 4, 'Registered Borrowers',  stats.totalBorrowers,   '#37474F');
  row += 2;

  // ── Overdue loans ────────────────────────────────────────────────────────
  const overdueLoans = allLoans.filter(r => r[LC.STATUS - 1] === 'Overdue');
  if (overdueLoans.length > 0) {
    row = writeSectionHeader(sheet, row, '🚨  OVERDUE LOANS', '#B71C1C');
    writeTableHeader(sheet, row,
      ['Loan ID', 'Tool Name', 'Qty', 'Borrower', 'Email', 'Due Date / Days Over'],
      '#FFCDD2', '#B71C1C');
    row++;
    overdueLoans
      .sort((a, b) => new Date(a[LC.DUE_DATE - 1]) - new Date(b[LC.DUE_DATE - 1]))
      .forEach(loan => {
        const daysOver = Math.floor((now - new Date(loan[LC.DUE_DATE - 1])) / 86400000);
        sheet.getRange(row, 1, 1, 6).setValues([[
          loan[LC.ID - 1], loan[LC.TOOL_NAME - 1], loan[LC.QTY - 1] || 1,
          loan[LC.BORROWER_NAME - 1], loan[LC.EMAIL - 1],
          Utilities.formatDate(new Date(loan[LC.DUE_DATE - 1]), Session.getScriptTimeZone(), 'MM/dd/yyyy') +
            ' (' + daysOver + ' days)',
        ]]).setBackground('#FFEBEE');
        row++;
      });
    row++;
  }

  // ── Active loans ─────────────────────────────────────────────────────────
  const activeLoans = allLoans
    .filter(r => r[LC.STATUS - 1] === 'Active')
    .sort((a, b) => new Date(a[LC.DUE_DATE - 1]) - new Date(b[LC.DUE_DATE - 1]));

  row = writeSectionHeader(sheet, row, '📤  ACTIVE LOANS');
  if (activeLoans.length === 0) {
    sheet.getRange(row, 1, 1, 3).merge().setValue('No active loans.')
      .setFontStyle('italic').setFontColor('#78909C');
    row++;
  } else {
    writeTableHeader(sheet, row,
      ['Loan ID', 'Tool Name', 'Qty', 'Borrower', 'Due Date', 'Days Remaining'],
      '#BBDEFB', '#1565C0');
    row++;
    activeLoans.forEach(loan => {
      const daysLeft = Math.ceil((new Date(loan[LC.DUE_DATE - 1]) - now) / 86400000);
      const r = sheet.getRange(row, 1, 1, 6);
      r.setValues([[
        loan[LC.ID - 1], loan[LC.TOOL_NAME - 1], loan[LC.QTY - 1] || 1,
        loan[LC.BORROWER_NAME - 1],
        loan[LC.DUE_DATE - 1], daysLeft,
      ]]);
      sheet.getRange(row, 5).setNumberFormat('MM/dd/yyyy');
      if (daysLeft <= 2) r.setBackground('#FFF9C4');
      row++;
    });
    row++;
  }

  // ── Tool inventory quick view ─────────────────────────────────────────────
  row = writeSectionHeader(sheet, row, '🗂️  TOOL INVENTORY');
  writeTableHeader(sheet, row,
    ['Tool ID', 'Tool Name', 'Category', 'Qty Available / Total', 'Status', 'Location'],
    '#C8E6C9', '#2E7D32');
  row++;
  tools.forEach(tool => {
    const avail = getAvailableQty(tool[TC.ID - 1]);
    const total = parseInt(tool[TC.QUANTITY - 1]) || 1;
    const statusColors = {
      Available:   '#E8F5E9', Borrowed: '#FFF3E0',
      Maintenance: '#FFF8E1', Retired:  '#ECEFF1',
    };
    const bg = statusColors[tool[TC.STATUS - 1]] || '#FFFFFF';
    sheet.getRange(row, 1, 1, 6).setValues([[
      tool[TC.ID - 1], tool[TC.NAME - 1], tool[TC.CATEGORY - 1],
      avail + ' / ' + total,
      tool[TC.STATUS - 1], tool[TC.LOCATION - 1],
    ]]).setBackground(bg);
    row++;
  });

  sheet.getRange('A2:F2').merge()
    .setValue('Last updated: ' + Utilities.formatDate(now, Session.getScriptTimeZone(), 'EEEE, MMMM d yyyy  h:mm a'))
    .setBackground('#E8EAF6').setFontColor('#5C6BC0').setFontStyle('italic')
    .setHorizontalAlignment('center');
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function writeSectionHeader(sheet, row, title, color) {
  color = color || '#1A237E';
  sheet.getRange(row, 1, 1, 6).merge()
    .setValue(title)
    .setBackground(color).setFontColor('#FFFFFF')
    .setFontWeight('bold').setFontSize(12);
  sheet.setRowHeight(row, 30);
  return row + 1;
}

function writeTableHeader(sheet, row, labels, bg, fg) {
  sheet.getRange(row, 1, 1, labels.length).setValues([labels])
    .setBackground(bg).setFontColor(fg).setFontWeight('bold');
}

function writeStat(sheet, row, col, label, value, color) {
  sheet.getRange(row, col).setValue(label).setFontWeight('bold').setFontColor('#37474F');
  sheet.getRange(row, col + 1).setValue(value)
    .setFontSize(16).setFontWeight('bold').setFontColor(color || '#000000');
  sheet.setRowHeight(row, 36);
}

function syncLoanStatuses() {
  const sheet = loansSheet();
  const data  = sheet.getDataRange().getValues();
  const now   = new Date();

  for (let i = 1; i < data.length; i++) {
    if (!data[i][LC.ID - 1]) continue;
    const returned = data[i][LC.RETURN_DATE - 1];
    const due      = data[i][LC.DUE_DATE - 1];
    const status   = data[i][LC.STATUS - 1];

    if (returned && status !== 'Returned') {
      sheet.getRange(i + 1, LC.STATUS).setValue('Returned');
    } else if (!returned && due && new Date(due) < now && status !== 'Overdue') {
      sheet.getRange(i + 1, LC.STATUS).setValue('Overdue');
    }
  }
}
