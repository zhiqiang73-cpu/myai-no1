@echo off
REM Quick Start - Skip all checks and start immediately

title BTC Trading System v4.0 - Quick Start

cd /d "%~dp0"

echo Starting BTC Trading System v4.0...
echo.
echo Web UI: http://localhost:5000/
echo.
echo Press Ctrl+C to stop the server
echo.

REM Open browser after 2 seconds
start /B timeout /t 2 /nobreak >nul && start http://localhost:5000/

REM Start Flask server
python web/app.py

pause

