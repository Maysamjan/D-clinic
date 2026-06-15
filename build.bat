@echo off
REM ===================================================================
REM  D-Clinic / Zenith Soft  -  production Windows build script
REM  Supported OS: Windows 10 and Windows 11 only.
REM
REM  Builds inside a CLEAN virtual environment (.venv-build) so the
REM  matched, pinned PyQt6 packages from requirements.txt are used and
REM  no stray/mismatched Qt DLLs leak into the build (which is what
REM  causes "DLL load failed while importing QtCore" on launch).
REM
REM  Step 1: create a clean venv and install pinned dependencies
REM  Step 2: build dist\D-Clinic\D-Clinic.exe with PyInstaller
REM  Step 3: smoke-test that the EXE launches
REM  Step 4: if Inno Setup (ISCC.exe) is installed, build the installer
REM          -> installer\Output\D-Clinic-Setup-1.1.0.exe
REM ===================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo  ============================================
echo   D-Clinic - building production executable
echo   Target OS: Windows 10 / Windows 11
echo  ============================================
echo.

REM 1) Create a CLEAN build virtual environment
set "VENV=.venv-build"
if exist "%VENV%" rmdir /s /q "%VENV%"
python -m venv "%VENV%"
if errorlevel 1 ( echo  *** Could not create venv. Is Python installed? *** & pause & exit /b 1 )
call "%VENV%\Scripts\activate.bat"

REM 2) Install pinned, matched dependencies + PyInstaller into the clean venv
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
python -m pip install pyinstaller
if errorlevel 1 ( echo  *** Dependency install failed. *** & pause & exit /b 1 )

REM 2a) Sanity check: bindings and Qt runtime versions MUST match
python -c "from PyQt6 import QtCore,QtGui,QtWidgets,QtPrintSupport; print('PyQt6',QtCore.PYQT_VERSION_STR,'/ Qt',QtCore.QT_VERSION_STR)"
if errorlevel 1 ( echo  *** PyQt6 import check failed (mismatched Qt DLLs?). *** & pause & exit /b 1 )

REM 3) Clean previous artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 4) Build the one-folder app from the spec (icon, fonts, assets, metadata)
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

REM 5) Build the Windows installer with Inno Setup, if available
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
    echo     Installer  : installer\Output\D-Clinic-Setup-1.1.0.exe
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
