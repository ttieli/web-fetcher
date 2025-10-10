# URL Suite Maintenance Guide / URL 套件维护指南

## Overview / 概述

The `url_suite.txt` file contains URLs for regression testing. This guide explains how to maintain and use it effectively.

`url_suite.txt` 文件包含用于回归测试的 URL。本指南说明如何有效地维护和使用它。

## File Format / 文件格式

### Structure / 结构
```
<url> | <description> | <expected_strategy> | <tags>
```

### Fields / 字段

1. **URL** - Full URL to test / 完整测试 URL
   - Must start with http:// or https://
   - Should be accessible publicly or with proper credentials
   - Examples:
     - `https://example.com`
     - `https://mp.weixin.qq.com/s/abc123`
     - `http://xhslink.com/o/9KDQLL0AMFy`

2. **Description** - Brief description / 简短描述
   - Human-readable label
   - Should be unique for easy identification
   - Keep it concise (under 50 characters)
   - Examples:
     - "WeChat article example"
     - "XHS test note"
     - "HTTPBin HTML test"

3. **Expected Strategy** - Expected fetcher / 期望的抓取器
   - `urllib`: Static content, no JavaScript required
     - Simple HTML pages
     - API endpoints
     - Most content sites
   - `selenium`: Requires JavaScript rendering
     - Single-page applications (SPAs)
     - Dynamic content loaded via JavaScript
     - Sites like XiaoHongShu, modern web apps
   - `manual`: Requires manual browser interaction
     - Anti-bot protection (e.g., CEB Bank)
     - CAPTCHA challenges
     - Sites requiring human verification

4. **Tags** - Comma-separated tags / 标签（逗号分隔）
   - Used for filtering in test runs
   - No spaces between tags
   - Common tags:
     - **Speed**: `fast` (<5s), `slow` (>5s)
     - **Type**: `basic`, `production`, `test`, `reference`
     - **Behavior**: `redirect`, `js-required`, `manual`, `anti-bot`
     - **Category**: `wechat`, `xhs`, `cebbank`, `news`, `developer`, `api`
     - **Error**: `error`, `timeout`

## Adding New URLs / 添加新 URL

### Step-by-Step / 步骤

1. **Find a URL to test**
   - Choose representative pages from production
   - Include edge cases and common scenarios
   - Verify the URL is accessible

2. **Determine the expected strategy**
   - Test manually if unsure
   - Check `config/routing.yaml` for routing rules
   - Consider:
     - Does it require JavaScript? → `selenium`
     - Does it have anti-bot protection? → `manual`
     - Otherwise → `urllib`

3. **Add appropriate tags**
   - Include site identifier (e.g., `wechat`, `xhs`)
   - Mark if manual/slow
   - Add functional category (e.g., `news`, `api`)
   - Add test type (e.g., `production`, `test`, `reference`)

4. **Add to the file**
   - Place in appropriate section
   - Follow the format strictly: `url | description | strategy | tags`
   - Use pipe `|` as separator with spaces around it
   - Ensure all 4 fields are present

### Example / 示例

```
https://news.ycombinator.com | Hacker News homepage | urllib | basic,news,fast
https://www.xiaohongshu.com/explore/123 | XHS explore page | selenium | xhs,js-required,slow,production
https://httpbin.org/status/500 | HTTPBin 500 error | urllib | error,fast,reference
```

## Using Tags for Filtering / 使用标签筛选

Tags allow you to run subsets of tests:

```bash
# Run only fast tests
python scripts/run_regression_suite.py --tags fast

# Run only WeChat tests
python scripts/run_regression_suite.py --tags wechat

# Run only production URLs
python scripts/run_regression_suite.py --tags production

# Exclude manual tests
python scripts/run_regression_suite.py --exclude-tags manual

# Multiple tags (AND logic - must have all tags)
python scripts/run_regression_suite.py --tags production,fast

# Combine include and exclude
python scripts/run_regression_suite.py --tags production --exclude-tags slow,manual
```

## Best Practices / 最佳实践

### DO / 应该

- ✅ Keep URLs organized by site/category
- ✅ Use descriptive, unique descriptions
- ✅ Tag manual URLs appropriately (and comment them out by default)
- ✅ Comment out unstable URLs with reason
- ✅ Test new URLs before adding
- ✅ Update tags when routing changes
- ✅ Include a mix of fast and comprehensive tests
- ✅ Document why URLs are commented out
- ✅ Group related URLs together
- ✅ Use reference URLs (like httpbin.org) for baseline testing

### DON'T / 不应该

- ❌ Add duplicate URLs
- ❌ Include broken/404 URLs (unless testing error handling)
- ❌ Use sensitive/private URLs with credentials in URL
- ❌ Forget to tag manual mode URLs
- ❌ Mix different formats
- ❌ Leave URLs uncommented that require manual interaction
- ❌ Use very long descriptions
- ❌ Add URLs without testing them first
- ❌ Remove URLs without documenting why

## File Organization / 文件组织

Organize URLs into logical sections:

```
# Basic Static Sites / 基础静态站点
# -------------------------------------------
(Reference URLs, simple test cases)

# WeChat Articles / 微信文章
# -------------------------------------------
(Production and test WeChat URLs)

# XiaoHongShu / 小红书
# -------------------------------------------
(XHS URLs requiring selenium)

# CEB Bank (Manual Mode) / 光大银行（手动模式）
# -------------------------------------------
(Commented out manual URLs)

# Edge Cases / 边界情况
# -------------------------------------------
(Error cases, timeouts, redirects)
```

