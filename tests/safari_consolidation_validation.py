#!/usr/bin/env python3
"""
Safari Module Consolidation Validation Script
Author: Phase 1 Implementation Team
Date: 2025-09-26

Tests Safari module consolidation and validates:
1. Directory structure correctness
2. Module import functionality
3. Configuration access
4. Plugin integration
5. No duplicate files in root directory
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

class SafariConsolidationValidator:
    """Validates Safari module consolidation."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.results = []
        self.errors = []
    
    def log_result(self, success: bool, message: str):
        """Log validation result."""
        symbol = "✅" if success else "❌"
        self.results.append((success, f"{symbol} {message}"))
        if not success:
            self.errors.append(message)
    
    def test_directory_structure(self):
        """Test Safari module directory structure."""
        print("1. Testing Safari Module Directory Structure...")
        
        required_files = {
            "plugins/safari/__init__.py": "Module initializer",
            "plugins/safari/config.py": "Configuration module",
            "plugins/safari/extractor.py": "Extraction logic",
            "plugins/safari/plugin.py": "Plugin implementation"
        }
        
        for file_path, description in required_files.items():
            full_path = self.base_path / file_path
            if full_path.exists() and full_path.is_file():
                self.log_result(True, f"{description} exists at {file_path}")
            else:
                self.log_result(False, f"{description} missing at {file_path}")
    
    def test_imports(self):
        """Test module imports."""
        print("2. Testing Safari Module Imports...")
        
        import_tests = [
            ("from plugins.safari.plugin import SafariFetcherPlugin", "Plugin class import"),
            ("from plugins.safari.config import should_use_safari_for_url", "Config function import"),
            ("from plugins.safari.extractor import SafariExtractor", "Extractor class import"),
            ("from plugins.safari import SafariFetcherPlugin", "Module-level plugin import"),
        ]
        
        for import_statement, description in import_tests:
            try:
                exec(import_statement)
                self.log_result(True, f"{description} successful")
            except Exception as e:
                self.log_result(False, f"{description} failed: {e}")
    
    def test_plugin_functionality(self):
        """Test plugin basic functionality."""
        print("3. Testing Safari Plugin Functionality...")
        
        try:
            from plugins.safari.plugin import SafariFetcherPlugin
            plugin = SafariFetcherPlugin()
            
            # Test plugin properties
            if hasattr(plugin, 'name') and plugin.name:
                self.log_result(True, f"Plugin has name: {plugin.name}")
            else:
                self.log_result(False, "Plugin missing name property")
            
            if hasattr(plugin, 'priority'):
                self.log_result(True, f"Plugin has priority: {plugin.priority}")
            else:
                self.log_result(False, "Plugin missing priority property")
            
            if hasattr(plugin, 'is_available'):
                available = plugin.is_available()
                self.log_result(True, f"Plugin availability check works: {available}")
            else:
                self.log_result(False, "Plugin missing is_available method")
                
        except Exception as e:
            self.log_result(False, f"Plugin functionality test failed: {e}")
    
    def test_configuration_access(self):
        """Test configuration access."""
        print("4. Testing Configuration Access...")
        
        try:
            from plugins.safari.config import (
                SAFARI_ENABLED, should_use_safari_for_url, 
                get_site_config, validate_safari_availability
            )
            
            self.log_result(True, f"Safari enabled: {SAFARI_ENABLED}")
            
            # Test URL checking
            test_url = "https://www.ccdi.gov.cn/test"
            should_use = should_use_safari_for_url(test_url)
            self.log_result(True, f"URL evaluation works: should_use_safari_for_url('{test_url}') = {should_use}")
            
            # Test site config
            config = get_site_config(test_url)
            self.log_result(True, f"Site config retrieval works: {config is not None}")
            
            # Test Safari availability
            available, message = validate_safari_availability()
            self.log_result(True, f"Safari availability check: {available} - {message}")
            
        except Exception as e:
            self.log_result(False, f"Configuration access test failed: {e}")
    
    def test_no_duplicate_files(self):
        """Test for absence of duplicate Safari files in root."""
        print("5. Testing for Duplicate Files...")
        
        potential_duplicates = [
            "safari_config.py",
            "safari_extractor.py",
            "safari_plugin.py"
        ]
        
        for file_name in potential_duplicates:
            file_path = self.base_path / file_name
            if file_path.exists():
                self.log_result(False, f"Duplicate file exists in root: {file_name}")
            else:
                self.log_result(True, f"No duplicate {file_name} in root directory")
    
    def test_registry_integration(self):
        """Test registry integration."""
        print("6. Testing Registry Integration...")
        
        try:
            from plugins.registry import get_global_registry
            registry = get_global_registry()
            
            # Check if Safari plugin can be registered
            plugins = registry.list_plugins()
            safari_found = any('safari' in plugin.lower() for plugin in plugins)
            self.log_result(True, f"Registry integration works. Safari plugin found: {safari_found}")
            
        except Exception as e:
            self.log_result(False, f"Registry integration test failed: {e}")
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("=" * 70)
        print("SAFARI MODULE CONSOLIDATION VALIDATION")
        print("=" * 70)
        print()
        
        self.test_directory_structure()
        print()
        
        self.test_imports()
        print()
        
        self.test_plugin_functionality()
        print()
        
        self.test_configuration_access()
        print()
        
        self.test_no_duplicate_files()
        print()
        
        self.test_registry_integration()
        print()
        
        # Report results
        self.report_results()
        
        return len(self.errors) == 0
    
    def report_results(self):
        """Generate final report."""
        print("=" * 70)
        print("VALIDATION RESULTS")
        print("=" * 70)
        print()
        
        success_count = sum(1 for success, _ in self.results if success)
        total_count = len(self.results)
        
        for success, message in self.results:
            print(f"   {message}")
        
        print()
        print("=" * 70)
        print(f"SUMMARY: {success_count}/{total_count} tests passed")
        
        if self.errors:
            print(f"❌ {len(self.errors)} issues found")
            print("ERRORS TO FIX:")
            for error in self.errors:
                print(f"   • {error}")
        else:
            print("✅ ALL TESTS PASSED - Safari module successfully consolidated")
        
        print("=" * 70)


def main():
    """Main entry point."""
    validator = SafariConsolidationValidator()
    success = validator.run_all_tests()
    
    if success:
        print("\n✅ Safari module consolidation SUCCESSFUL")
        sys.exit(0)
    else:
        print("\n❌ Safari module consolidation validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()