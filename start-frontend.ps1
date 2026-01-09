# Frontend startup script with memory optimization
$env:NODE_OPTIONS = "--max-old-space-size=4096"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Frontend Development Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Memory Limit: 4GB (4096 MB)" -ForegroundColor Yellow
Write-Host "Frontend URL: http://localhost:8081" -ForegroundColor Green
Write-Host "Backend API: http://localhost:3001" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""
npm run dev
