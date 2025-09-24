#!/usr/bin/env python3
"""
CCDI Extractor for Safari-based Content Extraction
=================================================

Site-specific extractor for CCDI (Central Commission for Discipline Inspection)
website content. Handles Chinese government content extraction with specialized
parsing for CCDI article structure.

Author: Web_Fetcher Team
Version: 1.0.0
"""

import re
from typing import Dict
from bs4 import BeautifulSoup
from datetime import datetime
from .base_extractor import BaseExtractor

class CCDIExtractor(BaseExtractor):
    """
    CCDI-specific Safari content extractor.
    
    Specialized for extracting content from ccdi.gov.cn with
    knowledge of CCDI page structure and content patterns.
    """
    
    def parse_content(self, html_content: str) -> Dict[str, str]:
        """
        Parse CCDI-specific content from HTML.
        
        Args:
            html_content (str): Raw HTML content from Safari
            
        Returns:
            Dict[str, str]: Parsed content with CCDI-specific structure
        """
        self.logger.info("Parsing CCDI content...")
        
        article = {
            'title': '',
            'content': '',
            'publish_time': '',
            'source': '',
            'author': '',
            'category': '',
            'tags': '',
            'summary': ''
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title with CCDI-specific selectors
            title_selectors = [
                'h1.bt_title',           # Primary CCDI title class
                'h1',                    # Standard h1
                '.article-title',        # Generic article title
                '.title',                # Generic title
                'title',                 # Page title fallback
                '.post-title',           # Blog-style title
                '.headline',             # News headline
                '[class*="title"]'       # Any class containing "title"
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    # Validate title quality
                    if (len(title_text) > 5 and 
                        '验证' not in title_text and 
                        'CAPTCHA' not in title_text and
                        '错误' not in title_text):
                        article['title'] = title_text
                        self.logger.info(f"Title found via {selector}: {title_text[:50]}...")
                        break
            
            # Extract main content with CCDI-specific approach
            content_selectors = [
                '.bt_content',           # Primary CCDI content class
                '.TRS_Editor',           # TRS content management system
                '.article-content',      # Standard article content
                'article',               # HTML5 article element
                'main',                  # HTML5 main element
                '.content',              # Generic content class
                '.post-content',         # Blog-style content
                '.entry-content',        # WordPress-style content
                '.article-body',         # Article body
                '#content',              # Content by ID
                '[class*="content"]',    # Any class containing "content"
                '.text-content'          # Text content class
            ]
            
            best_content = ""
            best_selector = None
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Create a copy to avoid modifying original
                    elem_copy = content_elem.__copy__()
                    
                    # Clean unwanted elements
                    for unwanted in elem_copy(['script', 'style', 'nav', 'header', 
                                              'footer', 'aside', '.nav', '.navigation',
                                              '.share', '.social', '.related']):
                        unwanted.decompose()
                    
                    # Extract clean text with proper spacing
                    content_text = elem_copy.get_text(strip=True, separator='\n\n')
                    
                    # Clean up excessive whitespace
                    content_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', content_text)
                    content_text = re.sub(r'[ \t]+', ' ', content_text)
                    
                    if len(content_text) > len(best_content):
                        best_content = content_text
                        best_selector = selector
            
            # Fallback to body content if needed
            if len(best_content) < 200:
                body = soup.find('body')
                if body:
                    body_copy = body.__copy__()
                    # Remove more aggressive unwanted elements for body fallback
                    for unwanted in body_copy(['script', 'style', 'nav', 'header', 
                                              'footer', 'aside', '.nav', '.navigation',
                                              '.menu', '.sidebar', '.share', '.social']):
                        unwanted.decompose()
                    body_text = body_copy.get_text(strip=True, separator='\n\n')
                    
                    # Clean up body text
                    body_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', body_text)
                    body_text = re.sub(r'[ \t]+', ' ', body_text)
                    
                    if len(body_text) > len(best_content):
                        best_content = body_text
                        best_selector = 'body (fallback)'
            
            if best_content:
                article['content'] = best_content
                self.logger.info(f"Content found via {best_selector}: {len(best_content)} characters")
            
            # Extract publish time with CCDI-specific patterns
            time_selectors = [
                '.bt_time',              # CCDI time class
                '.publish-time',         # Generic publish time
                '.date',                 # Date class
                '.time',                 # Time class
                '.pubtime',              # Publication time
                '.create-time',          # Creation time
                '[class*="time"]',       # Any class containing "time"
                '[class*="date"]'        # Any class containing "date"
            ]
            
            for selector in time_selectors:
                time_elem = soup.select_one(selector)
                if time_elem:
                    time_text = time_elem.get_text(strip=True)
                    # Validate time format
                    if re.search(r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}', time_text):
                        article['publish_time'] = time_text
                        self.logger.info(f"Publish time found: {time_text}")
                        break
            
            # Extract source information
            source_selectors = [
                '.bt_source',            # CCDI source class
                '.source',               # Generic source
                '.author',               # Author information
                '.from',                 # Source/from information
                '.origin',               # Origin source
                '[class*="source"]',     # Any class containing "source"
                '[class*="author"]'      # Any class containing "author"
            ]
            
            for selector in source_selectors:
                source_elem = soup.select_one(selector)
                if source_elem:
                    source_text = source_elem.get_text(strip=True)
                    if len(source_text) > 0 and len(source_text) < 100:
                        article['source'] = source_text
                        self.logger.info(f"Source found: {source_text}")
                        break
            
            # Extract category/section information
            category_selectors = [
                '.breadcrumb',           # Breadcrumb navigation
                '.category',             # Category class
                '.section',              # Section class
                'nav .current',          # Current navigation item
                '.active'                # Active navigation
            ]
            
            for selector in category_selectors:
                category_elem = soup.select_one(selector)
                if category_elem:
                    category_text = category_elem.get_text(strip=True)
                    if len(category_text) > 0 and len(category_text) < 100:
                        article['category'] = category_text
                        break
            
            # Extract meta description as summary
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                article['summary'] = meta_desc.get('content').strip()
            
            # Fallback title extraction if none found
            if not article['title']:
                title_elem = soup.find('title')
                if title_elem:
                    page_title = title_elem.get_text(strip=True)
                    # Clean up page title
                    page_title = re.sub(r'\s*[-|_]\s*.*?网站?\s*$', '', page_title)
                    if len(page_title) > 5:
                        article['title'] = page_title
                        self.logger.info("Using cleaned page title as fallback")
            
            # Content quality validation
            content_length = len(article['content'])
            title_length = len(article['title'])
            
            self.logger.info(f"CCDI parsing results:")
            self.logger.info(f"  Title: {article['title'][:50]}... ({title_length} chars)")
            self.logger.info(f"  Content: {content_length} characters")
            self.logger.info(f"  Publish time: {article['publish_time']}")
            self.logger.info(f"  Source: {article['source']}")
            
            # Final content validation
            if not article['title'] and content_length < 100:
                self.logger.warning("Insufficient content extracted from CCDI page")
            
        except Exception as e:
            self.logger.error(f"CCDI content parsing error: {e}")
            # Return partial results even if parsing fails
        
        return article
    
    def format_output(self, parsed_content: Dict[str, str]) -> str:
        """
        Format parsed CCDI content for output.
        
        Args:
            parsed_content (Dict[str, str]): Parsed content
            
        Returns:
            str: Formatted markdown content
        """
        self.logger.info("Formatting CCDI content as markdown...")
        
        # Prepare metadata
        title = parsed_content.get('title', 'CCDI文章')
        content = parsed_content.get('content', '')
        publish_time = parsed_content.get('publish_time', '')
        source = parsed_content.get('source', 'CCDI')
        category = parsed_content.get('category', '')
        summary = parsed_content.get('summary', '')
        
        # Format extraction time
        extraction_time = self.extraction_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Build markdown content
        markdown_parts = []
        
        # Title
        markdown_parts.append(f"# {title}")
        markdown_parts.append("")
        
        # Metadata section
        metadata_lines = [
            "## 文章信息",
            "",
            f"**源链接:** {self.url}",
            f"**发布时间:** {publish_time}",
            f"**来源:** {source}",
        ]
        
        if category:
            metadata_lines.append(f"**分类:** {category}")
        
        if summary:
            metadata_lines.append(f"**摘要:** {summary}")
        
        metadata_lines.extend([
            f"**提取时间:** {extraction_time}",
            f"**提取方法:** Safari自动化提取 (CCDI专用)",
            ""
        ])
        
        markdown_parts.extend(metadata_lines)
        
        # Separator
        markdown_parts.append("---")
        markdown_parts.append("")
        
        # Main content
        if content:
            # Clean and format content
            content = content.strip()
            
            # Add some basic paragraph formatting
            content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Clean excessive newlines
            content = re.sub(r'^　+', '', content, flags=re.MULTILINE)  # Remove Chinese indentation
            
            markdown_parts.append("## 正文内容")
            markdown_parts.append("")
            markdown_parts.append(content)
            markdown_parts.append("")
        else:
            markdown_parts.append("*内容提取失败*")
            markdown_parts.append("")
        
        # Footer
        markdown_parts.extend([
            "---",
            "",
            "*此文档由Web_Fetcher Safari提取系统自动生成*",
            f"*提取器: CCDIExtractor | 提取时间: {extraction_time}*"
        ])
        
        markdown_content = "\n".join(markdown_parts)
        
        self.logger.info(f"Formatted markdown: {len(markdown_content)} characters")
        
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
    test_url = "https://www.ccdi.gov.cn/yaowenn/202509/t20250918_448431.html"
    
    print(f"Testing CCDI Extractor with URL: {test_url}")
    print("=" * 60)
    
    extractor = CCDIExtractor(test_url)
    
    try:
        success, content, metadata = extractor.extract()
        
        if success:
            print("✅ CCDI extraction successful!")
            print(f"Content length: {len(content)} characters")
            print(f"Metadata: {metadata}")
            
            # Save test output
            output_file = f"/tmp/ccdi_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Test output saved to: {output_file}")
        else:
            print("❌ CCDI extraction failed!")
            print(f"Error: {content}")
            
    except Exception as e:
        print(f"💥 Test failed with exception: {e}")
    
    print("=" * 60)
    print("CCDI extractor testing completed")