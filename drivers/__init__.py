"""
ChromeDriver Version Management Module
ChromeDriver版本管理模块
"""
from .version_manager import (
    VersionDetector,
    CompatibilityResult,
    check_chrome_driver_compatibility
)

__all__ = [
    'VersionDetector',
    'CompatibilityResult',
    'check_chrome_driver_compatibility'
]
