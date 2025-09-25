#!/usr/bin/env python3
"""
Check differences between original and migrated functions.
Architecture validation script - NOT production code
"""

import re

def check_logging_vs_print():
    """Check for logging.debug() replaced with print() statements."""
    
    # Read parsers.py
    with open('parsers.py', 'r', encoding='utf-8') as f:
        parsers_content = f.read()
    
    # Read webfetcher.py  
    with open('webfetcher.py', 'r', encoding='utf-8') as f:
        webfetcher_content = f.read()
    
    # Count print statements in parsers.py
    print_count = len(re.findall(r'\bprint\(', parsers_content))
    
    # Check specific functions for logging differences
    functions_to_check = [
        'detect_page_type',
        'extract_list_content', 
        'generic_to_markdown'
    ]
    
    print("Checking for logging -> print conversions...")
    print(f"Found {print_count} print() statements in parsers.py")
    
    issues = []
    
    for func_name in functions_to_check:
        # Extract function from webfetcher
        pattern = rf'def {func_name}\([^)]*\):[^d]*?(?=\ndef |\Z)'
        webfetcher_match = re.search(pattern, webfetcher_content, re.DOTALL)
        
        if webfetcher_match:
            webfetcher_func = webfetcher_match.group(0)
            logging_count = len(re.findall(r'logging\.\w+\(', webfetcher_func))
            
            # Extract function from parsers
            parsers_match = re.search(pattern, parsers_content, re.DOTALL)
            if parsers_match:
                parsers_func = parsers_match.group(0)
                print_in_func = len(re.findall(r'\bprint\(', parsers_func))
                
                if logging_count > 0:
                    print(f"\n{func_name}:")
                    print(f"  - Original: {logging_count} logging statements")
                    print(f"  - Migrated: {print_in_func} print statements")
                    
                    if print_in_func > 0:
                        issues.append(f"{func_name}: logging.debug() replaced with print()")
    
    return issues

def check_beautifulsoup_handling():
    """Check BeautifulSoup handling."""
    
    with open('parsers.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for BeautifulSoup imports
    bs_imports = re.findall(r'from bs4 import.*', content)
    
    # Check for get_beautifulsoup_parser placeholder
    has_placeholder = 'def get_beautifulsoup_parser()' in content
    placeholder_raises = 'raise Exception' in content and 'Phase 1' in content
    
    print("\nBeautifulSoup handling check:")
    print(f"  - BeautifulSoup imports: {len(bs_imports)}")
    print(f"  - Has placeholder function: {has_placeholder}")
    print(f"  - Placeholder raises exception: {placeholder_raises}")
    
    return []

def check_imports():
    """Check import differences."""
    
    with open('parsers.py', 'r', encoding='utf-8') as f:
        parsers_imports = re.findall(r'^import .*|^from .* import .*', f.read(), re.MULTILINE)
    
    print("\nImports in parsers.py:")
    for imp in sorted(set(parsers_imports)):
        print(f"  - {imp}")
    
    # Check for missing logging import
    has_logging = any('logging' in imp for imp in parsers_imports)
    
    if not has_logging:
        print("\n⚠️  Note: logging module not imported (expected for Phase 1)")
    
    return []

if __name__ == "__main__":
    print("="*60)
    print("DIFFERENCE ANALYSIS")
    print("="*60)
    
    all_issues = []
    
    all_issues.extend(check_logging_vs_print())
    all_issues.extend(check_beautifulsoup_handling())
    all_issues.extend(check_imports())
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if all_issues:
        print("\nIdentified differences (expected for Phase 1):")
        for issue in all_issues:
            print(f"  - {issue}")
    else:
        print("\nNo unexpected differences found.")
    
    print("\n✅ These differences are EXPECTED for Phase 1:")
    print("  1. logging.debug() → print() conversion")
    print("  2. BeautifulSoup import handling deferred")
    print("  3. get_beautifulsoup_parser() placeholder")
    print("\nThese will be addressed in Phase 2 integration.")