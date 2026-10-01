@echo off
setlocal
cd /d "%~dp0"
python scripts\build_installer.py %*
exit /b %errorlevel%