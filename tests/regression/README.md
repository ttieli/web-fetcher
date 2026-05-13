# Regression Test Harness - Complete Guide
# 回归测试工具 - 完整指南

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.7+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](../../LICENSE)

## Table of Contents / 目录

- [Overview](#overview--概述)
- [Quick Start](#quick-start--快速入门)
- [Features](#features--功能特性)
- [Installation](#installation--安装)
- [Usage](#usage--使用方法)
  - [Basic Commands](#basic-commands--基本命令)
  - [Tag Filtering](#tag-filtering--标签过滤)
  - [Baseline Management](#baseline-management--基线管理)
  - [Report Generation](#report-generation--报告生成)
- [Integration](#integration--集成)
  - [CI/CD](#cicd-integration--cicd-集成)
  - [Docker](#docker-integration--docker-集成)
- [Advanced Usage](#advanced-usage--高级用法)
- [Troubleshooting](#troubleshooting--故障排除)
- [API Documentation](#api-documentation--api-文档)
- [Contributing](#contributing--贡献)

## Overview / 概述

The Regression Test Harness is a comprehensive testing framework for the Web Fetcher project. It enables automated testing of web content fetching across diverse URL types, platforms, and scenarios.

回归测试工具是Web Fetcher项目的综合测试框架。它能够在不同的URL类型、平台和场景中自动测试网页内容抓取。

### Key Features / 主要功能

- **Automated Testing**: Run tests against curated URL suites / 对精选URL套件运行自动化测试
- **Tag-based Filtering**: Flexible test selection using tags / 使用标签灵活选择测试
- **Baseline Comparison**: Track performance over time / 随时间跟踪性能
- **Multiple Report Formats**: Markdown, JSON, Text / Markdown、JSON、文本多种报告格式
- **CI/CD Ready**: GitHub Actions, GitLab CI, Jenkins integration / 支持GitHub Actions、GitLab CI、Jenkins集成
- **Docker Support**: Containerized testing environment / 容器化测试环境

## Quick Start / 快速入门

### 3-Minute Getting Started / 3分钟快速开始

```bash
# 1. Run all fast tests (recommended first run)
#    运行所有快速测试（推荐首次运行）
python scripts/run_regression_suite.py --tags fast

# 2. Save as baseline for future comparison
#    保存为基线以便将来比较
python scripts/run_regression_suite.py --tags fast --save-baseline v1.0

# 3. Generate markdown report
#    生成markdown报告
python scripts/run_regression_suite.py --tags fast --report markdown --output report.md
```

**That's it!** You're now running regression tests.
**就这样！** 您现在正在运行回归测试。

### Common Use Cases / 常见用例

#### Pre-Commit Testing / 提交前测试
```bash
# Quick smoke test (~10 seconds)
# 快速冒烟测试（约10秒）
python scripts/run_regression_suite.py --tags reference,basic
```

#### Pre-Release Validation / 发布前验证
```bash
# Full regression with baseline comparison
# 完整回归测试并与基线比较
python scripts/run_regression_suite.py \
  --exclude-tags manual,slow \
  --baseline baselines/v1.0.json \
  --fail-on-regression \
  --report markdown \
  --output release-report.md
```

#### Platform-Specific Testing / 平台特定测试
```bash
# Test WeChat parser changes
# 测试微信解析器更改
python scripts/run_regression_suite.py --tags wechat --verbose

# Test XiaoHongShu changes
# 测试小红书更改
python scripts/run_regression_suite.py --tags xhs --verbose
```

## Features / 功能特性

### Phase 1: Foundation / 阶段1：基础
- URL suite template with tag system
- Comprehensive test URL coverage
- Documentation framework

### Phase 2: Core Runner / 阶段2：核心运行器
- URL suite parser with validation
- Test execution engine
- Progress display and metrics collection
- CLI interface with filtering

### Phase 3: Baseline & Reporting / 阶段3：基线与报告
- Baseline save/load/compare
- Regression detection
- Multi-format reports (Markdown/JSON/Text)
- Performance tracking

### Phase 4: Documentation & Examples / 阶段4：文档与示例
- Comprehensive documentation suite
- CI/CD integration examples
- Docker support
- Migration guides and quick references

## Installation / 安装

### Prerequisites / 前置要求

```bash
# Python 3.7 or higher
python --version

# Web Fetcher dependencies
pip install -r requirements.txt
```

### No Additional Dependencies! / 无需额外依赖！

The regression test harness uses the existing webfetcher infrastructure. No additional packages required.

回归测试工具使用现有的webfetcher基础设施。无需额外的包。

## Usage / 使用方法

### Basic Commands / 基本命令

#### Run All Tests / 运行所有测试
```bash
# Exclude manual tests by default
# 默认排除手动测试
python scripts/run_regression_suite.py
```

#### Test Single URL / 测试单个URL
```bash
python scripts/run_regression_suite.py --url https://example.com
```

#### Verbose Output / 详细输出
```bash
python scripts/run_regression_suite.py --tags fast --verbose
```

#### Custom Timeout / 自定义超时
```bash
python scripts/run_regression_suite.py --timeout 60
```

### Tag Filtering / 标签过滤

#### Available Tags / 可用标签

| Tag | Description | Count | Speed |
|-----|-------------|-------|-------|
| `fast` | Fast tests (<5s) / 快速测试 | ~13 | ⚡ |
| `slow` | Slow tests (>5s) / 慢速测试 | ~3 | 🐌 |
| `basic` | Basic static sites / 基础静态站点 | ~6 | ⚡ |
| `reference` | HTTPBin test URLs / HTTPBin测试URL | ~6 | ⚡ |
| `wechat` | WeChat articles / 微信文章 | ~3 | 🐌 |
| `xhs` | XiaoHongShu / 小红书 | ~3 | 🐌 |
| `news` | News websites / 新闻网站 | ~2 | ⚡ |
| `developer` | GitHub, StackOverflow / 开发者站点 | ~2 | ⚡ |
| `error` | Expected errors / 预期错误 | ~1 | ⚡ |
| `redirect` | Redirect tests / 重定向测试 | ~2 | ⚡ |
| `manual` | Manual intervention / 需手动干预 | ~0 | ⏸️ |
| `js-required` | JavaScript needed / 需要JavaScript | ~2 | 🐌 |

#### Include Tags / 包含标签
```bash
# Single tag
python scripts/run_regression_suite.py --tags fast

# Multiple tags (OR logic)
# 多个标签（OR逻辑）
python scripts/run_regression_suite.py --tags wechat,xhs
```

#### Exclude Tags / 排除标签
```bash
# Exclude slow tests
# 排除慢速测试
python scripts/run_regression_suite.py --exclude-tags slow

# Exclude multiple
# 排除多个
python scripts/run_regression_suite.py --exclude-tags slow,manual,error
```

#### Combined Filtering / 组合过滤
```bash
# Include fast, exclude errors
# 包含快速，排除错误
python scripts/run_regression_suite.py --tags fast --exclude-tags error
```

### Baseline Management / 基线管理

#### Save Baseline / 保存基线
```bash
# Save current results as baseline
# 将当前结果保存为基线
python scripts/run_regression_suite.py \
  --tags fast \
  --save-baseline v1.0

# Baseline saved to: tests/regression/baselines/v1.0.json
```

#### Compare to Baseline / 与基线比较
```bash
# Compare current run to baseline
# 将当前运行与基线比较
python scripts/run_regression_suite.py \
  --tags fast \
  --baseline baselines/v1.0.json
```

#### Fail on Regression / 回归时失败
```bash
# Exit with code 1 if performance regression detected
# 如果检测到性能回归，以代码1退出
python scripts/run_regression_suite.py \
  --baseline baselines/v1.0.json \
  --fail-on-regression
```

#### Baseline Comparison Output / 基线比较输出
```
======================================================================
BASELINE COMPARISON / 基线对比
======================================================================
Baseline: v1.0 (2025-10-10 12:00:00)
Tests compared: 13

Performance Summary:
  Faster: 3 tests (23.1%)
  Similar: 9 tests (69.2%)
  Slower: 1 tests (7.7%)

Average duration change: -5.2%

REGRESSIONS DETECTED / 检测到回归:

⚠ https://example.com/slow
  Duration increased: 2.5s → 5.2s (+108%)
  Content size changed: 1024 → 2048 bytes (+100%)
```

### Report Generation / 报告生成

#### Text Report (Default) / 文本报告（默认）
```bash
# Print to terminal
# 打印到终端
python scripts/run_regression_suite.py --tags fast
```

#### Markdown Report / Markdown报告
```bash
# Generate markdown report
# 生成markdown报告
python scripts/run_regression_suite.py \
  --report markdown \
  --output report.md
```

**Example Markdown Output:**

```markdown
# Regression Test Report

**Date**: 2025-10-10 14:30:00
**Suite**: url_suite.txt
**Tests**: 13 passed, 0 failed, 0 errors

## Summary

- Total Tests: 13
- Success Rate: 100.0%
- Total Duration: 45.2s
- Total Data: 2.3 MB

## Test Results

| URL | Status | Duration | Size |
|-----|--------|----------|------|
| https://httpbin.org/html | ✓ PASSED | 1.2s | 12 KB |
...
```

#### JSON Report / JSON报告
```bash
# Generate JSON report for programmatic processing
# 生成JSON报告以便程序处理
python scripts/run_regression_suite.py \
  --report json \
  --output report.json
```

**Example JSON Output:**

```json
{
  "timestamp": "2025-10-10T14:30:00",
  "suite_file": "url_suite.txt",
  "summary": {
    "total": 13,
    "passed": 13,
    "failed": 0,
    "errors": 0,
    "success_rate": 100.0,
    "total_duration": 45.2,
    "total_data_bytes": 2345678
  },
  "results": [
    {
      "url": "https://httpbin.org/html",
      "status": "PASSED",
      "duration": 1.2,
      "content_size": 12345
    }
  ]
}
```

### Advanced Filtering / 高级过滤

#### Filter by Strategy / 按策略过滤
```bash
# Only show urllib tests
# 仅显示urllib测试
python scripts/run_regression_suite.py --strategy urllib

# Only show selenium tests
# 仅显示selenium测试
python scripts/run_regression_suite.py --strategy selenium
```

#### Filter by Duration / 按持续时间过滤
```bash
# Only show tests taking > 5 seconds
# 仅显示耗时>5秒的测试
python scripts/run_regression_suite.py --min-duration 5
```

#### Strict Mode / 严格模式
```bash
# Exit 1 on any warning
# 任何警告时退出1
python scripts/run_regression_suite.py --strict
```

## Integration / 集成

### CI/CD Integration / CI/CD 集成

#### GitHub Actions

See [examples/github-actions.yml](examples/github-actions.yml)

```yaml
name: Regression Tests

on: [push, pull_request]

jobs:
  regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run regression tests
        run: |
          python scripts/run_regression_suite.py \
            --tags fast \
            --baseline baselines/main.json \
            --fail-on-regression \
            --report markdown \
            --output regression-report.md

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: regression-report
          path: regression-report.md
```

#### GitLab CI

See [examples/gitlab-ci.yml](examples/gitlab-ci.yml)

```yaml
regression_tests:
  stage: test
  script:
    - pip install -r requirements.txt
    - python scripts/run_regression_suite.py --tags fast --report json --output report.json
  artifacts:
    reports:
      junit: report.json
    when: always
```

#### Jenkins

See [examples/Jenkinsfile](examples/Jenkinsfile)

```groovy
pipeline {
    agent any
    stages {
        stage('Regression Tests') {
            steps {
                sh 'python scripts/run_regression_suite.py --tags fast'
            }
        }
    }
}
```

### Docker Integration / Docker 集成

See [examples/Dockerfile.regression](examples/Dockerfile.regression)

```bash
# Build regression test image
# 构建回归测试镜像
docker build -f examples/Dockerfile.regression -t webfetcher-regression .

# Run tests in container
# 在容器中运行测试
docker run --rm webfetcher-regression --tags fast

# With volume for baselines
# 使用卷存储基线
docker run --rm \
  -v $(pwd)/baselines:/app/baselines \
  webfetcher-regression \
  --baseline baselines/v1.0.json
```

## Advanced Usage / 高级用法

### Programmatic Usage / 编程使用

```python
from pathlib import Path
from tests.regression.url_suite_parser import parse_url_suite, filter_by_tags
from tests.regression.regression_runner import RegressionRunner
from tests.regression.baseline_manager import BaselineManager
from tests.regression.report_generator import ReportGenerator

# Parse test suite
tests = parse_url_suite(Path('tests/url_suite.txt'))
filtered = filter_by_tags(tests, include_tags={'fast'})

# Run tests
runner = RegressionRunner(timeout=30)
results = runner.run_suite(filtered)

# Save baseline
baseline_mgr = BaselineManager()
baseline_mgr.save_baseline('v1.0', results)

# Generate report
report_gen = ReportGenerator(results, 'url_suite.txt')
markdown = report_gen.generate_markdown()
print(markdown)
```

### Custom Report Format / 自定义报告格式

See [examples/custom_report_template.py](examples/custom_report_template.py)

```python
from tests.regression.report_generator import ReportGenerator

class CustomReporter(ReportGenerator):
    def generate_custom(self):
        """Generate custom format report"""
        # Your custom logic here
        pass
```

### Slack Notifications / Slack 通知

See [examples/slack_notifier.py](examples/slack_notifier.py)

```python
# Send regression results to Slack
python examples/slack_notifier.py report.json
```

## Troubleshooting / 故障排除

### Common Issues / 常见问题

#### "No tests match the specified filters"
**Problem**: Tag filters exclude all tests
**Solution**: Check tag spelling and combination

```bash
# List available tags
grep -h "tags:" tests/url_suite.txt | sort -u

# Run without filters first
python scripts/run_regression_suite.py
```

#### Tests Timing Out / 测试超时
**Problem**: Tests exceed timeout limit
**Solution**: Increase timeout or exclude slow tests

```bash
# Increase timeout to 60 seconds
python scripts/run_regression_suite.py --timeout 60

# Or exclude slow tests
python scripts/run_regression_suite.py --exclude-tags slow
```

#### Import Errors / 导入错误
**Problem**: Module import failures
**Solution**: Run from project root directory

```bash
# Correct: from project root
cd /path/to/Web_Fetcher
python scripts/run_regression_suite.py

# Wrong: from scripts directory
cd scripts
python run_regression_suite.py  # Will fail
```

#### Connection Errors / 连接错误
**Problem**: Network failures, connection resets
**Solution**:
- Check network connection
- Retry with verbose logging
- Some URLs may be intermittently unavailable

```bash
# Debug with verbose logging
python scripts/run_regression_suite.py --url <failed_url> --verbose
```

#### Baseline Not Found / 基线未找到
**Problem**: Baseline file doesn't exist
**Solution**: Create baseline first

```bash
# Save baseline before comparing
python scripts/run_regression_suite.py --save-baseline v1.0
python scripts/run_regression_suite.py --baseline baselines/v1.0.json
```

### FAQ / 常见问题解答

**Q: How do I add new test URLs?**
A: Edit `tests/url_suite.txt` following the template format:
```
url | description | expected_strategy | tags
```

**Q: What's the difference between `--tags` and `--strategy`?**
A: `--tags` filters which tests to run. `--strategy` filters results by strategy used after running.

**Q: Can I run tests in parallel?**
A: Not yet. Parallel execution is planned for a future release.

**Q: How do I create a custom baseline directory?**
A: Baselines are saved to `tests/regression/baselines/` by default. You can specify full paths when loading.

**Q: What happens when a test fails?**
A: Failed tests are reported with error details. Exit code is 1 if any tests fail.

## API Documentation / API 文档

### URLTest

```python
@dataclass
class URLTest:
    url: str                    # Target URL
    description: str            # Brief description
    expected_strategy: str      # urllib/selenium/manual
    tags: Set[str]             # Tags for filtering
    line_number: int           # Source line number
```

### TestResult

```python
@dataclass
class TestResult:
    test: URLTest              # Original test case
    status: TestStatus         # PASSED/FAILED/SKIPPED/ERROR
    duration: float            # Execution time (seconds)
    content_size: int          # Fetched content size (bytes)
    error_message: str         # Error message if failed
    fetch_metrics: FetchMetrics # Webfetcher metrics
    strategy_used: str         # Actual strategy used

    @property
    def passed(self) -> bool:
        """Check if test passed"""
        return self.status == TestStatus.PASSED
```

### Baseline

```python
@dataclass
class Baseline:
    name: str                  # Baseline name
    timestamp: str             # ISO format timestamp
    suite_file: str            # Source suite file
    results: List[TestResult]  # Test results
    metadata: Dict[str, Any]   # Additional metadata
```

### API Examples / API 示例

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for detailed API documentation.

## Exit Codes / 退出代码

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success / 成功 | All tests passed |
| 1 | Failure / 失败 | One or more tests failed |
| 2 | Error / 错误 | Invalid arguments or suite load error |
| 130 | Interrupted / 中断 | User interrupted (Ctrl+C) |

## File Structure / 文件结构

```
tests/regression/
├── README.md                      # This file / 本文件
├── QUICK_START.md                 # Quick start guide / 快速入门指南
├── DEVELOPER_GUIDE.md             # Developer documentation / 开发者文档
├── QUICK_REFERENCE.md             # One-page cheat sheet / 单页速查表
├── MIGRATION.md                   # Migration guide / 迁移指南
├── CHANGELOG.md                   # Version history / 版本历史
├── PERFORMANCE.md                 # Benchmarks / 性能基准
│
├── __init__.py                    # Module initialization / 模块初始化
├── url_suite_parser.py            # Parse URL suite / 解析URL套件
├── regression_runner.py           # Execute tests / 执行测试
├── baseline_manager.py            # Baseline management / 基线管理
├── report_generator.py            # Report generation / 报告生成
│
├── baselines/                     # Saved baselines / 保存的基线
│   ├── v1.0.json
│   └── main.json
│
└── examples/                      # Integration examples / 集成示例
    ├── github-actions.yml         # GitHub Actions
    ├── gitlab-ci.yml              # GitLab CI
    ├── Jenkinsfile                # Jenkins
    ├── Dockerfile.regression      # Docker
    ├── docker-compose.regression.yml
    ├── daily_regression.sh        # Daily check
    ├── pre_release_check.sh       # Pre-release
    ├── compare_versions.sh        # Version comparison
    ├── custom_report_template.py  # Custom reporter
    └── slack_notifier.py          # Slack integration
```

## Contributing / 贡献

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for:
- Architecture overview
- Adding new features
- Testing guidelines
- Code style
- PR process

## Additional Resources / 额外资源

- **Quick Start**: [QUICK_START.md](QUICK_START.md) - 3-minute guide
- **Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - One-page cheat sheet
- **Migration Guide**: [MIGRATION.md](MIGRATION.md) - Upgrade instructions
- **Developer Guide**: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Contributor docs
- **Changelog**: [CHANGELOG.md](CHANGELOG.md) - Version history
- **Performance**: [PERFORMANCE.md](PERFORMANCE.md) - Benchmarks

## License / 许可证

This project is part of Web Fetcher and shares the same license.

本项目是Web Fetcher的一部分，使用相同的许可证。

---

**Version**: 1.0.0
**Last Updated**: 2025-10-10
**Status**: ✅ Production Ready / 生产就绪

For questions or issues, please open a GitHub issue.
如有问题，请在GitHub上开issue。
