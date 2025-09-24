# Safari CCDI Integration Architecture Specification

**Author:** Archy-Principle-Architect  
**Date:** 2025-09-23  
**Version:** 1.0  
**Status:** Architecture Design  

## Executive Summary

This document defines a clean, non-intrusive integration strategy for incorporating the proven Safari direct extraction solution into the Web_Fetcher core codebase without modifying existing core files. The approach uses a plugin-based architecture that extends Web_Fetcher's existing parser selection mechanism.

## Current Architecture Analysis

### Core Web_Fetcher Pattern
The Web_Fetcher follows a clear architectural pattern:

```python
# Parser Selection Pattern (Line 5033-5090 in webfetcher.py)
if condition_detected:
    logging.info("Selected parser: ParserName")
    parser_name = "ParserName"
    date_only, md, metadata = parser_to_markdown(html, url)
    rendered = should_render_flag
```

### Existing Parser Interface Contract
All parsers implement the standard interface:
```python
def parser_to_markdown(html: str, url: str) -> tuple[str, str, dict]:
    # Returns (date_only, markdown_content, metadata_dict)
```

### Site-Specific Detection Logic
The system uses URL pattern matching for parser selection:
```python
elif 'mp.weixin.qq.com' in host:
    # WeChat parser
elif 'xiaohongshu.com' in host or 'xhslink.com' in original_host:
    # Xiaohongshu parser  
elif 'ccdi.gov.cn' in host:
    # Proposed CCDI Safari parser
```

## Integration Strategy

### 1. Plugin-Based Architecture

**Principle:** Extend without modifying core files through a clean plugin interface.

#### Plugin Structure
```
Web_Fetcher/
├── webfetcher.py (UNCHANGED)
├── wf.py (UNCHANGED)
└── plugins/
    ├── __init__.py
    ├── plugin_registry.py
    ├── base_plugin.py
    └── ccdi_safari_plugin.py
```

#### Plugin Interface Contract
```python
class BaseSitePlugin:
    """Base class for site-specific extraction plugins"""
    
    @classmethod
    def can_handle(cls, url: str, html: str) -> bool:
        """Determine if this plugin can handle the given URL/content"""
        raise NotImplementedError
    
    @classmethod
    def extract_content(cls, html: str, url: str) -> tuple[str, str, dict]:
        """Extract content following webfetcher interface"""
        raise NotImplementedError
    
    @classmethod
    def requires_special_fetch(cls, url: str) -> bool:
        """Whether this plugin needs custom fetching (Safari, etc.)"""
        return False
    
    @classmethod
    def fetch_content(cls, url: str) -> str:
        """Custom fetch method if requires_special_fetch returns True"""
        raise NotImplementedError
```

### 2. Integration Points

#### 2.1 Parser Selection Enhancement
Add plugin detection before existing parser logic:

```python
# In webfetcher.py main() function - CONCEPTUAL ONLY
# This would be implemented as a minimal patch or configuration

# Check for plugin handlers first
plugin_handler = get_plugin_for_url(url, html)
if plugin_handler:
    logging.info(f"Selected parser: {plugin_handler.name}")
    parser_name = plugin_handler.name
    if plugin_handler.requires_special_fetch(url):
        # Re-fetch using plugin's method
        html = plugin_handler.fetch_content(url)
    date_only, md, metadata = plugin_handler.extract_content(html, url)
    rendered = False  # Plugin handles its own rendering
```

#### 2.2 Registry-Based Discovery
```python
# plugins/plugin_registry.py
class PluginRegistry:
    _plugins = []
    
    @classmethod
    def register_plugin(cls, plugin_class):
        cls._plugins.append(plugin_class)
    
    @classmethod
    def get_handler_for_url(cls, url: str, html: str):
        for plugin in cls._plugins:
            if plugin.can_handle(url, html):
                return plugin
        return None
```

### 3. CCDI Safari Plugin Implementation

