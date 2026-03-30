# NYC Tree Map — Windows Setup Script
# =====================================
# Run this ONCE from the repo folder to:
#   1. Check Python and Git are installed
#   2. Install the requests library
#   3. Run the historical backfill (first-time data fetch)
#   4. Schedule the daily scraper via Windows Task Scheduler
#
# HOW TO RUN:
#   Right-click this file → "Run with PowerShell"
#   (If you see a red error about execution policy, run this first in PowerShell:
#    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned)

$ErrorActionPreference = "Stop"

# ── Paths ─────────────────────────────────────────────────────────────────────
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoDir   = Split-Path -Parent $scriptDir
$batFile   = Join-Path $scriptDir "run_daily.bat"

Write-Host ""
Write-Host "=== NYC Tree Map Setup ===" -ForegroundColor Green
Write-Host "Repo: $repoDir"
Write-Host ""

# ── Check Python ──────────────────────────────────────────────────────────────
Write-Host "Checking Python..." -ForegroundColor Cyan
try {
    $pyVersion = & python --version 2>&1
    Write-Host "  Found: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "ERROR: Python not found." -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# ── Check Git ─────────────────────────────────────────────────────────────────
Write-Host "Checking Git..." -ForegroundColor Cyan
try {
    $gitVersion = & git --version 2>&1
    Write-Host "  Found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "ERROR: Git not found." -ForegroundColor Red
    Write-Host "Please install Git from https://git-scm.com/download/win" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# ── Install Python dependencies ───────────────────────────────────────────────
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
Set-Location $repoDir
& python -m pip install requests --quiet
Write-Host "  Done." -ForegroundColor Green

# ── Run historical backfill ───────────────────────────────────────────────────
Write-Host ""
Write-Host "Running historical backfill (this may take a minute)..." -ForegroundColor Cyan
& python backfill.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "WARNING: Backfill encountered an error (see above)." -ForegroundColor Yellow
    Write-Host "This may mean the API returned limited data." -ForegroundColor Yellow
    Write-Host "The daily scraper will still be set up." -ForegroundColor Yellow
} else {
    # Commit and push the backfill data
    & git add data\activities.csv
    $diff = & git diff --staged --quiet
    if ($LASTEXITCODE -ne 0) {
        & git commit -m "Initial historical backfill"
        & git push origin main
        Write-Host "  Backfill data pushed to GitHub." -ForegroundColor Green
    } else {
        Write-Host "  No new data from backfill." -ForegroundColor Yellow
    }
}

# ── Register Task Scheduler ───────────────────────────────────────────────────
Write-Host ""
Write-Host "Setting up daily Task Scheduler job..." -ForegroundColor Cyan

$taskName = "NYC Tree Map Daily Scraper"
$action   = New-ScheduledTaskAction -Execute $batFile
$trigger  = New-ScheduledTaskTrigger -Daily -At "9:00AM"
$settings = New-ScheduledTaskSettingsSet `
    -RunOnlyIfNetworkAvailable `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

# Remove existing task if present
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Limited `
    -Force | Out-Null

Write-Host "  Task '$taskName' registered — runs daily at 9:00 AM." -ForegroundColor Green

# ── Done ──────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== Setup complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "The scraper will run automatically every day at 9:00 AM" -ForegroundColor White
Write-Host "as long as this computer is on and connected to the internet." -ForegroundColor White
Write-Host ""
Write-Host "To run it manually at any time, double-click:" -ForegroundColor White
Write-Host "  $batFile" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to close"
