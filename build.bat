@echo off
REM ===================================================================
REM  D-Clinic / Zenith Soft  -  production Windows build script
REM
REM  Step 1: builds a standalone, fully offline application with
REM          PyInstaller using D-Clinic.spec
REM          -> dist\D-Clinic\D-Clinic.exe
REM  Step 2: if Inno Setup (ISCC.exe) is installed, also builds a
REM          professional installer
REM          -> installer\Output\D-Clinic-Setup-1.0.0.exe
REM ===================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo  ============================================
echo   D-Clinic - building production executable
echo  ============================================
echo.

REM 1) Ensure build tools / dependencies are present
python -m pip install --upgrade pyinstaller >nul 2>&1
python -m pip install -r requirements.txt >nul 2>&1

REM 2) Clean previous artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 3) Build the one-folder app from the spec (icon, fonts, assets, metadata)
python -m PyInstaller --noconfirm --clean D-Clinic.spec
if errorlevel 1 (
    echo.
    echo  *** BUILD FAILED - see the messages above. ***
    pause
    exit /b 1
)

if not exist "dist\D-Clinic\D-Clinic.exe" (
    echo.
    echo  *** Expected dist\D-Clinic\D-Clinic.exe was not produced. ***
    pause
    exit /b 1
)

echo.
echo  [OK] Application built:  dist\D-Clinic\D-Clinic.exe
echo.

REM 4) Build the Windows installer with Inno Setup, if available
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe"      set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if defined ISCC (
    echo  Building installer with Inno Setup...
    "!ISCC!" "installer\D-Clinic.iss"
    if errorlevel 1 (
        echo  *** Installer build failed - see messages above. ***
        pause
        exit /b 1
    )
    echo.
    echo  ============================================
    echo   Done!
    echo     App folder : dist\D-Clinic\
    echo     Installer  : installer\Output\D-Clinic-Setup-1.0.0.exe
    echo  ============================================
) else (
    echo  Inno Setup not found - skipped installer step.
    echo  Install it from https://jrsoftware.org/isdl.php and re-run,
    echo  or distribute the portable folder dist\D-Clinic\ as-is.
    echo.
    echo  ============================================
    echo   Done!  App folder: dist\D-Clinic\
    echo  ============================================
)

echo.
pause
endlocal
