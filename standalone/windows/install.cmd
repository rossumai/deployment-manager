@echo off
rem Installs prd2 from this folder. Double-click it, or run it from a terminal.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
