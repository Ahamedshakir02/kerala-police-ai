# Kerala Police AI — Start Backend Server
# Usage:  cd backend;  .\start.ps1

$VenvPython = "$PSScriptRoot\venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "❌ venv not found. Run .\setup.ps1 first." -ForegroundColor Red
    exit 1
}

Write-Host "`n🚔 Starting Kerala Police AI Backend..." -ForegroundColor Cyan
Write-Host "   API docs: http://localhost:8000/api/docs"
Write-Host "   Health:   http://localhost:8000/api/health`n"

& $VenvPython -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
