# LES Ecology Center - Event Workflow Dashboard

## Overview

A unified web application that streamlines event planning and execution for the Street Tree Care Program. This dashboard eliminates manual data entry across multiple systems and provides a single source of truth for all event workflows.

## Features

### ✅ Core Features Implemented

1. **Event Creation & Management**
   - Create events with a single form
   - Supports 4 event types: Field Trip, Private Volunteer, Public Volunteer, Public Program
   - Auto-generates customized task checklists based on event type
   - Track progress across all tasks

2. **Unified Workflow Timeline**
   - Visual timeline showing all phases (Immediate → Day After)
   - Task checklists organized by timeline phase
   - Check off tasks as you complete them
   - Persistent storage using browser localStorage

3. **Event Dashboard**
   - Quick stats: Total events, Upcoming, In Progress, Completed
   - All events list with progress tracking
   - Color-coded event types for quick identification
   - One-click event selection to view full workflow

4. **Email Templates Library**
   - Pre-written templates for all communication needs:
     - Group Confirmation Email
     - Thank You Email
     - Event Reminder Email
   - Customizable with event-specific variables

5. **Data Persistence**
   - All events stored locally in browser
   - No server required
   - Data survives browser restarts

---

## How to Use

### 1. **Creating an Event**

1. Click the event type button (Field Trip, Private Volunteer, etc.)
2. Fill in event details:
   - Event name
   - Date
   - Location/Block
   - Coordinator name
   - Expected group size
3. Click "Create Event"
4. Event appears in the events list with all tasks ready to track

### 2. **Tracking Event Progress**

1. Click on any event in the events list
2. The workflow timeline appears on the right
3. Check off tasks as you complete them
4. Progress bar updates automatically
5. All progress is saved automatically

### 3. **Using Email Templates**

Scroll to the bottom of the dashboard to find pre-written email templates:
- Copy the template
- Replace placeholders (in [BRACKETS]) with actual event info
- Send to participants

---

## Workflow Details by Event Type

### 🏫 Field Trip (Schools)
**Timeline Phases:**
- Immediate: Spreadsheet entry, coordinator confirmation, calendar setup
- 1 Month Before: Equipment reservation
- 2 Weeks Before: Order compost, identify block
- 1 Week Before: Email confirmation, scouting, calendar blocking
- Day Before/Of: Tool prep, event reporting, tree map usage
- Day After: Cleanup, thank you, tree mapping, photo upload

### 🤝 Private Volunteer Event
**Timeline Phases:**
- Immediate: Spreadsheet, coordinator confirmation, volunteer tracking
- 2 Weeks Before: Compost order, block identification
- 1 Week Before: Email confirmation, scouting, equipment reservation
- Day Of: Tool prep, event reporting
- Day After: Cleanup, thank you, tree mapping, photo upload

### 📣 Public Volunteer Event
**Timeline Phases:**
- Immediate: Spreadsheet entry, coordinator confirmation, volunteer tracking
- 1 Month Before: Event brief, Eventbrite, communications request
- 2 Weeks Before: Compost order
- 1 Week Before: Block confirmation, email reminder, scouting, equipment
- Day Of: Tool prep, event reporting
- Day After: Cleanup, thank you, tree mapping, photo upload

### 📋 Public Program
**Timeline Phases:**
- Immediate: Spreadsheet entry, calendar setup, volunteer tracking
- 1 Month Before: Event brief, Eventbrite, communications request
- 2 Weeks Before: Content creation, vendor confirmation
- 1 Week Before: Email confirmation to registrants
- Day Of: Event reporting, participation tracking
- Day After: Thank you email

---

## Integration with Existing Tools

### Current Workflow Integration Points

