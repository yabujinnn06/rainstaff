@echo off
REM ============================================================================
REM Rainstaff Sync Service - Task Scheduler Setup
REM ============================================================================
REM Creates a Windows Task Scheduler job that runs sync_service.py
REM every 1 minute (repeating)
REM
REM Requirements: Run as Administrator
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo Rainstaff Sync Service - Task Scheduler Setup
echo ============================================================================
echo.

REM Check if running as Administrator
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if %errorlevel% neq 0 (
    echo ERROR: This script must run as Administrator!
    echo.
    echo Solution: Right-click this file and select "Run as Administrator"
    pause
    exit /b 1
)

REM Set paths
set SCRIPT_DIR=%~dp0
set TASK_NAME=RainstaffSyncService
set PYTHON_EXE=python
set SERVICE_SCRIPT=%SCRIPT_DIR%sync_service.py
set LOG_FILE=%SCRIPT_DIR%sync_service_task.log

echo Script Directory: %SCRIPT_DIR%
echo Task Name: %TASK_NAME%
echo Python Executable: %PYTHON_EXE%
echo Service Script: %SERVICE_SCRIPT%
echo Log File: %LOG_FILE%
echo.

REM Check if Python is installed
%PYTHON_EXE% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    pause
    exit /b 1
)

echo Python found:
%PYTHON_EXE% --version
echo.

REM Check if sync_service.py exists
if not exist "%SERVICE_SCRIPT%" (
    echo ERROR: sync_service.py not found at %SERVICE_SCRIPT%
    pause
    exit /b 1
)

echo sync_service.py found
echo.

REM Delete existing task if it exists
echo [*] Checking for existing task...
tasklist /fi "TASKKEYWORDS eq %TASK_NAME%" 2>nul | find /I "%TASK_NAME%" >nul
if %errorlevel% equ 0 (
    echo [*] Removing existing task...
    schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1
    timeout /t 2 /nobreak
)

echo.
echo [*] Creating Task Scheduler job...
echo.

REM Create the task using schtasks
REM - Runs on system startup
REM - Repeats every 1 minute
REM - Runs whether user is logged in or not
REM - Runs with highest privileges
schtasks /create /tn "%TASK_NAME%" ^
    /tr "\"%PYTHON_EXE%\" \"%SERVICE_SCRIPT%\"" ^
    /sc onstart ^
    /f >nul 2>&1

if %errorlevel% equ 0 (
    echo [✓] Task created successfully!
) else (
    echo ERROR: Failed to create task!
    pause
    exit /b 1
)

REM Set task to run with highest privileges
schtasks /change /tn "%TASK_NAME%" /ru "NT AUTHORITY\SYSTEM" /rp "" >nul 2>&1

REM Run task immediately
echo [*] Starting task...
schtasks /run /tn "%TASK_NAME%" >nul 2>&1

echo.
echo ============================================================================
echo [✓] SUCCESS! Rainstaff Sync Service is installed!
echo ============================================================================
echo.
echo Task Name: %TASK_NAME%
echo Status: Will start automatically on system startup
echo Logs: %APPDATA%\Rainstaff\logs\sync_service.log
echo.
echo Management Commands:
echo   - View task:   tasklist /fi "TASKKEYWORDS eq %TASK_NAME%"
echo   - Run now:     schtasks /run /tn "%TASK_NAME%"
echo   - Stop:        taskkill /f /im python.exe (all Python processes)
echo   - Delete task: schtasks /delete /tn "%TASK_NAME%" /f
echo.
echo View Task Scheduler:
echo   - Windows + R, type: taskschd.msc
echo   - Look for: %TASK_NAME% in Task Scheduler Library
echo.

pause
