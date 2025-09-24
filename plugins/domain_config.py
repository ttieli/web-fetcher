"""Domain-specific plugin configuration for the Web Fetcher plugin system."""

import logging
from typing import Dict, Optional
from urllib.parse import urlparse

from .base import FetchPriority

logger = logging.getLogger(__name__)

# Domains that require Safari browser automation
DOMAIN_PLUGIN_OVERRIDES = {
    # Chinese government and institutional sites that often block automated requests
    'ccdi.gov.cn': {
        'preferred_plugin': 'safari_fetcher',
        'priority_boost': FetchPriority.DOMAIN_OVERRIDE,
        'reason': 'Anti-bot protection requires browser automation'
    },
    'qcc.com': {
        'preferred_plugin': 'safari_fetcher', 
        'priority_boost': FetchPriority.DOMAIN_OVERRIDE,
        'reason': 'Enterprise data site with strict bot detection'
    },
    'tianyancha.com': {
        'preferred_plugin': 'safari_fetcher',
        'priority_boost': FetchPriority.DOMAIN_OVERRIDE,
        'reason': 'Business intelligence site with anti-automation measures'
    },
    'enterprise.gxzf.gov.cn': {
        'preferred_plugin': 'safari_fetcher',
        'priority_boost': FetchPriority.DOMAIN_OVERRIDE,
        'reason': 'Government enterprise registry with bot protection'
    },
    # Additional domains that commonly require browser automation
    'linkedin.com': {
        'preferred_plugin': 'safari_fetcher',
        'priority_boost': FetchPriority.DOMAIN_OVERRIDE,
        'reason': 'Social platform with strong anti-bot protection'
    },
    'facebook.com': {
        'preferred_plugin': 'safari_fetcher',
        'priority_boost': FetchPriority.DOMAIN_OVERRIDE,
        'reason': 'Social platform requiring authentication and JS'
    }
}

# Domains that should explicitly avoid Safari (performance-sensitive)
HTTP_PREFERRED_DOMAINS = {
    'httpbin.org',
    'example.com',
    'github.com',
    'stackoverflow.com',
    'wikipedia.org',
    'google.com',
    'news.ycombinator.com'
}


def get_domain_from_url(url: str) -> Optional[str]:
    """Extract domain from URL, handling subdomains appropriately."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
    except Exception as e:
        logger.warning(f"Failed to parse domain from URL {url}: {e}")
        return None


def get_domain_priority_override(url: str, plugin_name: str) -> Optional[int]:
    """
    Calculate priority boost for a plugin based on domain-specific requirements.
    
    Args:
        url: The URL being fetched
        plugin_name: Name of the plugin requesting priority calculation
        
    Returns:
        Priority boost value if domain override applies, None otherwise
    """
    domain = get_domain_from_url(url)
    if not domain:
        return None
    
    # Check for exact domain match
    if domain in DOMAIN_PLUGIN_OVERRIDES:
        override_config = DOMAIN_PLUGIN_OVERRIDES[domain]
        if override_config['preferred_plugin'] == plugin_name:
            logger.info(f"Domain {domain} prefers {plugin_name}: {override_config['reason']}")
            return override_config['priority_boost']
    
    # Check for subdomain matches (e.g., subdomain.ccdi.gov.cn)
    for configured_domain, config in DOMAIN_PLUGIN_OVERRIDES.items():
        if domain.endswith(f".{configured_domain}") or domain == configured_domain:
            if config['preferred_plugin'] == plugin_name:
                logger.info(f"Domain {domain} matches {configured_domain}, prefers {plugin_name}: {config['reason']}")
                return config['priority_boost']
    
    # Check if domain explicitly prefers HTTP
    if domain in HTTP_PREFERRED_DOMAINS and plugin_name == 'http_fetcher':
        logger.debug(f"Domain {domain} prefers HTTP fetching for performance")
        return FetchPriority.HIGH  # Maintain high priority for HTTP on these domains
    
    return None


def should_use_safari_for_domain(url: str) -> bool:
    """
    Check if a domain typically requires Safari browser automation.
    
    Args:
        url: The URL to check
        
    Returns:
        True if Safari is recommended for this domain
    """
    domain = get_domain_from_url(url)
    if not domain:
        return False
    
    # Check exact matches
    if domain in DOMAIN_PLUGIN_OVERRIDES:
        return DOMAIN_PLUGIN_OVERRIDES[domain]['preferred_plugin'] == 'safari_fetcher'
    
    # Check subdomain matches
    for configured_domain, config in DOMAIN_PLUGIN_OVERRIDES.items():
        if domain.endswith(f".{configured_domain}") or domain == configured_domain:
            return config['preferred_plugin'] == 'safari_fetcher'
    
    return False


def get_domain_config(url: str) -> Dict:
    """
    Get complete domain configuration for a URL.
    
    Args:
        url: The URL to get configuration for
        
    Returns:
        Dictionary with domain configuration, empty if no specific config
    """
    domain = get_domain_from_url(url)
    if not domain:
        return {}
    
    # Check exact matches first
    if domain in DOMAIN_PLUGIN_OVERRIDES:
        return DOMAIN_PLUGIN_OVERRIDES[domain].copy()
    
    # Check subdomain matches
    for configured_domain, config in DOMAIN_PLUGIN_OVERRIDES.items():
        if domain.endswith(f".{configured_domain}") or domain == configured_domain:
            return config.copy()
    
    # Check HTTP preferred domains
    if domain in HTTP_PREFERRED_DOMAINS:
        return {
            'preferred_plugin': 'http_fetcher',
            'priority_boost': FetchPriority.HIGH,
            'reason': 'Performance-optimized domain'
        }
    
    return {}


def is_problematic_domain(url: str) -> bool:
    """
    Check if a domain is known to have anti-bot or access restrictions.
    
    Args:
        url: The URL to check
        
    Returns:
        True if domain is known to be problematic for automated access
    """
    return should_use_safari_for_domain(url)