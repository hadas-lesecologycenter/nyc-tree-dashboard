# NYC Tree Map — Automatic Daily Scraper
# ========================================
# No Python, no Git, no installation needed.
# Just PowerShell, which is already on your Windows computer.
#
# FIRST TIME SETUP (do this once):
#   1. Get a GitHub token:
#      - Go to github.com → click your profile photo → Settings
#      - Left sidebar → Developer settings → Personal access tokens → Tokens (classic)
#      - "Generate new token (classic)" → check the "repo" box → click Generate

# Keep window open no matter what — wrap everything so errors are always visible.
trap {
    Write-Host ""
    Write-Host "ERROR: $_" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}
#      - Copy the token (starts with ghp_...)
#   2. Right-click THIS FILE → "Run with PowerShell"
#      It will ask for your token, save it, and schedule itself to run every day.
#
# After that, it runs automatically every morning. You never need to touch it again.

$REPO  = "hadas-lesecologycenter/nyc-tree-dashboard"
$FILE  = "data/activities.csv"
$GROUP = 14

# ── Load or ask for GitHub token ──────────────────────────────────────────────
$tokenFile = Join-Path $PSScriptRoot ".token"

if (Test-Path $tokenFile) {
    $token = (Get-Content $tokenFile -Raw).Trim()
} else {
    Write-Host ""
    Write-Host "First-time setup — enter your GitHub token." -ForegroundColor Cyan
    Write-Host "(See the instructions at the top of this file if you need to create one)" -ForegroundColor Gray
    Write-Host ""
    $token = Read-Host "GitHub token"
    $token | Set-Content $tokenFile
    Write-Host "Token saved. You won't be asked again." -ForegroundColor Green
    Write-Host ""
}

$headers = @{
    Authorization = "token $token"
    "User-Agent"  = "nyc-tree-scraper"
    Accept        = "application/vnd.github.v3+json"
}

