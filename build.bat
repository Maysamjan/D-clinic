@echo off
REM ===================================================================
REM  D-Clinic / Zenith Soft  -  one-click Windows build script
REM  Produces a standalone, fully offline executable in dist\D-Clinic\
REM ===================================================================
setlocal

echo.
echo  ============================================
echo   Building D-Clinic standalone executable...
echo  ============================================
echo.

REM 1) Make sure PyInstaller is available
python -m pip install --upgrade pyinstaller >nul 2>&1
python -m pip install -r requirements.txt >nul 2>&1

REM 2) Clean previous build artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 3) Build (windowed = no console window, with app icon + bundled assets)
python -m PyInstaller --noconfirm --windowed --name D-Clinic ^
    --icon assets\icon.ico ^
    --add-data "app\resources\styles.qss;app\resources" ^
    --add-data "assets;assets" ^
    main.py

if errorlevel 1 (
    echo.
    echo  *** BUILD FAILED - see the messages above. ***
    pause
    exit /b 1
)

echo.
echo  ============================================
echo   Done!  Your program is here:
echo     dist\D-Clinic\D-Clinic.exe
echo  ============================================
echo.
echo  Copy the whole "dist\D-Clinic" folder to the clinic computer
echo  and run D-Clinic.exe . The program is fully offline.
echo.
pause
endlocal
