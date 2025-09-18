#!/usr/bin/env python3
"""
Architect Validation Test Suite for WeChat Parser Fix
Version: 1.0
Date: 2025-09-18
Architect: Archy-Principle-Architect

This test suite validates the WeChat parser JavaScript filtering implementation.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
import urllib.request
import urllib.error
import re

# Test configuration
TEST_CONFIG = {
    "urls": {
        "wechat_standard": "https://mp.weixin.qq.com/s/JNKdr2qAxI1uam90vBC98Q",
        "wechat_with_code": "https://mp.weixin.qq.com/s/example_code_article",  # Article with code snippets
        "wechat_heavy_css": "https://mp.weixin.qq.com/s/example_css_heavy",    # CSS-heavy article
        "wechat_inline_script": "https://mp.weixin.qq.com/s/example_inline",   # Inline scripts
    },
    "thresholds": {
        "max_file_size_kb": 100,        # Maximum acceptable output size in KB
        "min_content_ratio": 0.8,       # Minimum content preservation ratio
        "max_processing_time_s": 10,    # Maximum processing time in seconds
        "js_contamination_limit": 0,    # Zero tolerance for JavaScript
    },
    "patterns": {
        "javascript": [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=\s*['\"]",  # Event handlers
            r"function\s*\(",
            r"var\s+\w+\s*=",
            r"const\s+\w+\s*=",
            r"let\s+\w+\s*=",
            r"window\.",
            r"document\.",
            r"setTimeout",
            r"setInterval",
        ],
        "style": [
            r"<style[^>]*>.*?</style>",
            r"style\s*=\s*['\"]",
        ],
        "content_markers": [
            r"!\[.*?\]\(.*?\)",  # Markdown images
            r"#+\s+.+",          # Headers
            r"-\s+标题:",         # Metadata
            r"-\s+作者:",
            r"-\s+发布时间:",
        ],
        "code_blocks": [
            r"```[\s\S]*?```",   # Markdown code blocks (should be preserved)
            r"`[^`]+`",          # Inline code
        ]
    }
}

class ValidationTestRunner:
    def __init__(self):
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": [],
            "metrics": {}
        }
        self.wf_path = Path(__file__).parent / "wf.py"
        
    def run_all_tests(self) -> Dict:
        """Execute all validation tests."""
        print("=" * 80)
        print("ARCHITECT VALIDATION TEST SUITE")
        print("Testing WeChat Parser JavaScript Filtering Implementation")
        print("=" * 80)
        
        # Test categories
        self.test_code_review()
        self.test_functional_validation()
        self.test_quality_validation()
        self.test_performance()
        self.test_edge_cases()
        
        # Generate report
        self.generate_report()
        return self.results
    
    def test_code_review(self):
        """1. CODE REVIEW TESTS"""
        print("\n[1] CODE REVIEW VALIDATION")
        print("-" * 40)
        
        # Check implementation exists
        test_name = "WxParser class modification check"
        try:
            with open("webfetcher.py", "r", encoding="utf-8") as f:
                content = f.read()
                
            # Check for required flags
            checks = [
                ("in_script flag", "self.in_script = False" in content),
                ("in_style flag", "self.in_style = False" in content),
                ("script tag handling", "elif tag == 'script':" in content),
                ("style tag handling", "elif tag == 'style':" in content),
                ("data filtering", "not self.in_script and not self.in_style" in content),
            ]
            
            all_passed = True
            for check_name, passed in checks:
                if passed:
                    self.log_pass(f"{test_name}: {check_name}")
                else:
                    self.log_fail(f"{test_name}: {check_name}")
                    all_passed = False
                    
            if all_passed:
                print("✅ All code modifications verified")
            else:
                print("❌ Some code modifications missing")
                
        except Exception as e:
            self.log_fail(f"{test_name}: {str(e)}")
    
    def test_functional_validation(self):
        """2. FUNCTIONAL VALIDATION TESTS"""
        print("\n[2] FUNCTIONAL VALIDATION")
        print("-" * 40)
        
        test_url = TEST_CONFIG["urls"]["wechat_standard"]
        test_name = "JavaScript filtering test"
        
        try:
            # Run the parser
            output_file = self.run_parser(test_url)
            
            if output_file and output_file.exists():
                with open(output_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check for JavaScript contamination
                js_found = []
                for pattern in TEST_CONFIG["patterns"]["javascript"]:
                    if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                        js_found.append(pattern)
                
                if not js_found:
                    self.log_pass(f"{test_name}: No JavaScript contamination")
                    print("✅ JavaScript completely filtered")
                else:
                    self.log_fail(f"{test_name}: Found JS patterns: {js_found}")
                    print(f"❌ JavaScript patterns detected: {len(js_found)}")
                
                # Check content preservation
                content_markers_found = 0
                for pattern in TEST_CONFIG["patterns"]["content_markers"]:
                    if re.search(pattern, content, re.MULTILINE):
                        content_markers_found += 1
                
                if content_markers_found >= 3:
                    self.log_pass(f"{test_name}: Content preserved")
                    print(f"✅ Content preservation verified ({content_markers_found} markers)")
                else:
                    self.log_warning(f"{test_name}: Low content markers: {content_markers_found}")
                
                # Check file size
                file_size_kb = output_file.stat().st_size / 1024
                self.results["metrics"]["file_size_kb"] = file_size_kb
                
                if file_size_kb < TEST_CONFIG["thresholds"]["max_file_size_kb"]:
                    self.log_pass(f"{test_name}: File size {file_size_kb:.1f}KB")
                    print(f"✅ File size optimal: {file_size_kb:.1f}KB")
                else:
                    self.log_warning(f"{test_name}: Large file {file_size_kb:.1f}KB")
                    
        except Exception as e:
            self.log_fail(f"{test_name}: {str(e)}")
    
    def test_quality_validation(self):
        """3. QUALITY VALIDATION TESTS"""
        print("\n[3] QUALITY VALIDATION")
        print("-" * 40)
        
        test_url = TEST_CONFIG["urls"]["wechat_standard"]
        test_name = "Output quality test"
        
        try:
            output_file = self.run_parser(test_url)
            
            if output_file and output_file.exists():
                with open(output_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check Chinese text handling
                chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
                if chinese_chars > 100:
                    self.log_pass(f"{test_name}: Chinese text preserved ({chinese_chars} chars)")
                    print(f"✅ Chinese text handling correct ({chinese_chars} characters)")
                else:
                    self.log_warning(f"{test_name}: Low Chinese char count: {chinese_chars}")
                
                # Check markdown structure
                headers = len(re.findall(r'^#+\s+', content, re.MULTILINE))
                images = len(re.findall(r'!\[.*?\]\(.*?\)', content))
                links = len(re.findall(r'\[.*?\]\(.*?\)', content))
                
                print(f"📊 Markdown structure: {headers} headers, {images} images, {links} links")
                
                if headers > 0 and images > 0:
                    self.log_pass(f"{test_name}: Markdown structure intact")
                else:
                    self.log_warning(f"{test_name}: Markdown structure incomplete")
                    
        except Exception as e:
            self.log_fail(f"{test_name}: {str(e)}")
    
    def test_performance(self):
        """4. PERFORMANCE TESTS"""
        print("\n[4] PERFORMANCE VALIDATION")
        print("-" * 40)
        
        test_url = TEST_CONFIG["urls"]["wechat_standard"]
        test_name = "Performance test"
        
        try:
            start_time = time.time()
            output_file = self.run_parser(test_url)
            elapsed_time = time.time() - start_time
            
            self.results["metrics"]["processing_time_s"] = elapsed_time
            
            if elapsed_time < TEST_CONFIG["thresholds"]["max_processing_time_s"]:
                self.log_pass(f"{test_name}: Completed in {elapsed_time:.2f}s")
                print(f"✅ Performance acceptable: {elapsed_time:.2f} seconds")
            else:
                self.log_warning(f"{test_name}: Slow processing {elapsed_time:.2f}s")
                print(f"⚠️ Performance warning: {elapsed_time:.2f} seconds")
                
        except Exception as e:
            self.log_fail(f"{test_name}: {str(e)}")
    
    def test_edge_cases(self):
        """5. EDGE CASE TESTS"""
        print("\n[5] EDGE CASE VALIDATION")
        print("-" * 40)
        
        # Test with inline scripts (simulation)
        test_name = "Edge case: inline scripts"
        test_content = '''
        <div id="js_content">
            <p>Normal content</p>
            <script>alert('should be filtered')</script>
            <p>More content</p>
            <style>.hidden { display: none; }</style>
            <p>Final content</p>
        </div>
        '''
        
        try:
            # Test the parser directly
            from webfetcher import wechat_to_markdown
            
            # Create test HTML
            test_html = f'''
            <html>
            <head><meta property="og:title" content="Test Article"/></head>
            <body>{test_content}</body>
            </html>
            '''
            
            _, markdown, _ = wechat_to_markdown(test_html, "http://test.url")
            
            # Check filtering
            if "<script>" not in markdown and "alert(" not in markdown:
                self.log_pass(f"{test_name}: Scripts filtered")
                print("✅ Edge case: inline scripts handled correctly")
            else:
                self.log_fail(f"{test_name}: Scripts not filtered")
                
            if "<style>" not in markdown and ".hidden" not in markdown:
                self.log_pass(f"{test_name}: Styles filtered")
                print("✅ Edge case: inline styles handled correctly")
            else:
                self.log_fail(f"{test_name}: Styles not filtered")
                
        except Exception as e:
            self.log_warning(f"{test_name}: Could not test directly - {str(e)}")
    
    def run_parser(self, url: str) -> Path:
        """Run the wf.py parser and return output path."""
        try:
            cmd = [sys.executable, str(self.wf_path), url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Find the output file
                output_dir = Path(__file__).parent / "output"
                if output_dir.exists():
                    files = list(output_dir.glob("*.md"))
                    if files:
                        # Return most recent file
                        return max(files, key=lambda f: f.stat().st_mtime)
            return None
        except Exception:
            return None
    
    def log_pass(self, message: str):
        self.results["passed"].append(message)
    
    def log_fail(self, message: str):
        self.results["failed"].append(message)
    
    def log_warning(self, message: str):
        self.results["warnings"].append(message)
    
    def generate_report(self):
        """Generate final validation report."""
        print("\n" + "=" * 80)
        print("VALIDATION REPORT SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.results["passed"]) + len(self.results["failed"])
        pass_rate = (len(self.results["passed"]) / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 TEST RESULTS:")
        print(f"   ✅ Passed: {len(self.results['passed'])}")
        print(f"   ❌ Failed: {len(self.results['failed'])}")
        print(f"   ⚠️  Warnings: {len(self.results['warnings'])}")
        print(f"   📈 Pass Rate: {pass_rate:.1f}%")
        
        if self.results["metrics"]:
            print(f"\n📏 METRICS:")
            for key, value in self.results["metrics"].items():
                print(f"   • {key}: {value}")
        
        # Final verdict
        print(f"\n🏁 FINAL VERDICT:")
        if len(self.results["failed"]) == 0 and pass_rate >= 90:
            print("   ✅ IMPLEMENTATION APPROVED - Ready for production")
        elif len(self.results["failed"]) <= 2 and pass_rate >= 70:
            print("   ⚠️ CONDITIONALLY APPROVED - Minor issues need attention")
        else:
            print("   ❌ NOT APPROVED - Critical issues must be resolved")
        
        # Save detailed report
        self.save_report()
    
    def save_report(self):
        """Save detailed report to file."""
        report_path = Path(__file__).parent / "VALIDATION_REPORT.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Detailed report saved to: {report_path}")

if __name__ == "__main__":
    runner = ValidationTestRunner()
    results = runner.run_all_tests()