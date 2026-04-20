# Krishi Project - Startup Logger (PowerShell)
# Run: powershell -ExecutionPolicy Bypass -File RUN_STARTUP_CHECK.ps1

Write-Host "" 
Write-Host "========================================" -ForegroundColor Green
Write-Host "KRISHI PROJECT - STARTUP CHECK" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Get script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python or add it to PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Starting Krishi Startup Logger..." -ForegroundColor Yellow
Write-Host ""

# Run startup logger
try {
    python startup_logger.py
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ Startup check completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "For detailed logs, check:" -ForegroundColor Cyan
    Write-Host "  - logs\krishi_errors.log (errors only)" -ForegroundColor White
    Write-Host "  - logs\krishi_startup.log (startup details)" -ForegroundColor White
    Write-Host "  - logs\krishi_main.log (all events)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ ERROR: Startup check failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Read-Host "Press Enter to exit"
