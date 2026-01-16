@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动Web服务器...
python web\app.py
pause





