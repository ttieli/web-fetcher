"""Base plugin interface and data classes for the Web Fetcher plugin system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Optional, Dict, Any, List
import time


class FetchPriority(IntEnum):
    """Priority levels for fetcher plugins. Higher values = higher priority."""
    FALLBACK = 0      # Last resort fallback
    LOW = 10          # Low priority
    MEDIUM = 50       # Medium priority
    NORMAL = 50       # Default priority  
    HIGH = 100        # High priority
    DOMAIN_OVERRIDE = 500  # Domain-specific priority override
    CRITICAL = 1000   # Critical priority - use first


@dataclass
class FetchContext:
    """Context information passed to fetcher plugins."""
    url: str
    user_agent: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    additional_headers: Optional[Dict[str, str]] = None
    cookies: Optional[Dict[str, str]] = None
    # Plugin-specific configuration
    plugin_config: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class FetchResult:
    """Result from a fetch operation."""
    success: bool
    html_content: Optional[str] = None
    error_message: Optional[str] = None
    fetch_method: str = "unknown"
    attempts: int = 0
    duration: float = 0.0
    status_code: Optional[int] = None
    final_url: Optional[str] = None
    # Additional metadata that plugins can populate
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_legacy_metrics(self):
        """Convert to legacy FetchMetrics format for backward compatibility."""
        # Import here to avoid circular dependency
        try:
            import sys
            
            # Check if webfetcher module is already loaded
            if 'webfetcher' in sys.modules:
                webfetcher_module = sys.modules['webfetcher']
                FetchMetrics = getattr(webfetcher_module, 'FetchMetrics')
            else:
                from webfetcher import FetchMetrics
            
            metrics = FetchMetrics()
            metrics.primary_method = self.fetch_method
            metrics.total_attempts = self.attempts
            metrics.fetch_duration = self.duration
            metrics.final_status = "success" if self.success else "failed"
            metrics.error_message = self.error_message
            
            # Copy additional metadata
            if 'ssl_fallback_used' in self.metadata:
                metrics.ssl_fallback_used = self.metadata['ssl_fallback_used']
            if 'fallback_method' in self.metadata:
                metrics.fallback_method = self.metadata['fallback_method']
                
            return metrics
        except (ImportError, AttributeError):
            # If webfetcher not available, create a simple object that mimics FetchMetrics
            class SimpleFetchMetrics:
                def __init__(self, fetch_method, attempts, duration, success, error_message):
                    self.primary_method = fetch_method
                    self.total_attempts = attempts
                    self.fetch_duration = duration
                    self.final_status = "success" if success else "failed"
                    self.error_message = error_message
                    self.ssl_fallback_used = False
                    self.fallback_method = None
                    
                def to_dict(self):
                    return {
                        'primary_method': self.primary_method,
                        'total_attempts': self.total_attempts,
                        'fetch_duration': self.fetch_duration,
                        'final_status': self.final_status,
                        'error_message': self.error_message,
                        'ssl_fallback_used': self.ssl_fallback_used,
                        'fallback_method': self.fallback_method
                    }
            
            return SimpleFetchMetrics(
                self.fetch_method, 
                self.attempts, 
                self.duration, 
                self.success, 
                self.error_message
            )


class IFetcherPlugin(ABC):
    """Interface that all fetcher plugins must implement."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this plugin."""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> FetchPriority:
        """Return the priority of this plugin."""
        pass
    
    @abstractmethod
    def can_handle(self, context: FetchContext) -> bool:
        """
        Determine if this plugin can handle the given fetch request.
        
        Args:
            context: The fetch context containing URL and other parameters
            
        Returns:
            True if this plugin can handle the request, False otherwise
        """
        pass
    
    @abstractmethod
    def fetch(self, context: FetchContext) -> FetchResult:
        """
        Perform the actual fetch operation.
        
        Args:
            context: The fetch context containing URL and parameters
            
        Returns:
            FetchResult containing the result of the operation
        """
        pass
    
    def is_available(self) -> bool:
        """
        Check if this plugin is available for use.
        Default implementation returns True.
        
        Returns:
            True if the plugin is available, False otherwise
        """
        return True
    
    def get_capabilities(self) -> List[str]:
        """
        Return a list of capabilities this plugin provides.
        
        Returns:
            List of capability strings
        """
        return []
    
    def validate_context(self, context: FetchContext) -> bool:
        """
        Validate that the context is suitable for this plugin.
        
        Args:
            context: The fetch context to validate
            
        Returns:
            True if context is valid, False otherwise
        """
        return context.url is not None and len(context.url.strip()) > 0


class BaseFetcherPlugin(IFetcherPlugin):
    """Base implementation of IFetcherPlugin providing common functionality."""
    
    def __init__(self, name: str, priority: FetchPriority = FetchPriority.NORMAL):
        self._name = name
        self._priority = priority
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def priority(self) -> FetchPriority:
        return self._priority
    
    def _create_result(self, success: bool, html_content: Optional[str] = None, 
                      error_message: Optional[str] = None, attempts: int = 1) -> FetchResult:
        """Helper method to create a FetchResult with common fields populated."""
        return FetchResult(
            success=success,
            html_content=html_content,
            error_message=error_message,
            fetch_method=self.name,
            attempts=attempts,
            duration=0.0
        )
    
    def _time_operation(self, operation):
        """Helper method to time an operation and return the result and duration."""
        start_time = time.time()
        try:
            result = operation()
            duration = time.time() - start_time
            return result, duration
        except Exception as e:
            duration = time.time() - start_time
            raise e