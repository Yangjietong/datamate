@echo off
REM Configuration Manager - Toggle long-term memory feature
echo ========================================
echo AI Assistant - Configuration Manager
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [ERROR] .env file not found
    echo Please run install.bat first
    pause
    exit /b 1
)

echo Current configuration:
echo.

REM Check MEM0_API_KEY in .env
findstr /C:"MEM0_API_KEY=" .env >nul 2>&1
if errorlevel 1 (
    echo [MEMORY] Long-term memory: DISABLED (no MEM0_API_KEY)
    set CURRENT_STATE=disabled
) else (
    findstr /C:"# MEM0_API_KEY=" .env >nul 2>&1
    if errorlevel 1 (
        echo [MEMORY] Long-term memory: ENABLED (MEM0_API_KEY configured)
        set CURRENT_STATE=enabled
    ) else (
        echo [MEMORY] Long-term memory: DISABLED (MEM0_API_KEY commented out)
        set CURRENT_STATE=disabled
    )
)
echo.

echo What would you like to do?
echo.
echo 1. Enable long-term memory
echo 2. Disable long-term memory
echo 3. Check status only (exit)
echo.
set /p CHOICE="Enter choice (1-3): "

if "%CHOICE%"=="1" (
    echo.
    echo [INFO] Enabling long-term memory...
    echo.
    echo To enable long-term memory, you need:
    echo 1. MEM0_API_KEY from https://app.mem0.ai/
    echo 2. Uncomment and fill the key in .env file
    echo.
    echo Opening .env file for editing...
    notepad .env
    echo.
    echo [INFO] Installing mem0ai package...
    .venv\Scripts\python.exe -m pip install "mem0ai>=0.1.50"
    if errorlevel 1 (
        echo [ERROR] Failed to install mem0ai
        pause
        exit /b 1
    )
    echo [OK] mem0ai installed
    echo.
    echo After saving:
    echo - Make sure MEM0_API_KEY=your_key_here is uncommented
    echo - Restart the application
    echo.
) else if "%CHOICE%"=="2" (
    echo.
    echo [INFO] Disabling long-term memory...
    REM Comment out MEM0_API_KEY in .env
    powershell -Command "(Get-Content .env) -replace '^MEM0_API_KEY=', '# MEM0_API_KEY=' | Set-Content .env"
    echo [OK] Long-term memory disabled
    echo Restart the application for changes to take effect
    echo.
) else if "%CHOICE%"=="3" (
    echo.
    echo [INFO] No changes made
    echo.
) else (
    echo.
    echo [ERROR] Invalid choice
    echo.
)

pause
