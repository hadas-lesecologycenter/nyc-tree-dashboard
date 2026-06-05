/**
 * Forms.gs — Creates Google Forms for checkout and return,
 * and handles form submission events.
 *
 * Run from  Tool Library > Create / Update Checkout Form  (or Return Form)
 * every time your tool inventory changes significantly.
 */

// ── Checkout form ─────────────────────────────────────────────────────────────

function createCheckoutForm() {
  const settings = getSettings();
  const orgName  = settings['orgName'] || 'Tool Library';
  const ui       = SpreadsheetApp.getUi();

  let form = openOrCreateForm('checkoutFormId', orgName + ' — Checkout Request');
  clearFormItems(form);

  form.setTitle(orgName + ' — Checkout Request');
  form.setDescription(
    'Use this form to request a tool. You will receive an email confirmation once your checkout is processed.'
  );
  form.setCollectEmail(false);
  form.setConfirmationMessage('Thank you! Your checkout request has been received. Check your email for confirmation.');

  // Tool dropdown — populated from current Available tools
  const tools = getAvailableTools();
  const choices = tools.map(r => {
    const avail = getAvailableQty(r[TC.ID - 1]);
    const total = parseInt(r[TC.QUANTITY - 1]) || 1;
    return r[TC.NAME - 1] + ' [' + r[TC.ID - 1] + '] — ' + avail + '/' + total + ' available';
  });
  if (choices.length === 0) choices.push('(No tools currently available — check back soon)');

  form.addListItem()
    .setTitle('Which tool would you like to borrow?')
    .setChoiceValues(choices)
    .setRequired(true);

  form.addTextItem().setTitle('Your Full Name').setRequired(true);
  form.addTextItem().setTitle('Your Email Address').setRequired(true);
  form.addTextItem().setTitle('Your Phone Number').setRequired(false);
  form.addDateItem().setTitle('Expected Return Date').setRequired(true);
  form.addParagraphTextItem().setTitle('Notes or questions (optional)').setRequired(false);

  // Link to spreadsheet and set up trigger
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss().getId());
  ensureFormTrigger(form.getId(), 'handleCheckoutSubmit');

  saveSetting('checkoutFormId',      form.getId());
  saveSetting('checkoutFormUrl',     form.getPublishedUrl());
  saveSetting('checkoutFormEditUrl', form.getEditUrl());

  ui.alert(
    '✅ Checkout Form Ready',
    'Share this URL with borrowers:\n' + form.getPublishedUrl() +
    '\n\nAdmin edit link:\n' + form.getEditUrl(),
    ui.ButtonSet.OK,
  );
}

// ── Return form ───────────────────────────────────────────────────────────────

function createReturnForm() {
  const settings = getSettings();
  const orgName  = settings['orgName'] || 'Tool Library';
  const ui       = SpreadsheetApp.getUi();

  let form = openOrCreateForm('returnFormId', orgName + ' — Return a Tool');
  clearFormItems(form);

  form.setTitle(orgName + ' — Return a Tool');
  form.setDescription(
    'Use this form to log a tool return. Please place the tool back in its proper storage location.'
  );
  form.setCollectEmail(false);
  form.setConfirmationMessage('Thank you for returning the tool! Your return has been logged.');

  form.addTextItem().setTitle('Your Full Name').setRequired(true);
  form.addTextItem().setTitle('Tool Name or Loan ID').setRequired(true);
  form.addMultipleChoiceItem()
    .setTitle('Tool Condition on Return')
    .setChoiceValues(CONDITIONS)
    .setRequired(true);
  form.addParagraphTextItem()
    .setTitle('Any damage, issues, or notes? (optional)')
    .setRequired(false);

  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss().getId());
  ensureFormTrigger(form.getId(), 'handleReturnSubmit');

  saveSetting('returnFormId',      form.getId());
  saveSetting('returnFormUrl',     form.getPublishedUrl());
  saveSetting('returnFormEditUrl', form.getEditUrl());

  ui.alert(
    '✅ Return Form Ready',
    'Share this URL with borrowers:\n' + form.getPublishedUrl() +
    '\n\nAdmin edit link:\n' + form.getEditUrl(),
    ui.ButtonSet.OK,
  );
}

// ── Form helpers ──────────────────────────────────────────────────────────────

function openOrCreateForm(settingKey, fallbackTitle) {
  const settings = getSettings();
  if (settings[settingKey]) {
    try { return FormApp.openById(settings[settingKey]); } catch (e) { /* form deleted */ }
  }
  return FormApp.create(fallbackTitle);
}

function clearFormItems(form) {
  form.getItems().forEach(item => form.deleteItem(item));
}

function ensureFormTrigger(formId, handlerFn) {
  const existing = ScriptApp.getProjectTriggers().find(t =>
    t.getHandlerFunction() === handlerFn &&
    t.getTriggerSource()   === ScriptApp.TriggerSource.FORMS
  );
  if (!existing) {
    ScriptApp.newTrigger(handlerFn).forForm(formId).onFormSubmit().create();
  }
}

// ── Checkout form submission handler ─────────────────────────────────────────

