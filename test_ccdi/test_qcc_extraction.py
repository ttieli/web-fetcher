#!/usr/bin/env python3
"""
QCC.com Safari Extraction Test
==============================

Test script to validate whether the Safari extraction solution can handle
qcc.com website without modifying core webfetcher code.

This script analyzes qcc.com anti-scraping measures and tests Safari extraction
capabilities on the target URL.

Target URL: https://news.qcc.com/postnews/7588330b53d07872c37bd92842647deb.html

Author: Archy-Principle-Architect
Version: 1.0
Date: 2025-09-23
"""

import sys
import time
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import urllib.request
import urllib.error
from bs4 import BeautifulSoup

# Add parent directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# Import the CCDI extractor (will be extended for QCC)
from ccdi_production_extractor import CCDIProductionExtractor

class QCCAnalyzer:
    """Analyze QCC.com website characteristics and anti-scraping measures"""
    
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.analysis_results = {}
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def test_direct_access(self) -> Dict[str, Any]:
        """Test direct HTTP access to identify blocking mechanisms"""
        self.logger.info("Testing direct HTTP access to QCC.com...")
        
        results = {
            'accessible': False,
            'status_code': None,
            'error': None,
            'headers': {},
            'content_length': 0,
            'indicators': []
        }
        
        try:
            # Try with standard user agent
            req = urllib.request.Request(
                self.target_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                results['accessible'] = True
                results['status_code'] = response.status
                results['headers'] = dict(response.headers)
                
                html = response.read().decode('utf-8', errors='ignore')
                results['content_length'] = len(html)
                
                # Check for anti-scraping indicators
                indicators = []
                
                # Common anti-bot patterns
                anti_bot_patterns = [
                    'captcha', 'seccaptcha', '验证码', '滑动验证',
                    'cloudflare', 'cf-ray', 'challenge-form',
                    'robot', 'bot-check', 'access denied',
                    'forbidden', 'blocked', '请先完成验证',
                    'antibot', 'security-check', 'verify human'
                ]
                
                html_lower = html.lower()
                for pattern in anti_bot_patterns:
                    if pattern in html_lower:
                        indicators.append(f"Found '{pattern}' in content")
                
                # Check for JavaScript-heavy loading
                if 'window.location' in html or 'document.location' in html:
                    indicators.append("JavaScript redirect detected")
                
                if html.count('<script') > 20:
                    indicators.append(f"Heavy JavaScript usage ({html.count('<script')} script tags)")
                
                # Check for empty or minimal content
                soup = BeautifulSoup(html, 'html.parser')
                text_content = soup.get_text(strip=True)
                
                if len(text_content) < 500:
                    indicators.append(f"Minimal text content ({len(text_content)} chars)")
                
                results['indicators'] = indicators
                
                # Save sample for analysis
                sample_file = SCRIPT_DIR / 'qcc_direct_sample.html'
                with open(sample_file, 'w', encoding='utf-8') as f:
                    f.write(html)
                self.logger.info(f"Saved direct access sample to {sample_file}")
                
        except urllib.error.HTTPError as e:
            results['status_code'] = e.code
            results['error'] = f"HTTP Error {e.code}: {e.reason}"
            results['indicators'].append(f"HTTP {e.code} error")
            
        except Exception as e:
            results['error'] = str(e)
            results['indicators'].append(f"Access failed: {type(e).__name__}")
        
        return results
    
    def analyze_domain_characteristics(self) -> Dict[str, Any]:
        """Analyze QCC.com domain and URL patterns"""
        self.logger.info("Analyzing QCC.com domain characteristics...")
        
        from urllib.parse import urlparse
        parsed = urlparse(self.target_url)
        
        return {
            'domain': parsed.netloc,
            'path': parsed.path,
            'scheme': parsed.scheme,
            'is_news_section': 'news' in parsed.path,
            'is_dynamic_content': 'pageSource=dynamic' in self.target_url,
            'content_id': '7588330b53d07872c37bd92842647deb',
            'likely_requires_login': False,  # Will be determined by tests
            'business_data_site': True,  # QCC is a business information platform
            'chinese_content': True
        }


class QCCSafariExtractor(CCDIProductionExtractor):
    """Extended Safari extractor for QCC.com content"""
    
    def __init__(self, target_url: str, output_dir: str):
        super().__init__(target_url, output_dir)
        self.logger.info("QCC Safari Extractor initialized")
    
    def extract_with_analysis(self) -> Dict[str, Any]:
        """Extract content with detailed analysis for QCC"""
        results = {
            'extraction_successful': False,
            'content': None,
            'metrics': {},
            'quality_analysis': {},
            'errors': []
        }
        
        start_time = time.time()
        
        try:
            # Step 1: Check Safari availability
            if not self.check_safari_availability():
                results['errors'].append("Safari not available")
                return results
            
            # Step 2: Navigate to URL
            if not self.navigate_to_url():
                results['errors'].append("Failed to navigate to URL")
                return results
            
            # Step 3: Wait for page load
            if not self.wait_for_page_load(timeout=60):
                self.logger.warning("Page load timeout - proceeding anyway")
            
            # Step 4: Additional wait for dynamic content
            self.logger.info("Waiting for dynamic content to load...")
            time.sleep(5)
            
            # Step 5: Extract HTML content
            html_content = self.extract_html_content()
            if not html_content:
                results['errors'].append("No HTML content extracted")
                return results
            
            results['metrics']['extraction_time'] = time.time() - start_time
            results['metrics']['html_size'] = len(html_content)
            
            # Step 6: Parse and analyze content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for article content
            article_content = None
            
            # Try common article selectors
            selectors = [
                'article',
                '[class*="article"]',
                '[class*="content"]',
                '[class*="news"]',
                '[id*="content"]',
                '[class*="detail"]',
                'main',
                '.main-content'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if len(text) > 100:  # Meaningful content
                        article_content = element
                        self.logger.info(f"Found article content with selector: {selector}")
                        break
            
            if article_content:
                # Extract text and metadata
                results['content'] = {
                    'title': None,
                    'text': article_content.get_text(separator='\n', strip=True),
                    'html': str(article_content)
                }
                
                # Try to find title
                title_element = soup.find('h1') or soup.find('title')
                if title_element:
                    results['content']['title'] = title_element.get_text(strip=True)
                
                results['extraction_successful'] = True
                
                # Quality analysis
                validation = self.validate_content_quality(html_content)
                results['quality_analysis'] = validation
                
                # Save extracted content
                output_file = self.output_dir / f"qcc_extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                self.logger.info(f"Extraction results saved to {output_file}")
                
            else:
                results['errors'].append("Could not locate article content in page")
                
                # Save raw HTML for debugging
                debug_file = self.output_dir / f"qcc_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.logger.info(f"Debug HTML saved to {debug_file}")
                
        except Exception as e:
            results['errors'].append(f"Extraction error: {str(e)}")
            self.logger.error(f"Extraction failed: {e}")
        
        results['metrics']['total_time'] = time.time() - start_time
        return results


def test_qcc_safari_extraction():
    """Main test function for QCC.com Safari extraction"""
    
    target_url = "https://news.qcc.com/postnews/7588330b53d07872c37bd92842647deb.html?pageSource=dynamic"
    output_dir = SCRIPT_DIR / "qcc_test_output"
    output_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*80)
    print("QCC.COM SAFARI EXTRACTION TEST")
    print("="*80)
    print(f"Target URL: {target_url}")
    print(f"Output Directory: {output_dir}")
    print("-"*80)
    
    # Phase 1: Analyze QCC.com characteristics
    print("\n[Phase 1] Analyzing QCC.com website characteristics...")
    analyzer = QCCAnalyzer(target_url)
    
    # Test direct access
    direct_access = analyzer.test_direct_access()
    print(f"\nDirect Access Test:")
    print(f"  - Accessible: {direct_access['accessible']}")
    print(f"  - Status Code: {direct_access['status_code']}")
    print(f"  - Content Length: {direct_access['content_length']} bytes")
    
    if direct_access['indicators']:
        print(f"  - Anti-scraping indicators detected:")
        for indicator in direct_access['indicators']:
            print(f"    • {indicator}")
    
    # Analyze domain
    domain_info = analyzer.analyze_domain_characteristics()
    print(f"\nDomain Analysis:")
    print(f"  - Domain: {domain_info['domain']}")
    print(f"  - News Section: {domain_info['is_news_section']}")
    print(f"  - Dynamic Content: {domain_info['is_dynamic_content']}")
    print(f"  - Business Data Site: {domain_info['business_data_site']}")
    
    # Phase 2: Test Safari extraction
    print("\n[Phase 2] Testing Safari extraction...")
    extractor = QCCSafariExtractor(target_url, str(output_dir))
    
    results = extractor.extract_with_analysis()
    
    print(f"\nSafari Extraction Results:")
    print(f"  - Successful: {results['extraction_successful']}")
    print(f"  - Extraction Time: {results['metrics'].get('extraction_time', 0):.2f}s")
    print(f"  - HTML Size: {results['metrics'].get('html_size', 0)} bytes")
    
    if results['extraction_successful'] and results['content']:
        print(f"  - Title: {results['content'].get('title', 'N/A')}")
        print(f"  - Text Length: {len(results['content'].get('text', ''))} chars")
        
        # Show snippet
        text = results['content'].get('text', '')
        if text:
            snippet = text[:200] + "..." if len(text) > 200 else text
            print(f"  - Content Snippet: {snippet}")
    
    if results['quality_analysis']:
        print(f"\nContent Quality Analysis:")
        qa = results['quality_analysis']
        print(f"  - Has CAPTCHA: {qa.get('has_captcha', False)}")
        print(f"  - Has Content: {qa.get('has_content', False)}")
        print(f"  - Word Count: {qa.get('word_count', 0)}")
        print(f"  - Link Count: {qa.get('link_count', 0)}")
    
    if results['errors']:
        print(f"\nErrors Encountered:")
        for error in results['errors']:
            print(f"  - {error}")
    
    # Phase 3: Generate recommendation
    print("\n[Phase 3] Generating recommendations...")
    
    recommendation = {
        'can_use_safari': results['extraction_successful'],
        'requires_modification': False,
        'trigger_patterns': [],
        'notes': []
    }
    
    if results['extraction_successful']:
        recommendation['trigger_patterns'] = [
            'qcc.com',
            'news.qcc.com',
            'pageSource=dynamic'
        ]
        recommendation['notes'].append("QCC.com can be successfully extracted using Safari")
        
        if direct_access['indicators']:
            recommendation['notes'].append("Direct access shows anti-scraping measures that Safari bypasses")
    else:
        recommendation['notes'].append("Safari extraction failed - may need additional configuration")
    
    # Save comprehensive test report
    report = {
        'test_date': datetime.now().isoformat(),
        'target_url': target_url,
        'direct_access_analysis': direct_access,
        'domain_analysis': domain_info,
        'safari_extraction_results': results,
        'recommendation': recommendation
    }
    
    report_file = output_dir / f"qcc_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"Full report saved to: {report_file}")
    print(f"{'='*80}")
    
    return report


if __name__ == "__main__":
    test_qcc_safari_extraction()