@echo off
setlocal
cd /d "%~dp0"
py -3 main.py
if errorlevel 1 (
  echo.
  echo DX Assistant stopped with an error. Review the message above.
  pause
)

