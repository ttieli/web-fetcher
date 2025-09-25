"""Simple configuration for plugins.

This module provides basic configuration for the curl plugin and other plugins.
Uses Python dictionaries for simplicity, no YAML required.
"""

# Curl plugin configuration
CURL_CONFIG = {
    "enabled": True,
    "priority": 0,  # FALLBACK priority
    "timeout_buffer": 5,  # Extra seconds on top of context timeout
    "ssl_ignore": True,  # Use -k flag to ignore SSL issues
    "follow_redirects": True,  # Use -L flag to follow redirects
    "compressed": True,  # Use --compressed flag
    "default_user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36",
    "default_headers": {
        "Accept-Language": "zh-CN,zh;q=0.9"
    }
}

# HTTP plugin configuration  
HTTP_CONFIG = {
    "enabled": True,
    "priority": 50,  # NORMAL priority
    "timeout": 30,
    "max_retries": 3,
    "default_user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"
}

# Safari plugin configuration
SAFARI_CONFIG = {
    "enabled": True, 
    "priority": 100,  # HIGH priority for supported domains
    "timeout": 30,
    "max_retries": 2
}

# Playwright plugin configuration
PLAYWRIGHT_CONFIG = {
    "enabled": True,
    "priority": 50,  # NORMAL priority - JavaScript rendering capability
    "timeout_ms": 60000,  # 60 seconds timeout
    "headless": True,
    "viewport": {"width": 390, "height": 844},
    "device_scale_factor": 3,
    "locale": "zh-CN",
    "default_user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "wait_strategy": "domcontentloaded",  # Options: load, domcontentloaded, networkidle
    "scroll_to_bottom": True,
    "scroll_delay": 800,  # ms to wait before scrolling
    "page_load_delay": 600,  # ms to wait after scrolling
}

# Global plugin system configuration
PLUGIN_SYSTEM_CONFIG = {
    "auto_discovery": True,
    "fallback_to_legacy": True,
    "max_plugin_attempts": 3,
    "log_plugin_failures": True
}

def get_plugin_config(plugin_name: str) -> dict:
    """Get configuration for a specific plugin."""
    config_map = {
        "curl": CURL_CONFIG,
        "http": HTTP_CONFIG, 
        "safari": SAFARI_CONFIG,
        "playwright": PLAYWRIGHT_CONFIG
    }
    return config_map.get(plugin_name, {})

def is_plugin_enabled(plugin_name: str) -> bool:
    """Check if a plugin is enabled."""
    config = get_plugin_config(plugin_name)
    return config.get("enabled", False)