| Step | Current Tool | How Dashboard Helps |
|------|-------------|-------------------|
| Event entry | STC 2026 All-Events Tracker | One form, many destinations |
| Calendar management | Google Calendar + Planning Calendar | Auto-generate calendar events (future) |
| Compost tracking | Compost and Tool Tracking | Reminder at 2-week mark |
| Equipment | Equipment calendar | Reminder to reserve |
| Tree reporting | NYC tree map | Task checklist reminder |
| Email templates | Google Drive (scattered) | Centralized library |
| Photo storage | STC album | Task reminder |

### Recommended Next Steps (Phase 2)

1. **Google Sheets Integration**
   - Auto-populate master spreadsheet with new events
   - Sync event data to "STC 2026 All-Events Tracker"
   - Two-way sync for coordinator updates

2. **Google Calendar Integration**
   - Auto-create events on LES events calendar
   - Auto-create on planning calendar
   - Color-coded by event type

3. **Email Automation**
   - One-click send confirmation emails
   - Automated reminder emails
   - Thank you emails with event summary

4. **Reporting Export**
   - Generate event reports as PDF
   - Export participation data
   - Export tree care metrics to NYC tree map format

---

## Technical Details

### Technology Stack
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Storage**: Browser localStorage (local)
- **No Backend Required**: Runs entirely in browser

### Files
- `event-dashboard.html` - Complete application (single file)

### Browser Compatibility
- Chrome/Edge 60+
- Firefox 55+
- Safari 12+
- Requires localStorage enabled

### Data Structure

Events are stored as JSON objects:
```json
{
  "id": 1712345678,
  "type": "field-trip",
  "name": "Upper West Side Tree Care",
  "date": "2026-04-15",
  "location": "8th Ave between 75th & 76th",
  "coordinator": "Jane Smith",
  "size": "20",
  "createdAt": "2026-04-06T15:30:00Z",
  "taskProgress": {
    "0-0": true,
    "0-1": false,
    ...
  }
}
```

---

## Quick Start

1. **Open the Dashboard**
   - Open `event-dashboard.html` in any web browser
   - No installation needed
   - Bookmark for easy access

2. **Create Your First Event**
   - Select event type
   - Fill in details
   - Click "Create Event"

3. **Track Progress**
   - Click event to view timeline
   - Check off tasks as you complete them
   - Progress saves automatically

4. **Use Email Templates**
   - Scroll to bottom of page
   - Copy template text
   - Customize with event details
   - Send to participants

---

## Future Enhancements (Phase 2+)

### Planned Features
- [ ] Google Sheets integration (auto-populate master spreadsheet)
- [ ] Google Calendar integration (auto-create calendar events)
- [ ] Email sending integration
- [ ] PDF event reporting
- [ ] Photo upload & organization
- [ ] Participant tracking
- [ ] Tree care metrics dashboard
- [ ] Multi-user collaboration
- [ ] Cloud sync

### Integration Roadmap
1. **Phase 1** (Current): Standalone dashboard ✅
2. **Phase 2**: Google Sheets + Calendar integration
3. **Phase 3**: Email automation
4. **Phase 4**: Cloud backup & multi-user support
5. **Phase 5**: Analytics dashboard

---

## Troubleshooting

### Events not saving?
- Check if localStorage is enabled in browser
- Try clearing browser cache and reload
- Events are stored locally per browser

### Tasks not showing?
- Ensure event type was selected before creating event
- Refresh page if workflow doesn't appear

### Lost data?
- Data is stored per browser on your device
- Use different browser = different data
- Consider exporting data before clearing cache

---

## Support & Questions

For questions about the dashboard:
1. Check the workflow details for your event type
2. Review email templates at bottom of page
3. All data is local - no privacy concerns
4. No internet required after initial load

---

## Files Included

- `event-dashboard.html` - Main application file
- `EVENT_DASHBOARD_GUIDE.md` - This guide
- Integration guides (forthcoming)

---

## Version

**v1.0** - Initial release
- Event creation and management
- Workflow tracking
- Email templates
- Local storage persistence

**Next Update**: Phase 2 integrations (Google Sheets, Calendar, Email)

---

**Last Updated**: April 6, 2026
