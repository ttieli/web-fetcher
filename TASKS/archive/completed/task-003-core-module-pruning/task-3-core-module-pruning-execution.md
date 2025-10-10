# Task 3: Core Module Pruning - Execution / 核心模块精简 - 执行阶段

## Status / 状态
- 🔄 **READY FOR EXECUTION** / 准备执行
- Planning Complete ✅ / 规划完成
- Awaiting user approval to begin / 等待用户批准开始

## Priority / 优先级
- P2 – Reduce maintenance surface without breaking wf / 第二优先级，在不影响 wf 工具的前提下降本增效

## Estimated Effort / 预计工时
- 4 hours total / 总计4小时
  - Stage 1: 0.75h (30min execution + 15min validation)
  - Stage 2: 1.25h (45min execution + 30min validation)
  - Stage 3: 2h (1h execution + 1h validation)

## Overview / 概述

This task executes the comprehensive Core Module Pruning plan documented in `docs/Core-Cleanup-Plan.md`. The execution follows a careful 3-stage approach with validation gates at each step, ensuring zero functional impact on the `wf` tool while reducing codebase size by ~40%.

本任务执行`docs/Core-Cleanup-Plan.md`中记录的全面核心模块精简计划。执行遵循仔细的3阶段方法，每步都有验证关卡，确保对`wf`工具零功能影响，同时减少约40%的代码量。

## Prerequisites / 前置条件

Before executing this task, ensure:
执行此任务前，确保：

- ✅ Core Cleanup Plan reviewed and approved / 核心清理计划已审查和批准
- ✅ Task-002 (Regression Test Harness) completed / Task-002（回归测试工具）已完成
- ✅ Task-003 (ChromeDriver Version Management) completed / Task-003（ChromeDriver版本管理）已完成
- ✅ All integration tests passing / 所有集成测试通过
- ✅ Git repository in clean state / Git仓库处于干净状态
- ✅ Full backup available / 完整备份可用

## Phase 0: Pre-Execution Preparation / 阶段0：执行前准备

### Milestone 0.1: Environment Verification / 里程碑0.1：环境验证

**Duration / 时长:** 10 minutes / 10分钟

**Objective / 目标:** Verify execution environment is ready and safe for pruning operations.

**Execution Steps / 执行步骤:**

```bash
# Step 1: Verify git status
cd /Users/tieli/Library/Mobile\ Documents/com~apple~CloudDocs/Project/Web_Fetcher
git status

# Expected: clean working tree
# 预期：工作树干净

# Step 2: Record current state
git log --oneline -5 > /tmp/pre-pruning-commits.txt
find . -type f -name "*.py" | wc -l > /tmp/pre-pruning-file-count.txt
du -sh . > /tmp/pre-pruning-size.txt

# Step 3: Run baseline tests
python webfetcher.py --help > /tmp/pre-pruning-webfetcher-help.txt
wf --help > /tmp/pre-pruning-wf-help.txt
python -m pytest tests/test_integration_simple.py -v > /tmp/pre-pruning-integration-tests.txt
python -m pytest tests/test_drivers/ -v > /tmp/pre-pruning-driver-tests.txt
```

**Validation Criteria / 验证标准:**
- [ ] Git working tree is clean / Git工作树干净
- [ ] All baseline tests pass / 所有基线测试通过
- [ ] `webfetcher.py --help` runs without errors / webfetcher.py --help运行无错误
- [ ] `wf --help` runs without errors / wf --help运行无错误
- [ ] Integration tests: All passing / 集成测试：全部通过
- [ ] Driver tests: All passing / 驱动测试：全部通过

**Output / 输出:**
- Baseline state files saved to `/tmp/pre-pruning-*.txt`
- Ready to proceed to Stage 1

### Milestone 0.2: Create Execution Branch / 里程碑0.2：创建执行分支

**Duration / 时长:** 5 minutes / 5分钟

**Objective / 目标:** Create dedicated git branch for pruning operations with full traceability.

**Execution Steps / 执行步骤:**

```bash
# Step 1: Create and checkout new branch
git checkout -b task-3-core-module-pruning

# Step 2: Verify branch creation
git branch --show-current

# Expected output: task-3-core-module-pruning
# 预期输出：task-3-core-module-pruning

# Step 3: Create safety commit
git commit --allow-empty -m "chore: Begin Task-3 Core Module Pruning Execution

Starting 3-stage code cleanup process:
- Stage 1: Safe deletions (low risk)
- Stage 2: Medium-risk deletions
- Stage 3: Archive parser_engine

Reference: docs/Core-Cleanup-Plan.md
Planning Task: TASKS/task-2-core-module-pruning.md

Baseline state preserved in /tmp/pre-pruning-*.txt files"
```

**Validation Criteria / 验证标准:**
- [ ] Branch created successfully / 分支创建成功
- [ ] On correct branch (task-3-core-module-pruning) / 在正确分支上
- [ ] Safety commit created / 安全提交已创建

**Rollback Procedure / 回滚程序:**
```bash
# If issues occur, return to main
git checkout main
git branch -D task-3-core-module-pruning
```

---

## Stage 1: Safe Deletions (Low Risk) / 阶段1：安全删除（低风险）

**Risk Level / 风险级别:** LOW / 低
**Impact if Failed / 失败影响:** Minimal - easily recoverable / 最小 - 易恢复
**Estimated Duration / 预计时长:** 45 minutes total (30min execution + 15min validation)

### Milestone 1.1: Delete Test Artifacts & Logs / 里程碑1.1：删除测试产物和日志

**Duration / 时长:** 10 minutes / 10分钟

**Objective / 目标:** Remove test output files and logs (6 files total).

**Files to Delete / 删除文件清单:**
```
test_example.log
test_github.log
test_python.log
test_xiaohongshu.log
test_icbc.log
test_cebbank.log
```

**Execution Commands / 执行命令:**

```bash
cd /Users/tieli/Library/Mobile\ Documents/com~apple~CloudDocs/Project/Web_Fetcher

# Step 1: Verify files exist before deletion
ls -la test_*.log 2>/dev/null | tee /tmp/stage1-1-files-to-delete.txt

# Step 2: Delete log files
rm -v test_example.log test_github.log test_python.log \
     test_xiaohongshu.log test_icbc.log test_cebbank.log

# Step 3: Verify deletion
ls -la test_*.log 2>&1 | grep "No such file"

# Expected: "No such file or directory"
# 预期："No such file or directory"
```

**Validation / 验证:**
```bash
# Quick smoke test
python webfetcher.py --help >/dev/null && echo "✅ webfetcher.py OK" || echo "❌ webfetcher.py FAILED"
wf --help >/dev/null && echo "✅ wf OK" || echo "❌ wf FAILED"
```

