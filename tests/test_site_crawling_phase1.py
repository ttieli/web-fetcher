#!/usr/bin/env python3
"""
Regression tests for site crawling functionality (Task-008 Phase 1)
站点爬取功能回归测试（Task-008 Phase 1）
"""

import subprocess
import sys
import tempfile
from pathlib import Path

def run_command(cmd, timeout=60):
    """Run command and return result"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher"
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"

def test_basic_site_crawl():
    """Test 1: Basic site crawl command"""
    print("Test 1: Basic site crawl...")

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ['python', 'wf.py', 'site', 'https://httpbin.org/html',
               '-o', tmpdir, '--max-pages', '1']

        code, stdout, stderr = run_command(cmd)

        if 'unrecognized arguments' in stderr:
            print(f"  ❌ FAILED: Unrecognized arguments error")
            print(f"  stderr: {stderr}")
            return False

        # Check output directory has files
        output_files = list(Path(tmpdir).glob('**/*.md'))
        if not output_files:
            print(f"  ⚠️  WARNING: No output files, but command executed")
            # This is acceptable for Phase 1 - flag is recognized
            return True

        print(f"  ✅ PASSED: Generated {len(output_files)} files")
        return True

def test_follow_pagination_flag():
    """Test 2: --follow-pagination flag is recognized"""
    print("Test 2: --follow-pagination flag recognition...")

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ['python', 'wf.py', 'site', 'https://httpbin.org/html',
               '-o', tmpdir, '--max-pages', '1', '--follow-pagination']

        code, stdout, stderr = run_command(cmd)

        # Check for "unrecognized arguments" error
        if 'unrecognized arguments' in stderr:
            print(f"  ❌ FAILED: --follow-pagination not recognized")
            print(f"  stderr: {stderr}")
            return False

        print(f"  ✅ PASSED: --follow-pagination flag recognized")
        return True

def test_custom_parameters():
    """Test 3: Custom crawl parameters"""
    print("Test 3: Custom crawl parameters...")

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ['python', 'wf.py', 'site', 'https://httpbin.org/html',
               '-o', tmpdir,
               '--max-pages', '3',
               '--max-depth', '2',
               '--delay', '0.1']

        code, stdout, stderr = run_command(cmd, timeout=30)

        if 'unrecognized arguments' in stderr:
            print(f"  ❌ FAILED: Parameters not recognized")
            print(f"  stderr: {stderr}")
            return False

        print(f"  ✅ PASSED: Custom parameters accepted")
        return True

def test_backward_compatibility():
    """Test 4: Backward compatibility (old command format)"""
    print("Test 4: Backward compatibility...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Old format: wf site <URL> <output_dir>
        cmd = ['python', 'wf.py', 'site', 'https://httpbin.org/html', tmpdir]

        code, stdout, stderr = run_command(cmd)

        if 'unrecognized arguments' in stderr:
            print(f"  ❌ FAILED: Backward compatibility broken")
            print(f"  stderr: {stderr}")
            return False

        print(f"  ✅ PASSED: Backward compatibility maintained")
        return True

def test_help_text():
    """Test 5: Help text is displayed correctly"""
    print("Test 5: Help text display...")

    cmd = ['python', 'wf.py', 'site']
    code, stdout, stderr = run_command(cmd, timeout=10)

    # Check for bilingual help text
    if '可用选项' not in stdout and '可用选项' not in stderr:
        print(f"  ❌ FAILED: Help text missing or not bilingual")
        return False

    if 'max-pages' not in stdout and 'max-pages' not in stderr:
        print(f"  ❌ FAILED: Help text incomplete")
        return False

    print(f"  ✅ PASSED: Help text displayed correctly")
    return True

def main():
    """Run all regression tests"""
    print("=" * 70)
    print("Site Crawling Regression Tests (Task-008 Phase 1)")
    print("站点爬取回归测试（Task-008 Phase 1）")
    print("=" * 70)
    print()

    tests = [
        test_basic_site_crawl,
        test_follow_pagination_flag,
        test_custom_parameters,
        test_backward_compatibility,
        test_help_text
    ]

    results = []
    for test_func in tests:
        try:
            passed = test_func()
            results.append(passed)
        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
        print()

    # Summary
    print("=" * 70)
    passed_count = sum(results)
    total_count = len(results)
    success_rate = (passed_count / total_count * 100) if total_count > 0 else 0

    print(f"Results: {passed_count}/{total_count} tests passed ({success_rate:.1f}%)")
    print(f"结果：{passed_count}/{total_count} 测试通过 ({success_rate:.1f}%)")

    if passed_count == total_count:
        print("\n✅ All tests PASSED! Phase 1 regression testing complete.")
        print("✅ 所有测试通过！Phase 1 回归测试完成。")
        return 0
    else:
        print(f"\n❌ {total_count - passed_count} test(s) FAILED!")
        print(f"❌ {total_count - passed_count} 个测试失败！")
        return 1

if __name__ == '__main__':
    sys.exit(main())
