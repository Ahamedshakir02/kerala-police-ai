# Kerala Police AI — Backend Setup Script
# Run this ONCE to create the venv and install all packages.
# Usage:  cd backend;  .\setup.ps1

$VenvDir = "$PSScriptRoot\venv"
$PythonExe = "$VenvDir\Scripts\python.exe"
$PipExe    = "$VenvDir\Scripts\pip.exe"

Write-Host "`n🚔 Kerala Police AI — Backend Setup" -ForegroundColor Cyan
Write-Host "=" * 50

# ── 1. Find Python 3.13 ───────────────────────────────────────────────────────
Write-Host "`n[1/4] Looking for Python 3.13..." -ForegroundColor Yellow
$py313 = Get-Command python3.13 -ErrorAction SilentlyContinue
if (-not $py313) {
    $py313 = Get-Command python -ErrorAction SilentlyContinue
    if ($py313) {
        $ver = & $py313.Source --version 2>&1
        Write-Host "     Found: $ver at $($py313.Source)"
    } else {
        Write-Host "❌ Python not found. Install Python 3.13 from https://python.org" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "     Found: python3.13 at $($py313.Source)"
}

# ── 2. Create venv ────────────────────────────────────────────────────────────
Write-Host "`n[2/4] Creating virtual environment at $VenvDir..." -ForegroundColor Yellow
if (Test-Path $VenvDir) {
    Remove-Item -Recurse -Force $VenvDir
    Write-Host "     Removed old venv."
}
& $py313.Source -m venv $VenvDir
Write-Host "     ✅ venv created."

# ── 3. Upgrade pip ────────────────────────────────────────────────────────────
Write-Host "`n[3/4] Upgrading pip..." -ForegroundColor Yellow
& $PipExe install --upgrade pip --quiet

# ── 4. Install requirements ───────────────────────────────────────────────────
Write-Host "`n[4/4] Installing packages from requirements.txt..." -ForegroundColor Yellow
Write-Host "     (This may take 5-10 minutes — ML packages are large)`n"
& $PipExe install -r "$PSScriptRoot\requirements.txt"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Setup complete!" -ForegroundColor Green
    Write-Host "`nTo start the backend server, run:" -ForegroundColor Cyan
    Write-Host "   .\start.ps1`n"
} else {
    Write-Host "`n⚠️  Some packages failed. Try running .\start.ps1 — it may still work." -ForegroundColor Yellow
}