**Checkpoint Commit / 检查点提交:**
```bash
git add -A
git commit -m "chore(cleanup): Stage 1.1 - Remove test log files

Deleted 6 test log files:
- test_example.log
- test_github.log
- test_python.log
- test_xiaohongshu.log
- test_icbc.log
- test_cebbank.log

Validation: webfetcher.py and wf CLI both functional ✅"
```

### Milestone 1.2: Delete Benchmarks Directory / 里程碑1.2：删除基准测试目录

**Duration / 时长:** 5 minutes / 5分钟

**Objective / 目标:** Remove performance benchmarking code (not used by wf tool).

**Directory to Delete / 删除目录:**
- `benchmarks/` (2 files: `__init__.py`, `parser_performance.py`)

**Execution Commands / 执行命令:**

```bash
# Step 1: Verify directory contents
ls -la benchmarks/ | tee /tmp/stage1-2-benchmarks-contents.txt

# Step 2: Delete benchmarks directory
rm -rf benchmarks/

# Step 3: Verify deletion
test ! -d benchmarks && echo "✅ benchmarks/ deleted" || echo "❌ Still exists"
```

**Validation / 验证:**
```bash
# Check for any imports of benchmarks
grep -r "import benchmarks" . --exclude-dir=.git 2>/dev/null
grep -r "from benchmarks" . --exclude-dir=.git 2>/dev/null

# Expected: No results
# 预期：无结果

# Quick smoke test
wf --help >/dev/null && echo "✅ wf OK" || echo "❌ wf FAILED"
```

**Checkpoint Commit / 检查点提交:**
```bash
git add -A
git commit -m "chore(cleanup): Stage 1.2 - Remove benchmarks directory

Deleted benchmarks/ directory (2 files):
- __init__.py
- parser_performance.py

Reason: Performance testing only, not used by wf tool
Validation: No imports detected, wf CLI functional ✅"
```

### Milestone 1.3: Delete test_artifacts Directory / 里程碑1.3：删除测试产物目录

**Duration / 时长:** 5 minutes / 5分钟

**Objective / 目标:** Remove test output artifacts directory.

**Execution Commands / 执行命令:**

```bash
# Step 1: Check if directory exists and list contents
if [ -d test_artifacts ]; then
    ls -la test_artifacts/ | tee /tmp/stage1-3-test-artifacts-contents.txt
    du -sh test_artifacts/
fi

# Step 2: Delete directory
rm -rf test_artifacts/

# Step 3: Verify deletion
test ! -d test_artifacts && echo "✅ test_artifacts/ deleted" || echo "❌ Still exists"
```

**Validation / 验证:**
```bash
# Check for any references
grep -r "test_artifacts" . --exclude-dir=.git --exclude-dir=TASKS 2>/dev/null | grep -v "\.md:"

# Quick smoke test
wf --help >/dev/null && echo "✅ wf OK"
```

**Checkpoint Commit / 检查点提交:**
```bash
git add -A
git commit -m "chore(cleanup): Stage 1.3 - Remove test_artifacts directory

Deleted test_artifacts/ directory and contents
Reason: Test output files, not part of core functionality
Validation: No references found, wf CLI functional ✅"
```

### Milestone 1.4: Delete Experimental Test Files / 里程碑1.4：删除实验性测试文件

**Duration / 时长:** 10 minutes / 10分钟

**Objective / 目标:** Remove 18 experimental test files from root directory.

**Files to Delete / 删除文件清单 (18 files):**
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
FAILED_2025-10-10-094832 - www.cebbank.com.cn.md
```

**Execution Commands / 执行命令:**

```bash
# Step 1: List all test files to be deleted
ls -la test_*.py check_*.py verify_*.py FAILED_*.md 2>/dev/null | tee /tmp/stage1-4-test-files.txt

# Step 2: Delete experimental test files
rm -v test_raw_html.py \
      test_chrome_cdp_connection.py \
      test_chrome_cdp_ssl_bypass.py \
      test_chrome_cdp_simple.py \
      test_manual_chrome_check.py \
      test_pdf_print_playwright.py \
      test_pdf_print_selenium.py \
      verify_pdf_approach.py \
      test_manual_chrome_selenium.py \
      test_manual_chrome_pychrome.py \
      check_manual_test_env.py \
      test_manual_chrome_module.py \
      test_manual_chrome_import.py \
      FAILED_2025-10-10-094832\ -\ www.cebbank.com.cn.md 2>/dev/null

# Step 3: Verify root directory cleanup
ls -la test_*.py check_*.py verify_*.py 2>&1 | grep "No such file" && echo "✅ All deleted"
```

**Validation / 验证:**
```bash
# Verify no broken imports
python -c "import webfetcher" 2>/dev/null && echo "✅ webfetcher imports OK"
python -c "import sys; sys.path.insert(0, '.'); import wf" 2>/dev/null && echo "✅ wf imports OK"

# Run smoke tests
wf --help >/dev/null && echo "✅ wf CLI OK"
python webfetcher.py --help >/dev/null && echo "✅ webfetcher CLI OK"
```

**Checkpoint Commit / 检查点提交:**
```bash
git add -A
git commit -m "chore(cleanup): Stage 1.4 - Remove experimental test files

Deleted 14 experimental test files from root:
- test_*.py (CDP, PDF, manual chrome tests)
- check_manual_test_env.py
- verify_pdf_approach.py
- FAILED test output markdown file

Reason: Experimental/one-time tests, not part of test suite
Validation: Imports successful, CLI tools functional ✅"
```

### Stage 1 Validation Gate / 阶段1验证关卡

**Duration / 时长:** 15 minutes / 15分钟

**Objective / 目标:** Comprehensive validation before proceeding to Stage 2.

**Validation Commands / 验证命令:**

```bash
# 1. Help commands must work
echo "=== Testing Help Commands ==="
python webfetcher.py --help && echo "✅ webfetcher --help OK" || echo "❌ FAILED"
wf --help && echo "✅ wf --help OK" || echo "❌ FAILED"

# 2. Basic fetch test
echo "=== Testing Basic Fetch ==="
wf "https://example.com" && echo "✅ Basic fetch OK" || echo "❌ FAILED"

# 3. No import errors on startup
echo "=== Testing Imports ==="
python -c "import webfetcher; print('✅ webfetcher imports OK')" || echo "❌ FAILED"

# 4. File count comparison
echo "=== File Count Comparison ==="
echo "Before: $(cat /tmp/pre-pruning-file-count.txt)"
echo "After: $(find . -type f -name '*.py' | wc -l)"

