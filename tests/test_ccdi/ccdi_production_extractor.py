#!/usr/bin/env python3
"""
CCDI Production Content Extractor
=================================

Production-ready solution for extracting content from CCDI website articles
using the proven Safari + AppleScript + BeautifulSoup approach.

This script provides a clean, reliable method to extract Chinese government 
content while bypassing CAPTCHA restrictions through Safari session reuse.

Architecture:
- Safari browser automation via AppleScript
- HTML content extraction and parsing  
- Clean markdown output generation
- Comprehensive error handling and user feedback
- Production-ready logging and status reporting

Author: Archy-Principle-Architect
Version: 1.0
Date: 2025-09-23
"""

import subprocess
import json
import time
import sys
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import logging
from typing import Dict, Optional, Tuple

class CCDIProductionExtractor:
    """Production-ready CCDI content extractor using Safari direct method"""
    
    def __init__(self, target_url: str, output_dir: str):
        self.target_url = target_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        log_file = self.output_dir.parent / "ccdi_extraction.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"CCDI Production Extractor initialized")
        self.logger.info(f"Target URL: {target_url}")
        self.logger.info(f"Output directory: {output_dir}")
    
    def check_safari_availability(self) -> bool:
        """Check if Safari is available and ready for automation"""
        self.logger.info("Checking Safari availability...")
        
        try:
            # Test AppleScript permissions with Safari
            result = subprocess.run([
                'osascript', '-e',
                'tell application "Safari" to get name'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.logger.error("Safari AppleScript permissions not available")
                self.logger.error("Please grant AppleScript permissions to Terminal/Python in System Preferences")
                return False
            
            # Check if Safari has windows
            result = subprocess.run([
                'osascript', '-e',
                'tell application "Safari" to get count of windows'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                window_count = int(result.stdout.strip())
                if window_count == 0:
                    self.logger.warning("Safari has no windows open - will create one")
                else:
                    self.logger.info(f"Safari ready with {window_count} window(s)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Safari availability check failed: {e}")
            return False
    
    def navigate_to_url(self) -> bool:
        """Navigate Safari to the target URL"""
        self.logger.info("Navigating to target URL...")
        
        script = f'''
        tell application "Safari"
            if not (exists window 1) then
                make new document
            end if
            set URL of current tab of window 1 to "{self.target_url}"
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
        """Wait for page to fully load"""
        self.logger.info("Waiting for page to load...")
        
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
                        self.logger.info(f"Page loaded successfully in {load_time:.2f} seconds")
                        return True
                
                time.sleep(2)
                
            except Exception as e:
                self.logger.warning(f"Error checking page readiness: {e}")
                time.sleep(2)
                continue
        
        self.logger.warning(f"Page load timeout after {timeout} seconds")
        return False
    
    def extract_html_content(self) -> Optional[str]:
        """Extract HTML content from Safari"""
        self.logger.info("Extracting HTML content...")
        
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
                self.logger.info(f"Successfully extracted {len(html_content)} characters of HTML")
                return html_content
            else:
                self.logger.error(f"Failed to extract HTML: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"HTML extraction error: {e}")
            return None
    
    def validate_content_quality(self, html_content: str) -> Dict[str, any]:
        """Validate extracted content quality"""
        self.logger.info("Validating content quality...")
        
        validation = {
            'is_valid': False,
            'has_captcha': False,
            'has_content': False,
            'content_length': 0,
            'quality_indicators': []
        }
        
        try:
            # Check for CAPTCHA indicators
            captcha_keywords = ['seccaptcha', 'captcha', '验证码', '滑动验证', 'security check']
            for keyword in captcha_keywords:
                if keyword.lower() in html_content.lower():
                    validation['has_captcha'] = True
                    self.logger.warning(f"CAPTCHA detected: {keyword}")
                    break
            
            # Parse HTML to check content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for main content areas with more comprehensive selectors
            content_selectors = [
                '.bt_content', '.TRS_Editor', '.article-content', 'article', 'main',
                '.content', '.post-content', '.entry-content', '.article-body',
                '#content', '[class*="content"]', '[class*="article"]', 'p'
            ]
            
            max_content_length = 0
            best_selector = None
            
            for selector in content_selectors:
                try:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        content_text = content_elem.get_text(strip=True)
                        if len(content_text) > max_content_length:
                            max_content_length = len(content_text)
                            best_selector = selector
                            validation['quality_indicators'].append(f"Found {len(content_text)} chars via {selector}")
                except:
                    continue
            
            # If no specific content area found, check overall body content
            if max_content_length < 200:
                body = soup.find('body')
                if body:
                    # Remove navigation, header, footer elements
                    for unwanted in body(['nav', 'header', 'footer', 'script', 'style']):
                        unwanted.decompose()
                    body_text = body.get_text(strip=True)
                    if len(body_text) > max_content_length:
                        max_content_length = len(body_text)
                        best_selector = 'body (fallback)'
                        validation['quality_indicators'].append(f"Found {len(body_text)} chars via body fallback")
            
            # Set validation results
            validation['content_length'] = max_content_length
            validation['has_content'] = max_content_length > 100  # Lowered threshold
            
            # More lenient validation criteria
            validation['is_valid'] = (
                not validation['has_captcha'] and 
                validation['has_content'] and 
                validation['content_length'] > 200  # Reduced threshold
            )
            
            self.logger.info(f"Content analysis: {max_content_length} chars found via {best_selector}")
            
            if validation['is_valid']:
                self.logger.info("Content validation passed")
            else:
                self.logger.warning("Content validation failed")
                self.logger.warning(f"Indicators: {validation['quality_indicators']}")
                
        except Exception as e:
            self.logger.error(f"Content validation error: {e}")
        
        return validation
    
    def parse_article_content(self, html_content: str) -> Dict[str, str]:
        """Parse structured article content from HTML"""
        self.logger.info("Parsing article content...")
        
        article = {
            'title': '',
            'content': '',
            'publish_time': '',
            'source': '',
            'extraction_time': datetime.now().isoformat()
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title with expanded selectors
            title_selectors = [
                'h1.bt_title', 'h1', '.article-title', '.title', 'title',
                '.post-title', '.entry-title', '[class*="title"]', '.headline'
            ]
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if len(title_text) > 5 and '验证' not in title_text and 'CAPTCHA' not in title_text:
                        article['title'] = title_text
                        self.logger.info(f"Title found via {selector}: {title_text[:50]}...")
                        break
            
            # Extract main content with comprehensive approach
            content_selectors = [
                '.bt_content', '.TRS_Editor', '.article-content', 'article', 'main',
                '.content', '.post-content', '.entry-content', '.article-body',
                '#content', '[class*="content"]', '.text-content'
            ]
            
            best_content = ""
            best_selector = None
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Clean unwanted elements
                    elem_copy = content_elem.__copy__()
                    for unwanted in elem_copy(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                        unwanted.decompose()
                    
                    # Extract clean text
                    content_text = elem_copy.get_text(strip=True, separator='\n\n')
                    if len(content_text) > len(best_content):
                        best_content = content_text
                        best_selector = selector
            
            # If still no good content, try body fallback
            if len(best_content) < 100:
                body = soup.find('body')
                if body:
                    body_copy = body.__copy__()
                    for unwanted in body_copy(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                        unwanted.decompose()
                    body_text = body_copy.get_text(strip=True, separator='\n\n')
                    if len(body_text) > len(best_content):
                        best_content = body_text
                        best_selector = 'body (fallback)'
            
            if best_content:
                article['content'] = best_content
                self.logger.info(f"Content found via {best_selector}: {len(best_content)} characters")
            
            # Extract metadata
            time_selectors = ['.bt_time', '.publish-time', '.date', '.time', '.pubtime']
            for selector in time_selectors:
                time_elem = soup.select_one(selector)
                if time_elem:
                    article['publish_time'] = time_elem.get_text(strip=True)
                    break
            
            source_selectors = ['.bt_source', '.source', '.author', '.from']
            for selector in source_selectors:
                source_elem = soup.select_one(selector)
                if source_elem:
                    article['source'] = source_elem.get_text(strip=True)
                    break
            
            # Fallback for missing title - use page title or first heading
            if not article['title']:
                title_elem = soup.find('title')
                if title_elem:
                    article['title'] = title_elem.get_text(strip=True)
                    self.logger.info("Using page title as fallback")
            
            self.logger.info(f"Final article - Title: {article['title'][:50]}...")
            self.logger.info(f"Content length: {len(article['content'])} characters")
            
        except Exception as e:
            self.logger.error(f"Article parsing error: {e}")
        
        return article
    
    def generate_markdown(self, article: Dict[str, str]) -> str:
        """Generate clean markdown output"""
        self.logger.info("Generating markdown output...")
        
        # Clean title for filename
        safe_title = "".join(c for c in article['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
        if len(safe_title) > 100:
            safe_title = safe_title[:100] + "..."
        
        markdown_content = f"""# {article['title']}

**源链接:** {self.target_url}
**发布时间:** {article['publish_time']}
**来源:** {article['source']}
**提取时间:** {article['extraction_time']}
**提取方法:** Safari直接提取 (Production Ready)

---

{article['content']}

---

*此文档由CCDI Production Extractor自动生成*
*Generated by CCDI Production Extractor*
"""
        
        return markdown_content, safe_title
    
    def save_output(self, markdown_content: str, title: str) -> str:
        """Save markdown content to output directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ccdi_article_{timestamp}.md"
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            self.logger.info(f"Article saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save output: {e}")
            raise
    
    def extract_article(self) -> Tuple[bool, str]:
        """Main extraction workflow"""
        self.logger.info("Starting article extraction...")
        
        try:
            # Step 1: Check Safari
            if not self.check_safari_availability():
                return False, "Safari not available or permissions not granted"
            
            # Step 2: Navigate to URL
            if not self.navigate_to_url():
                return False, "Failed to navigate to URL"
            
            # Step 3: Wait for page load
            if not self.wait_for_page_load():
                self.logger.warning("Page load timeout - proceeding anyway")
            
            # Give extra time for dynamic content
            self.logger.info("Waiting for dynamic content to load...")
            time.sleep(5)
            
            # Step 4: Extract HTML
            html_content = self.extract_html_content()
            if not html_content:
                return False, "Failed to extract HTML content"
            
            # Step 5: Validate content
            validation = self.validate_content_quality(html_content)
            if not validation['is_valid']:
                error_msg = "Content validation failed"
                if validation['has_captcha']:
                    error_msg += " - CAPTCHA detected"
                if not validation['has_content']:
                    error_msg += " - No substantial content found"
                return False, error_msg
            
            # Step 6: Parse article
            article = self.parse_article_content(html_content)
            if not article['title'] or not article['content']:
                return False, "Failed to parse article content"
            
            # Step 7: Generate and save markdown
            markdown_content, title = self.generate_markdown(article)
            output_path = self.save_output(markdown_content, title)
            
            self.logger.info("Article extraction completed successfully!")
            return True, output_path
            
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            return False, str(e)

def main():
    """Main execution function"""
    print("=" * 70)
    print("CCDI Production Content Extractor")
    print("=" * 70)
    print("Production-ready solution for extracting CCDI website content")
    print("Uses Safari + AppleScript + BeautifulSoup architecture")
    print("=" * 70)
    
    # Configuration
    target_url = "https://www.ccdi.gov.cn/yaowenn/202509/t20250918_448431.html"
    output_dir = "/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher/output"
    
    print(f"Target URL: {target_url}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Create extractor
    extractor = CCDIProductionExtractor(target_url, output_dir)
    
    try:
        # Run extraction
        print("Starting extraction process...")
        success, result = extractor.extract_article()
        
        if success:
            print(f"\n✅ SUCCESS: Article extracted successfully!")
            print(f"📄 Output file: {result}")
            print(f"📁 Location: {output_dir}")
            print("\nExtraction completed. The markdown file is ready for use.")
            return 0
        else:
            print(f"\n❌ FAILED: {result}")
            print("\nPlease check the logs for more details.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Extraction interrupted by user")
        return 2
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        return 3

if __name__ == "__main__":
    sys.exit(main())