@echo off
REM ============================================================================
REM Download and Extract NSSM
REM ============================================================================

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set NSSM_DIR=%SCRIPT_DIR%nssm
set NSSM_ZIP=%SCRIPT_DIR%nssm.zip
set NSSM_DOWNLOAD=https://nssm.cc/download/nssm-2.24-101-g897c7f7.zip

echo ============================================================================
echo NSSM Downloader
echo ============================================================================
echo.

REM Check if NSSM already exists
if exist "%NSSM_DIR%\win64\nssm.exe" (
    echo [✓] NSSM is already installed at: %NSSM_DIR%
    pause
    exit /b 0
)

REM Create nssm directory
if not exist "%NSSM_DIR%" mkdir "%NSSM_DIR%"

echo [*] Downloading NSSM from: %NSSM_DOWNLOAD%
echo [*] Saving to: %NSSM_ZIP%
echo.

REM Try PowerShell first (faster)
powershell -Command "(New-Object System.Net.ServicePointManager).SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('%NSSM_DOWNLOAD%', '%NSSM_ZIP%')" 2>nul

if %errorlevel% neq 0 (
    echo [!] PowerShell download failed, trying certutil...
    
    REM Fallback to certutil (Windows built-in)
    certutil -urlcache -split -f "%NSSM_DOWNLOAD%" "%NSSM_ZIP%" >nul 2>&1
    
    if %errorlevel% neq 0 (
        echo ERROR: Failed to download NSSM using both PowerShell and certutil!
        echo.
        echo Solution: Download manually from https://nssm.cc/download/nssm-2.24-101-g897c7f7.zip
        echo            and extract to: %NSSM_DIR%
        echo.
        pause
        exit /b 1
    )
)

echo [✓] Download complete!
echo.

echo [*] Extracting NSSM...
REM Extract ZIP using PowerShell
powershell -Command "Expand-Archive -Path '%NSSM_ZIP%' -DestinationPath '%NSSM_DIR%' -Force" >nul 2>&1

if %errorlevel% neq 0 (
    echo ERROR: Failed to extract NSSM!
    pause
    exit /b 1
)

REM Move files from extracted folder to NSSM_DIR root
for /d %%D in ("%NSSM_DIR%\nssm*") do (
    echo [*] Moving extracted files...
    move "%%D\*" "%NSSM_DIR%\" >nul
    rmdir /s /q "%%D" >nul
)

REM Cleanup zip file
del /q "%NSSM_ZIP%"

echo.
echo ============================================================================
echo [✓] NSSM installation complete!
echo ============================================================================
echo.
echo NSSM is ready at: %NSSM_DIR%\win64\nssm.exe
echo.

pause
