#!/usr/bin/env python3
"""
Parameter Validation Test Suite
Phase 1 Task 1.1 - Cherry-pick Preparation Testing

This script validates the parameter system functionality after cherry-pick operations.
It tests -u/-s/-m parameter combinations and ensures proper integration.
"""

import subprocess
import sys
import os
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class ParameterValidator:
    """Validates parameter system functionality for webfetcher.py"""
    
    def __init__(self, webfetcher_path: str = "webfetcher.py"):
        self.webfetcher_path = webfetcher_path
        self.test_results: List[Dict] = []
        self.temp_dir = tempfile.mkdtemp(prefix="webfetcher_test_")
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with level"""
        colors = {
            "INFO": "\033[0;34m",
            "SUCCESS": "\033[0;32m", 
            "WARNING": "\033[1;33m",
            "ERROR": "\033[0;31m",
            "RESET": "\033[0m"
        }
        print(f"{colors.get(level, '')}{level}: {message}{colors['RESET']}")
        
    def run_webfetcher(self, args: List[str], expect_success: bool = True) -> Tuple[bool, str, str]:
        """Run webfetcher with given arguments and return result"""
        cmd = ["python3", self.webfetcher_path] + args
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd=os.path.dirname(os.path.abspath(self.webfetcher_path))
            )
            success = (result.returncode == 0) == expect_success
            return success, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
            
    def test_help_output(self) -> bool:
        """Test that help output works and contains expected parameters"""
        self.log("Testing help output...")
        
        success, stdout, stderr = self.run_webfetcher(["--help"])
        if not success:
            self.log("Help command failed", "ERROR")
            return False
            
        # Check for required parameters in help output
        required_params = [
            "--method",
            "-m",
            "-s",
            "--selenium", 
            "-u",
            "--urllib"
        ]
        
        missing_params = []
        for param in required_params:
            if param not in stdout:
                missing_params.append(param)
                
        if missing_params:
            self.log(f"Missing parameters in help: {missing_params}", "ERROR")
            return False
            
        self.log("Help output validation passed", "SUCCESS")
        return True
        
    def test_parameter_conflicts(self) -> bool:
        """Test parameter conflict detection"""
        self.log("Testing parameter conflicts...")
        
        # Test -s and -u together (should fail)
        success, stdout, stderr = self.run_webfetcher([
            "-s", "-u", 
            "--outdir", self.temp_dir,
            "http://httpbin.org/html"
        ], expect_success=False)
        
        if success:
            self.log("Expected -s/-u conflict not detected", "ERROR")
            return False
            
        if "Cannot use both" not in stderr and "mutually exclusive" not in stderr:
            self.log("No conflict error message found", "ERROR") 
            return False
            
        self.log("Parameter conflict detection working", "SUCCESS")
        return True
        
    def test_method_parameter(self) -> bool:
        """Test --method parameter functionality"""
        self.log("Testing --method parameter...")
        
        # Test valid method values
        methods = ["auto", "urllib", "selenium"]
        
        for method in methods:
            # Test that parameter is accepted (dry run with invalid URL to avoid actual fetch)
            success, stdout, stderr = self.run_webfetcher([
                "--method", method,
                "--help"  # Use help to avoid actual web request
            ])
            
            if not success:
                self.log(f"Method parameter '{method}' validation failed", "ERROR")
                return False
                
        # Test invalid method value
        success, stdout, stderr = self.run_webfetcher([
            "--method", "invalid_method",
            "http://example.com"
        ], expect_success=False)
        
        if success:
            self.log("Invalid method value not rejected", "ERROR")
            return False
            
        self.log("Method parameter validation passed", "SUCCESS") 
        return True
        
    def test_shortcut_parameters(self) -> bool:
        """Test -s and -u shortcut parameters"""
        self.log("Testing shortcut parameters...")
        
        # These tests check that the parameters are accepted
        # We use --help to avoid making actual web requests
        
        # Test -s shortcut
        success, stdout, stderr = self.run_webfetcher(["-s", "--help"])
        if not success:
            self.log("Shortcut -s parameter not accepted", "ERROR")
            return False
            
        # Test -u shortcut  
        success, stdout, stderr = self.run_webfetcher(["-u", "--help"])
        if not success:
            self.log("Shortcut -u parameter not accepted", "ERROR")
            return False
            
        # Test --selenium long form
        success, stdout, stderr = self.run_webfetcher(["--selenium", "--help"])
        if not success:
            self.log("Long form --selenium parameter not accepted", "ERROR")
            return False
            
        # Test --urllib long form
        success, stdout, stderr = self.run_webfetcher(["--urllib", "--help"])
        if not success:
            self.log("Long form --urllib parameter not accepted", "ERROR")
            return False
            
        self.log("Shortcut parameter validation passed", "SUCCESS")
        return True
        
    def test_import_chain(self) -> bool:
        """Test that webfetcher can be imported without errors"""
        self.log("Testing import chain...")
        
        success, stdout, stderr = self.run_webfetcher([
            "-c", 
            "import webfetcher; print('Import successful')"
        ])
        
        # Try direct import test
        try:
            cmd = ["python3", "-c", "import sys; sys.path.insert(0, '.'); import webfetcher; print('Import successful')"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and "Import successful" in result.stdout:
                self.log("Import chain validation passed", "SUCCESS")
                return True
            else:
                self.log(f"Import failed: {result.stderr}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Import test exception: {e}", "ERROR")
            return False
            
    def test_no_fallback_parameter(self) -> bool:
        """Test --no-fallback parameter"""
        self.log("Testing --no-fallback parameter...")
        
        # Test that parameter is accepted
        success, stdout, stderr = self.run_webfetcher(["--no-fallback", "--help"])
        if not success:
            self.log("No-fallback parameter not accepted", "ERROR")
            return False
            
        self.log("No-fallback parameter validation passed", "SUCCESS")
        return True
        
    def run_all_tests(self) -> bool:
        """Run complete validation suite"""
        self.log("Starting Parameter Validation Test Suite")
        self.log("=" * 50)
        
        tests = [
            ("Import Chain", self.test_import_chain),
            ("Help Output", self.test_help_output),
            ("Method Parameter", self.test_method_parameter),
            ("Shortcut Parameters", self.test_shortcut_parameters),
            ("Parameter Conflicts", self.test_parameter_conflicts),
            ("No-Fallback Parameter", self.test_no_fallback_parameter),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                    self.test_results.append({"name": test_name, "status": "PASSED"})
                else:
                    self.test_results.append({"name": test_name, "status": "FAILED"})
            except Exception as e:
                self.log(f"Test {test_name} threw exception: {e}", "ERROR")
                self.test_results.append({"name": test_name, "status": "ERROR", "error": str(e)})
            
            self.log("-" * 30)
            
        # Summary
        self.log("=" * 50)
        self.log(f"Test Results: {passed}/{total} passed")
        
        if passed == total:
            self.log("ALL TESTS PASSED - Parameter system ready!", "SUCCESS")
        else:
            self.log(f"{total - passed} tests failed - manual review required", "ERROR")
            
        return passed == total
        
    def generate_report(self, output_file: str = "parameter_validation_report.json"):
        """Generate detailed test report"""
        report = {
            "timestamp": subprocess.run(["date", "-u"], capture_output=True, text=True).stdout.strip(),
            "webfetcher_path": self.webfetcher_path,
            "total_tests": len(self.test_results),
            "passed_tests": len([r for r in self.test_results if r["status"] == "PASSED"]),
            "failed_tests": len([r for r in self.test_results if r["status"] == "FAILED"]),
            "error_tests": len([r for r in self.test_results if r["status"] == "ERROR"]),
            "results": self.test_results
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        self.log(f"Detailed report saved to: {output_file}")
        
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.log(f"Cleanup warning: {e}", "WARNING")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate parameter system functionality")
    parser.add_argument("--webfetcher", default="webfetcher.py", help="Path to webfetcher.py")
    parser.add_argument("--report", default="parameter_validation_report.json", help="Report output file")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.webfetcher):
        print(f"ERROR: webfetcher.py not found at: {args.webfetcher}")
        sys.exit(1)
        
    validator = ParameterValidator(args.webfetcher)
    
    try:
        success = validator.run_all_tests()
        validator.generate_report(args.report)
        
        if success:
            print("\n✅ Parameter system validation: PASSED")
            sys.exit(0)
        else:
            print("\n❌ Parameter system validation: FAILED")
            sys.exit(1)
            
    finally:
        validator.cleanup()

if __name__ == "__main__":
    main()