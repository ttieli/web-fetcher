# Web_Fetcher Plugin Interface Specification

**Author:** Archy-Principle-Architect  
**Date:** 2025-09-23  
**Version:** 1.0  
**Type:** Technical Interface Contract  

## Overview

This document defines the formal interface contracts for the Web_Fetcher plugin system, enabling clean integration of specialized extraction methods (like Safari direct extraction) without modifying core system files.

## Core Plugin Interface

### BaseSitePlugin Abstract Class

```python
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class PluginCapabilities:
    """Defines what a plugin can do"""
    requires_special_fetch: bool = False
    supports_pagination: bool = False
    handles_javascript: bool = False
    bypasses_captcha: bool = False
    extraction_method: str = "standard"
    platform_requirements: list = None  # e.g., ["macos", "safari"]

@dataclass
class ExtractionResult:
    """Standardized extraction result"""
    success: bool
    date_only: str
    markdown_content: str
    metadata: Dict[str, Any]
    error_message: Optional[str] = None
    warnings: list = None

class BaseSitePlugin(ABC):
    """
    Abstract base class for all Web_Fetcher site-specific plugins.
    
    This interface ensures compatibility with the core webfetcher.py
    parser selection and content processing pipeline.
    """
    
    # Plugin metadata (must be defined by subclasses)
    name: str = None
    version: str = "1.0"
    author: str = None
    description: str = None
    capabilities: PluginCapabilities = None
    
    @classmethod
    @abstractmethod
    def can_handle(cls, url: str, html: str = "", **kwargs) -> bool:
        """
        Determine if this plugin can/should handle the given URL and content.
        
        Args:
            url: Target URL to process
            html: HTML content (may be empty for pre-fetch detection)
            **kwargs: Additional context (user_agent, headers, etc.)
            
        Returns:
            bool: True if this plugin should handle this URL/content
            
        Example:
            @classmethod
            def can_handle(cls, url: str, html: str = "", **kwargs) -> bool:
                if 'ccdi.gov.cn' not in url:
                    return False
                # Check for CAPTCHA indicators
                if html and any(indicator in html.lower() 
                               for indicator in ['seccaptcha', '验证码']):
                    return True
                return False
        """
        pass
    
    @classmethod
    @abstractmethod  
    def extract_content(cls, html: str, url: str, **kwargs) -> ExtractionResult:
        """
        Extract content following webfetcher interface contract.
        
        Args:
            html: HTML content to process
            url: Source URL
            **kwargs: Additional options (filter_level, download_assets, etc.)
            
        Returns:
            ExtractionResult: Standardized result object
            
        Must return data compatible with webfetcher's expected format:
        - date_only: YYYY-MM-DD format string
        - markdown_content: Clean markdown with proper formatting
        - metadata: Dict with page_type, title, and plugin-specific data
        """
        pass
    
    @classmethod
    def requires_special_fetch(cls, url: str, **kwargs) -> bool:
        """
        Whether this plugin needs custom fetching method.
        
        Args:
            url: Target URL
            **kwargs: Additional context
            
        Returns:
            bool: True if plugin provides its own fetch_content method
        """
        return cls.capabilities.requires_special_fetch if cls.capabilities else False
    
    @classmethod
    def fetch_content(cls, url: str, **kwargs) -> str:
        """
        Custom fetch method for plugins that need special retrieval.
        
        Only called if requires_special_fetch() returns True.
        
        Args:
            url: Target URL to fetch
            **kwargs: Fetch options (timeout, user_agent, headers, etc.)
            
        Returns:
            str: Raw HTML content
            
        Raises:
            NotImplementedError: If plugin doesn't support custom fetching
            PluginFetchError: If custom fetch fails
        """
        raise NotImplementedError("Plugin does not implement custom fetching")
    
    @classmethod
    def validate_environment(cls) -> Tuple[bool, str]:
        """
        Check if plugin can run in current environment.
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
            
        Example:
            @classmethod
            def validate_environment(cls) -> Tuple[bool, str]:
                if platform.system() != "Darwin":
                    return False, "Safari plugin requires macOS"
                # Check Safari availability
                try:
                    subprocess.run(['osascript', '-e', 'tell application "Safari" to get name'], 
                                 check=True, capture_output=True)
                    return True, ""
                except:
                    return False, "Safari not available or no AppleScript permissions"
        """
        return True, ""
    
    @classmethod
    def get_priority(cls, url: str, html: str = "") -> int:
        """
        Return priority for this plugin when multiple plugins can handle URL.
        
        Higher numbers = higher priority
        
        Args:
            url: Target URL
            html: HTML content
            
        Returns:
            int: Priority level (0-100, default 50)
        """
        return 50
    
    @classmethod
    def cleanup(cls) -> None:
        """
        Cleanup resources after extraction (optional).
        
        Called after extraction completes or fails.
        Used for cleaning temporary files, closing connections, etc.
        """
        pass

class PluginError(Exception):
    """Base exception for plugin errors"""
    pass

class PluginFetchError(PluginError):
    """Error during custom content fetching"""
    pass

class PluginValidationError(PluginError):
    """Error during environment validation"""
    pass

class PluginExtractionError(PluginError):
    """Error during content extraction"""
    pass
```

