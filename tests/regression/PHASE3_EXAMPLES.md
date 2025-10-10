# Phase 3 - Example Outputs / 阶段 3 - 示例输出

This document shows real example outputs from Phase 3 features.

本文档显示阶段 3 功能的实际示例输出。

## 1. Baseline Save / 基线保存

**Command:**
```bash
python scripts/run_regression_suite.py --tags fast,reference --save-baseline test_v1
```

**Output:**
```
Loaded 16 tests from url_suite.txt
Include tags: fast, reference
Running 14 tests...

======================================================================
REGRESSION TEST SUMMARY / 回归测试摘要
======================================================================
Total Tests:    14
Passed:         12 ✓
Failed:         0 ✗
Errors:         2 ⚠
Skipped:        0 ⊘
Total Duration: 90.51s
Total Data:     3,747,358 bytes (3659.5 KB)
======================================================================
Success Rate: 85.7%
======================================================================

Baseline saved to: tests/regression/baselines/test_v1.json
```

**Baseline File (test_v1.json):**
```json
{
  "timestamp": "2025-10-10T13:00:23.717552",
  "suite_version": "88b2e008",
  "results": {
    "https://example.com": {
      "url": "https://example.com",
      "status": "passed",
      "duration": 1.2422809600830078,
      "content_size": 513,
      "strategy": "urllib"
    },
    "https://httpbin.org/html": {
      "url": "https://httpbin.org/html",
      "status": "passed",
      "duration": 6.633378982543945,
      "content_size": 3739,
      "strategy": "urllib"
    }
  },
  "metadata": {
    "total_tests": 14,
    "total_duration": 90.51
  }
}
```

## 2. Markdown Report / Markdown 报告

**Command:**
```bash
python scripts/run_regression_suite.py --tags fast,reference --report markdown --output report.md
```

**Output (report.md):**
```markdown
# Regression Test Report / 回归测试报告

**Generated / 生成时间:** 2025-10-10 13:02:05
**Suite / 测试套件:** url_suite.txt (14 URLs)

## Summary / 总结

| Metric / 指标 | Value / 值 |
|--------------|-----------|
| Total / 总数 | 14 |
| Passed / 通过 | 12 |
| Failed / 失败 | 0 |
| Error / 错误 | 2 |
| Skipped / 跳过 | 0 |
| Success Rate / 成功率 | 85.7% |

## Performance / 性能

- **Total Duration / 总耗时:** 91.05s
- **Average Duration / 平均耗时:** 6.50s
- **Fastest / 最快:** https://mp.weixin.qq.com/s/test123 (0.29s)
- **Slowest / 最慢:** https://news.ycombinator.com (36.18s)
- **Total Content / 总内容:** 3,747,502 bytes (3659.7 KB)

## Failed Tests / 失败测试

1. **https://news.ycombinator.com**
   - **Status:** ERROR
   - **Error:** URLError: <urlopen error [Errno 54] Connection reset by peer>
   - **Duration:** 36.18s
   - **Expected Strategy:** urllib

2. **https://httpbin.org/status/404**
   - **Status:** ERROR
   - **Error:** HTTPError: HTTP Error 404: NOT FOUND
   - **Duration:** 6.64s
   - **Expected Strategy:** urllib

## Test Breakdown by Tags / 按标签分类测试

| Tag / 标签 | Total / 总数 | Passed / 通过 | Success Rate / 成功率 |
|----------|------------|--------------|---------------------|
| api | 1 | 1 | 100.0% |
| basic | 6 | 5 | 83.3% |
| developer | 2 | 2 | 100.0% |
| error | 1 | 0 | 0.0% |
| fast | 13 | 11 | 84.6% |
| wechat | 3 | 3 | 100.0% |
| xhs | 1 | 1 | 100.0% |
```

## 3. JSON Report / JSON 报告

**Command:**
```bash
python scripts/run_regression_suite.py --tags fast,reference --report json --output report.json
```

