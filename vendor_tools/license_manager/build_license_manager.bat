@echo off
REM ===================================================================
REM  Build the Zenith Soft License Manager (VENDOR-ONLY tool)
REM  Produces: dist\LicenseManager\LicenseManager.exe
REM  Optionally compiles an installer if Inno Setup 6 is installed.
REM ===================================================================
setlocal

echo [1/4] Creating a CLEAN build virtual environment ...
set "VENV=.venv-build"
if exist "%VENV%" rmdir /s /q "%VENV%"
python -m venv "%VENV%"
if errorlevel 1 ( echo Could not create venv. & exit /b 1 )
call "%VENV%\Scripts\activate.bat"

echo [2/4] Installing pinned, matched dependencies ...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
python -m pip install pyinstaller
REM Sanity check: bindings and Qt runtime versions MUST match
python -c "from PyQt6 import QtCore,QtGui,QtWidgets; print('PyQt6',QtCore.PYQT_VERSION_STR,'/ Qt',QtCore.QT_VERSION_STR)"
if errorlevel 1 ( echo PyQt6 import check failed (mismatched Qt DLLs?). & exit /b 1 )

echo [3/4] Cleaning old build output ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [4/4] Building LicenseManager.exe ...
pyinstaller --noconfirm --clean LicenseManager.spec
if errorlevel 1 (
    echo BUILD FAILED.
    exit /b 1
)

echo.
echo Built: dist\LicenseManager\LicenseManager.exe

REM Optional installer (Inno Setup 6)
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
    echo Compiling installer ...
    "%ISCC%" LicenseManager.iss
    echo Installer: Output\LicenseManager-Setup.exe
) else (
    echo Inno Setup 6 not found - skipping installer. Ship dist\LicenseManager\ instead.
)

echo.
echo IMPORTANT: copy your license_private\private_key.hex NEXT TO the exe
echo (do NOT bundle it in the build, and never give it to customers).
endlocal