## Plugin Registry Interface

```python
from typing import List, Optional, Type, Dict
import importlib
import logging

class PluginRegistry:
    """
    Central registry for managing and discovering Web_Fetcher plugins.
    
    Handles plugin registration, discovery, and selection based on URL/content.
    """
    
    _plugins: List[Type[BaseSitePlugin]] = []
    _logger = logging.getLogger(__name__)
    
    @classmethod
    def register_plugin(cls, plugin_class: Type[BaseSitePlugin]) -> bool:
        """
        Register a plugin class with the registry.
        
        Args:
            plugin_class: Plugin class implementing BaseSitePlugin
            
        Returns:
            bool: True if registered successfully
            
        Raises:
            ValueError: If plugin doesn't implement required interface
        """
        # Validate plugin implements required interface
        if not issubclass(plugin_class, BaseSitePlugin):
            raise ValueError(f"Plugin {plugin_class} must inherit from BaseSitePlugin")
        
        # Check required metadata
        if not plugin_class.name:
            raise ValueError(f"Plugin {plugin_class} must define 'name' attribute")
        
        # Validate environment
        is_valid, error_msg = plugin_class.validate_environment()
        if not is_valid:
            cls._logger.warning(f"Plugin {plugin_class.name} validation failed: {error_msg}")
            return False
        
        # Check for duplicates
        existing = next((p for p in cls._plugins if p.name == plugin_class.name), None)
        if existing:
            cls._logger.warning(f"Replacing existing plugin: {plugin_class.name}")
            cls._plugins.remove(existing)
        
        cls._plugins.append(plugin_class)
        cls._logger.info(f"Registered plugin: {plugin_class.name} v{plugin_class.version}")
        return True
    
    @classmethod
    def get_handler_for_url(cls, url: str, html: str = "", **kwargs) -> Optional[Type[BaseSitePlugin]]:
        """
        Find the best plugin to handle a given URL/content.
        
        Args:
            url: Target URL
            html: HTML content (optional)
            **kwargs: Additional context
            
        Returns:
            Optional plugin class that can handle the URL, or None
        """
        candidates = []
        
        for plugin in cls._plugins:
            try:
                if plugin.can_handle(url, html, **kwargs):
                    priority = plugin.get_priority(url, html)
                    candidates.append((plugin, priority))
            except Exception as e:
                cls._logger.error(f"Error checking plugin {plugin.name}: {e}")
                continue
        
        if not candidates:
            return None
        
        # Sort by priority (highest first)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        selected = candidates[0][0]
        cls._logger.info(f"Selected plugin: {selected.name} (priority: {candidates[0][1]})")
        return selected
    
    @classmethod
    def list_plugins(cls) -> List[Dict[str, Any]]:
        """Return information about all registered plugins"""
        return [
            {
                'name': plugin.name,
                'version': plugin.version,
                'author': plugin.author,
                'description': plugin.description,
                'capabilities': plugin.capabilities.__dict__ if plugin.capabilities else {},
                'valid': plugin.validate_environment()[0]
            }
            for plugin in cls._plugins
        ]
    
    @classmethod
    def discover_plugins(cls, plugin_dir: str) -> int:
        """
        Auto-discover and register plugins from directory.
        
        Args:
            plugin_dir: Directory to search for plugin files
            
        Returns:
            int: Number of plugins successfully registered
        """
        import os
        from pathlib import Path
        
        registered_count = 0
        plugin_path = Path(plugin_dir)
        
        if not plugin_path.exists():
            cls._logger.warning(f"Plugin directory not found: {plugin_dir}")
            return 0
        
        # Look for Python files ending with _plugin.py
        for plugin_file in plugin_path.glob("*_plugin.py"):
            try:
                # Import module
                module_name = plugin_file.stem
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for plugin classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BaseSitePlugin) and 
                        attr != BaseSitePlugin):
                        
                        if cls.register_plugin(attr):
                            registered_count += 1
                        
            except Exception as e:
                cls._logger.error(f"Failed to load plugin from {plugin_file}: {e}")
                continue
        
        cls._logger.info(f"Auto-discovered {registered_count} plugins from {plugin_dir}")
        return registered_count
```