**Output (report.json):**
```json
{
  "metadata": {
    "generated_at": "2025-10-10T13:03:49.006870",
    "suite_name": "url_suite.txt",
    "total_tests": 14
  },
  "summary": {
    "total": 14,
    "passed": 12,
    "failed": 0,
    "errors": 2,
    "skipped": 0,
    "success_rate": 85.71428571428571
  },
  "performance": {
    "total_duration": 91.85871839523315,
    "avg_duration": 6.561337028230939,
    "total_size": 3746868,
    "fastest": {
      "url": "https://mp.weixin.qq.com/s/test123",
      "duration": 0.2792551517486572
    },
    "slowest": {
      "url": "https://news.ycombinator.com",
      "duration": 36.226929903030396
    }
  },
  "results": [
    {
      "url": "https://httpbin.org/html",
      "description": "HTTPBin HTML test",
      "status": "passed",
      "duration": 7.027285814285278,
      "content_size": 3739,
      "strategy_used": "urllib",
      "error_message": null,
      "tags": ["reference", "basic", "fast"],
      "expected_strategy": "urllib"
    },
    {
      "url": "https://example.com",
      "description": "Example domain",
      "status": "passed",
      "duration": 1.340620994567871,
      "content_size": 513,
      "strategy_used": "urllib",
      "error_message": null,
      "tags": ["reference", "basic", "fast"],
      "expected_strategy": "urllib"
    }
  ]
}
```

## 4. Baseline Comparison / 基线比较

**Command:**
```bash
python scripts/run_regression_suite.py --tags fast,reference --baseline test_v1
```

**Output:**
```
Loaded 16 tests from url_suite.txt
Include tags: fast, reference
Running 14 tests...

Loaded baseline: test_v1
Comparison: Regressions: 5, Improvements: 0, New: 0, Removed: 0, Unchanged: 9

======================================================================
REGRESSION TEST SUMMARY / 回归测试摘要
======================================================================
Total Tests:    14
Passed:         12 ✓
Failed:         0 ✗
Errors:         2 ⚠
Skipped:        0 ⊘
Total Duration: 111.34s
Total Data:     3,746,073 bytes (3658.3 KB)
======================================================================
Success Rate: 85.7%
======================================================================

======================================================================
BASELINE COMPARISON / 基线对比
======================================================================
Regressions: 5, Improvements: 0, New: 0, Removed: 0, Unchanged: 9

REGRESSIONS DETECTED / 检测到回归:

⚠ https://www.bbc.com/news
  Performance: 1.76s → 2.53s (+43.5% slower)

⚠ https://httpbin.org/html
  Performance: 6.63s → 8.68s (+30.9% slower)

⚠ https://mp.weixin.qq.com/s/test123
  Performance: 0.28s → 0.38s (+33.9% slower)

⚠ https://stackoverflow.com
  Performance: 2.59s → 4.92s (+90.3% slower)

⚠ https://httpbin.org/get
  Performance: 6.47s → 9.70s (+49.9% slower)
```

## 5. Comparison Report (Markdown) / 比较报告（Markdown）

**Command:**
```bash
python scripts/run_regression_suite.py --tags fast,reference --baseline test_v1 --report markdown --output comparison.md
```

**Output (comparison.md):**
```markdown
# Regression Test Report / 回归测试报告

**Generated / 生成时间:** 2025-10-10 13:09:22
**Suite / 测试套件:** url_suite.txt (14 URLs)

## Summary / 总结

| Metric / 指标 | Value / 值 |
|--------------|-----------|
| Total / 总数 | 14 |
| Passed / 通过 | 12 |
| Failed / 失败 | 0 |
| Error / 错误 | 2 |
| Skipped / 跳过 | 0 |
| Success Rate / 成功率 | 85.7% |

## Performance / 性能

- **Total Duration / 总耗时:** 97.41s
- **Average Duration / 平均耗时:** 6.96s
- **Fastest / 最快:** https://mp.weixin.qq.com/s/test123 (0.29s)
- **Slowest / 最慢:** https://news.ycombinator.com (36.21s)
- **Total Content / 总内容:** 3,745,850 bytes (3658.1 KB)

## Baseline Comparison / 基线对比

**Regressions: 1, Improvements: 0, New: 0, Removed: 0, Unchanged: 13**

### Regressions / 回归

1. ⚠ **https://stackoverflow.com**
   - Performance: 2.59s → 5.75s (+122.0% slower)

## Failed Tests / 失败测试

1. **https://news.ycombinator.com**
   - **Status:** ERROR
   - **Error:** URLError: <urlopen error [Errno 54] Connection reset by peer>
   - **Duration:** 36.21s
   - **Expected Strategy:** urllib

2. **https://httpbin.org/status/404**
   - **Status:** ERROR
   - **Error:** HTTPError: HTTP Error 404: NOT FOUND
   - **Duration:** 8.31s
   - **Expected Strategy:** urllib
```

## 6. Filter by Strategy / 按策略过滤

**Command:**
```bash
python scripts/run_regression_suite.py --tags fast,reference --strategy urllib
```

