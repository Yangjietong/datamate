@echo off
REM AI Assistant - Windows Quick Install Script
echo ========================================
echo AI Assistant - Quick Install
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] Detected Python version:
python --version
echo.

REM Create virtual environment
echo [2/5] Creating virtual environment...
if not exist .venv (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [SKIP] Virtual environment already exists
)
echo.

REM Activate and install dependencies
echo [3/5] Installing dependencies...
call .venv\Scripts\activate.bat
python -m ensurepip --upgrade >nul 2>&1
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Copy config template
echo [4/5] Configuration setup...
if not exist .env (
    copy .env.example .env >nul
    echo [INFO] Created .env config file
    echo.
    echo [IMPORTANT] Edit .env file and fill in your API keys:
    echo   - DEEPSEEK_API_KEY (Required)
    echo   - QIANFAN_API_KEY (Required)
    echo   - EMBEDDING_API_KEY (Required)
    echo   - MEM0_API_KEY (Optional - for long-term memory)
    echo.
) else (
    echo [OK] Config file already exists
)
echo.

REM Ask about long-term memory feature
echo [5/5] Optional Feature Configuration...
echo.
echo Do you want to enable long-term memory feature?
echo (Requires MEM0_API_KEY from https://app.mem0.ai/)
echo.
set /p ENABLE_MEMORY="Enable long-term memory? (y/N): "

if /i "%ENABLE_MEMORY%"=="y" (
    echo.
    echo [INFO] Installing mem0ai package...
    python -m pip install "mem0ai>=0.1.50"
    if errorlevel 1 (
        echo [ERROR] Failed to install mem0ai
        pause
        exit /b 1
    )
    echo [OK] mem0ai installed
    echo Please configure MEM0_API_KEY in .env file
    echo.
) else (
    echo.
    echo [INFO] Long-term memory will be DISABLED (default)
    echo You can enable it later by:
    echo   1. Run: python -m pip install mem0ai
    echo   2. Configure MEM0_API_KEY in .env
)
echo.

echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit .env file and fill in API keys
if /i "%ENABLE_MEMORY%"=="y" (
    echo   2. Get MEM0_API_KEY from https://app.mem0.ai/
    echo   3. Run: .venv\Scripts\activate
    echo   4. Run: python main.py
) else (
    echo   2. Run: .venv\Scripts\activate
    echo   3. Run: python main.py
)
echo.
echo For help, see README.md or QUICKSTART.md
echo.
pause
