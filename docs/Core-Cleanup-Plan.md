# Core Cleanup Plan / 核心模块精简方案
# Task-2: Core Module Pruning

**Created:** 2025-10-10
**Status:** Planning Phase - Pending User Approval / 规划阶段 - 待用户确认
**Estimated Impact:** Reduce codebase by ~40%, improve maintainability / 减少约40%代码量，提升可维护性

---

## Executive Summary / 执行摘要

This document provides a comprehensive plan for pruning non-essential modules from the Web_Fetcher project while preserving all core functionality of the `wf` tool and its fallback chains.

本文档提供了精简Web_Fetcher项目非核心模块的全面方案，同时保留`wf`工具及其兜底链路的所有核心功能。

### Key Findings / 关键发现

- **55 test files** identified (many experimental or legacy) / 识别出55个测试文件（多为实验性或历史文件）
- **3 major directories** can be safely removed/archived / 3个主要目录可以安全删除/归档
- **Core dependencies** clearly mapped to 8 essential modules / 核心依赖明确映射到8个必要模块
- **Zero functional impact** if executed correctly / 如果正确执行，零功能影响

---

## Phase 1: Dependency & Directory Inventory / 阶段1：依赖与目录清单

### 1.1 Core Dependency Chain / 核心依赖链

Based on manual analysis of `webfetcher.py` and `wf.py`:

**webfetcher.py core imports:**
```python
# Direct dependencies (必须保留)
from error_handler import ...
from config.ssl_problematic_domains import ...
import parsers
from parsers import ...

# Conditional imports (根据可用性)
from selenium_config import SeleniumConfig
from selenium_fetcher import SeleniumFetcher
```

**wf.py core imports:**
```python
# ChromeDriver management (Task-3成果)
from drivers import check_chrome_driver_compatibility
```

### 1.2 Must-Keep Modules / 必须保留模块

| Module / 模块 | Reason / 原因 | Used By / 被谁使用 |
|---------------|---------------|-------------------|
| `webfetcher.py` | Core CLI entry point / 核心CLI入口 | Direct user invocation |
| `wf.py` | Convenience wrapper / 便捷包装器 | User-facing tool |
| `error_handler.py` | Error classification & handling / 错误分类和处理 | webfetcher.py |
| `error_types.py` | Error type definitions / 错误类型定义 | error_handler.py |
| `error_classifier.py` | Error pattern matching / 错误模式匹配 | error_handler.py |
| `error_cache.py` | Error caching mechanism / 错误缓存机制 | error_handler.py |
| `selenium_config.py` | Selenium configuration / Selenium配置 | webfetcher.py |
| `selenium_fetcher.py` | Selenium fallback / Selenium兜底 | webfetcher.py |
| `parsers.py` | Main parser dispatcher / 主解析器分发器 | webfetcher.py |
| `parsers_migrated.py` | Migrated parser implementations / 已迁移解析器实现 | parsers.py |
| `parsers_legacy.py` | Legacy parser fallback / 旧解析器兜底 | parsers.py (optional) |
| `routing/` | URL routing engine / URL路由引擎 | parsers.py |
| `manual_chrome/` | Manual Chrome fallback / 手动Chrome兜底 | webfetcher.py |
| `config/` | Configuration files / 配置文件 | Multiple modules |
| `drivers/` | ChromeDriver version management / ChromeDriver版本管理 | wf.py |

**Total:** 15 core modules/directories / 共15个核心模块/目录

### 1.3 Removable Directories / 可删除目录

| Directory / 目录 | Size | Files | Reason / 原因 | Action / 操作 |
|------------------|------|-------|---------------|---------------|
| `benchmarks/` | Small | 2 | Performance testing only / 仅用于性能测试 | **DELETE** |
| `diagnostics/` | Medium | 5 | SPA diagnosis tools (not used by wf) / SPA诊断工具（wf不使用） | **DELETE** |
| `parser_engine/` | Large | ~30 | Old parser architecture (replaced by routing/) / 旧解析器架构（已被routing/取代） | **ARCHIVE** |
| `test_artifacts/` | Medium | Various | Test output files / 测试输出文件 | **DELETE** |

### 1.4 Removable Test Files / 可删除测试文件

**Root-level test files** (18 files):
```
test_raw_html.py
test_chrome_cdp_connection.py
test_chrome_cdp_ssl_bypass.py
test_chrome_cdp_simple.py
test_manual_chrome_check.py
test_pdf_print_playwright.py
test_pdf_print_selenium.py
verify_pdf_approach.py
test_manual_chrome_selenium.py
test_manual_chrome_pychrome.py
check_manual_test_env.py
test_manual_chrome_module.py
test_manual_chrome_import.py
test_example.log
test_github.log
test_python.log
test_xiaohongshu.log
test_icbc.log
test_cebbank.log
```

