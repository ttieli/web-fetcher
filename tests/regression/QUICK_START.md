# Regression Test Harness - Quick Start Guide
# 回归测试工具 - 快速入门指南

## Installation / 安装

No additional dependencies required! Uses existing webfetcher infrastructure.
无需额外依赖！使用现有的webfetcher基础设施。

## Basic Usage / 基本用法

### Run All Tests (Excluding Manual)
```bash
python scripts/run_regression_suite.py
```

### Run Fast Tests Only
```bash
python scripts/run_regression_suite.py --tags fast
```

### Run Specific Platform Tests
```bash
# WeChat tests
python scripts/run_regression_suite.py --tags wechat

# XiaoHongShu tests
python scripts/run_regression_suite.py --tags xhs

# Both
python scripts/run_regression_suite.py --tags wechat,xhs
```

### Exclude Slow Tests
```bash
python scripts/run_regression_suite.py --exclude-tags slow
```

### Test Single URL
```bash
python scripts/run_regression_suite.py --url https://example.com
```

### Verbose Logging
```bash
python scripts/run_regression_suite.py --tags basic --verbose
```

## Common Workflows / 常用工作流

### Pre-Commit Testing
快速测试核心功能（~10秒）：
```bash
python scripts/run_regression_suite.py --tags reference,basic
```

### Full Regression (Before Release)
完整回归测试（~90秒）：
```bash
python scripts/run_regression_suite.py --exclude-tags slow,manual
```

### Platform-Specific Testing
平台特定测试：
```bash
# Test WeChat parser changes
python scripts/run_regression_suite.py --tags wechat --verbose

# Test XiaoHongShu changes
python scripts/run_regression_suite.py --tags xhs --verbose
```

### Debug Failures
调试失败：
```bash
# Run failed test with verbose logging
python scripts/run_regression_suite.py --url <failed_url> --verbose
```

## Output Examples / 输出示例

### Successful Run
```
Loaded 16 tests from url_suite.txt
Include tags: fast
Running 13 tests...

======================================================================
REGRESSION TEST SUMMARY / 回归测试摘要
======================================================================
Total Tests:    13
Passed:         13 ✓
Failed:         0 ✗
Errors:         0 ⚠
Skipped:        0 ⊘
Total Duration: 45.23s
Total Data:     2,345,678 bytes (2291.7 KB)

======================================================================
Success Rate: 100.0%
======================================================================
```

### With Failures
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

======================================================================
Success Rate: 85.7%
======================================================================
```

## Available Tags / 可用标签

| Tag | Count | Description |
|-----|-------|-------------|
| **fast** | 13 | Fast-loading tests (<5s) |
| **slow** | 3 | Slow tests (>5s) |
| **basic** | 6 | Basic static sites |
| **reference** | 6 | HTTPBin reference tests |
| **wechat** | 3 | WeChat articles |
| **xhs** | 3 | XiaoHongShu content |
| **news** | 2 | News websites |
| **developer** | 2 | GitHub, StackOverflow |
| **error** | 1 | Expected error cases |
| **redirect** | 2 | Redirect testing |
| **timeout** | 1 | Timeout testing |
| **manual** | 0 | Manual intervention required |
| **js-required** | 2 | JavaScript rendering needed |
| **production** | 2 | Production URLs |
| **test** | 3 | Test/sample URLs |
| **api** | 1 | API endpoints |
| **international** | 1 | International sites |

## Exit Codes / 退出代码

| Code | Meaning | Action |
|------|---------|--------|
| 0 | All passed | ✅ Continue |
| 1 | Tests failed | ❌ Fix issues |
| 2 | Error/Invalid args | 🔧 Check command |
| 130 | User interrupted | ⏸️ Stopped by Ctrl+C |

## Tips / 提示

1. **Start Small**: Test with `--tags fast` first
   从小处开始：先用 `--tags fast` 测试

2. **Use Verbose**: Add `--verbose` when debugging
   使用详细模式：调试时添加 `--verbose`

3. **Combine Tags**: Use multiple tags: `--tags wechat,xhs`
   组合标签：使用多个标签 `--tags wechat,xhs`

4. **Exclude Problematic**: Skip slow/failing tests: `--exclude-tags slow,error`
   排除问题：跳过慢速/失败测试 `--exclude-tags slow,error`

5. **Test Changes**: Use `--url` to test specific URLs before adding to suite
   测试变更：在添加到套件前用 `--url` 测试特定 URL

## Troubleshooting / 故障排除

### "No tests match the specified filters"
检查标签拼写和组合是否正确

### Tests timing out
增加超时时间：`--timeout 60`

### Import errors
确保从项目根目录运行

### Connection errors
检查网络连接，某些 URL 可能间歇性失败

## Help / 帮助

Full help documentation:
```bash
python scripts/run_regression_suite.py --help
```

## Files / 文件

- **url_suite.txt**: Test URL definitions
- **url_suite_parser.py**: Parse and filter logic
- **regression_runner.py**: Test execution engine
- **run_regression_suite.py**: CLI entry point

## Next: Phase 3 / 下一步：阶段3

Phase 3 will add:
- Baseline capture and comparison
- JSON/HTML reporting
- Performance tracking
- CI/CD integration

---

**Quick Start Complete!** / **快速入门完成！**

For detailed documentation, see `README.md`
详细文档请参见 `README.md`
