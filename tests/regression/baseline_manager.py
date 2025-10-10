#!/usr/bin/env python3
"""
Baseline Manager - Save and compare regression test baselines
基线管理器 - 保存和比较回归测试基线

This module manages baseline test results for regression detection.
本模块管理基线测试结果以进行回归检测。
"""

import json
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from tests.regression.regression_runner import TestResult, TestStatus


@dataclass
class BaselineResult:
    """
    Simplified test result for baseline storage.
    用于基线存储的简化测试结果。

    Attributes:
        url: Test URL / 测试 URL
        status: Test status / 测试状态
        duration: Execution time / 执行时间
        content_size: Content size in bytes / 内容大小（字节）
        strategy: Strategy used / 使用的策略
    """
    url: str
    status: str
    duration: float
    content_size: int
    strategy: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary / 转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'BaselineResult':
        """Create from dictionary / 从字典创建"""
        return cls(**data)


@dataclass
class Baseline:
    """
    Complete baseline containing metadata and results.
    包含元数据和结果的完整基线。

    Attributes:
        timestamp: When baseline was created / 基线创建时间
        suite_version: Hash of suite file / 套件文件的哈希
        results: Map of URL to baseline result / URL 到基线结果的映射
        metadata: Additional metadata / 额外的元数据
    """
    timestamp: str
    suite_version: str
    results: Dict[str, BaselineResult]
    metadata: Dict[str, any] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization / 转换为字典用于 JSON 序列化"""
        return {
            'timestamp': self.timestamp,
            'suite_version': self.suite_version,
            'results': {url: result.to_dict() for url, result in self.results.items()},
            'metadata': self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Baseline':
        """Create from dictionary / 从字典创建"""
        results = {
            url: BaselineResult.from_dict(result_data)
            for url, result_data in data['results'].items()
        }
        return cls(
            timestamp=data['timestamp'],
            suite_version=data['suite_version'],
            results=results,
            metadata=data.get('metadata', {})
        )


@dataclass
class ComparisonResult:
    """
    Result of comparing two baselines.
    比较两个基线的结果。

    Attributes:
        regressions: Tests that got worse / 变差的测试
        improvements: Tests that got better / 变好的测试
        new_tests: Tests only in current / 仅在当前中的测试
        removed_tests: Tests only in baseline / 仅在基线中的测试
        unchanged: Tests with no significant changes / 没有显著变化的测试
    """
    regressions: List[Dict]
    improvements: List[Dict]
    new_tests: List[str]
    removed_tests: List[str]
    unchanged: List[str]

    @property
    def has_regressions(self) -> bool:
        """Check if any regressions detected / 检查是否检测到任何回归"""
        return len(self.regressions) > 0

    @property
    def summary(self) -> str:
        """Get summary string / 获取摘要字符串"""
        return (
            f"Regressions: {len(self.regressions)}, "
            f"Improvements: {len(self.improvements)}, "
            f"New: {len(self.new_tests)}, "
            f"Removed: {len(self.removed_tests)}, "
            f"Unchanged: {len(self.unchanged)}"
        )


class BaselineManager:
    """
    Manage baseline test results.
    管理基线测试结果。
    """

    # Thresholds for regression detection
    # 回归检测的阈值
    PERFORMANCE_REGRESSION_THRESHOLD = 0.20  # 20% slower
    CONTENT_SIZE_THRESHOLD = 0.10  # 10% size change

    def __init__(self, baseline_dir: Optional[Path] = None):
        """
        Initialize baseline manager.
        初始化基线管理器。

        Args:
            baseline_dir: Directory to store baselines / 存储基线的目录
        """
        if baseline_dir is None:
            # Default to tests/regression/baselines
            # 默认为 tests/regression/baselines
            baseline_dir = Path(__file__).parent / 'baselines'

        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

    def save_baseline(
        self,
        name: str,
        results: List[TestResult],
        suite_file: Optional[Path] = None,
        metadata: Optional[Dict] = None
    ) -> Path:
        """
        Save test results as a baseline.
        将测试结果保存为基线。

        Args:
            name: Baseline name / 基线名称
            results: Test results to save / 要保存的测试结果
            suite_file: Suite file for version hash / 用于版本哈希的套件文件
            metadata: Additional metadata / 额外的元数据

        Returns:
            Path: Path to saved baseline file / 保存的基线文件的路径
        """
        # Calculate suite version
        # 计算套件版本
        suite_version = self._calculate_suite_version(suite_file) if suite_file else "unknown"

        # Convert results to baseline format
        # 将结果转换为基线格式
        baseline_results = {}
        for result in results:
            # Skip skipped tests
            # 跳过跳过的测试
            if result.status == TestStatus.SKIPPED:
                continue

            baseline_results[result.test.url] = BaselineResult(
                url=result.test.url,
                status=result.status.value,
                duration=result.duration,
                content_size=result.content_size,
                strategy=result.strategy_used
            )

        # Create baseline
        # 创建基线
        baseline = Baseline(
            timestamp=datetime.now().isoformat(),
            suite_version=suite_version,
            results=baseline_results,
            metadata=metadata or {}
        )

        # Save to file
        # 保存到文件
        baseline_file = self.baseline_dir / f"{name}.json"
        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(baseline.to_dict(), f, indent=2, ensure_ascii=False)

        return baseline_file

    def load_baseline(self, name: str) -> Baseline:
        """
        Load a baseline from file.
        从文件加载基线。

        Args:
            name: Baseline name (with or without .json) / 基线名称（带或不带 .json）

        Returns:
            Baseline: Loaded baseline / 加载的基线

        Raises:
            FileNotFoundError: If baseline file not found / 如果找不到基线文件
        """
        # Handle both "name" and "name.json"
        # 处理 "name" 和 "name.json"
        if not name.endswith('.json'):
            name = f"{name}.json"

        baseline_file = self.baseline_dir / name

        if not baseline_file.exists():
            raise FileNotFoundError(f"Baseline not found: {baseline_file}")

        with open(baseline_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return Baseline.from_dict(data)

    def list_baselines(self) -> List[str]:
        """
        List all available baselines.
        列出所有可用的基线。

        Returns:
            List[str]: List of baseline names / 基线名称列表
        """
        if not self.baseline_dir.exists():
            return []

        return [f.stem for f in self.baseline_dir.glob('*.json')]

    def compare(
        self,
        baseline: Baseline,
        current_results: List[TestResult]
    ) -> ComparisonResult:
        """
        Compare current results against baseline.
        将当前结果与基线进行比较。

        Args:
            baseline: Baseline to compare against / 要比较的基线
            current_results: Current test results / 当前测试结果

        Returns:
            ComparisonResult: Comparison analysis / 比较分析
        """
        # Convert current results to dict
        # 将当前结果转换为字典
        current_dict = {}
        for result in current_results:
            if result.status != TestStatus.SKIPPED:
                current_dict[result.test.url] = result

        # Initialize comparison lists
        # 初始化比较列表
        regressions = []
        improvements = []
        unchanged = []

        # Get URL sets
        # 获取 URL 集
        baseline_urls = set(baseline.results.keys())
        current_urls = set(current_dict.keys())

        new_tests = list(current_urls - baseline_urls)
        removed_tests = list(baseline_urls - current_urls)
        common_urls = baseline_urls & current_urls

        # Compare common URLs
        # 比较共同的 URL
        for url in common_urls:
            baseline_result = baseline.results[url]
            current_result = current_dict[url]

            changes = self._analyze_changes(baseline_result, current_result)

            if changes['is_regression']:
                regressions.append({
                    'url': url,
                    'baseline': baseline_result.to_dict(),
                    'current': self._result_to_dict(current_result),
                    'changes': changes
                })
            elif changes['is_improvement']:
                improvements.append({
                    'url': url,
                    'baseline': baseline_result.to_dict(),
                    'current': self._result_to_dict(current_result),
                    'changes': changes
                })
            else:
                unchanged.append(url)

        return ComparisonResult(
            regressions=regressions,
            improvements=improvements,
            new_tests=new_tests,
            removed_tests=removed_tests,
            unchanged=unchanged
        )

    def _analyze_changes(
        self,
        baseline_result: BaselineResult,
        current_result: TestResult
    ) -> Dict:
        """
        Analyze changes between baseline and current result.
        分析基线和当前结果之间的变化。

        Args:
            baseline_result: Baseline result / 基线结果
            current_result: Current result / 当前结果

        Returns:
            Dict: Analysis of changes / 变化分析
        """
        changes = {
            'is_regression': False,
            'is_improvement': False,
            'status_changed': False,
            'performance_delta': 0.0,
            'performance_delta_pct': 0.0,
            'size_delta': 0,
            'size_delta_pct': 0.0,
            'strategy_changed': False,
            'details': []
        }

        # Status change
        # 状态变化
        baseline_status = baseline_result.status
        current_status = current_result.status.value

        if baseline_status != current_status:
            changes['status_changed'] = True
            changes['details'].append(f"Status: {baseline_status} → {current_status}")

            # Status regression: PASSED → FAILED/ERROR
            # 状态回归：PASSED → FAILED/ERROR
            if baseline_status == 'passed' and current_status in ['failed', 'error']:
                changes['is_regression'] = True
            # Status improvement: FAILED/ERROR → PASSED
            # 状态改进：FAILED/ERROR → PASSED
            elif baseline_status in ['failed', 'error'] and current_status == 'passed':
                changes['is_improvement'] = True

        # Performance change (only for successful tests)
        # 性能变化（仅适用于成功的测试）
        if baseline_status == 'passed' and current_status == 'passed':
            baseline_duration = baseline_result.duration
            current_duration = current_result.duration

            if baseline_duration > 0:
                delta = current_duration - baseline_duration
                delta_pct = delta / baseline_duration

                changes['performance_delta'] = delta
                changes['performance_delta_pct'] = delta_pct

                # Performance regression: >20% slower
                # 性能回归：> 20% 慢
                if delta_pct > self.PERFORMANCE_REGRESSION_THRESHOLD:
                    changes['is_regression'] = True
                    changes['details'].append(
                        f"Performance: {baseline_duration:.2f}s → {current_duration:.2f}s "
                        f"({delta_pct*100:+.1f}% slower)"
                    )
                # Performance improvement: >20% faster
                # 性能改进：> 20% 快
                elif delta_pct < -self.PERFORMANCE_REGRESSION_THRESHOLD:
                    changes['is_improvement'] = True
                    changes['details'].append(
                        f"Performance: {baseline_duration:.2f}s → {current_duration:.2f}s "
                        f"({abs(delta_pct)*100:.1f}% faster)"
                    )

            # Content size change
            # 内容大小变化
            baseline_size = baseline_result.content_size
            current_size = current_result.content_size

            if baseline_size > 0:
                size_delta = current_size - baseline_size
                size_delta_pct = size_delta / baseline_size

                changes['size_delta'] = size_delta
                changes['size_delta_pct'] = size_delta_pct

                # Significant size change: >10%
                # 显著大小变化：> 10%
                if abs(size_delta_pct) > self.CONTENT_SIZE_THRESHOLD:
                    changes['details'].append(
                        f"Content size: {baseline_size:,} → {current_size:,} bytes "
                        f"({size_delta_pct*100:+.1f}%)"
                    )

        # Strategy change
        # 策略变化
        if baseline_result.strategy and current_result.strategy_used:
            if baseline_result.strategy != current_result.strategy_used:
                changes['strategy_changed'] = True
                changes['details'].append(
                    f"Strategy: {baseline_result.strategy} → {current_result.strategy_used}"
                )

        return changes

    def _result_to_dict(self, result: TestResult) -> dict:
        """
        Convert TestResult to dictionary.
        将 TestResult 转换为字典。

        Args:
            result: Test result / 测试结果

        Returns:
            dict: Dictionary representation / 字典表示
        """
        return {
            'status': result.status.value,
            'duration': result.duration,
            'content_size': result.content_size,
            'strategy': result.strategy_used
        }

    def _calculate_suite_version(self, suite_file: Path) -> str:
        """
        Calculate hash of suite file for version tracking.
        计算套件文件的哈希以进行版本跟踪。

        Args:
            suite_file: Path to suite file / 套件文件的路径

        Returns:
            str: SHA256 hash of suite file / 套件文件的 SHA256 哈希
        """
        if not suite_file or not suite_file.exists():
            return "unknown"

        with open(suite_file, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:8]
