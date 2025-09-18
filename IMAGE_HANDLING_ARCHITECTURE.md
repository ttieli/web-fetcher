# Image Handling Architecture Specification

## Executive Summary

This document specifies the architectural solution for preventing automatic image downloads in the Web_Fetcher tool while preserving image URLs in the output. The solution follows the principles of progressive enhancement, pragmatic design, and minimal resource consumption.

## Current State Analysis

### 1. Existing Image Handling Flow

The current implementation has the following characteristics:

1. **Image URL Collection**: All parsers (generic, weixin, xiaohongshu, dianping, raw) collect image URLs during HTML parsing:
   - Images are stored in `parser.images` list
   - URLs are normalized and resolved to absolute paths
   - Images are embedded in markdown as `![](url)` format

2. **Automatic Download Behavior**:
   - Triggered by `--download-assets` flag OR automatically for specific domains:
     - `mp.weixin.qq.com` (WeChat articles)
     - `xiaohongshu.com` (XiaoHongShu posts)
   - Downloads all images to `assets/<filename>/` directory
   - Rewrites markdown links to local paths

3. **Resource Consumption Issues**:
   - No bandwidth throttling or limits
   - Downloads all images regardless of size or relevance
   - No option to skip downloads for bandwidth-constrained environments
   - Automatic downloads for certain domains cannot be disabled

### 2. Architecture Components

```
User Input → URL Parser → Content Fetcher → HTML Parser → Markdown Generator → Asset Downloader → File Writer
                                                    ↓
                                            Image URL Collection
```

## Proposed Architecture

### 1. Design Principles

Following the core architectural principles:

1. **Progressive Over Big Bang**: Introduce changes in backward-compatible phases
2. **Pragmatic Over Dogmatic**: Balance user needs with resource constraints
3. **Clear Intent Over Clever Code**: Make image handling behavior explicit and predictable
4. **Choose Boring but Clear Solutions**: Use simple flags and clear defaults

### 2. Phased Implementation Roadmap

#### Phase 1: Default Behavior Change (Minimal Impact)
- **Goal**: Stop automatic image downloads by default
- **Scope**: Change default behavior, maintain all existing functionality
- **Rollback**: Single flag to restore old behavior

#### Phase 2: Enhanced Control (Progressive Enhancement)
- **Goal**: Provide granular control over image handling
- **Scope**: Add configuration options for different image handling strategies
- **Rollback**: Maintain Phase 1 defaults

#### Phase 3: Smart Resource Management (Future)
- **Goal**: Intelligent image handling based on context
- **Scope**: Size limits, format filtering, thumbnail generation
- **Rollback**: Disable smart features via configuration

### 3. Technical Specification

#### 3.1 Configuration Interface

```python
# Image handling modes enumeration
class ImageHandlingMode(Enum):
    PRESERVE_LINKS = "links"      # Default: Keep URLs only
    DOWNLOAD_ALL = "download"     # Download all images
    DOWNLOAD_SMART = "smart"      # Download based on rules
    SKIP = "skip"                 # Remove image references

# Command-line interface
--images <mode>                   # Image handling mode
--download-assets                 # Legacy: equals --images download
--skip-images                     # Convenience: equals --images skip
--image-size-limit <MB>          # Max size per image (Phase 3)
--image-formats <list>           # Allowed formats (Phase 3)
```

#### 3.2 Behavioral Changes

```python
# Current behavior (problematic)
do_download_assets = args.download_assets or domain in AUTO_DOWNLOAD_DOMAINS

# Phase 1: New default behavior
def should_download_images(args, domain):
    # Explicit flag always wins
    if args.download_assets:
        return True
    if args.skip_images:
        return False
    
    # Default: preserve links only
    return False

# Phase 2: Mode-based behavior
def get_image_handling_mode(args, domain):
    if args.images:
        return ImageHandlingMode(args.images)
    if args.download_assets:  # Legacy support
        return ImageHandlingMode.DOWNLOAD_ALL
    if args.skip_images:
        return ImageHandlingMode.SKIP
    
    # Default for all domains
    return ImageHandlingMode.PRESERVE_LINKS
```

#### 3.3 Compatibility Matrix

| Command | Old Behavior | New Behavior | Migration Path |
|---------|-------------|--------------|----------------|
| `wf url` | Auto-download for weixin/xhs | Preserve links only | Add `--download-assets` for old behavior |
| `wf url --download-assets` | Download all | Download all | No change |
| `wf full url` | Download all | Download all | No change (full mode implies downloads) |
| `wf raw url` | Preserve links | Preserve links | No change |
| `wf url --skip-images` | N/A | Remove image refs | New feature |

### 4. Implementation Contracts

#### 4.1 Parser Interface Contract

```python
class ParserInterface:
    """Contract for all HTML parsers"""
    
    def parse(self, html: str, url: str) -> tuple[str, str, dict]:
        """
        Parse HTML to markdown
        
        Returns:
            date_only: str - Date string
            markdown: str - Markdown content with image references
            metadata: dict - Must include 'images' key with list of URLs
        """
        pass
    
    def handle_images(self, mode: ImageHandlingMode) -> str:
        """
        Process images according to specified mode
        
        Args:
            mode: How to handle image references
            
        Returns:
            Processed markdown content
        """
        pass
```

#### 4.2 Asset Manager Contract

