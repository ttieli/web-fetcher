# Regression Test Harness - Phase 2 Complete
# 回归测试工具 - 阶段2完成

## Overview / 概述

Phase 2 implements the core regression test runner infrastructure for the Web Fetcher project. This enables automated testing against a curated suite of URLs with various characteristics.

阶段2实现了Web Fetcher项目的核心回归测试运行器基础设施。这使得能够对具有各种特征的精选URL套件进行自动化测试。

## Components / 组件

### 1. URL Suite Parser (`url_suite_parser.py`)

Parses and filters test URLs from `tests/url_suite.txt`.
从 `tests/url_suite.txt` 解析和过滤测试URL。

**Features:**
- Parse pipe-delimited format: `url | description | expected_strategy | tags`
- Tag-based filtering (include/exclude)
- Validation of URL format and fields
- Statistics and grouping utilities

**Usage:**
```python
from tests.regression.url_suite_parser import parse_url_suite, filter_by_tags

tests = parse_url_suite(Path('tests/url_suite.txt'))
fast_tests = filter_by_tags(tests, include_tags={'fast'})
```

### 2. Regression Runner (`regression_runner.py`)

Executes tests using the existing webfetcher infrastructure.
使用现有的webfetcher基础设施执行测试。

**Features:**
- Execute tests with timeout control
- Collect metrics (timing, content size, strategy used)
- Handle errors gracefully
- Support for auto/urllib/selenium strategies
- Skip manual tests by default

**Usage:**
```python
from tests.regression.regression_runner import RegressionRunner

runner = RegressionRunner(timeout=30, skip_manual=True)
results = runner.run_suite(tests)
```

### 3. CLI Entry Point (`scripts/run_regression_suite.py`)

Command-line interface for running regression tests.
用于运行回归测试的命令行界面。

**Features:**
- Full suite execution
- Tag filtering (--tags, --exclude-tags)
- Single URL testing
- Verbose logging
- Colored output with progress
- Summary statistics
- Proper exit codes (0=pass, 1=fail, 2=error)

## Usage Examples / 使用示例

### Run All Tests (Excluding Manual)
### 运行所有测试（不包括手动）

```bash
python scripts/run_regression_suite.py
```

### Run Fast Tests Only
### 仅运行快速测试

```bash
python scripts/run_regression_suite.py --tags fast
```

### Run WeChat and XiaoHongShu Tests
### 运行微信和小红书测试

```bash
python scripts/run_regression_suite.py --tags wechat,xhs
```

### Exclude Slow and Error Tests
### 排除慢速和错误测试

```bash
python scripts/run_regression_suite.py --exclude-tags slow,error
```

### Test Single URL
### 测试单个URL

```bash
python scripts/run_regression_suite.py --url https://example.com
```

### Verbose Mode
### 详细模式

```bash
python scripts/run_regression_suite.py --tags basic --verbose
```

### Include Manual Tests
### 包含手动测试

```bash
python scripts/run_regression_suite.py --include-manual
```

## Output Format / 输出格式

### Summary Statistics / 摘要统计
```
======================================================================
REGRESSION TEST SUMMARY / 回归测试摘要
======================================================================
Total Tests:    14
Passed:         12 ✓
Failed:         0 ✗
Errors:         2 ⚠
Skipped:        0 ⊘
Total Duration: 94.09s
Total Data:     3,749,047 bytes (3661.2 KB)
```

### Failed Test Details / 失败测试详情
```
----------------------------------------------------------------------
FAILED TESTS / 失败的测试
----------------------------------------------------------------------

✗ Test Description
  URL: https://example.com/failed
  Expected: urllib
  Used: selenium
  Error: Timeout after 30s
  Duration: 30.15s
```

## Exit Codes / 退出代码

- **0**: All tests passed / 所有测试通过
- **1**: One or more tests failed / 一个或多个测试失败
- **2**: Error loading suite or invalid arguments / 加载套件错误或无效参数
- **130**: Interrupted by user (Ctrl+C) / 用户中断（Ctrl+C）

