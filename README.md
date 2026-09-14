# NYC Tree Dashboard
CB3 Manhattan tree care dashboard + Event Workflow Management

## 📂 Quick Navigation

### 🎯 For Event Workflow Streamlining (NEW!)
Start here → **[START_HERE.md](START_HERE.md)**

- Complete event management system
- Saves 16 minutes per event
- 4 workflow types (Field Trip, Private Volunteer, Public Volunteer, Public Program)
- Email templates built-in
- Everything in one place

**Get started in 5 minutes**: Open `event-dashboard.html` in your browser!

### 📖 Documentation
- **[START_HERE.md](START_HERE.md)** - Entry point (read this first!)
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - 2-minute overview
- **[EVENT_DASHBOARD_GUIDE.md](EVENT_DASHBOARD_GUIDE.md)** - Full documentation
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Switch from spreadsheets
- **[SOLUTIONS_SUMMARY.md](SOLUTIONS_SUMMARY.md)** - Problem analysis & solutions
- **[PHASE2_GOOGLE_SHEETS_INTEGRATION.md](PHASE2_GOOGLE_SHEETS_INTEGRATION.md)** - What's coming May 2026

### 🎯 Tree Dashboard
Original NYC tree care dashboard functionality

### 🌱 Upcoming Plantings layer
Planned plantings live in `data/upcoming-plantings.csv` and appear on the main map
under **Program Layers → Upcoming Plantings**. These trees aren't in the census yet,
so the layer plots the CSV's own coordinates rather than census markers.

To add plantings: append rows (address, borough, area, species — leave the coordinate
columns blank), then geocode them:

```bash
python3 scripts/geocode_plantings.py
```

The script fills in `latitude`/`longitude` from the NYC Planning Labs GeoSearch API
and rewrites the CSV in place. Commit the result. Rows that fail to geocode keep
blank coordinates and are reported on the console — the map layer skips them rather
than guessing a location. Use `--dry-run` to preview and `--force` to re-geocode
rows that already have coordinates.
