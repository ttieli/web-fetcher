#!/bin/bash

echo "=== Selenium Installation Diagnosis ==="
echo "Diagnostic Time: $(date)"
echo

# Check Python
echo "1. Python Version:"
python --version 2>/dev/null || python3 --version 2>/dev/null || echo "Python not found"
echo

# Check pip
echo "2. Pip Version:"
pip --version 2>/dev/null || pip3 --version 2>/dev/null || echo "Pip not found"
echo

# Check Selenium
echo "3. Selenium Installation:"
python -c "import selenium; print(f'✓ Selenium {selenium.__version__} installed')" 2>&1 || echo "✗ Selenium not installed"
echo

# Check PyYAML
echo "4. PyYAML Installation:"
python -c "import yaml; print('✓ PyYAML installed')" 2>&1 || echo "✗ PyYAML not installed"
echo

# Check lxml
echo "5. lxml Installation:"
python -c "import lxml; print(f'✓ lxml {lxml.__version__} installed')" 2>&1 || echo "✗ lxml not installed"
echo

# Check Chrome
echo "6. Chrome Installation:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version
    else
        echo "✗ Chrome not found at expected location"
    fi
else
    google-chrome --version 2>/dev/null || chromium-browser --version 2>/dev/null || echo "✗ Chrome not found"
fi
echo

# Check port 9222
echo "7. Port 9222 Status:"
if lsof -i :9222 2>/dev/null | grep LISTEN > /dev/null; then
    echo "✓ Port 9222 is in use (Chrome debug likely running)"
    lsof -i :9222 | grep LISTEN
else
    echo "✗ Port 9222 is free (Chrome debug not running)"
fi
echo

# Check Chrome debug connectivity
echo "8. Chrome Debug API Status:"
if curl -s --connect-timeout 2 http://localhost:9222/json/version > /dev/null 2>&1; then
    echo "✓ Chrome debug API responding"
    curl -s http://localhost:9222/json/version | python -m json.tool 2>/dev/null | head -n 5
else
    echo "✗ Chrome debug API not responding"
    echo "  Run: ./config/chrome-debug.sh"
fi
echo

# Check project directory
echo "9. Project Directory Check:"
PROJECT_DIR="/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher"
if [ -d "$PROJECT_DIR" ]; then
    echo "✓ Project directory exists"
    
    # Check key files
    echo "  Checking key files:"
    [ -f "$PROJECT_DIR/selenium_fetcher.py" ] && echo "  ✓ selenium_fetcher.py found" || echo "  ✗ selenium_fetcher.py missing"
    [ -f "$PROJECT_DIR/requirements-selenium.txt" ] && echo "  ✓ requirements-selenium.txt found" || echo "  ✗ requirements-selenium.txt missing"
    [ -f "$PROJECT_DIR/config/chrome-debug.sh" ] && echo "  ✓ chrome-debug.sh found" || echo "  ✗ chrome-debug.sh missing"
else
    echo "✗ Project directory not found"
fi
echo

# Test import
echo "10. Testing SeleniumFetcher import:"
cd "$PROJECT_DIR" 2>/dev/null && {
    python -c "
try:
    from selenium_fetcher import SeleniumFetcher
    print('✓ SeleniumFetcher imports successfully')
except ImportError as e:
    print(f'✗ Import failed: {e}')
except Exception as e:
    print(f'✗ Unexpected error: {e}')
" 2>&1
} || echo "✗ Could not change to project directory"
echo

# Summary
echo "=== Diagnosis Summary ==="
echo
echo "Quick Fix Commands:"
echo "-------------------"

# Check if Selenium is installed
if ! python -c "import selenium" 2>/dev/null; then
    echo "1. Install Selenium:"
    echo "   pip install selenium>=4.15.0 pyyaml>=6.0.0 lxml>=4.9.0"
    echo
fi

# Check if Chrome debug is running
if ! curl -s --connect-timeout 1 http://localhost:9222/json/version > /dev/null 2>&1; then
    echo "2. Start Chrome Debug:"
    echo "   cd '$PROJECT_DIR'"
    echo "   ./config/chrome-debug.sh"
    echo
fi

echo "For detailed troubleshooting, see:"
echo "TASKS/SELENIUM_DEPENDENCIES_INSTALLATION_GUIDE.md"
echo
echo "=== End of Diagnosis ===