# 5. No unexpected errors in logs
echo "=== Checking for Errors ==="
! grep -i "error\|exception\|failed" /tmp/stage1-*.txt | grep -v "Expected"
```

**Go/No-Go Decision Criteria / 通过/不通过决策标准:**

**✅ GO (Proceed to Stage 2) IF / 如果满足以下条件则继续:**
- [ ] All help commands work / 所有帮助命令工作
- [ ] Basic fetch succeeds / 基础抓取成功
- [ ] No import errors / 无导入错误
- [ ] File count reduced by ~25 files / 文件数减少约25个
- [ ] No unexpected errors in validation logs / 验证日志无意外错误

**❌ NO-GO (Rollback Stage 1) IF / 如果出现以下情况则回滚:**
- Import errors detected / 检测到导入错误
- CLI tools not functional / CLI工具不可用
- Basic fetch fails / 基础抓取失败

**Rollback Procedure (if needed) / 回滚程序（如需要）:**
```bash
# Full rollback of Stage 1
git log --oneline | head -5  # Find the "Begin Task-3" commit
git reset --hard <commit-before-stage1>
git clean -fd

# Or restore specific items
git checkout HEAD~4 -- benchmarks/
git checkout HEAD~4 -- test_artifacts/
# etc.
```

**Stage 1 Completion Commit / 阶段1完成提交:**
```bash
git commit --allow-empty -m "milestone: Stage 1 Complete - Safe Deletions ✅

Summary:
- Deleted 6 log files
- Deleted benchmarks/ directory (2 files)
- Deleted test_artifacts/ directory
- Deleted 14 experimental test files
- Total: ~25 files removed

Validation:
✅ All CLI tools functional
✅ Basic fetch test passed
✅ No import errors
✅ File count reduced as expected

Next: Proceed to Stage 2 (Medium-Risk Deletions)"
```

---

## Stage 2: Medium-Risk Deletions / 阶段2：中风险删除

**Risk Level / 风险级别:** MEDIUM / 中
**Impact if Failed / 失败影响:** Moderate - requires careful validation / 中等 - 需要仔细验证
**Estimated Duration / 预计时长:** 1.25 hours total (45min execution + 30min validation)

### Milestone 2.1: Delete Diagnostics Directory / 里程碑2.1：删除诊断工具目录

**Duration / 时长:** 10 minutes / 10分钟

**Objective / 目标:** Remove SPA diagnostics tools (not used by wf tool).

**Directory to Delete / 删除目录:**
- `diagnostics/` (5 files: README.md, run_diagnosis.py, spa_diagnosis.py, test_results/)

**Execution Commands / 执行命令:**

```bash
# Step 1: Document directory contents
ls -laR diagnostics/ | tee /tmp/stage2-1-diagnostics-contents.txt
du -sh diagnostics/

# Step 2: Check for any imports
grep -r "import diagnostics" . --exclude-dir=.git --exclude-dir=diagnostics 2>/dev/null
grep -r "from diagnostics" . --exclude-dir=.git --exclude-dir=diagnostics 2>/dev/null

# Expected: No results (no dependencies)
# 预期：无结果（无依赖）

# Step 3: Delete directory
rm -rf diagnostics/

# Step 4: Verify deletion
test ! -d diagnostics && echo "✅ diagnostics/ deleted" || echo "❌ Still exists"
```

**Validation / 验证:**
```bash
# Import test
python -c "import webfetcher" && echo "✅ Imports OK"

# CLI test
wf --help >/dev/null && echo "✅ wf CLI OK"

# Fetch test
wf "https://example.com" >/dev/null && echo "✅ Fetch OK"
```

**Checkpoint Commit / 检查点提交:**
```bash
git add -A
git commit -m "chore(cleanup): Stage 2.1 - Remove diagnostics directory

Deleted diagnostics/ directory (5 files):
- README.md
- run_diagnosis.py
- spa_diagnosis.py
- test_results/ subdirectory

Reason: SPA diagnosis tools, not used by wf tool
Validation: No imports detected, all tests passing ✅"
```

### Milestone 2.2: Archive Historical Reports / 里程碑2.2：归档历史报告

**Duration / 时长:** 15 minutes / 15分钟

**Objective / 目标:** Move 7 historical phase report files to docs/archive/historical-reports/.

**Files to Archive / 归档文件清单:**
```
PHASE_2.2_STEP_2.2.1_REPORT.md
PHASE_2.2_STEP_2.2.3_SUMMARY.txt
PHASE_2.2_STEP_2.2.3_COMPLETED.md
PHASE_3.1_COMPLETION_REPORT.md
PHASE_3.1_SUMMARY.txt
stage3_test_report.md
PROJECT_ANALYSIS_REPORT_2025_10_09.md
```

**Execution Commands / 执行命令:**

```bash
# Step 1: Create archive directory
mkdir -p docs/archive/historical-reports

# Step 2: List files to archive
ls -la PHASE*.md PHASE*.txt stage*.md PROJECT*.md 2>/dev/null | tee /tmp/stage2-2-reports-to-archive.txt

# Step 3: Move files to archive
mv -v PHASE_2.2_STEP_2.2.1_REPORT.md docs/archive/historical-reports/
mv -v PHASE_2.2_STEP_2.2.3_SUMMARY.txt docs/archive/historical-reports/
mv -v PHASE_2.2_STEP_2.2.3_COMPLETED.md docs/archive/historical-reports/
mv -v PHASE_3.1_COMPLETION_REPORT.md docs/archive/historical-reports/
mv -v PHASE_3.1_SUMMARY.txt docs/archive/historical-reports/
mv -v stage3_test_report.md docs/archive/historical-reports/
mv -v PROJECT_ANALYSIS_REPORT_2025_10_09.md docs/archive/historical-reports/

# Step 4: Create README in archive
cat > docs/archive/historical-reports/README.md <<'EOF'
# Historical Reports Archive / 历史报告归档

This directory contains historical phase reports and project analysis documents that are no longer actively referenced but preserved for historical record.

本目录包含不再主动引用但为历史记录保留的历史阶段报告和项目分析文档。

## Archived Files / 归档文件

- PHASE_2.2_STEP_2.2.1_REPORT.md - Phase 2.2 Step 2.2.1 implementation report
- PHASE_2.2_STEP_2.2.3_SUMMARY.txt - Phase 2.2 Step 2.2.3 summary
- PHASE_2.2_STEP_2.2.3_COMPLETED.md - Phase 2.2 Step 2.2.3 completion
- PHASE_3.1_COMPLETION_REPORT.md - Phase 3.1 completion report
- PHASE_3.1_SUMMARY.txt - Phase 3.1 summary
- stage3_test_report.md - Stage 3 test report
- PROJECT_ANALYSIS_REPORT_2025_10_09.md - Project analysis 2025-10-09