## CCDI Safari Plugin Implementation Contract

```python
from .base_plugin import BaseSitePlugin, PluginCapabilities, ExtractionResult
import platform
import subprocess
from datetime import datetime

class CCDISafariPlugin(BaseSitePlugin):
    """
    Safari-based CCDI content extractor plugin.
    
    Uses Safari automation via AppleScript to bypass CAPTCHA restrictions
    on Chinese government websites.
    """
    
    name = "CCDI_Safari"
    version = "1.0.0"
    author = "Archy-Principle-Architect"
    description = "Safari direct extraction for CCDI government content"
    capabilities = PluginCapabilities(
        requires_special_fetch=True,
        supports_pagination=False,
        handles_javascript=True,
        bypasses_captcha=True,
        extraction_method="safari_applescript",
        platform_requirements=["macos", "safari"]
    )
    
    @classmethod
    def can_handle(cls, url: str, html: str = "", **kwargs) -> bool:
        """
        Detect CCDI URLs requiring Safari extraction.
        
        Handles:
        1. Direct CCDI URLs
        2. Content with CAPTCHA indicators
        3. Insufficient content from standard fetch
        """
        # Must be CCDI domain
        if 'ccdi.gov.cn' not in url:
            return False
        
        # If HTML provided, check for problems
        if html:
            # Check for CAPTCHA indicators
            captcha_indicators = [
                'seccaptcha', 'captcha', '验证码', 
                '滑动验证', 'security check', 'verification'
            ]
            
            if any(indicator.lower() in html.lower() for indicator in captcha_indicators):
                return True
            
            # Check for insufficient content
            if len(html.strip()) < 1000:
                return True
            
            # Check for blocked content patterns
            blocked_patterns = ['access denied', '拒绝访问', 'forbidden', '403']
            if any(pattern in html.lower() for pattern in blocked_patterns):
                return True
        
        # Default to Safari for all CCDI URLs as primary method
        return True
    
    @classmethod
    def validate_environment(cls) -> Tuple[bool, str]:
        """Validate Safari and AppleScript availability"""
        # Check platform
        if platform.system() != "Darwin":
            return False, "Safari plugin requires macOS"
        
        try:
            # Test AppleScript permissions
            result = subprocess.run([
                'osascript', '-e', 'tell application "Safari" to get name'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return False, "Safari AppleScript permissions not granted"
            
            return True, ""
            
        except Exception as e:
            return False, f"Safari validation failed: {e}"
    
    @classmethod
    def get_priority(cls, url: str, html: str = "") -> int:
        """High priority for CCDI URLs with problems"""
        if 'ccdi.gov.cn' not in url:
            return 0
        
        base_priority = 80  # High priority for CCDI
        
        if html:
            # Higher priority if problems detected
            problems = [
                'seccaptcha' in html.lower(),
                'captcha' in html.lower(),
                '验证码' in html.lower(),
                len(html.strip()) < 1000,
                'access denied' in html.lower()
            ]
            
            if any(problems):
                return 95  # Very high priority
        
        return base_priority
    
    @classmethod
    def fetch_content(cls, url: str, **kwargs) -> str:
        """
        Use Safari automation to fetch content.
        
        Implements the complete Safari extraction workflow:
        1. Check Safari availability
        2. Navigate to URL
        3. Wait for page load
        4. Extract HTML content
        """
        from .ccdi_safari_extractor import CCDISafariExtractor
        
        try:
            # Create extractor instance
            extractor = CCDISafariExtractor(url)
            
            # Execute Safari workflow
            if not extractor.check_safari_availability():
                raise PluginFetchError("Safari not available")
            
            if not extractor.navigate_to_url():
                raise PluginFetchError("Failed to navigate to URL")
            
            if not extractor.wait_for_page_load():
                logging.warning("Page load timeout - proceeding anyway")
            
            # Extract HTML
            html_content = extractor.extract_html_content()
            if not html_content:
                raise PluginFetchError("Failed to extract HTML content")
            
            return html_content
            
        except Exception as e:
            raise PluginFetchError(f"Safari fetch failed: {e}")
    
    @classmethod
    def extract_content(cls, html: str, url: str, **kwargs) -> ExtractionResult:
        """
        Extract and format content for webfetcher compatibility.
        """
        from .ccdi_safari_extractor import CCDISafariExtractor
        
        try:
            # Create extractor for parsing
            extractor = CCDISafariExtractor(url)
            
            # Validate content quality
            validation = extractor.validate_content_quality(html)
            if not validation['is_valid']:
                error_msg = "Content validation failed"
                if validation['has_captcha']:
                    error_msg += " - CAPTCHA detected"
                if not validation['has_content']:
                    error_msg += " - No substantial content found"
                
                return ExtractionResult(
                    success=False,
                    date_only="",
                    markdown_content="",
                    metadata={},
                    error_message=error_msg
                )
            
            # Parse article content
            article = extractor.parse_article_content(html)
            
            if not article['title'] or not article['content']:
                return ExtractionResult(
                    success=False,
                    date_only="",
                    markdown_content="",
                    metadata={},
                    error_message="Failed to parse article content"
                )
            
            # Convert to webfetcher format
            date_only = datetime.now().strftime('%Y-%m-%d')
            if article['publish_time']:
                try:
                    # Parse date if available
                    parsed_date = cls._parse_date_like(article['publish_time'])
                    if parsed_date:
                        date_only = parsed_date
                except:
                    pass
            
            # Generate webfetcher-compatible markdown
            markdown_content = cls._format_markdown(article, url)
            
            # Create metadata following webfetcher conventions
            metadata = {
                'page_type': 'ccdi_article',
                'title': article['title'],
                'source': article['source'],
                'publish_time': article['publish_time'],
                'extraction_method': 'safari_direct',
                'safari_extraction': True,
                'plugin_name': cls.name,
                'plugin_version': cls.version,
                'content_length': len(article['content']),
                'validation_passed': True
            }
            
            return ExtractionResult(
                success=True,
                date_only=date_only,
                markdown_content=markdown_content,
                metadata=metadata
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                date_only="",
                markdown_content="",
                metadata={},
                error_message=f"Extraction failed: {e}"
            )
    
    @classmethod
    def _format_markdown(cls, article: Dict[str, str], url: str) -> str:
        """Format article data as webfetcher-compatible markdown"""
        return f"""# {article['title']}

**来源:** {article['source']}
**发布时间:** {article['publish_time']}
**原文链接:** {url}

---

{article['content']}

---

*通过Safari直接提取获得*"""
    
    @classmethod
    def _parse_date_like(cls, date_str: str) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format"""
        # Implement date parsing logic
        # This is a simplified version - full implementation would handle various formats
        import re
        
        # Look for YYYY-MM-DD pattern
        match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Look for Chinese date pattern
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return None
    
    @classmethod
    def cleanup(cls) -> None:
        """Cleanup Safari automation resources"""
        # Close Safari tabs if needed
        # Clean temporary files
        pass
```

