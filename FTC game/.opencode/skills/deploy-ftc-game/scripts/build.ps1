# build.ps1 — Build and deploy the FTC DECODE Simulator executable
# Usage: powershell -ExecutionPolicy Bypass -File build.ps1
# Run from the workspace root (FTC-game-TEAM-19084-ZENITH/)

$ErrorActionPreference = "Stop"
$workspaceRoot = Join-Path $PSScriptRoot "..\..\..\..\.."
$specDir = Join-Path $PSScriptRoot "..\..\..\.."
$specFile = Join-Path $specDir "FTC_DECODE_Simulator.spec"
$exeDest = Join-Path $workspaceRoot "EXECUTABLE\FTC_DECODE_Simulator.exe"

# Verify spec file exists
if (-not (Test-Path $specFile)) {
    Write-Host "ERROR: Spec file not found at $specFile" -ForegroundColor Red
    exit 1
}

Write-Host "Building FTC_DECODE_Simulator.exe ..." -ForegroundColor Cyan

Push-Location $specDir
try {
    pyinstaller FTC_DECODE_Simulator.spec --noconfirm
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: PyInstaller failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

# Verify the built exe exists
$builtExe = Join-Path $specDir "dist\FTC_DECODE_Simulator.exe"
if (-not (Test-Path $builtExe)) {
    Write-Host "ERROR: Built exe not found at $builtExe" -ForegroundColor Red
    exit 1
}

# Copy to deployment location
Write-Host "Deploying to EXECUTABLE folder ..." -ForegroundColor Cyan
Copy-Item -LiteralPath $builtExe -Destination $exeDest -Force

$size = (Get-Item $exeDest).Length
$sizeMB = [math]::Round($size / 1MB, 1)
Write-Host "Deployed: $exeDest ($sizeMB MB)" -ForegroundColor Green

# Cleanup build artifacts
Write-Host "Cleaning up build artifacts ..." -ForegroundColor Cyan
Remove-Item -Recurse -Force (Join-Path $specDir "build") -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force (Join-Path $specDir "dist") -ErrorAction SilentlyContinue
Write-Host "Cleanup done." -ForegroundColor Green

Write-Host "Build complete!" -ForegroundColor Green
