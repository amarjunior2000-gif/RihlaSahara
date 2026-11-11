$ErrorActionPreference = "Stop"
$Frontend = Join-Path $PSScriptRoot "frontend"
Set-Location $Frontend
Write-Host "[1/4] Installation des dependances..." -ForegroundColor Cyan
npm install
Write-Host "[2/4] Construction de l'application web..." -ForegroundColor Cyan
npm run build
if (-not (Test-Path (Join-Path $Frontend "android"))) {
  Write-Host "[3/4] Creation du projet Android..." -ForegroundColor Cyan
  npx cap add android
} else {
  Write-Host "[3/4] Projet Android deja present." -ForegroundColor Yellow
}
Write-Host "[4/4] Synchronisation Capacitor..." -ForegroundColor Cyan
npx cap sync android
Write-Host "Ouverture Android Studio..." -ForegroundColor Green
npx cap open android
