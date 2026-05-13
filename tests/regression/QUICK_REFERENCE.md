# Regression Test Quick Reference
# 回归测试快速参考

**One-page cheat sheet for common operations**
**常用操作的单页速查表**

---

## Common Commands / 常用命令

```bash
# Run all tests (exclude manual)
python scripts/run_regression_suite.py

# Run fast tests only
python scripts/run_regression_suite.py --tags fast

# Run with baseline comparison
python scripts/run_regression_suite.py --baseline baselines/v1.0.json

# Save new baseline
python scripts/run_regression_suite.py --save-baseline v1.0

# Generate markdown report
python scripts/run_regression_suite.py --report markdown --output report.md

# Test single URL
python scripts/run_regression_suite.py --url https://example.com

# Verbose logging
python scripts/run_regression_suite.py --verbose
```

---

## Tag Filters / 标签过滤

```bash
# Include specific tags
--tags <tags>           # Include tags (comma-separated OR logic)
--tags fast             # Only fast tests
--tags wechat,xhs       # WeChat OR XiaoHongShu tests

# Exclude specific tags
--exclude-tags <tags>   # Exclude tags (comma-separated)
--exclude-tags slow     # Exclude slow tests
--exclude-tags manual,error  # Exclude manual and error tests

# Combined filtering
--tags fast --exclude-tags error  # Fast tests but not error tests
```

### Available Tags / 可用标签

| Tag | Tests | Description |
|-----|-------|-------------|
| `fast` | ~13 | Fast tests (<5s) ⚡ |
| `slow` | ~3 | Slow tests (>5s) 🐌 |
| `basic` | ~6 | Basic static sites |
| `reference` | ~6 | HTTPBin test URLs |
| `wechat` | ~3 | WeChat articles |
| `xhs` | ~3 | XiaoHongShu content |
| `news` | ~2 | News websites |
| `developer` | ~2 | GitHub, StackOverflow |
| `manual` | ~0 | Manual intervention required |

---

## Baseline Management / 基线管理

```bash
# Save baseline
--save-baseline <name>

# Load and compare
--baseline <file>

# Fail on regression
--fail-on-regression

# Examples:
python scripts/run_regression_suite.py --save-baseline v1.0
python scripts/run_regression_suite.py --baseline baselines/v1.0.json
python scripts/run_regression_suite.py --baseline baselines/v1.0.json --fail-on-regression
```

---

## Report Formats / 报告格式

```bash
# Report formats
--report <format>       # markdown | json | text
--output <file>         # Output file (default: stdout)

# Examples:
--report markdown       # Markdown format
--report json          # JSON format
--report text          # Text format (default)

--report markdown --output report.md
--report json --output report.json
```

---

## Advanced Options / 高级选项

```bash
# Strategy filter (post-run)
--strategy <type>       # urllib | selenium | auto
--strategy urllib       # Only urllib results

# Duration filter
--min-duration <sec>    # Only tests taking > N seconds
--min-duration 5        # Tests taking > 5 seconds

# Strict mode
--strict                # Exit 1 on any warning

# Timeout
--timeout <sec>         # Timeout per URL (default: 30)
--timeout 60            # 60 second timeout

# Custom suite file
--suite-file <path>     # Path to url_suite.txt
```

---

## CI/CD Integration / CI/CD 集成

### GitHub Actions
```yaml
- run: python scripts/run_regression_suite.py --tags fast --baseline baselines/main.json --fail-on-regression
```

### GitLab CI
```yaml
script:
  - python scripts/run_regression_suite.py --tags fast --report json --output report.json
```

### Jenkins
```groovy
sh 'python scripts/run_regression_suite.py --tags fast'
```

---

## Docker / Docker

```bash
# Build
docker build -f tests/regression/examples/Dockerfile.regression -t webfetcher-regression .

# Run
docker run --rm webfetcher-regression --tags fast

# With baseline
docker run --rm -v $(pwd)/baselines:/app/baselines \
  webfetcher-regression --baseline baselines/main.json

# Docker Compose
docker-compose -f tests/regression/examples/docker-compose.regression.yml up
```

---

## Exit Codes / 退出代码

| Code | Meaning |
|------|---------|
| 0 | All tests passed ✓ |
| 1 | Tests failed ✗ |
| 2 | Error/Invalid args 🔧 |
| 130 | User interrupted ⏸️ |

---

## Common Workflows / 常用工作流

### Pre-Commit (~10s)
```bash
python scripts/run_regression_suite.py --tags reference,basic
```

### Pre-Release
```bash
python scripts/run_regression_suite.py \
  --exclude-tags manual,slow \
  --baseline baselines/v1.0.json \
  --fail-on-regression \
  --report markdown \
  --output release-report.md
```

### Daily Regression
```bash
python scripts/run_regression_suite.py \
  --exclude-tags manual \
  --baseline baselines/main.json \
  --report json \
  --output daily-report.json
```

### Platform Testing
```bash
# WeChat
python scripts/run_regression_suite.py --tags wechat --verbose

# XiaoHongShu
python scripts/run_regression_suite.py --tags xhs --verbose
```

---

## Troubleshooting / 故障排除

```bash
# No tests match filters
python scripts/run_regression_suite.py  # Run all first

# Tests timeout
python scripts/run_regression_suite.py --timeout 60  # Increase timeout

# Import errors
cd /path/to/Web_Fetcher  # Run from project root

# Baseline not found
python scripts/run_regression_suite.py --save-baseline v1.0  # Create first

# Debug single URL
python scripts/run_regression_suite.py --url <url> --verbose
```

---

## Quick Tips / 快速提示

1. **Start small**: Use `--tags fast` first
2. **Use verbose**: Add `--verbose` when debugging
3. **Save baselines**: Save before major changes
4. **Check reports**: Review JSON for automation
5. **Tag wisely**: Combine tags for precise selection

---

## File Locations / 文件位置

```
tests/regression/
├── baselines/          # Saved baselines
├── examples/           # Integration examples
├── README.md          # Full documentation
├── QUICK_START.md     # 3-minute guide
└── QUICK_REFERENCE.md # This file
```

---

## Help / 帮助

```bash
# Full help
python scripts/run_regression_suite.py --help

# Docs
tests/regression/README.md           # Complete guide
tests/regression/QUICK_START.md      # Quick start
tests/regression/DEVELOPER_GUIDE.md  # Developer docs
```

---

**Version**: 1.0.0 | **Updated**: 2025-10-10
