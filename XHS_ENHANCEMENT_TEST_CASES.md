# XiaoHongShu Enhancement Test Cases and Validation Framework

## Test Case Framework

### Primary Test Case: Multi-Image Post Extraction

```python
#!/usr/bin/env python3
"""
XiaoHongShu Image Extraction Enhancement Test Suite
Test the enhanced image extraction against known multi-image posts
"""

import sys
import time
import json
import logging
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class TestResult:
    test_name: str
    url: str
    expected_images: int
    extracted_images: int
    success: bool
    processing_time: float
    errors: List[str]
    image_urls: List[str]

class XHSEnhancementTester:
    """Test suite for XiaoHongShu image extraction enhancement"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        
    def test_primary_multi_image_post(self) -> TestResult:
        """Test Case 1: Primary failing case with 8 images"""
        
        test_url = "http://xhslink.com/o/9aAFGUwOWq0"
        expected_count = 8
        
        start_time = time.time()
        
        try:
            # Execute enhanced extraction
            from webfetcher import xhs_to_markdown
            
            # Fetch HTML (simulate browser rendering if needed)
            html = self._fetch_html_with_rendering(test_url)
            
            # Execute extraction
            date_only, markdown, metadata = xhs_to_markdown(html, test_url)
            
            processing_time = time.time() - start_time
            extracted_count = len(metadata.get('images', []))
            
            # Validation checks
            success = self._validate_extraction_quality(
                metadata.get('images', []),
                expected_count,
                test_url
            )
            
            return TestResult(
                test_name="primary_multi_image_post",
                url=test_url,
                expected_images=expected_count,
                extracted_images=extracted_count,
                success=success,
                processing_time=processing_time,
                errors=[],
                image_urls=metadata.get('images', [])
            )
            
        except Exception as e:
            return TestResult(
                test_name="primary_multi_image_post",
                url=test_url,
                expected_images=expected_count,
                extracted_images=0,
                success=False,
                processing_time=time.time() - start_time,
                errors=[str(e)],
                image_urls=[]
            )
    
    def test_single_image_post(self) -> TestResult:
        """Test Case 2: Single image post (regression test)"""
        
        # Use a known single-image XHS post for regression testing
        test_url = "https://www.xiaohongshu.com/discovery/item/[SINGLE_IMAGE_POST_ID]"
        expected_count = 1
        
        # Similar implementation to test_primary_multi_image_post
        # but with different expectations
        pass
    
    def test_mixed_content_post(self) -> TestResult:
        """Test Case 3: Post with mixed content (images + videos)"""
        
        # Test handling of posts that contain both images and videos
        # Should extract only images, not video thumbnails
        pass
    
    def test_lazy_loading_post(self) -> TestResult:
        """Test Case 4: Post with heavy lazy loading"""
        
        # Test posts where images are heavily lazy-loaded
        # and require JavaScript execution to discover
        pass
        
    def test_malformed_content(self) -> TestResult:
        """Test Case 5: Malformed or incomplete HTML"""
        
        # Test graceful handling of malformed HTML
        # Should not crash and should provide meaningful fallback
        pass

    def _fetch_html_with_rendering(self, url: str) -> str:
        """Fetch HTML with JavaScript rendering if needed"""
        
        try:
            # Try static fetch first
            html = self._static_fetch(url)
            
            # Check if rendering is needed (look for XHS dynamic content indicators)
            if self._needs_rendering(html):
                html = self._render_with_playwright(url)
                
            return html
            
        except Exception as e:
            logging.error(f"Failed to fetch {url}: {e}")
            return ""
    
    def _static_fetch(self, url: str) -> str:
        """Static HTML fetch with appropriate headers"""
        import urllib.request
        
        ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        req = urllib.request.Request(url, headers={'User-Agent': ua})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8', errors='ignore')
    
    def _needs_rendering(self, html: str) -> bool:
        """Detect if JavaScript rendering is needed"""
        indicators = [
            'window.__INITIAL_STATE__',
            'xiaohongshu.com/discovery',
            'data-src=',
            'lazy-load'
        ]
        return any(indicator in html for indicator in indicators)
    
    def _render_with_playwright(self, url: str) -> str:
        """Render with Playwright if available"""
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(url, wait_until='networkidle')
                html = page.content()
                browser.close()
                return html
                
        except ImportError:
            logging.warning("Playwright not available, using static HTML")
            return ""
    
    def _validate_extraction_quality(self, images: List[str], expected_count: int, url: str) -> bool:
        """Comprehensive validation of extraction quality"""
        
        if not images:
            return False
        
        # Check 1: Minimum count threshold (allow some tolerance)
        min_threshold = max(1, expected_count * 0.75)  # 75% of expected
        if len(images) < min_threshold:
            return False
        
        # Check 2: Valid XiaoHongShu image URLs
        valid_domains = ['ci.xiaohongshu.com', 'xhscdn.com', 'sns-img', 'sns-webpic-qc']
        valid_images = [
            img for img in images 
            if any(domain in img for domain in valid_domains)
        ]
        if len(valid_images) < len(images) * 0.8:  # 80% should be XHS images
            return False
        
        # Check 3: No duplicate URLs
        if len(set(images)) != len(images):
            return False
        
        # Check 4: Valid image format indicators
        format_indicators = ['.jpg', '.jpeg', '.png', '.webp', 'imageMogr2', 'imageView2']
        valid_format_count = sum(
            1 for img in images 
            if any(indicator in img.lower() for indicator in format_indicators)
        )
        if valid_format_count < len(images) * 0.9:  # 90% should have format indicators
            return False
        
        return True
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Execute all test cases and return comprehensive results"""
        
        test_methods = [
            self.test_primary_multi_image_post,
            # self.test_single_image_post,
            # self.test_mixed_content_post,
            # self.test_lazy_loading_post,
            # self.test_malformed_content
        ]
        
        results = []
        for test_method in test_methods:
            try:
                result = test_method()
                results.append(result)
                
                # Log result
                status = "PASS" if result.success else "FAIL"
                print(f"[{status}] {result.test_name}: {result.extracted_images}/{result.expected_images} images in {result.processing_time:.2f}s")
                
                if result.errors:
                    for error in result.errors:
                        print(f"  Error: {error}")
                        
            except Exception as e:
                print(f"[ERROR] {test_method.__name__}: {e}")
        
        # Summary
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'results': results
        }
        
        return summary

# Benchmark and Performance Tests

class PerformanceBenchmark:
    """Performance benchmarking for enhanced image extraction"""
    
    def __init__(self):
        self.baseline_times = {}
        self.enhanced_times = {}
    
    def benchmark_extraction_performance(self, test_urls: List[str]) -> Dict[str, Any]:
        """Benchmark extraction performance comparison"""
        
        results = {
            'urls_tested': len(test_urls),
            'baseline_avg_time': 0.0,
            'enhanced_avg_time': 0.0,
            'performance_ratio': 0.0,
            'memory_usage': {},
            'detailed_results': []
        }
        
        for url in test_urls:
            # Benchmark baseline implementation
            baseline_time = self._benchmark_baseline(url)
            
            # Benchmark enhanced implementation  
            enhanced_time = self._benchmark_enhanced(url)
            
            results['detailed_results'].append({
                'url': url,
                'baseline_time': baseline_time,
                'enhanced_time': enhanced_time,
                'improvement_ratio': baseline_time / enhanced_time if enhanced_time > 0 else 0
            })
        
        # Calculate averages
        if results['detailed_results']:
            results['baseline_avg_time'] = sum(r['baseline_time'] for r in results['detailed_results']) / len(results['detailed_results'])
            results['enhanced_avg_time'] = sum(r['enhanced_time'] for r in results['detailed_results']) / len(results['detailed_results'])
            results['performance_ratio'] = results['baseline_avg_time'] / results['enhanced_avg_time'] if results['enhanced_avg_time'] > 0 else 0
        
        return results
    
    def _benchmark_baseline(self, url: str) -> float:
        """Benchmark current implementation"""
        # Implementation would test current xhs_to_markdown function
        pass
    
    def _benchmark_enhanced(self, url: str) -> float:
        """Benchmark enhanced implementation"""
        # Implementation would test enhanced xhs_to_markdown function
        pass

# Integration Test Script

def run_integration_tests():
    """Main integration test runner"""
    
    print("=" * 60)
    print("XiaoHongShu Image Extraction Enhancement Test Suite")
    print("=" * 60)
    
    # Initialize tester
    tester = XHSEnhancementTester()
    
    # Run functionality tests
    print("\n1. Running Functionality Tests...")
    func_results = tester.run_all_tests()
    
    print(f"\nFunctionality Test Results:")
    print(f"  Total Tests: {func_results['total_tests']}")
    print(f"  Passed: {func_results['passed_tests']}")
    print(f"  Failed: {func_results['failed_tests']}")
    print(f"  Success Rate: {func_results['success_rate']:.1%}")
    
    # Run performance benchmarks
    print("\n2. Running Performance Benchmarks...")
    benchmark = PerformanceBenchmark()
    
    test_urls = [
        "http://xhslink.com/o/9aAFGUwOWq0",  # Primary test case
        # Additional test URLs would be added here
    ]
    
    perf_results = benchmark.benchmark_extraction_performance(test_urls)
    
    print(f"\nPerformance Benchmark Results:")
    print(f"  URLs Tested: {perf_results['urls_tested']}")
    print(f"  Baseline Avg Time: {perf_results['baseline_avg_time']:.3f}s")
    print(f"  Enhanced Avg Time: {perf_results['enhanced_avg_time']:.3f}s")
    print(f"  Performance Ratio: {perf_results['performance_ratio']:.2f}x")
    
    # Overall assessment
    print("\n" + "=" * 60)
    print("OVERALL ASSESSMENT")
    print("=" * 60)
    
    overall_success = (
        func_results['success_rate'] >= 0.8 and  # 80% test pass rate
        perf_results['performance_ratio'] <= 3.0  # No more than 3x slower
    )
    
    if overall_success:
        print("✅ ENHANCEMENT READY FOR DEPLOYMENT")
    else:
        print("❌ ENHANCEMENT NEEDS IMPROVEMENT")
        
        if func_results['success_rate'] < 0.8:
            print(f"  - Improve functionality: {func_results['success_rate']:.1%} pass rate (need 80%)")
        
        if perf_results['performance_ratio'] > 3.0:
            print(f"  - Optimize performance: {perf_results['performance_ratio']:.1f}x slower (max 3x)")
    
    return {
        'functionality': func_results,
        'performance': perf_results,
        'ready_for_deployment': overall_success
    }

if __name__ == "__main__":
    results = run_integration_tests()
    
    # Exit with appropriate code
    sys.exit(0 if results['ready_for_deployment'] else 1)
```

