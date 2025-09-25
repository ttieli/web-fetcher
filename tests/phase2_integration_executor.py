#!/usr/bin/env python3
"""
Phase 2 Integration Executor
Automated script to perform the parsers module integration.
Run with --dry-run first to preview changes.
"""

import os
import re
import sys
import argparse
from typing import List, Tuple

class Phase2Integrator:
    """Handles the integration of parsers module into webfetcher."""
    
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.webfetcher_path = 'webfetcher.py'
        self.parsers_path = 'parsers.py'
        self.changes_log = []
        
    def log_change(self, action: str, detail: str):
        """Log a change for reporting."""
        self.changes_log.append((action, detail))
        print(f"  {'[DRY RUN]' if self.dry_run else '[EXECUTE]'} {action}: {detail}")
    
    def step1_add_import(self) -> bool:
        """Step 1: Add parsers import to webfetcher.py."""
        print("\n" + "=" * 60)
        print("STEP 1: ADD PARSERS IMPORT")
        print("=" * 60)
        
        with open(self.webfetcher_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find the right place to add import (after core.downloader import)
        import_line = None
        for i, line in enumerate(lines):
            if 'from core.downloader import' in line:
                import_line = i + 1
                break
        
        if import_line is None:
            print("  ❌ ERROR: Could not find appropriate location for import")
            return False
        
        # Check if already imported
        if any('import parsers' in line for line in lines):
            print("  ✓ parsers module already imported")
            return True
        
        # Add the import
        new_import = "\n# Parser modules\nimport parsers\n"
        
        if not self.dry_run:
            lines.insert(import_line, new_import)
            with open(self.webfetcher_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        
        self.log_change("ADD IMPORT", f"Line {import_line}: import parsers")
        return True
    
    def step2_update_function_calls(self) -> bool:
        """Step 2: Update all function calls to use parsers prefix."""
        print("\n" + "=" * 60)
        print("STEP 2: UPDATE FUNCTION CALLS")
        print("=" * 60)
        
        with open(self.webfetcher_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Functions to update
        functions = [
            'extract_meta',
            'extract_json_ld_content',
            'extract_from_modern_selectors',
            'extract_text_from_html_fragment',
            'parse_date_like',
            'extract_list_content'
        ]
        
        updated_content = content
        total_replacements = 0
        
        for func in functions:
            # Pattern to match function calls but not definitions
            # Negative lookbehind for 'def ' and 'parsers.'
            pattern = rf'(?<!def )(?<!parsers\.)\b{func}\('
            replacement = f'parsers.{func}('
            
            # Count replacements
            matches = re.findall(pattern, updated_content)
            count = len(matches)
            
            if count > 0:
                updated_content = re.sub(pattern, replacement, updated_content)
                self.log_change(f"UPDATE {func}", f"{count} calls updated")
                total_replacements += count
        
        if not self.dry_run and total_replacements > 0:
            with open(self.webfetcher_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
        
        print(f"\n  Total function calls updated: {total_replacements}")
        return total_replacements > 0
    
    def step3_remove_duplicate_functions(self) -> bool:
        """Step 3: Remove duplicate function definitions from webfetcher."""
        print("\n" + "=" * 60)
        print("STEP 3: REMOVE DUPLICATE FUNCTIONS")
        print("=" * 60)
        
        with open(self.webfetcher_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Functions to remove with their approximate line ranges
        functions_to_remove = [
            ('extract_meta', 1752, 1756),
            ('extract_json_ld_content', 1757, 1809),
            ('extract_from_modern_selectors', 1810, 1857),
            ('extract_text_from_html_fragment', 1858, 1889),
            ('parse_date_like', 1890, 1924),
            ('extract_list_content', 3480, 3514)
        ]
        
        # Build list of line ranges to remove
        lines_to_remove = set()
        
        for func_name, start_hint, end_hint in functions_to_remove:
            # Find actual function boundaries
            func_start = None
            func_end = None
            
            # Search around the hint lines
            search_start = max(0, start_hint - 10)
            search_end = min(len(lines), end_hint + 10)
            
            for i in range(search_start, search_end):
                if i < len(lines):
                    if f'def {func_name}(' in lines[i]:
                        func_start = i
                        # Find the end of the function (next def or class)
                        for j in range(i + 1, min(len(lines), i + 200)):
                            if lines[j].startswith('def ') or lines[j].startswith('class '):
                                func_end = j - 1
                                # Remove trailing blank lines
                                while func_end > func_start and lines[func_end].strip() == '':
                                    func_end -= 1
                                break
                        break
            
            if func_start is not None and func_end is not None:
                for line_num in range(func_start, func_end + 1):
                    lines_to_remove.add(line_num)
                self.log_change(f"REMOVE {func_name}", 
                              f"Lines {func_start+1}-{func_end+1} ({func_end-func_start+1} lines)")
        
        if not self.dry_run and lines_to_remove:
            # Create new content without removed lines
            new_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
            with open(self.webfetcher_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
        
        print(f"\n  Total lines removed: {len(lines_to_remove)}")
        return len(lines_to_remove) > 0
    
    def step4_verify_integration(self) -> bool:
        """Step 4: Verify the integration was successful."""
        print("\n" + "=" * 60)
        print("STEP 4: VERIFY INTEGRATION")
        print("=" * 60)
        
        if self.dry_run:
            print("  [SKIP] Verification skipped in dry-run mode")
            return True
        
        # Try to import both modules
        try:
            # Add parent directory to path
            sys.path.insert(0, '..')
            
            # Try importing
            import parsers
            print("  ✓ parsers module imports successfully")
            
            # Check for required functions
            required_functions = [
                'extract_meta',
                'parse_date_like',
                'extract_list_content'
            ]
            
            for func in required_functions:
                if hasattr(parsers, func):
                    print(f"  ✓ parsers.{func} available")
                else:
                    print(f"  ❌ parsers.{func} NOT FOUND")
                    return False
            
            # Try importing webfetcher (basic syntax check)
            try:
                with open(self.webfetcher_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                compile(code, self.webfetcher_path, 'exec')
                print("  ✓ webfetcher.py syntax valid")
            except SyntaxError as e:
                print(f"  ❌ webfetcher.py has syntax error: {e}")
                return False
            
            return True
            
        except ImportError as e:
            print(f"  ❌ Import error: {e}")
            return False
        finally:
            # Clean up path
            if '..' in sys.path:
                sys.path.remove('..')
    
    def generate_report(self):
        """Generate final report of changes."""
        print("\n" + "=" * 60)
        print("INTEGRATION REPORT")
        print("=" * 60)
        
        if self.dry_run:
            print("\n🔍 DRY RUN MODE - No actual changes made")
            print("   Run without --dry-run to apply changes")
        else:
            print("\n✅ INTEGRATION COMPLETE")
        
        print("\nChanges Summary:")
        print("-" * 40)
        
        action_groups = {}
        for action, detail in self.changes_log:
            action_type = action.split()[0]
            if action_type not in action_groups:
                action_groups[action_type] = []
            action_groups[action_type].append(detail)
        
        for action_type, details in action_groups.items():
            print(f"\n{action_type}:")
            for detail in details[:5]:  # Show first 5
                print(f"  • {detail}")
            if len(details) > 5:
                print(f"  • ... and {len(details)-5} more")
        
        # File size analysis
        if os.path.exists(self.webfetcher_path):
            size = os.path.getsize(self.webfetcher_path)
            lines = sum(1 for _ in open(self.webfetcher_path))
            print(f"\nFile Statistics:")
            print(f"  • Size: {size:,} bytes")
            print(f"  • Lines: {lines:,}")
    
    def run(self) -> bool:
        """Execute all integration steps."""
        print("=" * 60)
        print("PHASE 2 INTEGRATION EXECUTOR")
        print("=" * 60)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTE'}")
        
        # Check prerequisites
        if not os.path.exists(self.webfetcher_path):
            print(f"❌ ERROR: {self.webfetcher_path} not found")
            return False
        
        if not os.path.exists(self.parsers_path):
            print(f"❌ ERROR: {self.parsers_path} not found")
            return False
        
        # Execute steps
        success = True
        
        if not self.step1_add_import():
            success = False
        
        if success and not self.step2_update_function_calls():
            print("⚠️  Warning: No function calls needed updating")
        
        if success and not self.step3_remove_duplicate_functions():
            print("⚠️  Warning: No duplicate functions found to remove")
        
        if success and not self.dry_run:
            if not self.step4_verify_integration():
                success = False
        
        # Generate report
        self.generate_report()
        
        return success

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Phase 2 Parsers Module Integration')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview changes without modifying files')
    parser.add_argument('--force', action='store_true',
                       help='Force execution even if checks fail')
    
    args = parser.parse_args()
    
    # Create integrator
    integrator = Phase2Integrator(dry_run=args.dry_run)
    
    # Run integration
    success = integrator.run()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ PHASE 2 INTEGRATION SUCCESSFUL")
        print("=" * 60)
        
        if args.dry_run:
            print("\nTo apply changes, run:")
            print("  python phase2_integration_executor.py")
        else:
            print("\nNext steps:")
            print("  1. Test with: python ../webfetcher.py 'https://example.com'")
            print("  2. Run full test suite")
            print("  3. Commit changes to git")
    else:
        print("\n" + "=" * 60)
        print("❌ PHASE 2 INTEGRATION FAILED")
        print("=" * 60)
        
        if not args.force:
            print("\nTroubleshooting:")
            print("  1. Check error messages above")
            print("  2. Ensure parsers.py has all required functions")
            print("  3. Try running with --dry-run first")
            print("  4. Use --force to bypass checks (use with caution)")
        
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())