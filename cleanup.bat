@echo off
REM Cleanup script before packaging
echo ========================================
echo Cleanup Before Packaging
echo ========================================
echo.

echo [WARNING] This script will delete:
echo   - .env (contains API keys)
echo   - *.db (conversation database)
echo   - *.csv (generated data files)
echo   - *.png, *.jpg (generated images)
echo   - test_*.py (test files)
echo   - requirements_full.txt
echo.
echo Press any key to continue, or close window to cancel...
pause >nul
echo.

REM Delete sensitive config
if exist .env (
    del .env
    echo [OK] Deleted .env
)

REM Delete database
if exist *.db (
    del *.db
    echo [OK] Deleted database files
)

REM Delete generated files
del /Q *.csv 2>nul
del /Q *.png 2>nul
del /Q *.jpg 2>nul
del /Q *.jpeg 2>nul
echo [OK] Deleted generated files

REM Delete test files
del /Q test_*.py 2>nul
echo [OK] Deleted test files

REM Delete full requirements list
if exist requirements_full.txt (
    del requirements_full.txt
    echo [OK] Deleted requirements_full.txt
)

REM Verify .env.example exists
if not exist .env.example (
    echo [WARNING] .env.example not found
)

echo.
echo ========================================
echo Cleanup Complete!
echo ========================================
echo.
echo Checklist:
echo [ ] .env.example exists and complete
echo [ ] requirements.txt exists
echo [ ] README.md complete
echo [ ] All test files deleted
echo [ ] No hardcoded API keys
echo.
echo Ready to package!
pause
