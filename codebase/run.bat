@echo off
title VinAI Knowledge Assistant v2.0
color 0A
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║    VinAI Knowledge Assistant v2.0 - B7-E402         ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0backend"

REM Check .venv exists
if not exist ".venv\Scripts\python.exe" (
    echo [SETUP] Tao moi truong ao .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Khong the tao .venv. Kiem tra Python da cai chua.
        pause
        exit /b 1
    )
    echo [SETUP] Cai packages...
    .venv\Scripts\pip install -r requirements.txt --quiet
    echo [SETUP] Hoan thanh!
)

REM Check .env
if not exist ".env" (
    echo [WARN] Chua co file .env - copy tu .env.example...
    copy .env.example .env
    echo [WARN] Mo file .env va dien GEMINI_API_KEY vao!
    notepad .env
    timeout /t 3
)

echo [INFO] Khoi dong server tai http://localhost:8000
echo [INFO] Nhan Ctrl+C de dung server
echo.

.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
