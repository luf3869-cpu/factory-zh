@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ===========================================
echo   Factory 界面汉化安装
echo ===========================================
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 没有找到 Python 3。
    pause
    exit /b 1
)
python -c "import websockets" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 websockets...
    python -m pip install -r requirements.txt
)
python factory_zh.py --setup
echo.
echo 如果 Factory 正在运行，请先完全退出，再从原来的 Factory 图标打开。
pause
