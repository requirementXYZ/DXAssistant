@echo off
setlocal
cd /d "%~dp0"
py -3 tools\simulate_wsjtx.py
echo.
pause
