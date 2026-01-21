# World-Class Frontend Startup Script
# Uses proper process management to avoid blocking Cursor terminal

param(
    [switch]$Background = $false
)

$ErrorActionPreference = "Stop"

# Set memory limit
$env:NODE_OPTIONS = "--max-old-space-size=4096"

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Check if port is already in use
$portInUse = Get-NetTCPConnection -LocalPort 8081 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "Port 8081 is already in use!" -ForegroundColor Red
    Write-Host "Stopping existing process..." -ForegroundColor Yellow
    $process = Get-Process -Id $portInUse.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "node_modules not found. Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Frontend Development Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Memory Limit: 4GB" -ForegroundColor Gray
Write-Host "  Frontend URL: http://localhost:8081" -ForegroundColor Green
Write-Host "  Backend API: http://localhost:3001" -ForegroundColor Gray
Write-Host ""

if ($Background) {
    # Start in background (new window)
    Write-Host "Starting in background window..." -ForegroundColor Yellow
    $psCommand = @"
cd '$scriptDir'; `$env:NODE_OPTIONS = '--max-old-space-size=4096'; Write-Host 'Frontend Server Starting...' -ForegroundColor Green; Write-Host 'URL: http://localhost:8081' -ForegroundColor Cyan; Write-Host ''; npm run dev
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $psCommand
    Write-Host "Frontend is starting in a new window." -ForegroundColor Green
    Write-Host "Check the new PowerShell window for status." -ForegroundColor Gray
} else {
    # Start in foreground
    Write-Host "Starting frontend server..." -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
    Write-Host ""
    npm run dev
}