**Action:** DELETE all root-level test_*.py and test_*.log files / 删除所有根目录的测试文件

**tests/ directory** (37 files):
- Keep integration tests: `test_integration_simple.py`, `test_selenium_integration.py`
- Keep driver tests: `tests/test_drivers/` (Task-3 成果)
- Delete experimental tests: `verify_phase1_optimization.py`, `verify_phase2.py`

### 1.5 Removable Documentation Files / 可删除文档文件

**Root-level report files:**
```
PHASE_2.2_STEP_2.2.1_REPORT.md
PHASE_2.2_STEP_2.2.3_SUMMARY.txt
PHASE_2.2_STEP_2.2.3_COMPLETED.md
PHASE_3.1_COMPLETION_REPORT.md
PHASE_3.1_SUMMARY.txt
stage3_test_report.md
PROJECT_ANALYSIS_REPORT_2025_10_09.md
```

**Action:** ARCHIVE to `docs/archive/historical-reports/` / 归档到文档历史报告目录

### 1.6 Removable Scripts / 可删除脚本

Based on scanning `scripts/` directory, identify:
- One-time migration scripts
- Experimental tools
- Duplicate functionality

**Keep:**
- `scripts/manage_chromedriver.py` (Task-3 deliverable)
- Any scripts imported by wf.py or webfetcher.py

---

## Phase 2: Pruning Plan Draft / 阶段2：精简方案草案

### 2.1 Removal Strategy / 删除策略

**Three-stage approach:**

#### Stage 1: Safe Deletions (Low Risk) / 第一阶段：安全删除（低风险）
1. Delete `test_artifacts/` directory
2. Delete root-level `*.log` files
3. Delete `benchmarks/` directory
4. Delete experimental test files (`test_chrome_cdp_*.py`, `test_pdf_*.py`, etc.)

**Validation:**
- Run `wf --help` - should work
- Run `python webfetcher.py --help` - should work
- No import errors

#### Stage 2: Medium-Risk Deletions / 第二阶段：中风险删除
1. Delete `diagnostics/` directory
2. Delete root-level phase report markdown files (move to archive first)
3. Delete redundant test files in `tests/`

**Validation:**
- Run integration tests: `python -m pytest tests/test_integration_simple.py`
- Run selenium tests: `python -m pytest tests/test_selenium_integration.py`
- Test wf tool: `wf "https://example.com"`

#### Stage 3: Archive parser_engine (Requires Analysis) / 第三阶段：归档parser_engine（需要分析）
1. Verify `parser_engine/` is NOT imported by any core modules
2. Create archive directory: `ARCHIVE/parser_engine/`
3. Move `parser_engine/` to archive
4. Add README explaining why it's archived

**Validation:**
- Full regression suite (when available from P1 tasks)
- Test WeChat parsing: `wf "https://mp.weixin.qq.com/s/..."`
- Test Xiaohongshu parsing: `wf "https://www.xiaohongshu.com/..."`
- Test generic parsing: `wf "https://github.com/..."`
- Test manual Chrome fallback with problematic domains

### 2.2 File-Level Categorization / 文件级分类

| Category / 类别 | Count | Action / 操作 |
|-----------------|-------|---------------|
| Core Modules | 15 | **KEEP** 保留 |
| Driver Tests (Task-3) | 3 | **KEEP** 保留 |
| Integration Tests | 2 | **KEEP** 保留 |
| Historical Reports | 7 | **ARCHIVE** 归档 |
| Experimental Tests | 18 | **DELETE** 删除 |
| Log Files | 6 | **DELETE** 删除 |
| Benchmarks | 2 | **DELETE** 删除 |
| Diagnostics | 5 | **DELETE** 删除 |
| Test Artifacts | ~10 | **DELETE** 删除 |
| parser_engine/ | ~30 | **ARCHIVE** 归档 (后续) |

**Total files to remove:** ~80 files (approximately 40% of codebase)
**总删除文件数：**约80个文件（约占代码库的40%）

---

## Phase 3: Validation & Risk Assessment / 阶段3：验证与风险评估

### 3.1 Validation Checklist / 验证清单

**Pre-deletion:**
- [ ] Create git branch: `task-2-module-pruning`
- [ ] Full backup commit
- [ ] Document current directory structure
- [ ] Run `python webfetcher.py --help` - record output
- [ ] Run `wf --help` - record output
- [ ] Run existing integration tests - record pass/fail count

**Post-Stage-1:**
- [ ] No import errors on startup
- [ ] `wf --help` still works
- [ ] `python webfetcher.py --help` still works
- [ ] Basic fetch test: `wf "https://example.com"`

