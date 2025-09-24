"""Web Fetcher Plugin System.

This package provides a plugin-based architecture for web content fetching.
Plugins can handle different types of URLs and provide fallback mechanisms.
"""

from .base import (
    IFetcherPlugin,
    BaseFetcherPlugin,
    FetchPriority,
    FetchContext,
    FetchResult
)

from .registry import (
    PluginRegistry,
    get_global_registry,
    reset_global_registry
)

# Version info
__version__ = "1.0.0"

# Public API
__all__ = [
    # Base classes and interfaces
    "IFetcherPlugin",
    "BaseFetcherPlugin",
    
    # Data classes and enums
    "FetchPriority",
    "FetchContext", 
    "FetchResult",
    
    # Registry
    "PluginRegistry",
    "get_global_registry",
    "reset_global_registry",
]