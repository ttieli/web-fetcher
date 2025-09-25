#!/usr/bin/env python3
"""
Phase 1 Validation Test for Parser Migration
Architecture validation script - NOT production code
"""

import sys
import os
import importlib
import inspect

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def validate_parser_migration():
    """Validate the parser migration completeness and correctness."""
    
    results = {
        'module_import': False,
        'functions_found': {},
        'function_signatures': {},
        'helper_functions': {},
        'data_classes': {},
        'issues': []
    }
    
    # Expected main functions from specification
    expected_functions = [
        'docusaurus_to_markdown',
        'mkdocs_to_markdown', 
        'ebchina_news_list_to_markdown',
        'dianping_to_markdown',
        'xhs_to_markdown',
        'wechat_to_markdown',
        'detect_page_type',
        'raw_to_markdown',
        'generic_to_markdown'
    ]
    
    # Expected helper functions
    expected_helpers = [
        'extract_meta',
        'extract_json_ld_content',
        'extract_from_modern_selectors',
        'extract_text_from_html_fragment',
        'parse_date_like',
        'extract_list_content',
        'resolve_url_with_context',
        'normalize_media_url',
        'format_list_page_markdown',
        'add_metrics_to_markdown'
    ]
    
    try:
        # Import the parsers module
        import parsers
        results['module_import'] = True
        print("✅ parsers.py module imported successfully")
        
        # Check for main parsing functions
        for func_name in expected_functions:
            if hasattr(parsers, func_name):
                func = getattr(parsers, func_name)
                results['functions_found'][func_name] = True
                # Get function signature
                sig = inspect.signature(func)
                results['function_signatures'][func_name] = str(sig)
                print(f"✅ Found function: {func_name}{sig}")
            else:
                results['functions_found'][func_name] = False
                results['issues'].append(f"Missing function: {func_name}")
                print(f"❌ Missing function: {func_name}")
        
        # Check for helper functions
        for func_name in expected_helpers:
            if hasattr(parsers, func_name):
                results['helper_functions'][func_name] = True
                print(f"✅ Found helper: {func_name}")
            else:
                results['helper_functions'][func_name] = False
                print(f"⚠️  Missing helper: {func_name}")
        
        # Check for data classes
        if hasattr(parsers, 'PageType'):
            results['data_classes']['PageType'] = True
            print("✅ Found PageType enum")
        else:
            results['issues'].append("Missing PageType enum")
            print("❌ Missing PageType enum")
            
        if hasattr(parsers, 'ListItem'):
            results['data_classes']['ListItem'] = True
            print("✅ Found ListItem dataclass")
        else:
            results['issues'].append("Missing ListItem dataclass")
            print("❌ Missing ListItem dataclass")
        
        # Validate function signatures match expected
        expected_signatures = {
            'docusaurus_to_markdown': '(html: str, url: str) -> tuple[str, str, dict]',
            'mkdocs_to_markdown': '(html: str, url: str) -> tuple[str, str, dict]',
            'ebchina_news_list_to_markdown': '(html: str, url: str) -> tuple[str, str, dict]',
            'dianping_to_markdown': '(html: str, url: str) -> tuple[str, str, dict]',
            'xhs_to_markdown': '(html: str, url: str) -> tuple[str, str, dict]',
            'wechat_to_markdown': '(html: str, url: str) -> tuple[str, str, dict]',
            'detect_page_type': '(html: str, url: Optional[str] = None, is_crawling: bool = False) -> PageType',
            'raw_to_markdown': '(html: str, url: str) -> tuple[str, str, dict]',
            'generic_to_markdown': '(html: str, url: str, filter_level: str = \'safe\', is_crawling: bool = False) -> tuple[str, str, dict]'
        }
        
        print("\n--- Signature Validation ---")
        for func_name, expected_sig in expected_signatures.items():
            if func_name in results['function_signatures']:
                actual_sig = results['function_signatures'][func_name]
                # Simple check - can be more sophisticated
                if 'tuple' in actual_sig and 'str' in actual_sig:
                    print(f"✅ {func_name} signature looks correct")
                else:
                    print(f"⚠️  {func_name} signature may need review: {actual_sig}")
        
    except ImportError as e:
        results['issues'].append(f"Import error: {str(e)}")
        print(f"❌ Failed to import parsers.py: {str(e)}")
    except Exception as e:
        results['issues'].append(f"Unexpected error: {str(e)}")
        print(f"❌ Unexpected error: {str(e)}")
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    total_main = len(expected_functions)
    found_main = sum(1 for v in results['functions_found'].values() if v)
    total_helpers = len(expected_helpers)
    found_helpers = sum(1 for v in results['helper_functions'].values() if v)
    
    print(f"Main Functions: {found_main}/{total_main} found")
    print(f"Helper Functions: {found_helpers}/{total_helpers} found")
    print(f"Data Classes: {len(results['data_classes'])}/2 found")
    
    if results['issues']:
        print("\n⚠️  Issues Found:")
        for issue in results['issues']:
            print(f"  - {issue}")
    else:
        print("\n✅ No critical issues found")
    
    # Final verdict
    if found_main == total_main and not results['issues']:
        print("\n🎉 PHASE 1 VALIDATION: PASSED")
        return True
    else:
        print("\n❌ PHASE 1 VALIDATION: NEEDS ATTENTION")
        return False

if __name__ == "__main__":
    success = validate_parser_migration()
    sys.exit(0 if success else 1)