## Archive Date / 归档日期
2025-10-10

## Archived By / 归档者
Task-3: Core Module Pruning Execution
EOF

# Step 5: Verify archival
ls -la docs/archive/historical-reports/ | tee /tmp/stage2-2-archive-verification.txt
```

**Validation / 验证:**
```bash
# Verify no broken references in active docs
grep -r "PHASE_2.2\|PHASE_3.1\|stage3_test\|PROJECT_ANALYSIS_2025_10_09" docs/*.md TASKS/*.md README.md 2>/dev/null | grep -v "archive/historical-reports"

# If any references found, they need to be updated
# 如果发现任何引用，需要更新

# Quick smoke test
wf --help >/dev/null && echo "✅ wf OK"
```

**Checkpoint Commit / 检查点提交:**
```bash
git add -A
git commit -m "docs(cleanup): Stage 2.2 - Archive historical phase reports

Moved 7 historical report files to docs/archive/historical-reports/:
- PHASE_2.2_STEP_2.2.1_REPORT.md
- PHASE_2.2_STEP_2.2.3_SUMMARY.txt
- PHASE_2.2_STEP_2.2.3_COMPLETED.md
- PHASE_3.1_COMPLETION_REPORT.md
- PHASE_3.1_SUMMARY.txt
- stage3_test_report.md
- PROJECT_ANALYSIS_REPORT_2025_10_09.md

Created archive README with metadata
Validation: No broken references, wf CLI functional ✅"
```

### Milestone 2.3: Delete Redundant Test Files in tests/ / 里程碑2.3：删除tests/中的冗余测试文件

**Duration / 时长:** 10 minutes / 10分钟

**Objective / 目标:** Remove experimental verification tests while keeping integration tests.

**Files to Delete / 删除文件清单:**
```
tests/verify_phase1_optimization.py
tests/verify_phase2.py
```

**Files to KEEP / 保留文件:**
```
tests/test_integration_simple.py
tests/test_selenium_integration.py
tests/test_drivers/ (entire directory - Task-3 deliverable)
```

**Execution Commands / 执行命令:**

```bash
# Step 1: List current test files
ls -la tests/*.py 2>/dev/null | tee /tmp/stage2-3-tests-before.txt

# Step 2: Verify which files to delete
test -f tests/verify_phase1_optimization.py && echo "Found: verify_phase1_optimization.py"
test -f tests/verify_phase2.py && echo "Found: verify_phase2.py"

# Step 3: Delete experimental verification tests
rm -v tests/verify_phase1_optimization.py tests/verify_phase2.py 2>/dev/null

# Step 4: List remaining test files
ls -la tests/*.py 2>/dev/null | tee /tmp/stage2-3-tests-after.txt

# Step 5: Verify kept files
test -f tests/test_integration_simple.py && echo "✅ Kept: test_integration_simple.py"
test -f tests/test_selenium_integration.py && echo "✅ Kept: test_selenium_integration.py"
test -d tests/test_drivers && echo "✅ Kept: test_drivers/ directory"
```

**Validation / 验证:**
```bash
# Run remaining integration tests
python -m pytest tests/test_integration_simple.py -v && echo "✅ Integration tests pass"
python -m pytest tests/test_selenium_integration.py -v && echo "✅ Selenium tests pass"
python -m pytest tests/test_drivers/ -v && echo "✅ Driver tests pass"
```

**Checkpoint Commit / 检查点提交:**
```bash
git add -A
git commit -m "test(cleanup): Stage 2.3 - Remove experimental verification tests

Deleted 2 experimental test files:
- tests/verify_phase1_optimization.py
- tests/verify_phase2.py

Kept essential tests:
✅ tests/test_integration_simple.py
✅ tests/test_selenium_integration.py
✅ tests/test_drivers/ (Task-3 deliverable)

Validation: All remaining tests passing ✅"
```

### Stage 2 Validation Gate / 阶段2验证关卡

**Duration / 时长:** 30 minutes / 30分钟

**Objective / 目标:** Comprehensive validation with integration and selenium tests.

**Validation Commands / 验证命令:**

```bash
# 1. Integration test suite
echo "=== Running Integration Tests ==="
python -m pytest tests/test_integration_simple.py -v --tb=short && echo "✅ PASS" || echo "❌ FAIL"

# 2. Selenium integration tests
echo "=== Running Selenium Tests ==="
python -m pytest tests/test_selenium_integration.py -v --tb=short && echo "✅ PASS" || echo "❌ FAIL"

# 3. Driver tests (Task-3)
echo "=== Running Driver Tests ==="
python -m pytest tests/test_drivers/ -v --tb=short && echo "✅ PASS" || echo "❌ FAIL"

# 4. Manual Chrome test (if applicable)
echo "=== Testing Manual Chrome Fallback ==="
# Test with problematic domain
wf "https://www.cebbank.com.cn/site/zhpd/zxgg35/cgjggg/263565922/index.html" && echo "✅ Manual Chrome OK" || echo "⚠️ Manual test skipped"

# 5. Smoke test matrix
echo "=== Smoke Test Matrix ==="
wf --help >/dev/null && echo "✅ Help command OK"
wf "https://example.com" >/dev/null && echo "✅ Basic fetch OK"
wf --diagnose && echo "✅ Diagnose command OK"

# 6. File count comparison
echo "=== File Count After Stage 2 ==="
echo "Original: $(cat /tmp/pre-pruning-file-count.txt)"
echo "After Stage 1: (see Stage 1 validation)"
echo "After Stage 2: $(find . -type f -name '*.py' | wc -l)"
```

**Go/No-Go Decision Criteria / 通过/不通过决策标准:**

**✅ GO (Proceed to Stage 3) IF / 如果满足以下条件则继续:**
- [ ] Integration tests: ALL PASSING / 集成测试：全部通过
- [ ] Selenium tests: ALL PASSING / Selenium测试：全部通过
- [ ] Driver tests: ALL PASSING / 驱动测试：全部通过
- [ ] Smoke test matrix: ALL PASSING / 冒烟测试矩阵：全部通过
- [ ] No regression detected / 未检测到回归

**❌ NO-GO (Rollback Stage 2) IF / 如果出现以下情况则回滚:**
- Any test failures / 任何测试失败
- Integration broken / 集成损坏
- CLI functionality impaired / CLI功能受损

**Rollback Procedure (if needed) / 回滚程序（如需要）:**
```bash
# Option 1: Full rollback to Stage 1 completion
git log --oneline | grep "Stage 1 Complete"
git reset --hard <stage-1-complete-commit>

# Option 2: Partial rollback of specific milestone
git log --oneline | head -10
git revert <milestone-commit>
```

**Stage 2 Completion Commit / 阶段2完成提交:**
```bash
git commit --allow-empty -m "milestone: Stage 2 Complete - Medium-Risk Deletions ✅

Summary:
- Deleted diagnostics/ directory (5 files)
- Archived 7 historical phase reports to docs/archive/historical-reports/
- Deleted 2 experimental verification tests from tests/

Total removed in Stage 2: ~12 files/directories
Cumulative removal: ~37 files

Validation:
✅ All integration tests passing
✅ All selenium tests passing
✅ All driver tests passing
✅ Smoke test matrix: all passing
✅ No regressions detected

Next: Proceed to Stage 3 (Archive parser_engine)"
```

---

## Stage 3: Archive parser_engine / 阶段3：归档parser_engine

**Risk Level / 风险级别:** MEDIUM-HIGH / 中高
**Impact if Failed / 失败影响:** Significant - requires full regression testing / 重大 - 需要完整回归测试
**Estimated Duration / 预计时长:** 2 hours total (1h execution + 1h validation)

### Milestone 3.1: Pre-Archive Dependency Analysis / 里程碑3.1：归档前依赖分析

**Duration / 时长:** 20 minutes / 20分钟

**Objective / 目标:** Final verification that parser_engine/ is not imported by core modules.

**Execution Commands / 执行命令:**

```bash
# Step 1: Search for all imports of parser_engine
echo "=== Searching for parser_engine imports ===" | tee /tmp/stage3-1-import-analysis.txt
grep -r "import parser_engine" . --exclude-dir=.git --exclude-dir=parser_engine 2>/dev/null | tee -a /tmp/stage3-1-import-analysis.txt
grep -r "from parser_engine" . --exclude-dir=.git --exclude-dir=parser_engine 2>/dev/null | tee -a /tmp/stage3-1-import-analysis.txt

# Expected: NO RESULTS
# 预期：无结果

# Step 2: Check for dynamic imports
echo "=== Checking for dynamic imports ===" | tee -a /tmp/stage3-1-import-analysis.txt
grep -r "__import__.*parser_engine" . --exclude-dir=.git --exclude-dir=parser_engine 2>/dev/null | tee -a /tmp/stage3-1-import-analysis.txt
grep -r "importlib.*parser_engine" . --exclude-dir=.git --exclude-dir=parser_engine 2>/dev/null | tee -a /tmp/stage3-1-import-analysis.txt

# Expected: NO RESULTS
# 预期：无结果

# Step 3: Check for string references in config files
echo "=== Checking config files ===" | tee -a /tmp/stage3-1-import-analysis.txt
grep -r "parser_engine" config/ 2>/dev/null | tee -a /tmp/stage3-1-import-analysis.txt

# Step 4: Document parser_engine contents
echo "=== Documenting parser_engine contents ===" | tee /tmp/stage3-1-parser-engine-inventory.txt
find parser_engine -type f | tee -a /tmp/stage3-1-parser-engine-inventory.txt
du -sh parser_engine | tee -a /tmp/stage3-1-parser-engine-inventory.txt
```

**Validation Criteria / 验证标准:**
- [ ] NO imports found in core modules / 核心模块中未发现导入
- [ ] NO dynamic imports detected / 未检测到动态导入
- [ ] NO config file references / 配置文件中无引用
- [ ] Inventory complete / 清单完整

**Decision Point / 决策点:**
- ✅ IF all checks pass: Proceed to archival / 如所有检查通过：继续归档
- ❌ IF any imports found: STOP and investigate / 如发现任何导入：停止并调查

### Milestone 3.2: Create Archive Structure / 里程碑3.2：创建归档结构

**Duration / 时长:** 10 minutes / 10分钟

**Objective / 目标:** Prepare ARCHIVE directory with proper documentation.

**Execution Commands / 执行命令:**

```bash
# Step 1: Create archive directory
mkdir -p ARCHIVE/parser_engine

# Step 2: Create archive README
cat > ARCHIVE/README.md <<'EOF'
# ARCHIVE Directory / 归档目录

This directory contains archived code that is no longer part of the active codebase but preserved for historical reference and potential future use.

本目录包含不再属于活跃代码库但为历史参考和未来潜在使用而保留的归档代码。

## Archived Modules / 归档模块

### parser_engine/ (Archived 2025-10-10)

**Reason for Archive / 归档原因:**
Old parser architecture replaced by the new routing/ and template-based parser system (Task-001 deliverable). The parser_engine/ module is no longer imported or used by any core functionality.

旧解析器架构已被新的routing/和基于模板的解析器系统（Task-001交付物）取代。parser_engine/模块不再被任何核心功能导入或使用。

**What was parser_engine? / parser_engine是什么？**
The original parser engine implementation before migration to the template-based system. It contained:
- Base parser classes
- Strategy pattern implementations
- Template parser (legacy version)
- Parser utilities and tools

**Replacement / 替代品:**
- routing/ - Config-driven URL routing system
- parsers_migrated.py - Template-based parser implementations
- parser_engine/templates/ - Migrated to routing/templates/

**When to Restore / 何时恢复:**
Only restore if:
1. Critical bug discovered in new routing system
2. Need to reference original implementation
3. Rollback to pre-migration state required

**How to Restore / 如何恢复:**
```bash
# Copy archived parser_engine back to root
cp -r ARCHIVE/parser_engine/ .

# Run tests to verify functionality
python -m pytest tests/ -k parser

# Check for import errors
python -c "import parser_engine"
```

**Archive Metadata / 归档元数据:**
- Archive Date: 2025-10-10
- Archived By: Task-3 Core Module Pruning Execution
- File Count: ~30 files
- Size: ~XX KB
- Git Reference: <commit-hash-before-archival>
- Related Task: TASKS/task-3-core-module-pruning-execution.md
EOF

# Step 3: Create parser_engine specific README
cat > ARCHIVE/parser_engine/README.md <<'EOF'
# parser_engine Archive / parser_engine归档

**Archive Date / 归档日期:** 2025-10-10
**Reason / 原因:** Replaced by routing/ and template-based parser system

## Original Structure / 原始结构

This directory preserves the original parser_engine/ module structure.

## Restoration Instructions / 恢复说明

See ARCHIVE/README.md for full restoration instructions.

## Contents / 内容

Preserved from original location with no modifications.
EOF
```

**Validation / 验证:**
- [ ] ARCHIVE/ directory created / ARCHIVE/目录已创建
- [ ] README.md created with full documentation / README.md已创建且包含完整文档
- [ ] Archive structure ready / 归档结构就绪

### Milestone 3.3: Move parser_engine to Archive / 里程碑3.3：移动parser_engine到归档

**Duration / 时长:** 10 minutes / 10分钟

**Objective / 目标:** Physically move parser_engine/ directory to ARCHIVE/.

**Execution Commands / 执行命令:**

```bash
# Step 1: Final size check before move
echo "=== parser_engine size before archival ===" | tee /tmp/stage3-3-size-check.txt
du -sh parser_engine/ | tee -a /tmp/stage3-3-size-check.txt

# Step 2: Move directory to archive
mv -v parser_engine/ ARCHIVE/

# Step 3: Verify move completed
test -d ARCHIVE/parser_engine && echo "✅ Move successful"
test ! -d parser_engine && echo "✅ Original removed"

# Step 4: Document archive
ls -laR ARCHIVE/parser_engine/ | head -50 | tee /tmp/stage3-3-archive-contents.txt
```

**Validation / 验证:**
```bash
# Verify no broken imports (should be same as 3.1)
grep -r "import parser_engine" . --exclude-dir=.git --exclude-dir=ARCHIVE 2>/dev/null

# Expected: NO RESULTS
# 预期：无结果

# Quick import test
python -c "import webfetcher" && echo "✅ webfetcher imports OK"
python -c "import parsers" && echo "✅ parsers imports OK"
```

**Checkpoint Commit / 检查点提交:**
```bash
git add -A
git commit -m "feat(archive): Stage 3.3 - Archive parser_engine to ARCHIVE/

Moved parser_engine/ directory (~30 files) to ARCHIVE/parser_engine/

Reason:
- Old parser architecture replaced by routing/ and template system
- No longer imported by core modules
- Preserved for historical reference

Archive includes:
- ARCHIVE/README.md with full documentation
- ARCHIVE/parser_engine/README.md with restoration instructions

Validation:
✅ No broken imports detected
✅ Core parsers import successfully

References: docs/Core-Cleanup-Plan.md Section 2.1 Stage 3"
```

### Stage 3 Validation Gate / 阶段3验证关卡

**Duration / 时长:** 1 hour / 1小时

**Objective / 目标:** Full regression testing with all parser types and fallback chains.

**Validation Commands / 验证命令:**

```bash
# === 1. Core Import Tests ===
echo "=== Core Import Tests ===" | tee /tmp/stage3-validation.txt
python -c "import webfetcher" && echo "✅ webfetcher" | tee -a /tmp/stage3-validation.txt
python -c "import parsers" && echo "✅ parsers" | tee -a /tmp/stage3-validation.txt
python -c "import parsers_migrated" && echo "✅ parsers_migrated" | tee -a /tmp/stage3-validation.txt
python -c "import routing.engine" && echo "✅ routing.engine" | tee -a /tmp/stage3-validation.txt

# === 2. CLI Commands ===
echo "=== CLI Commands ===" | tee -a /tmp/stage3-validation.txt
wf --help >/dev/null && echo "✅ wf --help" | tee -a /tmp/stage3-validation.txt
python webfetcher.py --help >/dev/null && echo "✅ webfetcher --help" | tee -a /tmp/stage3-validation.txt
wf --diagnose && echo "✅ wf --diagnose" | tee -a /tmp/stage3-validation.txt

# === 3. Parser-Specific Tests ===
echo "=== Parser-Specific Tests ===" | tee -a /tmp/stage3-validation.txt

# WeChat parser test
echo "Testing WeChat parser..." | tee -a /tmp/stage3-validation.txt
wf "https://mp.weixin.qq.com/s/test" 2>&1 | grep -q "WeChat\|微信" && echo "✅ WeChat parser" | tee -a /tmp/stage3-validation.txt

# Xiaohongshu parser test
echo "Testing Xiaohongshu parser..." | tee -a /tmp/stage3-validation.txt
wf "https://www.xiaohongshu.com/test" 2>&1 | grep -q "Xiaohongshu\|小红书" && echo "✅ Xiaohongshu parser" | tee -a /tmp/stage3-validation.txt

# Generic parser test
echo "Testing Generic parser..." | tee -a /tmp/stage3-validation.txt
wf "https://github.com/test" >/dev/null && echo "✅ Generic parser" | tee -a /tmp/stage3-validation.txt

# === 4. Integration Test Suite ===
echo "=== Integration Test Suite ===" | tee -a /tmp/stage3-validation.txt
python -m pytest tests/test_integration_simple.py -v --tb=short && echo "✅ Integration tests" | tee -a /tmp/stage3-validation.txt

# === 5. Selenium Integration ===
echo "=== Selenium Integration ===" | tee -a /tmp/stage3-validation.txt
python -m pytest tests/test_selenium_integration.py -v --tb=short && echo "✅ Selenium tests" | tee -a /tmp/stage3-validation.txt

# === 6. Driver Tests ===
echo "=== Driver Tests ===" | tee -a /tmp/stage3-validation.txt
python -m pytest tests/test_drivers/ -v --tb=short && echo "✅ Driver tests" | tee -a /tmp/stage3-validation.txt

# === 7. Routing System ===
echo "=== Routing System Test ===" | tee -a /tmp/stage3-validation.txt
python -c "
from routing.engine import RoutingEngine
engine = RoutingEngine()
print('✅ Routing engine loads')
" | tee -a /tmp/stage3-validation.txt

# === 8. Error Handling ===
echo "=== Error Handling ===" | tee -a /tmp/stage3-validation.txt
python -c "
from error_handler import ErrorHandler
from error_classifier import ErrorClassifier
print('✅ Error system imports')
" | tee -a /tmp/stage3-validation.txt

# === 9. Full Smoke Test Matrix (from Core Cleanup Plan Appendix) ===
echo "=== Full Smoke Test Matrix ===" | tee -a /tmp/stage3-validation.txt
# Refer to Core Cleanup Plan Section 3.4 for complete matrix
```

**Regression Test with Regression Harness (if available) / 使用回归测试工具进行回归测试（如可用）:**

```bash
# If Task-002 Regression Test Harness is available
if [ -f scripts/run_regression_suite.py ]; then
    echo "=== Running Full Regression Suite ===" | tee -a /tmp/stage3-validation.txt
    python scripts/run_regression_suite.py --mode full && echo "✅ Full regression passed" | tee -a /tmp/stage3-validation.txt
fi
```

**Go/No-Go Decision Criteria / 通过/不通过决策标准:**

**✅ GO (Complete Stage 3) IF / 如果满足以下条件则完成:**
- [ ] ALL core imports successful / 所有核心导入成功
- [ ] ALL CLI commands functional / 所有CLI命令功能正常
- [ ] ALL parsers working (WeChat, Xiaohongshu, Generic) / 所有解析器工作（微信、小红书、通用）
- [ ] Integration tests: ALL PASSING / 集成测试：全部通过
- [ ] Selenium tests: ALL PASSING / Selenium测试：全部通过
- [ ] Driver tests: ALL PASSING / 驱动测试：全部通过
- [ ] Routing system operational / 路由系统运行正常
- [ ] Error handling intact / 错误处理完整
- [ ] (Optional) Regression harness: ALL PASSING / （可选）回归测试工具：全部通过

**❌ NO-GO (Rollback Stage 3) IF / 如果出现以下情况则回滚:**
- Any parser fails / 任何解析器失败
- Integration tests fail / 集成测试失败
- Routing errors detected / 检测到路由错误
- Critical functionality broken / 关键功能损坏

**Rollback Procedure (if needed) / 回滚程序（如需要）:**
```bash
# Option 1: Restore parser_engine from archive
cp -r ARCHIVE/parser_engine/ .
git add parser_engine/
git commit -m "revert: Restore parser_engine from archive (rollback Stage 3)"

# Option 2: Full rollback to Stage 2 completion
git log --oneline | grep "Stage 2 Complete"
git reset --hard <stage-2-complete-commit>
rm -rf ARCHIVE/  # Clean up archive directory

# Option 3: Hard reset to pre-Stage-3
git log --oneline | head -10
git reset --hard <commit-before-stage-3>
git clean -fd
```

**Stage 3 Completion Commit / 阶段3完成提交:**
```bash
git commit --allow-empty -m "milestone: Stage 3 Complete - parser_engine Archived ✅

Summary:
- Conducted dependency analysis: NO imports found ✅
- Created ARCHIVE structure with documentation
- Moved parser_engine/ (~30 files) to ARCHIVE/parser_engine/
- Created restoration instructions in ARCHIVE/README.md

Total removed in Stage 3: ~30 files
Cumulative removal: ~67 files (~40% of original codebase)

Full Validation Results:
✅ All core imports successful
✅ All CLI commands functional
✅ WeChat parser: WORKING
✅ Xiaohongshu parser: WORKING
✅ Generic parser: WORKING
✅ Integration tests: ALL PASSING
✅ Selenium tests: ALL PASSING
✅ Driver tests: ALL PASSING
✅ Routing system: OPERATIONAL
✅ Error handling: INTACT

Cleanup Complete: 3/3 stages ✅
Next: Final verification and merge to main"
```

---

## Phase 4: Final Verification & Completion / 阶段4：最终验证与完成

### Milestone 4.1: Comprehensive Post-Cleanup Verification / 里程碑4.1：全面清理后验证

**Duration / 时长:** 30 minutes / 30分钟

**Objective / 目标:** Final comprehensive check before merging to main.

**Execution Commands / 执行命令:**

```bash
# 1. Compare file counts
echo "=== File Count Comparison ===" | tee /tmp/final-verification.txt
echo "Before: $(cat /tmp/pre-pruning-file-count.txt)" | tee -a /tmp/final-verification.txt
echo "After: $(find . -type f -name '*.py' | wc -l)" | tee -a /tmp/final-verification.txt

# 2. Compare repository size
echo "=== Repository Size Comparison ===" | tee -a /tmp/final-verification.txt
echo "Before: $(cat /tmp/pre-pruning-size.txt)" | tee -a /tmp/final-verification.txt
echo "After: $(du -sh .)" | tee -a /tmp/final-verification.txt

# 3. Git status check
echo "=== Git Status ===" | tee -a /tmp/final-verification.txt
git status --short | tee -a /tmp/final-verification.txt

# 4. Commit history review
echo "=== Commit History ===" | tee -a /tmp/final-verification.txt
git log --oneline | head -20 | tee -a /tmp/final-verification.txt

# 5. Final smoke test
echo "=== Final Smoke Test ===" | tee -a /tmp/final-verification.txt
wf --help >/dev/null && echo "✅ wf --help" | tee -a /tmp/final-verification.txt
wf "https://example.com" >/dev/null && echo "✅ Basic fetch" | tee -a /tmp/final-verification.txt
python -m pytest tests/test_integration_simple.py -q && echo "✅ Integration tests" | tee -a /tmp/final-verification.txt
```

**Success Metrics / 成功指标:**
- File count reduced by ~65-80 files (40% reduction) / 文件数减少约65-80个（40%减少）
- Repository size reduced / 仓库大小减少
- Git commits clean and documented / Git提交干净且有文档
- All smoke tests passing / 所有冒烟测试通过

### Milestone 4.2: Generate Completion Report / 里程碑4.2：生成完成报告

**Duration / 时长:** 20 minutes / 20分钟

**Objective / 目标:** Create comprehensive completion report documenting all changes.

**Execution Commands / 执行命令:**

```bash
# Create completion report
cat > TASKS/task-3-COMPLETION-REPORT.md <<'EOF'
# Task-3 Completion Report / Task-3完成报告
# Core Module Pruning - Execution / 核心模块精简 - 执行

**Completion Date / 完成日期:** $(date +%Y-%m-%d)
**Execution Branch / 执行分支:** task-3-core-module-pruning
**Final Commit / 最终提交:** $(git rev-parse HEAD)

## Executive Summary / 执行摘要

Successfully executed 3-stage core module pruning, reducing codebase by ~40% while maintaining 100% functional integrity.

成功执行3阶段核心模块精简，减少约40%代码量，同时保持100%功能完整性。

## Stage Results / 阶段结果

### Stage 1: Safe Deletions ✅
- Log files deleted: 6
- Directories deleted: 2 (benchmarks/, test_artifacts/)
- Test files deleted: 14
- **Total: ~25 files**
- Validation: ALL PASSED ✅

### Stage 2: Medium-Risk Deletions ✅
- Diagnostics directory deleted: 1 (5 files)
- Historical reports archived: 7
- Test files deleted: 2
- **Total: ~12 files**
- Validation: ALL PASSED ✅

### Stage 3: Archive parser_engine ✅
- Directories archived: 1 (parser_engine/, ~30 files)
- Archive documentation created
- **Total: ~30 files**
- Validation: ALL PASSED ✅

## Cumulative Impact / 累计影响

**Files Removed/Archived:** ~67 files
**Percentage Reduction:** ~40%
**Repository Size Reduction:** $(calculate from metrics)
**Functional Impact:** ZERO ✅

## Validation Summary / 验证摘要

All validation gates passed:
所有验证关卡通过：

- ✅ CLI tools functional (wf, webfetcher.py)
- ✅ All parsers working (WeChat, Xiaohongshu, Generic)
- ✅ Integration tests: 100% passing
- ✅ Selenium tests: 100% passing
- ✅ Driver tests: 100% passing
- ✅ Routing system: operational
- ✅ Error handling: intact
- ✅ No regressions detected

## Archive Locations / 归档位置

- parser_engine/ → ARCHIVE/parser_engine/
- Historical reports → docs/archive/historical-reports/

## Git Commits / Git提交

$(git log --oneline task-3-core-module-pruning | head -20)

## References / 参考

- Planning: docs/Core-Cleanup-Plan.md
- Execution Task: TASKS/task-3-core-module-pruning-execution.md
- Original Planning: TASKS/task-2-core-module-pruning.md

**Status / 状态:** COMPLETE ✅
**Grade / 评级:** A (Pending Review)
**Production Ready / 生产就绪:** YES ✅
EOF

# Generate detailed change log
git log task-3-core-module-pruning --oneline --decorate > /tmp/task-3-changelog.txt
```

### Milestone 4.3: Update Documentation / 里程碑4.3：更新文档

**Duration / 时长:** 15 minutes / 15分钟

**Objective / 目标:** Update README and TASKS documentation to reflect completed pruning.

**Files to Update / 更新文件:**
- README.md (if applicable)
- TASKS/README.md
- TASKS/task-2-core-module-pruning.md (update status)
- TASKS/task-3-core-module-pruning-execution.md (mark complete)

**Execution:**
- Update task status to COMPLETED
- Add completion date
- Reference completion report
- Update project structure diagrams if present

### Milestone 4.4: Prepare for Merge / 里程碑4.4：准备合并

**Duration / 时长:** 10 minutes / 10分钟

**Objective / 目标:** Prepare branch for merge to main.

**Execution Commands / 执行命令:**

```bash
# 1. Final commit on branch
git add -A
git commit -m "docs: Task-3 completion documentation

- Created comprehensive completion report
- Updated TASKS documentation
- Marked task-3-core-module-pruning-execution.md as COMPLETE

All 3 stages completed successfully:
✅ Stage 1: Safe deletions (~25 files)
✅ Stage 2: Medium-risk deletions (~12 files)
✅ Stage 3: Archive parser_engine (~30 files)

Total impact: ~67 files removed/archived (~40% reduction)
Validation: 100% functional integrity maintained

Ready for merge to main"

# 2. Push to remote (if applicable)
git push origin task-3-core-module-pruning

# 3. Prepare for merge
git checkout main
git pull origin main

# Note: DO NOT merge yet - wait for user approval
# 注意：不要立即合并 - 等待用户批准
```

---

## Success Criteria / 验收标准

Task-3 is considered complete when ALL of the following are met:
当满足以下所有条件时，Task-3被视为完成：

### Functional Criteria / 功能标准
- [ ] All CLI commands functional (wf, webfetcher.py, diagnose)
- [ ] All parsers operational (WeChat, Xiaohongshu, Generic)
- [ ] All fallback chains intact (urllib → Selenium → Manual Chrome)
- [ ] All integration tests passing (test_integration_simple.py)
- [ ] All selenium tests passing (test_selenium_integration.py)
- [ ] All driver tests passing (tests/test_drivers/)
- [ ] Routing system operational
- [ ] Error handling system intact
- [ ] No import errors detected
- [ ] No functional regressions

### Cleanup Criteria / 清理标准
- [ ] ~67 files removed/archived (~40% of codebase)
- [ ] benchmarks/ directory deleted
- [ ] diagnostics/ directory deleted
- [ ] test_artifacts/ directory deleted
- [ ] 18 experimental test files deleted
- [ ] 6 log files deleted
- [ ] 7 historical reports archived
- [ ] parser_engine/ archived with documentation
- [ ] ARCHIVE/ structure created with README

### Documentation Criteria / 文档标准
- [ ] Completion report created (TASKS/task-3-COMPLETION-REPORT.md)
- [ ] All git commits properly documented
- [ ] ARCHIVE/README.md created with restoration instructions
- [ ] Task status updated in TASKS/README.md
- [ ] task-3-core-module-pruning-execution.md marked COMPLETE

### Safety Criteria / 安全标准
- [ ] All changes on dedicated branch (task-3-core-module-pruning)
- [ ] All validation gates passed
- [ ] Rollback procedures documented and tested
- [ ] Baseline state preserved in /tmp/pre-pruning-*.txt
- [ ] No data loss occurred

---

## Risks & Mitigations / 风险与缓解

Reference Core Cleanup Plan Section 3.2 for full risk matrix.
参考Core Cleanup Plan第3.2节获取完整风险矩阵。

**Key Risks / 关键风险:**
1. Hidden import dependency → Mitigated by comprehensive grep analysis
2. Dynamic import (not detectable) → Mitigated by full smoke test coverage
3. Test regression failure → Mitigated by validation gates at each stage
4. parser_engine future dependency → Mitigated by archiving (not deleting)

---

## Rollback Procedures / 回滚程序

### Full Rollback / 完全回滚
```bash
# Return to main branch and delete execution branch
git checkout main
git branch -D task-3-core-module-pruning

# All changes discarded, project returns to pre-execution state
```

### Stage-Specific Rollback / 阶段特定回滚

**Rollback to Stage 2 (undo Stage 3):**
```bash
git log --oneline | grep "Stage 2 Complete"
git reset --hard <stage-2-commit-hash>
```

**Rollback to Stage 1 (undo Stages 2 & 3):**
```bash
git log --oneline | grep "Stage 1 Complete"
git reset --hard <stage-1-commit-hash>
```

**Rollback entire task:**
```bash
git log --oneline | grep "Begin Task-3"
git reset --hard <begin-task-3-commit-hash>
git clean -fd
```

### Restore Specific Archive / 恢复特定归档

**Restore parser_engine:**
```bash
cp -r ARCHIVE/parser_engine/ .
git add parser_engine/
git commit -m "restore: Bring back parser_engine from archive"
```

---

## Notes / 备注

- This task is EXECUTION ONLY - no new feature development
- All deletions are based on approved Core Cleanup Plan
- Validation is mandatory at each stage - DO NOT skip
- When in doubt, err on side of caution (archive instead of delete)
- Keep user informed of progress at each milestone
- Request approval before merging to main

本任务仅为执行 - 不涉及新功能开发
所有删除均基于已批准的核心清理计划
每个阶段的验证是强制性的 - 不要跳过
如有疑问，采取谨慎态度（归档而非删除）
在每个里程碑保持用户知情
合并到main前请求批准

---

## See Also / 另见

- Planning Document: `docs/Core-Cleanup-Plan.md`
- Original Task: `TASKS/task-2-core-module-pruning.md`
- Project Management: `TASKS/PROJECT-MANAGEMENT-REPORT-2025-10-10.md`

---

**Document Version / 文档版本:** 1.0
**Created / 创建日期:** 2025-10-10
**Status / 状态:** READY FOR EXECUTION ✅
**Requires User Approval / 需要用户批准:** YES / 是
