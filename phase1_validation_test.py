#!/usr/bin/env python3
"""
Phase 1 Validation Test
Tests core functionality before and after safe deletions
"""

import sys
import os
import json
import traceback
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_core_sites():
    """Test the three core sites that should continue working"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "summary": {"passed": 0, "failed": 0, "errors": []}
    }
    
    # Test URLs representing core functionality
    test_cases = [
        {
            "name": "BBC News Article",
            "url": "https://www.bbc.com/news/technology-67890123",
            "expected_content": ["title", "content"],
            "description": "Test BBC news extraction"
        },
        {
            "name": "CNN Article", 
            "url": "https://edition.cnn.com/2024/01/15/tech/ai-news/index.html",
            "expected_content": ["title", "content"],
            "description": "Test CNN news extraction"
        },
        {
            "name": "Reuters Article",
            "url": "https://www.reuters.com/technology/artificial-intelligence/",
            "expected_content": ["title", "content"],
            "description": "Test Reuters news extraction"
        }
    ]
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        test_result = {
            "name": test_case["name"],
            "url": test_case["url"],
            "status": "unknown",
            "error": None,
            "has_content": False,
            "content_length": 0
        }
        
        try:
            # Import webfetcher
            import webfetcher
            
            # Test basic fetch - use generic_to_markdown for testing
            html, metrics = webfetcher.fetch_html(test_case["url"])
            
            if html:
                # Use generic parser to extract content
                date_only, md, metadata = webfetcher.generic_to_markdown(html, test_case["url"])
                result = {
                    "title": metadata.get("title", ""),
                    "content": md,
                    "metadata": metadata
                }
            else:
                result = None
            
            if result and isinstance(result, dict):
                # Check if we got basic content
                has_title = bool(result.get("title", "").strip())
                has_content = bool(result.get("content", "").strip())
                
                test_result["has_content"] = has_title or has_content
                test_result["content_length"] = len(str(result.get("content", "")))
                test_result["status"] = "passed" if test_result["has_content"] else "failed"
                
                if test_result["status"] == "passed":
                    results["summary"]["passed"] += 1
                    print(f"  ✓ PASSED - Got content ({test_result['content_length']} chars)")
                else:
                    results["summary"]["failed"] += 1
                    print(f"  ✗ FAILED - No meaningful content extracted")
                    
            else:
                test_result["status"] = "failed"
                test_result["error"] = "No result returned or invalid format"
                results["summary"]["failed"] += 1
                print(f"  ✗ FAILED - {test_result['error']}")
                
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
            results["summary"]["errors"].append(f"{test_case['name']}: {str(e)}")
            results["summary"]["failed"] += 1
            print(f"  ✗ ERROR - {str(e)}")
        
        results["tests"].append(test_result)
    
    return results

def test_import_structure():
    """Test that core imports work"""
    print("\nTesting import structure...")
    import_results = {
        "webfetcher_import": False,
        "safari_plugin": False,
        "errors": []
    }
    
    try:
        import webfetcher
        import_results["webfetcher_import"] = True
        print("  ✓ webfetcher imports successfully")
    except Exception as e:
        import_results["errors"].append(f"webfetcher import: {str(e)}")
        print(f"  ✗ webfetcher import failed: {str(e)}")
    
    try:
        from plugins.safari.extractor import extract_with_safari_fallback
        import_results["safari_plugin"] = True
        print("  ✓ Safari plugin imports successfully")
    except Exception as e:
        import_results["errors"].append(f"Safari plugin import: {str(e)}")
        print(f"  ✗ Safari plugin import failed: {str(e)}")
    
    return import_results

def main():
    """Run validation tests"""
    print("=" * 60)
    print("PHASE 1 VALIDATION TEST")
    print("=" * 60)
    
    # Test imports first
    import_results = test_import_structure()
    
    # Test core functionality
    results = test_core_sites()
    results["import_tests"] = import_results
    
    # Summary
    print(f"\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {results['summary']['passed']}")
    print(f"Tests Failed: {results['summary']['failed']}")
    print(f"Import Success: webfetcher={import_results['webfetcher_import']}, safari={import_results['safari_plugin']}")
    
    if results["summary"]["errors"]:
        print("\nErrors encountered:")
        for error in results["summary"]["errors"]:
            print(f"  - {error}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"phase1_validation_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {filename}")
    
    return results["summary"]["failed"] == 0 and import_results["webfetcher_import"]

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)