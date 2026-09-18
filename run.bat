@echo off
title LyricAligner
cd /d "%~dp0"

python --version >nul 2>&1 || (
    echo [!] Python is not installed or not in PATH.
    pause
    exit /b
)

pip install -q -r requirements.txt
python align_server.py
pause