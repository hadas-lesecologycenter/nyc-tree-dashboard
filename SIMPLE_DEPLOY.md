# Deploy Dashboard to Google Site — Simplest Way (5 Minutes)

## Step 1: Create Apps Script Project (1 minute)

1. Go to **https://script.google.com**
2. Click **New project**
3. You now have a blank Apps Script editor

## Step 2: Add the Code (2 minutes)

### Code.gs File:
1. In the editor, select all (Cmd/Ctrl+A) and delete
2. Open this file in the repo: `/apps-script/Code.gs`
3. Copy ALL the code
4. Paste into the Apps Script editor
5. Click **Save**

### Index.html File:
1. Click **File** → **New** → **HTML file**
2. Name it: `Index`
3. Open this file in the repo: `/apps-script/Index.html`
4. Copy ALL the code
5. Paste into the new HTML file
6. Click **Save**

## Step 3: Deploy (1 minute)

1. Click the **Deploy** button (top right of Apps Script editor)
2. Select **New deployment**
3. Click the gear icon → Select **Web app**
4. **Execute as:** Your account (Me)
5. **Access:** Anyone in your organization
6. Click **Deploy**
7. A popup appears with your deployment URL — **COPY IT**

Example URL looks like:
```
https://script.google.com/macros/d/1A2B3C4D5E6F7G8H9I0J1K2L3M4N5O/userweb
```

## Step 4: Create Google Site (1 minute)

1. Go to **https://sites.google.com**
2. Click **Create**
3. Name it: `Event Dashboard` (or any name)
4. Click **Create**

## Step 5: Add Dashboard to Site (30 seconds)

1. Click **Insert** (top menu bar)
2. Click **Embed URL**
3. Paste your deployment URL from Step 3
4. Click **Next**
5. Set:
   - **Width:** 100%
   - **Height:** 1200px
6. Click **Embed**

**Done!** Your dashboard is now live on your Google Site.

---

## What Works Now

✅ Calendar view  
✅ Create events  
✅ Generate event briefs (Google Docs)  
✅ Add tracker rows (Google Sheets)  
✅ Create task lists  
✅ Push to Google Calendar  
✅ Push to Google Tasks  
✅ Push to Google Chat  
✅ Post-event reports  
✅ Eventbrite integration  
✅ Demo events to show team  

---

## Optional: Share with Your Team

1. In your Google Site, click **Share** (top right)
2. Add email addresses for Maddy, Hadas, Gretel
3. Set permission: **Editor**
4. Send them the site URL

---

## If Something Goes Wrong

**Dashboard shows blank:**
- Hard refresh (Cmd/Ctrl+Shift+R)
- Wait 30 seconds
- Check browser console (F12) for errors

**Can't create spreadsheet rows:**
- Verify the Tracker Sheet ID is correct in Code.gs
- Make sure you have edit access to the sheet

**Chat integration not working:**
- Add webhook URL to `CONFIG.CHAT_WEBHOOK_URL` in Code.gs
- Re-deploy after updating

---

## That's It!

You now have a fully functional event dashboard on your Google Site with Sheets, Docs, Calendar, Chat, and Eventbrite integration.
