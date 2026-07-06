@echo off
REM ==== Post-Visit Auto-Debrief - Windows launcher ====
REM Double-click this file to start the app. It opens in your web browser.

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed.
  echo Install it from https://www.python.org/downloads/ ^(check "Add to PATH"^), then run this again.
  pause
  exit /b 1
)

echo Installing / updating components ^(first run only^)...
python -m pip install --quiet --disable-pip-version-check -r requirements.txt

echo Starting Post-Visit Auto-Debrief...
python app.py

pause
