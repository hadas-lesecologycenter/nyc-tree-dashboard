# Public view-only dashboard

A read-only copy of the Tree Care Map to share with people outside the team.
It runs as a Google Apps Script web app, which you can also embed in a Google Site.
Your Google account hosts the page. The data stays live: it loads the same
published data files and Google Sheet the team dashboard uses, every time someone opens it.

## What outside viewers see

| Shown | Hidden |
|---|---|
| Map: priority tiers, species colors, species and age filters, empty beds, planted beds, tree guards, missing/removed, fire hydrants | Every button in the tree panel (reserve, report care, advanced care, stewarded, nominate, guard, missing, assess) |
| Program layers: DEC grant tree guards (Rounds 1–3, rejected, Spring 2026 installs), Coolest Block 2025, sub-zones, block segments, other districts | Reservations (filter, view mode, counter, map dots) |
| Stats tab (charts, goal progress, quarterly report, query box) | Guard nominations and suggested trees |
| Tree Care tab, read-only (care map, table, stats) | Community stewarded trees and caretaker names |
| 311 Calls tab | Care Needed (to-do) list and "Cared For by Me" |
| Health Assessment tab, read-only (ratings and history) | 2027 Work Plan, tool storage locations |
| About tab, with a view-only note | Assessor, staff and volunteer names, and free-text notes |
| | CSV export buttons, the bookmarklet, the GitHub token setup |

Public view never requests the internal Sheet tabs (Reservations, GuardNominations,
DismissedSuggestions, CommunityStewardship, CareNeeded). It refuses every save, and it
keeps browser storage in memory, so data cached by a staff member's browser can't appear.

**Preview it before sharing:** add `?view=public` to the end of the team dashboard's
address, e.g. `.../index.html?view=public`.

## One-time setup (about 10 minutes)

### 1. Create the Apps Script project

1. Go to <https://script.google.com> and click **New project**.
2. Click **Untitled project** at the top and name it, e.g. `Tree Care Map – Public`.
3. In `Code.gs`, delete what's there and paste the contents of
   [`public-view/Code.gs`](public-view/Code.gs).
4. Click **+** next to *Files*, choose **HTML**, and name it `Index` (Apps Script adds `.html`).
5. Delete what's in it. Paste the whole contents of [`public-view/Index.html`](public-view/Index.html):
   on GitHub, open the file, click **Raw**, select all, and copy.
   The file is about 1.3 MB, so the editor may take a few seconds.
6. Click **Save** (💾).

### 2. Deploy it as a web app

1. Click **Deploy → New deployment**.
2. Click the gear ⚙ next to *Select type* and choose **Web app**.
3. Set **Execute as: Me** and **Who has access: Anyone**.
4. Click **Deploy** and approve the authorization prompts.
5. Copy the **Web app URL** (it ends in `/exec`). This is the link you share.
6. **Test it in a private/incognito window**, signed out of Google, to see exactly what an outside
   viewer sees.

> If the incognito test sends you to a Google sign-in page, or **Anyone** isn't offered,
> your Google Workspace admin restricts sharing outside lesecologycenter.org.
> An admin can allow it in the Admin console under Apps Script and Drive sharing settings.

### 3. (Optional) Put it on a Google Site

1. Go to <https://sites.google.com> and create a site, or open an existing one.
2. Click **Insert → Embed → By URL**, paste the `/exec` URL, and choose **Whole page**.
3. Resize the embed to fill the page (the map needs about 900 px of height).
4. Click **Publish**. Under *Who can view my published site*, choose **Anyone**
   (the same Workspace restriction can apply here).

## Keeping it up to date

- **Data** (trees, care activities, 311 calls, assessments) updates on its own. You don't need to redeploy.
- **Dashboard changes** (new features or fixes in `index.html`) need a rebuild and a redeploy:
  1. Run `python3 scripts/build_public_view.py` from the repo root, or ask Claude to rebuild it.
  2. Paste the new `public-view/Index.html` over the `Index` file in the Apps Script project and save.
  3. Click **Deploy → Manage deployments**, click the pencil ✏, set **Version: New version**,
     and click **Deploy**. The URL stays the same.

Don't edit `public-view/Index.html` by hand. It's generated from `index.html`.

## Things to know

- **This is a presentation layer, not a lock.** The full team dashboard and the TreeCareData
  Apps Script URL are both written in this repository. Anyone who finds them can still open the full
  dashboard, or ask that web app for any Sheet tab, including Reservations.
  If that matters, the TreeCareData web app needs its own protection, such as a shared key for reads and writes.
- **Hosting is on Google. Data still comes from this repo.** The page itself lives in your Google account.
  The tree files under `data/` still load from this repository's published copy
  (`raw.githubusercontent.com`) and are kept current by the GitHub Actions workflows.
- **"Find my location" (⊕)** may not work inside the embed, since browsers can block location access in
  embedded frames.
- Map tiles, the 311 data (NYC Open Data) and fonts load from their usual public services, as they do on the team dashboard.