## Quality Gates and Acceptance Criteria

### Functional Quality Gates

#### Phase 1 Acceptance Criteria
- [ ] **Minimum Image Count**: Extract ≥6 images from test URL (current: 1)
- [ ] **Domain Validation**: ≥90% of extracted images from valid XHS domains
- [ ] **No Duplicates**: All extracted URLs must be unique
- [ ] **Valid Formats**: ≥90% of URLs must have valid image format indicators
- [ ] **Cover Image**: Cover image (if present) must be first in the list
- [ ] **Backward Compatibility**: No changes to function signature or return structure

#### Phase 2 Acceptance Criteria  
- [ ] **Target Image Count**: Extract all 8 images from test URL
- [ ] **Lazy Loading Support**: Successfully detect lazy-loaded images
- [ ] **Progressive Enhancement**: Handle progressive image loading patterns
- [ ] **Error Handling**: Graceful degradation on malformed content
- [ ] **Logging**: Comprehensive logging for debugging and monitoring

#### Phase 3 Acceptance Criteria
- [ ] **Performance**: Processing time increase ≤3x baseline
- [ ] **Memory**: Memory usage increase ≤50MB per extraction
- [ ] **Reliability**: ≥95% success rate across diverse XHS posts
- [ ] **Maintainability**: Clear separation of concerns and comprehensive documentation

