/**
 * Reminders.gs — Sends overdue email reminders to borrowers
 * and a summary digest to the admin.
 *
 * Runs automatically if you set up the daily trigger via
 * Tool Library > Setup Daily Reminder Trigger
 */

function sendOverdueReminders() {
  const lSheet   = loansSheet();
  const data     = lSheet.getDataRange().getValues();
  const settings = getSettings();
  const orgName  = settings['orgName']  || 'Tool Library';
  const adminEmail = settings['adminEmail'] || Session.getActiveUser().getEmail();
  const now      = new Date();

  const overdueItems = [];

  for (let i = 1; i < data.length; i++) {
    const row = data[i];
    if (!row[LC.ID - 1])           continue; // empty row
    if (row[LC.RETURN_DATE - 1])   continue; // already returned
    const due = row[LC.DUE_DATE - 1];
    if (!due)                      continue;
    const dueDate = new Date(due);
    if (dueDate >= now)            continue; // not overdue

    const daysOverdue    = Math.floor((now - dueDate) / 86400000);
    const borrowerEmail  = row[LC.EMAIL - 1];
    const borrowerName   = row[LC.BORROWER_NAME - 1];
    const toolName       = row[LC.TOOL_NAME - 1];
    const loanId         = row[LC.ID - 1];
    const dueFmt         = Utilities.formatDate(dueDate, Session.getScriptTimeZone(), 'MMMM d, yyyy');

    // Mark as overdue in sheet
    lSheet.getRange(i + 1, LC.STATUS).setValue('Overdue');

    // Email the borrower
    if (borrowerEmail) {
      const subject = `⚠️ Overdue Tool Reminder: ${toolName} — ${daysOverdue} day${daysOverdue === 1 ? '' : 's'} late`;
      const body =
        `Hi ${borrowerName},\n\n` +
        `This is a friendly reminder that the following tool is overdue:\n\n` +
        `  Tool:         ${toolName}\n` +
        `  Loan ID:      ${loanId}\n` +
        `  Due Date:     ${dueFmt}\n` +
        `  Days Overdue: ${daysOverdue}\n\n` +
        `Please return the tool as soon as possible. If you need more time, ` +
        `contact us to arrange an extension.\n\n` +
        `Thank you,\n${orgName}`;
      sendEmail(borrowerEmail, subject, body);
    }

    overdueItems.push(
      `  • ${toolName} — borrowed by ${borrowerName}` +
      `${borrowerEmail ? ' (' + borrowerEmail + ')' : ''}, ${daysOverdue} day${daysOverdue === 1 ? '' : 's'} overdue`
    );
  }

  // Admin summary
  if (overdueItems.length > 0 && adminEmail) {
    const subject = `📋 ${orgName}: ${overdueItems.length} Overdue Tool${overdueItems.length === 1 ? '' : 's'}`;
    const body =
      `Hi Admin,\n\n` +
      `Overdue reminders have been sent to borrowers. Here is today's overdue summary:\n\n` +
      overdueItems.join('\n') + '\n\n' +
      `View full details in your Tool Library spreadsheet.\n\n` +
      `— ${orgName} Automated System`;
    sendEmail(adminEmail, subject, body);
  }

  // User feedback
  const ui = SpreadsheetApp.getUi();
  if (overdueItems.length === 0) {
    ui.alert('✅ No Overdue Loans', 'All loans are current. No reminders sent.', ui.ButtonSet.OK);
  } else {
    ui.alert(
      `📧 Reminders Sent`,
      `Sent overdue reminders for ${overdueItems.length} loan${overdueItems.length === 1 ? '' : 's'}.\n` +
      `An admin summary was sent to ${adminEmail}.`,
      ui.ButtonSet.OK,
    );
  }

  updateDashboard();
}

// ── Daily trigger setup ───────────────────────────────────────────────────────

function setupDailyTrigger() {
  // Remove any existing daily triggers for sendOverdueReminders
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'sendOverdueReminders')
    .forEach(t => ScriptApp.deleteTrigger(t));

  ScriptApp.newTrigger('sendOverdueReminders')
    .timeBased()
    .everyDays(1)
    .atHour(8)
    .create();

  SpreadsheetApp.getUi().alert(
    '⏰ Daily Trigger Active',
    'Overdue reminders will now run automatically every morning at 8 AM.\n\n' +
    'You can also run them manually at any time from the menu.',
    SpreadsheetApp.getUi().ButtonSet.OK,
  );
}