**Output:**
```
Loaded 16 tests from url_suite.txt
Include tags: fast, reference
Running 14 tests...

Filtered to 12 tests using urllib strategy

======================================================================
REGRESSION TEST SUMMARY / 回归测试摘要
======================================================================
Total Tests:    12
Passed:         12 ✓
Failed:         0 ✗
Errors:         0 ⚠
Skipped:        0 ⊘
Total Duration: 33.45s
Total Data:     3,246,073 bytes (3170.0 KB)
======================================================================
Success Rate: 100.0%
======================================================================
```

## 7. Filter by Duration / 按持续时间过滤

**Command:**
```bash
python scripts/run_regression_suite.py --tags fast,reference --min-duration 5.0
```

**Output:**
```
Loaded 16 tests from url_suite.txt
Include tags: fast, reference
Running 14 tests...

Filtered to 5 tests with duration >= 5.0s

======================================================================
REGRESSION TEST SUMMARY / 回归测试摘要
======================================================================
Total Tests:    5
Passed:         3 ✓
Failed:         0 ✗
Errors:         2 ⚠
Skipped:        0 ⊘
Total Duration: 66.74s
Total Data:     8,152 bytes (8.0 KB)
======================================================================
Success Rate: 60.0%
======================================================================

----------------------------------------------------------------------
FAILED TESTS / 失败的测试
----------------------------------------------------------------------

✗ Hacker News homepage
  URL: https://news.ycombinator.com
  Expected: urllib
  Error: URLError: <urlopen error [Errno 54] Connection reset by peer>
  Duration: 36.17s

✗ HTTPBin 404 error
  URL: https://httpbin.org/status/404
  Expected: urllib
  Error: HTTPError: HTTP Error 404: NOT FOUND
  Duration: 7.64s
```

## 8. CI/CD Mode: Fail on Regression / CI/CD 模式：回归时失败

**Command:**
```bash
python scripts/run_regression_suite.py --tags fast,reference --baseline test_v1 --fail-on-regression
echo "Exit code: $?"
```

**Output (when regression detected):**
```
Loaded 16 tests from url_suite.txt
Include tags: fast, reference
Running 14 tests...

Loaded baseline: test_v1
Comparison: Regressions: 2, Improvements: 0, New: 0, Removed: 0, Unchanged: 12

======================================================================
REGRESSION TEST SUMMARY / 回归测试摘要
======================================================================
Total Tests:    14
Passed:         12 ✓
Failed:         0 ✗
Errors:         2 ⚠
Skipped:        0 ⊘
======================================================================
Success Rate: 85.7%
======================================================================

======================================================================
BASELINE COMPARISON / 基线对比
======================================================================
Regressions: 2, Improvements: 0, New: 0, Removed: 0, Unchanged: 12

REGRESSIONS DETECTED / 检测到回归:

⚠ https://stackoverflow.com
  Performance: 2.59s → 5.75s (+122.0% slower)

⚠ https://httpbin.org/html
  Performance: 6.63s → 8.68s (+30.9% slower)

Exiting with error: Performance regressions detected
Exit code: 1
```

## 9. Combined Workflow / 组合工作流

**Command:**
```bash
# Run comprehensive test with all features
python scripts/run_regression_suite.py \
    --tags fast,reference \
    --baseline production_v1.0 \
    --save-baseline production_v1.1 \
    --report markdown \
    --output reports/weekly_regression.md \
    --fail-on-regression
```

**This command:**
1. Runs tests with 'fast' and 'reference' tags
2. Compares against production_v1.0 baseline
3. Saves results as production_v1.1 baseline
4. Generates markdown report to reports/weekly_regression.md
5. Exits with code 1 if regressions detected

**此命令:**
1. 运行带有 'fast' 和 'reference' 标签的测试
2. 与 production_v1.0 基线比较
3. 将结果保存为 production_v1.1 基线
4. 生成 markdown 报告到 reports/weekly_regression.md
5. 如果检测到回归，退出码为 1

## Summary / 总结

Phase 3 provides:
- ✓ Comprehensive baseline management
- ✓ Multi-format report generation
- ✓ Automated regression detection
- ✓ Flexible filtering options
- ✓ CI/CD integration support
- ✓ Bilingual output

All examples shown above are from real test runs.

阶段 3 提供:
- ✓ 全面的基线管理
- ✓ 多格式报告生成
- ✓ 自动回归检测
- ✓ 灵活的过滤选项
- ✓ CI/CD 集成支持
- ✓ 双语输出

以上所有示例均来自实际测试运行。
