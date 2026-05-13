@echo off
REM Debug script for frontend issues
echo ================================
echo FRONTEND DEBUG CHECK
echo ================================
echo.

echo Checking Node.js...
node --version
if errorlevel 1 (
    echo ERROR: Node.js not found!
) else (
    echo OK: Node.js installed
)
echo.

echo Checking npm...
npm --version
if errorlevel 1 (
    echo ERROR: npm not found!
) else (
    echo OK: npm installed
)
echo.

echo Checking current directory...
cd
echo.

echo Current folder contents:
dir
echo.

cd ui
echo.
echo UI folder contents:
dir
echo.

if exist "node_modules" (
    echo OK: node_modules exists
) else (
    echo WARNING: node_modules missing - running npm install...
    call npm install
)
echo.

echo Checking package.json...
type package.json
echo.

echo.
echo Attempting npm run dev...
call npm run dev

pause
