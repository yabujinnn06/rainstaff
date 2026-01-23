@echo off
echo ========================================
echo   RainStaff ERP - GitHub Push Script
echo ========================================
echo.

cd /d "%~dp0"

echo [1/5] Git durumunu kontrol ediyorum...
git status
echo.

echo [2/5] Degisiklikleri ekliyorum...
git add .
echo.

echo [3/5] Commit mesajinizi girin (veya Enter'a basin):
set /p commit_msg="Commit mesaji: "
if "%commit_msg%"=="" set commit_msg=Update

echo [4/5] Commit yapiyorum...
git commit -m "%commit_msg%"
echo.

echo [5/5] GitHub'a push ediyorum...
git push
echo.

echo ========================================
echo   Tamamlandi! Render.com otomatik
echo   olarak yeni deploy baslatacak.
echo ========================================
echo.
pause
