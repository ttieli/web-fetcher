#!/usr/bin/env python3
"""
Phase 2: Automated Safari and Plugin Removal Script
This script safely removes Safari and plugin system code from webfetcher.py
"""

import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

class Phase2Remover:
    def __init__(self, webfetcher_path="webfetcher.py"):
        self.webfetcher_path = Path(webfetcher_path)
        self.backup_path = None
        self.content = None
        self.original_content = None
        
    def create_backup(self):
        """Create a backup of the original file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = self.webfetcher_path.parent / f"webfetcher_backup_{timestamp}.py"
        shutil.copy2(self.webfetcher_path, self.backup_path)
        print(f"✓ Backup created: {self.backup_path}")
        
    def load_content(self):
        """Load the webfetcher.py content"""
        self.content = self.webfetcher_path.read_text()
        self.original_content = self.content
        print(f"✓ Loaded {len(self.content)} bytes from {self.webfetcher_path}")
        
    def remove_safari_imports(self):
        """Step 1: Remove Safari import block (lines ~44-58)"""
        print("\n=== Step 1: Removing Safari imports ===")
        
        # Pattern to match Safari import block
        safari_import_pattern = r'# Safari extraction integration.*?logging\.warning\("Safari integration unavailable[^"]*"\)'
        
        # Replace with disabled message
        replacement = "# Safari integration removed - using urllib/curl only\nSAFARI_AVAILABLE = False"
        
        self.content = re.sub(safari_import_pattern, replacement, self.content, flags=re.DOTALL)
        print("✓ Safari import block removed")
        
    def remove_safari_preemptive_function(self):
        """Step 2: Remove requires_safari_preemptively function"""
        print("\n=== Step 2: Removing Safari preemptive check function ===")
        
        # Pattern to match the entire function
        pattern = r'def requires_safari_preemptively\(url: str\) -> bool:.*?return False\n(?=\n|\Z)'
        
        self.content = re.sub(pattern, '', self.content, flags=re.DOTALL)
        print("✓ requires_safari_preemptively function removed")
        
    def simplify_fetch_html_with_retry(self):
        """Step 3: Remove Safari logic from fetch_html_with_retry"""
        print("\n=== Step 3: Simplifying fetch_html_with_retry ===")
        
        # Remove preemptive Safari check block
        pattern1 = r'    # Check if this URL requires preemptive Safari usage.*?logging\.info\(f"Falling back to standard HTTP methods[^"]*"\)\n'
        self.content = re.sub(pattern1, '', self.content, flags=re.DOTALL)
        
        # Remove Safari fallback for 403 errors
        pattern2 = r'            # Immediate Safari fallback for HTTP 403 errors.*?logging\.warning\(f"HTTP 403 detected but Safari not available[^"]*"\)\n'
        self.content = re.sub(pattern2, '', self.content, flags=re.DOTALL)
        
        # Remove Safari fallback for non-retryable errors
        pattern3 = r'                # Check Safari fallback for non-retryable errors too.*?# Continue to original error handling\n'
        self.content = re.sub(pattern3, '', self.content, flags=re.DOTALL)
        
        # Remove Safari fallback after retries exhausted
        pattern4 = r'    # All retry attempts exhausted - try Safari fallback before giving up.*?# Continue to original error handling\n    \n    # All retry attempts exhausted and Safari fallback failed/unavailable\n'
        self.content = re.sub(pattern4, '    # All retry attempts exhausted\n', self.content, flags=re.DOTALL)
        
        print("✓ Safari logic removed from fetch_html_with_retry")
        
    def remove_plugin_imports(self):
        """Step 4: Remove plugin system imports"""
        print("\n=== Step 4: Removing plugin system imports ===")
        
        # Pattern to match plugin import block
        plugin_import_pattern = r'# Plugin system integration \(optional\).*?PLUGIN_SYSTEM_AVAILABLE = False\n'
        
        # Remove entirely
        self.content = re.sub(plugin_import_pattern, '', self.content, flags=re.DOTALL)
        print("✓ Plugin system import block removed")
        
    def remove_fetch_html_with_plugins(self):
        """Step 5: Remove fetch_html_with_plugins function"""
        print("\n=== Step 5: Removing fetch_html_with_plugins ===")
        
        # Pattern to match the entire function
        pattern = r'def fetch_html_with_plugins\(url: str.*?\n    return html, metrics\n'
        
        self.content = re.sub(pattern, '', self.content, flags=re.DOTALL)
        print("✓ fetch_html_with_plugins function removed")
        
    def update_fetch_html_assignment(self):
        """Step 6: Update fetch_html to point directly to fetch_html_with_retry"""
        print("\n=== Step 6: Updating fetch_html assignment ===")
        
        # Find and replace the assignment
        pattern = r'fetch_html = fetch_html_with_plugins\nfetch_html_with_metrics = fetch_html_with_plugins'
        replacement = 'fetch_html = fetch_html_with_retry\nfetch_html_with_metrics = fetch_html_with_retry'
        
        self.content = re.sub(pattern, replacement, self.content)
        print("✓ fetch_html now points to fetch_html_with_retry")
        
    def clean_up_references(self):
        """Additional cleanup of any remaining references"""
        print("\n=== Cleaning up remaining references ===")
        
        # Remove any remaining SAFARI_AVAILABLE checks
        self.content = re.sub(r'if SAFARI_AVAILABLE:.*?(?=\n(?:    )?(?:if|elif|else|def|class|\Z))', 
                              '', self.content, flags=re.DOTALL)
        
        # Remove any remaining PLUGIN_SYSTEM_AVAILABLE checks  
        self.content = re.sub(r'if (?:not )?PLUGIN_SYSTEM_AVAILABLE:.*?(?=\n(?:    )?(?:if|elif|else|def|class|\Z))',
                              '', self.content, flags=re.DOTALL)
        
        print("✓ Cleaned up remaining conditional references")
        
    def validate_changes(self):
        """Validate that changes are correct"""
        print("\n=== Validating changes ===")
        
        issues = []
        
        # Check for remaining Safari references
        safari_refs = ["SAFARI_AVAILABLE", "should_fallback_to_safari", 
                      "extract_with_safari_fallback", "requires_safari_preemptively"]
        for ref in safari_refs:
            if ref in self.content and ref != "SAFARI_AVAILABLE = False":
                count = self.content.count(ref)
                issues.append(f"Found {count} instances of '{ref}'")
                
        # Check for remaining plugin references
        plugin_refs = ["PLUGIN_SYSTEM_AVAILABLE", "fetch_html_with_plugins",
                       "get_global_registry", "FetchContext"]
        for ref in plugin_refs:
            if ref in self.content:
                count = self.content.count(ref)
                issues.append(f"Found {count} instances of '{ref}'")
                
        # Check that fetch_html assignment is correct
        if "fetch_html = fetch_html_with_retry" not in self.content:
            issues.append("fetch_html assignment not found or incorrect")
            
        if issues:
            print("✗ Validation issues found:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("✓ All validations passed")
            return True
            
    def save_changes(self):
        """Save the modified content back to file"""
        self.webfetcher_path.write_text(self.content)
        print(f"✓ Changes saved to {self.webfetcher_path}")
        
    def show_diff_summary(self):
        """Show a summary of changes"""
        original_lines = self.original_content.count('\n')
        new_lines = self.content.count('\n')
        removed_lines = original_lines - new_lines
        
        print(f"\n=== Change Summary ===")
        print(f"Original: {original_lines} lines")
        print(f"New: {new_lines} lines")  
        print(f"Removed: {removed_lines} lines")
        print(f"File size: {len(self.original_content)} -> {len(self.content)} bytes")
        
    def execute_phase2(self):
        """Execute the complete Phase 2 removal process"""
        print("=" * 60)
        print("Phase 2: Safari and Plugin System Removal")
        print("=" * 60)
        
        # Create backup
        self.create_backup()
        
        # Load content
        self.load_content()
        
        # Phase 2.1: Remove Safari
        print("\n--- Phase 2.1: Safari Removal ---")
        self.remove_safari_imports()
        self.remove_safari_preemptive_function()
        self.simplify_fetch_html_with_retry()
        
        # Phase 2.2: Remove Plugin System
        print("\n--- Phase 2.2: Plugin System Removal ---")
        self.remove_plugin_imports()
        self.remove_fetch_html_with_plugins()
        self.update_fetch_html_assignment()
        
        # Cleanup
        self.clean_up_references()
        
        # Validate
        if not self.validate_changes():
            print("\n✗ Validation failed! Restoring backup...")
            shutil.copy2(self.backup_path, self.webfetcher_path)
            print(f"✓ Restored from backup: {self.backup_path}")
            return False
            
        # Show summary
        self.show_diff_summary()
        
        # Save changes
        self.save_changes()
        
        print("\n✓ Phase 2 removal completed successfully!")
        print(f"  Backup available at: {self.backup_path}")
        print("\nNext steps:")
        print("1. Run: python3 tests/test_urllib_only.py")
        print("2. Test: wf 'https://example.com' -o /tmp/test")
        print("3. Commit: git add -A && git commit -m 'Phase 2: Remove Safari and plugin system'")
        
        return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 2: Remove Safari and Plugin System")
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without modifying files')
    parser.add_argument('--file', default='webfetcher.py', help='Path to webfetcher.py')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
        print("This would remove:")
        print("  - Safari integration code")
        print("  - Plugin system code")
        print("  - All related imports and functions")
        return 0
        
    remover = Phase2Remover(args.file)
    success = remover.execute_phase2()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())