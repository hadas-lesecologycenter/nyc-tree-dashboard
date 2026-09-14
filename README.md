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
its own data rather than census markers.

No setup, no build step — open it either way:
- **Locally**: double-click `plantings-map.html`
- **Published**: <https://hadas-lesecologycenter.github.io/nyc-tree-dashboard/plantings-map.html>
  — live once the file is on `main`, which is the branch GitHub Pages serves.
  On a feature branch the link 404s.

The page geocodes the street addresses in your browser via the
[NYC Planning Labs GeoSearch API](https://geosearch.planninglabs.nyc) the first
time it loads, then caches the results in `localStorage`, so later visits are
instant and don't hit the API again. If an address can't be resolved the page says
which one and greys it out in the list, rather than guessing a location.

Leaflet is vendored in `vendor/` (extracted from the copy already bundled in
`index.html`), so the only third-party requests are basemap tiles and the
geocoder.

#### Editing the list
The roster lives in two places, both plain text:
- `data/upcoming-plantings.csv` — the source of truth
- a `FALLBACK_PLANTINGS` array near the top of the page's script, used when the
  CSV can't be fetched (opening the file straight off disk)

Keep them in step when you add or remove trees.

#### Optional: freezing coordinates
If you'd rather the page not call the geocoder at all, bake the coordinates in:

```bash
python3 scripts/geocode_plantings.py
```

It fills `latitude`/`longitude` in the CSV from the same API, mirrors the rows
into `data/upcoming-plantings.js`, and the page prefers those over live lookups.
Commit both files. `--dry-run` previews; `--force` re-geocodes rows that already
have coordinates.
