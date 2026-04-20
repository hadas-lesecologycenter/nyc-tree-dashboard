# LES Ecology Center Event Dashboard — Google Sites Setup

## Step 1: Deploy Apps Script as Web App

1. Go to https://script.google.com
2. Create a **New Project**
3. Create two files:
   - **Code.gs** — copy from `/apps-script/Code.gs`
   - **Index.html** — copy from `/apps-script/Index.html`
4. Click **Deploy** → **New deployment**
5. Select type: **Web app**
6. Execute as: **Me** (your account)
7. Access: **Anyone in your org** (or **Anyone** if you want public access)
8. Click **Deploy**
9. Copy the deployment URL (looks like: `https://script.google.com/macros/d/[ID]/userweb`)

## Step 2: Create Google Site

1. Go to https://sites.google.com
2. Click **Create**
3. Name it: **Event Workflow Dashboard** (or your preferred name)
4. Choose a template (blank is fine)

## Step 3: Add Dashboard to Site

### Option A: Embed via iframe (recommended)

1. On your Google Site, click **Insert** (top menu)
2. Select **Embed URL**
3. Paste your Apps Script URL from Step 1
4. Click **Next**
5. Set size: **Width: 100%**, **Height: 1200px** (adjust as needed)
6. Click **Embed**

### Option B: Embed via HTML

1. Click **Insert** → **HTML**
2. Paste this code:
```html
<iframe 
  src="[YOUR_APPS_SCRIPT_URL]" 
  style="width:100%; height:1200px; border:none; display:block;"
  allow="camera; microphone; clipboard-read; clipboard-write"
></iframe>
```
3. Replace `[YOUR_APPS_SCRIPT_URL]` with your deployment URL
4. Click **Insert**

## Step 4: Configure Dashboard Settings

Once the dashboard loads in your Site:

1. Go to the **Setup** tab
2. Fill in:
   - **Apps Script Web App URL** — your deployment URL (for Google integration)
   - **STC Tracker Spreadsheet ID** — `1EKZHAAlNOPPQEgxDgR7IMBKXWY5aR3VEURl4crImsrY`
   - **Event Brief Folder ID** — `1vAH4OPtWMIkZIBtKRcdKwfbYT4bebfnC`
   - **Post-Event Report Response Sheet ID** — `1RqQl5Wx-DUhMDQwTk2APz0VulodV3FaS51Y9WGuYwAs`
3. Click **Save Settings**

## Step 5: Fill in Google Chat Integration (optional)

To enable Google Chat task notifications:

1. Open your **Street Tree Care Crew** space in Google Chat
2. Click the space name → **Apps & integrations**
3. Click **Manage webhooks** → **Add webhook**
4. Give it a name (e.g., "STC Dashboard")
5. Copy the webhook URL
6. In Code.gs, update:
   ```javascript
   CHAT_WEBHOOK_URL: '[PASTE_YOUR_WEBHOOK_URL]'
   ```
7. Also fill in team email addresses:
   ```javascript
   TEAM: {
     'Maddy': 'maddy@lesecologycenter.org',
     'Hadas': 'hadas@lesecologycenter.org',
     'Gretel': 'gretel@lesecologycenter.org'
   }
   ```
8. Re-deploy Apps Script (Deploy → Manage deployments → select your deployment → click trash icon → redeploy)

## Step 6: Enable Google Tasks API (optional)

To push tasks to Google Tasks:

1. In Apps Script editor, click **Services** (+ button)
2. Find **Google Tasks API** and click **Add**
3. Now `pushTasksToGoogleTasks()` will work when users click "Push to Google Tasks"

## Step 7: Publish Your Site

1. Click **Publish** (top right)
2. Get the shareable link
3. Share with your team

---

## Troubleshooting

**Dashboard shows blank?**
- Check Apps Script deployment is "New deployment" (not Legacy)
- Make sure access is set to "Anyone in your org"
- Hard-refresh the page (Cmd/Ctrl+Shift+R)

**Can't create spreadsheet rows?**
- Verify Tracker Sheet ID in Setup tab
- Make sure you're logged in to the Google account that owns the sheet

**Chat integration not working?**
- Check webhook URL is valid and copied exactly
- Make sure chat space has the webhook enabled
- Team email addresses must be exact

---

## Features Once Deployed

✅ **Calendar view** — See all events on a monthly calendar
✅ **Event form** — Create new events with full brief details
✅ **Auto-generated outputs** — Event briefs, tracker rows, task lists
✅ **Tasks tab** — Filter tasks by staff member, time, status
✅ **Integration buttons** — Post-event report, photo sharing, Eventbrite
✅ **Google integration** — Push to Sheets, Docs, Calendar, Tasks, Chat
✅ **Demo events** — Pre-populated so team can see how it works

---

## URLs & IDs Reference

| Item | Value |
|------|-------|
| STC Tracker Sheet ID | `1EKZHAAlNOPPQEgxDgR7IMBKXWY5aR3VEURl4crImsrY` |
| Event Brief Folder ID | `1vAH4OPtWMIkZIBtKRcdKwfbYT4bebfnC` |
| Post-Event Form ID | `1FAIpQLSftVFR0w5zrNKr_T00DxueKDp3S5bM919cQ3paHQn9igpvUfw` |
| Response Sheet ID | `1RqQl5Wx-DUhMDQwTk2APz0VulodV3FaS51Y9WGuYwAs` |
| Eventbrite Org ID | `13297911311` |
