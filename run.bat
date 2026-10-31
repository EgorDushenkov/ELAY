@echo off
cd /d "%~dp0"
title VibeSense AI
echo Starting VibeSense AI...
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with code %ERRORLEVEL%.
    pause
)