## Integration Interface Contract

```python
class WebFetcherPluginManager:
    """
    Manager class for integrating plugins with core webfetcher.
    
    Provides clean interface between plugin system and webfetcher main().
    """
    
    def __init__(self, plugin_dir: str = None):
        self.registry = PluginRegistry()
        if plugin_dir:
            self.registry.discover_plugins(plugin_dir)
    
    def process_url(self, url: str, args: Any) -> Tuple[bool, str, str, Dict]:
        """
        Process URL using appropriate plugin or return None for standard processing.
        
        Args:
            url: Target URL
            args: Parsed command line arguments
            
        Returns:
            Tuple[plugin_handled, date_only, markdown_content, metadata]
            If plugin_handled is False, use standard webfetcher processing
        """
        try:
            # Try standard fetch first to get HTML for analysis
            html = ""
            try:
                html, _ = fetch_html_with_retry(url, None, args.timeout)
            except:
                pass  # HTML not available for analysis
            
            # Find appropriate plugin
            plugin = self.registry.get_handler_for_url(url, html)
            if not plugin:
                return False, "", "", {}
            
            # Handle with plugin
            if plugin.requires_special_fetch(url):
                # Plugin provides its own fetch
                html = plugin.fetch_content(url, timeout=args.timeout)
            
            # Extract content
            result = plugin.extract_content(html, url)
            
            if result.success:
                return True, result.date_only, result.markdown_content, result.metadata
            else:
                logging.warning(f"Plugin {plugin.name} failed: {result.error_message}")
                return False, "", "", {}
                
        except Exception as e:
            logging.error(f"Plugin processing failed: {e}")
            return False, "", "", {}
        
        finally:
            # Cleanup
            if plugin:
                plugin.cleanup()
```

