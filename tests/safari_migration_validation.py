#!/usr/bin/env python3
"""
Safari Module Migration Validation Script
==========================================

Pre-migration validation script to test current Safari functionality
and prepare for safe migration to plugins/safari/ subdirectory.

Author: Architecture Team
Version: 1.0.0
"""

import sys
import os
import json
import importlib
import traceback
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SafariMigrationValidator:
    """Validates Safari module functionality before and after migration."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': [],
            'import_paths': {},
            'dependencies': [],
            'test_results': []
        }
    
    def check_module_import(self, module_name: str, expected_location: str = None) -> dict:
        """Check if a module can be imported and record its location."""
        check_result = {
            'module': module_name,
            'importable': False,
            'location': None,
            'attributes': [],
            'error': None
        }
        
        try:
            module = importlib.import_module(module_name)
            check_result['importable'] = True
            check_result['location'] = getattr(module, '__file__', 'built-in')
            
            # Get public attributes
            check_result['attributes'] = [
                attr for attr in dir(module) 
                if not attr.startswith('_')
            ][:10]  # Limit to first 10 for brevity
            
            if expected_location and check_result['location']:
                check_result['location_correct'] = expected_location in check_result['location']
            
        except ImportError as e:
            check_result['error'] = str(e)
        except Exception as e:
            check_result['error'] = f"Unexpected error: {str(e)}"
        
        return check_result
    
    def check_function_import(self, import_statement: str) -> dict:
        """Check if specific functions can be imported."""
        check_result = {
            'import_statement': import_statement,
            'success': False,
            'functions_available': [],
            'error': None
        }
        
        try:
            # Execute the import statement
            exec_globals = {}
            exec(import_statement, exec_globals)
            
            check_result['success'] = True
            # Get imported names
            check_result['functions_available'] = [
                k for k in exec_globals.keys() 
                if not k.startswith('__')
            ]
            
        except ImportError as e:
            check_result['error'] = str(e)
        except Exception as e:
            check_result['error'] = f"Unexpected error: {str(e)}"
        
        return check_result
    
    def test_safari_functionality(self) -> dict:
        """Test actual Safari functionality with a simple URL."""
        test_result = {
            'test': 'safari_basic_fetch',
            'success': False,
            'error': None,
            'output': None
        }
        
        try:
            from plugins.safari.extractor import extract_with_safari_fallback
            
            # Test with a simple, reliable URL
            test_url = "https://example.com"
            html, metrics = extract_with_safari_fallback(test_url)
            
            if html and len(html) > 100:
                test_result['success'] = True
                test_result['output'] = {
                    'html_length': len(html),
                    'metrics': metrics if metrics else {}
                }
            else:
                test_result['error'] = "No content returned or content too short"
                
        except ImportError as e:
            test_result['error'] = f"Import error: {str(e)}"
        except Exception as e:
            test_result['error'] = f"Runtime error: {str(e)}"
            test_result['traceback'] = traceback.format_exc()
        
        return test_result
    
    def check_file_dependencies(self) -> list:
        """Check which files import Safari modules."""
        dependencies = []
        
        patterns = [
            'from safari_',
            'import safari_',
            'safari_config',
            'safari_extractor',
            'safari_plugin'
        ]
        
        # Check Python files in the project
        project_root = Path(__file__).parent.parent
        for py_file in project_root.rglob('*.py'):
            # Skip test files and templates for cleaner output
            if 'test' in str(py_file) or 'template' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in patterns:
                    if pattern in content:
                        # Find the actual import lines
                        lines = content.split('\n')
                        import_lines = [
                            (i+1, line.strip()) 
                            for i, line in enumerate(lines) 
                            if pattern in line and not line.strip().startswith('#')
                        ]
                        
                        if import_lines:
                            dependencies.append({
                                'file': str(py_file.relative_to(project_root)),
                                'pattern': pattern,
                                'lines': import_lines[:3]  # Limit to first 3 occurrences
                            })
                            break
                            
            except Exception as e:
                dependencies.append({
                    'file': str(py_file.relative_to(project_root)),
                    'error': str(e)
                })
        
        return dependencies
    
    def run_validation(self) -> dict:
        """Run all validation checks."""
        print("Safari Module Migration Validation")
        print("=" * 50)
        
        # Check current module imports
        print("\n1. Checking module imports...")
        modules_to_check = [
            ('safari_config', 'safari_config.py'),
            ('safari_extractor', 'safari_extractor.py'),
            ('plugins.safari_plugin', 'plugins/safari_plugin.py'),
        ]
        
        for module_name, expected_loc in modules_to_check:
            result = self.check_module_import(module_name, expected_loc)
            self.results['checks'].append(result)
            status = "✓" if result['importable'] else "✗"
            print(f"  {status} {module_name}: {result.get('location', result.get('error'))}")
        
        # Check function imports
        print("\n2. Checking function imports...")
        imports_to_check = [
            "from plugins.safari.config import SAFARI_ENABLED, validate_safari_availability",
            "from plugins.safari.extractor import should_fallback_to_safari, extract_with_safari_fallback",
            "from plugins.safari.config import get_extractor_class_name",
        ]
        
        for import_stmt in imports_to_check:
            result = self.check_function_import(import_stmt)
            self.results['import_paths'][import_stmt] = result
            status = "✓" if result['success'] else "✗"
            print(f"  {status} {import_stmt[:60]}...")
        
        # Check file dependencies
        print("\n3. Analyzing file dependencies...")
        self.results['dependencies'] = self.check_file_dependencies()
        
        # Group by file for cleaner output
        files_with_deps = {}
        for dep in self.results['dependencies']:
            if 'error' not in dep:
                file = dep['file']
                if file not in files_with_deps:
                    files_with_deps[file] = []
                files_with_deps[file].append(dep['pattern'])
        
        for file, patterns in list(files_with_deps.items())[:5]:  # Show first 5
            print(f"  • {file}: {', '.join(set(patterns))}")
        
        if len(files_with_deps) > 5:
            print(f"  ... and {len(files_with_deps) - 5} more files")
        
        # Test Safari functionality
        print("\n4. Testing Safari functionality...")
        test_result = self.test_safari_functionality()
        self.results['test_results'].append(test_result)
        
        if test_result['success']:
            print(f"  ✓ Safari basic fetch test passed")
            if test_result.get('output'):
                print(f"    - HTML length: {test_result['output'].get('html_length', 0)} bytes")
        else:
            print(f"  ✗ Safari test failed: {test_result.get('error', 'Unknown error')}")
        
        # Summary
        print("\n" + "=" * 50)
        print("Validation Summary")
        print("-" * 50)
        
        importable_count = sum(1 for c in self.results['checks'] if c['importable'])
        total_checks = len(self.results['checks'])
        
        print(f"Modules importable: {importable_count}/{total_checks}")
        print(f"Files with dependencies: {len(files_with_deps)}")
        print(f"Safari functional: {'Yes' if test_result['success'] else 'No'}")
        
        # Save results
        output_file = Path(__file__).parent / f"safari_migration_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nFull results saved to: {output_file}")
        
        return self.results


if __name__ == "__main__":
    validator = SafariMigrationValidator()
    results = validator.run_validation()
    
    # Exit with error code if validation failed
    all_importable = all(c['importable'] for c in results['checks'])
    safari_works = any(t['success'] for t in results['test_results'])
    
    if not all_importable or not safari_works:
        print("\n⚠️  WARNING: Some validations failed. Review before migration.")
        sys.exit(1)
    else:
        print("\n✅ All validations passed. Safe to proceed with migration.")
        sys.exit(0)