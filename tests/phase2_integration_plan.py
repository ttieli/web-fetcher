#!/usr/bin/env python3
"""
Phase 2 Integration Validation Script
Validates prerequisites and provides integration plan for parsers module.
"""

import os
import re
from typing import List, Dict, Tuple, Set

def analyze_webfetcher_functions():
    """Analyze webfetcher.py to identify functions that need migration."""
    webfetcher_path = 'webfetcher.py'
    
    with open(webfetcher_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Functions that should be migrated to parsers
    target_functions = [
        'extract_meta',
        'extract_json_ld_content', 
        'extract_from_modern_selectors',
        'extract_text_from_html_fragment',
        'parse_date_like',
        'extract_list_content'
    ]
    
    # Find function definitions
    func_pattern = r'^def\s+(' + '|'.join(target_functions) + r')\s*\([^)]*\):'
    matches = re.finditer(func_pattern, content, re.MULTILINE)
    
    functions_to_remove = []
    for match in matches:
        func_name = match.group(1)
        start_line = content[:match.start()].count('\n') + 1
        functions_to_remove.append((func_name, start_line))
    
    return functions_to_remove

def find_function_calls_in_webfetcher():
    """Find all calls to parser functions in webfetcher.py."""
    webfetcher_path = 'webfetcher.py'
    
    with open(webfetcher_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    target_functions = [
        'extract_meta',
        'extract_json_ld_content',
        'extract_from_modern_selectors', 
        'extract_text_from_html_fragment',
        'parse_date_like',
        'extract_list_content'
    ]
    
    call_locations = []
    for i, line in enumerate(lines, 1):
        for func in target_functions:
            if f'{func}(' in line and not line.strip().startswith('def '):
                call_locations.append({
                    'line': i,
                    'function': func,
                    'code': line.strip()
                })
    
    return call_locations

def check_parsers_module():
    """Verify parsers.py module has all required functions."""
    parsers_path = 'parsers.py'
    
    with open(parsers_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_functions = {
        'extract_meta': False,
        'extract_json_ld_content': False,
        'extract_from_modern_selectors': False,
        'extract_text_from_html_fragment': False,
        'parse_date_like': False,
        'extract_list_content': False
    }
    
    for func in required_functions:
        if f'def {func}(' in content:
            required_functions[func] = True
    
    return required_functions

def generate_integration_plan():
    """Generate detailed integration plan for Phase 2."""
    
    print("=" * 80)
    print("PHASE 2 INTEGRATION PLAN - PARSERS MODULE")
    print("=" * 80)
    print()
    
    # Step 1: Verify parsers module
    print("STEP 1: VERIFY PARSERS MODULE")
    print("-" * 40)
    parsers_status = check_parsers_module()
    all_present = all(parsers_status.values())
    
    for func, present in parsers_status.items():
        status = "✓" if present else "✗"
        print(f"  {status} {func}: {'Present' if present else 'MISSING'}")
    
    if not all_present:
        print("\n  ⚠️  WARNING: Not all functions present in parsers.py!")
        return False
    else:
        print("\n  ✅ All required functions present in parsers.py")
    
    print()
    
    # Step 2: Identify function calls
    print("STEP 2: FUNCTION CALLS TO UPDATE")
    print("-" * 40)
    calls = find_function_calls_in_webfetcher()
    
    call_summary = {}
    for call in calls:
        func = call['function']
        if func not in call_summary:
            call_summary[func] = []
        call_summary[func].append(call['line'])
    
    for func, lines in call_summary.items():
        print(f"  {func}: {len(lines)} calls at lines {lines[:5]}{'...' if len(lines) > 5 else ''}")
    
    print(f"\n  Total calls to update: {len(calls)}")
    print()
    
    # Step 3: Functions to remove
    print("STEP 3: FUNCTIONS TO REMOVE FROM WEBFETCHER")
    print("-" * 40)
    functions = analyze_webfetcher_functions()
    
    for func_name, line in functions:
        print(f"  Line {line}: def {func_name}(...)")
    
    print(f"\n  Total functions to remove: {len(functions)}")
    print()
    
    # Step 4: Implementation steps
    print("STEP 4: IMPLEMENTATION SEQUENCE")
    print("-" * 40)
    print("  1. Add import statement at top of webfetcher.py:")
    print("     import parsers")
    print()
    print("  2. Update all function calls:")
    for func in call_summary:
        print(f"     {func}() → parsers.{func}()")
    print()
    print("  3. Remove function definitions from webfetcher.py")
    print()
    print("  4. Fix BeautifulSoup dependencies in parsers.py:")
    print("     - Import BeautifulSoup at module level")
    print("     - Update get_beautifulsoup_parser() implementation")
    print()
    print("  5. Test the integration")
    print()
    
    # Step 5: Risk assessment
    print("STEP 5: RISK ASSESSMENT")
    print("-" * 40)
    print("  ✓ Low risk: Functions already extracted to parsers.py")
    print("  ✓ Simple integration: Only requires import and prefix changes")
    print("  ⚠️  Dependency risk: BeautifulSoup parser needs proper implementation")
    print("  ⚠️  Testing required: Verify all parsing functionality works")
    print()
    
    return True

def generate_sed_commands():
    """Generate sed commands for automated replacement."""
    
    print("=" * 80)
    print("AUTOMATED REPLACEMENT COMMANDS")
    print("=" * 80)
    print()
    
    functions = [
        'extract_meta',
        'extract_json_ld_content',
        'extract_from_modern_selectors',
        'extract_text_from_html_fragment',
        'parse_date_like',
        'extract_list_content'
    ]
    
    print("# Step 1: Add import statement (manual - add after line 39)")
    print("# import parsers")
    print()
    
    print("# Step 2: Update function calls")
    for func in functions:
        # Match function calls but not definitions
        print(f"sed -i '' 's/\\b{func}(/parsers.{func}(/g' webfetcher.py")
        print(f"sed -i '' 's/def parsers.{func}/def {func}/g' webfetcher.py  # Fix definitions")
    
    print()
    print("# Step 3: Manually remove function definitions after verification")
    print()

if __name__ == "__main__":
    success = generate_integration_plan()
    
    if success:
        print("=" * 80)
        print("READY FOR PHASE 2 INTEGRATION")
        print("=" * 80)
        
        generate_sed_commands()
    else:
        print("=" * 80)
        print("PHASE 2 CANNOT PROCEED - ISSUES DETECTED")
        print("=" * 80)