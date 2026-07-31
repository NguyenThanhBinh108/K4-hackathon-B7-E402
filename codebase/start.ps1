# VinAI Knowledge Assistant v2.0 - PowerShell Launcher
Set-Location "$PSScriptRoot\backend"

# Setup venv if not exists
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "[SETUP] Tao .venv..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "[SETUP] Cai packages..." -ForegroundColor Yellow
    .\.venv\Scripts\pip.exe install -r requirements.txt --quiet
    Write-Host "[SETUP] Hoan thanh!" -ForegroundColor Green
}

# Check .env
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[WARN] Mo file .env va dien API key vao!" -ForegroundColor Red
    Start-Process notepad ".env"
    Start-Sleep 3
}

Write-Host ""
Write-Host " VinAI Knowledge Assistant v2.0" -ForegroundColor Cyan
Write-Host " http://localhost:8000" -ForegroundColor Green
Write-Host " Ctrl+C de dung" -ForegroundColor Gray
Write-Host ""

.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