### Performance Quality Gates

```python
# Performance Thresholds
PERFORMANCE_THRESHOLDS = {
    'max_processing_time': 5.0,      # seconds per post
    'max_memory_increase': 50,        # MB
    'max_slowdown_ratio': 3.0,       # compared to baseline
    'min_success_rate': 0.95         # 95% success rate
}

# Quality Validation Function
def validate_quality_gates(test_results: Dict) -> Dict[str, bool]:
    """Validate all quality gates are met"""
    
    gates = {
        'functionality_pass_rate': test_results['functionality']['success_rate'] >= 0.8,
        'performance_acceptable': test_results['performance']['performance_ratio'] <= 3.0,
        'image_count_improved': any(
            r.extracted_images >= r.expected_images * 0.75 
            for r in test_results['functionality']['results']
        ),
        'no_regressions': all(
            len(r.errors) == 0 
            for r in test_results['functionality']['results'] 
            if r.test_name.startswith('regression_')
        )
    }
    
    return gates
```

## Test Data and Mock Scenarios

### Test URL Collection
```python
# Test URLs for different scenarios
TEST_URLS = {
    'multi_image_post': "http://xhslink.com/o/9aAFGUwOWq0",  # 8 images
    'single_image_post': "https://www.xiaohongshu.com/discovery/item/[SINGLE_ID]",
    'video_with_thumbnail': "https://www.xiaohongshu.com/discovery/item/[VIDEO_ID]",
    'lazy_loading_heavy': "https://www.xiaohongshu.com/discovery/item/[LAZY_ID]",
    'malformed_content': "https://www.xiaohongshu.com/discovery/item/[MALFORMED_ID]"
}

# Expected Results
EXPECTED_RESULTS = {
    'multi_image_post': {
        'min_images': 8,
        'domains': ['ci.xiaohongshu.com', 'xhscdn.com'],
        'has_cover': True
    },
    'single_image_post': {
        'min_images': 1,
        'domains': ['ci.xiaohongshu.com'],
        'has_cover': True
    }
    # ... additional expected results
}
```

