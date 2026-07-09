@echo off
REM AI Assistant - Chat Launcher
setlocal enabledelayedexpansion

if not exist .venv\Scripts\python.exe (
    echo [ERROR] Virtual environment not found. Please run install.bat first.
    pause
    exit /b 1
)

:MENU
cls
echo ========================================
echo AI Assistant - Chat Launcher
echo ========================================
echo.
echo 1. New conversation
echo 2. Browse previous conversations
echo 3. Resume a previous conversation
echo 4. Exit
echo.
set /p CHOICE="Enter choice (1-4): "

if "%CHOICE%"=="1" goto NEW_CHAT
if "%CHOICE%"=="2" goto BROWSE
if "%CHOICE%"=="3" goto RESUME
if "%CHOICE%"=="4" goto END

echo.
echo [ERROR] Invalid choice
echo.
pause
goto MENU

:NEW_CHAT
echo.
.venv\Scripts\python.exe main.py
goto AFTER_CHAT

:BROWSE
echo.
.venv\Scripts\python.exe cli_conversation.py list
echo.
set /p SHOW_ID="Enter a Session ID to view details (or press Enter to go back): "
if not "%SHOW_ID%"=="" (
    echo.
    .venv\Scripts\python.exe cli_conversation.py show %SHOW_ID%
)
echo.
pause
goto MENU

:RESUME
echo.
.venv\Scripts\python.exe cli_conversation.py list
echo.
set /p SESSION_ID="Enter the Session ID to resume (or press Enter to go back): "
if "%SESSION_ID%"=="" goto MENU
echo.
.venv\Scripts\python.exe main.py --session-id %SESSION_ID%
goto AFTER_CHAT

:AFTER_CHAT
echo.
set /p AGAIN="Return to menu? (Y/n): "
if /i "%AGAIN%"=="n" goto END
goto MENU

:END
echo.
echo Bye!
pause
endlocal
