@echo off
REM ===================================================================
REM  Build the Zenith Soft License Manager (VENDOR-ONLY tool)
REM  Produces: dist\LicenseManager\LicenseManager.exe
REM  Optionally compiles an installer if Inno Setup 6 is installed.
REM ===================================================================
setlocal

echo [1/3] Installing build dependencies ...
python -m pip install --upgrade pyinstaller >nul
python -m pip install -r requirements.txt >nul

echo [2/3] Cleaning old build output ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [3/3] Building LicenseManager.exe ...
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
