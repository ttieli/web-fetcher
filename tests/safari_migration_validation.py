#!/usr/bin/env python3
"""
Phase 0: Safari Migration Validation and Code Consistency Check
Author: Archy-Principle-Architect
Date: 2025-09-26

This script validates the Safari module migration and identifies code consistency issues
that need to be fixed before proceeding with Phase 1 implementation.
"""

import sys
import os
import importlib
import traceback
from typing import Dict, List, Tuple
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Phase0Validator:
    """Phase 0 validation for code consistency and migration status."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.successes = []
        self.base_path = Path(__file__).parent.parent
    
    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("=" * 70)
        print("PHASE 0: Pre-Implementation Validation")
        print("=" * 70)
        print()
        
        # Check 1: Safari module migration status
        print("1. Checking Safari Module Migration...")
        self.check_safari_migration()
        print()
        
        # Check 2: Chrome Manager consistency
        print("2. Checking Chrome Manager Class Consistency...")
        self.check_chrome_manager_consistency()
        print()
        
        # Check 3: Selenium plugin priority mechanism
        print("3. Checking Selenium Plugin Priority Mechanism...")
        self.check_selenium_priority()
        print()
        
        # Check 4: Registry configuration integration
        print("4. Checking Registry Configuration Integration...")
        self.check_registry_config()
        print()
        
        # Check 5: Plugin imports and dependencies
        print("5. Checking Plugin Import Consistency...")
        self.check_plugin_imports()
        print()
        
        # Report results
        self.report_results()
        
        return len(self.issues) == 0
    
    def check_safari_migration(self):
        """Validate Safari module migration status."""
        # Check if Safari module exists in plugins/safari/
        safari_module_path = self.base_path / "plugins" / "safari"
        
        required_files = {
            "__init__.py": "Safari module initializer",
            "plugin.py": "Safari plugin implementation",
            "config.py": "Safari configuration",
            "extractor.py": "Safari content extractor"
        }
        
        for file_name, description in required_files.items():
            file_path = safari_module_path / file_name
            if file_path.exists():
                self.successes.append(f"✅ Found {description}: {file_path.relative_to(self.base_path)}")
            else:
                self.issues.append(f"❌ Missing {description}: {file_path.relative_to(self.base_path)}")
        
        # Check for duplicate Safari files in root
        root_safari_files = ["safari_config.py", "safari_extractor.py"]
        for file_name in root_safari_files:
            file_path = self.base_path / file_name
            if file_path.exists():
                self.warnings.append(f"⚠️  Duplicate Safari file in root: {file_name}")
    
    def check_chrome_manager_consistency(self):
        """Check ChromeManager class naming consistency."""
        chrome_manager_path = self.base_path / "plugins" / "selenium" / "chrome_manager.py"
        
        if not chrome_manager_path.exists():
            self.issues.append(f"❌ ChromeManager file not found: {chrome_manager_path.relative_to(self.base_path)}")
            return
        
        with open(chrome_manager_path, 'r') as f:
            content = f.read()
        
        # Check class definition
        if "class ChromeManager" in content:
            self.successes.append("✅ ChromeManager class correctly named")
        elif "class ChromeDebugManager" in content:
            self.issues.append("❌ ChromeManager class incorrectly named as ChromeDebugManager")
        else:
            self.issues.append("❌ ChromeManager class not found in chrome_manager.py")
        
        # Check imports in selenium_plugin.py
        selenium_plugin_path = self.base_path / "plugins" / "selenium" / "selenium_plugin.py"
        if selenium_plugin_path.exists():
            with open(selenium_plugin_path, 'r') as f:
                plugin_content = f.read()
            
            if "from .chrome_manager import ChromeManager" in plugin_content:
                self.successes.append("✅ ChromeManager import is consistent in selenium_plugin.py")
            else:
                self.issues.append("❌ ChromeManager import inconsistency in selenium_plugin.py")
    
    def check_selenium_priority(self):
        """Check Selenium plugin priority mechanism."""
        selenium_plugin_path = self.base_path / "plugins" / "selenium" / "selenium_plugin.py"
        
        if not selenium_plugin_path.exists():
            self.issues.append(f"❌ Selenium plugin not found: {selenium_plugin_path.relative_to(self.base_path)}")
            return
        
        with open(selenium_plugin_path, 'r') as f:
            content = f.read()
        
        # Check priority property implementation
        if "def priority(self)" in content:
            # Check for problematic getattr usage
            if "getattr(self," in content and "_priority" in content:
                self.issues.append("❌ Selenium plugin uses problematic getattr for priority")
                self.issues.append("   Fix: Line 46 should return FetchPriority.NORMAL directly")
            else:
                self.successes.append("✅ Selenium plugin priority property looks correct")
        else:
            self.issues.append("❌ Selenium plugin missing priority property")
    
    def check_registry_config(self):
        """Check registry configuration integration."""
        registry_path = self.base_path / "plugins" / "registry.py"
        
        if not registry_path.exists():
            self.issues.append(f"❌ Registry file not found: {registry_path.relative_to(self.base_path)}")
            return
        
        with open(registry_path, 'r') as f:
            content = f.read()
        
        # Check for PluginConfig integration
        if "from .plugin_config import PluginConfig" in content:
            self.successes.append("✅ Registry imports PluginConfig")
        elif "from plugin_config import PluginConfig" in content:
            self.warnings.append("⚠️  Registry uses relative import for PluginConfig (should use .plugin_config)")
        else:
            self.issues.append("❌ Registry missing PluginConfig import")
        
        # Check for is_plugin_enabled usage
        if "PluginConfig.is_plugin_enabled" in content:
            self.successes.append("✅ Registry uses PluginConfig.is_plugin_enabled")
        else:
            self.warnings.append("⚠️  Registry may not be using configuration-based plugin enabling")
    
    def check_plugin_imports(self):
        """Check plugin import consistency."""
        plugins_to_check = [
            ("HTTPFetcherPlugin", "plugins/http_fetcher.py"),
            ("SeleniumFetcherPlugin", "plugins/selenium/selenium_plugin.py"),
            ("CurlPlugin", "plugins/curl.py"),
            ("SafariPlugin", "plugins/safari/plugin.py")
        ]
        
        for plugin_name, expected_path in plugins_to_check:
            full_path = self.base_path / expected_path
            if full_path.exists():
                try:
                    # Try to import the module
                    module_path = expected_path.replace('/', '.').replace('.py', '')
                    if module_path.startswith('plugins.'):
                        module = importlib.import_module(module_path)
                        if hasattr(module, plugin_name):
                            self.successes.append(f"✅ {plugin_name} can be imported from {expected_path}")
                        else:
                            self.issues.append(f"❌ {plugin_name} class not found in {expected_path}")
                except ImportError as e:
                    self.warnings.append(f"⚠️  Cannot import {plugin_name}: {str(e)}")
            else:
                if "Safari" in plugin_name:
                    self.warnings.append(f"⚠️  {plugin_name} file not at expected location: {expected_path}")
                else:
                    self.issues.append(f"❌ {plugin_name} file missing: {expected_path}")
    
    def report_results(self):
        """Generate comprehensive report."""
        print("=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)
        print()
        
        if self.successes:
            print("✅ SUCCESSES:")
            for success in self.successes:
                print(f"   {success}")
            print()
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   {warning}")
            print()
        
        if self.issues:
            print("❌ CRITICAL ISSUES TO FIX:")
            for issue in self.issues:
                print(f"   {issue}")
            print()
            
            print("REQUIRED FIXES FOR PHASE 0:")
            print("-" * 40)
            
            # Provide specific fix instructions
            if any("ChromeDebugManager" in issue for issue in self.issues):
                print("1. Fix ChromeManager class naming:")
                print("   - In chrome_manager.py, rename ChromeDebugManager to ChromeManager")
                print("   - Update all imports accordingly")
                print()
            
            if any("getattr" in issue for issue in self.issues):
                print("2. Fix Selenium priority mechanism:")
                print("   - In selenium_plugin.py line 46:")
                print("   - Change: return getattr(self, '_priority', FetchPriority.NORMAL)")
                print("   - To: return FetchPriority.NORMAL")
                print()
            
            if any("Safari" in issue and "Missing" in issue for issue in self.issues):
                print("3. Complete Safari module migration:")
                print("   - Move safari_extractor.py to plugins/safari/extractor.py")
                print("   - Move safari_config.py to plugins/safari/config.py")
                print("   - Ensure plugins/safari/__init__.py exists")
                print()
        else:
            print("✅ ALL CHECKS PASSED - Ready for Phase 1")
        
        print()
        print("=" * 70)
        print(f"Summary: {len(self.successes)} successes, {len(self.warnings)} warnings, {len(self.issues)} issues")
        print("=" * 70)


def main():
    """Main entry point."""
    validator = Phase0Validator()
    success = validator.validate_all()
    
    if success:
        print("\n✅ Phase 0 validation PASSED - Ready to proceed with Phase 1")
        sys.exit(0)
    else:
        print("\n❌ Phase 0 validation FAILED - Fix issues before proceeding")
        sys.exit(1)


if __name__ == "__main__":
    main()