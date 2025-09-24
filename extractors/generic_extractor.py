#!/usr/bin/env python3
"""
Generic Extractor for Safari-based Content Extraction
====================================================

Generic site extractor for Safari-based content extraction.
Provides fallback extraction capability for sites that are not
specifically configured but may benefit from Safari automation.

Author: Web_Fetcher Team
Version: 1.0.0
"""

import re
from typing import Dict
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse
from .base_extractor import BaseExtractor

class GenericExtractor(BaseExtractor):
    """
    Generic Safari content extractor.
    
    Provides best-effort content extraction for any website
    using common HTML patterns and heuristics.
    """
    
    def parse_content(self, html_content: str) -> Dict[str, str]:
        """
        Parse generic content from HTML using common patterns.
        
        Args:
            html_content (str): Raw HTML content from Safari
            
        Returns:
            Dict[str, str]: Parsed content with generic structure
        """
        self.logger.info("Parsing content with generic extractor...")
        
        article = {
            'title': '',
            'content': '',
            'author': '',
            'publish_time': '',
            'description': '',
            'keywords': '',
            'site_name': ''
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title using multiple strategies
            title = self._extract_title(soup)
            article['title'] = title
            
            # Extract main content
            content = self._extract_main_content(soup)
            article['content'] = content
            
            # Extract metadata
            self._extract_metadata(soup, article)
            
            # Extract publication time
            pub_time = self._extract_publish_time(soup)
            article['publish_time'] = pub_time
            
            # Extract author information
            author = self._extract_author(soup)
            article['author'] = author
            
            # Get site name from URL
            try:
                parsed_url = urlparse(self.url)
                article['site_name'] = parsed_url.netloc
            except:
                pass
            
            content_length = len(article['content'])
            self.logger.info(f"Generic parsing results:")
            self.logger.info(f"  Title: {article['title'][:50]}...")
            self.logger.info(f"  Content: {content_length} characters")
            self.logger.info(f"  Author: {article['author']}")
            self.logger.info(f"  Publish time: {article['publish_time']}")
            
        except Exception as e:
            self.logger.error(f"Generic content parsing error: {e}")
        
        return article
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title using multiple strategies."""
        # Strategy 1: Look for common title selectors
        title_selectors = [
            'h1',                    # Most common main heading
            '.title',                # Common title class
            '.headline',             # News-style headline
            '.post-title',           # Blog post title
            '.article-title',        # Article title
            '.entry-title',          # Entry title
            'h2',                    # Secondary heading
            '.page-title',           # Page title
            '[class*="title"]',      # Any class containing "title"
            'title'                  # Page title (fallback)
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # Validate title quality
                if (len(title_text) > 3 and 
                    len(title_text) < 200 and
                    '验证' not in title_text and 
                    'CAPTCHA' not in title_text and
                    'Error' not in title_text and
                    '404' not in title_text):
                    self.logger.info(f"Title found via {selector}: {title_text[:50]}...")
                    return title_text
        
        # Strategy 2: Use page title as fallback
        title_elem = soup.find('title')
        if title_elem:
            page_title = title_elem.get_text(strip=True)
            # Clean common website suffixes
            cleaned_title = re.sub(r'\s*[-|_]\s*[^-|_]*\.(com|org|net|gov|cn|co).*$', '', page_title)
            if len(cleaned_title) > 3:
                return cleaned_title
            return page_title
        
        return "提取的网页内容"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content using content detection heuristics."""
        # Strategy 1: Look for semantic content containers
        content_selectors = [
            'article',               # HTML5 article element
            'main',                  # HTML5 main element
            '.content',              # Generic content class
            '.post-content',         # Blog post content
            '.article-content',      # Article content
            '.entry-content',        # Entry content
            '.article-body',         # Article body
            '.post-body',            # Post body
            '#content',              # Content by ID
            '.text-content',         # Text content
            '[class*="content"]',    # Any class containing "content"
            '[role="main"]',         # Main role attribute
            '.container'             # Container class
        ]
        
        best_content = ""
        best_selector = None
        best_score = 0
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                elem_copy = content_elem.__copy__()
                
                # Remove unwanted elements
                for unwanted in elem_copy(['script', 'style', 'nav', 'header', 
                                          'footer', 'aside', '.nav', '.navigation',
                                          '.menu', '.sidebar', '.share', '.social',
                                          '.advertisement', '.ad', '.comments']):
                    unwanted.decompose()
                
                # Extract text
                content_text = elem_copy.get_text(strip=True, separator='\n\n')
                
                # Clean up text
                content_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', content_text)
                content_text = re.sub(r'[ \t]+', ' ', content_text)
                
                # Score content quality
                score = self._score_content_quality(content_text)
                
                if score > best_score:
                    best_content = content_text
                    best_selector = selector
                    best_score = score
        
        # Strategy 2: Fallback to body content
        if len(best_content) < 100:
            body = soup.find('body')
            if body:
                body_copy = body.__copy__()
                
                # More aggressive cleaning for body fallback
                for unwanted in body_copy(['script', 'style', 'nav', 'header', 
                                          'footer', 'aside', '.nav', '.navigation',
                                          '.menu', '.sidebar', '.share', '.social',
                                          '.advertisement', '.ad', '.comments',
                                          '.related', '.popup', '.modal']):
                    unwanted.decompose()
                
                body_text = body_copy.get_text(strip=True, separator='\n\n')
                body_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', body_text)
                body_text = re.sub(r'[ \t]+', ' ', body_text)
                
                if len(body_text) > len(best_content):
                    best_content = body_text
                    best_selector = 'body (fallback)'
        
        if best_content:
            self.logger.info(f"Content found via {best_selector}: {len(best_content)} characters")
        
        return best_content
    
    def _score_content_quality(self, text: str) -> int:
        """Score content quality based on various heuristics."""
        score = 0
        
        # Length scoring
        length = len(text)
        if length > 1000:
            score += 5
        elif length > 500:
            score += 3
        elif length > 200:
            score += 2
        elif length > 100:
            score += 1
        
        # Paragraph structure (newlines indicate structure)
        paragraphs = text.count('\n\n')
        if paragraphs > 3:
            score += 2
        elif paragraphs > 1:
            score += 1
        
        # Sentence structure (periods indicate complete sentences)
        sentences = text.count('。') + text.count('.') + text.count('！') + text.count('?')
        if sentences > 10:
            score += 2
        elif sentences > 5:
            score += 1
        
        # Penalize if it looks like navigation or error content
        nav_indicators = ['首页', '导航', '菜单', '登录', '注册', '404', 'Error', 'Not Found']
        for indicator in nav_indicators:
            if indicator in text:
                score -= 2
        
        return score
    
    def _extract_metadata(self, soup: BeautifulSoup, article: Dict[str, str]):
        """Extract metadata from HTML meta tags."""
        try:
            # Description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                article['description'] = meta_desc.get('content').strip()
            
            # Keywords
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords and meta_keywords.get('content'):
                article['keywords'] = meta_keywords.get('content').strip()
            
            # Open Graph data
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            if og_desc and og_desc.get('content') and not article['description']:
                article['description'] = og_desc.get('content').strip()
            
        except Exception as e:
            self.logger.warning(f"Error extracting metadata: {e}")
    
    def _extract_publish_time(self, soup: BeautifulSoup) -> str:
        """Extract publication time using various strategies."""
        # Look for time-related selectors
        time_selectors = [
            'time',                  # HTML5 time element
            '.date',                 # Date class
            '.publish-date',         # Publish date
            '.post-date',            # Post date
            '.article-date',         # Article date
            '.entry-date',           # Entry date
            '.time',                 # Time class
            '[datetime]',            # Elements with datetime attribute
            '[class*="date"]',       # Any class containing "date"
            '[class*="time"]'        # Any class containing "time"
        ]
        
        for selector in time_selectors:
            time_elem = soup.select_one(selector)
            if time_elem:
                # Try datetime attribute first
                datetime_attr = time_elem.get('datetime')
                if datetime_attr:
                    return datetime_attr
                
                # Fall back to text content
                time_text = time_elem.get_text(strip=True)
                if re.search(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}', time_text):
                    return time_text
        
        # Look for date patterns in text
        page_text = soup.get_text()
        date_patterns = [
            r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?\s*\d{1,2}:\d{2}',  # Full datetime
            r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?',                 # Date only
            r'\d{1,2}月\d{1,2}日',                                   # Month-day Chinese
            r'\d{1,2}/\d{1,2}/\d{4}',                               # MM/DD/YYYY
            r'\d{4}/\d{1,2}/\d{1,2}'                                # YYYY/MM/DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, page_text)
            if match:
                return match.group(0)
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author information."""
        # Look for author-related selectors
        author_selectors = [
            '.author',               # Author class
            '.byline',               # Byline
            '.post-author',          # Post author
            '.article-author',       # Article author
            '.writer',               # Writer
            '[class*="author"]',     # Any class containing "author"
            '[rel="author"]'         # Author relationship
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_text = author_elem.get_text(strip=True)
                if len(author_text) > 0 and len(author_text) < 100:
                    # Clean common prefixes
                    author_text = re.sub(r'^(作者|by|author)[：:\s]*', '', author_text, flags=re.IGNORECASE)
                    return author_text
        
        return ""
    
    def format_output(self, parsed_content: Dict[str, str]) -> str:
        """
        Format parsed generic content for output.
        
        Args:
            parsed_content (Dict[str, str]): Parsed content
            
        Returns:
            str: Formatted markdown content
        """
        self.logger.info("Formatting generic content as markdown...")
        
        # Prepare data
        title = parsed_content.get('title', '网页内容')
        content = parsed_content.get('content', '')
        author = parsed_content.get('author', '')
        publish_time = parsed_content.get('publish_time', '')
        description = parsed_content.get('description', '')
        site_name = parsed_content.get('site_name', '')
        
        # Format extraction time
        extraction_time = self.extraction_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Build markdown content
        markdown_parts = []
        
        # Title
        markdown_parts.append(f"# {title}")
        markdown_parts.append("")
        
        # Metadata section
        markdown_parts.extend([
            "## 页面信息",
            "",
            f"**源链接:** {self.url}"
        ])
        
        if site_name:
            markdown_parts.append(f"**网站:** {site_name}")
        
        if author:
            markdown_parts.append(f"**作者:** {author}")
        
        if publish_time:
            markdown_parts.append(f"**发布时间:** {publish_time}")
        
        if description:
            markdown_parts.append(f"**描述:** {description}")
        
        markdown_parts.extend([
            f"**提取时间:** {extraction_time}",
            f"**提取方法:** Safari自动化提取 (通用模式)",
            ""
        ])
        
        # Separator
        markdown_parts.append("---")
        markdown_parts.append("")
        
        # Main content
        if content:
            markdown_parts.extend([
                "## 页面内容",
                "",
                content.strip(),
                ""
            ])
        else:
            markdown_parts.extend([
                "*无法提取到有效内容*",
                ""
            ])
        
        # Footer
        markdown_parts.extend([
            "---",
            "",
            "*此文档由Web_Fetcher Safari提取系统自动生成*",
            f"*提取器: GenericExtractor | 提取时间: {extraction_time}*"
        ])
        
        markdown_content = "\n".join(markdown_parts)
        
        self.logger.info(f"Formatted generic markdown: {len(markdown_content)} characters")
        
        return markdown_content

# Testing
if __name__ == "__main__":
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test URL
    test_url = "https://example.com/test-article"
    
    print(f"Testing Generic Extractor with URL: {test_url}")
    print("=" * 60)
    
    extractor = GenericExtractor(test_url)
    
    try:
        success, content, metadata = extractor.extract()
        
        if success:
            print("✅ Generic extraction successful!")
            print(f"Content length: {len(content)} characters")
            print(f"Metadata: {metadata}")
            
            # Save test output
            output_file = f"/tmp/generic_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Test output saved to: {output_file}")
        else:
            print("❌ Generic extraction failed!")
            print(f"Error: {content}")
            
    except Exception as e:
        print(f"💥 Test failed with exception: {e}")
    
    print("=" * 60)
    print("Generic extractor testing completed")