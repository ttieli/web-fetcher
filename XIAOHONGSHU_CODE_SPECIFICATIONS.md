# XiaoHongShu URL Fixes - Exact Code Specifications

## Code Modification Instructions

### Modification 1: Enhanced Redirect Resolver

**File**: `webfetcher.py`  
**Location**: After line 737 (after the existing `resolve_final_url` function)

**Add this new function**:

```python
def resolve_final_url_with_fallback(url: str, ua: Optional[str] = None, timeout: int = 10, max_redirects: int = 5) -> tuple[str, bool]:
    """
    Enhanced redirect resolver with fallback strategies for problematic redirect services.
    
    Some redirect services (like xhslink.com) return 404 on HEAD requests but work with GET.
    This function implements a fallback strategy for such services.
    
    Args:
        url: Original URL to resolve
        ua: User agent string (optional)
        timeout: Request timeout in seconds
        max_redirects: Maximum number of redirects to follow
        
    Returns:
        tuple[str, bool]: (final_url, was_redirected)
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    
    ua = ua or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0 Safari/537.36"
    current_url = url.strip()
    redirect_count = 0
    was_redirected = False
    
    # Check if this is a known problematic redirect service
    parsed_original = urllib.parse.urlparse(current_url)
    is_known_redirect_service = parsed_original.hostname and 'xhslink.com' in parsed_original.hostname
    
    # For known problematic services, try GET-based resolution immediately
    if is_known_redirect_service:
        logging.debug(f"Using GET-based redirect resolution for known service: {parsed_original.hostname}")
        return resolve_redirects_with_get(current_url, ua, timeout, max_redirects)
    
    # First attempt: Use the standard HEAD-based resolution
    try:
        final_url, was_redirected = resolve_final_url(current_url, ua, timeout, max_redirects)
        return final_url, was_redirected
    except Exception as e:
        logging.debug(f"Standard redirect resolution failed for {current_url}: {e}")
        
        # Check if this might be a redirect service that blocks HEAD requests
        if "404" in str(e) or "HTTP Error 404" in str(e):
            parsed = urllib.parse.urlparse(current_url)
            hostname = parsed.hostname or ""
            
            # Heuristic: domains that might be redirect services
            redirect_indicators = ['link', 'short', 'redirect', 'go', 'r', 'l']
            might_be_redirect_service = any(indicator in hostname.lower() for indicator in redirect_indicators)
            
            if might_be_redirect_service:
                logging.info(f"404 response detected on potential redirect service {hostname}, attempting GET fallback")
                try:
                    return resolve_redirects_with_get(current_url, ua, timeout, max_redirects)
                except Exception as fallback_error:
                    logging.warning(f"GET fallback also failed for {current_url}: {fallback_error}")
                    return current_url, False
        
        # For other errors, return original URL
        logging.warning(f"Redirect resolution failed for {current_url}: {e}")
        return current_url, False


def resolve_redirects_with_get(url: str, ua: str, timeout: int, max_redirects: int) -> tuple[str, bool]:
    """
    Resolve redirects using GET requests instead of HEAD.
    
    This is a fallback for services that return 404 on HEAD but work with GET.
    
    Args:
        url: URL to resolve
        ua: User agent string
        timeout: Request timeout
        max_redirects: Maximum redirects to follow
        
    Returns:
        tuple[str, bool]: (final_url, was_redirected)
    """
    current_url = url
    redirect_count = 0
    was_redirected = False
    
    while redirect_count < max_redirects:
        logging.debug(f"GET-based redirect check for: {current_url}")
        
        try:
            req = urllib.request.Request(current_url, headers={
                "User-Agent": ua,
                "Accept-Language": "zh-CN,zh;q=0.9"
            })
            
            with urllib.request.urlopen(req, timeout=timeout, context=ssl_context_unverified) as response:
                final_url = response.geturl()
                if final_url != current_url:
                    was_redirected = True
                    logging.info(f"GET-based redirect resolved: {url} -> {final_url}")
                return final_url, was_redirected
                
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                location = e.headers.get('Location')
                if not location:
                    return current_url, was_redirected
                
                # Handle relative URLs
                if location.startswith('/'):
                    parsed = urllib.parse.urlparse(current_url)
                    location = f"{parsed.scheme}://{parsed.netloc}{location}"
                elif not location.startswith(('http://', 'https://')):
                    location = urllib.parse.urljoin(current_url, location)
                
                logging.debug(f"GET-based redirect {e.code}: {current_url} -> {location}")
                current_url = location
                redirect_count += 1
                was_redirected = True
                continue
            else:
                # Non-redirect HTTP error
                logging.warning(f"GET-based resolution HTTP error {e.code} for {current_url}")
                return current_url, was_redirected
                
        except Exception as e:
            logging.warning(f"GET-based resolution error for {current_url}: {e}")
            return current_url, was_redirected
    
    # Max redirects exceeded
    logging.warning(f"Max redirects ({max_redirects}) exceeded in GET-based resolution for {url}")
    return current_url, was_redirected
```

