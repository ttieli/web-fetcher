#!/usr/bin/env python3
"""
Phase 2.2: Safe Plugin System Removal Script
This script safely removes the plugin system from webfetcher.py
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

def create_backup():
    """Create backup before changes"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("Creating backup...")
    
    # Backup webfetcher.py
    shutil.copy('webfetcher.py', f'webfetcher_before_plugin_removal_{timestamp}.py')
    
    # Backup plugins directory if it exists
    if Path('plugins').exists():
        backup_name = f'plugins_backup_{timestamp}.tar.gz'
        subprocess.run(['tar', '-czf', backup_name, 'plugins/'], check=True)
        print(f"  ✅ Created backups: webfetcher_before_plugin_removal_{timestamp}.py, {backup_name}")
    else:
        print(f"  ✅ Created backup: webfetcher_before_plugin_removal_{timestamp}.py")
    
    return timestamp

def test_current_state():
    """Test current functionality before changes"""
    print("\nTesting current state...")
    
    result = subprocess.run([sys.executable, 'tests/test_urllib_only.py'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("  ✅ Current state tests passed")
        return True
    else:
        print("  ❌ Current state tests failed")
        print(result.stderr)
        return False

def step1_redirect_entry_points():
    """Step 1: Redirect entry points from plugin to direct functions"""
    print("\nStep 1: Redirecting entry points...")
    
    with open('webfetcher.py', 'r') as f:
        lines = f.readlines()
    
    modified = False
    
    # Find and replace the assignments
    for i, line in enumerate(lines):
        if line.strip() == 'fetch_html = fetch_html_with_plugins':
            lines[i] = 'fetch_html = fetch_html_with_retry\n'
            modified = True
            print(f"  Modified line {i+1}: fetch_html assignment")
        elif line.strip() == 'fetch_html_with_metrics = fetch_html_with_plugins':
            lines[i] = 'fetch_html_with_metrics = fetch_html_with_retry\n'
            modified = True
            print(f"  Modified line {i+1}: fetch_html_with_metrics assignment")
    
    if modified:
        with open('webfetcher.py', 'w') as f:
            f.writelines(lines)
        print("  ✅ Entry points redirected")
        return True
    else:
        print("  ⚠️ Entry point assignments not found or already modified")
        return True  # May already be modified

def test_after_redirect():
    """Test functionality after redirecting entry points"""
    print("\nTesting after entry point redirect...")
    
    # Quick test with a simple fetch
    test_script = '''
import sys
sys.path.insert(0, '.')
from webfetcher import fetch_html
try:
    html, metrics = fetch_html("https://www.example.com", timeout=10)
    if html and "Example Domain" in html:
        print("SUCCESS")
        sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
'''
    
    result = subprocess.run([sys.executable, '-c', test_script], 
                          capture_output=True, text=True, timeout=15)
    
    if result.returncode == 0 and "SUCCESS" in result.stdout:
        print("  ✅ Fetch works after redirect")
        return True
    else:
        print("  ❌ Fetch failed after redirect")
        print(result.stderr)
        return False

def step2_remove_plugin_function():
    """Step 2: Remove the fetch_html_with_plugins function"""
    print("\nStep 2: Removing plugin function...")
    
    with open('webfetcher.py', 'r') as f:
        lines = f.readlines()
    
    # Find the function start and end
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if 'def fetch_html_with_plugins' in line:
            start_idx = i
            # Find the end of the function (next def or class at same indentation)
            for j in range(i+1, len(lines)):
                if lines[j].startswith('def ') or lines[j].startswith('class '):
                    end_idx = j
                    break
            break
    
    if start_idx is not None and end_idx is not None:
        # Remove the function
        del lines[start_idx:end_idx]
        
        # Remove extra blank lines if any
        while start_idx < len(lines) and lines[start_idx].strip() == '':
            del lines[start_idx]
        
        with open('webfetcher.py', 'w') as f:
            f.writelines(lines)
        
        print(f"  ✅ Removed fetch_html_with_plugins function (lines {start_idx+1}-{end_idx})")
        return True
    else:
        print("  ⚠️ fetch_html_with_plugins function not found or already removed")
        return True  # May already be removed

def step3_remove_plugin_imports():
    """Step 3: Remove plugin system imports"""
    print("\nStep 3: Removing plugin imports...")
    
    with open('webfetcher.py', 'r') as f:
        lines = f.readlines()
    
    # Find and remove plugin import block
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if 'PLUGIN_SYSTEM_AVAILABLE = False' in line and start_idx is None:
            # Look backwards for comment
            for j in range(i-1, max(0, i-10), -1):
                if '# Plugin system' in lines[j]:
                    start_idx = j
                    break
            if start_idx is None:
                start_idx = i - 1  # Just before the flag
            
            # Find end of the import block
            for j in range(i+1, min(len(lines), i+20)):
                if 'PLUGIN_SYSTEM_AVAILABLE = False' in lines[j] and 'except' in lines[j-1]:
                    end_idx = j + 1
                    break
            break
    
    if start_idx is not None and end_idx is not None:
        # Remove the import block
        del lines[start_idx:end_idx]
        
        # Remove extra blank lines
        while start_idx < len(lines) and lines[start_idx].strip() == '':
            del lines[start_idx]
        
        with open('webfetcher.py', 'w') as f:
            f.writelines(lines)
        
        print(f"  ✅ Removed plugin imports (lines {start_idx+1}-{end_idx})")
        return True
    else:
        print("  ⚠️ Plugin imports not found or already removed")
        return True  # May already be removed

def step4_remove_plugin_directory():
    """Step 4: Remove plugins directory"""
    print("\nStep 4: Removing plugins directory...")
    
    plugins_path = Path('plugins')
    
    if plugins_path.exists():
        shutil.rmtree(plugins_path)
        print("  ✅ Removed plugins/ directory")
        return True
    else:
        print("  ⚠️ plugins/ directory not found or already removed")
        return True

def final_validation():
    """Run final validation tests"""
    print("\nRunning final validation...")
    
    result = subprocess.run([sys.executable, 'tests/test_phase2_2_validation.py'], 
                          capture_output=True, text=True)
    
    print(result.stdout)
    
    if result.returncode == 0:
        print("  ✅ Final validation passed")
        return True
    else:
        print("  ❌ Final validation failed")
        return False

def rollback(timestamp):
    """Rollback changes if needed"""
    print("\n⚠️ Rolling back changes...")
    
    backup_file = f'webfetcher_before_plugin_removal_{timestamp}.py'
    if Path(backup_file).exists():
        shutil.copy(backup_file, 'webfetcher.py')
        print(f"  ✅ Restored webfetcher.py from {backup_file}")
    
    # Restore plugins if backup exists
    backup_tar = f'plugins_backup_{timestamp}.tar.gz'
    if Path(backup_tar).exists():
        subprocess.run(['tar', '-xzf', backup_tar], check=True)
        print(f"  ✅ Restored plugins/ from {backup_tar}")

def main():
    """Main execution"""
    print("=" * 60)
    print("Phase 2.2: Plugin System Removal")
    print("=" * 60)
    
    # Create backup
    timestamp = create_backup()
    
    # Test current state
    if not test_current_state():
        print("\n❌ Current state tests failed. Aborting.")
        return 1
    
    try:
        # Step 1: Redirect entry points
        if not step1_redirect_entry_points():
            raise Exception("Failed to redirect entry points")
        
        if not test_after_redirect():
            raise Exception("Tests failed after redirect")
        
        # Step 2: Remove plugin function
        if not step2_remove_plugin_function():
            raise Exception("Failed to remove plugin function")
        
        # Step 3: Remove plugin imports
        if not step3_remove_plugin_imports():
            raise Exception("Failed to remove plugin imports")
        
        # Step 4: Remove plugin directory
        if not step4_remove_plugin_directory():
            raise Exception("Failed to remove plugin directory")
        
        # Final validation
        if not final_validation():
            raise Exception("Final validation failed")
        
        print("\n" + "=" * 60)
        print("🎉 Phase 2.2 COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\nBackup saved as: webfetcher_before_plugin_removal_{timestamp}.py")
        print("Plugin system has been completely removed.")
        print("The system now uses direct urllib/curl fetching.")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during removal: {e}")
        rollback(timestamp)
        print("\n⚠️ System has been rolled back to previous state")
        return 1

if __name__ == "__main__":
    sys.exit(main())