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
        "safari": SAFARI_CONFIG
    }
    return config_map.get(plugin_name, {})

def is_plugin_enabled(plugin_name: str) -> bool:
    """Check if a plugin is enabled."""
    config = get_plugin_config(plugin_name)
    return config.get("enabled", False)