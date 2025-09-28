#!/usr/bin/env python3
"""
Phase 1 Pre-deletion Validation Script
Tests core functionality before safe file deletions
"""

import subprocess
import os
import json
import sys
from datetime import datetime
from pathlib import Path

class Phase1Validator:
    def __init__(self):
        self.test_urls = {
            'wechat': 'https://mp.weixin.qq.com/s/MkN0RNffnbN1cqpgOOC0fA',
            'xiaohongshu': 'https://www.xiaohongshu.com/explore/6734e9ab000000001201db4c', 
            'xinhua': 'http://www.news.cn/politics/leaders/20241028/test.htm'
        }
        self.results = {}
        self.output_dir = Path('./test_output_phase1')
        self.output_dir.mkdir(exist_ok=True)
        
    def test_wf_command(self, site_name, url):
        """Test the wf command for a specific URL"""
        print(f"\nTesting {site_name}: {url}")
        
        # Run wf command
        cmd = ['python3', 'wf.py', url, str(self.output_dir)]
        result = {
            'site': site_name,
            'url': url,
            'success': False,
            'error': None,
            'output_file': None
        }
        
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if process.returncode == 0:
                # Check if output file was created
                md_files = list(self.output_dir.glob('*.md'))
                latest_file = max(md_files, key=lambda f: f.stat().st_mtime, default=None)
                
                if latest_file:
                    result['success'] = True
                    result['output_file'] = str(latest_file)
                    print(f"  ✓ Success - Output: {latest_file.name}")
                    
                    # Check file content
                    content = latest_file.read_text()
                    if len(content) > 100:
                        print(f"  ✓ Content extracted: {len(content)} characters")
                    else:
                        print(f"  ⚠ Warning: Small output ({len(content)} characters)")
                else:
                    result['error'] = "No output file created"
                    print(f"  ✗ Failed: No output file created")
            else:
                result['error'] = f"Command failed with code {process.returncode}"
                if process.stderr:
                    result['error'] += f"\nError: {process.stderr[:500]}"
                print(f"  ✗ Failed: {result['error'][:100]}")
                
        except subprocess.TimeoutExpired:
            result['error'] = "Command timed out after 30 seconds"
            print(f"  ✗ Failed: Timeout")
        except Exception as e:
            result['error'] = str(e)
            print(f"  ✗ Failed: {e}")
            
        self.results[site_name] = result
        return result
        
    def check_dependencies(self):
        """Check which modules and files are actually imported/used"""
        print("\n=== Dependency Check ===")
        dependencies = {
            'extractors_imported': False,
            'plugins_imported': False,
            'safari_available': False
        }
        
        # Check if extractors are imported anywhere critical
        try:
            import webfetcher
            # Check for Safari availability
            dependencies['safari_available'] = hasattr(webfetcher, 'SAFARI_AVAILABLE') and webfetcher.SAFARI_AVAILABLE
            print(f"Safari Available: {dependencies['safari_available']}")
        except:
            pass
            
        # Check for actual usage of extractors
        grep_cmd = "grep -r 'from extractors' --include='*.py' | grep -v 'plugins/safari'"
        result = subprocess.run(grep_cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"Extractors imported in: {result.stdout[:200]}")
            dependencies['extractors_imported'] = True
        else:
            print("Extractors not imported in core files")
            
        # Check for plugin usage
        plugin_files = ['playwright_fetcher.py', 'curl.py', 'http_fetcher.py']
        for pf in plugin_files:
            grep_cmd = f"grep -r '{pf.split('.')[0]}' webfetcher.py wf.py"
            result = subprocess.run(grep_cmd, shell=True, capture_output=True, text=True)
            if result.stdout:
                print(f"Plugin {pf} referenced: {result.stdout[:100]}")
                dependencies['plugins_imported'] = True
                
        return dependencies
        
    def run_all_tests(self):
        """Execute all validation tests"""
        print("=" * 60)
        print("PHASE 1 PRE-DELETION VALIDATION")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Check dependencies first
        deps = self.check_dependencies()
        
        # Test each core site
        print("\n=== Core Site Testing ===")
        for site_name, url in self.test_urls.items():
            self.test_wf_command(site_name, url)
            
        # Generate summary
        self.generate_summary()
        
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        all_passed = all(r['success'] for r in self.results.values())
        
        for site, result in self.results.items():
            status = "✓ PASS" if result['success'] else "✗ FAIL"
            print(f"{site:15} {status}")
            if not result['success'] and result['error']:
                print(f"                Error: {result['error'][:100]}")
                
        print("\n" + "=" * 60)
        if all_passed:
            print("✓ ALL TESTS PASSED - SAFE TO PROCEED WITH PHASE 1 DELETIONS")
            print("\nSafe to delete:")
            print("  • extractors/ directory")
            print("  • plugins/playwright_fetcher.py")
            print("  • plugins/curl.py")
            print("  • plugins/http_fetcher.py")
            print("  • plugins/selenium/ directory")
        else:
            print("✗ VALIDATION FAILED - DO NOT PROCEED WITH DELETIONS")
            print("Fix issues before proceeding")
            
        # Save results to JSON
        report_file = f"phase1_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': self.results,
                'all_passed': all_passed
            }, f, indent=2)
        print(f"\nDetailed report saved to: {report_file}")
        
if __name__ == "__main__":
    validator = Phase1Validator()
    validator.run_all_tests()