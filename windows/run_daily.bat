@echo off
:: NYC Tree Map — Daily Scraper
:: Runs automatically via Windows Task Scheduler.
:: Do not move this file — setup.ps1 registers its full path.

cd /d "%~dp0.."

:: Pull latest code in case anything changed
git pull origin main --quiet

:: Run the scraper
python scrape.py
if errorlevel 1 (
    echo Scraper failed. See output above.
    exit /b 1
)

:: Commit and push if there is new data
git add data\activities.csv
git diff --staged --quiet
if errorlevel 1 (
    git commit -m "Daily scrape %date%"
    git push origin main
)

exit /b 0