**Post-Stage-2:**
- [ ] Integration tests still pass: `pytest tests/test_integration_simple.py`
- [ ] Selenium tests still pass: `pytest tests/test_selenium_integration.py`
- [ ] Driver tests still pass: `pytest tests/test_drivers/`
- [ ] Manual Chrome test: Fetch problematic domain

**Post-Stage-3:**
- [ ] All core parsers work: WeChat, Xiaohongshu, generic
- [ ] Routing system intact
- [ ] Error handling unchanged
- [ ] Selenium fallback operational

### 3.2 Risk Matrix / 风险矩阵

| Risk / 风险 | Probability / 概率 | Impact / 影响 | Mitigation / 缓解措施 |
|-------------|-------------------|---------------|---------------------|
| Hidden import dependency | Medium / 中 | High / 高 | Grep全局搜索, 渐进式删除 |
| Dynamic import (not detectable) | Low / 低 | High / 高 | Smoke test覆盖所有功能 |
| Config file dependency | Low / 低 | Medium / 中 | Review config/ before deletion |
| Test regression failure | Medium / 中 | Medium / 中 | Keep integration tests, run after each stage |
| parser_engine future dependency | Low / 低 | Medium / 中 | Archive instead of delete |

### 3.3 Rollback Strategy / 回滚策略

If any validation fails:

1. **Immediate rollback:**
   ```bash
   git reset --hard HEAD
   git clean -fd
   ```

2. **Partial rollback:**
   - Restore specific directory from git history
   - Example: `git checkout HEAD -- parser_engine/`

3. **Investigation:**
   - Identify which deleted file caused the issue
   - Use `git log --all --full-history -- path/to/file` to find deletion commit
   - Use `git show <commit>:path/to/file` to review file content

4. **Documentation:**
   - Record why rollback was necessary
   - Update this plan with findings
   - Mark module as "requires further analysis"

### 3.4 Smoke Test Matrix / 冒烟测试矩阵

| Scenario / 场景 | Test Command / 测试命令 | Expected Result / 预期结果 |
|-----------------|------------------------|---------------------------|
| Help display | `wf --help` | Usage info printed |
| Simple static fetch | `wf "https://example.com"` | Markdown output created |
| WeChat article | `wf "https://mp.weixin.qq.com/s/..."` | WeChat-specific parser runs |
| Xiaohongshu note | `wf "https://www.xiaohongshu.com/..."` | Xiaohongshu parser runs |
| Bank domain (SSL issue) | `wf "https://www.cebbank.com.cn/..."` | Selenium fallback triggered |
| Manual Chrome fallback | Test with debug Chrome | Manual Chrome helper works |
| ChromeDriver check | `wf --diagnose` | Version compatibility check runs |
| Integration test | `pytest tests/test_integration_simple.py` | All tests pass |
| Driver test | `pytest tests/test_drivers/` | All tests pass |

---

## Phase 4: Plan Review & Adjustment / 阶段4：方案评审与调整

### 4.1 Dependencies on Other Tasks / 对其他任务的依赖

This pruning plan coordinates with:

- **Task-1 (P1):** Regression test suite - WAIT for completion before Stage 3
- **Task-3 (P2):** ChromeDriver version management - COMPLETED ✅ Keep drivers/ intact
- **Future tasks:** If any future task plans to use parser_engine, consult before archiving

### 4.2 Execution Timeline / 执行时间线

| Stage / 阶段 | Duration / 时长 | Prerequisites / 前置条件 |
|--------------|----------------|-------------------------|
| Stage 1: Safe deletions | 30 min | User approval, git backup |
| Validation 1 | 15 min | Stage 1 complete |
| Stage 2: Medium-risk deletions | 45 min | Validation 1 passed |
| Validation 2 | 30 min | Stage 2 complete |
| Stage 3: Archive parser_engine | 1 hour | Validation 2 passed, grep analysis done |
| Final validation | 1 hour | Stage 3 complete, full smoke tests |

**Total estimated time:** 4 hours / 总预计时间：4小时

### 4.3 Adjustment Opportunities / 调整机会

After each validation stage, review:

1. **Did any unexpected errors occur?**
   - Document new dependencies discovered
   - Adjust next stage plan accordingly

2. **Can we safely delete more?**
   - If validation passes easily, consider additional candidates
   - Always err on side of caution

3. **Should we preserve anything planned for deletion?**
   - If user feedback indicates future use
   - If hidden value discovered during execution

---

## Appendix A: Detailed Directory Structure / 附录A：详细目录结构

