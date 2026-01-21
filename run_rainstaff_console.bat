@echo off
setlocal
cd /d %~dp0

rem Varsa yerel sanal ortamı etkinleştir
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat

set APPDIR=%CD%

echo [INFO] Rainstaff uygulamasi konsol modunda baslatiliyor...
python -u puantaj_app\app.py

echo.
echo [INFO] Program kapandi. Pencereyi kapatmak icin bir tusa basin...
pause >nul
