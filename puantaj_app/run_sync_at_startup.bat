@echo off
REM ============================================================================
REM Rainstaff Sync Service - Startup Script
REM ============================================================================
REM This script runs in background when Windows boots
REM Place in: C:\Users\{YourName}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
REM ============================================================================

setlocal

REM Get script directory (where this file is)
set SCRIPT_DIR=%~dp0

REM Run sync_service.py in background (invisible window)
start "" /b /low "%ProgramFiles%\Python312\python.exe" "%SCRIPT_DIR%sync_service.py" >nul 2>&1

REM Exit immediately (let process continue in background)
exit /b 0
