@echo off
title BTC Trading System
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo Starting BTC Trading System...
echo Please visit: http://127.0.0.1:5000
echo.

python -c "
import sys
import os
sys.path.insert(0, '.')
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 禁用所有print输出到控制台
class NullWriter:
    def write(self, txt): pass
    def flush(self): pass

# 只在导入rl模块时重定向输出
original_stdout = sys.stdout
sys.stdout = NullWriter()

try:
    from web.app import app
    sys.stdout = original_stdout
    print('Server starting on http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=False)
except Exception as e:
    sys.stdout = original_stdout
    print(f'Error: {e}')
"

pause