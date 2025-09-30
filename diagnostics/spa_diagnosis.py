#!/usr/bin/env python3
"""
SPA页面诊断工具

用于诊断为什么SPA页面（如React.dev）的内容提取失败。
分析可能的根本原因：等待时间、DOM选择器、JS完成状态等。

Author: Cody (Full-Stack Engineer)
Date: 2025-09-30
"""

import sys
import os
import time
import logging
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from selenium_fetcher import SeleniumFetcher
from selenium_config import SeleniumConfig
from parsers import extract_from_modern_selectors

# Initialize config
_config_obj = SeleniumConfig()
SELENIUM_CONFIG = {
    'chrome': {
        'debug_port': _config_obj.get_debug_port(),
        'debug_host': _config_obj.get_debug_host()
    },
    'connection': _config_obj.get_connection_config(),
    'timeouts': _config_obj.get_timeouts(),
    'wait_conditions': _config_obj.get_wait_conditions(),
    'chrome_options': _config_obj.get_chrome_options(),
    'retry': _config_obj.get_retry_config(),
    'js_detection': _config_obj.get_js_detection_config()
}

# BeautifulSoup for DOM analysis
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    print("Warning: BeautifulSoup not available, DOM analysis will be limited")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DOMContainerInfo:
    """Information about a DOM container"""
    selector: str
    tag_name: str
    text_length: int
    child_count: int
    preview: str  # First 200 chars of text


@dataclass
class WaitStrategyResult:
    """Result from testing a wait strategy"""
    wait_time: int
    html_length: int
    content_extracted: bool
    content_length: int
    error: Optional[str] = None


@dataclass
class SelectorTestResult:
    """Result from testing a selector"""
    selector: str
    matched: bool
    element_count: int
    text_length: int
    preview: str


