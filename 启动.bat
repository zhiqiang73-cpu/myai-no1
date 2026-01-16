@echo off
chcp 65001 >nul
title BTC交易系统
set PYTHONIOENCODING=utf-8

echo ========================================
echo    BTC 强化学习交易系统
echo ========================================
echo.

cd /d "%~dp0"

echo 正在启动Web服务...
echo.
echo 启动后请访问: http://127.0.0.1:5000
echo.

python -m web.app

pause
