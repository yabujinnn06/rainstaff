@echo off
setlocal enabledelayedexpansion

echo Rainstaff Sync Service - Delete Old Service
echo.

REM Delete old service
sc stop RainstaffSyncService >nul 2>&1
timeout /t 1 /nobreak >nul

sc delete RainstaffSyncService >nul 2>&1
timeout /t 1 /nobreak >nul

echo Rainstaff Sync Service - Create New Service
echo.

REM Use correct Python path
set PYTHON=C:\Users\rainwater\AppData\Local\Programs\Python\Python312\python.exe
set SCRIPT=C:\Users\rainwater\Desktop\puantaj\puantaj_app\sync_service.py

echo Python: %PYTHON%
echo Script: %SCRIPT%
echo.

REM Create service
sc create RainstaffSyncService binPath= "\"!PYTHON!\" \"!SCRIPT!\"" DisplayName= "Rainstaff Sync Service" start= auto type= own

echo.
echo Starting service...
net start RainstaffSyncService

echo.
echo Service status:
sc query RainstaffSyncService

pause
