#!/usr/bin/env python3
"""
Task 1 Phase 2 Verification Script
Comprehensive testing of failure handling integration in main() function
"""

import subprocess
import sys
import os
import time
from pathlib import Path
import json
import tempfile
import shutil

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{msg}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_test(msg):
    print(f"{Colors.OKCYAN}▶ {msg}{Colors.ENDC}")

def print_success(msg):
    print(f"{Colors.OKGREEN}✅ {msg}{Colors.ENDC}")

def print_fail(msg):
    print(f"{Colors.FAIL}❌ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKBLUE}ℹ️  {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠️  {msg}{Colors.ENDC}")

class FailureIntegrationVerifier:
    def __init__(self):
        self.test_results = []
        self.temp_dirs = []

    def cleanup(self):
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    def create_temp_dir(self):
        """Create a temporary directory for test outputs"""
        temp_dir = Path(tempfile.mkdtemp(prefix="webfetcher_test_"))
        self.temp_dirs.append(temp_dir)
        return temp_dir

    def run_webfetcher(self, url, extra_args=None, expect_failure=False):
        """Run webfetcher and capture results"""
        temp_dir = self.create_temp_dir()
        cmd = [
            sys.executable,
            "webfetcher.py",
            url,
            "--outdir", str(temp_dir)
        ]

        if extra_args:
            cmd.extend(extra_args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(__file__).parent
            )

            # Check exit code
            if expect_failure:
                if result.returncode != 1:
                    return False, f"Expected exit code 1, got {result.returncode}", None
            else:
                if result.returncode != 0:
                    return False, f"Expected exit code 0, got {result.returncode}", None

            # Check for output files
            output_files = list(temp_dir.glob("*.md"))

            return True, result, output_files

        except subprocess.TimeoutExpired:
            return False, "Command timed out", None
        except Exception as e:
            return False, f"Execution error: {e}", None

    def test_selenium_failure_chrome_not_running(self):
        """Test Selenium failure when Chrome is not running"""
        print_test("Testing Selenium failure (Chrome not running)")

        # Ensure Chrome is not running on debug port
        subprocess.run(["pkill", "-f", "remote-debugging-port=9222"],
                      capture_output=True, stderr=subprocess.DEVNULL)
        time.sleep(1)

        success, result, files = self.run_webfetcher(
            "https://example.com",
            ["--fetch-mode", "selenium"],
            expect_failure=True
        )

        if not success:
            print_fail(f"Test failed: {result}")
            return False

        # Verify failure file was created
        if not files or not any("FAILED_" in f.name for f in files):
            print_fail("No failure report file generated")
            return False

        failure_file = next(f for f in files if "FAILED_" in f.name)
        content = failure_file.read_text(encoding='utf-8')

        # Check content includes Chrome connection error
        checks = [
            ("FAILED_ prefix in filename", "FAILED_" in failure_file.name),
            ("ChromeConnectionError mentioned", "ChromeConnectionError" in content or "Chrome" in content),
            ("Failure heading", "Failed" in content or "失败" in content),
            ("Exit code 1", result.returncode == 1)
        ]

        all_passed = True
        for check_name, passed in checks:
            if passed:
                print_success(f"  {check_name}")
            else:
                print_fail(f"  {check_name}")
                all_passed = False

        return all_passed

    def test_urllib_network_failure(self):
        """Test urllib failure with network error"""
        print_test("Testing urllib failure (invalid URL)")

        success, result, files = self.run_webfetcher(
            "https://this-domain-definitely-does-not-exist-12345.com",
            ["--fetch-mode", "urllib"],
            expect_failure=True
        )

        if not success:
            print_fail(f"Test failed: {result}")
            return False

        # Verify failure file was created
        if not files or not any("FAILED_" in f.name for f in files):
            print_fail("No failure report file generated")
            print_info(f"Files found: {[f.name for f in files] if files else 'None'}")
            if result:
                print_info(f"Stdout: {result.stdout[:500]}")
                print_info(f"Stderr: {result.stderr[:500]}")
            return False

        failure_file = next(f for f in files if "FAILED_" in f.name)
        content = failure_file.read_text(encoding='utf-8')

        # Check content includes network error
        checks = [
            ("FAILED_ prefix in filename", "FAILED_" in failure_file.name),
            ("Network error mentioned", "URLError" in content or "Error" in content or "错误" in content),
            ("Failure heading", "Failed" in content or "失败" in content),
            ("Exit code 1", result.returncode == 1)
        ]

        all_passed = True
        for check_name, passed in checks:
            if passed:
                print_success(f"  {check_name}")
            else:
                print_fail(f"  {check_name}")
                all_passed = False

        return all_passed

    def test_success_case(self):
        """Test successful fetch doesn't generate failure report"""
        print_test("Testing successful fetch (no failure report)")

        # Use a reliable test URL
        success, result, files = self.run_webfetcher(
            "https://httpbin.org/html",
            ["--fetch-mode", "urllib"],
            expect_failure=False
        )

        if not success:
            print_fail(f"Test failed: {result}")
            return False

        # Verify NO failure file was created
        if files and any("FAILED_" in f.name for f in files):
            print_fail("Unexpected failure report generated for successful fetch")
            return False

        # Verify normal output file exists
        if not files or len(files) == 0:
            print_fail("No output file generated")
            return False

        normal_file = files[0]

        checks = [
            ("No FAILED_ prefix", "FAILED_" not in normal_file.name),
            ("Normal filename format", "httpbin.org" in normal_file.name or "httpbin" in normal_file.name),
            ("Exit code 0", result.returncode == 0)
        ]

        all_passed = True
        for check_name, passed in checks:
            if passed:
                print_success(f"  {check_name}")
            else:
                print_fail(f"  {check_name}")
                all_passed = False

        return all_passed

    def test_fetch_metrics_flow(self):
        """Test that FetchMetrics correctly tracks failure status"""
        print_test("Testing FetchMetrics failure status flow")

        # Test with a URL that will timeout quickly
        success, result, files = self.run_webfetcher(
            "https://httpbin.org/delay/60",  # Will timeout
            ["--timeout", "2", "--fetch-mode", "urllib"],
            expect_failure=True
        )

        if not success:
            print_fail(f"Test failed: {result}")
            return False

        # Verify failure file was created
        if not files or not any("FAILED_" in f.name for f in files):
            print_fail("No failure report file generated for timeout")
            return False

        failure_file = next(f for f in files if "FAILED_" in f.name)
        content = failure_file.read_text(encoding='utf-8')

        checks = [
            ("Timeout error mentioned", "timeout" in content.lower() or "超时" in content),
            ("Method shown as urllib", "urllib" in content.lower()),
            ("Exit code 1", result.returncode == 1)
        ]

        all_passed = True
        for check_name, passed in checks:
            if passed:
                print_success(f"  {check_name}")
            else:
                print_fail(f"  {check_name}")
                all_passed = False

        return all_passed

    def verify_code_structure(self):
        """Verify code structure and exception handling hierarchy"""
        print_test("Verifying code structure and exception handling")

        # Read the main webfetcher.py file
        webfetcher_path = Path(__file__).parent / "webfetcher.py"
        if not webfetcher_path.exists():
            print_fail("webfetcher.py not found")
            return False

        content = webfetcher_path.read_text(encoding='utf-8')

        # Check for required exception handlers
        checks = [
            ("ChromeConnectionError handler", "except (ChromeConnectionError" in content or "except ChromeConnectionError" in content),
            ("Generic Exception handler", "except Exception as e:" in content),
            ("FetchMetrics failure check", 'fetch_metrics.final_status == "failed"' in content),
            ("Failure report generation", "generate_failure_markdown" in content),
            ("sys.exit(1) on failure", "sys.exit(1)" in content),
            ("FAILED_ filename prefix", "FAILED_" in content)
        ]

        all_passed = True
        for check_name, passed in checks:
            if passed:
                print_success(f"  {check_name}")
            else:
                print_fail(f"  {check_name}")
                all_passed = False

        return all_passed

    def run_all_tests(self):
        """Run all verification tests"""
        print_header("Task 1 Phase 2 Failure Integration Verification")

        tests = [
            ("Code Structure", self.verify_code_structure),
            ("Selenium Failure", self.test_selenium_failure_chrome_not_running),
            ("Network Failure", self.test_urllib_network_failure),
            ("Success Case", self.test_success_case),
            ("Metrics Flow", self.test_fetch_metrics_flow)
        ]

        results = []
        for test_name, test_func in tests:
            print(f"\n{Colors.BOLD}Running: {test_name}{Colors.ENDC}")
            try:
                passed = test_func()
                results.append((test_name, passed))
                if passed:
                    print_success(f"{test_name} PASSED")
                else:
                    print_fail(f"{test_name} FAILED")
            except Exception as e:
                print_fail(f"{test_name} ERRORED: {e}")
                results.append((test_name, False))

        # Summary
        print_header("Verification Summary")
        total = len(results)
        passed = sum(1 for _, p in results if p)

        for test_name, passed_flag in results:
            if passed_flag:
                print_success(f"  {test_name}")
            else:
                print_fail(f"  {test_name}")

        print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.ENDC}")

        if passed == total:
            print_success("\n🎉 All tests passed! Phase 2 implementation verified.")
            return True
        else:
            print_fail(f"\n⚠️  {total - passed} test(s) failed. Review implementation.")
            return False

def main():
    verifier = FailureIntegrationVerifier()
    try:
        success = verifier.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        verifier.cleanup()

if __name__ == "__main__":
    main()