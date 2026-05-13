@echo off
cd /d "%~dp0"
cd ui

echo.
echo ===============================================
echo AI SQL Query Generator - Frontend
echo ===============================================
echo.

REM Check if node_modules exists
if not exist "node_modules" (
    echo [1/2] Installing npm dependencies...
    echo.
    call npm install
    echo.
)

echo [2/2] Starting development server...
echo.
echo Frontend will run on: http://localhost:5173
echo Backend API:        http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop.
echo.

call npm run dev

pause

pause
