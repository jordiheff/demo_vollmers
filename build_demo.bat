@echo off
REM Build script for Nutrition Label Generator Demo (Windows)
REM
REM Prerequisites:
REM - Python 3.10+
REM - Node.js/npm (for frontend build if not already built)
REM - PyInstaller (pip install pyinstaller)

echo ==========================================
echo   Nutrition Label Generator Demo Builder
echo ==========================================
echo.

cd /d "%~dp0"

REM Step 1: Check Python
echo Step 1: Checking prerequisites...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is required. Install from python.org
    pause
    exit /b 1
)
echo   Python OK
echo.

REM Step 2: Install Python dependencies
echo Step 2: Installing Python dependencies...
pip install -r backend\requirements.txt
pip install pyinstaller
if errorlevel 1 (
    echo Error: Failed to install Python dependencies
    pause
    exit /b 1
)
echo   Python dependencies installed
echo.

REM Step 3: Check if frontend is already built
if not exist "backend\static\index.html" (
    echo Step 3: Building frontend...
    cd frontend
    if exist "node_modules" (
        npm run build
    ) else (
        npm install
        npm run build
    )
    cd ..

    REM Copy frontend to backend/static
    echo   Copying frontend to backend/static...
    if exist "backend\static" rmdir /s /q backend\static
    mkdir backend\static
    xcopy /s /e /q frontend\dist\* backend\static\
    echo   Frontend built
) else (
    echo Step 3: Frontend already built, skipping...
)
echo.

REM Step 4: Check .env file
echo Step 4: Checking configuration...
if not exist ".env" (
    echo WARNING: No .env file found!
    echo Creating template .env file...
    (
        echo # Nutrition Label Generator Configuration
        echo # IMPORTANT: Add your OpenAI API key below before building!
        echo.
        echo OPENAI_API_KEY=your_api_key_here
        echo.
        echo # Optional: USDA API key for enhanced nutrition data
        echo # USDA_API_KEY=your_usda_key_here
        echo.
        echo # Rate limiting ^(disabled for demo^)
        echo RATE_LIMIT_ENABLED=false
        echo.
        echo # CORS ^(localhost for demo^)
        echo CORS_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
    ) > .env
    echo Template .env created. Please edit it and add your OpenAI API key.
    echo.
    echo IMPORTANT: Edit .env and add your API key, then run this script again!
    pause
    exit /b 0
) else (
    echo   .env file found
)
echo.

REM Step 5: Build executable
echo Step 5: Building Windows executable...
pyinstaller nutrition_label.spec --clean
if errorlevel 1 (
    echo Error: PyInstaller build failed
    pause
    exit /b 1
)
echo   Executable built
echo.

REM Step 6: Copy .env to dist
echo Step 6: Copying configuration to dist...
copy .env dist\NutritionLabelGenerator\
echo   Configuration copied
echo.

REM Step 7: Create README
echo Step 7: Creating README...
(
    echo ====================================================
    echo   Nutrition Label Generator - Demo Version
    echo ====================================================
    echo.
    echo QUICK START:
    echo 1. Double-click NutritionLabelGenerator.exe
    echo 2. Wait for browser to open ^(about 2 seconds^)
    echo 3. Use the application!
    echo.
    echo TO QUIT:
    echo - Close the black console window
    echo - Or press Ctrl+C in the console
    echo.
    echo REQUIREMENTS:
    echo - Windows 10 or later
    echo - Internet connection ^(for OpenAI API^)
    echo - Modern web browser ^(Chrome, Firefox, Edge^)
    echo.
    echo TROUBLESHOOTING:
    echo - If nothing happens, make sure you have internet access
    echo - If you get an API error, the OpenAI API key may be invalid
    echo - Try running as Administrator if you have issues
    echo.
    echo NOTES:
    echo - Your files are processed using OpenAI's GPT-4o Vision
    echo - No data is stored on external servers
    echo - The application runs entirely on your computer
    echo.
    echo For support, contact the developer.
) > dist\NutritionLabelGenerator\README.txt
echo   README created
echo.

echo ==========================================
echo   BUILD COMPLETE!
echo ==========================================
echo.
echo Output directory: dist\NutritionLabelGenerator\
echo.
echo To distribute, zip the NutritionLabelGenerator folder.
echo.
pause
