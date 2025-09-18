# XiaoHongShu Enhancement Code Architecture

## Function Signatures and Interfaces

### Core Enhancement Classes

```python
from dataclasses import dataclass
from typing import List, Dict, Optional, Set, Any
import json
import re
import logging
from urllib.parse import urlparse, urljoin

@dataclass
class XHSImageData:
    """Structured representation of XiaoHongShu image data"""
    url: str
    pic_id: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    is_cover: bool = False
    processing_params: Optional[Dict[str, str]] = None
    source: str = "unknown"  # Track extraction source for debugging

class XHSImageExtractor:
    """
    Enhanced XiaoHongShu image extraction engine.
    
    Replaces the simple regex-based approach in the current xhs_to_markdown()
    function with comprehensive JSON/JavaScript data mining and lazy loading detection.
    """
    
    def __init__(self, html: str, url: str = ""):
        """
        Initialize extractor with HTML content and optional source URL.
        
        Args:
            html: Raw HTML content from XiaoHongShu page
            url: Source URL for context and validation
        """
        self.html = html
        self.url = url
        self.images: List[XHSImageData] = []
        self.seen_urls: Set[str] = set()
        self._compiled_patterns = self._compile_patterns()
    
    def extract_all(self) -> List[str]:
        """
        Main extraction orchestrator - executes all extraction strategies.
        
        Returns:
            List[str]: Ordered list of unique, validated image URLs
        """
        extraction_strategies = [
            self._extract_from_initial_state,
            self._extract_from_api_responses,
            self._extract_from_lazy_loading,
            self._extract_from_html_attributes,
            self._extract_from_json_ld  # Existing JSON-LD extraction
        ]
        
        for strategy in extraction_strategies:
            try:
                strategy()
            except Exception as e:
                logging.warning(f"XHS extraction strategy {strategy.__name__} failed: {e}")
                continue
        
        return self._dedupe_and_order()
    
    def _extract_from_initial_state(self) -> None:
        """
        Extract images from window.__INITIAL_STATE__ and similar XHS globals.
        
        This is the PRIMARY strategy as XHS heavily relies on client-side state.
        Targets patterns like:
        - window.__INITIAL_STATE__ = {...}
        - window.initialState = {...}
        - __NUXT__ = {...}
        """
        state_patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
            r'window\.initialState\s*=\s*({.+?});',  
            r'__NUXT__\s*=\s*({.+?});',
            r'window\.__store\s*=\s*({.+?});'
        ]
        
        for pattern in state_patterns:
            matches = re.finditer(pattern, self.html, re.DOTALL)
            for match in matches:
                try:
                    state_json = match.group(1)
                    # Clean up common JavaScript to JSON issues
                    state_json = self._clean_javascript_json(state_json)
                    data = json.loads(state_json)
                    self._parse_state_object(data, source="initial_state")
                except json.JSONDecodeError as e:
                    logging.debug(f"Failed to parse state JSON: {e}")
                    continue
                except Exception as e:
                    logging.debug(f"Error processing state object: {e}")
                    continue
    
    def _parse_state_object(self, data: Any, source: str = "state", path: str = "") -> None:
        """
        Recursively parse XHS state objects to find image data structures.
        
        Args:
            data: JSON object/array to parse
            source: Source identifier for debugging
            path: Current path in the object tree
        """
        if isinstance(data, dict):
            # Check for XHS-specific image structures
            if 'imageList' in data:
                self._process_image_list(data['imageList'], source=f"{source}.imageList")
            
            if 'pics' in data:
                self._process_pics_array(data['pics'], source=f"{source}.pics")
            
            if 'noteDetailMap' in data:
                # XHS note detail structure
                note_map = data['noteDetailMap']
                for note_id, note_data in note_map.items():
                    if isinstance(note_data, dict):
                        self._parse_state_object(note_data, source=f"{source}.noteDetailMap.{note_id}")
            
            # Recursively search other dict keys
            for key, value in data.items():
                if key in ['imageList', 'pics', 'noteDetailMap']:
                    continue  # Already processed
                self._parse_state_object(value, source, f"{path}.{key}")
        
        elif isinstance(data, list):
            # Process array elements
            for i, item in enumerate(data):
                self._parse_state_object(item, source, f"{path}[{i}]")
    
    def _process_image_list(self, image_list: Any, source: str = "imageList") -> None:
        """Process XHS imageList array structure"""
        if not isinstance(image_list, list):
            return
        
        for i, img_data in enumerate(image_list):
            if isinstance(img_data, dict):
                url = img_data.get('url') or img_data.get('pic')
                pic_id = img_data.get('picId') or img_data.get('id')
                
                if url and self._is_valid_xhs_image_url(url):
                    self._add_image(XHSImageData(
                        url=url,
                        pic_id=pic_id,
                        width=img_data.get('width'),
                        height=img_data.get('height'),
                        is_cover=(i == 0),  # First image often cover
                        source=source
                    ))
            elif isinstance(img_data, str):
                # Sometimes imageList contains direct URL strings
                if self._is_valid_xhs_image_url(img_data):
                    self._add_image(XHSImageData(
                        url=img_data,
                        is_cover=(i == 0),
                        source=source
                    ))
    
    def _process_pics_array(self, pics: Any, source: str = "pics") -> None:
        """Process XHS pics array structure"""
        if not isinstance(pics, list):
            return
        
        for pic_data in pics:
            if isinstance(pic_data, dict):
                # Multiple URL formats in XHS pics structure
                url_candidates = [
                    pic_data.get('url'),
                    pic_data.get('original'),
                    pic_data.get('large'),
                    pic_data.get('medium'),
                    pic_data.get('small')
                ]
                
                for url in url_candidates:
                    if url and self._is_valid_xhs_image_url(url):
                        self._add_image(XHSImageData(
                            url=url,
                            pic_id=pic_data.get('picId'),
                            width=pic_data.get('width'),
                            height=pic_data.get('height'),
                            source=source
                        ))
                        break  # Use first valid URL found
    
    def _extract_from_api_responses(self) -> None:
        """
        Extract images from embedded API response data in script tags.
        
        XHS often embeds API responses directly in the HTML for faster loading.
        """
        api_patterns = [
            r'"note"\s*:\s*({[^{}]*"imageList"[^{}]*})',
            r'"data"\s*:\s*({[^{}]*"pics"[^{}]*})',
            r'{"code"\s*:\s*0[^{}]*"imageList"\s*:\s*(\[[^\]]*\])',
        ]
        
        for pattern in api_patterns:
            matches = re.finditer(pattern, self.html, re.DOTALL)
            for match in matches:
                try:
                    json_data = match.group(1)
                    data = json.loads(json_data)
                    self._parse_state_object(data, source="api_response")
                except json.JSONDecodeError:
                    continue
    
    def _extract_from_lazy_loading(self) -> None:
        """
        Extract images from lazy loading configurations.
        
        Detects various lazy loading patterns used by XHS:
        - data-src attributes
        - data-original attributes  
        - JavaScript lazy loading configurations
        - Intersection Observer setups
        """
        lazy_patterns = [
            r'data-src=["\']([^"\']*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"\']*)["\']',
            r'data-original=["\']([^"\']*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"\']*)["\']',
            r'data-lazy-src=["\']([^"\']*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"\']*)["\']',
            r'"lazyLoad"\s*:\s*true[^}]*"src"\s*:\s*"([^"]*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"]*)"',
        ]
        
        for pattern in lazy_patterns:
            matches = re.finditer(pattern, self.html, re.IGNORECASE)
            for match in matches:
                url = match.group(1).strip()
                if self._is_valid_xhs_image_url(url):
                    self._add_image(XHSImageData(
                        url=url,
                        source="lazy_loading"
                    ))
    
    def _extract_from_html_attributes(self) -> None:
        """
        Enhanced HTML attribute scanning with XHS-specific patterns.
        
        This is the fallback strategy, enhanced from the current implementation.
        """
        attribute_patterns = [
            r'src=["\']([^"\']*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"\']*)["\']',
            r'srcset=["\']([^"\']*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"\']*)["\']',
            r'background-image:\s*url\(["\']?([^"\']*(?:ci\.xiaohongshu|xhscdn|sns-img)[^"\']*)["\']?\)',
        ]
        
        for pattern in attribute_patterns:
            matches = re.finditer(pattern, self.html, re.IGNORECASE)
            for match in matches:
                url_data = match.group(1)
                
                # Handle srcset (contains multiple URLs)
                if 'srcset' in pattern:
                    urls = self._parse_srcset(url_data)
                    for url in urls:
                        if self._is_valid_xhs_image_url(url):
                            self._add_image(XHSImageData(
                                url=url,
                                source="html_srcset"
                            ))
                else:
                    if self._is_valid_xhs_image_url(url_data):
                        self._add_image(XHSImageData(
                            url=url_data,
                            source="html_attributes"
                        ))
    
    def _extract_from_json_ld(self) -> None:
        """
        Extract from JSON-LD structured data (existing implementation).
        
        Maintains compatibility with current JSON-LD extraction logic.
        """
        json_ld_pattern = r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.finditer(json_ld_pattern, self.html, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match.group(1).strip())
                self._parse_json_ld_images(data)
            except json.JSONDecodeError:
                continue
    
    def _parse_json_ld_images(self, data: Any) -> None:
        """Parse JSON-LD data for image references"""
        if isinstance(data, dict):
            # Look for image properties
            for key in ['image', 'thumbnail', 'url']:
                if key in data:
                    img_data = data[key]
                    if isinstance(img_data, str) and self._is_valid_xhs_image_url(img_data):
                        self._add_image(XHSImageData(
                            url=img_data,
                            source="json_ld"
                        ))
                    elif isinstance(img_data, list):
                        for img_url in img_data:
                            if isinstance(img_url, str) and self._is_valid_xhs_image_url(img_url):
                                self._add_image(XHSImageData(
                                    url=img_url,
                                    source="json_ld"
                                ))
        elif isinstance(data, list):
            for item in data:
                self._parse_json_ld_images(item)
    
    def _is_valid_xhs_image_url(self, url: str) -> bool:
        """
        Enhanced validation for XiaoHongShu image URLs.
        
        More comprehensive than the current consider() function.
        """
        if not url or not isinstance(url, str):
            return False
        
        url_clean = url.strip().strip('"\'')
        
        # Domain validation (expanded from current implementation)
        valid_domains = [
            'ci.xiaohongshu.com',
            'sns-img',
            'xhscdn.com',
            'sns-webpic-qc.xhscdn.com',
            'picasso-static.xiaohongshu.com',
            'sns-avatar-qc.xhscdn.com',  # Profile images
        ]
        
        domain_ok = any(domain in url_clean for domain in valid_domains)
        if not domain_ok:
            return False
        
        # Exclude avatars and icons (from current implementation)
        exclusions = ['avatar', 'favicon', 'icon', 'logo']
        if any(exclusion in url_clean.lower() for exclusion in exclusions):
            return False
        
        # Image format validation (enhanced)
        format_indicators = [
            r'\.(?:jpg|jpeg|png|webp|gif)(?:\?|$)',
            r'imageMogr2',      # XHS image processing
            r'imageView2',      # XHS image processing  
            r'thumbnail',
            r'format=',
            r'/photos/',        # XHS photo URLs
        ]
        
        format_ok = any(
            re.search(indicator, url_clean, re.IGNORECASE) 
            for indicator in format_indicators
        )
        
        return format_ok
    
    def _add_image(self, image_data: XHSImageData) -> None:
        """Add image if not already seen"""
        if image_data.url not in self.seen_urls:
            self.seen_urls.add(image_data.url)
            self.images.append(image_data)
    
    def _dedupe_and_order(self) -> List[str]:
        """
        Deduplicate and order images for final output.
        
        Returns:
            List[str]: Ordered, deduplicated image URLs
        """
        if not self.images:
            return []
        
        # Remove duplicates while preserving order
        seen = set()
        unique_images = []
        for img in self.images:
            if img.url not in seen:
                seen.add(img.url)
                unique_images.append(img)
        
        # Prioritize cover images first
        cover_images = [img for img in unique_images if img.is_cover]
        non_cover_images = [img for img in unique_images if not img.is_cover]
        
        # Order by discovery priority: initial_state > api_response > lazy_loading > html
        source_priority = {
            "initial_state": 1,
            "api_response": 2, 
            "lazy_loading": 3,
            "html_attributes": 4,
            "html_srcset": 4,
            "json_ld": 5,
            "unknown": 6
        }
        
        non_cover_images.sort(key=lambda img: (
            source_priority.get(img.source.split('.')[0], 6),
            img.source
        ))
        
        ordered_images = cover_images + non_cover_images
        return [img.url for img in ordered_images]
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Pre-compile regex patterns for performance"""
        return {
            'state_patterns': [
                re.compile(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', re.DOTALL),
                re.compile(r'window\.initialState\s*=\s*({.+?});', re.DOTALL),
                re.compile(r'__NUXT__\s*=\s*({.+?});', re.DOTALL),
            ],
            'domain_validation': re.compile(
                r'(?:ci\.xiaohongshu\.com|xhscdn\.com|sns-img|sns-webpic-qc)', 
                re.IGNORECASE
            ),
            'format_validation': re.compile(
                r'\.(?:jpg|jpeg|png|webp|gif)(?:\?|$)|imageMogr2|imageView2|format=',
                re.IGNORECASE
            )
        }
    
    def _clean_javascript_json(self, js_string: str) -> str:
        """Clean JavaScript object syntax to valid JSON"""
        # Remove JavaScript comments
        js_string = re.sub(r'//.*?$', '', js_string, flags=re.MULTILINE)
        js_string = re.sub(r'/\*.*?\*/', '', js_string, flags=re.DOTALL)
        
        # Handle undefined values
        js_string = re.sub(r'\bundefined\b', 'null', js_string)
        
        # Handle trailing commas (basic cleanup)
        js_string = re.sub(r',(\s*[}\]])', r'\1', js_string)
        
        return js_string
    
    def _parse_srcset(self, srcset: str) -> List[str]:
        """Parse srcset attribute to extract individual URLs"""
        urls = []
        parts = srcset.split(',')
        for part in parts:
            # Extract URL (first part before any space)
            url = part.strip().split(' ')[0]
            if url:
                urls.append(url)
        return urls


# Enhanced xhs_to_markdown function interface

def xhs_to_markdown_enhanced(html: str, url: str) -> tuple[str, str, dict]:
    """
    Enhanced XiaoHongShu parser with comprehensive image extraction.
    
    This function maintains the exact same interface as the current xhs_to_markdown
    but uses the enhanced XHSImageExtractor internally.
    
    Args:
        html: Raw HTML content from XiaoHongShu page
        url: Source URL for context
    
    Returns:
        tuple[str, str, dict]: (date_only, markdown_content, metadata)
            - date_only: Date string for filename
            - markdown_content: Complete markdown content
            - metadata: Dict with images, cover, author, etc.
    """
    
    # EXISTING LOGIC - Preserve all current title/author/date extraction
    # ... (existing implementation from lines 1183-1233) ...
    
    # ENHANCED IMAGE EXTRACTION - Replace lines 1233-1276
    extractor = XHSImageExtractor(html, url)
    image_urls = extractor.extract_all()
    
    # Apply existing validation logic for backward compatibility
    validated_images = []
    for img_url in image_urls:
        # Use existing consider() function logic or enhanced validation
        if _validate_image_url_legacy(img_url):
            validated_images.append(img_url)
    
    # Maintain existing cover image logic
    cover = extract_meta(html, 'og:image')
    if cover and cover not in validated_images:
        if _validate_image_url_legacy(cover):
            validated_images.insert(0, cover)
    elif cover and cover in validated_images:
        # Move cover to front if already in list
        validated_images.remove(cover)
        validated_images.insert(0, cover)
    
    # EXISTING LOGIC - Preserve all current markdown generation
    # ... (existing implementation from lines 1277-1296) ...
    
    return date_only, markdown_content, metadata


def _validate_image_url_legacy(url: str) -> bool:
    """
    Legacy validation function to maintain backward compatibility.
    
    This preserves the exact logic from the current consider() function.
    """
    if not url:
        return False
    
    url_clean = url.strip().strip('"\'')
    
    # Current domain validation logic
    ok_domain = any(x in url_clean for x in (
        'ci.xiaohongshu.com',
        'sns-img',
        'xhscdn.com',
    ))
    if not ok_domain:
        return False
    
    if any(bad in url_clean for bad in ('avatar', 'favicon')):
        return False
    
    # Current format validation logic
    if not (re.search(r'\.(?:jpg|jpeg|png|webp|gif)(?:\?|$)', url_clean, re.I) or 
            ('imageMogr2' in url_clean) or ('imageView2' in url_clean)):
        return False
    
    return True

# Integration helper functions

def get_extraction_statistics(extractor: XHSImageExtractor) -> Dict[str, Any]:
    """Get detailed statistics about the extraction process"""
    
    source_counts = {}
    for img in extractor.images:
        source = img.source.split('.')[0]  # Get base source name
        source_counts[source] = source_counts.get(source, 0) + 1
    
    return {
        'total_images_found': len(extractor.images),
        'unique_images': len(set(img.url for img in extractor.images)),
        'sources': source_counts,
        'has_cover': any(img.is_cover for img in extractor.images),
        'image_formats': [img.format for img in extractor.images if img.format]
    }

def debug_extraction_process(html: str, url: str = "") -> Dict[str, Any]:
    """
    Debug helper to understand extraction process step by step.
    
    Useful for troubleshooting and validating enhancements.
    """
    
    extractor = XHSImageExtractor(html, url)
    
    # Run each strategy individually
    strategies = [
        ('initial_state', extractor._extract_from_initial_state),
        ('api_responses', extractor._extract_from_api_responses),
        ('lazy_loading', extractor._extract_from_lazy_loading),
        ('html_attributes', extractor._extract_from_html_attributes),
        ('json_ld', extractor._extract_from_json_ld)
    ]
    
    results = {}
    for strategy_name, strategy_func in strategies:
        initial_count = len(extractor.images)
        try:
            strategy_func()
            final_count = len(extractor.images)
            results[strategy_name] = {
                'success': True,
                'images_added': final_count - initial_count,
                'error': None
            }
        except Exception as e:
            results[strategy_name] = {
                'success': False, 
                'images_added': 0,
                'error': str(e)
            }
    
    return {
        'strategy_results': results,
        'final_statistics': get_extraction_statistics(extractor),
        'final_urls': extractor._dedupe_and_order()
    }
```

