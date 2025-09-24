"""Plugin registry system for managing and discovering fetcher plugins."""

import logging
from typing import Dict, List, Optional, Type
from .base import IFetcherPlugin, FetchContext, FetchResult, FetchPriority


logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing fetcher plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, IFetcherPlugin] = {}
        self._sorted_plugins: List[IFetcherPlugin] = []
        self._plugin_discovery_enabled = True
        
    def register_plugin(self, plugin: IFetcherPlugin) -> None:
        """
        Register a plugin with the registry.
        
        Args:
            plugin: The plugin instance to register
            
        Raises:
            ValueError: If plugin name is already registered or plugin is invalid
        """
        if not isinstance(plugin, IFetcherPlugin):
            raise ValueError(f"Plugin must implement IFetcherPlugin interface")
            
        name = plugin.name
        if name in self._plugins:
            logger.warning(f"Plugin '{name}' is already registered. Replacing existing plugin.")
        
        # Check if plugin is available before registering
        if not plugin.is_available():
            logger.warning(f"Plugin '{name}' is not available and will not be registered")
            return
        
        self._plugins[name] = plugin
        self._resort_plugins()
        logger.debug(f"Registered plugin '{name}' with priority {plugin.priority}")
    
    def unregister_plugin(self, name: str) -> bool:
        """
        Unregister a plugin by name.
        
        Args:
            name: Name of the plugin to unregister
            
        Returns:
            True if plugin was found and removed, False otherwise
        """
        if name in self._plugins:
            del self._plugins[name]
            self._resort_plugins()
            logger.debug(f"Unregistered plugin '{name}'")
            return True
        return False
    
    def get_plugin(self, name: str) -> Optional[IFetcherPlugin]:
        """
        Get a plugin by name.
        
        Args:
            name: Name of the plugin to retrieve
            
        Returns:
            The plugin instance if found, None otherwise
        """
        return self._plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """
        List all registered plugin names.
        
        Returns:
            List of plugin names
        """
        return list(self._plugins.keys())
    
    def get_suitable_plugins(self, context: FetchContext) -> List[IFetcherPlugin]:
        """
        Get plugins that can handle the given context, sorted by priority.
        
        Args:
            context: The fetch context
            
        Returns:
            List of suitable plugins sorted by priority (highest first)
        """
        suitable_plugins = []
        for plugin in self._sorted_plugins:
            try:
                if plugin.can_handle(context) and plugin.validate_context(context):
                    suitable_plugins.append(plugin)
            except Exception as e:
                logger.warning(f"Error checking if plugin '{plugin.name}' can handle context: {e}")
                continue
        
        # Sort by effective priority if plugins support it, otherwise by base priority
        def get_sort_key(plugin):
            try:
                # Check if plugin has get_effective_priority method
                if hasattr(plugin, 'get_effective_priority'):
                    return plugin.get_effective_priority(context.url)
                else:
                    return plugin.priority
            except Exception as e:
                logger.warning(f"Error getting priority for plugin '{plugin.name}': {e}")
                return plugin.priority
        
        suitable_plugins.sort(key=get_sort_key, reverse=True)
        
        # Log the final plugin order for debugging
        if suitable_plugins:
            plugin_order = [(p.name, get_sort_key(p)) for p in suitable_plugins]
            logger.debug(f"Plugin priority order for {context.url}: {plugin_order}")
        
        return suitable_plugins
    
    def fetch_with_fallback(self, context: FetchContext) -> FetchResult:
        """
        Attempt to fetch content using suitable plugins in priority order.
        
        Args:
            context: The fetch context
            
        Returns:
            FetchResult from the first successful plugin, or failure result if all fail
        """
        suitable_plugins = self.get_suitable_plugins(context)
        
        if not suitable_plugins:
            return FetchResult(
                success=False,
                error_message="No suitable plugins found for this URL",
                fetch_method="none",
                attempts=0
            )
        
        last_error = "No plugins attempted"
        total_attempts = 0
        
        for plugin in suitable_plugins:
            try:
                logger.debug(f"Attempting to fetch with plugin '{plugin.name}'")
                result = plugin.fetch(context)
                total_attempts += result.attempts
                
                if result.success and result.html_content:
                    logger.debug(f"Successfully fetched with plugin '{plugin.name}'")
                    result.attempts = total_attempts
                    return result
                else:
                    last_error = result.error_message or f"Plugin '{plugin.name}' failed without specific error"
                    logger.debug(f"Plugin '{plugin.name}' failed: {last_error}")
                    
            except Exception as e:
                last_error = f"Plugin '{plugin.name}' threw exception: {str(e)}"
                logger.warning(last_error)
                total_attempts += 1
                continue
        
        return FetchResult(
            success=False,
            error_message=f"All plugins failed. Last error: {last_error}",
            fetch_method="fallback_failed",
            attempts=total_attempts
        )
    
    def _resort_plugins(self) -> None:
        """Resort plugins by priority (highest priority first)."""
        self._sorted_plugins = sorted(
            self._plugins.values(),
            key=lambda p: p.priority,
            reverse=True
        )
    
    def auto_discover_plugins(self) -> None:
        """
        Automatically discover and register available plugins.
        This tries to import and register common plugins.
        """
        if not self._plugin_discovery_enabled:
            return
        
        # Try to register HTTP plugin (should always work)
        try:
            from .http_fetcher import HTTPFetcherPlugin
            self.register_plugin(HTTPFetcherPlugin())
            logger.debug("Auto-discovered HTTP fetcher plugin")
        except ImportError as e:
            logger.debug(f"HTTP fetcher plugin not available: {e}")
        except Exception as e:
            logger.warning(f"Failed to register HTTP fetcher plugin: {e}")
        
        # Try to register Safari plugin (optional)
        try:
            from .safari.plugin import SafariFetcherPlugin
            safari_plugin = SafariFetcherPlugin()
            if safari_plugin.is_available():
                self.register_plugin(safari_plugin)
                logger.debug("Auto-discovered Safari fetcher plugin")
            else:
                logger.debug("Safari fetcher plugin not available")
        except ImportError as e:
            logger.debug(f"Safari fetcher plugin not available: {e}")
        except Exception as e:
            logger.debug(f"Failed to register Safari fetcher plugin: {e}")
    
    def disable_auto_discovery(self) -> None:
        """Disable automatic plugin discovery."""
        self._plugin_discovery_enabled = False
    
    def enable_auto_discovery(self) -> None:
        """Enable automatic plugin discovery."""
        self._plugin_discovery_enabled = True
    
    def get_plugin_info(self) -> Dict[str, Dict]:
        """
        Get information about all registered plugins.
        
        Returns:
            Dictionary mapping plugin names to their info
        """
        info = {}
        for name, plugin in self._plugins.items():
            info[name] = {
                'name': plugin.name,
                'priority': plugin.priority,
                'available': plugin.is_available(),
                'capabilities': plugin.get_capabilities()
            }
        return info


# Global plugin registry instance
_global_registry = None


def get_global_registry() -> PluginRegistry:
    """
    Get the global plugin registry instance.
    
    Returns:
        The global PluginRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = PluginRegistry()
        # Auto-discover plugins on first access
        _global_registry.auto_discover_plugins()
    return _global_registry


def reset_global_registry() -> None:
    """Reset the global registry (mainly for testing)."""
    global _global_registry
    _global_registry = None