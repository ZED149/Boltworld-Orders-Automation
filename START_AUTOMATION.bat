@echo off
setlocal EnableDelayedExpansion

title Boltworld Order Automation - Zed Management Systems
mode con: cols=70 lines=45
color 0F
reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1
cd /d "%~dp0"

cls
echo.
echo  ============================================================
echo   BOLTWORLD ORDER AUTOMATION - ZED MANAGEMENT SYSTEMS
echo  ============================================================
echo.


:: ── STEP 1: Find Python ──────────────────────────────────────────────────
echo  [1/4] Locating Python...

set PYTHON=

:: Try 'python' command first (in PATH)
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=python
    goto :python_found
)

:: Try 'py' launcher (Windows Python Launcher)
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON=py
    goto :python_found
)

:: Search common install locations manually
set SEARCH_PATHS=^
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" ^
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" ^
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" ^
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" ^
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"  ^
    "C:\Python313\python.exe"                             ^
    "C:\Python312\python.exe"                             ^
    "C:\Python311\python.exe"                             ^
    "C:\Python310\python.exe"                             ^
    "C:\Python39\python.exe"                              ^
    "C:\Program Files\Python313\python.exe"               ^
    "C:\Program Files\Python312\python.exe"               ^
    "C:\Program Files\Python311\python.exe"               ^
    "C:\Program Files\Python310\python.exe"

for %%p in (%SEARCH_PATHS%) do (
    if exist %%p (
        set PYTHON=%%p
        goto :python_found
    )
)

:: Also search via registry
for /f "tokens=*" %%k in ('reg query "HKCU\Software\Python\PythonCore" /s /f "InstallPath" 2^>nul ^| findstr /i "InstallPath"') do (
    for /f "tokens=2,*" %%a in ('reg query "%%k" /ve 2^>nul ^| findstr /i "REG_SZ"') do (
        if exist "%%b\python.exe" (
            set PYTHON="%%b\python.exe"
            goto :python_found
        )
    )
)

:: Python truly not found anywhere
echo.
echo  ============================================================
echo   PYTHON NOT FOUND
echo  ============================================================
echo.
echo   Python could not be found on this computer.
echo.
echo   Please install it:
echo.
echo   1. Go to  https://www.python.org/downloads/
echo   2. Click "Download Python 3.x" (the big yellow button)
echo   3. Run the downloaded installer
echo   4. IMPORTANT: on the first screen, tick the box that says:
echo      "Add Python to PATH"  (at the bottom of the window)
echo   5. Click "Install Now"
echo   6. When finished, close this window and double-click again
echo.
echo  ============================================================
echo.
pause
exit /b 1

:python_found
for /f "tokens=*" %%v in ('!PYTHON! --version 2^>^&1') do echo  [OK] %%v found at !PYTHON!


:: ── STEP 2: pip check ────────────────────────────────────────────────────
echo.
echo  [2/4] Checking pip...
!PYTHON! -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [..] pip missing - installing...
    !PYTHON! -m ensurepip --upgrade >nul 2>&1
    !PYTHON! -m pip --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo.
        echo  ============================================================
        echo   PIP COULD NOT BE INSTALLED
        echo  ============================================================
        echo.
        echo   Please do the following:
        echo.
        echo   1. Open Command Prompt as Administrator
        echo      (right-click Start, choose "Command Prompt (Admin)")
        echo   2. Type this and press Enter:
        echo      python -m ensurepip --upgrade
        echo   3. Wait for it to finish
        echo   4. Double-click this file again
        echo.
        echo  ============================================================
        echo.
        pause
        exit /b 1
    )
)
echo  [OK] pip is available


:: ── STEP 3: Install packages ─────────────────────────────────────────────
echo.
echo  [3/4] Installing required packages...
echo        (first run takes ~1 minute, after that it is instant)
echo.

set PACKAGES=requests reportlab pywin32 pypdf python-dotenv

for %%p in (%PACKAGES%) do (
    echo  [..] %%p
    !PYTHON! -m pip install %%p -q --disable-pip-version-check 2>nul
    if !errorlevel! neq 0 (
        echo.
        echo  ============================================================
        echo   FAILED TO INSTALL: %%p
        echo  ============================================================
        echo.
        echo   This is usually a network issue. Please:
        echo.
        echo   1. Check your internet connection
        echo   2. Double-click this file again
        echo.
        echo   If the problem continues, contact Zed Management Systems.
        echo.
        echo  ============================================================
        echo.
        pause
        exit /b 1
    )
    echo  [OK] %%p
)


:: ── STEP 4: Check required files ─────────────────────────────────────────
echo.
echo  [4/4] Checking required files...

set MISSING=0
if not exist "%~dp0BoltworldLauncher.py"  set MISSING=1
if not exist "%~dp0check_orders.py"        set MISSING=1
if not exist "%~dp0report_generator.py"    set MISSING=1
if not exist "%~dp0.env"                    set MISSING=1

if %MISSING%==1 (
    echo.
    echo  ============================================================
    echo   MISSING FILES DETECTED
    echo  ============================================================
    echo.
    echo   The following files must all be in the same folder:
    echo.
    echo     START_AUTOMATION.bat      ^(this file^)
    echo     BoltworldLauncher.py
    echo     check_orders.py
    echo     report_generator.py
    echo     .env
    echo.
    echo   Missing:
    if not exist "%~dp0BoltworldLauncher.py"  echo     - BoltworldLauncher.py
    if not exist "%~dp0check_orders.py"        echo     - check_orders.py
    if not exist "%~dp0report_generator.py"    echo     - report_generator.py
    if not exist "%~dp0.env"                   echo     - .env
    echo.
    echo  ============================================================
    echo.
    pause
    exit /b 1
)
echo  [OK] All files found


:: ── ALL CHECKS PASSED ────────────────────────────────────────────────────
echo.
echo  ============================================================
echo   All checks passed. Launching automation...
echo  ============================================================
echo.
timeout /t 2 /nobreak >nul

!PYTHON! "%~dp0BoltworldLauncher.py"

echo.
echo  ============================================================
echo   Automation stopped. Press any key to close.
echo  ============================================================
pause >nul