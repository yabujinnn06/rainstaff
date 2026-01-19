@echo off
REM ============================================================================
REM Rainstaff Sync Service - Windows Service Installation
REM ============================================================================
REM Creates Windows Service using sc.exe (no external dependencies)
REM Runs continuously in background, auto-starts on boot
REM
REM Requirements: Run as Administrator
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo Rainstaff Sync Service - Windows Service Installation
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
set DISPLAY_NAME=Rainstaff Sync Service
set PYTHON_EXE=python.exe
set SERVICE_SCRIPT=%SCRIPT_DIR%sync_service.py

REM Find Python executable path
for /f "delims=" %%A in ('where %PYTHON_EXE% 2^>nul') do (
    set PYTHON_PATH=%%A
)

if not defined PYTHON_PATH (
    echo ERROR: Python executable not found in PATH!
    echo.
    echo Solution: Install Python and add it to PATH
    pause
    exit /b 1
)

echo Python Path: !PYTHON_PATH!
echo Script Directory: %SCRIPT_DIR%
echo Service Name: %SERVICE_NAME%
echo Service Script: %SERVICE_SCRIPT%
echo.

REM Check if sync_service.py exists
if not exist "%SERVICE_SCRIPT%" (
    echo ERROR: sync_service.py not found at %SERVICE_SCRIPT%
    pause
    exit /b 1
)

echo ✓ sync_service.py found
echo.

REM Stop and remove existing service
echo [*] Checking for existing service...
sc query %SERVICE_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] Stopping existing service...
    net stop %SERVICE_NAME% >nul 2>&1
    timeout /t 2 /nobreak
    
    echo [*] Removing existing service...
    sc delete %SERVICE_NAME% >nul 2>&1
    timeout /t 2 /nobreak
)

echo.
echo [*] Creating Windows Service...

REM Create service with sc.exe
REM binPath format: "python.exe script.py"
REM start=auto: Auto-start on boot
REM type=own: Own process (not shared)

sc create %SERVICE_NAME% ^
    binPath= "\"!PYTHON_PATH!\" \"%SERVICE_SCRIPT%\"" ^
    DisplayName= "%DISPLAY_NAME%" ^
    start= auto ^
    type= own >nul 2>&1

if %errorlevel% neq 0 (
    echo ERROR: Failed to create service!
    echo.
    echo Try this command manually:
    echo   sc create %SERVICE_NAME% binPath= "\"!PYTHON_PATH!\" \"%SERVICE_SCRIPT%\"" start= auto
    echo.
    pause
    exit /b 1
)

echo [✓] Service created!
echo.

REM Set service description
echo [*] Setting service description...
sc description %SERVICE_NAME% "Rainstaff 24/7 database synchronization service. Auto-syncs every 3 minutes." >nul 2>&1

REM Start service
echo [*] Starting service...
net start %SERVICE_NAME% >nul 2>&1

if %errorlevel% equ 0 (
    echo [✓] Service started successfully!
    timeout /t 2 /nobreak
) else (
    echo [!] Failed to start service immediately. Trying again...
    timeout /t 3 /nobreak
    net start %SERVICE_NAME% >nul 2>&1
)

echo.
echo ============================================================================
echo [✓] SUCCESS! Rainstaff Sync Service is installed as Windows Service!
echo ============================================================================
echo.
echo Service Name: %SERVICE_NAME%
echo Display Name: %DISPLAY_NAME%
echo Status: Automatic (starts on boot)
echo Python: !PYTHON_PATH!
echo Script: %SERVICE_SCRIPT%
echo Logs: %%APPDATA%%\Rainstaff\logs\sync_service.log
echo.

REM Verify service is running
echo [*] Service Status:
sc query %SERVICE_NAME%

echo.
echo Management Commands:
echo   - Start service:   net start %SERVICE_NAME%
echo   - Stop service:    net stop %SERVICE_NAME%
echo   - Check status:    sc query %SERVICE_NAME%
echo   - View logs:       %%APPDATA%%\Rainstaff\logs\sync_service.log
echo   - Remove service:  sc delete %SERVICE_NAME%
echo.
echo Windows Services UI:
echo   - Press: Windows + R
echo   - Type: services.msc
echo   - Find: %DISPLAY_NAME%
echo.

pause