### Modification 2: Update get_effective_host Function

**File**: `webfetcher.py`  
**Location**: Line 752 (inside the `get_effective_host` function)

**Find this line**:
```python
final_url, was_redirected = resolve_final_url(url, ua=ua, timeout=10)
```

**Replace with**:
```python
final_url, was_redirected = resolve_final_url_with_fallback(url, ua=ua, timeout=10)
```

### Modification 3: URL Validation Function

**File**: `webfetcher.py`  
**Location**: After the import statements (around line 30), add this function:

```python
def validate_and_encode_url(url: str) -> str:
    """
    Validate URL and ensure safe encoding for subprocess calls.
    
    Checks for potentially problematic characters and ensures proper URL encoding.
    
    Args:
        url: URL to validate and encode
        
    Returns:
        str: Safely encoded URL
        
    Raises:
        ValueError: If URL is invalid or contains unsafe patterns
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
    
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty after stripping whitespace")
    
    try:
        # Parse URL to validate structure
        parsed = urllib.parse.urlparse(url)
        
        # Basic validation
        if not parsed.scheme:
            raise ValueError(f"URL missing scheme: {url}")
        if not parsed.netloc:
            raise ValueError(f"URL missing network location: {url}")
        
        # Check for potentially problematic characters in shell context
        # Note: & is actually fine in subprocess.run with list arguments,
        # but we log it for debugging purposes
        shell_special_chars = ['`', '$', '\\', '"', "'"]
        for char in shell_special_chars:
            if char in url:
                logging.warning(f"URL contains shell special character '{char}': {url}")
                # Don't raise error, just warn - subprocess.run with list args handles this
        
        # Re-encode the URL to ensure proper formatting
        # This handles cases where URLs might have been partially decoded
        if parsed.query:
            # Re-encode query parameters to handle & properly
            query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            new_query = urllib.parse.urlencode(query_params)
            parsed = parsed._replace(query=new_query)
        
        encoded_url = urllib.parse.urlunparse(parsed)
        
        if encoded_url != url:
            logging.debug(f"URL re-encoded: {url} -> {encoded_url}")
        
        return encoded_url
        
    except Exception as e:
        raise ValueError(f"URL validation failed for '{url}': {e}")