#### 3.1 Plugin Class Structure
```python
class CCDISafariPlugin(BaseSitePlugin):
    name = "CCDI_Safari"
    
    @classmethod
    def can_handle(cls, url: str, html: str) -> bool:
        """Detect CCDI URLs that need Safari extraction"""
        if 'ccdi.gov.cn' in url:
            # Check for CAPTCHA indicators
            captcha_indicators = ['seccaptcha', '验证码', 'security check']
            for indicator in captcha_indicators:
                if indicator.lower() in html.lower():
                    return True
            # Also handle if content is insufficient
            if len(html.strip()) < 1000:
                return True
        return False
    
    @classmethod
    def requires_special_fetch(cls, url: str) -> bool:
        return True
    
    @classmethod
    def fetch_content(cls, url: str) -> str:
        """Use Safari direct extraction"""
        from .ccdi_safari_extractor import CCDISafariExtractor
        extractor = CCDISafariExtractor()
        return extractor.extract_html_from_safari(url)
    
    @classmethod
    def extract_content(cls, html: str, url: str) -> tuple[str, str, dict]:
        """Process Safari-extracted content"""
        from .ccdi_safari_extractor import CCDISafariExtractor
        extractor = CCDISafariExtractor()
        return extractor.parse_to_webfetcher_format(html, url)
```

#### 3.2 Adapter Implementation
```python
# plugins/ccdi_safari_extractor.py
class CCDISafariExtractor:
    """Adapter for existing CCDI production extractor"""
    
    def __init__(self):
        # Initialize Safari extractor with minimal config
        pass
    
    def extract_html_from_safari(self, url: str) -> str:
        """Use Safari automation to get clean HTML"""
        # Leverage existing CCDIProductionExtractor methods
        from ..test_ccdi.ccdi_production_extractor import CCDIProductionExtractor
        
        # Create temporary instance for HTML extraction only
        temp_dir = "/tmp/safari_extraction"
        extractor = CCDIProductionExtractor(url, temp_dir)
        
        # Execute Safari extraction steps
        if extractor.check_safari_availability():
            if extractor.navigate_to_url():
                extractor.wait_for_page_load()
                return extractor.extract_html_content()
        
        raise Exception("Safari extraction failed")
    
    def parse_to_webfetcher_format(self, html: str, url: str) -> tuple[str, str, dict]:
        """Convert Safari content to webfetcher format"""
        # Reuse existing parsing logic but return webfetcher format
        from ..test_ccdi.ccdi_production_extractor import CCDIProductionExtractor
        
        temp_dir = "/tmp/safari_extraction"
        extractor = CCDIProductionExtractor(url, temp_dir)
        
        # Parse article content
        article = extractor.parse_article_content(html)
        
        # Convert to webfetcher format
        date_only = datetime.now().strftime('%Y-%m-%d')
        if article['publish_time']:
            # Parse publish time if available
            try:
                parsed_date = parse_date_like(article['publish_time'])
                if parsed_date[0]:
                    date_only = parsed_date[0]
            except:
                pass
        
        # Generate markdown in webfetcher style
        markdown_content = f"# {article['title']}\n\n{article['content']}"
        
        # Metadata following webfetcher conventions
        metadata = {
            'page_type': 'ccdi_article',
            'title': article['title'],
            'source': article['source'],
            'publish_time': article['publish_time'],
            'extraction_method': 'safari_direct',
            'safari_extraction': True
        }
        
        return (date_only, markdown_content, metadata)
```

## Non-Intrusive Integration Approach

### 1. Configuration-Based Activation

**Option A: Environment Variable**
```bash
export WF_ENABLE_PLUGINS=true
export WF_PLUGIN_PATH="/path/to/plugins"
```

**Option B: Command Line Flag**
```bash
./webfetcher.py --enable-plugins --plugin-path=./plugins https://ccdi.gov.cn/...
```

**Option C: Configuration File**
```yaml
# webfetcher.config.yaml
plugins:
  enabled: true
  path: "./plugins"
  auto_discovery: true
```

### 2. Minimal Core Modification Strategy

Instead of modifying core files, use one of these approaches:

#### 2.1 Wrapper Script Approach
```python
#!/usr/bin/env python3
# wf_enhanced.py - Enhanced wrapper that includes plugins

import sys
import os
from pathlib import Path

# Add plugin path
plugin_path = Path(__file__).parent / "plugins"
sys.path.insert(0, str(plugin_path))

# Import and initialize plugins
from plugins.plugin_registry import PluginRegistry
from plugins.ccdi_safari_plugin import CCDISafariPlugin

# Register plugins
PluginRegistry.register_plugin(CCDISafariPlugin)

# Monkey patch the main webfetcher with plugin support
from webfetcher import main as original_main

def enhanced_main():
    # Check for plugin handling before calling original
    if len(sys.argv) > 1:
        url = sys.argv[1]
        plugin = PluginRegistry.get_handler_for_url(url, "")
        if plugin and plugin.requires_special_fetch(url):
            # Handle via plugin
            return handle_with_plugin(plugin, url)
    
    # Fallback to original
    return original_main()

if __name__ == "__main__":
    enhanced_main()
```