# ── Helper: call the NYC Tree Map GraphQL API ─────────────────────────────────
function Invoke-TreeMapQuery($query, $variables) {
    $body = @{
        query     = $query
        variables = $variables
    } | ConvertTo-Json -Depth 5

    $apiHeaders = @{
        "Content-Type"    = "application/json"
        "User-Agent"      = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        "Accept"          = "application/json, text/plain, */*"
        "Referer"         = "https://tree-map.nycgovparks.org/tree-map/group/$GROUP"
        "Origin"          = "https://tree-map.nycgovparks.org"
    }

    $resp = Invoke-RestMethod `
        -Uri "https://www.nycgovparks.org/api-treemap/graphql" `
        -Method Post `
        -Body $body `
        -Headers $apiHeaders `
        -ContentType "application/json"

    return $resp
}

# ── Fetch activities from the NYC Tree Map API ────────────────────────────────
function Get-Activities {
    Write-Host "Fetching activities from NYC Tree Map..." -ForegroundColor Cyan

    # Strategy A: paginated activityReports
    $paginatedQuery = @"
query GroupActivityReports(`$groupId: Int!, `$limit: Int!, `$offset: Int!) {
  activityReports(groupId: `$groupId, limit: `$limit, offset: `$offset) {
    id date treeId duration stewardshipActivities
    tree { closestAddress species { commonName } }
  }
}
"@
    $allRows = @()
    $pageSize = 200
    $page = 0
    $strategyAWorked = $false

    do {
        $offset = $page * $pageSize
        try {
            $resp = Invoke-TreeMapQuery $paginatedQuery @{ groupId = $GROUP; limit = $pageSize; offset = $offset }
            $rows = $resp.data.activityReports
            if ($rows -and $rows.Count -gt 0) {
                $strategyAWorked = $true
                $allRows += $rows
                Write-Host "  Page $($page+1): $($rows.Count) records (total: $($allRows.Count))" -ForegroundColor Gray
            } else { break }
        } catch { break }
        $page++
    } while ($rows.Count -eq $pageSize -and $page -lt 500)

    if (-not $strategyAWorked) {
        # Strategy B: high-limit recentActivities
        Write-Host "  Trying high-limit query..." -ForegroundColor Gray
        $highLimitQuery = @"
query activitiesAndUser(`$id: Int!) {
  treeGroupById(id: `$id) {
    recentActivities(limit: 100000) {
      id date treeId duration stewardshipActivities
      tree { closestAddress species { commonName } }
    }
  }
}
"@
        $resp = Invoke-TreeMapQuery $highLimitQuery @{ id = $GROUP }
        $allRows = $resp.data.treeGroupById.recentActivities
    }

    Write-Host "  Got $($allRows.Count) activities from API." -ForegroundColor Green
    return $allRows
}

# ── Convert a raw activity to a CSV row ───────────────────────────────────────
function Format-Row($r, $scrapedAt) {
    $date = ""
    if ($r.date) {
        try {
            $d = [System.DateTimeOffset]::FromUnixTimeMilliseconds([long]$r.date)
            $date = $d.ToString("yyyy-MM-dd")
        } catch { $date = "$($r.date)".Substring(0, [Math]::Min(10, "$($r.date)".Length)) }
    }
    $species = if ($r.tree -and $r.tree.species) { $r.tree.species.commonName } else { "" }
    $address = if ($r.tree) { $r.tree.closestAddress } else { "" }
    $acts    = if ($r.stewardshipActivities) { $r.stewardshipActivities -join "; " } else { "" }
    $dur     = if ($r.duration) { $r.duration } else { "" }

    # Escape fields that may contain commas
    $fields = @($r.id, $date, $r.treeId, $species, $address, $acts, $dur, $scrapedAt) | ForEach-Object {
        $f = "$_"
        if ($f -match '[,"\n]') { '"' + $f.Replace('"', '""') + '"' } else { $f }
    }
    return $fields -join ","
}

# ── Get current CSV from GitHub ───────────────────────────────────────────────
Write-Host "Reading current data from GitHub..." -ForegroundColor Cyan
try {
    $ghFile = Invoke-RestMethod `
        -Uri "https://api.github.com/repos/$REPO/contents/$FILE" `
        -Headers $headers
    $currentCsv = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($ghFile.content -replace '\s'))
    $fileSha = $ghFile.sha
    Write-Host "  Found existing file ($([math]::Round($currentCsv.Length/1024,1)) KB)." -ForegroundColor Gray
} catch {
    # File doesn't exist yet — start fresh
    $currentCsv = "id,date,treeId,species,address,activitiesDone,durationMinutes,scrapedAt`n"
    $fileSha = $null
    Write-Host "  No existing file — will create it." -ForegroundColor Gray
}

# ── Load existing IDs to avoid duplicates ─────────────────────────────────────
$existingIds = @{}
$currentCsv.Split("`n") | Select-Object -Skip 1 | ForEach-Object {
    $id = $_.Split(",")[0].Trim()
    if ($id) { $existingIds[$id] = $true }
}
Write-Host "  Existing records: $($existingIds.Count)" -ForegroundColor Gray

# ── Fetch and append new activities ───────────────────────────────────────────
$rawActivities = Get-Activities
$scrapedAt = (Get-Date).ToString("yyyy-MM-dd")
$newRows = @()

foreach ($r in $rawActivities) {
    $id = "$($r.id)"
    if ($id -and -not $existingIds.ContainsKey($id)) {
        $newRows += Format-Row $r $scrapedAt
        $existingIds[$id] = $true
    }
}

Write-Host "New activities to add: $($newRows.Count)" -ForegroundColor Cyan

if ($newRows.Count -eq 0) {
    Write-Host "Nothing new — no update needed." -ForegroundColor Yellow
} else {
    # Append to CSV
    $updatedCsv = $currentCsv.TrimEnd() + "`n" + ($newRows -join "`n") + "`n"

    # Push to GitHub
    Write-Host "Pushing $($newRows.Count) new records to GitHub..." -ForegroundColor Cyan
    $encoded = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($updatedCsv))
    $pushBody = @{
        message = "Daily scrape $scrapedAt (+$($newRows.Count) new)"
        content = $encoded
    }
    if ($fileSha) { $pushBody.sha = $fileSha }

    Invoke-RestMethod `
        -Uri "https://api.github.com/repos/$REPO/contents/$FILE" `
        -Method Put `
        -Headers $headers `
        -Body ($pushBody | ConvertTo-Json) `
        -ContentType "application/json" | Out-Null

    Write-Host "Done! $($newRows.Count) new activities pushed to GitHub." -ForegroundColor Green
}

# ── On first run: set up Task Scheduler ───────────────────────────────────────
$taskName = "NYC Tree Map Daily Scraper"
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if (-not $existing) {
    Write-Host ""
    Write-Host "Setting up daily schedule (runs every morning at 9am)..." -ForegroundColor Cyan

    $action   = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    $trigger  = New-ScheduledTaskTrigger -Daily -At "9:00AM"
    $settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable -StartWhenAvailable

    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
        -Settings $settings -Force | Out-Null

    Write-Host "Scheduled! Will run automatically every day at 9am." -ForegroundColor Green
    Write-Host ""
    Write-Host "Setup complete. You never need to run this again." -ForegroundColor Green
}

Write-Host ""
Read-Host "Press Enter to close"
