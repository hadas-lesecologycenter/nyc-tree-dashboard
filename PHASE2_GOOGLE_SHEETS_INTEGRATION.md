# Phase 2: Google Sheets Integration Guide

**Status**: Planned for April-May 2026

---

## Overview

Phase 2 will automate the connection between the Event Dashboard and Google Sheets, eliminating manual data entry to the "STC 2026 All-Events Tracker" spreadsheet.

---

## What Will Happen (Phase 2)

### Current (Phase 1) - Manual
```
Dashboard → Manually enter into STC Tracker spreadsheet
```

### Phase 2 - Automated
```
Dashboard → Auto-populates STC Tracker spreadsheet
           → Auto-creates Google Calendar events
           → Auto-sends reminder emails
```

---

## Google Sheets Integration Details

### How It Will Work

1. **Create Event in Dashboard**
   - Fill in event form
   - Select event type
   - Click "Create Event"

2. **Auto-Populate Spreadsheet**
   - New row appears in STC Tracker
   - All fields auto-filled:
     - Event name
     - Date
     - Location
     - Coordinator
     - Group size
     - Event type
     - Status

3. **Keep Everything Synced**
   - Edit in dashboard → updates spreadsheet
   - Edit in spreadsheet → updates dashboard
   - Single source of truth

---

## Sheets Integration Features

### Auto-Create These Spreadsheet Columns

```
Event Name | Date | Time | Location | Coordinator | Type | Group Size | Status | Link to Dashboard
```

### Auto-Update These Fields
- Status (Pending → Confirmed → Complete)
- Notes
- Trees Stewarded (from reporting)
- Attendance (from form)

### Manual Entry (Still Required)
- Actual time of day (dashboard gets date only)
- Meeting location details
- Special instructions
- Post-event notes

---

## Setup Instructions (When Phase 2 Arrives)

### Step 1: Connect Google Account
1. Click "Connect Google Account" in dashboard
2. Authorize app to access your sheets
3. Select STC 2026 All-Events Tracker spreadsheet

### Step 2: Map Columns
1. Dashboard shows your spreadsheet columns
2. Confirm which column is which:
   - Event Name → Column A
   - Date → Column B
   - Etc.
3. Click "Confirm"

### Step 3: Start Using
1. Create event in dashboard
2. Check that row appears in spreadsheet
3. Edit spreadsheet
4. Confirm changes sync back to dashboard

---

## What This Saves

### Time Per Event
- ⏱️ **No manual spreadsheet entry**: 5 min saved
- ⏱️ **No copy-pasting dates**: 2 min saved
- ⏱️ **No formatting issues**: 1 min saved
- **Total**: ~8 min per event

### For 20 Events Per Year
- **20 events × 8 min = 160 minutes = ~2.5 hours per year saved**

---

## FAQ: Google Sheets Phase 2

**Q: Will I still see everything in the spreadsheet?**
A: Yes! The spreadsheet gets all your data. You can view/edit there too.

**Q: What if I edit the spreadsheet directly?**
A: Dashboard updates within seconds. Both stay in sync.

**Q: What about private events or test events?**
A: You can mark events as "Private" to exclude from shared spreadsheets.

**Q: Can multiple people use this together?**
A: Yes! Phase 2 also adds multi-user support.

**Q: What if Google Sheets goes down?**
A: Dashboard works offline. When connection returns, it syncs.

**Q: Is my data safe?**
A: Your Google account security protects it. The app never stores passwords.

---

## Related Phase 2 Features

### Google Calendar Integration
```
Dashboard Event
  ↓
Auto-creates event on LES events calendar
Auto-creates event on Planning calendar
Color-coded by event type
Attendees auto-added
```

### Email Automation
```
Click "Send Confirmation" button
  ↓
Customizable email opens
  ↓
One-click send
  ↓
Or copy-paste if you prefer
```

### PDF Reports
```
Click "Generate Report" button
  ↓
PDF downloads with:
  - Event details
  - Task checklist status
  - Participant list
  - Tree care summary
```

---

## Technical Details (For IT/Developers)

### Technology Used
- Google Sheets API v4
- OAuth 2.0 authentication
- JSON data synchronization
- Real-time sync every 30 seconds

### What Requires Permission
- Read/write access to STC 2026 All-Events Tracker
- Create calendar events on LES events calendar
- Send emails from your account (optional)

### What We Don't Access
- Other spreadsheets (only the one you select)
- Your password (OAuth handles this)
- Personal files or calendars
- Any data outside what you select

---

## Timeline

### April 2026 (Now)
- ✅ Phase 1: Dashboard complete
- 📅 Launch and collect feedback

### May 2026
- 🔄 Phase 2: Google integration
- Google Sheets auto-population
- Google Calendar integration
- Email template automation

### June 2026
- 📱 Phase 3: Mobile & cloud
- Mobile-friendly dashboard
- Cloud backup
- Multi-user collaboration

### July 2026+
- 📊 Analytics & reporting
- Tree care metrics dashboard
- Participation tracking
- Impact reports

---

## Preparation (What You Can Do Now)

### 1. Organize Your Spreadsheets
- Confirm column headers in STC 2026 All-Events Tracker
- Make sure event data is consistent
- Clean up old/duplicate entries
- Note which columns you actively use

### 2. Check Google Calendar
- Confirm calendar names (LES events, Planning, etc.)
- Set up color codes if desired
- Ensure you have edit access

### 3. Collect Feedback
- Use Phase 1 dashboard for one month
- Note what works well
- Note what's still manual/slow
- Suggest Phase 2 improvements

### 4. Get Your Team Ready
- Share MIGRATION_GUIDE.md
- Explain Phase 2 is coming
- Show them the automation benefits
- Start conversations about multi-user needs

---

## What You're Not Getting (Phase 2)

These are Phase 3+:
- ❌ Photo upload to dashboard (Phase 3)
- ❌ Tree care metrics (Phase 3)
- ❌ Volunteer hours tracking (Phase 3)
- ❌ Mobile app (Phase 3)
- ❌ Offline spreadsheet updates (Phase 3)

---

## Feedback & Requests

### What Would Help Phase 2?
Please let us know:
- [ ] Which spreadsheets to integrate first?
- [ ] Which calendar colors for each event type?
- [ ] Other tools that should auto-sync?
- [ ] Any data we're not capturing?
- [ ] Team members who should help test?

---

## Stay Updated

Phase 2 development will:
- Add new features gradually
- Keep backwards compatibility
- Be announced when ready
- Include setup wizard

---

## Questions?

Check:
- `QUICK_REFERENCE.md` - For dashboard basics
- `EVENT_DASHBOARD_GUIDE.md` - For full documentation
- `MIGRATION_GUIDE.md` - For workflow transition

---

**Phase 2 Coming May 2026**
*More automation, less manual work, better team coordination*

---

Version 1.0 | April 6, 2026