## Integration Points with Existing Code

### Modified `xhs_to_markdown` Function

The enhancement integrates at **line 1233** in the current `webfetcher.py` file where image collection begins. The integration strategy is:

1. **Preserve Existing Logic**: Lines 1182-1232 (title, author, date extraction) remain unchanged
2. **Replace Image Extraction**: Lines 1233-1276 are replaced with enhanced extraction
3. **Maintain Output Format**: Lines 1277-1296 (markdown generation) remain unchanged

### Code Location Mapping

```python
# CURRENT IMPLEMENTATION (webfetcher.py lines 1233-1276)
# image gallery - collect from attributes and JSON strings
imgs: list[str] = []
seen = set()
def consider(u: str):
    # ... validation logic ...

# 1) common attributes: src, data-src, srcset
for m in re.finditer(r'(?:src|data-src)=["\']([^"\']+)["\']', html, re.I):
    consider(m.group(1))
# ... more pattern matching ...

# ENHANCED IMPLEMENTATION (replacement)
# Enhanced image extraction with comprehensive JSON mining
extractor = XHSImageExtractor(html, url)
imgs = extractor.extract_all()

# Apply legacy validation for backward compatibility
validated_imgs = [url for url in imgs if _validate_image_url_legacy(url)]
```

### Data Structure Compatibility

