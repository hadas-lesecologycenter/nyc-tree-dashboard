# Tool Lending Library — Google Apps Script

A complete tool inventory and lending management system built on **Google Sheets + Google Apps Script**.

## Features

| Feature | Details |
|---|---|
| **Inventory** | Track tools with name, category, condition, status, storage location, and photo URL |
| **Loans** | Full checkout/return history with borrower contact info and due dates |
| **Borrowers** | Auto-maintained registry with total loan counts |
| **Google Forms** | Auto-generated checkout and return forms you share with borrowers |
| **Email confirmations** | Borrowers receive email when they check out or return a tool |
| **Overdue reminders** | Automatic daily emails to borrowers with overdue items + admin summary |
| **Live Dashboard** | One-tab overview with stats, overdue list, active loans, and full inventory |
| **Admin menu** | Manual checkout / return / add-tool dialogs for in-person operations |

---

## Setup (one-time, ~10 minutes)

### Step 1 — Create a new Google Spreadsheet

1. Go to [sheets.google.com](https://sheets.google.com) and create a blank spreadsheet
2. Name it something like **Tool Lending Library**

### Step 2 — Open the Apps Script editor

1. In the spreadsheet, click **Extensions → Apps Script**
2. You'll see an editor with a default `Code.gs` file

### Step 3 — Copy in the script files

Delete the default content and create these files (use the **+** button to add new files):

| File name | Content |
|---|---|
| `Code.gs` | Copy from `src/Code.gs` |
| `Setup.gs` | Copy from `src/Setup.gs` |
| `Dashboard.gs` | Copy from `src/Dashboard.gs` |
| `Forms.gs` | Copy from `src/Forms.gs` |
| `Reminders.gs` | Copy from `src/Reminders.gs` |
| `Admin.gs` | Copy from `src/Admin.gs` |

Then replace the contents of `appsscript.json` (click the gear icon ⚙️ to see it) with the contents of `src/appsscript.json`.

### Step 4 — Save and authorize

1. Click **Save** (Ctrl/Cmd + S)
2. Click **Run → onOpen** to trigger the authorization flow
3. Click **Review permissions** → choose your Google account → click **Allow**

### Step 5 — Run Initial Setup

1. Go back to your spreadsheet and **refresh the page**
2. You'll now see a **🔧 Tool Library** menu in the menu bar
3. Click **🔧 Tool Library → ⚙️ Initial Setup (run first!)**
4. Click **Yes** to confirm

This creates all five sheets: Dashboard, Tools Inventory, Loans, Borrowers, and Settings.

### Step 6 — Fill in your settings

1. Open the **Settings** sheet
2. Update `orgName` with your organization name
3. Verify `adminEmail` is correct (this is where overdue summaries are sent)
4. Adjust `loanPeriodDays` if you want a different default loan length

### Step 7 — Create your forms

1. Click **🔧 Tool Library → 📋 Create / Update Checkout Form**
2. Copy the public URL shown in the popup and share it with borrowers
3. Click **🔧 Tool Library → 📋 Create / Update Return Form**
4. Copy and share that URL too

> **Tip:** Paste both URLs into your website, email newsletters, or print them as QR codes.

### Step 8 — Enable daily overdue reminders

Click **🔧 Tool Library → ⏰ Setup Daily Reminder Trigger**

Reminders will now run automatically every morning at 8 AM.

---

## Adding Tools

**Option A — Manual (one tool at a time):**
Click **🔧 Tool Library → ➕ Add New Tool** and follow the prompts.

**Option B — Bulk (directly in the sheet):**
Open the **Tools Inventory** sheet and type rows directly. Use the column dropdowns for Status, Condition, and Category.
Tool IDs should follow the `T001`, `T002` format.

### Adding tool photos

1. Upload the photo to Google Drive
2. Right-click the file → **Share** → change to **"Anyone with the link"**
3. Copy the link and paste it into the **Photo URL** column for that tool

> Photos appear as clickable links. You can also add a column in the sheet with `=IMAGE(G2)` to display them inline.

---

## Day-to-day Operations

### Borrower checks out a tool
→ They fill out the **Checkout Form** (share the URL) — the sheet updates automatically.

### Tool is returned
→ They fill out the **Return Form** — the sheet updates automatically.

### Admin checks out / returns in person
→ Use **🔧 Tool Library → 📤 Check Out Tool (manual)** or **📥 Return Tool (manual)**

### Refresh the dashboard
→ Click **🔧 Tool Library → 🔄 Refresh Dashboard** (it also refreshes automatically after every checkout/return)

### Send overdue reminders now
→ Click **🔧 Tool Library → 📧 Send Overdue Reminders Now**

---

## Sheet Reference

### Tools Inventory
| Column | Description |
|---|---|
| Tool ID | Auto-generated (T001, T002, …) |
| Tool Name | Display name |
| Category | Dropdown (Hand Tools, Power Tools, etc.) |
| Condition | Dropdown (Excellent → Broken) |
| Status | Auto-managed (Available / Borrowed / Maintenance / Retired) |
| Location / Storage Bin | Where to find/return the tool |
| Photo URL | Google Drive share link |
| Notes | Free text |
| Date Added | Auto-set |

### Loans
| Column | Description |
|---|---|
| Loan ID | Auto-generated (L001, L002, …) |
| Tool ID | Links to Tools Inventory |
| Tool Name | Copied at time of checkout |
| Borrower Name / Email / Phone | Contact details |
| Borrow Date / Due Date | Set at checkout |
| Return Date | Set when returned |
| Return Condition | Set at return |
| Status | Auto-managed (Active / Overdue / Returned) |
| Notes | Free text |

---

## Troubleshooting

**Menu doesn't appear after setup**
→ Refresh the spreadsheet page.

**Form responses aren't logging**
→ Make sure you clicked "Create / Update Checkout Form" (or Return Form) from the menu — this sets up the submission triggers.

**Emails aren't sending**
→ Open Apps Script → Run → `sendEmail` manually to check for auth errors. Re-authorize if prompted.

**"Tool not found" errors on return form**
→ Borrowers can enter either the **Loan ID** (e.g., `L003`) or the exact **Tool Name** on the return form.

**Photos aren't showing**
→ Make sure the Google Drive sharing is set to "Anyone with the link can view" before copying the URL.

---

## Updating the Checkout Form when inventory changes

When you add or retire tools, re-run **🔧 Tool Library → 📋 Create / Update Checkout Form** to refresh the list of available tools in the dropdown.
