#!/usr/bin/env python3
"""
Test Playwright plugin with mock Playwright library
"""

import sys
import os
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_playwright_plugin_with_mock():
    """Test playwright plugin functionality with mocked Playwright."""
    
    # Create mock playwright module
    mock_playwright = MagicMock()
    mock_browser = MagicMock()
    mock_context = MagicMock()
    mock_page = MagicMock()
    
    # Setup mock chain
    mock_playwright.__enter__ = MagicMock(return_value=mock_playwright)
    mock_playwright.__exit__ = MagicMock(return_value=None)
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    mock_page.content.return_value = """
    <!DOCTYPE html>
    <html>
    <head><title>Example Domain</title></head>
    <body>
        <h1>Example Domain</h1>
        <p>This domain is for use in illustrative examples in documents.</p>
    </body>
    </html>
    """
    mock_page.url = "https://www.example.com"
    
    # Patch the import
    with patch.dict('sys.modules', {'playwright.sync_api': Mock(sync_playwright=lambda: mock_playwright)}):
        from plugins.playwright_fetcher import PlaywrightFetcherPlugin
        from plugins.base import FetchContext
        
        # Test plugin
        plugin = PlaywrightFetcherPlugin()
        
        print("Testing with mocked Playwright:")
        print(f"  Plugin name: {plugin.name}")
        print(f"  Plugin priority: {plugin.priority}")
        print(f"  Is available: {plugin.is_available()}")
        print(f"  Capabilities: {plugin.get_capabilities()}")
        
        # Test fetch
        context = FetchContext(url="https://www.example.com", timeout=30)
        result = plugin.fetch(context)
        
        print(f"\nFetch test:")
        print(f"  Success: {result.success}")
        print(f"  Method: {result.fetch_method}")
        print(f"  Content length: {len(result.html_content) if result.html_content else 0}")
        print(f"  Has expected content: {'Example Domain' in (result.html_content or '')}")
        
        # Verify resource cleanup
        mock_browser.close.assert_called_once()
        print(f"  Browser cleanup called: ✓")
        
        print("\n✅ All mock tests passed!")

if __name__ == "__main__":
    test_playwright_plugin_with_mock()