function handleCheckoutSubmit(e) {
  try {
    const resp   = e.response;
    const rmap   = responseMap(resp);
    const settings = getSettings();

    const toolSelection = rmap['Which tool would you like to borrow?'] || '';
    // Extract ID from  "Tool Name [T001]"
    const idMatch  = toolSelection.match(/\[([^\]]+)\]$/);
    const toolId   = idMatch ? idMatch[1] : null;
    const borrower = rmap['Your Full Name'] || '';
    const email    = rmap['Your Email Address'] || '';
    const phone    = rmap['Your Phone Number'] || '';
    const notes    = rmap['Notes or questions (optional)'] || '';

    const dueDateInput = rmap['Expected Return Date'];
    const loanDays     = parseInt(settings['loanPeriodDays']) || 14;

    if (!toolId || !borrower) {
      Logger.log('Checkout: missing tool or borrower — skipping');
      return;
    }

    const tool = getToolById(toolId);
    if (!tool || tool.data[TC.STATUS - 1] !== 'Available') {
      sendEmail(email, 'Tool Request — Tool Unavailable',
        `Hi ${borrower},\n\nUnfortunately the tool you requested is no longer available.\n` +
        `Please contact us to arrange an alternative.\n\n— ${settings['orgName'] || 'Tool Library'}`);
      return;
    }

    const borrowDate = new Date();
    let dueDate;
    if (dueDateInput) {
      dueDate = new Date(dueDateInput);
    } else {
      dueDate = new Date();
      dueDate.setDate(dueDate.getDate() + loanDays);
    }

    const loanId = checkOutTool(toolId, borrower, email, phone, borrowDate, dueDate);

    // Save notes
    if (notes) {
      const lSheet = loansSheet();
      const data   = lSheet.getDataRange().getValues();
      for (let i = 1; i < data.length; i++) {
        if (data[i][LC.ID - 1] === loanId) {
          lSheet.getRange(i + 1, LC.NOTES).setValue(notes);
          break;
        }
      }
    }

    // Confirmation email
    if (email) {
      const dueFmt = Utilities.formatDate(dueDate, Session.getScriptTimeZone(), 'MMMM d, yyyy');
      sendEmail(email, '✅ Tool Checked Out: ' + tool.data[TC.NAME - 1],
        `Hi ${borrower},\n\nYour checkout is confirmed!\n\n` +
        `Tool:     ${tool.data[TC.NAME - 1]}\n` +
        `Loan ID:  ${loanId}\n` +
        `Due Date: ${dueFmt}\n` +
        `Location: ${tool.data[TC.LOCATION - 1]}\n\n` +
        `Please return the tool by the due date in the same condition you received it.\n\n` +
        `Thank you,\n${settings['orgName'] || 'Tool Library'}`);
    }

    updateDashboard();
  } catch (err) {
    Logger.log('handleCheckoutSubmit error: ' + err.toString());
  }
}

// ── Return form submission handler ────────────────────────────────────────────

function handleReturnSubmit(e) {
  try {
    const resp      = e.response;
    const rmap      = responseMap(resp);
    const settings  = getSettings();

    const borrower  = rmap['Your Full Name'] || '';
    const toolInput = rmap['Tool Name or Loan ID'] || '';
    const condition = rmap['Tool Condition on Return'] || '';
    const notes     = rmap['Any damage, issues, or notes? (optional)'] || '';

    // Find tool — try loan ID first, then tool name
    let toolId = findToolIdFromReturnInput(toolInput);
    if (!toolId) {
      Logger.log('Return: could not find tool for input: ' + toolInput);
      return;
    }

    returnTool(toolId, new Date(), condition, notes);

    // Look up borrower email from the now-returned loan record
    const lSheet = loansSheet();
    const data   = lSheet.getDataRange().getValues();
    let email    = '';
    for (let i = data.length - 1; i >= 1; i--) {
      if (String(data[i][LC.TOOL_ID - 1]).trim() === String(toolId).trim()) {
        email = data[i][LC.EMAIL - 1];
        break;
      }
    }

    const tool = getToolById(toolId);
    if (email) {
      sendEmail(email, '✅ Tool Returned: ' + (tool ? tool.data[TC.NAME - 1] : toolInput),
        `Hi ${borrower},\n\nWe've logged your tool return.\n\n` +
        `Tool:            ${tool ? tool.data[TC.NAME - 1] : toolInput}\n` +
        `Return Date:     ${Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'MMMM d, yyyy')}\n` +
        `Condition Noted: ${condition}\n\n` +
        `Thank you for using the ${settings['orgName'] || 'Tool Library'}!`);
    }

    updateDashboard();
  } catch (err) {
    Logger.log('handleReturnSubmit error: ' + err.toString());
  }
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function responseMap(formResponse) {
  const map = {};
  formResponse.getItemResponses().forEach(r => {
    map[r.getItem().getTitle()] = r.getResponse();
  });
  return map;
}

function findToolIdFromReturnInput(input) {
  input = input.trim();
  // Try as loan ID → look up tool
  const lSheet = loansSheet();
  const lData  = lSheet.getDataRange().getValues();
  for (let i = 1; i < lData.length; i++) {
    if (String(lData[i][LC.ID - 1]).trim() === input && !lData[i][LC.RETURN_DATE - 1]) {
      return lData[i][LC.TOOL_ID - 1];
    }
  }
  // Try as tool ID
  if (getToolById(input)) return input;
  // Try as tool name
  const byName = getToolByName(input);
  if (byName) return byName.data[TC.ID - 1];
  return null;
}
