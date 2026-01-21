@echo off
setlocal enabledelayedexpansion

echo [INFO] Rainstaff uygulamasi konsol modunda baslatiliyor...
echo.

cd /d "%~dp0"

set "PYTHON_EXE=%cd%\puantaj_app\.venv\Scripts\python.exe"

if not exist "!PYTHON_EXE!" (
    echo ERROR: Virtual Environment'ta python.exe bulunamadi
    pause
    exit /b 1
)

echo [INFO] Python: !PYTHON_EXE!

"!PYTHON_EXE!" -c "import openpyxl" 1>nul 2>nul
if errorlevel 1 (
    echo [INFO] Bagimliliklar yukleniyor...
    "!PYTHON_EXE!" -m pip install -r puantaj_app\requirements.txt
)

echo [INFO] Rainstaff uygulamasi baslatiliyor...
"!PYTHON_EXE!" -u puantaj_app\app.py

echo.
echo [INFO] Program kapandi. Pencereyi kapatmak icin bir tusa basin...
pause
