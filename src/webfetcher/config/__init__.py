"""
Configuration module for WebFetcher

Contains SSL domain configurations and routing settings.
"""

from .ssl_problematic_domains import should_use_selenium_directly

__all__ = ['should_use_selenium_directly']