## Troubleshooting / 故障排除

### URL Not Being Tested / URL未被测试

**Symptoms**: URL appears in file but not in test results

**Possible Causes**:
- Syntax error: must have exactly 3 pipes `|` separating 4 fields
- Leading/trailing spaces in fields
- URL is commented out (line starts with `#`)
- Tags don't match your filter criteria

**Solutions**:
1. Check the line format: `url | description | strategy | tags`
2. Remove any extra spaces at line start
3. Verify the line isn't commented out
4. Run without tag filters to see if URL is processed

### Unexpected Strategy Used / 使用了意外的策略

**Symptoms**: Test reports different fetcher than expected

**Possible Causes**:
- Routing rules in `config/routing.yaml` override expected strategy
- URL matches a higher-priority routing rule
- Expected strategy field is incorrect

**Solutions**:
1. Review `config/routing.yaml` for matching rules
2. Check routing decision logs in test output
3. Update expected_strategy field to match actual behavior
4. File issue if routing is incorrect

### Parsing Errors / 解析错误

**Symptoms**: Error when loading url_suite.txt

**Possible Causes**:
- Missing pipe separators
- Wrong number of fields
- Special characters in fields

**Solutions**:
1. Ensure exactly 3 pipes per line (4 fields)
2. Check for pipe characters `|` in URL or description (escape if needed)
3. Verify no tabs or unusual characters

### Tests Failing Unexpectedly / 测试意外失败

**Possible Causes**:
- URL content changed
- Site is temporarily down
- Network issues
- Anti-bot protection activated

**Solutions**:
1. Manually visit the URL to verify accessibility
2. Check if site structure changed (update parser templates)
3. Temporarily comment out flaky URLs
4. Add retry logic for transient failures

## Maintenance Schedule / 维护计划

### Weekly / 每周
- Review failed URLs in regression reports
- Remove or comment out broken URLs
- Update descriptions if site content changed

### Monthly / 每月
- Add new production URLs from recent features
- Update tags based on performance observations
- Review and clean up test URLs
- Verify reference URLs still work

### After Routing Changes / 路由更改后
- Update expected_strategy fields
- Test affected URLs manually
- Update tags if behavior changed

### After Site Changes / 站点更改后
- Test URLs for affected sites
- Update parser templates if needed
- Verify expected_strategy is still correct
- Update descriptions if necessary

## Tag Reference / 标签参考

### Speed Tags / 速度标签
- `fast`: Completes in under 5 seconds
- `slow`: Takes 5 seconds or more

### Type Tags / 类型标签
- `basic`: Simple baseline test cases
- `production`: Real production URLs
- `test`: Test/mock URLs
- `reference`: Reference implementations (e.g., httpbin.org)

### Behavior Tags / 行为标签
- `redirect`: URL involves redirects
- `js-required`: Requires JavaScript rendering
- `manual`: Requires manual browser interaction
- `anti-bot`: Has anti-bot protection

### Site Tags / 站点标签
- `wechat`: WeChat articles (mp.weixin.qq.com)
- `xhs`: XiaoHongShu (xiaohongshu.com, xhslink.com)
- `cebbank`: CEB Bank (cebbank.com.cn)
- `news`: News sites
- `developer`: Developer resources
- `api`: API endpoints

### Special Tags / 特殊标签
- `error`: Expected to produce errors (for error handling tests)
- `timeout`: May timeout (for timeout handling tests)

## Integration with Test Scripts / 与测试脚本集成

The URL suite integrates with the regression test runner:

```bash
# Basic usage - run all non-manual URLs
python scripts/run_regression_suite.py

# Specific tags
python scripts/run_regression_suite.py --tags wechat,production

# Exclude tags
python scripts/run_regression_suite.py --exclude-tags manual,slow

# Save detailed report
python scripts/run_regression_suite.py --output reports/regression/latest.json

# Run with verbose logging
python scripts/run_regression_suite.py --verbose --tags fast
```

## Examples / 示例

### Adding a New WeChat URL

```
# 1. Find the URL
https://mp.weixin.qq.com/s/NewArticle123

# 2. Test it manually
# (Verify it loads and parses correctly)

# 3. Add to url_suite.txt under "WeChat Articles" section
https://mp.weixin.qq.com/s/NewArticle123 | New WeChat feature article | urllib | wechat,production,fast

# 4. Run regression test
python scripts/run_regression_suite.py --tags wechat
```

### Commenting Out a Broken URL

```
# Before:
https://example.com/article/123 | Example article | urllib | test,fast

# After (with reason):
# BROKEN 2025-10-10: Site redesigned, URL structure changed
# https://example.com/article/123 | Example article | urllib | test,fast
```

### Adding an Edge Case URL

```
# Add to "Edge Cases" section
https://httpbin.org/status/503 | HTTPBin 503 service unavailable | urllib | error,fast,reference

# Tag explanation:
# - error: Expected to produce error response
# - fast: Quick response
# - reference: Using httpbin.org reference service
```

## See Also / 另见

- Regression runner: `scripts/run_regression_suite.py` (Task-2 Phase 2)
- Routing config: `config/routing.yaml`
- Test reports: `reports/regression/`
- Template documentation: `parser_engine/templates/README.md`
- Error handling: `error_handler/README.md`
