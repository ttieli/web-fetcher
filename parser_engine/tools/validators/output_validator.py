#!/usr/bin/env python3
"""
Output Validator / 输出校验器

Compares extraction outputs between different fetchers.
比较不同抓取器之间的提取输出。
"""

from typing import Dict, Any, List, Tuple
from difflib import unified_diff
import json


class OutputValidator:
    """Validates output consistency / 验证输出一致性"""

    def __init__(self, tolerance: float = 0.1):
        """
        Initialize output validator / 初始化输出校验器

        Args:
            tolerance: Acceptable difference ratio (0.0 to 1.0)
                      0.1 means 10% difference is acceptable
        """
        self.tolerance = tolerance

    def compare_outputs(
        self,
        urllib_output: Dict[str, Any],
        selenium_output: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Compare outputs from urllib and selenium / 比较urllib和selenium的输出

        Args:
            urllib_output: Output from urllib fetcher
            selenium_output: Output from selenium fetcher

        Returns:
            (is_consistent, diff_messages)
            - is_consistent: True if outputs are consistent within tolerance
            - diff_messages: List of difference messages
        """
        diffs = []

        # Get all unique keys from both outputs
        all_keys = set(urllib_output.keys()) | set(selenium_output.keys())

        for key in all_keys:
            # Check for missing fields
            if key not in urllib_output:
                diffs.append(f"Field '{key}' missing in urllib output")
                continue
            if key not in selenium_output:
                diffs.append(f"Field '{key}' missing in selenium output")
                continue

            # Compare field values
            urllib_value = urllib_output[key]
            selenium_value = selenium_output[key]

            # Handle None values
            if urllib_value is None and selenium_value is None:
                continue
            if urllib_value is None:
                diffs.append(f"Field '{key}': urllib=None, selenium='{selenium_value}'")
                continue
            if selenium_value is None:
                diffs.append(f"Field '{key}': urllib='{urllib_value}', selenium=None")
                continue

            # Compare based on type
            if isinstance(urllib_value, str) and isinstance(selenium_value, str):
                diff_msg = self._compare_strings(key, urllib_value, selenium_value)
                if diff_msg:
                    diffs.append(diff_msg)
            elif isinstance(urllib_value, list) and isinstance(selenium_value, list):
                diff_msg = self._compare_lists(key, urllib_value, selenium_value)
                if diff_msg:
                    diffs.append(diff_msg)
            elif isinstance(urllib_value, dict) and isinstance(selenium_value, dict):
                # Recursively compare dictionaries
                nested_consistent, nested_diffs = self.compare_outputs(
                    urllib_value, selenium_value
                )
                if not nested_consistent:
                    for nested_diff in nested_diffs:
                        diffs.append(f"{key}.{nested_diff}")
            elif urllib_value != selenium_value:
                diffs.append(
                    f"Field '{key}': urllib={urllib_value}, selenium={selenium_value}"
                )

        # Determine if outputs are consistent
        # Allow some differences based on tolerance
        is_consistent = len(diffs) == 0 or self._check_tolerance(diffs, all_keys)

        return (is_consistent, diffs)

    def _compare_strings(self, key: str, str1: str, str2: str) -> str:
        """
        Compare two string values / 比较两个字符串值

        Args:
            key: Field name for error reporting
            str1: First string (urllib)
            str2: Second string (selenium)

        Returns:
            Difference message if significant difference found, empty string otherwise
        """
        # Normalize whitespace for comparison
        normalized1 = ' '.join(str1.split())
        normalized2 = ' '.join(str2.split())

        if normalized1 == normalized2:
            return ""

        # Calculate difference ratio
        len1 = len(normalized1)
        len2 = len(normalized2)

        if len1 == 0 and len2 == 0:
            return ""

        max_len = max(len1, len2)
        if max_len == 0:
            return ""

        # Simple difference ratio based on length
        diff_ratio = abs(len1 - len2) / max_len

        if diff_ratio > self.tolerance:
            preview1 = normalized1[:50] + ('...' if len(normalized1) > 50 else '')
            preview2 = normalized2[:50] + ('...' if len(normalized2) > 50 else '')
            return (
                f"Field '{key}': Significant difference (ratio: {diff_ratio:.2%})\n"
                f"  urllib:   '{preview1}'\n"
                f"  selenium: '{preview2}'"
            )

        return ""

    def _compare_lists(self, key: str, list1: List[Any], list2: List[Any]) -> str:
        """
        Compare two list values / 比较两个列表值

        Args:
            key: Field name for error reporting
            list1: First list (urllib)
            list2: Second list (selenium)

        Returns:
            Difference message if significant difference found, empty string otherwise
        """
        len1 = len(list1)
        len2 = len(list2)

        if len1 == len2 == 0:
            return ""

        if len1 != len2:
            return (
                f"Field '{key}': Different list lengths "
                f"(urllib={len1}, selenium={len2})"
            )

        # Compare individual elements
        for i, (item1, item2) in enumerate(zip(list1, list2)):
            if item1 != item2:
                return (
                    f"Field '{key}[{i}]': Different values\n"
                    f"  urllib:   {item1}\n"
                    f"  selenium: {item2}"
                )

        return ""

    def _check_tolerance(self, diffs: List[str], all_keys: set) -> bool:
        """
        Check if differences are within tolerance / 检查差异是否在容差范围内

        Args:
            diffs: List of difference messages
            all_keys: Set of all field keys

        Returns:
            True if within tolerance, False otherwise
        """
        if not all_keys:
            return True

        # Calculate error ratio
        error_ratio = len(diffs) / len(all_keys)
        return error_ratio <= self.tolerance

    def generate_diff_report(
        self,
        urllib_output: Dict[str, Any],
        selenium_output: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable diff report / 生成可读的差异报告

        Args:
            urllib_output: Output from urllib fetcher
            selenium_output: Output from selenium fetcher

        Returns:
            Formatted diff report string
        """
        is_consistent, diffs = self.compare_outputs(urllib_output, selenium_output)

        report = []
        report.append("=" * 70)
        report.append("Output Comparison Report / 输出比较报告")
        report.append("=" * 70)

        # Summary
        report.append(f"\nStatus: {'✓ CONSISTENT' if is_consistent else '✗ INCONSISTENT'}")
        report.append(f"Tolerance: {self.tolerance:.1%}")
        report.append(f"Differences found: {len(diffs)}")

        # Field comparison
        all_keys = sorted(set(urllib_output.keys()) | set(selenium_output.keys()))
        report.append(f"\nTotal fields: {len(all_keys)}")

        # Detailed differences
        if diffs:
            report.append("\n" + "-" * 70)
            report.append("Differences / 差异:")
            report.append("-" * 70)
            for i, diff in enumerate(diffs, 1):
                report.append(f"\n{i}. {diff}")
        else:
            report.append("\n✓ No differences found. Outputs are identical.")

        # Field-by-field summary
        report.append("\n" + "-" * 70)
        report.append("Field-by-field Summary / 逐字段摘要:")
        report.append("-" * 70)

        for key in all_keys:
            in_urllib = key in urllib_output
            in_selenium = key in selenium_output

            if in_urllib and in_selenium:
                status = "✓"
            else:
                status = "✗"

            report.append(f"{status} {key}")
            if not in_urllib:
                report.append(f"    Missing in urllib output")
            if not in_selenium:
                report.append(f"    Missing in selenium output")

        report.append("=" * 70)

        return "\n".join(report)

    def compare_json_files(
        self, urllib_file: str, selenium_file: str
    ) -> Tuple[bool, List[str]]:
        """
        Compare outputs from JSON files / 比较JSON文件输出

        Args:
            urllib_file: Path to urllib output JSON file
            selenium_file: Path to selenium output JSON file

        Returns:
            (is_consistent, diff_messages)

        Raises:
            FileNotFoundError: If either file is not found
            json.JSONDecodeError: If JSON is invalid
        """
        with open(urllib_file, 'r', encoding='utf-8') as f:
            urllib_output = json.load(f)

        with open(selenium_file, 'r', encoding='utf-8') as f:
            selenium_output = json.load(f)

        return self.compare_outputs(urllib_output, selenium_output)

    def save_diff_report(
        self,
        urllib_output: Dict[str, Any],
        selenium_output: Dict[str, Any],
        output_path: str
    ) -> None:
        """
        Generate and save diff report to file / 生成并保存差异报告到文件

        Args:
            urllib_output: Output from urllib fetcher
            selenium_output: Output from selenium fetcher
            output_path: Path to save report file
        """
        report = self.generate_diff_report(urllib_output, selenium_output)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
