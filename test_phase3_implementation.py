#!/usr/bin/env python3
"""
Task-003 Phase 3: Test Script
Tests the dual URL metadata section implementation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from url_formatter import format_dual_url_section, insert_dual_url_section


def test_format_dual_url_section():
    """Test format_dual_url_section() function"""
    print("=" * 70)
    print("TEST 1: format_dual_url_section() - Basic Test")
    print("=" * 70)

    url_metadata = {
        'input_url': 'example.com',
        'final_url': 'https://www.example.com/page',
        'fetch_date': '2025-10-13 12:00:00',
        'fetch_mode': 'urllib'
    }

    result = format_dual_url_section(url_metadata)
    print(result)

    # Verify expected content
    assert 'Fetch Information / 采集信息' in result
    assert 'Original Request / 原始请求' in result
    assert 'Final Location / 最终地址' in result
    assert 'Fetch Date / 采集时间' in result
    assert 'example.com' in result
    assert 'https://www.example.com/page' in result
    assert '2025-10-13 12:00:00' in result
    print("✅ Test 1 PASSED\n")


def test_format_dual_url_section_no_metadata():
    """Test graceful degradation with no metadata"""
    print("=" * 70)
    print("TEST 2: format_dual_url_section() - No Metadata (Graceful Degradation)")
    print("=" * 70)

    result = format_dual_url_section(None)
    print(f"Result: '{result}'")
    assert result == ""
    print("✅ Test 2 PASSED\n")


def test_format_dual_url_section_identical_urls():
    """Test with identical input and final URLs"""
    print("=" * 70)
    print("TEST 3: format_dual_url_section() - Identical URLs (No Redirect)")
    print("=" * 70)

    url_metadata = {
        'input_url': 'https://news.example.com/article',
        'final_url': 'https://news.example.com/article',
        'fetch_date': '2025-10-13 12:30:00'
    }

    result = format_dual_url_section(url_metadata)
    print(result)

    assert 'https://news.example.com/article' in result
    # Should appear twice (once for input, once for final)
    assert result.count('https://news.example.com/article') >= 2
    print("✅ Test 3 PASSED\n")


def test_insert_dual_url_section_with_title():
    """Test inserting dual URL section after title"""
    print("=" * 70)
    print("TEST 4: insert_dual_url_section() - With Title")
    print("=" * 70)

    sample_md = """# Test Article

- 标题: Test Article
- 作者: Test Author
- 发布时间: 2025-10-13

Content starts here...
"""

    url_metadata = {
        'input_url': 'example.com',
        'final_url': 'https://www.example.com/article',
        'fetch_date': '2025-10-13 12:00:00'
    }

    result = insert_dual_url_section(sample_md, url_metadata)
    print(result)

    # Verify structure
    lines = result.splitlines()
    assert lines[0] == '# Test Article'
    assert 'Fetch Information' in result
    assert 'Original Request' in result

    # Verify dual URL section appears before existing metadata
    fetch_info_idx = result.index('Fetch Information')
    metadata_idx = result.index('- 标题:')
    assert fetch_info_idx < metadata_idx, "Dual URL section should appear before existing metadata"

    print("✅ Test 4 PASSED\n")


def test_insert_dual_url_section_no_title():
    """Test inserting dual URL section when no title exists"""
    print("=" * 70)
    print("TEST 5: insert_dual_url_section() - No Title (Insert at Beginning)")
    print("=" * 70)

    sample_md = """This is a document without a title.

It has some content but no H1 heading.
"""

    url_metadata = {
        'input_url': 'example.com',
        'final_url': 'https://example.com',
        'fetch_date': '2025-10-13 12:00:00'
    }

    result = insert_dual_url_section(sample_md, url_metadata)
    print(result)

    # Verify dual URL section is at the beginning
    assert result.startswith('**Fetch Information')
    print("✅ Test 5 PASSED\n")


def test_insert_dual_url_section_no_metadata():
    """Test graceful degradation when no metadata provided"""
    print("=" * 70)
    print("TEST 6: insert_dual_url_section() - No Metadata (Return Original)")
    print("=" * 70)

    sample_md = """# Test Article

Content here...
"""

    result = insert_dual_url_section(sample_md, None)
    print(f"Result equals original: {result == sample_md}")
    assert result == sample_md
    print("✅ Test 6 PASSED\n")


def test_real_world_example():
    """Test with realistic WeChat article markdown"""
    print("=" * 70)
    print("TEST 7: Real-World Example - WeChat Article")
    print("=" * 70)

    sample_md = """# Chrome DevTools MCP：让AI替你调试网页

- 标题: Chrome DevTools MCP：让AI替你调试网页
- 作者: 诗书塞外
- 发布时间: 2025-10-09 15:22:10
- 来源: [https://mp.weixin.qq.com/s/Z375UG7t270F3j5zvRJgmQ](https://mp.weixin.qq.com/s/Z375UG7t270F3j5zvRJgmQ)
- 抓取时间: 2025-10-09 15:22:10

![](https://mmbiz.qpic.cn/sz_mmbiz_png/...)

Visit the official site for more information.
"""

    url_metadata = {
        'input_url': 'mp.weixin.qq.com/s/Z375UG7t270F3j5zvRJgmQ',
        'final_url': 'https://mp.weixin.qq.com/s/Z375UG7t270F3j5zvRJgmQ',
        'fetch_date': '2025-10-13 14:30:00',
        'fetch_mode': 'urllib'
    }

    result = insert_dual_url_section(sample_md, url_metadata)
    print(result)
    print("\n" + "=" * 70)

    # Verify structure
    assert '# Chrome DevTools MCP' in result
    assert 'Fetch Information / 采集信息' in result
    assert 'Original Request / 原始请求' in result
    assert 'mp.weixin.qq.com/s/Z375UG7t270F3j5zvRJgmQ' in result

    # Verify dual URL section appears after title but before existing metadata
    lines = result.splitlines()
    title_idx = next(i for i, line in enumerate(lines) if line.startswith('# Chrome'))
    fetch_info_idx = next(i for i, line in enumerate(lines) if 'Fetch Information' in line)
    metadata_idx = next(i for i, line in enumerate(lines) if line.startswith('- 标题:'))

    assert title_idx < fetch_info_idx < metadata_idx, "Order should be: Title -> Dual URL Section -> Existing Metadata"

    print("✅ Test 7 PASSED\n")


def main():
    """Run all tests"""
    print("\n")
    print("*" * 70)
    print("Task-003 Phase 3: Dual URL Metadata Section Tests")
    print("*" * 70)
    print("\n")

    tests = [
        test_format_dual_url_section,
        test_format_dual_url_section_no_metadata,
        test_format_dual_url_section_identical_urls,
        test_insert_dual_url_section_with_title,
        test_insert_dual_url_section_no_title,
        test_insert_dual_url_section_no_metadata,
        test_real_world_example
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"❌ {test.__name__} FAILED: {e}\n")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} ERROR: {e}\n")

    print("*" * 70)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("*" * 70)
    print("\n")

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
