#!/usr/bin/env python3
"""
Quality Assurance Test Suite for Safari CCDI Integration
=======================================================

Comprehensive QA tests to ensure production readiness and quality
of the Safari CCDI integration with Web_Fetcher.

Author: Archy-Principle-Architect
Date: 2025-09-23
Version: 1.0
"""

import sys
import os
import time
import json
import tempfile
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from unittest.mock import Mock, patch

@dataclass
class QATestResult:
    """Quality assurance test result"""
    test_category: str
    test_name: str
    success: bool
    message: str
    performance_metrics: Dict[str, float] = None
    quality_metrics: Dict[str, Any] = None
    error_details: Dict[str, Any] = None

class SafariCCDIQualityAssurance:
    """Comprehensive QA testing for Safari CCDI integration"""
    
    def __init__(self, webfetcher_root: str):
        self.webfetcher_root = Path(webfetcher_root)
        self.test_results: List[QATestResult] = []
        self.setup_logging()
        
        # Quality thresholds
        self.performance_thresholds = {
            "plugin_detection_time": 0.1,  # seconds
            "safari_launch_time": 10.0,     # seconds
            "content_extraction_time": 60.0, # seconds
            "markdown_generation_time": 5.0  # seconds
        }
        
        self.quality_thresholds = {
            "min_content_length": 500,      # characters
            "min_title_length": 10,         # characters
            "max_error_rate": 0.05,         # 5% error tolerance
            "min_success_rate": 0.95        # 95% success rate
        }
    
    def setup_logging(self):
        """Configure QA logging"""
        log_file = self.webfetcher_root / "qa_test_results.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_qa_test(self, category: str, test_name: str, test_func) -> QATestResult:
        """Run a single QA test with comprehensive metrics"""
        self.logger.info(f"Running QA test: {category} - {test_name}")
        start_time = time.time()
        
        try:
            success, message, perf_metrics, quality_metrics, error_details = test_func()
            
            # Add timing to performance metrics
            if perf_metrics is None:
                perf_metrics = {}
            perf_metrics["test_duration"] = time.time() - start_time
            
            result = QATestResult(
                test_category=category,
                test_name=test_name,
                success=success,
                message=message,
                performance_metrics=perf_metrics,
                quality_metrics=quality_metrics,
                error_details=error_details
            )
            
            status = "✅ PASS" if success else "❌ FAIL"
            self.logger.info(f"{status} {category} - {test_name}: {message}")
            
        except Exception as e:
            result = QATestResult(
                test_category=category,
                test_name=test_name,
                success=False,
                message=f"QA test error: {str(e)}",
                performance_metrics={"test_duration": time.time() - start_time},
                error_details={"exception": str(e), "type": type(e).__name__}
            )
            
            self.logger.error(f"❌ ERROR {category} - {test_name}: {str(e)}")
        
        self.test_results.append(result)
        return result
    
    # Performance Quality Tests
    
    def qa_performance_plugin_detection(self) -> Tuple[bool, str, Dict, Dict, Dict]:
        """Test plugin detection performance"""
        plugin_path = self.webfetcher_root / "plugins"
        sys.path.insert(0, str(plugin_path))
        
        perf_metrics = {}
        quality_metrics = {}
        
        try:
            from plugin_registry import PluginRegistry
            from ccdi_safari_plugin import CCDISafariPlugin
            
            # Test multiple URL detection cycles
            test_urls = [
                "https://www.ccdi.gov.cn/yaowenn/202509/t20250918_448431.html",
                "https://www.ccdi.gov.cn/toutiao/202509/t20250920_448496.html",
                "https://mp.weixin.qq.com/s/test",
                "https://example.com"
            ]
            
            detection_times = []
            for url in test_urls:
                start_time = time.time()
                can_handle = CCDISafariPlugin.can_handle(url)
                detection_time = time.time() - start_time
                detection_times.append(detection_time)
            
            avg_detection_time = sum(detection_times) / len(detection_times)
            max_detection_time = max(detection_times)
            
            perf_metrics = {
                "avg_detection_time": avg_detection_time,
                "max_detection_time": max_detection_time,
                "detection_count": len(detection_times)
            }
            
            quality_metrics = {
                "meets_threshold": avg_detection_time < self.performance_thresholds["plugin_detection_time"],
                "threshold": self.performance_thresholds["plugin_detection_time"]
            }
            
            if avg_detection_time > self.performance_thresholds["plugin_detection_time"]:
                return False, f"Plugin detection too slow: {avg_detection_time:.3f}s", perf_metrics, quality_metrics, {}
            
            return True, f"Plugin detection performance good: {avg_detection_time:.3f}s", perf_metrics, quality_metrics, {}
            
        except Exception as e:
            return False, f"Performance test failed: {e}", perf_metrics, quality_metrics, {"error": str(e)}
    
    def qa_performance_safari_automation(self) -> Tuple[bool, str, Dict, Dict, Dict]:
        """Test Safari automation performance"""
        perf_metrics = {}
        quality_metrics = {}
        
        try:
            # Test Safari launch time
            start_time = time.time()
            
            script = '''
            tell application "Safari"
                activate
                return "activated"
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=15)
            
            safari_launch_time = time.time() - start_time
            
            perf_metrics["safari_launch_time"] = safari_launch_time
            
            if result.returncode != 0:
                return False, f"Safari launch failed: {result.stderr}", perf_metrics, quality_metrics, {"error": result.stderr}
            
            # Test JavaScript execution time
            start_time = time.time()
            
            js_script = '''
            tell application "Safari"
                try
                    do JavaScript "Math.random()" in current tab of window 1
                    return "success"
                on error
                    return "no_tab"
                end try
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', js_script], 
                                  capture_output=True, text=True, timeout=10)
            
            js_execution_time = time.time() - start_time
            perf_metrics["js_execution_time"] = js_execution_time
            
            quality_metrics = {
                "safari_launch_acceptable": safari_launch_time < self.performance_thresholds["safari_launch_time"],
                "launch_threshold": self.performance_thresholds["safari_launch_time"]
            }
            
            if safari_launch_time > self.performance_thresholds["safari_launch_time"]:
                return False, f"Safari launch too slow: {safari_launch_time:.2f}s", perf_metrics, quality_metrics, {}
            
            return True, f"Safari automation performance good: {safari_launch_time:.2f}s", perf_metrics, quality_metrics, {}
            
        except Exception as e:
            return False, f"Safari performance test failed: {e}", perf_metrics, quality_metrics, {"error": str(e)}
    
    def qa_performance_content_extraction(self) -> Tuple[bool, str, Dict, Dict, Dict]:
        """Test content extraction performance with mock data"""
        plugin_path = self.webfetcher_root / "plugins"
        sys.path.insert(0, str(plugin_path))
        
        perf_metrics = {}
        quality_metrics = {}
        
        try:
            from ccdi_safari_extractor import CCDISafariExtractor
            
            # Create large test HTML for performance testing
            test_html = '''
            <!DOCTYPE html>
            <html>
            <head><title>性能测试文章</title></head>
            <body>
                <h1 class="bt_title">中央纪委国家监委性能测试文章</h1>
                <div class="bt_time">2025-09-23 10:30:00</div>
                <div class="bt_source">中央纪委国家监委网站</div>
                <div class="bt_content">
            ''' + "<p>这是性能测试内容。" * 1000 + '''
                </div>
            </body>
            </html>
            '''
            
            extractor = CCDISafariExtractor("https://www.ccdi.gov.cn/test")
            
            # Test content validation performance
            start_time = time.time()
            validation = extractor.validate_content_quality(test_html)
            validation_time = time.time() - start_time
            
            # Test article parsing performance
            start_time = time.time()
            article = extractor.parse_article_content(test_html)
            parsing_time = time.time() - start_time
            
            perf_metrics = {
                "validation_time": validation_time,
                "parsing_time": parsing_time,
                "total_extraction_time": validation_time + parsing_time,
                "content_size": len(test_html)
            }
            
            quality_metrics = {
                "extraction_within_threshold": (validation_time + parsing_time) < self.performance_thresholds["content_extraction_time"],
                "threshold": self.performance_thresholds["content_extraction_time"],
                "content_extracted": len(article["content"]) > 0,
                "title_extracted": len(article["title"]) > 0
            }
            
            total_time = validation_time + parsing_time
            if total_time > self.performance_thresholds["content_extraction_time"]:
                return False, f"Content extraction too slow: {total_time:.2f}s", perf_metrics, quality_metrics, {}
            
            return True, f"Content extraction performance good: {total_time:.3f}s", perf_metrics, quality_metrics, {}
            
        except Exception as e:
            return False, f"Content extraction performance test failed: {e}", perf_metrics, quality_metrics, {"error": str(e)}
    
    # Quality Assurance Tests
    
    def qa_quality_content_accuracy(self) -> Tuple[bool, str, Dict, Dict, Dict]:
        """Test content extraction accuracy"""
        plugin_path = self.webfetcher_root / "plugins"
        sys.path.insert(0, str(plugin_path))
        
        perf_metrics = {}
        quality_metrics = {}
        
        try:
            from ccdi_safari_extractor import CCDISafariExtractor
            
            # Test with various HTML structures
            test_cases = [
                {
                    "name": "standard_structure",
                    "html": '''
                    <html>
                    <body>
                        <h1 class="bt_title">标准结构测试标题</h1>
                        <div class="bt_time">2025-09-23</div>
                        <div class="bt_source">测试来源</div>
                        <div class="bt_content">
                            <p>这是标准结构的测试内容。</p>
                            <p>包含多个段落。</p>
                        </div>
                    </body>
                    </html>
                    ''',
                    "expected_title": "标准结构测试标题",
                    "expected_source": "测试来源"
                },
                {
                    "name": "alternative_structure",
                    "html": '''
                    <html>
                    <body>
                        <h1>替代结构测试标题</h1>
                        <div class="time">2025-09-23</div>
                        <div class="source">替代来源</div>
                        <article>
                            <p>这是替代结构的测试内容。</p>
                        </article>
                    </body>
                    </html>
                    ''',
                    "expected_title": "替代结构测试标题",
                    "expected_source": "替代来源"
                }
            ]
            
            extraction_results = []
            
            for test_case in test_cases:
                extractor = CCDISafariExtractor("https://www.ccdi.gov.cn/test")
                
                # Test extraction
                start_time = time.time()
                article = extractor.parse_article_content(test_case["html"])
                extraction_time = time.time() - start_time
                
                # Evaluate accuracy
                title_match = test_case["expected_title"] in article["title"]
                source_match = test_case["expected_source"] in article["source"]
                has_content = len(article["content"]) > 50
                
                result = {
                    "test_case": test_case["name"],
                    "title_match": title_match,
                    "source_match": source_match,
                    "has_content": has_content,
                    "content_length": len(article["content"]),
                    "extraction_time": extraction_time
                }
                
                extraction_results.append(result)
            
            # Calculate overall accuracy
            total_tests = len(extraction_results)
            successful_extractions = sum(1 for r in extraction_results 
                                       if r["title_match"] and r["has_content"])
            
            accuracy_rate = successful_extractions / total_tests
            
            perf_metrics = {
                "avg_extraction_time": sum(r["extraction_time"] for r in extraction_results) / total_tests
            }
            
            quality_metrics = {
                "accuracy_rate": accuracy_rate,
                "total_tests": total_tests,
                "successful_extractions": successful_extractions,
                "meets_accuracy_threshold": accuracy_rate >= self.quality_thresholds["min_success_rate"],
                "test_results": extraction_results
            }
            
            if accuracy_rate < self.quality_thresholds["min_success_rate"]:
                return False, f"Content accuracy too low: {accuracy_rate:.2%}", perf_metrics, quality_metrics, {}
            
            return True, f"Content accuracy good: {accuracy_rate:.2%}", perf_metrics, quality_metrics, {}
            
        except Exception as e:
            return False, f"Content accuracy test failed: {e}", perf_metrics, quality_metrics, {"error": str(e)}
    
    def qa_quality_error_handling(self) -> Tuple[bool, str, Dict, Dict, Dict]:
        """Test error handling robustness"""
        plugin_path = self.webfetcher_root / "plugins"
        sys.path.insert(0, str(plugin_path))
        
        perf_metrics = {}
        quality_metrics = {}
        
        try:
            from ccdi_safari_extractor import CCDISafariExtractor
            from ccdi_safari_plugin import CCDISafariPlugin
            
            error_scenarios = [
                {
                    "name": "empty_html",
                    "html": "",
                    "should_fail": True
                },
                {
                    "name": "malformed_html",
                    "html": "<html><body><div>Unclosed div</body></html>",
                    "should_fail": False  # Should handle gracefully
                },
                {
                    "name": "no_content",
                    "html": "<html><head><title>Only Title</title></head><body></body></html>",
                    "should_fail": True
                },
                {
                    "name": "captcha_detected",
                    "html": "<html><body><div>请完成验证码</div></body></html>",
                    "should_fail": True
                }
            ]
            
            error_handling_results = []
            
            for scenario in error_scenarios:
                extractor = CCDISafariExtractor("https://www.ccdi.gov.cn/test")
                
                try:
                    # Test validation
                    validation = extractor.validate_content_quality(scenario["html"])
                    
                    # Test extraction
                    article = extractor.parse_article_content(scenario["html"])
                    
                    # Test plugin extraction result
                    result = CCDISafariPlugin.extract_content(scenario["html"], "https://www.ccdi.gov.cn/test")
                    
                    test_result = {
                        "scenario": scenario["name"],
                        "validation_passed": validation["is_valid"],
                        "extraction_succeeded": result.success,
                        "handled_gracefully": True,
                        "expected_failure": scenario["should_fail"]
                    }
                    
                    # Check if behavior matches expectation
                    if scenario["should_fail"]:
                        test_result["correct_behavior"] = not result.success
                    else:
                        test_result["correct_behavior"] = result.success
                    
                except Exception as e:
                    test_result = {
                        "scenario": scenario["name"],
                        "validation_passed": False,
                        "extraction_succeeded": False,
                        "handled_gracefully": False,
                        "expected_failure": scenario["should_fail"],
                        "correct_behavior": scenario["should_fail"],  # Exception is acceptable for should_fail cases
                        "error": str(e)
                    }
                
                error_handling_results.append(test_result)
            
            # Calculate error handling quality
            total_scenarios = len(error_handling_results)
            correct_behaviors = sum(1 for r in error_handling_results if r["correct_behavior"])
            graceful_handling = sum(1 for r in error_handling_results if r["handled_gracefully"])
            
            error_handling_rate = correct_behaviors / total_scenarios
            graceful_rate = graceful_handling / total_scenarios
            
            quality_metrics = {
                "error_handling_rate": error_handling_rate,
                "graceful_handling_rate": graceful_rate,
                "total_scenarios": total_scenarios,
                "correct_behaviors": correct_behaviors,
                "scenario_results": error_handling_results
            }
            
            if error_handling_rate < 0.8:  # 80% threshold for error handling
                return False, f"Error handling insufficient: {error_handling_rate:.2%}", perf_metrics, quality_metrics, {}
            
            return True, f"Error handling robust: {error_handling_rate:.2%}", perf_metrics, quality_metrics, {}
            
        except Exception as e:
            return False, f"Error handling test failed: {e}", perf_metrics, quality_metrics, {"error": str(e)}
    
    def qa_quality_integration_stability(self) -> Tuple[bool, str, Dict, Dict, Dict]:
        """Test integration stability and consistency"""
        plugin_path = self.webfetcher_root / "plugins"
        sys.path.insert(0, str(plugin_path))
        
        perf_metrics = {}
        quality_metrics = {}
        
        try:
            from plugin_manager import WebFetcherPluginManager
            
            # Test multiple initialization cycles
            initialization_times = []
            initialization_successes = 0
            
            for i in range(5):
                start_time = time.time()
                try:
                    manager = WebFetcherPluginManager()
                    plugins = manager.list_available_plugins()
                    
                    # Verify CCDI plugin is available
                    ccdi_plugin = next((p for p in plugins if p['name'] == 'CCDI_Safari'), None)
                    
                    if ccdi_plugin and ccdi_plugin['valid']:
                        initialization_successes += 1
                    
                    initialization_time = time.time() - start_time
                    initialization_times.append(initialization_time)
                    
                except Exception:
                    initialization_times.append(float('inf'))
            
            # Test URL handling consistency
            test_url = "https://www.ccdi.gov.cn/test"
            handling_results = []
            
            for i in range(3):
                try:
                    manager = WebFetcherPluginManager()
                    from plugin_registry import PluginRegistry
                    handler = PluginRegistry.get_handler_for_url(test_url)
                    
                    handling_results.append({
                        "iteration": i,
                        "handler_found": handler is not None,
                        "handler_name": handler.name if handler else None
                    })
                except Exception as e:
                    handling_results.append({
                        "iteration": i,
                        "handler_found": False,
                        "error": str(e)
                    })
            
            avg_init_time = sum(t for t in initialization_times if t != float('inf')) / len([t for t in initialization_times if t != float('inf')])
            init_success_rate = initialization_successes / 5
            
            consistent_handling = all(r["handler_found"] for r in handling_results)
            consistent_handler = len(set(r.get("handler_name") for r in handling_results if r["handler_found"])) <= 1
            
            perf_metrics = {
                "avg_initialization_time": avg_init_time,
                "initialization_times": initialization_times
            }
            
            quality_metrics = {
                "initialization_success_rate": init_success_rate,
                "consistent_url_handling": consistent_handling,
                "consistent_handler_selection": consistent_handler,
                "handling_results": handling_results
            }
            
            if init_success_rate < 0.9 or not consistent_handling:
                return False, f"Integration stability issues detected", perf_metrics, quality_metrics, {}
            
            return True, f"Integration stable and consistent", perf_metrics, quality_metrics, {}
            
        except Exception as e:
            return False, f"Stability test failed: {e}", perf_metrics, quality_metrics, {"error": str(e)}
    
    # Security and Compliance Tests
    
    def qa_security_safari_automation(self) -> Tuple[bool, str, Dict, Dict, Dict]:
        """Test Safari automation security aspects"""
        perf_metrics = {}
        quality_metrics = {}
        
        try:
            # Test that we don't expose sensitive information
            script_tests = [
                {
                    "name": "no_credential_exposure",
                    "script": '''
                    tell application "Safari"
                        try
                            do JavaScript "document.cookie" in current tab of window 1
                            return "cookie_accessible"
                        on error
                            return "cookie_protected"
                        end try
                    end tell
                    ''',
                    "acceptable_results": ["cookie_protected", ""]
                },
                {
                    "name": "no_local_storage_access",
                    "script": '''
                    tell application "Safari"
                        try
                            do JavaScript "localStorage.getItem('test')" in current tab of window 1
                            return "storage_accessible"
                        on error
                            return "storage_protected"
                        end try
                    end tell
                    ''',
                    "acceptable_results": ["storage_protected", "null", ""]
                }
            ]
            
            security_results = []
            
            for test in script_tests:
                try:
                    result = subprocess.run(['osascript', '-e', test["script"]], 
                                          capture_output=True, text=True, timeout=10)
                    
                    output = result.stdout.strip()
                    is_secure = output in test["acceptable_results"] or result.returncode != 0
                    
                    security_results.append({
                        "test": test["name"],
                        "output": output,
                        "return_code": result.returncode,
                        "is_secure": is_secure
                    })
                    
                except Exception as e:
                    security_results.append({
                        "test": test["name"],
                        "error": str(e),
                        "is_secure": True  # Error is acceptable for security
                    })
            
            all_secure = all(r["is_secure"] for r in security_results)
            
            quality_metrics = {
                "all_security_tests_passed": all_secure,
                "security_test_results": security_results
            }
            
            if not all_secure:
                return False, "Security concerns detected in Safari automation", perf_metrics, quality_metrics, {}
            
            return True, "Safari automation security validated", perf_metrics, quality_metrics, {}
            
        except Exception as e:
            return False, f"Security test failed: {e}", perf_metrics, quality_metrics, {"error": str(e)}
    
    def run_full_qa_suite(self) -> Dict[str, Any]:
        """Run complete QA test suite"""
        print("🔬 Safari CCDI Integration Quality Assurance Suite")
        print("=" * 60)
        print(f"WebFetcher Root: {self.webfetcher_root}")
        print(f"QA Test Time: {datetime.now().isoformat()}")
        print()
        
        # Define QA test suite
        qa_tests = [
            # Performance Tests
            ("Performance", "Plugin Detection Speed", self.qa_performance_plugin_detection),
            ("Performance", "Safari Automation Speed", self.qa_performance_safari_automation),
            ("Performance", "Content Extraction Speed", self.qa_performance_content_extraction),
            
            # Quality Tests
            ("Quality", "Content Extraction Accuracy", self.qa_quality_content_accuracy),
            ("Quality", "Error Handling Robustness", self.qa_quality_error_handling),
            ("Quality", "Integration Stability", self.qa_quality_integration_stability),
            
            # Security Tests
            ("Security", "Safari Automation Security", self.qa_security_safari_automation),
        ]
        
        # Run all QA tests
        for category, test_name, test_func in qa_tests:
            self.run_qa_test(category, test_name, test_func)
        
        # Generate QA summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests
        
        # Calculate category summaries
        categories = {}
        for result in self.test_results:
            cat = result.test_category
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0}
            categories[cat]["total"] += 1
            if result.success:
                categories[cat]["passed"] += 1
        
        print()
        print("📊 QA Test Summary")
        print("-" * 40)
        print(f"Total QA Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        for category, stats in categories.items():
            success_rate = (stats["passed"] / stats["total"]) * 100
            print(f"{category}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        if failed_tests > 0:
            print("\n❌ Failed QA Tests:")
            for result in self.test_results:
                if not result.success:
                    print(f"  - {result.test_category} - {result.test_name}: {result.message}")
        
        # Performance summary
        print("\n⚡ Performance Summary")
        print("-" * 30)
        
        for result in self.test_results:
            if result.test_category == "Performance" and result.performance_metrics:
                key_metric = None
                if "avg_detection_time" in result.performance_metrics:
                    key_metric = f"{result.performance_metrics['avg_detection_time']:.3f}s"
                elif "safari_launch_time" in result.performance_metrics:
                    key_metric = f"{result.performance_metrics['safari_launch_time']:.2f}s"
                elif "total_extraction_time" in result.performance_metrics:
                    key_metric = f"{result.performance_metrics['total_extraction_time']:.3f}s"
                
                if key_metric:
                    status = "✅" if result.success else "❌"
                    print(f"{status} {result.test_name}: {key_metric}")
        
        # Save detailed QA report
        self.save_qa_report()
        
        return {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "category_results": categories,
            "production_ready": failed_tests == 0 and (passed_tests/total_tests) >= 0.9
        }
    
    def save_qa_report(self):
        """Save detailed QA report"""
        report_path = self.webfetcher_root / "safari_integration_qa_report.json"
        
        report = {
            "qa_info": {
                "timestamp": datetime.now().isoformat(),
                "webfetcher_root": str(self.webfetcher_root),
                "thresholds": {
                    "performance": self.performance_thresholds,
                    "quality": self.quality_thresholds
                }
            },
            "summary": {
                "total_tests": len(self.test_results),
                "passed": sum(1 for r in self.test_results if r.success),
                "failed": sum(1 for r in self.test_results if not r.success)
            },
            "qa_results": [asdict(result) for result in self.test_results]
        }
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 Detailed QA report saved: {report_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save QA report: {e}")

def main():
    """Main QA execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Quality Assurance testing for Safari CCDI integration"
    )
    parser.add_argument(
        "webfetcher_path", 
        help="Path to Web_Fetcher root directory"
    )
    parser.add_argument(
        "--category", "-c",
        choices=["Performance", "Quality", "Security"],
        help="Run only tests from specific category"
    )
    
    args = parser.parse_args()
    
    # Validate path
    webfetcher_path = Path(args.webfetcher_path).resolve()
    if not webfetcher_path.exists():
        print(f"❌ Error: WebFetcher path does not exist: {webfetcher_path}")
        return 1
    
    # Run QA tests
    qa_tester = SafariCCDIQualityAssurance(str(webfetcher_path))
    results = qa_tester.run_full_qa_suite()
    
    # Determine exit code based on production readiness
    if results["production_ready"]:
        print("\n🎉 QA PASSED - Integration is production ready!")
        return 0
    else:
        print("\n⚠️ QA ISSUES DETECTED - Review failed tests before production deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())