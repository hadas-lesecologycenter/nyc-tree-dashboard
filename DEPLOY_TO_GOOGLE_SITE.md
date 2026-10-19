# Deploy Event Dashboard to Google Site — 5 Minute Setup

## The Fastest Way: Use Apps Script Web App + Google Site Embed

### Step 1: Deploy to Apps Script (2 minutes)

1. Go to **https://script.google.com**
2. Click **New project**
3. Paste the contents of `apps-script/Code.gs` into the editor
4. Create a new file: **File → New → HTML file** named `Index`
5. Paste the contents of `apps-script/Index.html` into it
6. Click the **Deploy** button (top right)
7. Select **New deployment**
8. Type: **Web app**
9. Execute as: **Your account**
10. Access: **Anyone in your organization** (or **Anyone** for public)
11. Click **Deploy**
12. **Copy the deployment URL** — it looks like:
    ```
    https://script.google.com/macros/d/[DEPLOYMENT_ID]/userweb
    ```

### Step 2: Create Google Site (2 minutes)

1. Go to **https://sites.google.com**
2. Click **Create**
3. Enter site name: **Event Dashboard** (or any name)
4. Click **Create**
5. You now have a blank Google Site

### Step 3: Add Dashboard to Site (1 minute)

1. In your Google Site, click **Insert** (top toolbar)
2. Click **Embed URL**
3. Paste your Apps Script deployment URL from Step 1
4. Click **Next**
5. Set dimensions:
   - **Width**: 100%
   - **Height**: 1200px (adjust as needed)
6. Click **Embed**
7. The dashboard will load inside your site

### Step 4: Add Site Info (Optional)

1. Click the **Settings** icon (gear, top right)
2. Go to **Appearance**
3. Add a site header/title
4. Add navigation if desired
5. Set theme color to match LES branding (green gradient)

### Step 5: Share with Your Team

1. Click **Share** (top right)
2. Add email addresses for: Maddy, Hadas, Gretel
3. Set permission: **Editor** (so they can create/edit events)
4. Copy the site URL and share with team

---

## What Happens After Deployment

✅ Team members can:
- View calendar of all events
- Create new events with full brief details
- Auto-generate Event Briefs (Google Docs)
- Add tracker rows (Google Sheets)
- Create task lists with team assignments
- Send tasks to Google Chat space
- Push to Google Calendar
- Push to Google Tasks
- Submit post-event reports
- Share photos

✅ Everything syncs with:
- Google Sheets (STC Tracker)
- Google Docs (Event Briefs)
- Google Drive (Event Brief folder + photos)
- Google Calendar (task deadlines)
- Google Tasks (team tasks)
- Google Chat (team notifications)
- Eventbrite (public event listings)

---

## Troubleshooting

**Dashboard shows blank?**
- Hard refresh (Cmd/Ctrl+Shift+R)
- Wait 30 seconds for Apps Script to load
- Check that Apps Script deployment is "Web app" (not Legacy)

**Can't create spreadsheet rows?**
- Verify Tracker Sheet ID in Setup tab
- Make sure you're logged into the right Google account

**Chat integration not working?**
- Add webhook URL to `CONFIG.CHAT_WEBHOOK_URL` in Code.gs
- Re-deploy Apps Script after updating

**Eventbrite button doesn't work?**
- Check that `EVENTBRITE_TOKEN` is set in Script Properties (see below)
- Make sure event type includes "Public" or "Workshop" to show button

---

## IDs & Configuration Reference

| Item | Value |
|------|-------|
| STC Tracker Sheet | `1EKZHAAlNOPPQEgxDgR7IMBKXWY5aR3VEURl4crImsrY` |
| Event Brief Folder | `1vAH4OPtWMIkZIBtKRcdKwfbYT4bebfnC` |
| Post-Event Form | `1FAIpQLSftVFR0w5zrNKr_T00DxueKDp3S5bM919cQ3paHQn9igpvUfw` |
| Response Sheet | `1RqQl5Wx-DUhMDQwTk2APz0VulodV3FaS51Y9WGuYwAs` |
| Eventbrite Org | `13297911311` |
| Eventbrite API | Token in Script Properties as `EVENTBRITE_TOKEN` |

---

## Next Steps

After deploying, fill in optional integrations:

**Eventbrite token (required for Eventbrite features):**
1. Create a private token at https://www.eventbrite.com/platform/api-keys
2. In Apps Script: **Project Settings** (gear) → **Script Properties** → **Add script property**
3. Property: `EVENTBRITE_TOKEN`, Value: your token → **Save**

The token is kept out of `Code.gs` so it never ends up in this repository.

**Registered vs. attended (All Events tab):**
For every event with an Eventbrite link, the dashboard shows Registered,
Attended and Show-up rate, plus totals at the top.
- *Registered* = Eventbrite registrations still attending (cancelled and refunded orders left out). The link must contain the event's ID number, e.g. `.../e/spring-tree-care-tickets-123456789012`.
- *Attended* = headcount from the LESEC Activity Reporting form ("Number of Participants" for workshops, "Number of tree care volunteers" for Tree Care volunteer events). Only rows whose staff name includes someone in `CONFIG.STC_STAFF` are used.
- The report on the same day as the event is matched automatically; if there are several, the one sharing the most words with the event name/location wins and the card says "check the match". Use the **Report** dropdown on the card to pick a different report, mark "No report", or type a headcount by hand.
- Numbers refresh automatically once an hour when the dashboard opens, or with **Refresh attendance**.
- Run `testAttendance()` in the Apps Script editor to check both data sources.

**Google Chat Space Tasks:**
1. Open "Street Tree Care Crew" space in Google Chat
2. Space name → Apps & integrations → Manage webhooks → Add webhook
3. Copy webhook URL
4. Add to `CONFIG.CHAT_WEBHOOK_URL` in Code.gs
5. Add team email addresses to `CONFIG.TEAM` in Code.gs
6. Re-deploy Apps Script

**Team Email Addresses:**
Update in Code.gs:
```javascript
TEAM: {
  'Maddy': 'maddy@lesecologycenter.org',
  'Hadas': 'hadas@lesecologycenter.org',
  'Gretel': 'gretel@lesecologycenter.org'
}
```

---

## Support

If you run into issues:
1. Check the browser console (F12) for errors
2. Run `testConfig()` in Apps Script to verify setup
3. Check that all Google Drive/Sheets IDs are correct
4. Make sure you have edit access to linked Sheets/Folders
