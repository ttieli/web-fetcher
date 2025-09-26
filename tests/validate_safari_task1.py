#!/usr/bin/env python3
"""
Safari Module Task 1 Validation - Corrected Version
Validates the actual implementation against requirements
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def validate_safari_module():
    """Validate Safari module structure and basic functionality."""
    
    base_path = Path(__file__).parent.parent
    results = {
        'structure': [],
        'imports': [],
        'interface': [],
        'issues': []
    }
    
    print("=" * 70)
    print("SAFARI MODULE TASK 1 VALIDATION")
    print("=" * 70)
    print()
    
    # 1. Check module structure
    print("1. Checking Safari Module Structure...")
    safari_path = base_path / "plugins" / "safari"
    required_files = ["__init__.py", "plugin.py", "config.py", "extractor.py"]
    
    for file in required_files:
        file_path = safari_path / file
        if file_path.exists():
            results['structure'].append(f"✅ {file} present")
        else:
            results['issues'].append(f"❌ {file} missing")
    
    # 2. Check imports
    print("\n2. Checking Safari Module Imports...")
    try:
        from plugins.safari import SafariFetcherPlugin
        results['imports'].append("✅ SafariFetcherPlugin can be imported")
    except ImportError as e:
        results['issues'].append(f"❌ Cannot import SafariFetcherPlugin: {e}")
    
    try:
        from plugins.safari import SafariExtractor
        results['imports'].append("✅ SafariExtractor can be imported")
    except ImportError as e:
        results['issues'].append(f"❌ Cannot import SafariExtractor: {e}")
    
    # 3. Check plugin interface
    print("\n3. Checking Plugin Interface Implementation...")
    try:
        from plugins.safari.plugin import SafariFetcherPlugin
        from plugins.base import BaseFetcherPlugin, IFetcherPlugin
        
        # Check inheritance
        if issubclass(SafariFetcherPlugin, BaseFetcherPlugin):
            results['interface'].append("✅ SafariFetcherPlugin extends BaseFetcherPlugin")
        else:
            results['issues'].append("❌ SafariFetcherPlugin doesn't extend BaseFetcherPlugin")
        
        # Check required methods
        plugin = SafariFetcherPlugin()
        required_methods = ['can_handle', 'fetch', 'is_available', 'get_capabilities']
        
        for method in required_methods:
            if hasattr(plugin, method):
                results['interface'].append(f"✅ {method} method present")
            else:
                results['issues'].append(f"❌ {method} method missing")
        
        # Check properties
        if hasattr(plugin, 'name'):
            results['interface'].append(f"✅ name property: '{plugin.name}'")
        else:
            results['issues'].append("❌ name property missing")
            
        if hasattr(plugin, 'priority'):
            results['interface'].append(f"✅ priority property: {plugin.priority}")
        else:
            results['issues'].append("❌ priority property missing")
            
    except Exception as e:
        results['issues'].append(f"❌ Interface check failed: {e}")
    
    # 4. Check for duplicate files
    print("\n4. Checking for Duplicate Files...")
    duplicates = ["safari_config.py", "safari_extractor.py"]
    for file in duplicates:
        if (base_path / file).exists():
            results['issues'].append(f"⚠️  Duplicate file in root: {file}")
    
    # Report results
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    
    print("\n📁 Module Structure:")
    for item in results['structure']:
        print(f"   {item}")
    
    print("\n📦 Import Tests:")
    for item in results['imports']:
        print(f"   {item}")
    
    print("\n🔌 Interface Compliance:")
    for item in results['interface']:
        print(f"   {item}")
    
    if results['issues']:
        print("\n❌ Issues Found:")
        for issue in results['issues']:
            print(f"   {issue}")
    
    # Summary
    total_checks = len(results['structure']) + len(results['imports']) + len(results['interface'])
    issues_count = len(results['issues'])
    
    print("\n" + "=" * 70)
    if issues_count == 0:
        print(f"✅ VALIDATION PASSED: {total_checks}/{total_checks} checks successful")
        print("✅ Task 1 COMPLETE - Ready for Task 2")
    else:
        print(f"⚠️  VALIDATION INCOMPLETE: {issues_count} issues found")
        print("⚠️  Address issues before proceeding to Task 2")
    print("=" * 70)
    
    return issues_count == 0

if __name__ == "__main__":
    success = validate_safari_module()
    sys.exit(0 if success else 1)