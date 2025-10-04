#!/usr/bin/env python3
"""
Baseline Test Suite - Phase 3.1

Captures baseline output from legacy parsers for comparison during migration.
Creates snapshot files to validate that migrated parsers produce identical results.
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class BaselineTestSuite:
    """Test suite for capturing and validating baseline parser output"""

    def __init__(self):
        self.baseline_dir = Path(__file__).parent / 'baselines'
        self.baseline_dir.mkdir(exist_ok=True)
        self.test_cases = self._prepare_test_cases()

    def _prepare_test_cases(self) -> Dict[str, Tuple[str, str]]:
        """
        Prepare test cases for baseline capture

        Returns:
            Dict mapping test case name to (html, url) tuple
        """
        # WeChat test case
        wechat_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:title" content="微信测试文章">
            <meta property="og:article:author" content="张三">
            <meta property="article:published_time" content="2024-10-04">
        </head>
        <body>
            <div id="js_content">
                <h2>第一节标题</h2>
                <p>这是第一段内容，包含了一些测试文字。</p>
                <p>这是第二段内容，用于测试段落分割。</p>
                <img data-src="https://mmbiz.qpic.cn/mmbiz_jpg/test123.jpg">
                <h3>第二节标题</h3>
                <p>第三段内容，测试图片提取功能。</p>
                <ul>
                    <li>列表项一</li>
                    <li>列表项二</li>
                </ul>
            </div>
        </body>
        </html>
        """
        wechat_url = "https://mp.weixin.qq.com/s/test_article_123"

        # XHS test case
        xhs_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:title" content="小红书旅游攻略 - 小红书">
            <meta property="description" content="这是一篇关于旅游的小红书笔记，包含了详细的攻略和美图分享。">
            <meta property="og:image" content="https://ci.xiaohongshu.com/spectrum/cover123.jpg">
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "author": {
                    "@type": "Person",
                    "name": "旅游达人"
                },
                "datePublished": "2024-10-04T10:30:00Z",
                "headline": "小红书旅游攻略"
            }
            </script>
        </head>
        <body>
            <div class="note-content">
                <p>今天分享一个超美的旅游地点！</p>
                <img src="https://ci.xiaohongshu.com/photo1.jpg?imageView2/2/w/1080">
                <img src="https://ci.xiaohongshu.com/photo2.jpg?imageView2/2/w/1080">
            </div>
        </body>
        </html>
        """
        xhs_url = "https://www.xiaohongshu.com/explore/test_note_456"

        # Generic test case - Article page
        generic_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:title" content="技术博客：Python最佳实践">
            <meta property="description" content="本文介绍了Python开发中的最佳实践和常见陷阱。">
            <meta property="article:published_time" content="2024-10-04T08:00:00Z">
        </head>
        <body>
            <main>
                <article>
                    <h1>Python最佳实践</h1>
                    <p>Python是一门优雅的编程语言，但在实际开发中仍需要注意很多细节。本文将介绍一些重要的最佳实践。这段文字需要足够长以满足内容提取的阈值要求。</p>
                    <h2>1. 代码规范</h2>
                    <p>遵循PEP 8是Python开发的基础。良好的代码规范能够提高代码的可读性和可维护性。我们应该始终保持一致的代码风格，这样团队协作会更加顺畅。</p>
                    <h2>2. 类型提示</h2>
                    <p>使用类型提示可以让代码更加清晰，也便于IDE提供更好的代码补全。虽然Python是动态类型语言，但适当的类型标注能够减少很多潜在的bug。现代Python开发越来越重视类型安全。</p>
                    <h2>3. 异常处理</h2>
                    <p>合理的异常处理是健壮代码的关键。我们应该捕获具体的异常类型，而不是使用宽泛的except语句。同时也要注意异常的传播和日志记录，这对于问题排查非常重要。</p>
                    <h2>4. 性能优化</h2>
                    <p>虽然Python不是最快的语言，但通过合理的优化仍能获得良好的性能。使用生成器、列表推导式、以及选择合适的数据结构都能显著提升性能。在必要时也可以考虑使用Cython或其他加速方案。</p>
                </article>
            </main>
        </body>
        </html>
        """
        generic_url = "https://techblog.example.com/python-best-practices"

        return {
            'wechat': (wechat_html, wechat_url),
            'xhs': (xhs_html, xhs_url),
            'generic': (generic_html, generic_url),
        }

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _save_baseline(self, test_name: str, result: Tuple[str, str, dict]) -> None:
        """
        Save baseline output to file

        Args:
            test_name: Name of the test case
            result: Parser output (date, markdown, metadata)
        """
        date_only, markdown, metadata = result

        baseline = {
            'test_name': test_name,
            'date_only': date_only,
            'markdown': markdown,
            'markdown_hash': self._compute_hash(markdown),
            'metadata': metadata,
            'version': '3.1.0'
        }

        baseline_file = self.baseline_dir / f'{test_name}_baseline.json'
        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(baseline, f, ensure_ascii=False, indent=2)

        print(f"Saved baseline: {baseline_file}")
        print(f"  Content hash: {baseline['markdown_hash'][:16]}...")

    def test_wechat_baseline(self) -> bool:
        """Capture WeChat parser baseline"""
        print("\n" + "=" * 60)
        print("WeChat Parser Baseline Test")
        print("=" * 60)

        html, url = self.test_cases['wechat']

        try:
            from parsers_legacy import wechat_to_markdown
            result = wechat_to_markdown(html, url)

            # Validate result structure
            assert isinstance(result, tuple), "Result must be a tuple"
            assert len(result) == 3, "Result must have 3 elements"
            date_only, markdown, metadata = result
            assert isinstance(date_only, str), "date_only must be string"
            assert isinstance(markdown, str), "markdown must be string"
            assert isinstance(metadata, dict), "metadata must be dict"

            # Save baseline
            self._save_baseline('wechat', result)

            print("SUCCESS: WeChat baseline captured")
            print(f"  Markdown length: {len(markdown)} bytes")
            print(f"  Images found: {len(metadata.get('images', []))}")
            return True

        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_xhs_baseline(self) -> bool:
        """Capture XHS parser baseline"""
        print("\n" + "=" * 60)
        print("XiaoHongShu Parser Baseline Test")
        print("=" * 60)

        html, url = self.test_cases['xhs']

        try:
            from parsers_legacy import xhs_to_markdown
            result = xhs_to_markdown(html, url)

            # Validate result structure
            assert isinstance(result, tuple), "Result must be a tuple"
            assert len(result) == 3, "Result must have 3 elements"
            date_only, markdown, metadata = result
            assert isinstance(date_only, str), "date_only must be string"
            assert isinstance(markdown, str), "markdown must be string"
            assert isinstance(metadata, dict), "metadata must be dict"

            # Save baseline
            self._save_baseline('xhs', result)

            print("SUCCESS: XHS baseline captured")
            print(f"  Markdown length: {len(markdown)} bytes")
            print(f"  Images found: {len(metadata.get('images', []))}")
            print(f"  Author: {metadata.get('author', 'N/A')}")
            return True

        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False

    def test_generic_baseline(self) -> bool:
        """Capture Generic parser baseline"""
        print("\n" + "=" * 60)
        print("Generic Parser Baseline Test")
        print("=" * 60)

        html, url = self.test_cases['generic']

        try:
            from parsers_legacy import generic_to_markdown
            result = generic_to_markdown(html, url)

            # Validate result structure
            assert isinstance(result, tuple), "Result must be a tuple"
            assert len(result) == 3, "Result must have 3 elements"
            date_only, markdown, metadata = result
            assert isinstance(date_only, str), "date_only must be string"
            assert isinstance(markdown, str), "markdown must be string"
            assert isinstance(metadata, dict), "metadata must be dict"

            # Save baseline
            self._save_baseline('generic', result)

            print("SUCCESS: Generic baseline captured")
            print(f"  Markdown length: {len(markdown)} bytes")
            print(f"  Page type: {metadata.get('page_type', 'N/A')}")
            return True

        except Exception as e:
            print(f"FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False

    def verify_against_baseline(self, test_name: str, result: Tuple[str, str, dict]) -> bool:
        """
        Verify parser output against saved baseline

        Args:
            test_name: Name of test case
            result: Parser output to verify

        Returns:
            True if matches baseline, False otherwise
        """
        baseline_file = self.baseline_dir / f'{test_name}_baseline.json'

        if not baseline_file.exists():
            print(f"WARNING: No baseline file found for {test_name}")
            return False

        with open(baseline_file, 'r', encoding='utf-8') as f:
            baseline = json.load(f)

        date_only, markdown, metadata = result
        current_hash = self._compute_hash(markdown)

        if current_hash == baseline['markdown_hash']:
            print(f"MATCH: {test_name} output matches baseline")
            return True
        else:
            print(f"MISMATCH: {test_name} output differs from baseline")
            print(f"  Baseline hash: {baseline['markdown_hash'][:16]}...")
            print(f"  Current hash:  {current_hash[:16]}...")
            return False

    def run_all(self) -> bool:
        """Run all baseline tests"""
        print("=" * 60)
        print("Baseline Test Suite - Phase 3.1")
        print("=" * 60)

        results = []
        results.append(self.test_wechat_baseline())
        results.append(self.test_xhs_baseline())
        results.append(self.test_generic_baseline())

        print("\n" + "=" * 60)
        print("Baseline Test Summary")
        print("=" * 60)
        print(f"Total tests: {len(results)}")
        print(f"Passed: {sum(results)}")
        print(f"Failed: {len(results) - sum(results)}")

        return all(results)


def main():
    """Main entry point"""
    suite = BaselineTestSuite()
    success = suite.run_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