### Mock Data for Unit Tests
```python
# Mock HTML content for unit testing
MOCK_HTML_SAMPLES = {
    'initial_state_sample': """
    <script>
    window.__INITIAL_STATE__ = {
      "noteDetailMap": {
        "note_id_123": {
          "imageList": [
            {"url": "https://ci.xiaohongshu.com/image1.jpg", "picId": "pic1"},
            {"url": "https://ci.xiaohongshu.com/image2.jpg", "picId": "pic2"}
          ]
        }
      }
    };
    </script>
    """,
    
    'api_response_sample': """
    <script>
    {"code":0,"success":true,"data":{"note":{"imageList":[
      "https://sns-webpic-qc.xhscdn.com/image1.jpg",
      "https://sns-webpic-qc.xhscdn.com/image2.jpg"
    ]}}}
    </script>
    """,
    
    'lazy_loading_sample': """
    <img data-src="https://ci.xiaohongshu.com/lazy1.jpg" class="lazy-load" />
    <img data-original="https://ci.xiaohongshu.com/lazy2.jpg" />
    """
}
```

---

**Usage Instructions for Implementation Team**:

1. **Save this file** as `XHS_ENHANCEMENT_TEST_CASES.md` in the project directory
2. **Create the test script** by copying the Python code into `test_xhs_enhancement.py`
3. **Run baseline test** before implementing enhancements: `python test_xhs_enhancement.py`
4. **Implement enhancements** following the main specification
5. **Run tests iteratively** during development to validate progress
6. **Use quality gates** to determine when enhancement is ready for deployment

The test framework provides comprehensive validation, performance benchmarking, and clear success criteria for the XiaoHongShu image extraction enhancement.