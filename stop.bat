@echo off
echo Stopping PRORP Translator...
taskkill /F /IM pythonw.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
echo Done.

