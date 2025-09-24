#!/usr/bin/env python3
"""
Base Extractor Class for Safari-based Content Extraction
=========================================================

Abstract base class that defines the interface and common functionality
for all site-specific Safari extractors in the Web_Fetcher system.

This class provides:
- Standard interface for extraction
- Safari automation helpers
- Content validation framework
- Error handling patterns
- Cleanup mechanisms

Author: Web_Fetcher Team
Version: 1.0
Date: 2025-09-23
"""

import subprocess
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from bs4 import BeautifulSoup


@dataclass
class ExtractionResult:
    """Standard result container for all extractors"""
    success: bool
    html_content: Optional[str] = None
    title: Optional[str] = None
    date: Optional[str] = None
    author: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    extraction_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'success': self.success,
            'title': self.title,
            'date': self.date,
            'author': self.author,
            'content_length': len(self.content) if self.content else 0,
            'metadata': self.metadata,
            'error_message': self.error_message,
            'warnings': self.warnings,
            'extraction_time': self.extraction_time
        }


class BaseExtractor(ABC):
    """
    Abstract base class for site-specific Safari extractors.
    
    All site-specific extractors must inherit from this class and implement
    the required abstract methods while leveraging the provided utilities.
    """
    
    # Class attributes to be overridden by subclasses
    SITE_NAME: str = "Generic"
    SITE_PATTERNS: List[str] = []  # URL patterns this extractor handles
    REQUIRES_SAFARI: bool = True    # Whether Safari is required
    DEFAULT_TIMEOUT: int = 60       # Default page load timeout
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize base extractor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.safari_window_id = None
        self.last_error = None
        
    # ===========================================================================
    # ABSTRACT METHODS (must be implemented by subclasses)
    # ===========================================================================
    
    @abstractmethod
    def parse_content(self, html: str, url: str) -> ExtractionResult:
        """
        Parse HTML content and extract structured data.
        
        This method must be implemented by each site-specific extractor
        to handle the unique structure of that site.
        
        Args:
            html: Raw HTML content from Safari
            url: Original URL for context
            
        Returns:
            ExtractionResult with parsed data
        """
        pass
    
    @abstractmethod
    def validate_content(self, html: str, url: str) -> Tuple[bool, List[str]]:
        """
        Validate that content was properly extracted.
        
        Site-specific validation to ensure quality extraction.
        
        Args:
            html: HTML content to validate
            url: Original URL for context
            
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        pass
    
    # ===========================================================================
    # SAFARI AUTOMATION METHODS
    # ===========================================================================
    
    def check_safari_availability(self) -> bool:
        """Check if Safari is available and accessible."""
        try:
            result = subprocess.run(
                ['osascript', '-e', 'tell application "Safari" to name'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                self.logger.error("Safari not accessible via AppleScript")
                self.last_error = "Safari permission denied"
                return False
                
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error("Safari availability check timed out")
            self.last_error = "Safari check timeout"
            return False
        except Exception as e:
            self.logger.error(f"Safari availability check failed: {e}")
            self.last_error = str(e)
            return False
    
    def open_safari_window(self) -> bool:
        """Open a new Safari window for extraction."""
        script = '''
        tell application "Safari"
            make new document
            return id of window 1
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.safari_window_id = result.stdout.strip()
                self.logger.info(f"Opened Safari window: {self.safari_window_id}")
                return True
            else:
                self.logger.error(f"Failed to open Safari window: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error opening Safari window: {e}")
            return False
    
    def navigate_to_url(self, url: str) -> bool:
        """Navigate Safari to specified URL."""
        script = f'''
        tell application "Safari"
            set URL of current tab of window 1 to "{url}"
            activate
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if result.returncode == 0:
                self.logger.info(f"Navigated to: {url}")
                return True
            else:
                self.logger.error(f"Navigation failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Navigation error: {e}")
            return False
    
    def wait_for_page_load(self, timeout: int = None) -> bool:
        """Wait for page to fully load."""
        timeout = timeout or self.DEFAULT_TIMEOUT
        start_time = time.time()
        
        self.logger.info(f"Waiting for page load (timeout: {timeout}s)...")
        
        while time.time() - start_time < timeout:
            try:
                # Check document ready state
                script = '''
                tell application "Safari"
                    do JavaScript "document.readyState" in current tab of window 1
                end tell
                '''
                
                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0 and result.stdout.strip() == "complete":
                    load_time = time.time() - start_time
                    self.logger.info(f"Page loaded in {load_time:.2f}s")
                    return True
                
                time.sleep(2)
                
            except Exception as e:
                self.logger.warning(f"Error checking page state: {e}")
                
        self.logger.warning(f"Page load timeout after {timeout}s")
        return False
    
    def wait_for_element(self, selector: str, timeout: int = 30) -> bool:
        """
        Wait for specific element to appear on page.
        
        Args:
            selector: CSS selector for element
            timeout: Maximum wait time
            
        Returns:
            bool: True if element found
        """
        start_time = time.time()
        
        self.logger.info(f"Waiting for element: {selector}")
        
        while time.time() - start_time < timeout:
            try:
                script = f'''
                tell application "Safari"
                    do JavaScript "document.querySelector('{selector}') !== null" in current tab of window 1
                end tell
                '''
                
                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0 and result.stdout.strip() == "true":
                    self.logger.info(f"Element found: {selector}")
                    return True
                    
                time.sleep(1)
                
            except Exception:
                pass
                
        self.logger.warning(f"Element not found: {selector}")
        return False
    
    def extract_html_content(self) -> Optional[str]:
        """Extract full HTML content from current Safari page."""
        script = '''
        tell application "Safari"
            do JavaScript "document.documentElement.outerHTML" in current tab of window 1
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                html = result.stdout.strip()
                self.logger.info(f"Extracted HTML: {len(html)} bytes")
                return html
            else:
                self.logger.error(f"HTML extraction failed: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting HTML: {e}")
            return None
    
    def execute_javascript(self, js_code: str) -> Optional[str]:
        """
        Execute JavaScript in Safari and return result.
        
        Args:
            js_code: JavaScript code to execute
            
        Returns:
            Result of JavaScript execution or None
        """
        # Escape quotes in JavaScript
        js_escaped = js_code.replace('"', '\\"')
        
        script = f'''
        tell application "Safari"
            do JavaScript "{js_escaped}" in current tab of window 1
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                self.logger.error(f"JavaScript execution failed: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"JavaScript error: {e}")
            return None
    
    def close_safari_window(self) -> None:
        """Close the Safari window used for extraction."""
        if not self.safari_window_id:
            return
            
        script = f'''
        tell application "Safari"
            close window id {self.safari_window_id}
        end tell
        '''
        
        try:
            subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            self.logger.info("Closed Safari window")
        except Exception as e:
            self.logger.warning(f"Error closing Safari window: {e}")
    
    # ===========================================================================
    # MAIN EXTRACTION INTERFACE
    # ===========================================================================
    
    def extract(self, url: str, timeout: Optional[int] = None, **kwargs) -> ExtractionResult:
        """
        Main extraction method that coordinates the full process.
        
        Args:
            url: URL to extract content from
            timeout: Optional timeout override
            **kwargs: Additional parameters for specific extractors
            
        Returns:
            ExtractionResult with extracted data
        """
        start_time = time.time()
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        self.logger.info(f"Starting {self.SITE_NAME} extraction for: {url}")
        
        try:
            # Step 1: Check Safari availability
            if self.REQUIRES_SAFARI and not self.check_safari_availability():
                return ExtractionResult(
                    success=False,
                    error_message="Safari not available"
                )
            
            # Step 2: Open Safari window
            if self.REQUIRES_SAFARI and not self.open_safari_window():
                return ExtractionResult(
                    success=False,
                    error_message="Failed to open Safari window"
                )
            
            # Step 3: Navigate to URL
            if not self.navigate_to_url(url):
                return ExtractionResult(
                    success=False,
                    error_message="Failed to navigate to URL"
                )
            
            # Step 4: Wait for page load
            if not self.wait_for_page_load(timeout):
                self.logger.warning("Page load timeout - attempting extraction anyway")
            
            # Step 5: Additional wait for dynamic content (optional)
            if self.config.get('extra_wait', 0) > 0:
                time.sleep(self.config.get('extra_wait'))
            
            # Step 6: Extract HTML
            html = self.extract_html_content()
            if not html:
                return ExtractionResult(
                    success=False,
                    error_message="Failed to extract HTML content"
                )
            
            # Step 7: Validate content
            is_valid, warnings = self.validate_content(html, url)
            if not is_valid and not self.config.get('force_extraction', False):
                return ExtractionResult(
                    success=False,
                    error_message="Content validation failed",
                    warnings=warnings
                )
            
            # Step 8: Parse content
            result = self.parse_content(html, url)
            result.warnings.extend(warnings)
            result.extraction_time = time.time() - start_time
            result.html_content = html  # Store raw HTML
            
            self.logger.info(
                f"Extraction {'successful' if result.success else 'failed'} "
                f"in {result.extraction_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Extraction error: {e}")
            return ExtractionResult(
                success=False,
                error_message=str(e),
                extraction_time=time.time() - start_time
            )
        
        finally:
            # Always cleanup
            self.cleanup()
    
    def cleanup(self) -> None:
        """Cleanup resources after extraction."""
        try:
            self.close_safari_window()
        except:
            pass
    
    # ===========================================================================
    # UTILITY METHODS
    # ===========================================================================
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
            
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove zero-width characters
        text = text.replace('\u200b', '').replace('\u200c', '')
        
        return text.strip()
    
    def extract_date_from_url(self, url: str) -> Optional[str]:
        """
        Try to extract date from URL pattern.
        
        Args:
            url: URL to parse
            
        Returns:
            Date string or None
        """
        import re
        
        # Common date patterns in URLs
        patterns = [
            r'/(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # 2024-09-23 or 2024/09/23
            r'/(\d{8})',  # 20240923
            r't(\d{8})',  # t20240923
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                if len(match.groups()) == 3:
                    year, month, day = match.groups()
                    return f"{year}-{month:0>2}-{day:0>2}"
                elif len(match.groups()) == 1:
                    date_str = match.group(1)
                    if len(date_str) == 8:
                        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        
        return None
    
    def to_markdown(self, result: ExtractionResult) -> str:
        """
        Convert extraction result to Markdown format.
        
        Args:
            result: ExtractionResult to convert
            
        Returns:
            Markdown formatted string
        """
        md_parts = []
        
        # Title
        if result.title:
            md_parts.append(f"# {result.title}\n")
        
        # Metadata
        if result.date or result.author:
            md_parts.append("---\n")
            if result.date:
                md_parts.append(f"Date: {result.date}\n")
            if result.author:
                md_parts.append(f"Author: {result.author}\n")
            md_parts.append("---\n")
        
        # Content
        if result.content:
            md_parts.append(result.content)
        
        return '\n'.join(md_parts)
    
    @classmethod
    def can_handle(cls, url: str) -> bool:
        """
        Check if this extractor can handle the given URL.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if this extractor can handle the URL
        """
        if not cls.SITE_PATTERNS:
            return False
            
        for pattern in cls.SITE_PATTERNS:
            if pattern in url:
                return True
                
        return False


def test_extractor():
    """Test function for base extractor functionality"""
    
    # This would be implemented by a concrete extractor
    class TestExtractor(BaseExtractor):
        SITE_NAME = "Test"
        SITE_PATTERNS = ["example.com"]
        
        def parse_content(self, html: str, url: str) -> ExtractionResult:
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.find('title')
            
            return ExtractionResult(
                success=True,
                title=title.text if title else "No title",
                content="Test content extracted"
            )
        
        def validate_content(self, html: str, url: str) -> Tuple[bool, List[str]]:
            warnings = []
            if len(html) < 100:
                warnings.append("Content too short")
            return len(html) > 0, warnings
    
    # Test the extractor
    extractor = TestExtractor()
    print(f"Safari available: {extractor.check_safari_availability()}")
    print(f"Can handle example.com: {TestExtractor.can_handle('http://example.com/page')}")


if __name__ == '__main__':
    test_extractor()