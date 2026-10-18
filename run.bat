@echo off
:: Ensure administrator privileges for global game hotkeys
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"
:: Launch via pythonw in background and close terminal immediately
start "" pythonw main.py
exit
