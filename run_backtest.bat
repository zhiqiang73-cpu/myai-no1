@echo off
chcp 65001 >nul
python simple_backtest.py > backtest_output.txt 2>&1
type backtest_output.txt
pause
