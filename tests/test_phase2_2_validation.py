#!/usr/bin/env python3
"""
Phase 2.2 Validation Script - Plugin System Removal
Ensures safe removal of plugin system while preserving core functionality.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_no_plugin_references():
    """Ensure no plugin code references remain in webfetcher.py"""
    print("Testing for plugin references...")
    
    webfetcher_path = Path(__file__).parent.parent / 'webfetcher.py'
    
    with open(webfetcher_path, 'r') as f:
        content = f.read()
    
    plugin_indicators = [
        'PLUGIN_SYSTEM_AVAILABLE',
        'from plugins import',
        'import plugins',
        'fetch_html_with_plugins',
        'get_global_registry',
        'FetchContext',
        'PluginRegistry'
    ]
    
    found_references = []
    for indicator in plugin_indicators:
        if indicator in content:
            # Count occurrences
            count = content.count(indicator)
            found_references.append(f"{indicator} ({count} occurrences)")
    
    if found_references:
        print(f"  ❌ Found plugin references: {', '.join(found_references)}")
        return False
    else:
        print("  ✅ No plugin references found")
        return True

def test_no_plugin_directory():
    """Ensure plugins directory has been removed"""
    print("Testing for plugin directory...")
    
    plugins_dir = Path(__file__).parent.parent / 'plugins'
    
    if plugins_dir.exists():
        print(f"  ❌ Plugin directory still exists at {plugins_dir}")
        return False
    else:
        print("  ✅ Plugin directory removed")
        return True

def test_extractors_preserved():
    """Ensure extractors directory is preserved"""
    print("Testing extractors preservation...")
    
    extractors_dir = Path(__file__).parent.parent / 'extractors'
    
    if not extractors_dir.exists():
        print(f"  ❌ Extractors directory missing at {extractors_dir}")
        return False
    
    # Check for key files
    required_files = ['__init__.py', 'base_extractor.py', 'generic_extractor.py']
    missing_files = []
    
    for file in required_files:
        if not (extractors_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"  ❌ Missing extractor files: {', '.join(missing_files)}")
        return False
    else:
        print("  ✅ Extractors directory and files preserved")
        return True

def test_core_functionality():
    """Test core fetch functionality works without plugins"""
    print("\nTesting core functionality...")
    
    test_results = []
    
    # Test URLs for each supported site
    test_cases = [
        {
            'name': 'WeChat Article',
            'url': 'https://mp.weixin.qq.com/s/g3omvC69K9C70lrJKKFjFQ',
            'expected_title_fragment': '永定河'
        },
        {
            'name': 'Xiaohongshu Note',
            'url': 'https://www.xiaohongshu.com/explore/6703fc35000000001e034a04',
            'expected_title_fragment': '万物'
        },
        {
            'name': 'Xinhua News',
            'url': 'https://www.news.cn/politics/leaders/20241001/da2e9e2461bb41fbb96a913c89c90b38/c.html',
            'expected_title_fragment': '中华人民共和国'
        }
    ]
    
    for test in test_cases:
        print(f"\n  Testing {test['name']}...")
        start_time = time.time()
        
        try:
            # Use subprocess to test actual CLI functionality
            cmd = [
                sys.executable, 
                'webfetcher.py',
                test['url'],
                '--test'  # Test mode - no file output
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=30,
                cwd=Path(__file__).parent.parent
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                # Check if expected content is in output
                if test['expected_title_fragment'] in result.stdout:
                    print(f"    ✅ {test['name']} succeeded ({duration:.2f}s)")
                    test_results.append({
                        'test': test['name'],
                        'status': 'success',
                        'duration': duration
                    })
                else:
                    print(f"    ⚠️ {test['name']} fetched but content mismatch")
                    test_results.append({
                        'test': test['name'],
                        'status': 'partial',
                        'duration': duration,
                        'note': 'Content mismatch'
                    })
            else:
                print(f"    ❌ {test['name']} failed: {result.stderr}")
                test_results.append({
                    'test': test['name'],
                    'status': 'failed',
                    'error': result.stderr[:200]
                })
                
        except subprocess.TimeoutExpired:
            print(f"    ❌ {test['name']} timed out")
            test_results.append({
                'test': test['name'],
                'status': 'timeout'
            })
        except Exception as e:
            print(f"    ❌ {test['name']} error: {e}")
            test_results.append({
                'test': test['name'],
                'status': 'error',
                'error': str(e)
            })
    
    # Check if all tests passed
    success_count = sum(1 for r in test_results if r['status'] == 'success')
    return success_count == len(test_cases), test_results

def test_urllib_import_chain():
    """Verify the urllib import and usage chain"""
    print("\nTesting urllib import chain...")
    
    webfetcher_path = Path(__file__).parent.parent / 'webfetcher.py'
    
    with open(webfetcher_path, 'r') as f:
        content = f.read()
    
    required_imports = [
        'import urllib.request',
        'import urllib.parse',
        'import urllib.error'
    ]
    
    missing_imports = []
    for imp in required_imports:
        if imp not in content:
            missing_imports.append(imp)
    
    if missing_imports:
        print(f"  ❌ Missing imports: {', '.join(missing_imports)}")
        return False
    
    # Check for key urllib usage patterns
    urllib_patterns = [
        'urllib.request.Request',
        'urllib.request.urlopen',
        'urllib.error.HTTPError'
    ]
    
    missing_patterns = []
    for pattern in urllib_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)
    
    if missing_patterns:
        print(f"  ⚠️ Missing urllib patterns: {', '.join(missing_patterns)}")
        return False
    
    print("  ✅ urllib import chain verified")
    return True

def test_fetch_function_chain():
    """Verify the correct fetch function chain is in place"""
    print("\nTesting fetch function chain...")
    
    webfetcher_path = Path(__file__).parent.parent / 'webfetcher.py'
    
    with open(webfetcher_path, 'r') as f:
        content = f.read()
    
    # Check for required functions
    required_functions = [
        'def fetch_html_with_retry',
        'def fetch_html_original',
        'def fetch_html_with_curl_metrics'
    ]
    
    missing_functions = []
    for func in required_functions:
        if func not in content:
            missing_functions.append(func.replace('def ', ''))
    
    if missing_functions:
        print(f"  ❌ Missing functions: {', '.join(missing_functions)}")
        return False
    
    # Check the assignment at the end
    if 'fetch_html = fetch_html_with_retry' in content:
        print("  ✅ Correct function assignment found")
        return True
    elif 'fetch_html = fetch_html_with_plugins' in content:
        print("  ⚠️ Still using plugin-based assignment")
        return False
    else:
        print("  ❌ Unknown fetch_html assignment")
        return False

def generate_report(results):
    """Generate validation report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = Path(__file__).parent / f'phase2_2_validation_{timestamp}.json'
    
    report = {
        'timestamp': timestamp,
        'phase': '2.2',
        'description': 'Plugin System Removal Validation',
        'results': results,
        'summary': {
            'total_tests': len(results),
            'passed': sum(1 for r in results if r['status'] == 'passed'),
            'failed': sum(1 for r in results if r['status'] == 'failed'),
            'warnings': sum(1 for r in results if r['status'] == 'warning')
        }
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report_path

def main():
    """Main validation routine"""
    print("=" * 60)
    print("Phase 2.2: Plugin System Removal Validation")
    print("=" * 60)
    
    results = []
    
    # Test 1: No plugin references
    test_name = "No Plugin References"
    print(f"\n{test_name}:")
    if test_no_plugin_references():
        results.append({'test': test_name, 'status': 'passed'})
    else:
        results.append({'test': test_name, 'status': 'failed'})
    
    # Test 2: No plugin directory
    test_name = "Plugin Directory Removed"
    print(f"\n{test_name}:")
    if test_no_plugin_directory():
        results.append({'test': test_name, 'status': 'passed'})
    else:
        results.append({'test': test_name, 'status': 'warning', 
                       'note': 'Directory should be removed'})
    
    # Test 3: Extractors preserved
    test_name = "Extractors Preserved"
    print(f"\n{test_name}:")
    if test_extractors_preserved():
        results.append({'test': test_name, 'status': 'passed'})
    else:
        results.append({'test': test_name, 'status': 'failed'})
    
    # Test 4: urllib import chain
    test_name = "urllib Import Chain"
    print(f"\n{test_name}:")
    if test_urllib_import_chain():
        results.append({'test': test_name, 'status': 'passed'})
    else:
        results.append({'test': test_name, 'status': 'failed'})
    
    # Test 5: Fetch function chain
    test_name = "Fetch Function Chain"
    print(f"\n{test_name}:")
    if test_fetch_function_chain():
        results.append({'test': test_name, 'status': 'passed'})
    else:
        results.append({'test': test_name, 'status': 'failed'})
    
    # Test 6: Core functionality
    test_name = "Core Functionality"
    success, test_details = test_core_functionality()
    if success:
        results.append({'test': test_name, 'status': 'passed', 'details': test_details})
    else:
        results.append({'test': test_name, 'status': 'failed', 'details': test_details})
    
    # Generate report
    report_path = generate_report(results)
    
    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['status'] == 'passed')
    failed = sum(1 for r in results if r['status'] == 'failed')
    warnings = sum(1 for r in results if r['status'] == 'warning')
    
    print(f"Total Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️ Warnings: {warnings}")
    
    print(f"\nReport saved to: {report_path}")
    
    if failed == 0:
        print("\n🎉 Phase 2.2 validation PASSED - Safe to proceed!")
        return 0
    else:
        print("\n⚠️ Phase 2.2 validation has issues - Review before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main())