#!/usr/bin/env python3
"""
QCC Extractor for Safari-based Content Extraction
================================================

Site-specific extractor for QCC (企查查) website content.
Handles Chinese business information extraction with specialized
parsing for QCC company profile structure.

Author: Web_Fetcher Team
Version: 1.0.0
"""

import re
import json
from typing import Dict
from bs4 import BeautifulSoup
from datetime import datetime
from .base_extractor import BaseExtractor

class QCCExtractor(BaseExtractor):
    """
    QCC-specific Safari content extractor.
    
    Specialized for extracting content from qcc.com with
    knowledge of QCC page structure and business data patterns.
    """
    
    def parse_content(self, html_content: str) -> Dict[str, str]:
        """
        Parse QCC-specific content from HTML.
        
        Args:
            html_content (str): Raw HTML content from Safari
            
        Returns:
            Dict[str, str]: Parsed content with QCC-specific structure
        """
        self.logger.info("Parsing QCC content...")
        
        article = {
            'title': '',
            'content': '',
            'company_name': '',
            'company_status': '',
            'registration_number': '',
            'legal_representative': '',
            'registered_capital': '',
            'establishment_date': '',
            'business_scope': '',
            'address': '',
            'contact_info': '',
            'industry': '',
            'company_type': ''
        }
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract company name (title)
            title_selectors = [
                'h1.company-name',       # QCC company name class
                'h1',                    # Standard h1
                '.company-title',        # Company title class
                '.enterprise-name',      # Enterprise name
                '.firm-name',            # Firm name
                'title',                 # Page title fallback
                '[class*="name"]'        # Any class containing "name"
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    # Validate title quality (avoid CAPTCHA pages)
                    if (len(title_text) > 2 and 
                        '验证' not in title_text and 
                        'CAPTCHA' not in title_text and
                        '滑动' not in title_text and
                        '错误' not in title_text):
                        article['title'] = title_text
                        article['company_name'] = title_text
                        self.logger.info(f"Company name found via {selector}: {title_text}")
                        break
            
            # Extract main content - QCC has structured data
            content_parts = []
            
            # Try to extract structured company information
            info_selectors = [
                '.company-info',         # Company info section
                '.enterprise-info',      # Enterprise info
                '.basic-info',           # Basic information
                '.company-detail',       # Company details
                '.firm-info',            # Firm information
                'main',                  # Main content area
                '.content'               # Generic content
            ]
            
            main_content = ""
            for selector in info_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Clean unwanted elements
                    elem_copy = content_elem.__copy__()
                    for unwanted in elem_copy(['script', 'style', 'nav', 'header', 
                                              'footer', 'aside', '.advertisement',
                                              '.ad', '.share', '.social']):
                        unwanted.decompose()
                    
                    content_text = elem_copy.get_text(strip=True, separator='\n')
                    if len(content_text) > len(main_content):
                        main_content = content_text
            
            # Extract specific business data fields
            self._extract_business_fields(soup, article)
            
            # Build comprehensive content from extracted fields
            if article['company_name']:
                content_parts.append(f"企业名称：{article['company_name']}")
            
            if article['company_status']:
                content_parts.append(f"企业状态：{article['company_status']}")
            
            if article['legal_representative']:
                content_parts.append(f"法定代表人：{article['legal_representative']}")
            
            if article['registered_capital']:
                content_parts.append(f"注册资本：{article['registered_capital']}")
            
            if article['establishment_date']:
                content_parts.append(f"成立日期：{article['establishment_date']}")
            
            if article['registration_number']:
                content_parts.append(f"统一社会信用代码：{article['registration_number']}")
            
            if article['company_type']:
                content_parts.append(f"企业类型：{article['company_type']}")
            
            if article['industry']:
                content_parts.append(f"所属行业：{article['industry']}")
            
            if article['address']:
                content_parts.append(f"注册地址：{article['address']}")
            
            if article['business_scope']:
                content_parts.append(f"经营范围：{article['business_scope']}")
            
            # Combine structured data with main content
            if content_parts:
                structured_content = '\n\n'.join(content_parts)
                if main_content and main_content not in structured_content:
                    article['content'] = structured_content + '\n\n' + main_content
                else:
                    article['content'] = structured_content
            else:
                article['content'] = main_content
            
            # Fallback title extraction
            if not article['title']:
                title_elem = soup.find('title')
                if title_elem:
                    page_title = title_elem.get_text(strip=True)
                    # Clean up QCC page title
                    page_title = re.sub(r'\s*[-|_]\s*(企查查|qcc\.com).*$', '', page_title)
                    if len(page_title) > 2:
                        article['title'] = page_title
                        if not article['company_name']:
                            article['company_name'] = page_title
                        self.logger.info("Using cleaned page title as fallback")
            
            content_length = len(article['content'])
            self.logger.info(f"QCC parsing results:")
            self.logger.info(f"  Company: {article['company_name']}")
            self.logger.info(f"  Content: {content_length} characters")
            self.logger.info(f"  Status: {article['company_status']}")
            
        except Exception as e:
            self.logger.error(f"QCC content parsing error: {e}")
        
        return article
    
    def _extract_business_fields(self, soup: BeautifulSoup, article: Dict[str, str]):
        """Extract specific business information fields from QCC page."""
        try:
            # Look for structured data in various formats
            
            # Method 1: Try JSON-LD structured data
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        if 'name' in data and not article['company_name']:
                            article['company_name'] = data['name']
                        if 'legalName' in data and not article['company_name']:
                            article['company_name'] = data['legalName']
                        if 'address' in data and not article['address']:
                            if isinstance(data['address'], dict):
                                article['address'] = data['address'].get('streetAddress', '')
                            else:
                                article['address'] = str(data['address'])
                except json.JSONDecodeError:
                    continue
            
            # Method 2: Look for specific data fields with common patterns
            field_patterns = {
                'company_status': [r'企业状态[：:\s]*([^）\n]+)', r'状态[：:\s]*([^）\n]+)'],
                'legal_representative': [r'法定代表人[：:\s]*([^）\n]+)', r'法人[：:\s]*([^）\n]+)'],
                'registered_capital': [r'注册资本[：:\s]*([^）\n]+)', r'资本[：:\s]*([^）\n]+万元)'],
                'establishment_date': [r'成立日期[：:\s]*([0-9\-年月日]+)', r'成立时间[：:\s]*([0-9\-年月日]+)'],
                'registration_number': [r'统一社会信用代码[：:\s]*([A-Z0-9]+)', r'注册号[：:\s]*([A-Z0-9]+)'],
                'company_type': [r'企业类型[：:\s]*([^）\n]+)', r'公司类型[：:\s]*([^）\n]+)'],
                'industry': [r'所属行业[：:\s]*([^）\n]+)', r'行业[：:\s]*([^）\n]+)']
            }
            
            page_text = soup.get_text()
            for field, patterns in field_patterns.items():
                if not article[field]:  # Only extract if not already found
                    for pattern in patterns:
                        match = re.search(pattern, page_text)
                        if match:
                            article[field] = match.group(1).strip()
                            break
            
            # Method 3: Look for specific CSS classes or data attributes
            field_selectors = {
                'company_status': ['.company-status', '.status', '[data-status]'],
                'legal_representative': ['.legal-person', '.legal-rep', '.representative'],
                'registered_capital': ['.capital', '.register-capital', '.reg-capital'],
                'establishment_date': ['.establish-date', '.found-date', '.create-date'],
                'registration_number': ['.credit-code', '.reg-number', '.license-number'],
                'address': ['.address', '.company-address', '.reg-address'],
                'business_scope': ['.business-scope', '.scope', '.business-range']
            }
            
            for field, selectors in field_selectors.items():
                if not article[field]:  # Only extract if not already found
                    for selector in selectors:
                        elem = soup.select_one(selector)
                        if elem:
                            text = elem.get_text(strip=True)
                            if len(text) > 0 and len(text) < 500:  # Reasonable length
                                article[field] = text
                                break
            
            # Extract business scope (often longer text)
            if not article['business_scope']:
                scope_patterns = [r'经营范围[：:\s]*([^。\n]{20,})', r'业务范围[：:\s]*([^。\n]{20,})']
                for pattern in scope_patterns:
                    match = re.search(pattern, page_text)
                    if match:
                        scope_text = match.group(1).strip()
                        if len(scope_text) > 10:
                            article['business_scope'] = scope_text
                            break
            
        except Exception as e:
            self.logger.warning(f"Error extracting business fields: {e}")
    
    def format_output(self, parsed_content: Dict[str, str]) -> str:
        """
        Format parsed QCC content for output.
        
        Args:
            parsed_content (Dict[str, str]): Parsed content
            
        Returns:
            str: Formatted markdown content
        """
        self.logger.info("Formatting QCC content as markdown...")
        
        # Prepare data
        company_name = parsed_content.get('company_name', parsed_content.get('title', '企业信息'))
        content = parsed_content.get('content', '')
        
        # Format extraction time
        extraction_time = self.extraction_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Build markdown content
        markdown_parts = []
        
        # Title
        markdown_parts.append(f"# {company_name}")
        markdown_parts.append("")
        
        # Metadata section
        markdown_parts.extend([
            "## 企业基本信息",
            "",
            f"**源链接:** {self.url}",
            f"**提取时间:** {extraction_time}",
            f"**提取方法:** Safari自动化提取 (QCC专用)",
            ""
        ])
        
        # Business information table
        business_info = []
        info_fields = [
            ('企业名称', 'company_name'),
            ('企业状态', 'company_status'),
            ('法定代表人', 'legal_representative'),
            ('注册资本', 'registered_capital'),
            ('成立日期', 'establishment_date'),
            ('统一社会信用代码', 'registration_number'),
            ('企业类型', 'company_type'),
            ('所属行业', 'industry'),
            ('注册地址', 'address')
        ]
        
        for label, field in info_fields:
            value = parsed_content.get(field, '').strip()
            if value:
                business_info.append(f"| {label} | {value} |")
        
        if business_info:
            markdown_parts.extend([
                "### 企业详情",
                "",
                "| 项目 | 内容 |",
                "|------|------|"
            ])
            markdown_parts.extend(business_info)
            markdown_parts.append("")
        
        # Business scope section
        business_scope = parsed_content.get('business_scope', '').strip()
        if business_scope:
            markdown_parts.extend([
                "### 经营范围",
                "",
                business_scope,
                ""
            ])
        
        # Separator
        markdown_parts.append("---")
        markdown_parts.append("")
        
        # Additional content
        if content and content.strip():
            markdown_parts.extend([
                "## 详细信息",
                "",
                content.strip(),
                ""
            ])
        
        # Footer
        markdown_parts.extend([
            "---",
            "",
            "*此文档由Web_Fetcher Safari提取系统自动生成*",
            f"*提取器: QCCExtractor | 提取时间: {extraction_time}*",
            "*数据来源: 企查查 (qcc.com)*"
        ])
        
        markdown_content = "\n".join(markdown_parts)
        
        self.logger.info(f"Formatted QCC markdown: {len(markdown_content)} characters")
        
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
    test_url = "https://www.qcc.com/firm/abc123test"
    
    print(f"Testing QCC Extractor with URL: {test_url}")
    print("=" * 60)
    
    extractor = QCCExtractor(test_url)
    
    try:
        success, content, metadata = extractor.extract()
        
        if success:
            print("✅ QCC extraction successful!")
            print(f"Content length: {len(content)} characters")
            print(f"Metadata: {metadata}")
            
            # Save test output
            output_file = f"/tmp/qcc_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Test output saved to: {output_file}")
        else:
            print("❌ QCC extraction failed!")
            print(f"Error: {content}")
            
    except Exception as e:
        print(f"💥 Test failed with exception: {e}")
    
    print("=" * 60)
    print("QCC extractor testing completed")