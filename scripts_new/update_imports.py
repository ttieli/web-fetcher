#!/usr/bin/env python3
"""
Update import statements to use new module structure.
"""
import re
import sys
from pathlib import Path

# Import mappings: old -> new
IMPORT_MAPPINGS = {
    # Error handling
    'from error_handler import': 'from webfetcher.errors.handler import',
    'from error_classifier import': 'from webfetcher.errors.classifier import',
    'from error_types import': 'from webfetcher.errors.types import',
    'from error_cache import': 'from webfetcher.errors.cache import',

    # Parsing
    'from parsers import': 'from webfetcher.parsing.parser import',
    'from parsers_migrated import': 'from webfetcher.parsing.templates import',
    'from parsers_legacy import': 'from webfetcher.parsing.legacy import',
    'import parsers': 'import webfetcher.parsing.parser as parsers',

    # Fetchers
    'from selenium_fetcher import': 'from webfetcher.fetchers.selenium import',
    'from selenium_config import': 'from webfetcher.fetchers.config import',

    # Utils
    'from url_formatter import': 'from webfetcher.utils.url_formatter import',

    # These will be handled by relative imports within webfetcher/
    # 'from routing import': 'from webfetcher.routing import',
    # 'from manual_chrome import': 'from webfetcher.manual import',
    # 'from drivers import': 'from webfetcher.drivers import',
}

def update_imports_in_file(file_path):
    """Update imports in a single file."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        modified = False

        for old_import, new_import in IMPORT_MAPPINGS.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                modified = True
                print(f"  ✓ {file_path.name}: {old_import} -> {new_import}")

        if modified:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False

    except Exception as e:
        print(f"  ✗ Error updating {file_path}: {e}")
        return False

def main():
    root = Path(__file__).parent.parent

    print("Phase 5.1: Updating imports in webfetcher/ modules...")

    # Update files in webfetcher/
    updated_files = []
    for py_file in root.glob('webfetcher/**/*.py'):
        if '__pycache__' not in str(py_file):
            if update_imports_in_file(py_file):
                updated_files.append(py_file)

    print(f"\n✓ Updated {len(updated_files)} files in webfetcher/")

    # Update wf.py and webfetcher.py
    print("\nPhase 5.2: Updating main files...")
    for main_file in [root / 'wf.py', root / 'webfetcher.py']:
        if main_file.exists():
            if update_imports_in_file(main_file):
                print(f"  ✓ Updated {main_file.name}")

    print("\n✓ Phase 5: Import path updates completed")

if __name__ == '__main__':
    main()
