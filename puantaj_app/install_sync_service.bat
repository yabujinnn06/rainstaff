@echo off
REM ============================================================================
REM Rainstaff Sync Service Installer
REM ============================================================================
REM This script:
REM 1. Downloads NSSM (Non-Sucking Service Manager)
REM 2. Installs sync_service.py as a Windows Service
REM 3. Starts the service
REM
REM Requirements: Run as Administrator
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo Rainstaff Sync Service Installer
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
set SERVICE_NAME=RainstaffSyncService
set PYTHON_EXE=python
set SERVICE_SCRIPT=%SCRIPT_DIR%sync_service.py
set NSSM_DOWNLOAD=https://nssm.cc/download/nssm-2.24-101-g897c7f7.zip
set NSSM_DIR=%SCRIPT_DIR%nssm
set NSSM_EXE=%NSSM_DIR%\win64\nssm.exe

REM Get current user
for /f "delims=" %%A in ('whoami') do set CURRENT_USER=%%A

echo Service Name: %SERVICE_NAME%
echo Python: %PYTHON_EXE%
echo Script: %SERVICE_SCRIPT%
echo Current User: %CURRENT_USER%
echo NSSM Dir: %NSSM_DIR%
echo.

REM Check if Python is installed
%PYTHON_EXE% --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Solution: Install Python and add it to PATH, or modify PYTHON_EXE in this script
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

REM Stop existing service if it exists
echo [*] Checking for existing service...
sc query %SERVICE_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] Stopping existing service...
    net stop %SERVICE_NAME% >nul 2>&1
    timeout /t 2 /nobreak
    
    echo [*] Removing existing service...
    "%NSSM_EXE%" remove %SERVICE_NAME% confirm >nul 2>&1
    timeout /t 2 /nobreak
)

echo.
echo [*] Installing Rainstaff Sync Service...
echo.

REM Install service using NSSM
"%NSSM_EXE%" install %SERVICE_NAME% "%PYTHON_EXE%" "%SERVICE_SCRIPT%"

if %errorlevel% neq 0 (
    echo ERROR: Failed to install service!
    pause
    exit /b 1
)

REM Set service to run as current user
echo [*] Configuring service to run as current user: %CURRENT_USER%
"%NSSM_EXE%" set %SERVICE_NAME% ObjectName %CURRENT_USER%

REM Set startup type to Automatic
echo [*] Setting service to start automatically...
"%NSSM_EXE%" set %SERVICE_NAME% Start SERVICE_AUTO_START

REM Configure service restart behavior
echo [*] Configuring restart behavior...
"%NSSM_EXE%" set %SERVICE_NAME% AppRestartDelay 5000
"%NSSM_EXE%" set %SERVICE_NAME% AppExit Default Restart

REM Configure logging
set LOG_FILE=%SCRIPT_DIR%nssm_service.log
echo [*] Configuring logging to: %LOG_FILE%
"%NSSM_EXE%" set %SERVICE_NAME% AppStdout "%LOG_FILE%"
"%NSSM_EXE%" set %SERVICE_NAME% AppStderr "%LOG_FILE%"

echo.
echo [✓] Service installed successfully!
echo.
echo [*] Starting service...
net start %SERVICE_NAME%

if %errorlevel% equ 0 (
    echo.
    echo ============================================================================
    echo [✓] SUCCESS! Rainstaff Sync Service is running!
    echo ============================================================================
    echo.
    echo Service Name: %SERVICE_NAME%
    echo Status: Automatic (starts on boot)
    echo Logs: %SCRIPT_DIR%\logs\sync_service.log
    echo.
    echo Management Commands:
    echo   - Start:   net start %SERVICE_NAME%
    echo   - Stop:    net stop %SERVICE_NAME%
    echo   - Status:  sc query %SERVICE_NAME%
    echo   - Remove:  "%NSSM_EXE%" remove %SERVICE_NAME% confirm
    echo.
) else (
    echo ERROR: Failed to start service!
    echo.
    echo Try starting manually:
    echo   net start %SERVICE_NAME%
    echo.
)

pause