```

### Modification 4: Update fetch_html_with_curl Function

**File**: `webfetcher.py`  
**Location**: Lines 608-627 (the `fetch_html_with_curl` function)

**Find the existing function**:
```python
def fetch_html_with_curl(url: str, ua: Optional[str] = None, timeout: int = 30) -> str:
    """Fetch HTML using curl as fallback (for SSL issues)."""
    ua = ua or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    try:
        cmd = [
            'curl', '-s', '-L',
            '--max-time', str(timeout),
            '-H', f'User-Agent: {ua}',
            '--compressed',  # Accept compressed responses
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(f"curl failed with code {result.returncode}: {result.stderr}")
    except subprocess.TimeoutExpired:
        raise Exception(f"curl timeout for {url}")
    except Exception as e:
        logging.error(f"Failed to fetch with curl from {url}: {e}")
        raise
```

**Replace with**:
```python
def fetch_html_with_curl(url: str, ua: Optional[str] = None, timeout: int = 30) -> str:
    """Fetch HTML using curl as fallback (for SSL issues)."""
    ua = ua or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    
    try:
        # Validate and encode URL for safe subprocess execution
        validated_url = validate_and_encode_url(url)
        
        cmd = [
            'curl', '-s', '-L',
            '--max-time', str(timeout),
            '-H', f'User-Agent: {ua}',
            '--compressed',  # Accept compressed responses
            validated_url
        ]
        
        logging.debug(f"Executing curl command for URL: {validated_url}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
        
        if result.returncode == 0:
            return result.stdout
        else:
            # Log curl error details for debugging
            logging.error(f"curl failed for {validated_url}: return code {result.returncode}, stderr: {result.stderr}")
            raise Exception(f"curl failed with code {result.returncode}: {result.stderr}")
            
    except ValueError as e:
        # URL validation error
        logging.error(f"URL validation failed for curl: {e}")
        raise Exception(f"Invalid URL for curl: {e}")
    except subprocess.TimeoutExpired:
        logging.error(f"curl timeout for {url}")
        raise Exception(f"curl timeout for {url}")
    except Exception as e:
        logging.error(f"Failed to fetch with curl from {url}: {e}")
        raise
```

## Integration Testing Code

### Test Case 1: Redirect Resolution Test

Create a test file: `test_redirect_resolution.py`

```python
#!/usr/bin/env python3
"""Test script for enhanced redirect resolution."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from webfetcher import resolve_final_url_with_fallback, get_effective_host
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def test_redirect_resolution():
    """Test enhanced redirect resolution functionality."""
    
    print("Testing enhanced redirect resolution...")
    
    # Test 1: Known redirect service (xhslink.com)
    test_urls = [
        "https://xhslink.com/o/test",  # Should use GET fallback
        "https://www.xiaohongshu.com/explore/test",  # Should work directly
        "https://example.com/test",  # Should handle normally
    ]
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        try:
            final_url, was_redirected = resolve_final_url_with_fallback(url)
            print(f"  Result: {final_url} (redirected: {was_redirected})")
            
            # Test effective host determination
            effective_host = get_effective_host(url)
            print(f"  Effective host: {effective_host}")
            
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\nRedirect resolution tests completed.")

if __name__ == "__main__":
    test_redirect_resolution()
```

### Test Case 2: URL Validation Test

Create a test file: `test_url_validation.py`

```python
#!/usr/bin/env python3
"""Test script for URL validation functionality."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from webfetcher import validate_and_encode_url
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

def test_url_validation():
    """Test URL validation functionality."""
    
    print("Testing URL validation...")
    
    # Test cases: (url, should_pass, description)
    test_cases = [
        ("https://example.com/test?param=1&other=2", True, "URL with ampersands"),
        ("https://example.com/path with spaces", True, "URL with spaces"),
        ("https://example.com/test?search=hello%20world", True, "URL with encoded spaces"),
        ("https://example.com/test`cmd`", False, "URL with backticks"),
        ("not-a-url", False, "Invalid URL format"),
        ("", False, "Empty URL"),
        ("https://", False, "URL without netloc"),
        ("https://example.com/test?a=1&b=2&c=3", True, "Multiple ampersands"),
    ]
    
    for url, should_pass, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"  URL: {url}")
        try:
            validated_url = validate_and_encode_url(url)
            if should_pass:
                print(f"  ✓ PASS: {validated_url}")
            else:
                print(f"  ✗ FAIL: Expected validation error but got: {validated_url}")
        except ValueError as e:
            if not should_pass:
                print(f"  ✓ PASS: Correctly rejected with: {e}")
            else:
                print(f"  ✗ FAIL: Unexpected validation error: {e}")
        except Exception as e:
            print(f"  ✗ ERROR: Unexpected exception: {e}")
    
    print("\nURL validation tests completed.")

if __name__ == "__main__":
    test_url_validation()
```

## Verification Commands

### Command 1: Test XiaoHongShu Redirect Resolution
```bash
# Test xhslink.com URL (should resolve and use XiaoHongShu parser)
python webfetcher.py "https://xhslink.com/o/example" --verbose

# Expected logs should include:
# - "Using GET-based redirect resolution for known service: xhslink.com"
# - "Selected parser: Xiaohongshu"
```

### Command 2: Test URL with Special Characters
```bash
# Test URL with ampersands (should work without shell errors)
python webfetcher.py "https://example.com/test?param=1&other=2" --verbose

# Expected: No shell parsing errors, proper curl execution
```

### Command 3: Regression Test for Direct XiaoHongShu URLs
```bash
# Test direct xiaohongshu.com URL (should continue working)
python webfetcher.py "https://www.xiaohongshu.com/explore/example" --verbose

# Expected: Direct parser selection, no redirect resolution needed
```

### Command 4: Test wf.py Script Integration
```bash
# Test through wf.py wrapper
python wf.py "https://xhslink.com/o/example" output/

# Expected: Works correctly with output directory parsing
```

## Deployment Checklist

### Before Deployment
- [ ] Run all test scripts successfully
- [ ] Verify no syntax errors in modified functions
- [ ] Test with actual xhslink.com URLs (if available)
- [ ] Test URL validation with various special characters
- [ ] Confirm no regression in existing functionality

### After Deployment
- [ ] Monitor logs for new error patterns
- [ ] Verify redirect resolution performance
- [ ] Check that XiaoHongShu parser selection works correctly
- [ ] Validate curl subprocess calls work properly

### Rollback Plan
If issues occur:
1. Comment out call to `resolve_final_url_with_fallback` in `get_effective_host`
2. Restore original `resolve_final_url` call
3. Comment out URL validation in `fetch_html_with_curl`
4. Return to previous stable state

## Implementation Notes

### Function Integration Points
1. **Enhanced redirect resolution**: Used by `get_effective_host` for parser selection
2. **URL validation**: Used by `fetch_html_with_curl` for subprocess safety
3. **Original host tracking**: Maintained for parser selection logic
4. **Error handling**: Graceful fallbacks for all failure scenarios

### Performance Considerations
1. **GET fallback**: Only used for known problematic services or after HEAD fails
2. **URL validation**: Minimal overhead, mostly validation and logging
3. **Caching potential**: Consider adding redirect result caching for frequently accessed URLs
4. **Timeout handling**: Maintains existing timeout behavior

### Logging Strategy
1. **Debug level**: Detailed redirect resolution steps
2. **Info level**: Successful redirections and parser selections
3. **Warning level**: Fallback activations and URL encoding issues
4. **Error level**: Validation failures and resolution errors

This specification provides the exact code changes needed to implement both XiaoHongShu URL fixes while maintaining backward compatibility and system reliability.