```python
# CURRENT METADATA STRUCTURE (preserved)
metadata = {
    'author': author,
    'images': [normalize_media_url(u) for u in imgs],  # Enhanced imgs list
    'cover': normalize_media_url(cover) if cover else '',
    'description': desc,
    'publish_time': date_raw
}

# ENHANCED METADATA (optional additions)
enhanced_metadata = {
    'author': author,
    'images': [normalize_media_url(u) for u in imgs],
    'cover': normalize_media_url(cover) if cover else '',
    'description': desc,
    'publish_time': date_raw,
    
    # Optional enhancements (can be added later)
    'extraction_stats': get_extraction_statistics(extractor),
    'image_count': len(imgs),
    'sources_used': list(set(img.source for img in extractor.images))
}
```

## Error Handling and Logging Architecture

### Comprehensive Error Handling

```python
class XHSExtractionError(Exception):
    """Custom exception for XHS extraction failures"""
    pass

def xhs_to_markdown_with_fallback(html: str, url: str) -> tuple[str, str, dict]:
    """Enhanced function with comprehensive fallback strategy"""
    
    try:
        # Try enhanced extraction
        return xhs_to_markdown_enhanced(html, url)
        
    except Exception as e:
        logging.warning(f"Enhanced XHS extraction failed, falling back to legacy: {e}")
        
        try:
            # Fallback to current implementation
            return xhs_to_markdown_legacy(html, url)
            
        except Exception as fallback_error:
            logging.error(f"Both enhanced and legacy XHS extraction failed: {fallback_error}")
            
            # Final fallback - minimal extraction
            return _minimal_xhs_extraction(html, url)

def _minimal_xhs_extraction(html: str, url: str) -> tuple[str, str, dict]:
    """Minimal extraction as last resort"""
    
    title = "未命名"
    date_only = datetime.datetime.now().strftime('%Y-%m-%d')
    
    markdown = f"# {title}\n\n- 来源: {url}\n\n(提取失败)"
    metadata = {
        'author': '',
        'images': [],
        'cover': '',
        'description': '(提取失败)',
        'publish_time': ''
    }
    
    return date_only, markdown, metadata
```

### Logging Strategy

```python
import logging

# Configure extraction-specific logger
extraction_logger = logging.getLogger('xhs_extraction')

def log_extraction_results(extractor: XHSImageExtractor, final_count: int) -> None:
    """Log detailed extraction results for monitoring"""
    
    stats = get_extraction_statistics(extractor)
    
    extraction_logger.info(f"XHS extraction completed: {final_count} images found")
    extraction_logger.debug(f"Extraction sources: {stats['sources']}")
    
    if final_count == 0:
        extraction_logger.warning("No images extracted - possible site change or content issue")
    elif final_count < 3:
        extraction_logger.info(f"Low image count ({final_count}) - may need pattern updates")
```

---

**Implementation Instructions**:

1. **Add the XHSImageExtractor class** to `webfetcher.py` before the `xhs_to_markdown` function
2. **Modify the `xhs_to_markdown` function** to use enhanced extraction at line 1233
3. **Preserve existing function signature** and return structure for compatibility
4. **Add comprehensive error handling** with fallback to current implementation
5. **Include logging** for monitoring and debugging extraction performance
6. **Test integration** with existing codebase using the provided test cases

The architecture provides a clean separation between extraction logic and existing functionality, enabling progressive enhancement without breaking current behavior.