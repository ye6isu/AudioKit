@echo off
title Audio Kit
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo An error occurred launching Audio Kit.
    pause
)
