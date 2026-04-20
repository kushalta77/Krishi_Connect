@echo off
REM Krishi Project - Startup Logger Batch File
REM Double-click this file to run the comprehensive startup check

echo.
echo ========================================
echo KRISHI PROJECT - STARTUP CHECK
echo ========================================
echo.

REM Get the directory where this batch file is located
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python or add it to your PATH
    pause
    exit /b 1
)

echo Starting Krishi Startup Logger...
echo.

REM Run the startup logger
python startup_logger.py

REM Check if there was an error
if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Startup check failed
    echo Check the output above for details
    echo ========================================
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo Startup check completed successfully!
    echo.
    echo For detailed logs, check:
    echo - logs\krishi_errors.log (errors only)
    echo - logs\krishi_startup.log (startup details)
    echo - logs\krishi_main.log (all events)
    echo ========================================
)

pause
