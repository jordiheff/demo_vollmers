#!/bin/bash
# Build script for Nutrition Label Generator Demo
#
# Prerequisites:
# - Python 3.10+
# - Node.js/Bun (for frontend build)
# - PyInstaller (pip install pyinstaller)
#
# NOTE: PyInstaller must be run on Windows to create a Windows executable.
# This script prepares everything, but the final pyinstaller step
# should be run on a Windows machine.

set -e

echo "=========================================="
echo "  Nutrition Label Generator Demo Builder"
echo "=========================================="
echo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is required"; exit 1; }
command -v bun >/dev/null 2>&1 || command -v npm >/dev/null 2>&1 || { echo "Error: bun or npm is required"; exit 1; }
echo "  Prerequisites OK"
echo

# Step 2: Install Python dependencies
echo "Step 2: Installing Python dependencies..."
pip install -r backend/requirements.txt
pip install pyinstaller
echo "  Python dependencies installed"
echo

# Step 3: Build frontend
echo "Step 3: Building frontend..."
cd frontend
if command -v bun >/dev/null 2>&1; then
    bun install
    bun run build
else
    npm install
    npm run build
fi
cd ..
echo "  Frontend built"
echo

# Step 4: Copy frontend to backend/static
echo "Step 4: Copying frontend to backend/static..."
rm -rf backend/static
mkdir -p backend/static
cp -r frontend/dist/* backend/static/
echo "  Frontend copied to backend/static"
echo

# Step 5: Check .env file
echo "Step 5: Checking configuration..."
if [ ! -f ".env" ]; then
    echo "WARNING: No .env file found!"
    echo "Creating template .env file..."
    cat > .env << 'EOF'
# Nutrition Label Generator Configuration
# IMPORTANT: Add your OpenAI API key below before building!

OPENAI_API_KEY=your_api_key_here

# Optional: USDA API key for enhanced nutrition data
# USDA_API_KEY=your_usda_key_here

# Rate limiting (disabled for demo)
RATE_LIMIT_ENABLED=false

# CORS (localhost for demo)
CORS_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
EOF
    echo "Template .env created. Please edit it and add your OpenAI API key."
else
    echo "  .env file found"
fi
echo

# Step 6: Build executable (only on Windows)
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Step 6: Building Windows executable..."
    pyinstaller nutrition_label.spec --clean
    echo "  Executable built"
    echo

    # Step 7: Copy .env to dist
    echo "Step 7: Copying configuration to dist..."
    cp .env dist/NutritionLabelGenerator/
    echo "  Configuration copied"
    echo

    # Step 8: Create README in dist
    echo "Step 8: Creating README..."
    cat > dist/NutritionLabelGenerator/README.txt << 'EOF'
====================================================
  Nutrition Label Generator - Demo Version
====================================================

QUICK START:
1. Double-click NutritionLabelGenerator.exe
2. Wait for browser to open (about 2 seconds)
3. Use the application!

TO QUIT:
- Close the black console window
- Or press Ctrl+C in the console

REQUIREMENTS:
- Windows 10 or later
- Internet connection (for OpenAI API)
- Modern web browser (Chrome, Firefox, Edge)

TROUBLESHOOTING:
- If nothing happens, make sure you have internet access
- If you get an API error, the OpenAI API key may be invalid
- Try running as Administrator if you have issues

NOTES:
- Your files are processed using OpenAI's GPT-4o Vision
- No data is stored on external servers
- The application runs entirely on your computer

For support, contact the developer.
EOF
    echo "  README created"
    echo

    echo "=========================================="
    echo "  BUILD COMPLETE!"
    echo "=========================================="
    echo
    echo "Output directory: dist/NutritionLabelGenerator/"
    echo
    echo "To distribute:"
    echo "  cd dist"
    echo "  zip -r NutritionLabelGenerator.zip NutritionLabelGenerator/"
    echo
else
    echo "=========================================="
    echo "  PREPARATION COMPLETE!"
    echo "=========================================="
    echo
    echo "The demo is ready for PyInstaller, but PyInstaller"
    echo "must be run on Windows to create a Windows executable."
    echo
    echo "To build on Windows:"
    echo "  1. Copy this entire folder to a Windows machine"
    echo "  2. Install Python 3.10+ and pip"
    echo "  3. Run: pip install -r backend/requirements.txt pyinstaller"
    echo "  4. Run: pyinstaller nutrition_label.spec --clean"
    echo "  5. Copy .env to dist/NutritionLabelGenerator/"
    echo
    echo "Or run on Windows using WSL or a VM."
    echo
fi
