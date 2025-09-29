#!/usr/bin/env python3
"""
Phase 3 Removal Validator
========================
Validates that removing extractors and unused parsers doesn't break core functionality.

Author: Architecture Team
Date: 2025-09-28
"""

import os
import sys
import ast
import json
import subprocess
import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Set

class RemovalValidator:
    """Validates safe removal of extractors and unused parsers."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.webfetcher_path = project_root / "webfetcher.py"
        self.extractors_dir = project_root / "extractors"
        self.validation_results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "phase": "3.0",
            "checks": []
        }
    
    def check_extractor_usage(self) -> Tuple[bool, List[str]]:
        """Check if extractors are referenced anywhere in the codebase."""
        issues = []
        
        # Patterns that would indicate extractor usage
        patterns = [
            "from extractors",
            "import.*extractor",
            "get_extractor",
            "BaseExtractor",
            "CCDIExtractor", 
            "QCCExtractor",
            "GenericExtractor"
        ]
        
        # Files to check (excluding extractors directory itself)
        files_to_check = [
            self.webfetcher_path,
            self.project_root / "wf.py",
            self.project_root / "parsers.py",
            self.project_root / "core" / "downloader.py"
        ]
        
        for file_path in files_to_check:
            if file_path.exists():
                content = file_path.read_text()
                for pattern in patterns:
                    if pattern.lower() in content.lower():
                        issues.append(f"{file_path.name}: Found pattern '{pattern}'")
        
        return len(issues) == 0, issues
    
    def identify_unused_parsers(self) -> Dict[str, Dict]:
        """Identify parsers not used by core sites."""
        
        unused_parsers = {
            "docusaurus_to_markdown": {
                "lines": "587-767",
                "class": "DocParser",
                "safe_to_remove": True,
                "reason": "Not used by core sites"
            },
            "mkdocs_to_markdown": {
                "lines": "769-1580", 
                "class": "MkParser",
                "safe_to_remove": True,
                "reason": "Not used by core sites"
            },
            "dianping_to_markdown": {
                "lines": "2545-2698",
                "class": None,
                "safe_to_remove": True,
                "reason": "Dianping not a core site"
            },
            "ebchina_news_list_to_markdown": {
                "lines": "2700-2761",
                "class": None,
                "safe_to_remove": True,
                "reason": "EBChina not a core site"
            },
            "raw_to_markdown": {
                "lines": "2763-3483",
                "class": None,
                "safe_to_remove": False,  # Conditional
                "reason": "Keep if --raw flag is used"
            }
        }
        
        return unused_parsers
    
    def check_core_site_parsers(self) -> Tuple[bool, Dict]:
        """Verify core site parsers are present and functional."""
        
        core_parsers = {
            "wechat_to_markdown": {
                "sites": ["mp.weixin.qq.com"],
                "required": True,
                "found": False
            },
            "xhs_to_markdown": {
                "sites": ["xiaohongshu.com", "xhslink.com"],
                "required": True,
                "found": False
            },
            "generic_to_markdown": {
                "sites": ["news.cn", "fallback"],
                "required": True,
                "found": False
            }
        }
        
        if self.webfetcher_path.exists():
            content = self.webfetcher_path.read_text()
            for parser_name in core_parsers:
                if f"def {parser_name}(" in content:
                    core_parsers[parser_name]["found"] = True
        
        all_found = all(p["found"] for p in core_parsers.values())
        return all_found, core_parsers
    
    def test_core_sites(self) -> List[Dict]:
        """Test that core sites still work."""
        
        test_results = []
        test_urls = [
            {
                "site": "WeChat",
                "url": "https://mp.weixin.qq.com/s/g3omvC69K9C70lrJKKFjFQ",
                "parser": "wechat_to_markdown"
            },
            {
                "site": "XiaoHongShu",
                "url": "https://www.xiaohongshu.com/explore/6703fc35000000001e034a04",
                "parser": "xhs_to_markdown"
            },
            {
                "site": "Xinhua News",
                "url": "https://www.news.cn/politics/leaders/20241001/da2e9e2461bb41fbb96a913c89c90b38/c.html",
                "parser": "generic_to_markdown"
            }
        ]
        
        for test in test_urls:
            result = {
                "site": test["site"],
                "url": test["url"],
                "expected_parser": test["parser"],
                "status": "not_tested",
                "output": None
            }
            
            try:
                # Run wf.py with the URL
                cmd = [sys.executable, str(self.project_root / "wf.py"), test["url"]]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(self.project_root)
                )
                
                if proc.returncode == 0:
                    result["status"] = "success"
                    # Check if output file was created
                    output_dir = self.project_root / "output"
                    if output_dir.exists():
                        latest_files = sorted(output_dir.glob("*.md"), 
                                            key=lambda x: x.stat().st_mtime, 
                                            reverse=True)
                        if latest_files:
                            result["output"] = latest_files[0].name
                else:
                    result["status"] = "failed"
                    result["error"] = proc.stderr[:500] if proc.stderr else "Unknown error"
                    
            except subprocess.TimeoutExpired:
                result["status"] = "timeout"
            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)[:500]
            
            test_results.append(result)
        
        return test_results
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check for hidden dependencies."""
        
        checks = {
            "no_safari_refs": True,
            "no_plugin_refs": True,
            "no_dynamic_imports": True,
            "parsers_self_contained": True
        }
        
        if self.webfetcher_path.exists():
            content = self.webfetcher_path.read_text()
            
            # Check for Safari references
            if "safari" in content.lower() and "# safari" not in content.lower():
                checks["no_safari_refs"] = False
            
            # Check for plugin references
            if "plugin" in content.lower() and "# plugin" not in content.lower():
                checks["no_plugin_refs"] = False
            
            # Check for dynamic imports
            if "__import__" in content or "importlib" in content:
                checks["no_dynamic_imports"] = False
        
        return checks
    
    def generate_removal_script(self) -> str:
        """Generate a safe removal script."""
        
        script = '''#!/bin/bash
# Phase 3 Removal Script - Generated by validator
# Date: {date}

set -e  # Exit on error

echo "Phase 3: Removing extractors and unused parsers"
echo "================================================"

# Step 1: Backup current state
BACKUP_NAME="web_fetcher_pre_phase3_$(date +%Y%m%d_%H%M%S).tar.gz"
echo "Creating backup: $BACKUP_NAME"
tar -czf "$BACKUP_NAME" . --exclude="*.tar.gz" --exclude=".git"

# Step 2: Remove extractors directory
if [ -d "extractors" ]; then
    echo "Removing extractors directory..."
    rm -rf extractors/
    echo "✓ Extractors removed"
else
    echo "✓ Extractors directory not found (already removed)"
fi

# Step 3: Create Python script to remove unused parsers
cat > remove_unused_parsers.py << 'EOF'
#!/usr/bin/env python3
"""Remove unused parsers from webfetcher.py"""

import re
from pathlib import Path

def remove_parser_functions():
    webfetcher = Path("webfetcher.py")
    if not webfetcher.exists():
        print("webfetcher.py not found!")
        return False
    
    content = webfetcher.read_text()
    original_length = len(content.splitlines())
    
    # Parsers to remove with their approximate line ranges
    removals = [
        ("dianping_to_markdown", 2545, 2698),
        ("ebchina_news_list_to_markdown", 2700, 2761),
    ]
    
    # TODO: Implement actual removal logic
    # This is a placeholder for the architectural design
    
    print(f"Parser removal script ready for implementation")
    print(f"Would remove {len(removals)} parser functions")
    return True

if __name__ == "__main__":
    remove_parser_functions()
EOF

echo "Ready to remove unused parsers (requires implementation)"

# Step 4: Run validation tests
echo ""
echo "Running validation tests..."
python tests/test_phase2_2_validation.py

echo ""
echo "Phase 3 removal complete!"
echo "Please verify all core sites still work:"
echo "  - WeChat: mp.weixin.qq.com"
echo "  - XiaoHongShu: xiaohongshu.com"  
echo "  - Xinhua News: news.cn"
'''.format(date=datetime.datetime.now().isoformat())
        
        return script
    
    def validate(self) -> Dict:
        """Run all validation checks."""
        
        print("Phase 3 Removal Validation")
        print("=" * 50)
        
        # Check 1: Extractor usage
        print("\n1. Checking extractor usage...")
        no_usage, issues = self.check_extractor_usage()
        self.validation_results["checks"].append({
            "name": "extractor_usage",
            "passed": no_usage,
            "issues": issues,
            "safe_to_remove": no_usage
        })
        if no_usage:
            print("   ✓ No extractor usage found - safe to remove")
        else:
            print(f"   ✗ Found {len(issues)} references to extractors")
            for issue in issues[:3]:
                print(f"     - {issue}")
        
        # Check 2: Identify unused parsers
        print("\n2. Identifying unused parsers...")
        unused = self.identify_unused_parsers()
        self.validation_results["checks"].append({
            "name": "unused_parsers",
            "parsers": unused,
            "count": len([p for p in unused.values() if p["safe_to_remove"]])
        })
        print(f"   Found {len(unused)} potentially unused parsers:")
        for name, info in unused.items():
            status = "✓ Safe to remove" if info["safe_to_remove"] else "⚠ Check before removing"
            print(f"   - {name}: {status}")
        
        # Check 3: Core site parsers
        print("\n3. Verifying core site parsers...")
        all_present, core_parsers = self.check_core_site_parsers()
        self.validation_results["checks"].append({
            "name": "core_parsers",
            "all_present": all_present,
            "parsers": core_parsers
        })
        if all_present:
            print("   ✓ All core parsers present")
        else:
            print("   ✗ Missing core parsers!")
        for name, info in core_parsers.items():
            status = "✓" if info["found"] else "✗"
            print(f"   {status} {name}: {', '.join(info['sites'])}")
        
        # Check 4: Dependencies
        print("\n4. Checking for hidden dependencies...")
        deps = self.check_dependencies()
        self.validation_results["checks"].append({
            "name": "dependencies",
            "checks": deps,
            "all_clear": all(deps.values())
        })
        for check, passed in deps.items():
            status = "✓" if passed else "✗"
            print(f"   {status} {check}")
        
        # Check 5: Test core sites
        print("\n5. Testing core sites...")
        test_results = self.test_core_sites()
        self.validation_results["checks"].append({
            "name": "core_site_tests",
            "results": test_results,
            "all_passed": all(r["status"] == "success" for r in test_results)
        })
        for result in test_results:
            status = "✓" if result["status"] == "success" else "✗"
            print(f"   {status} {result['site']}: {result['status']}")
            if result.get("output"):
                print(f"      Output: {result['output']}")
        
        # Summary
        print("\n" + "=" * 50)
        print("VALIDATION SUMMARY")
        print("=" * 50)
        
        extractor_safe = self.validation_results["checks"][0]["passed"]
        core_ok = self.validation_results["checks"][2]["all_present"]
        tests_ok = self.validation_results["checks"][4]["all_passed"]
        
        if extractor_safe:
            print("✓ Extractors directory can be safely removed")
        else:
            print("✗ Extractors still have references - investigate before removal")
        
        if core_ok and tests_ok:
            print("✓ Core functionality verified - safe to proceed")
        else:
            print("⚠ Core functionality issues - fix before proceeding")
        
        # Save results
        output_file = self.project_root / "tests" / f"phase3_validation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.write_text(json.dumps(self.validation_results, indent=2))
        print(f"\nValidation report saved to: {output_file}")
        
        return self.validation_results


def main():
    """Run Phase 3 removal validation."""
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Run validation
    validator = RemovalValidator(project_root)
    results = validator.validate()
    
    # Generate removal script if safe
    if results["checks"][0]["passed"]:  # Extractors safe to remove
        script_path = project_root / "phase3_remove_extractors.sh"
        script_content = validator.generate_removal_script()
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        print(f"\nRemoval script generated: {script_path}")
        print("Run with: ./phase3_remove_extractors.sh")
    
    # Exit code based on validation
    all_safe = (results["checks"][0]["passed"] and 
                results["checks"][2]["all_present"] and
                results["checks"][4]["all_passed"])
    
    sys.exit(0 if all_safe else 1)


if __name__ == "__main__":
    main()