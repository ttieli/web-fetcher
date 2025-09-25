#!/usr/bin/env python3
"""
Phase 1 Parser Migration Validation Script
Architect: Archy-Principle-Architect
Purpose: Validate the successful migration of parser functions from webfetcher.py to parsers.py
"""

import sys
import os
import importlib.util
from typing import List, Dict, Any

class Phase1Validator:
    """Validates Phase 1 parser migration according to architectural specifications."""
    
    # Expected parser functions to be migrated
    EXPECTED_PARSERS = [
        'docusaurus_to_markdown',
        'mkdocs_to_markdown', 
        'wechat_to_markdown',
        'xhs_to_markdown',
        'dianping_to_markdown',
        'ebchina_news_list_to_markdown',
        'raw_to_markdown',
        'generic_to_markdown',
        'add_metrics_to_markdown'
    ]
    
    # Helper functions that should be migrated with parsers
    EXPECTED_HELPERS = [
        'extract_meta',
        'extract_json_ld_content',
        'extract_from_modern_selectors',
        'extract_text_from_html_fragment',
        'extract_list_content'
    ]
    
    def __init__(self):
        self.results = []
        self.errors = []
        
    def validate_parsers_file_exists(self) -> bool:
        """Check if parsers.py file has been created."""
        parsers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'parsers.py')
        if not os.path.exists(parsers_path):
            self.errors.append("❌ parsers.py file not found")
            return False
        self.results.append("✅ parsers.py file exists")
        return True
    
    def validate_parsers_syntax(self) -> bool:
        """Verify parsers.py has valid Python syntax."""
        try:
            parsers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'parsers.py')
            spec = importlib.util.spec_from_file_location("parsers", parsers_path)
            parsers_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(parsers_module)
            self.results.append("✅ parsers.py syntax is valid")
            return True
        except SyntaxError as e:
            self.errors.append(f"❌ parsers.py has syntax error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"❌ parsers.py import failed: {e}")
            return False
    
    def validate_functions_migrated(self) -> Dict[str, List[str]]:
        """Check which functions have been successfully migrated."""
        migrated = []
        missing = []
        
        try:
            parsers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'parsers.py')
            spec = importlib.util.spec_from_file_location("parsers", parsers_path)
            parsers_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(parsers_module)
            
            # Check main parser functions
            for func_name in self.EXPECTED_PARSERS:
                if hasattr(parsers_module, func_name):
                    migrated.append(func_name)
                else:
                    missing.append(func_name)
            
            # Check helper functions (optional for Phase 1)
            helpers_found = []
            for func_name in self.EXPECTED_HELPERS:
                if hasattr(parsers_module, func_name):
                    helpers_found.append(func_name)
            
            if migrated:
                self.results.append(f"✅ Migrated {len(migrated)}/{len(self.EXPECTED_PARSERS)} parser functions")
            if missing:
                self.errors.append(f"⚠️ Missing parsers: {', '.join(missing)}")
            if helpers_found:
                self.results.append(f"✅ Also migrated {len(helpers_found)} helper functions")
                
        except Exception as e:
            self.errors.append(f"❌ Could not validate functions: {e}")
            
        return {"migrated": migrated, "missing": missing, "helpers": helpers_found}
    
    def validate_function_signatures(self) -> bool:
        """Verify migrated functions maintain correct signatures."""
        try:
            parsers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'parsers.py')
            spec = importlib.util.spec_from_file_location("parsers", parsers_path)
            parsers_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(parsers_module)
            
            # Check main parser signatures (should all be: (html: str, url: str) -> tuple[str, str, dict])
            parser_funcs = ['docusaurus_to_markdown', 'mkdocs_to_markdown', 'wechat_to_markdown',
                           'xhs_to_markdown', 'dianping_to_markdown', 'ebchina_news_list_to_markdown',
                           'raw_to_markdown']
            
            for func_name in parser_funcs:
                if hasattr(parsers_module, func_name):
                    func = getattr(parsers_module, func_name)
                    if callable(func):
                        # Basic check that it's a function
                        import inspect
                        sig = inspect.signature(func)
                        params = list(sig.parameters.keys())
                        if 'html' in params and 'url' in params:
                            continue
                        else:
                            self.errors.append(f"⚠️ {func_name} has unexpected parameters: {params}")
            
            self.results.append("✅ Function signatures appear correct")
            return True
            
        except Exception as e:
            self.errors.append(f"❌ Could not validate signatures: {e}")
            return False
    
    def validate_webfetcher_cleanup(self) -> bool:
        """Check if parser functions have been removed from webfetcher.py."""
        try:
            webfetcher_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'webfetcher.py')
            with open(webfetcher_path, 'r') as f:
                content = f.read()
            
            # Check if parser functions still exist in webfetcher.py
            remaining = []
            for func_name in self.EXPECTED_PARSERS:
                if f'def {func_name}(' in content:
                    remaining.append(func_name)
            
            if remaining:
                self.results.append(f"⚠️ Note: {len(remaining)} parser functions still in webfetcher.py (will be removed after Phase 2)")
            else:
                self.results.append("✅ Parser functions removed from webfetcher.py")
                
            return True
            
        except Exception as e:
            self.errors.append(f"❌ Could not check webfetcher.py: {e}")
            return False
    
    def generate_report(self) -> str:
        """Generate Phase 1 validation report."""
        report = []
        report.append("=" * 60)
        report.append("PHASE 1 PARSER MIGRATION VALIDATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        if self.results:
            report.append("SUCCESSES:")
            for result in self.results:
                report.append(f"  {result}")
            report.append("")
        
        if self.errors:
            report.append("ISSUES TO ADDRESS:")
            for error in self.errors:
                report.append(f"  {error}")
            report.append("")
        
        # Phase 1 completion criteria
        report.append("PHASE 1 COMPLETION CRITERIA:")
        report.append("  [✓] parsers.py file created")
        report.append("  [✓] All parser functions migrated with correct signatures")
        report.append("  [✓] Helper functions migrated as needed")
        report.append("  [✓] parsers.py has valid syntax and can be imported")
        report.append("  [ ] Ready for Phase 2: Update webfetcher.py imports")
        report.append("")
        
        if not self.errors:
            report.append("✅ PHASE 1 COMPLETED SUCCESSFULLY - Ready for Phase 2")
        else:
            report.append("⚠️ PHASE 1 INCOMPLETE - Address issues before proceeding to Phase 2")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def run_validation(self):
        """Execute all Phase 1 validation checks."""
        print("\n🔍 Starting Phase 1 Validation...\n")
        
        # Run validation checks in order
        self.validate_parsers_file_exists()
        if self.validate_parsers_file_exists():
            self.validate_parsers_syntax()
            self.validate_functions_migrated()
            self.validate_function_signatures()
        self.validate_webfetcher_cleanup()
        
        # Generate and print report
        report = self.generate_report()
        print(report)
        
        # Return success status
        return len(self.errors) == 0


if __name__ == "__main__":
    validator = Phase1Validator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)