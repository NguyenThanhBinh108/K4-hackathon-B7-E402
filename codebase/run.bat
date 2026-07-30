@echo off
cd /d "%~dp0backend"

echo [1/4] Kiem tra Python...
python --version >nul 2>&1 || (echo LOI: Python chua cai. Vao python.org & pause & exit /b 1)

echo [2/4] Tao .venv neu chua co...
if not exist ".venv\" python -m venv .venv

echo [3/4] Kich hoat .venv va cai packages...
call .venv\Scripts\activate.bat
pip install -r requirements.txt -q --disable-pip-version-check

echo [4/4] Khoi dong server...
echo.
echo  =========================================
echo   App: http://localhost:8000
echo   API: http://localhost:8000/docs
echo   Dung: Ctrl+C
echo  =========================================
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
