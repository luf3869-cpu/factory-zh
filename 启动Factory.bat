@echo off
chcp 65001 >nul
cd /d "%~dp0"
python factory_zh.py --launch
if errorlevel 1 pause