## Usage Integration Pattern

```python
# In webfetcher.py main() function (conceptual integration point)

def main():
    # ... existing argument parsing ...
    
    # Initialize plugin manager if enabled
    plugin_manager = None
    if (os.environ.get('WF_ENABLE_PLUGINS') == 'true' or 
        args.enable_plugins):
        
        plugin_dir = (args.plugin_path or 
                     os.environ.get('WF_PLUGIN_PATH') or 
                     './plugins')
        
        try:
            plugin_manager = WebFetcherPluginManager(plugin_dir)
            logging.info(f"Loaded {len(plugin_manager.registry.list_plugins())} plugins")
        except Exception as e:
            logging.warning(f"Plugin initialization failed: {e}")
    
    # ... existing URL processing ...
    
    # Try plugin processing first
    if plugin_manager:
        plugin_handled, date_only, md, metadata = plugin_manager.process_url(url, args)
        if plugin_handled:
            parser_name = metadata.get('plugin_name', 'Plugin')
            logging.info(f"Selected parser: {parser_name}")
            # Skip to output generation
            # ... existing output code ...
            return
    
    # Fallback to existing parser selection logic
    # ... existing parser selection code unchanged ...
```

## Compliance with Web_Fetcher Patterns

### 1. Return Format Compatibility
All plugins must return data in the exact format expected by webfetcher:
- `date_only`: String in YYYY-MM-DD format
- `markdown_content`: Clean markdown text  
- `metadata`: Dictionary with webfetcher-standard keys

### 2. Logging Integration
Plugins use the same logging patterns as core webfetcher:
```python
logging.info("Selected parser: Plugin_Name")
logging.warning("Plugin warning message")
logging.error("Plugin error message")
```

### 3. Error Handling
Plugins follow webfetcher error handling patterns:
- Graceful degradation to standard processing
- Clear error messages in logs
- No crashes on plugin failures

### 4. Metadata Standards
Plugin metadata follows webfetcher conventions:
```python
metadata = {
    'page_type': 'plugin_specific_type',
    'title': article_title,
    'plugin_name': plugin_name,
    'extraction_method': method_description
}
```

This interface specification ensures clean, maintainable integration while preserving all existing webfetcher functionality and patterns.