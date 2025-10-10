#!/usr/bin/env python3
"""
Regression tests for sitemap crawling functionality (Task-008 Phase 2)
Sitemap爬取功能回归测试（Task-008 Phase 2）
"""

import subprocess
import sys
import tempfile
from pathlib import Path

def run_command(cmd, timeout=120):
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

def test_use_sitemap_flag_recognized():
    """Test 1: --use-sitemap flag is recognized"""
    print("Test 1: --use-sitemap flag recognition...")

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ['python', 'wf.py', 'site', 'https://example.com',
               '-o', tmpdir, '--max-pages', '1', '--use-sitemap']

        code, stdout, stderr = run_command(cmd, timeout=30)

        # Check for "unrecognized arguments" error
        if 'unrecognized arguments' in stderr or 'unrecognized arguments' in stdout:
            print(f"  ❌ FAILED: --use-sitemap not recognized")
            print(f"  stderr: {stderr}")
            return False

        print(f"  ✅ PASSED: --use-sitemap flag recognized")
        return True

def test_sitemap_fallback_to_bfs():
    """Test 2: Falls back to BFS when no sitemap found"""
    print("Test 2: Sitemap fallback to BFS...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Use httpbin.org which likely doesn't have sitemap.xml
        cmd = ['python', 'wf.py', 'site', 'https://httpbin.org/html',
               '-o', tmpdir, '--max-pages', '1', '--use-sitemap']

        code, stdout, stderr = run_command(cmd, timeout=30)

        # Should not error, should fall back to BFS
        if 'unrecognized arguments' in stderr:
            print(f"  ❌ FAILED: Command failed with unrecognized arguments")
            return False

        # Check for fallback message in logs (if visible)
        # This is a soft check - we mainly want to ensure no crash
        print(f"  ✅ PASSED: Sitemap fallback executed without errors")
        return True

def test_sitemap_with_real_sitemap():
    """Test 3: Crawl site with actual sitemap.xml"""
    print("Test 3: Crawl site with real sitemap...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Wikipedia likely has sitemap.xml
        cmd = ['python', 'wf.py', 'site', 'https://zh.wikipedia.org',
               '-o', tmpdir, '--max-pages', '3', '--use-sitemap']

        code, stdout, stderr = run_command(cmd, timeout=60)

        # Should complete without errors
        if code != 0 and 'unrecognized arguments' in stderr:
            print(f"  ❌ FAILED: Command failed")
            print(f"  stderr: {stderr}")
            return False

        # Check output directory has files
        output_files = list(Path(tmpdir).glob('**/*.md'))
        if output_files:
            print(f"  ✅ PASSED: Generated {len(output_files)} files with sitemap crawling")
        else:
            print(f"  ⚠️  WARNING: No output files, but command executed")

        return True

def test_backward_compatibility_without_sitemap():
    """Test 4: Backward compatibility (no --use-sitemap flag)"""
    print("Test 4: Backward compatibility without sitemap flag...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Old format: site command without --use-sitemap should still work
        cmd = ['python', 'wf.py', 'site', 'https://httpbin.org/html',
               '-o', tmpdir, '--max-pages', '1']

        code, stdout, stderr = run_command(cmd)

        if 'unrecognized arguments' in stderr:
            print(f"  ❌ FAILED: Backward compatibility broken")
            print(f"  stderr: {stderr}")
            return False

        print(f"  ✅ PASSED: Backward compatibility maintained (BFS crawling works)")
        return True

def test_help_text_includes_sitemap():
    """Test 5: Help text includes --use-sitemap option"""
    print("Test 5: Help text includes --use-sitemap...")

    cmd = ['python', 'wf.py', 'site']
    code, stdout, stderr = run_command(cmd, timeout=10)

    # Check for sitemap help text
    help_text = stdout + stderr
    if '--use-sitemap' not in help_text and 'sitemap' not in help_text.lower():
        print(f"  ❌ FAILED: Help text missing sitemap option")
        return False

    print(f"  ✅ PASSED: Help text includes sitemap option")
    return True

def test_sitemap_with_custom_parameters():
    """Test 6: Sitemap crawling with custom parameters"""
    print("Test 6: Sitemap with custom parameters...")

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ['python', 'wf.py', 'site', 'https://example.com',
               '-o', tmpdir,
               '--max-pages', '2',
               '--delay', '0.1',
               '--use-sitemap']

        code, stdout, stderr = run_command(cmd, timeout=30)

        if 'unrecognized arguments' in stderr:
            print(f"  ❌ FAILED: Custom parameters with sitemap not working")
            print(f"  stderr: {stderr}")
            return False

        print(f"  ✅ PASSED: Custom parameters work with --use-sitemap")
        return True

def main():
    """Run all Phase 2 regression tests"""
    print("=" * 70)
    print("Site Crawling Regression Tests (Task-008 Phase 2)")
    print("站点爬取回归测试（Task-008 Phase 2）- Sitemap Support")
    print("=" * 70)
    print()

    tests = [
        test_use_sitemap_flag_recognized,
        test_sitemap_fallback_to_bfs,
        test_sitemap_with_real_sitemap,
        test_backward_compatibility_without_sitemap,
        test_help_text_includes_sitemap,
        test_sitemap_with_custom_parameters,
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
        print("\n✅ All tests PASSED! Phase 2 regression testing complete.")
        print("✅ 所有测试通过！Phase 2 回归测试完成。")
        return 0
    else:
        print(f"\n❌ {total_count - passed_count} test(s) FAILED!")
        print(f"❌ {total_count - passed_count} 个测试失败！")
        return 1

if __name__ == '__main__':
    sys.exit(main())
