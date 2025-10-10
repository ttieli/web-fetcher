#!/usr/bin/env python3
"""
URL Suite Parser - Parse and filter regression test URLs
URL 套件解析器 - 解析和过滤回归测试 URL

This module parses the url_suite.txt file and provides filtering capabilities.
本模块解析 url_suite.txt 文件并提供过滤功能。

Format: <url> | <description> | <expected_strategy> | <tags>
格式：<url> | <描述> | <期望策略> | <标签>
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Optional, Union
import logging


@dataclass
class URLTest:
    """
    Represents a single URL test case from the suite.
    表示套件中的单个 URL 测试用例。

    Attributes:
        url: Target URL to test / 目标测试 URL
        description: Brief description of the test / 测试简短描述
        expected_strategies: Expected fetch strategies (urllib/selenium/manual) / 期望的抓取策略列表
        tags: Set of tags for filtering / 用于过滤的标签集
        line_number: Source line number (for error reporting) / 源文件行号（用于错误报告）
        compare_methods: Enable comparison when testing multiple methods / 启用多方法测试时的比较

    Note:
        For backward compatibility, expected_strategy (singular) is supported via property.
        为了向后兼容，通过属性支持 expected_strategy（单数）。
    """
    url: str
    description: str
    expected_strategies: List[str]
    tags: Set[str]
    line_number: int
    compare_methods: bool = False

    @property
    def expected_strategy(self) -> str:
        """
        Backward compatibility property for single-method tests.
        单方法测试的向后兼容性属性。

        Returns the first strategy in the list.
        返回列表中的第一个策略。
        """
        return self.expected_strategies[0] if self.expected_strategies else "urllib"

    @property
    def is_dual_method(self) -> bool:
        """
        Check if this test uses dual-method testing.
        检查此测试是否使用双方法测试。

        Returns:
            bool: True if testing with multiple methods
        """
        return len(self.expected_strategies) > 1

    def has_strategy(self, strategy: str) -> bool:
        """
        Check if test includes a specific strategy.
        检查测试是否包含特定策略。

        Args:
            strategy: Strategy name (urllib/selenium/manual)

        Returns:
            bool: True if strategy is in expected_strategies
        """
        return strategy.lower() in [s.lower() for s in self.expected_strategies]

    def has_tag(self, tag: str) -> bool:
        """Check if test has a specific tag / 检查测试是否有特定标签"""
        return tag.lower() in {t.lower() for t in self.tags}

    def has_any_tag(self, tags: Set[str]) -> bool:
        """Check if test has any of the specified tags / 检查测试是否有任何指定标签"""
        if not tags:
            return True
        return bool({t.lower() for t in self.tags} & {t.lower() for t in tags})

    def has_all_tags(self, tags: Set[str]) -> bool:
        """Check if test has all of the specified tags / 检查测试是否有所有指定标签"""
        if not tags:
            return True
        return {t.lower() for t in tags}.issubset({t.lower() for t in self.tags})


def parse_url_suite(file_path: Path) -> List[URLTest]:
    """
    Parse the URL suite file and return list of URL test cases.
    解析 URL 套件文件并返回 URL 测试用例列表。

    Args:
        file_path: Path to url_suite.txt / url_suite.txt 的路径

    Returns:
        List[URLTest]: Parsed test cases / 解析后的测试用例

    Raises:
        FileNotFoundError: If suite file doesn't exist / 如果套件文件不存在
        ValueError: If file format is invalid / 如果文件格式无效
    """
    if not file_path.exists():
        raise FileNotFoundError(f"URL suite file not found: {file_path}")

    tests = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            # Skip empty lines and comments
            # 跳过空行和注释
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Parse pipe-delimited format
            # 解析管道分隔格式
            parts = [p.strip() for p in line.split('|')]

            if len(parts) != 4:
                logging.warning(
                    f"Skipping malformed line {line_num}: expected 4 fields, got {len(parts)}"
                )
                continue

            url, description, strategy_str, tags_str = parts

            # Validate required fields
            # 验证必需字段
            if not url or not url.startswith(('http://', 'https://')):
                logging.warning(f"Skipping line {line_num}: invalid URL '{url}'")
                continue

            if not description:
                logging.warning(f"Skipping line {line_num}: empty description")
                continue

            # Parse strategies (supports both single and comma-separated list)
            # 解析策略（支持单个和逗号分隔列表）
            # Examples:
            #   "urllib" → ["urllib"]
            #   "urllib,selenium" → ["urllib", "selenium"]
            #   "urllib,selenium,compare" → ["urllib", "selenium"] with compare_methods=True
            expected_strategies = []
            compare_methods = False

            if strategy_str:
                strategy_parts = [s.strip().lower() for s in strategy_str.split(',') if s.strip()]

                # Check for special 'compare' flag
                # 检查特殊的 'compare' 标志
                if 'compare' in strategy_parts:
                    compare_methods = True
                    strategy_parts = [s for s in strategy_parts if s != 'compare']

                # Validate strategies
                # 验证策略
                valid_strategies = {'urllib', 'selenium', 'manual'}
                for strategy in strategy_parts:
                    if strategy not in valid_strategies:
                        logging.warning(
                            f"Line {line_num}: unexpected strategy '{strategy}', "
                            f"expected urllib/selenium/manual"
                        )
                    else:
                        expected_strategies.append(strategy)

            # Default to urllib if no valid strategies found
            # 如果未找到有效策略，默认为 urllib
            if not expected_strategies:
                expected_strategies = ['urllib']
                logging.warning(
                    f"Line {line_num}: no valid strategies, defaulting to urllib"
                )

            # Parse tags (comma-separated)
            # 解析标签（逗号分隔）
            tags = set()
            if tags_str:
                tags = {t.strip() for t in tags_str.split(',') if t.strip()}

            tests.append(URLTest(
                url=url,
                description=description,
                expected_strategies=expected_strategies,
                tags=tags,
                line_number=line_num,
                compare_methods=compare_methods
            ))

    logging.info(f"Parsed {len(tests)} test cases from {file_path}")
    return tests


def filter_by_tags(
    tests: List[URLTest],
    include_tags: Optional[Set[str]] = None,
    exclude_tags: Optional[Set[str]] = None
) -> List[URLTest]:
    """
    Filter test cases by tags.
    按标签过滤测试用例。

    Args:
        tests: List of URL test cases / URL 测试用例列表
        include_tags: Only include tests with ANY of these tags / 仅包含具有这些标签中任何一个的测试
        exclude_tags: Exclude tests with ANY of these tags / 排除具有这些标签中任何一个的测试

    Returns:
        List[URLTest]: Filtered test cases / 过滤后的测试用例

    Note:
        - If include_tags is None or empty, all tests pass the include filter
        - 如果 include_tags 为 None 或为空，所有测试都通过包含过滤器
        - exclude_tags takes precedence over include_tags
        - exclude_tags 优先于 include_tags
    """
    filtered = tests

    # Apply include filter (tests must have ANY of the specified tags)
    # 应用包含过滤器（测试必须有任何指定的标签）
    if include_tags:
        filtered = [t for t in filtered if t.has_any_tag(include_tags)]
        logging.info(
            f"Include filter ({','.join(include_tags)}): {len(filtered)}/{len(tests)} tests"
        )

    # Apply exclude filter (tests must NOT have ANY of the specified tags)
    # 应用排除过滤器（测试不能有任何指定的标签）
    if exclude_tags:
        before_count = len(filtered)
        filtered = [t for t in filtered if not t.has_any_tag(exclude_tags)]
        logging.info(
            f"Exclude filter ({','.join(exclude_tags)}): {len(filtered)}/{before_count} tests"
        )

    return filtered


def get_unique_tags(tests: List[URLTest]) -> Set[str]:
    """
    Get all unique tags from a list of tests.
    从测试列表中获取所有唯一标签。

    Args:
        tests: List of URL test cases / URL 测试用例列表

    Returns:
        Set[str]: All unique tags / 所有唯一标签
    """
    all_tags = set()
    for test in tests:
        all_tags.update(test.tags)
    return all_tags


def group_by_tag(tests: List[URLTest]) -> dict:
    """
    Group tests by tag for analysis.
    按标签分组测试以进行分析。

    Args:
        tests: List of URL test cases / URL 测试用例列表

    Returns:
        dict: Mapping from tag to list of tests / 从标签到测试列表的映射
    """
    groups = {}
    for test in tests:
        for tag in test.tags:
            if tag not in groups:
                groups[tag] = []
            groups[tag].append(test)
    return groups


if __name__ == '__main__':
    # Test the parser with the actual suite file
    # 使用实际套件文件测试解析器
    import sys

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    # Find url_suite.txt relative to this file
    # 相对于此文件查找 url_suite.txt
    suite_file = Path(__file__).parent.parent / 'url_suite.txt'

    try:
        tests = parse_url_suite(suite_file)
        print(f"\n✓ Successfully parsed {len(tests)} tests")

        # Display statistics
        # 显示统计信息
        print(f"\nStrategy breakdown:")
        strategies = {}
        for test in tests:
            strategies[test.expected_strategy] = strategies.get(test.expected_strategy, 0) + 1
        for strategy, count in sorted(strategies.items()):
            print(f"  {strategy}: {count}")

        # Display tags
        # 显示标签
        all_tags = get_unique_tags(tests)
        print(f"\nAvailable tags ({len(all_tags)}):")
        for tag in sorted(all_tags):
            count = sum(1 for t in tests if tag in t.tags)
            print(f"  {tag}: {count} tests")

        # Test filtering
        # 测试过滤
        fast_tests = filter_by_tags(tests, include_tags={'fast'})
        print(f"\n✓ Fast tests: {len(fast_tests)}")

        no_manual = filter_by_tags(tests, exclude_tags={'manual'})
        print(f"✓ Non-manual tests: {len(no_manual)}")

    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)
