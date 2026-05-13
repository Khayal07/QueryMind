@echo off
cd /d "%~dp0"
cd ui

echo.
echo ========================================
echo Installing dependencies first time...
echo ========================================
call npm install

if errorlevel 1 (
    echo ERROR during npm install!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Starting development server...
echo ========================================
call npm run dev

pause
