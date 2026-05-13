@echo off
REM Start Backend API Server
echo Starting AI SQL Query Generator Backend...
echo.
echo Backend will run on: http://0.0.0.0:8000
echo.

cd /d "%~dp0"

REM Check if venv exists
if not exist "venv" (
    echo Virtual environment not found. Creating...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "venv\Lib\site-packages\fastapi" (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Start server
echo Starting server...
python app.py

pause