```python
class AssetManager:
    """Manages external resource handling"""
    
    def process_images(self, 
                       markdown: str, 
                       image_urls: list[str],
                       mode: ImageHandlingMode,
                       config: dict) -> str:
        """
        Process images in markdown according to mode
        
        Args:
            markdown: Original markdown with image references
            image_urls: List of discovered image URLs
            mode: Processing mode
            config: Additional configuration (size limits, formats, etc.)
            
        Returns:
            Processed markdown with appropriate image handling
        """
        pass
```

### 5. Test Scenarios

#### 5.1 Acceptance Criteria

```python
# Test: Default behavior preserves links
def test_default_preserves_links():
    """
    Given: URL with images, no flags
    When: Fetching content
    Then: Markdown contains image URLs, no downloads occur
    """
    pass

# Test: Explicit download flag works
def test_explicit_download_flag():
    """
    Given: URL with images, --download-assets flag
    When: Fetching content
    Then: Images are downloaded, links are rewritten
    """
    pass

# Test: Skip images removes references
def test_skip_images_flag():
    """
    Given: URL with images, --skip-images flag
    When: Fetching content
    Then: No image references in output
    """
    pass

# Test: Full mode maintains download behavior
def test_full_mode_downloads():
    """
    Given: URL with images, full mode
    When: Using wf full command
    Then: Images are downloaded (backward compatible)
    """
    pass
```

### 6. Migration Guide

#### For Users

1. **Default Usage Change**:
   - Old: `wf mp.weixin.qq.com/article` → Downloads images
   - New: `wf mp.weixin.qq.com/article` → Preserves links only
   - Migration: Add `--download-assets` for old behavior

2. **Bandwidth-Conscious Usage**:
   - New: Default behavior saves bandwidth
   - Use `--skip-images` to remove image references entirely

3. **Full Mode Unchanged**:
   - `wf full url` continues to download assets

#### For Scripts/Automation

```bash
# Update scripts to be explicit about image handling
# Old
wf "$URL" "$OUTPUT_DIR"

# New (if downloads needed)
wf "$URL" "$OUTPUT_DIR" --download-assets

# New (explicit link preservation)
wf "$URL" "$OUTPUT_DIR" --images links
```

## Decision Records

### ADR-001: Default to Link Preservation

**Context**: Users report excessive bandwidth usage and storage consumption from automatic image downloads.

**Decision**: Change default behavior to preserve image links without downloading.

**Alternatives Considered**:
1. Keep current behavior, add --skip-downloads flag
2. Make behavior configurable via config file
3. Prompt user for each domain

**Rationale**: 
- Minimal resource consumption by default aligns with efficiency goals
- Explicit opt-in for downloads provides clear user intent
- Preserving links maintains content completeness without resource cost

**Trade-offs**:
- (+) Reduces bandwidth and storage usage
- (+) Faster execution for most use cases
- (+) Clear, predictable behavior
- (-) Breaking change for some workflows
- (-) Requires migration for existing scripts

### ADR-002: Maintain Full Mode Behavior

**Context**: The `wf full` command implies complete content capture.

**Decision**: Keep `--download-assets` as default for full mode only.

**Rationale**: 
- Mode name implies comprehensive capture
- Maintains semantic meaning of "full"
- Provides clear differentiation between modes

### ADR-003: Remove Domain-Specific Auto-Downloads

**Context**: Hardcoded domain list for automatic downloads violates principle of predictable behavior.

**Decision**: Remove automatic downloads for specific domains.

**Rationale**:
- Consistent behavior across all domains
- User intent should be explicit
- Reduces surprise and confusion

## Performance Metrics

### Success Metrics

1. **Resource Consumption**:
   - Bandwidth usage reduction: Target 70-90% for typical usage
   - Storage usage reduction: Target 60-80% for typical usage
   - Execution time improvement: 30-50% faster without downloads

2. **User Experience**:
   - Clear documentation of behavior change
   - Zero regression in content quality (links preserved)
   - Smooth migration path for existing users

### Monitoring Checkpoints

- Week 1: Monitor for user feedback on behavior change
- Week 2: Analyze bandwidth usage patterns
- Month 1: Review adoption of new flags
- Month 2: Consider Phase 2 implementation based on feedback

## Security Considerations

1. **URL Validation**: Continue to validate and normalize image URLs
2. **Path Traversal**: Maintain protections when downloading
3. **Resource Limits**: Consider implementing download size limits in Phase 3
4. **Content Type Validation**: Verify image content types when downloading

## Operational Guidelines

### Deployment Strategy

1. **Phase 1 Deployment**:
   - Update documentation first
   - Add deprecation notice for auto-download behavior
   - Deploy with clear changelog
   - Monitor for issues

2. **Rollback Plan**:
   - Environment variable to restore old behavior: `WF_LEGACY_IMAGE_MODE=1`
   - Flag to restore old behavior: `--legacy-image-handling`
   - Document rollback procedure

### Support Documentation

1. Update README with new default behavior
2. Add migration guide for existing users
3. Create FAQ for common scenarios
4. Update command help text

## Conclusion

This architecture provides a pragmatic solution to the image handling requirement that:

1. **Reduces resource consumption** by default
2. **Maintains backward compatibility** through flags
3. **Provides clear migration path** for existing users
4. **Follows progressive enhancement** principle
5. **Enables future improvements** without breaking changes

The solution prioritizes efficiency and predictability while maintaining the tool's flexibility and power for users who need comprehensive content capture.