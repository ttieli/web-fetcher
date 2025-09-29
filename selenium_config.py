"""
Selenium Configuration Management for Web_Fetcher

This module provides configuration management for Selenium integration,
loading settings from YAML files and managing Chrome options for
debug port connections.

Author: Cody (Claude Code)
Date: 2025-09-29
Version: 1.0 (Phase 1)
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List


class SeleniumConfigError(Exception):
    """Selenium configuration error"""
    pass


class SeleniumConfig:
    """
    Selenium configuration management.
    Loads defaults from config/selenium_defaults.yaml.
    Handles Chrome options, timeouts, and debug port settings.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to custom config file (optional)
                        If None, loads from config/selenium_defaults.yaml
        """
        self.config_path = config_path
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            if self.config_path:
                config_file = Path(self.config_path)
            else:
                # Use default config relative to this module
                current_dir = Path(__file__).parent
                config_file = current_dir / "config" / "selenium_defaults.yaml"
            
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f)
                logging.info(f"Loaded Selenium config from {config_file}")
            else:
                logging.warning(f"Config file not found: {config_file}, using defaults")
                self._config = self.load_default_config()
                
        except Exception as e:
            logging.error(f"Failed to load Selenium config: {e}")
            self._config = self.load_default_config()
    
    def get_chrome_options(self) -> List[str]:
        """
        Get Chrome options for webdriver.
        
        Returns:
            List of Chrome command line arguments
        """
        try:
            options_config = self._config.get('options', {})
            chrome_options = []
            
            # Core options for debug port connection
            if not options_config.get('headless', False):
                # Never use headless mode - session preservation requirement
                pass
            
            # Add stability options
            chrome_options.extend([
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ])
            
            return chrome_options
            
        except Exception as e:
            logging.error(f"Error getting Chrome options: {e}")
            return ['--no-sandbox', '--disable-dev-shm-usage']  # Minimal safe options
    
    def get_timeouts(self) -> Dict[str, int]:
        """
        Get timeout configurations.
        
        Returns:
            Dictionary with timeout values in seconds
        """
        try:
            timeouts = self._config.get('timeouts', {})
            return {
                'page_load': timeouts.get('page_load', 30),
                'script': timeouts.get('script', 10),
                'implicit_wait': timeouts.get('implicit_wait', 5),
                'element_wait': timeouts.get('element_wait', 15)
            }
        except Exception as e:
            logging.error(f"Error getting timeouts: {e}")
            return {'page_load': 30, 'script': 10, 'implicit_wait': 5, 'element_wait': 15}
    
    def get_debug_port(self) -> int:
        """
        Get Chrome debug port (default: 9222).
        
        Returns:
            Debug port number
        """
        try:
            return self._config.get('chrome', {}).get('debug_port', 9222)
        except Exception as e:
            logging.error(f"Error getting debug port: {e}")
            return 9222
    
    def get_debug_host(self) -> str:
        """
        Get Chrome debug host (default: localhost).
        
        Returns:
            Debug host address
        """
        try:
            return self._config.get('chrome', {}).get('debug_host', 'localhost')
        except Exception as e:
            logging.error(f"Error getting debug host: {e}")
            return 'localhost'
    
    def get_connection_config(self) -> Dict[str, Any]:
        """
        Get connection configuration.
        
        Returns:
            Dictionary with connection settings
        """
        try:
            connection = self._config.get('connection', {})
            return {
                'max_connection_attempts': connection.get('max_connection_attempts', 3),
                'connection_timeout': connection.get('connection_timeout', 10),
                'fallback_strategy': connection.get('fallback_strategy', 'fail_gracefully'),
                'preserve_session': connection.get('preserve_session', True)
            }
        except Exception as e:
            logging.error(f"Error getting connection config: {e}")
            return {
                'max_connection_attempts': 3,
                'connection_timeout': 10,
                'fallback_strategy': 'fail_gracefully',
                'preserve_session': True
            }
    
    def get_wait_conditions(self) -> Dict[str, Any]:
        """
        Get wait condition configurations.
        
        Returns:
            Dictionary with wait condition settings
        """
        try:
            wait_conditions = self._config.get('wait_conditions', {})
            return {
                'default_selector': wait_conditions.get('default_selector', 'body'),
                'js_complete': wait_conditions.get('js_complete', "return document.readyState === 'complete'"),
                'images_loaded': wait_conditions.get('images_loaded', "return Array.from(document.images).every(img => img.complete)")
            }
        except Exception as e:
            logging.error(f"Error getting wait conditions: {e}")
            return {
                'default_selector': 'body',
                'js_complete': "return document.readyState === 'complete'",
                'images_loaded': "return Array.from(document.images).every(img => img.complete)"
            }
    
    def get_retry_config(self) -> Dict[str, int]:
        """
        Get retry configuration.
        
        Returns:
            Dictionary with retry settings
        """
        try:
            retry = self._config.get('retry', {})
            return {
                'max_attempts': retry.get('max_attempts', 2),
                'backoff_factor': retry.get('backoff_factor', 1.5)
            }
        except Exception as e:
            logging.error(f"Error getting retry config: {e}")
            return {'max_attempts': 2, 'backoff_factor': 1.5}
    
    def get_js_detection_config(self) -> Dict[str, Any]:
        """
        Get JavaScript detection configuration.
        
        Returns:
            Dictionary with JS detection settings
        """
        try:
            js_detection = self._config.get('js_detection', {})
            return {
                'enabled': js_detection.get('enabled', True),
                'indicators': js_detection.get('indicators', ['React', 'Vue', 'Angular', 'document.getElementById', 'window.onload']),
                'content_threshold': js_detection.get('content_threshold', 100)
            }
        except Exception as e:
            logging.error(f"Error getting JS detection config: {e}")
            return {
                'enabled': True,
                'indicators': ['React', 'Vue', 'Angular', 'document.getElementById', 'window.onload'],
                'content_threshold': 100
            }
    
    @staticmethod
    def load_default_config() -> Dict[str, Any]:
        """
        Load default configuration when YAML file is not available.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'chrome': {
                'debug_port': 9222,
                'debug_host': 'localhost',
                'user_data_dir': '~/.chrome-wf'
            },
            'connection': {
                'max_connection_attempts': 3,
                'connection_timeout': 10,
                'fallback_strategy': 'fail_gracefully',
                'preserve_session': True
            },
            'options': {
                'headless': False,
                'use_existing_session': True,
                'no_new_instance': True
            },
            'timeouts': {
                'page_load': 30,
                'script': 10,
                'implicit_wait': 5,
                'element_wait': 15
            },
            'wait_conditions': {
                'default_selector': 'body',
                'js_complete': "return document.readyState === 'complete'",
                'images_loaded': "return Array.from(document.images).every(img => img.complete)"
            },
            'retry': {
                'max_attempts': 2,
                'backoff_factor': 1.5
            },
            'js_detection': {
                'enabled': True,
                'indicators': ['React', 'Vue', 'Angular', 'document.getElementById', 'window.onload'],
                'content_threshold': 100
            }
        }
    
    def get_debugger_address(self) -> str:
        """
        Get the complete debugger address for Chrome connection.
        
        Returns:
            Debugger address string (e.g., "localhost:9222")
        """
        try:
            host = self.get_debug_host()
            port = self.get_debug_port()
            return f"{host}:{port}"
        except Exception as e:
            logging.error(f"Error getting debugger address: {e}")
            return "localhost:9222"
    
    def is_session_preservation_enabled(self) -> bool:
        """
        Check if session preservation is enabled.
        
        Returns:
            True if session preservation is enabled
        """
        try:
            return self._config.get('connection', {}).get('preserve_session', True)
        except Exception as e:
            logging.error(f"Error checking session preservation: {e}")
            return True
    
    def validate_config(self) -> bool:
        """
        Validate the loaded configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            # Check required sections
            required_sections = ['chrome', 'connection', 'timeouts']
            for section in required_sections:
                if section not in self._config:
                    logging.error(f"Missing required config section: {section}")
                    return False
            
            # Validate debug port
            debug_port = self.get_debug_port()
            if not isinstance(debug_port, int) or debug_port < 1024 or debug_port > 65535:
                logging.error(f"Invalid debug port: {debug_port}")
                return False
            
            # Validate timeouts
            timeouts = self.get_timeouts()
            for timeout_name, timeout_value in timeouts.items():
                if not isinstance(timeout_value, int) or timeout_value < 1:
                    logging.error(f"Invalid timeout {timeout_name}: {timeout_value}")
                    return False
            
            logging.info("Selenium configuration validation passed")
            return True
            
        except Exception as e:
            logging.error(f"Configuration validation failed: {e}")
            return False