#### 2.2 Import Hook Approach
```python
# plugins/__init__.py
import sys
import importlib.util

def patch_webfetcher():
    """Dynamically patch webfetcher to support plugins"""
    # Load webfetcher module
    spec = importlib.util.find_spec("webfetcher")
    webfetcher = importlib.util.module_from_spec(spec)
    
    # Store original main
    original_main = webfetcher.main
    
    # Create enhanced main
    def enhanced_main():
        # Plugin logic here
        return original_main()
    
    # Replace main function
    webfetcher.main = enhanced_main
    
    return webfetcher

# Auto-patch when plugins module is imported
if 'webfetcher' in sys.modules:
    patch_webfetcher()
```

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create plugin directory structure
- [ ] Implement base plugin interface
- [ ] Create plugin registry system
- [ ] Implement wrapper script approach

### Phase 2: CCDI Integration (Week 2)
- [ ] Create CCDI Safari plugin
- [ ] Adapt existing CCDIProductionExtractor
- [ ] Implement webfetcher format conversion
- [ ] Add Safari availability detection

### Phase 3: Testing & Validation (Week 3)
- [ ] Create integration test suite
- [ ] Validate CCDI extraction quality
- [ ] Performance benchmarking
- [ ] Error handling validation

### Phase 4: Documentation & Deployment (Week 4)
- [ ] Create user documentation
- [ ] Installation and setup guides
- [ ] Migration documentation
- [ ] Production deployment guide

## Quality Assurance Strategy

### 1. Backward Compatibility
- Core webfetcher functionality unchanged
- All existing parsers continue to work
- No breaking changes to command-line interface

### 2. Fallback Mechanisms
- Plugin failures fall back to original parsers
- Safari unavailability falls back to standard fetch
- Graceful degradation for all failure modes

### 3. Performance Impact
- Plugin detection adds minimal overhead
- Safari extraction only for CCDI URLs
- No impact on non-CCDI processing

### 4. Testing Strategy
- Unit tests for all plugin components
- Integration tests with real CCDI URLs
- Performance regression tests
- Cross-platform compatibility tests (macOS focus)

## Security Considerations

### 1. Safari Automation
- Uses standard AppleScript automation
- No browser extension or modification required
- Respects same-origin policy and browser security

### 2. Plugin Security
- Plugin registry prevents unauthorized plugins
- Input validation for all plugin methods
- Sandboxed execution environment

### 3. Data Handling
- No sensitive data stored permanently
- Temporary files cleaned up automatically
- Logging excludes sensitive information

## Migration Strategy

### 1. Gradual Rollout
- Deploy plugins alongside existing system
- Enable via configuration flag
- Monitor performance and reliability

### 2. User Training
- Documentation for new plugin features
- Examples of CCDI extraction usage
- Troubleshooting guides for Safari issues

### 3. Maintenance Plan
- Plugin updates independent of core system
- Version compatibility matrix
- Regular testing with CCDI website changes

## Success Metrics

### 1. Functional Success
- [ ] CCDI articles extract successfully via Safari
- [ ] Content quality matches production extractor
- [ ] Zero impact on non-CCDI functionality

### 2. Performance Success
- [ ] Plugin detection overhead < 10ms
- [ ] Safari extraction completes within 60 seconds
- [ ] System resource usage within acceptable limits

### 3. Reliability Success
- [ ] 95% success rate for CCDI extractions
- [ ] Graceful fallback for Safari failures
- [ ] No core system regressions

## Conclusion

This architecture provides a clean, maintainable approach to integrating Safari direct extraction capabilities into Web_Fetcher without modifying core files. The plugin-based design allows for future extensions while maintaining system stability and backward compatibility.

The implementation prioritizes:
1. **Non-intrusive integration** - Core files remain unchanged
2. **Progressive enhancement** - New capabilities without breaking existing functionality  
3. **Clear boundaries** - Well-defined interfaces between core and plugins
4. **Operational simplicity** - Minimal configuration and maintenance overhead
5. **Graceful degradation** - Fallback mechanisms for all failure scenarios

This approach aligns with the progressive improvement principles while delivering immediate value for CCDI content extraction requirements.