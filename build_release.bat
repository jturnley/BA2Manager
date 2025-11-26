@echo off
REM BA2 Manager v2.0.0 Production Release Build Script
echo ========================================
echo BA2 Manager v2.0.0 Release Build
echo ========================================
echo.

REM Set version
set VERSION=2.0.0
set RELEASE_DIR=releases\v%VERSION%

REM Clean previous builds
echo [1/5] Cleaning previous builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist %RELEASE_DIR% rmdir /s /q %RELEASE_DIR%
mkdir %RELEASE_DIR%

REM Build the executable
echo.
echo [2/5] Building BA2 Manager executable...
pyinstaller --noconfirm ba2-manager.spec
if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

REM Create release package
echo.
echo [3/5] Creating release package...
mkdir %RELEASE_DIR%\BA2_Manager_v%VERSION%
xcopy /E /I /Y dist\ba2-manager %RELEASE_DIR%\BA2_Manager_v%VERSION%\ba2-manager
copy README.md %RELEASE_DIR%\BA2_Manager_v%VERSION%\
copy LICENSE %RELEASE_DIR%\BA2_Manager_v%VERSION%\
copy CHANGELOG.md %RELEASE_DIR%\BA2_Manager_v%VERSION%\
copy QUICK_START.md %RELEASE_DIR%\BA2_Manager_v%VERSION%\

REM Create source package
echo.
echo [4/5] Creating source code package...
mkdir %RELEASE_DIR%\BA2_Manager_v%VERSION%_Source
xcopy /E /I /Y ba2_manager %RELEASE_DIR%\BA2_Manager_v%VERSION%_Source\ba2_manager
xcopy /E /I /Y tests %RELEASE_DIR%\BA2_Manager_v%VERSION%_Source\tests
copy ba2-manager.spec %RELEASE_DIR%\BA2_Manager_v%VERSION%_Source\
copy pyproject.toml %RELEASE_DIR%\BA2_Manager_v%VERSION%_Source\
copy requirements-dev.txt %RELEASE_DIR%\BA2_Manager_v%VERSION%_Source\
copy README.md %RELEASE_DIR%\BA2_Manager_v%VERSION%_Source\
copy LICENSE %RELEASE_DIR%\BA2_Manager_v%VERSION%_Source\
copy CHANGELOG.md %RELEASE_DIR%\BA2_Manager_v%VERSION%_Source\
copy app.ico %RELEASE_DIR%\BA2_Manager_v%VERSION%_Source\
copy create_icon.py %RELEASE_DIR%\BA2_Manager_v%VERSION%_Source\

REM Create zip archives
echo.
echo [5/5] Creating zip archives...
cd %RELEASE_DIR%
powershell Compress-Archive -Path BA2_Manager_v%VERSION% -DestinationPath BA2_Manager_v%VERSION%_Windows.zip -Force
powershell Compress-Archive -Path BA2_Manager_v%VERSION%_Source -DestinationPath BA2_Manager_v%VERSION%_Source.zip -Force
cd ..\..

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo Binary package: %RELEASE_DIR%\BA2_Manager_v%VERSION%_Windows.zip
echo Source package: %RELEASE_DIR%\BA2_Manager_v%VERSION%_Source.zip
echo.
pause
