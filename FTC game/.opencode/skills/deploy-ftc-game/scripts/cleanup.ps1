# cleanup.ps1 — Remove PyInstaller build artifacts
# Usage: powershell -ExecutionPolicy Bypass -File cleanup.ps1
# Run from the workspace root (FTC-game-TEAM-19084-ZENITH/)

$specDir = Join-Path $PSScriptRoot "..\..\..\FTC game"
$buildDir = Join-Path $specDir "build"
$distDir = Join-Path $specDir "dist"

$cleaned = 0

if (Test-Path $buildDir) {
    Remove-Item -Recurse -Force $buildDir
    Write-Host "Removed: build/" -ForegroundColor Yellow
    $cleaned++
}

if (Test-Path $distDir) {
    Remove-Item -Recurse -Force $distDir
    Write-Host "Removed: dist/" -ForegroundColor Yellow
    $cleaned++
}

if ($cleaned -eq 0) {
    Write-Host "Nothing to clean - build/ and dist/ do not exist." -ForegroundColor Gray
} else {
    Write-Host "Cleanup done: $cleaned folders removed." -ForegroundColor Green
}
