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

### 🌱 Upcoming Plantings map
`plantings-map.html` is a standalone map of planned plantings, separate from the
main dashboard. These trees aren't in the NYC tree census yet, so the page plots
coordinates from its own data file rather than census markers.

Planted trees live in `data/upcoming-plantings.csv` (address, borough, area,
species). To add some, append rows leaving the coordinate columns blank, then
geocode them:

```bash
python3 scripts/geocode_plantings.py
```

The script fills in `latitude`/`longitude` from the NYC Planning Labs GeoSearch API,
rewrites the CSV in place, and mirrors the rows into `data/upcoming-plantings.js`.
Commit both files. Use `--dry-run` to preview and `--force` to re-geocode rows that
already have coordinates.

Rows that fail to geocode keep blank coordinates and are reported on the console —
the map skips them rather than guessing a location.

Open the page either way:
- **Served** — <https://hadas-lesecologycenter.github.io/nyc-tree-dashboard/plantings-map.html>,
  or locally via `python3 -m http.server`
- **Straight off disk** — double-click the file. This is why the script writes the
  `.js` mirror: a `file://` page may load a script but not `fetch` a CSV.

Leaflet is vendored in `vendor/` (extracted from the copy already bundled in
`index.html`), so the only third-party request the page makes is for basemap tiles.