class SPADiagnostics:
    """SPA页面诊断工具"""

    # Generic Parser的内容选择器（从parsers.py中提取）
    CONTENT_SELECTORS = [
        ('span#detailContent', 'span[id="detailContent"]'),
        ('div#detailContent', 'div[id="detailContent"]'),
        ('div.hero-content', 'div[class*="hero-content"]'),
        ('div.post-content', 'div[class*="post-content"]'),
        ('div.article-content', 'div[class*="article-content"]'),
        ('div.entry-content', 'div[class*="entry-content"]'),
        ('div.main-content', 'div[class*="main-content"]'),
        ('div.content', 'div[class*="content"]'),
        ('main', 'main'),
        ('article', 'article'),
        ('section.content', 'section[class*="content"]'),
        ('div.intro', 'div[class*="intro"]'),
        ('div.description', 'div[class*="description"]'),
        ('div.lead', 'div[class*="lead"]'),
    ]

    def __init__(self, output_dir: str = None):
        """
        Initialize diagnostics tool

        Args:
            output_dir: Directory for output files (defaults to diagnostics/test_results)
        """
        if output_dir is None:
            script_dir = Path(__file__).parent
            output_dir = script_dir / "test_results"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"SPADiagnostics initialized - output dir: {self.output_dir}")

    def save_raw_html(self, url: str, output_file: str) -> Tuple[str, int, str]:
        """
        使用SeleniumFetcher获取并保存原始HTML

        Args:
            url: Target URL
            output_file: Output filename (relative to output_dir)

        Returns:
            Tuple of (html_content, html_length, output_path)
        """
        logger.info(f"Fetching HTML from: {url}")

        # Initialize Selenium fetcher
        fetcher = SeleniumFetcher(SELENIUM_CONFIG)

        try:
            # Connect to Chrome
            success, message = fetcher.connect_to_chrome()
            if not success:
                logger.error(f"Failed to connect to Chrome: {message}")
                raise Exception(f"Chrome connection failed: {message}")

            logger.info("Connected to Chrome successfully")

            # Fetch the page
            html, metrics = fetcher.fetch_html_selenium(url)

            logger.info(f"Fetched HTML: {len(html)} bytes in {metrics.selenium_wait_time:.2f}s")

            # Save to file
            output_path = self.output_dir / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

            logger.info(f"Saved HTML to: {output_path}")

            return html, len(html), str(output_path)

        finally:
            # Cleanup
            fetcher.cleanup()

    def analyze_dom_structure(self, html: str) -> Dict[str, DOMContainerInfo]:
        """
        分析DOM结构，识别主要内容容器

        Args:
            html: HTML content

        Returns:
            Dictionary mapping selector to container info
        """
        logger.info("Analyzing DOM structure")

        if not BEAUTIFULSOUP_AVAILABLE:
            logger.warning("BeautifulSoup not available, skipping DOM analysis")
            return {}

        soup = BeautifulSoup(html, 'html.parser')
        results = {}

        # Define selectors to analyze
        selectors = [
            ('main', 'main'),
            ('article', 'article'),
            ('[role="main"]', lambda tag: tag.has_attr('role') and tag['role'] == 'main'),
            ('#root', lambda tag: tag.has_attr('id') and tag['id'] == 'root'),
            ('#app', lambda tag: tag.has_attr('id') and tag['id'] == 'app'),
            ('[id*="content"]', lambda tag: tag.has_attr('id') and 'content' in tag['id'].lower()),
            ('[class*="content"]', lambda tag: tag.has_attr('class') and any('content' in c.lower() for c in tag['class'])),
            ('body', 'body'),
        ]

        for selector_name, selector_func in selectors:
            try:
                if isinstance(selector_func, str):
                    elements = soup.select(selector_func)
                else:
                    elements = soup.find_all(selector_func)

                if elements:
                    # Take the first matching element
                    element = elements[0]
                    text = element.get_text(strip=True)
                    children = len(list(element.children))

                    info = DOMContainerInfo(
                        selector=selector_name,
                        tag_name=element.name,
                        text_length=len(text),
                        child_count=children,
                        preview=text[:200] if text else "(empty)"
                    )

                    results[selector_name] = info
                    logger.debug(f"Found {selector_name}: {len(text)} chars, {children} children")

            except Exception as e:
                logger.warning(f"Error analyzing selector {selector_name}: {e}")

        logger.info(f"DOM analysis complete - found {len(results)} containers")
        return results

    def test_wait_strategies(self, url: str) -> List[WaitStrategyResult]:
        """
        测试不同等待策略的效果

        Args:
            url: Target URL

        Returns:
            List of wait strategy results
        """
        logger.info(f"Testing wait strategies for: {url}")

        results = []
        wait_times = [1, 3, 5, 10]

        for wait_time in wait_times:
            logger.info(f"Testing wait time: {wait_time}s")

            # Create custom config with specific wait time
            custom_config = SELENIUM_CONFIG.copy()
            custom_config['timeouts'] = custom_config.get('timeouts', {}).copy()
            custom_config['timeouts']['implicit_wait'] = wait_time

            fetcher = SeleniumFetcher(custom_config)

            try:
                # Connect to Chrome
                success, message = fetcher.connect_to_chrome()
                if not success:
                    logger.error(f"Failed to connect for wait test: {message}")
                    results.append(WaitStrategyResult(
                        wait_time=wait_time,
                        html_length=0,
                        content_extracted=False,
                        content_length=0,
                        error=message
                    ))
                    continue

                # Fetch with this wait time
                html, metrics = fetcher.fetch_html_selenium(url)

                # Try to extract content
                content = extract_from_modern_selectors(html)
                content_length = len(content.strip()) if content else 0

                results.append(WaitStrategyResult(
                    wait_time=wait_time,
                    html_length=len(html),
                    content_extracted=content_length > 200,
                    content_length=content_length,
                    error=None
                ))

                logger.info(f"Wait {wait_time}s: HTML={len(html)}, Content={content_length}, Success={content_length > 200}")

            except Exception as e:
                logger.error(f"Error testing wait time {wait_time}s: {e}")
                results.append(WaitStrategyResult(
                    wait_time=wait_time,
                    html_length=0,
                    content_extracted=False,
                    content_length=0,
                    error=str(e)
                ))

            finally:
                fetcher.cleanup()
                # Brief pause between tests
                time.sleep(2)

        logger.info(f"Wait strategy testing complete - {len(results)} results")
        return results

    def test_parser_selectors(self, html: str) -> List[SelectorTestResult]:
        """
        测试Generic Parser的选择器匹配情况

        Args:
            html: HTML content

        Returns:
            List of selector test results
        """
        logger.info("Testing parser selectors")

        if not BEAUTIFULSOUP_AVAILABLE:
            logger.warning("BeautifulSoup not available, skipping selector tests")
            return []

        soup = BeautifulSoup(html, 'html.parser')
        results = []

        for selector_name, css_selector in self.CONTENT_SELECTORS:
            try:
                # Use CSS selector
                elements = soup.select(css_selector)

                if elements:
                    # Get first matching element
                    element = elements[0]
                    text = element.get_text(strip=True)

                    result = SelectorTestResult(
                        selector=selector_name,
                        matched=True,
                        element_count=len(elements),
                        text_length=len(text),
                        preview=text[:200] if text else "(empty)"
                    )
                else:
                    result = SelectorTestResult(
                        selector=selector_name,
                        matched=False,
                        element_count=0,
                        text_length=0,
                        preview="(no match)"
                    )

                results.append(result)
                logger.debug(f"Selector {selector_name}: matched={result.matched}, length={result.text_length}")

            except Exception as e:
                logger.warning(f"Error testing selector {selector_name}: {e}")
                results.append(SelectorTestResult(
                    selector=selector_name,
                    matched=False,
                    element_count=0,
                    text_length=0,
                    preview=f"(error: {e})"
                ))

        logger.info(f"Selector testing complete - {len(results)} selectors tested")
        return results

    def generate_report(self, url: str, results: Dict) -> str:
        """
        生成Markdown格式的诊断报告

        Args:
            url: Target URL
            results: Dictionary containing all test results

        Returns:
            Markdown formatted report
        """
        logger.info("Generating diagnostic report")

        lines = []
        lines.append(f"# SPA页面诊断报告")
        lines.append("")
        lines.append(f"**测试URL**: {url}")
        lines.append(f"**测试时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Raw HTML statistics
        if 'html_stats' in results:
            stats = results['html_stats']
            lines.append("## 原始HTML统计")
            lines.append("")
            lines.append(f"- **HTML大小**: {stats['size']:,} 字节 ({stats['size']/1024:.1f} KB)")
            lines.append(f"- **标签总数**: ~{stats['tag_count']:,}")
            lines.append(f"- **div标签**: {stats['div_count']:,}")
            lines.append(f"- **script标签**: {stats['script_count']:,}")
            lines.append("")

        # DOM structure analysis
        if 'dom_analysis' in results:
            dom = results['dom_analysis']
            lines.append("## DOM结构分析")
            lines.append("")
            lines.append("主要内容容器：")
            lines.append("")

            if dom:
                lines.append("| 选择器 | 标签 | 文本长度 | 子元素数 | 预览 |")
                lines.append("|--------|------|----------|----------|------|")

                for selector, info in dom.items():
                    preview = info.preview.replace('|', '\\|')[:50] + "..."
                    lines.append(f"| `{selector}` | {info.tag_name} | {info.text_length:,} | {info.child_count} | {preview} |")
            else:
                lines.append("*(DOM分析不可用)*")

            lines.append("")

        # Wait strategy comparison
        if 'wait_strategies' in results:
            wait_results = results['wait_strategies']
            lines.append("## 等待策略对比")
            lines.append("")
            lines.append("| 等待时间 | HTML大小 | 内容提取成功 | 内容长度 | 错误 |")
            lines.append("|----------|----------|--------------|----------|------|")

            for result in wait_results:
                error_msg = result.error[:30] + "..." if result.error else "-"
                success_icon = "✓" if result.content_extracted else "✗"
                lines.append(f"| {result.wait_time}s | {result.html_length:,} | {success_icon} | {result.content_length:,} | {error_msg} |")

            lines.append("")

        # Selector matching
        if 'selector_tests' in results:
            selector_results = results['selector_tests']
            lines.append("## 选择器匹配情况")
            lines.append("")

            matched = [r for r in selector_results if r.matched]
            unmatched = [r for r in selector_results if not r.matched]

            lines.append(f"**匹配成功**: {len(matched)}/{len(selector_results)}")
            lines.append("")

            if matched:
                lines.append("### 匹配的选择器")
                lines.append("")
                lines.append("| 选择器 | 元素数 | 文本长度 | 预览 |")
                lines.append("|--------|--------|----------|------|")

                for result in matched:
                    preview = result.preview.replace('|', '\\|')[:50] + "..."
                    lines.append(f"| `{result.selector}` | {result.element_count} | {result.text_length:,} | {preview} |")

                lines.append("")

            if unmatched:
                lines.append("### 未匹配的选择器")
                lines.append("")
                for result in unmatched:
                    lines.append(f"- `{result.selector}`")
                lines.append("")

        # Root cause analysis
        lines.append("## 根因分析和建议")
        lines.append("")

        # Analyze results to determine root cause
        root_causes = []
        recommendations = []

        # Check if HTML is too small
        if 'html_stats' in results and results['html_stats']['size'] < 50000:
            root_causes.append("HTML内容较小，可能页面加载不完整")
            recommendations.append("增加页面加载等待时间")

        # Check if no selectors matched
        if 'selector_tests' in results:
            matched_count = sum(1 for r in results['selector_tests'] if r.matched)
            if matched_count == 0:
                root_causes.append("所有内容选择器都未匹配")
                recommendations.append("页面使用非标准DOM结构，需要添加针对性选择器")
            elif matched_count < 3:
                root_causes.append(f"只有{matched_count}个选择器匹配，匹配率较低")
                recommendations.append("扩展选择器列表以支持更多页面结构")

        # Check if matched but content is empty
        if 'selector_tests' in results:
            matched_but_empty = [r for r in results['selector_tests'] if r.matched and r.text_length < 200]
            if matched_but_empty:
                root_causes.append(f"{len(matched_but_empty)}个选择器匹配但内容为空或很短")
                recommendations.append("匹配到的元素可能不是真正的内容容器，需要更精确的选择器")

        # Check wait strategy results
        if 'wait_strategies' in results:
            all_failed = all(not r.content_extracted for r in results['wait_strategies'] if not r.error)
            if all_failed:
                root_causes.append("所有等待策略都无法提取内容")
                recommendations.append("问题不在等待时间，而在选择器或页面结构")
            else:
                successful = [r for r in results['wait_strategies'] if r.content_extracted]
                if successful:
                    min_wait = min(r.wait_time for r in successful)
                    recommendations.append(f"建议使用至少{min_wait}秒的等待时间")

        if root_causes:
            lines.append("### 识别的问题")
            lines.append("")
            for i, cause in enumerate(root_causes, 1):
                lines.append(f"{i}. {cause}")
            lines.append("")
        else:
            lines.append("未识别到明显问题，需要进一步手动分析。")
            lines.append("")

        if recommendations:
            lines.append("### 建议的解决方案")
            lines.append("")
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        # Add specific recommendation for React.dev
        if 'react.dev' in url.lower():
            lines.append("### React.dev特定建议")
            lines.append("")
            lines.append("React.dev使用现代SPA架构，建议：")
            lines.append("1. 检查页面使用的主容器ID（通常是`#root`或`#app`）")
            lines.append("2. 等待React hydration完成")
            lines.append("3. 可能需要等待特定的data-ready属性")
            lines.append("4. 考虑使用网络空闲等待策略")
            lines.append("")

        report = "\n".join(lines)
        logger.info("Report generation complete")

        return report


def main():
    """Main diagnostic workflow"""
    print("=== SPA页面诊断工具 ===\n")

    # Initialize diagnostics
    diagnostics = SPADiagnostics()

    # Target URL
    url = "https://react.dev/"
    print(f"目标URL: {url}\n")

    # Step 1: Fetch and save raw HTML
    print("1. 获取原始HTML...")
    try:
        raw_html, html_size, html_path = diagnostics.save_raw_html(url, "reactdev_raw.html")
        print(f"   ✓ 成功: {html_size:,} 字节")
        print(f"   保存到: {html_path}\n")
    except Exception as e:
        print(f"   ✗ 失败: {e}\n")
        return 1

    # Calculate HTML statistics
    html_stats = {
        'size': html_size,
        'tag_count': len(re.findall(r'<[^>]+>', raw_html)),
        'div_count': len(re.findall(r'<div[^>]*>', raw_html, re.I)),
        'script_count': len(re.findall(r'<script[^>]*>', raw_html, re.I)),
    }

    # Step 2: Analyze DOM structure
    print("2. 分析DOM结构...")
    dom_analysis = diagnostics.analyze_dom_structure(raw_html)
    print(f"   ✓ 找到 {len(dom_analysis)} 个主要容器\n")

    # Step 3: Test wait strategies
    print("3. 测试等待策略（这可能需要几分钟）...")
    wait_results = diagnostics.test_wait_strategies(url)
    successful_waits = sum(1 for r in wait_results if r.content_extracted)
    print(f"   ✓ 完成: {successful_waits}/{len(wait_results)} 个策略成功\n")

    # Step 4: Test parser selectors
    print("4. 测试解析器选择器...")
    selector_results = diagnostics.test_parser_selectors(raw_html)
    matched_selectors = sum(1 for r in selector_results if r.matched)
    print(f"   ✓ 匹配: {matched_selectors}/{len(selector_results)} 个选择器\n")

    # Step 5: Generate report
    print("5. 生成诊断报告...")
    results = {
        'html_stats': html_stats,
        'dom_analysis': dom_analysis,
        'wait_strategies': wait_results,
        'selector_tests': selector_results,
    }

    report = diagnostics.generate_report(url, results)

    # Save report
    report_path = diagnostics.output_dir / "diagnosis_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"   ✓ 报告已保存到: {report_path}\n")

    print("=" * 50)
    print("诊断完成！")
    print(f"报告位置: {report_path}")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())