#!/bin/bash

# Kill existing Chrome
echo "Killing existing Chrome processes..."
pkill -f "Google Chrome"
sleep 2

# Start Chrome with proper flags
echo "Starting Chrome with debugging flags..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=9222 \
    --user-data-dir=/Users/tieli/.chrome-wf \
    --no-first-run \
    --no-default-browser-check \
    --remote-allow-origins='*' \
    --enable-automation \
    --disable-blink-features=AutomationControlled &

echo "Chrome started. Waiting for it to be ready..."
sleep 3

# Verify Chrome is running
if curl -s http://localhost:9222/json/version > /dev/null 2>&1; then
    echo "✅ Chrome is running with debugging enabled on port 9222"
    curl -s http://localhost:9222/json/version | grep -o '"Browser":"[^"]*"' | cut -d'"' -f4
else
    echo "❌ Chrome failed to start properly"
    exit 1
fi