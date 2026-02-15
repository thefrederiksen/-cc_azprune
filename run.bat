@echo off
cd /d "%~dp0"
echo Starting cc_azprune...
echo.
echo Log files are saved to: %~dp0logs\
echo.
call .venv\Scripts\activate
python -m cc_azprune.app
echo.
echo Application closed.
pause