## Test Data Structure / 测试数据结构

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
```

## Available Tags / 可用标签

Based on `tests/url_suite.txt`:
基于 `tests/url_suite.txt`：

- **basic**: Basic static websites / 基础静态网站
- **reference**: Reference/test URLs (httpbin) / 参考/测试URL
- **fast**: Fast-loading URLs / 快速加载的URL
- **slow**: Slow-loading URLs / 慢速加载的URL
- **wechat**: WeChat articles / 微信文章
- **xhs**: XiaoHongShu content / 小红书内容
- **news**: News websites / 新闻网站
- **developer**: Developer sites (GitHub, StackOverflow) / 开发者站点
- **error**: Expected error cases / 预期错误情况
- **redirect**: Redirect testing / 重定向测试
- **timeout**: Timeout testing / 超时测试
- **manual**: Requires manual intervention / 需要手动干预
- **js-required**: Requires JavaScript rendering / 需要JavaScript渲染
- **production**: Production URLs / 生产URL
- **test**: Test URLs / 测试URL

## Integration with Webfetcher / 与Webfetcher集成

The regression runner uses the existing webfetcher infrastructure:
回归运行器使用现有的webfetcher基础设施：

1. **fetch_html_with_retry()**: Core fetching function / 核心抓取函数
2. **FetchMetrics**: Performance and method tracking / 性能和方法跟踪
3. **User Agent Management**: Site-specific UA handling / 站点特定的UA处理
4. **Strategy Selection**: Auto/urllib/selenium routing / 自动/urllib/selenium路由

## Testing the Implementation / 测试实现

### Test URL Suite Parser
### 测试URL套件解析器

```bash
python tests/regression/url_suite_parser.py
```

Expected output:
```
✓ Successfully parsed 16 tests

Strategy breakdown:
  selenium: 2
  urllib: 14

Available tags (16):
  api: 1 tests
  basic: 6 tests
  ...
```

### Test Regression Runner
### 测试回归运行器

```bash
python tests/regression/regression_runner.py
```

This runs a quick test with reference URLs.
这将使用参考URL运行快速测试。

### Full Suite Test
### 完整套件测试

```bash
python scripts/run_regression_suite.py --tags basic
```

## Known Issues / 已知问题

1. **Hacker News Connection Resets**: Some URLs may fail intermittently due to network issues
   某些URL可能由于网络问题而间歇性失败

2. **404 Tests**: The HTTPBin 404 test is expected to fail (testing error handling)
   HTTPBin 404测试预期失败（测试错误处理）

3. **Timeout Tests**: Long-running tests may exceed timeout in some environments
   长时间运行的测试在某些环境中可能会超时

## Future Enhancements (Phase 3-4) / 未来增强（阶段3-4）

- JSON/HTML reporting formats
- Baseline comparison (detect regressions)
- Performance tracking over time
- CI/CD integration
- Parallel test execution
- Screenshot capture for visual regression
- Content validation beyond size checks

## Files Created / 创建的文件

```
tests/regression/
├── __init__.py              # Module initialization
├── url_suite_parser.py      # Parse and filter URL suite
├── regression_runner.py     # Execute regression tests
└── README.md               # This file

scripts/
└── run_regression_suite.py  # CLI entry point
```

## Dependencies / 依赖

- Python 3.7+
- webfetcher.py (existing)
- tests/url_suite.txt (Phase 1)
- Optional: Selenium integration (for selenium strategy tests)

## Completion Checklist / 完成检查清单

- [x] URL suite parser with validation
- [x] Tag-based filtering (include/exclude)
- [x] Regression runner with timeout control
- [x] Error handling and graceful failures
- [x] CLI entry point with argparse
- [x] Progress display during execution
- [x] Summary statistics output
- [x] Failed test details
- [x] Proper exit codes
- [x] Bilingual comments (Chinese/English)
- [x] Integration with existing webfetcher
- [x] Manual testing verification

## Phase 2 Complete! / 阶段2完成！

**Date**: 2025-10-10
**Status**: ✓ All objectives met / 所有目标达成
**Next**: Phase 3 - Baseline and Reporting
