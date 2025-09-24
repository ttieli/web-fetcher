#!/usr/bin/env python3
"""
Base Extractor for Safari-based Content Extraction
=================================================

Abstract base class for site-specific Safari extractors.
Provides common functionality and interface for all extractors.

Author: Web_Fetcher Team
Version: 1.0.0
"""

import subprocess
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
from bs4 import BeautifulSoup

class BaseExtractor(ABC):
    """
    Abstract base class for Safari-based content extractors.
    
    Provides common Safari automation functionality and defines
    the interface that all site-specific extractors must implement.
    """
    
    def __init__(self, url: str):
        """
        Initialize the extractor.
        
        Args:
            url (str): Target URL to extract content from
        """
        self.url = url
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.extraction_time = datetime.now()
        
    def check_safari_availability(self) -> bool:
        """
        Check if Safari is available and ready for automation.
        
        Returns:
            bool: True if Safari is available
        """
        self.logger.debug("Checking Safari availability...")
        
        try:
            # Test AppleScript permissions with Safari
            result = subprocess.run([
                'osascript', '-e',
                'tell application "Safari" to get name'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.logger.error("Safari AppleScript permissions not available")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Safari availability check failed: {e}")
            return False
    
    def navigate_to_url(self) -> bool:
        """
        Navigate Safari to the target URL.
        
        Returns:
            bool: True if navigation successful
        """
        self.logger.info(f"Navigating to: {self.url}")
        
        script = f'''
        tell application "Safari"
            if not (exists window 1) then
                make new document
            end if
            set URL of current tab of window 1 to "{self.url}"
            activate
        end tell
        '''
        
        try:
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=20)
            
            if result.returncode == 0:
                self.logger.info("Successfully navigated to URL")
                return True
            else:
                self.logger.error(f"Failed to navigate to URL: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Navigation error: {e}")
            return False
    
    def wait_for_page_load(self, timeout: int = 60) -> bool:
        """
        Wait for page to fully load.
        
        Args:
            timeout (int): Maximum time to wait in seconds
            
        Returns:
            bool: True if page loaded successfully
        """
        self.logger.debug("Waiting for page to load...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check document ready state
                ready_script = '''
                tell application "Safari"
                    set readyState to do JavaScript "document.readyState" in current tab of window 1
                    return readyState
                end tell
                '''
                
                result = subprocess.run(['osascript', '-e', ready_script], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    ready_state = result.stdout.strip()
                    if ready_state == "complete":
                        load_time = time.time() - start_time
                        self.logger.info(f"Page loaded in {load_time:.2f} seconds")
                        return True
                
                time.sleep(2)
                
            except Exception as e:
                self.logger.warning(f"Error checking page readiness: {e}")
                time.sleep(2)
                continue
        
        self.logger.warning(f"Page load timeout after {timeout} seconds")
        return False
    
    def extract_html_content(self) -> Optional[str]:
        """
        Extract HTML content from Safari.
        
        Returns:
            Optional[str]: HTML content or None if extraction failed
        """
        self.logger.debug("Extracting HTML content...")
        
        script = '''
        tell application "Safari"
            set pageSource to do JavaScript "document.documentElement.outerHTML" in current tab of window 1
            return pageSource
        end tell
        '''
        
        try:
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                html_content = result.stdout
                self.logger.info(f"Extracted {len(html_content)} characters of HTML")
                return html_content
            else:
                self.logger.error(f"Failed to extract HTML: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"HTML extraction error: {e}")
            return None
    
    def validate_content_quality(self, html_content: str) -> Dict[str, Any]:
        """
        Validate extracted content quality.
        
        Args:
            html_content (str): HTML content to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        validation = {
            'is_valid': False,
            'has_captcha': False,
            'has_content': False,
            'content_length': 0,
            'quality_score': 0,
            'issues': []
        }
        
        try:
            # Check for CAPTCHA indicators
            captcha_keywords = ['seccaptcha', 'captcha', '验证码', '滑动验证', 'security check']
            for keyword in captcha_keywords:
                if keyword.lower() in html_content.lower():
                    validation['has_captcha'] = True
                    validation['issues'].append(f"CAPTCHA detected: {keyword}")
                    break
            
            # Parse HTML and check content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text_content = soup.get_text()
            text_length = len(text_content.strip())
            
            validation['content_length'] = text_length
            validation['has_content'] = text_length > 100
            
            # Calculate quality score
            if text_length > 1000:
                validation['quality_score'] += 3
            elif text_length > 500:
                validation['quality_score'] += 2
            elif text_length > 100:
                validation['quality_score'] += 1
            
            # Check for title
            title = soup.find('title')
            if title and len(title.get_text().strip()) > 5:
                validation['quality_score'] += 1
            
            # Check for main content areas
            content_selectors = ['article', 'main', '.content', '.article-content']
            for selector in content_selectors:
                if soup.select_one(selector):
                    validation['quality_score'] += 1
                    break
            
            # Final validation
            validation['is_valid'] = (
                not validation['has_captcha'] and 
                validation['has_content'] and 
                validation['quality_score'] >= 2
            )
            
            if not validation['is_valid']:
                if validation['has_captcha']:
                    validation['issues'].append("CAPTCHA present")
                if not validation['has_content']:
                    validation['issues'].append("Insufficient content")
                if validation['quality_score'] < 2:
                    validation['issues'].append(f"Low quality score: {validation['quality_score']}")
                    
        except Exception as e:
            self.logger.error(f"Content validation error: {e}")
            validation['issues'].append(f"Validation error: {e}")
        
        return validation
    
    @abstractmethod
    def parse_content(self, html_content: str) -> Dict[str, str]:
        """
        Parse site-specific content from HTML.
        
        This method must be implemented by each site-specific extractor
        to handle the unique structure and content of that site.
        
        Args:
            html_content (str): Raw HTML content
            
        Returns:
            Dict[str, str]: Parsed content with keys like 'title', 'content', etc.
        """
        pass
    
    @abstractmethod
    def format_output(self, parsed_content: Dict[str, str]) -> str:
        """
        Format parsed content for output.
        
        This method must be implemented by each site-specific extractor
        to format the content according to the expected output format.
        
        Args:
            parsed_content (Dict[str, str]): Parsed content
            
        Returns:
            str: Formatted content (typically markdown)
        """
        pass
    
    def extract(self, timeout: int = 60, wait_time: int = 3) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Main extraction workflow.
        
        Args:
            timeout (int): Page load timeout in seconds
            wait_time (int): Additional wait time for dynamic content
            
        Returns:
            Tuple[bool, str, Dict]: (success, content, metadata)
        """
        metadata = {
            'url': self.url,
            'extractor': self.__class__.__name__,
            'extraction_time': self.extraction_time.isoformat(),
            'method': 'safari'
        }
        
        try:
            # Step 1: Check Safari availability
            if not self.check_safari_availability():
                return False, "Safari not available", metadata
            
            # Step 2: Navigate to URL
            if not self.navigate_to_url():
                return False, "Failed to navigate to URL", metadata
            
            # Step 3: Wait for page load
            if not self.wait_for_page_load(timeout):
                self.logger.warning("Page load timeout - proceeding anyway")
            
            # Step 4: Additional wait for dynamic content
            if wait_time > 0:
                self.logger.info(f"Waiting {wait_time}s for dynamic content...")
                time.sleep(wait_time)
            
            # Step 5: Extract HTML
            html_content = self.extract_html_content()
            if not html_content:
                return False, "Failed to extract HTML content", metadata
            
            # Step 6: Validate content
            validation = self.validate_content_quality(html_content)
            metadata['validation'] = validation
            
            if not validation['is_valid']:
                issues = ', '.join(validation['issues'])
                return False, f"Content validation failed: {issues}", metadata
            
            # Step 7: Parse content (site-specific)
            parsed_content = self.parse_content(html_content)
            if not parsed_content.get('title') or not parsed_content.get('content'):
                return False, "Failed to parse content", metadata
            
            # Step 8: Format output
            formatted_content = self.format_output(parsed_content)
            
            metadata['content_length'] = len(formatted_content)
            metadata['parsed_fields'] = list(parsed_content.keys())
            
            self.logger.info("Extraction completed successfully")
            return True, formatted_content, metadata
            
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            metadata['error'] = str(e)
            return False, str(e), metadata