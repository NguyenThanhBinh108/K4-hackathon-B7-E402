# start.ps1 — Chay trong PowerShell
# Cach dung: .\codebase\start.ps1
# Hoac: cd codebase ; .\start.ps1

$ErrorActionPreference = "Stop"
$backendPath = Join-Path $PSScriptRoot "backend"
Set-Location $backendPath

Write-Host "[1/4] Kiem tra Python..." -ForegroundColor Cyan
$pyVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "LOI: Python chua cai. Vao https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host "     $pyVersion" -ForegroundColor Green

Write-Host "[2/4] Tao .venv neu chua co..." -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "     Da tao .venv" -ForegroundColor Green
} else {
    Write-Host "     .venv da ton tai" -ForegroundColor Green
}

Write-Host "[3/4] Kich hoat .venv..." -ForegroundColor Cyan
& ".venv\Scripts\Activate.ps1"

Write-Host "[3/4] Cai packages..." -ForegroundColor Cyan
pip install -r requirements.txt -q --disable-pip-version-check
Write-Host "     Packages OK" -ForegroundColor Green

Write-Host ""
Write-Host "=========================================" -ForegroundColor Magenta
Write-Host "  App : http://localhost:8000" -ForegroundColor White
Write-Host "  API : http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Dung: Ctrl+C" -ForegroundColor White
Write-Host "=========================================" -ForegroundColor Magenta
Write-Host ""

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
