@echo off
chcp 65001 >nul
echo Starting Stock Analysis System...

echo 1. Starting Backend API Service (monitor.py)
start "Backend Service" cmd /k "cd /d %~dp0..\src && python -m uvicorn monitor:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak > nul

echo 2. Starting Frontend UI Service (app.py)
start "Frontend Service" cmd /k "cd /d %~dp0 && python app.py"

echo.
echo ======================================
echo Services Started Successfully!
echo ======================================
echo Backend API:  http://localhost:8000
echo Frontend UI:  http://127.0.0.1:7860
echo API Docs:     http://localhost:8000/docs
echo ======================================
echo Press any key to exit launcher...
pause > nul