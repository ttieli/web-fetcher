# Migration Guide
# 迁移指南

**Upgrading to the Regression Test Harness**
**升级到回归测试工具**

---

## Table of Contents / 目录

1. [Migrating from Manual Testing](#migrating-from-manual-testing--从手动测试迁移)
2. [Upgrading from Phase 2](#upgrading-from-phase-2--从阶段2升级)
3. [Breaking Changes](#breaking-changes--重大变更)
4. [Migration Checklist](#migration-checklist--迁移检查清单)

---

## Migrating from Manual Testing / 从手动测试迁移

### Before: Manual Testing / 之前：手动测试

```bash
# Manually test each URL
python webfetcher.py https://example.com
python webfetcher.py https://mp.weixin.qq.com/...
python webfetcher.py https://www.xiaohongshu.com/...

# Keep manual notes of results
# Track failures manually
```

### After: Automated Regression Testing / 之后：自动回归测试

```bash
# Single command for all tests
python scripts/run_regression_suite.py --tags fast

# Automatic tracking and reporting
# Baseline comparison
# Historical trends
```

### Step 1: Create URL Suite / 创建 URL 套件

Convert your manual test list to `tests/url_suite.txt`:

```text
# Format: url | description | expected_strategy | tags

https://example.com | Example static site | urllib | basic,fast,test
https://mp.weixin.qq.com/... | WeChat article | urllib | wechat,production
```

**Migration Template**:
```python
# Convert from manual list
manual_urls = [
    "https://example1.com",
    "https://example2.com",
]

# To suite format
for url in manual_urls:
    print(f"{url} | Description | urllib | basic,test")
```

### Step 2: Run Initial Test / 运行初始测试

```bash
# Test your converted suite
python scripts/run_regression_suite.py --tags test

# Verify results
# Fix any issues with URL format or tags
```

### Step 3: Create Baseline / 创建基线

```bash
# Save current state as baseline
python scripts/run_regression_suite.py --save-baseline v1.0

# This becomes your reference point
```

### Step 4: Integrate into Workflow / 集成到工作流

```bash
# Pre-commit: Quick check
python scripts/run_regression_suite.py --tags fast

# Daily: Full regression
python scripts/run_regression_suite.py \
  --baseline baselines/v1.0.json \
  --report markdown \
  --output daily-report.md

# Pre-release: Comprehensive
./tests/regression/examples/pre_release_check.sh v2.0
```

---

## Upgrading from Phase 2 / 从阶段2升级

### Phase 2 → Phase 3 Changes / 阶段2到阶段3的变更

#### New CLI Options / 新的 CLI 选项

```bash
# Phase 2
python scripts/run_regression_suite.py --tags fast

# Phase 3 - New options added
python scripts/run_regression_suite.py \
  --tags fast \
  --save-baseline v1.0          # NEW: Save baseline
  --baseline baselines/v1.0.json  # NEW: Compare baseline
  --fail-on-regression           # NEW: Exit 1 on regression
  --report markdown              # NEW: Report formats
  --output report.md             # NEW: Output file
  --strategy urllib              # NEW: Strategy filter
  --min-duration 5               # NEW: Duration filter
  --strict                       # NEW: Strict mode
```

#### Migration Steps / 迁移步骤

1. **Update Command**: Add baseline management
```bash
# Before
python scripts/run_regression_suite.py --tags fast

# After
python scripts/run_regression_suite.py \
  --tags fast \
  --save-baseline main
```

2. **Save Initial Baseline**: Create reference point
```bash
python scripts/run_regression_suite.py \
  --exclude-tags manual,slow \
  --save-baseline v1.0
```

3. **Update CI/CD**: Add baseline comparison
```yaml
# Before
- run: python scripts/run_regression_suite.py --tags fast

# After
- run: |
    python scripts/run_regression_suite.py \
      --tags fast \
      --baseline baselines/main.json \
      --fail-on-regression
```

4. **Use New Reports**: Generate formatted reports
```bash
# Markdown for humans
python scripts/run_regression_suite.py --report markdown --output report.md

# JSON for automation
python scripts/run_regression_suite.py --report json --output report.json
```

---

## Breaking Changes / 重大变更

### None! / 无！

**Good news**: All Phase 2 commands continue to work in Phase 3+.

**好消息**：所有阶段2命令在阶段3+中继续工作。

The new features are **additive only**:
- Old scripts continue to work
- New options are optional
- Default behavior unchanged

新功能仅为**增量添加**：
- 旧脚本继续工作
- 新选项是可选的
- 默认行为未更改

### Deprecated Features / 已弃用功能

None currently. All features remain supported.

当前没有。所有功能仍然受支持。

---

## Migration Checklist / 迁移检查清单

### For New Users / 新用户

- [ ] Create or verify `tests/url_suite.txt` exists
- [ ] Run first test: `python scripts/run_regression_suite.py --tags fast`
- [ ] Save initial baseline: `--save-baseline v1.0`
- [ ] Set up CI/CD integration (optional)
- [ ] Configure daily regression (optional)

### For Phase 2 Users / 阶段2用户

- [ ] Read Phase 3 documentation
- [ ] Save current state as baseline
- [ ] Update CI/CD scripts to use baselines
- [ ] Try new report formats
- [ ] Experiment with new filtering options

### For CI/CD Integration / CI/CD 集成

- [ ] Update workflow files with new options
- [ ] Add baseline comparison
- [ ] Enable `--fail-on-regression`
- [ ] Set up artifact upload for reports
- [ ] Configure scheduled runs

---

## Common Migration Scenarios / 常见迁移场景

### Scenario 1: From Manual Testing / 场景1：从手动测试

**Problem**: Currently testing URLs manually, want automation.

**Solution**:
1. Create URL suite file
2. Run initial test
3. Save baseline
4. Automate with CI/CD

### Scenario 2: Adding Baseline Comparison / 场景2：添加基线比较

**Problem**: Running tests but no historical comparison.

**Solution**:
```bash
# 1. Save current state
python scripts/run_regression_suite.py --save-baseline current

# 2. Run future tests with comparison
python scripts/run_regression_suite.py --baseline baselines/current.json
```

### Scenario 3: CI/CD Integration / 场景3：CI/CD 集成

**Problem**: Need to integrate into existing pipeline.

**Solution**:
1. Copy example workflow from `examples/`
2. Customize tags and options
3. Add to `.github/workflows/` or `.gitlab-ci.yml`
4. Configure baseline storage

### Scenario 4: Custom Reports / 场景4：自定义报告

**Problem**: Need specific report format.

**Solution**:
1. Use existing formats: `--report markdown|json|text`
2. Or extend `ReportGenerator` class
3. See `examples/custom_report_template.py`

---

## Example Migration Scripts / 示例迁移脚本

### Convert Manual Test List / 转换手动测试列表

```python
#!/usr/bin/env python3
"""Convert manual test list to url_suite.txt format"""

manual_tests = [
    ("https://example.com", "Example site", "basic,test"),
    ("https://httpbin.org/html", "HTTPBin HTML", "reference,fast"),
]

with open('tests/url_suite.txt', 'a') as f:
    f.write("\n# Migrated tests\n")
    for url, desc, tags in manual_tests:
        f.write(f"{url} | {desc} | urllib | {tags}\n")

print("✓ Migration complete")
```

### Update CI/CD Config / 更新 CI/CD 配置

```bash
#!/bin/bash
# Update GitHub Actions workflow

cat << 'EOF' >> .github/workflows/regression.yml
name: Regression Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: |
          python scripts/run_regression_suite.py \
            --tags fast \
            --baseline baselines/main.json \
            --fail-on-regression
EOF
```

---

## Rollback Plan / 回滚计划

If you encounter issues with new features:

如果您在新功能中遇到问题：

### Option 1: Use Phase 2 Commands / 选项1：使用阶段2命令

```bash
# Simple Phase 2 command (still works)
python scripts/run_regression_suite.py --tags fast

# Avoid new options if problematic
```

### Option 2: Temporarily Disable Features / 选项2：临时禁用功能

```bash
# Skip baseline comparison temporarily
python scripts/run_regression_suite.py --tags fast
# (Don't use --baseline flag)

# Use text output instead of formatted reports
python scripts/run_regression_suite.py --tags fast
# (Don't use --report flag)
```

### Option 3: Report Issues / 选项3：报告问题

Open a GitHub issue with:
- Error message
- Command used
- Expected vs actual behavior
- Environment details

---

## Support / 支持

- **Documentation**: `tests/regression/README.md`
- **Examples**: `tests/regression/examples/`
- **Issues**: GitHub Issues
- **Questions**: GitHub Discussions

---

## Summary / 总结

### Key Points / 要点

✓ **No breaking changes** - All Phase 2 commands still work
✓ **Gradual adoption** - Use new features at your pace
✓ **Backward compatible** - Old scripts continue to function
✓ **Well documented** - Comprehensive guides available

✓ **无重大变更** - 所有阶段2命令仍然有效
✓ **逐步采用** - 按自己的节奏使用新功能
✓ **向后兼容** - 旧脚本继续运行
✓ **文档完善** - 提供全面的指南

---

**Version**: 1.0.0
**Last Updated**: 2025-10-10