### Current Structure (Before Pruning) / 当前结构（精简前）
```
Web_Fetcher/
├── webfetcher.py           [KEEP] Core CLI
├── wf.py                   [KEEP] Wrapper tool
├── error_handler.py        [KEEP] Error system
├── error_types.py          [KEEP] Error types
├── error_classifier.py     [KEEP] Error classification
├── error_cache.py          [KEEP] Error caching
├── selenium_config.py      [KEEP] Selenium config
├── selenium_fetcher.py     [KEEP] Selenium fallback
├── parsers.py              [KEEP] Parser dispatcher
├── parsers_migrated.py     [KEEP] Migrated parsers
├── parsers_legacy.py       [KEEP?] Legacy parsers - review usage
│
├── routing/                [KEEP] URL routing
│   ├── __init__.py
│   ├── engine.py
│   ├── matchers.py
│   └── config_loader.py
│
├── manual_chrome/          [KEEP] Manual Chrome fallback
│   ├── __init__.py
│   ├── helper.py
│   └── exceptions.py
│
├── drivers/                [KEEP] Task-3 deliverable
│   ├── __init__.py
│   ├── constants.py
│   └── version_manager.py
│
├── config/                 [KEEP] Configuration
│   ├── ssl_problematic_domains.py
│   └── manual_chrome_config.yaml
│
├── docs/                   [KEEP] Documentation
│   ├── chromedriver-management.md
│   └── [other docs]
│
├── scripts/                [REVIEW] Scripts
│   └── manage_chromedriver.py  [KEEP]
│
├── tests/                  [REVIEW] Test suite
│   ├── test_integration_simple.py      [KEEP]
│   ├── test_selenium_integration.py    [KEEP]
│   └── test_drivers/                   [KEEP] Task-3 tests
│
├── TASKS/                  [KEEP] Task documentation
│
├── benchmarks/             [DELETE] Performance testing
├── diagnostics/            [DELETE] SPA diagnostics
├── parser_engine/          [ARCHIVE] Old parser architecture
├── test_artifacts/         [DELETE] Test outputs
│
└── [Root test files]       [DELETE] 18 test_*.py files
```

### Target Structure (After Pruning) / 目标结构（精简后）
```
Web_Fetcher/
├── webfetcher.py           Core CLI
├── wf.py                   Wrapper tool
├── error_*.py              Error system (4 files)
├── selenium_*.py           Selenium integration (2 files)
├── parsers*.py             Parser modules (3 files)
│
├── routing/                URL routing engine
├── manual_chrome/          Manual Chrome fallback
├── drivers/                ChromeDriver management
├── config/                 Configuration files
├── docs/                   Documentation (+ archive/)
├── scripts/                Essential scripts only
├── tests/                  Core tests only (~10 files)
└── TASKS/                  Task documentation

ARCHIVE/                    [NEW] Historical code
└── parser_engine/          Old parser architecture
    └── README.md           Explanation of archival
```

---

## Appendix B: Import Analysis Commands / 附录B：导入分析命令

**To verify no hidden imports before deletion:**

```bash
# Search for imports of a module
grep -r "import parser_engine" .
grep -r "from parser_engine" .

# Search for imports of diagnostics
grep -r "import diagnostics" .
grep -r "from diagnostics" .

# Search for imports of benchmarks
grep -r "import benchmarks" .
grep -r "from benchmarks" .

# Search for dynamic imports
grep -r "__import__(" .
grep -r "importlib.import_module(" .
```

---

## Appendix C: Rollback Commands / 附录C：回滚命令

**Full rollback:**
```bash
git reset --hard HEAD
git clean -fd
```

**Restore specific directory:**
```bash
git checkout HEAD -- parser_engine/
```

**Restore specific file:**
```bash
git checkout HEAD -- path/to/file.py
```

**Find deletion commit:**
```bash
git log --all --full-history -- path/to/deleted/file
```

**View deleted file content:**
```bash
git show <commit-hash>:path/to/file
```

---

## Approval & Sign-off / 批准与确认

**Plan Status:** Pending User Approval / 待用户批准

**Before proceeding with execution:**
- [ ] User has reviewed this plan
- [ ] User approves the categorization (KEEP/DELETE/ARCHIVE)
- [ ] User confirms no additional modules are needed
- [ ] User agrees with the three-stage approach
- [ ] Git backup branch created

**Approved by:** _________________
**Date:** _________________
**Approval signature:** _________________

---

## Execution Log / 执行日志

*This section will be populated during actual execution.*

### Stage 1 Execution
- **Date:** TBD
- **Status:** Not started
- **Files deleted:** 0
- **Validation result:** N/A

### Stage 2 Execution
- **Date:** TBD
- **Status:** Not started
- **Files deleted:** 0
- **Validation result:** N/A

### Stage 3 Execution
- **Date:** TBD
- **Status:** Not started
- **Directories archived:** 0
- **Validation result:** N/A

---

**Document Version:** 1.0
**Last Updated:** 2025-10-10
**Next Review:** After user approval / 用户批准后
