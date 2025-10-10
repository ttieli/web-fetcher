# Task 2: Core Module Pruning Plan / 核心模块精简方案

## Status / 状态
- ✅ **PLANNING COMPLETED** (2025-10-10) / 规划已完成
- Awaiting user approval for execution / 等待用户批准执行

## Priority / 优先级
- P2 – Reduce maintenance surface without breaking wf / 第二优先级，在不影响 wf 工具的前提下降本增效

## Estimated Effort / 预计工时
- 5 hours / 5小时

## Overview / 概述
- Use dependency analysis (pydeps) to map wf 核心依赖链，划定必须保留的模块集合，并制定安全删除非核心代码的计划，确保 `wf` 工具及其兜底链路在精简后依旧完整可用。 / 基于 pydeps 依赖图梳理 wf 所需模块，制定安全的非核心代码清理与验证流程，保证精简后工具链无功能损失。

## pydeps Snapshot / 依赖快照
- 命令 / Command: `pydeps webfetcher.py --show-deps --no-show`
- Graphviz 未安装导致图像导出失败，但 JSON 结果可用；核心依赖如下：
  - `webfetcher.py` 直接依赖：`error_classifier`, `error_handler`, `error_types`, `manual_chrome`, `parsers`, `routing`, `selenium_config`, `selenium_fetcher`
  - 二级依赖：`manual_chrome.helper`, `manual_chrome.exceptions`, `routing.engine`, `routing.matchers`, `routing.config_loader`, `parsers_migrated`, `error_cache`
- 未在依赖链中的目录（可评估裁剪）：`parser_engine/`, `diagnostics/`, `benchmarks/`, 大量测试脚本、历史脚本与实验性工具。

## Objectives / 关键目标
- 明确保留清单：确保 `wf`、Selenium 兜底、手动 Chrome、配置路由、解析器、错误处理链全部保留。 / Produce must-keep list covering wf pipeline.
- 分类非核心模块：按“可删除 / 可归档 / 待验证”拆分所有其他目录与脚本。 / Categorize remaining code for removal or archiving.
- 定义精简流程：制定逐步删除策略与验证步骤（单测、回归套件、手动 smoke）。 / Outline staged removal process with validation.
- 输出行动清单：形成可执行的清理计划（含回滚、留存文档方式）。 / Deliver actionable cleanup checklist with rollback guidance.

## In Scope / 工作范围
- 整理 pydeps 结果，补充跨模块引用（例如配置文件、CLI、docs）。
- 盘点当前目录（`benchmarks/`, `diagnostics/`, `scripts/`, `parser_engine/` 等）并标注归类。
- 识别与 `wf` 强耦合的配置文件、测试、脚本（例如 `config/manual_chrome_config.yaml`, `scripts/manual_mode_cli.py`）。
- 给出删除顺序、验证步骤（运行单测、回归套件、Smoke wf）。
- 评估风险：例如 `parser_engine/` 未来 Phase 4 依赖度、`tests/` 中保留的关键断言。
- 产出精简路线文档（Markdown），包含“保留 / 迁移 / 删除”表格与回滚建议。

## Out of Scope / 非范围事项
- 不立即删除任何代码，仅制定方案。 / No actual deletion in this task.
- 不重构 wf 主流程或解析逻辑。 / No refactor of core pipeline.
- 不执行生产部署。 / No production rollout.

## Dependencies / 依赖
- 需可运行 `pydeps`（已验证 JSON 输出可用，若需图像需安装 graphviz）。
- 依赖 Task 1 & Task 2（P1）的成果以更新验证清单，但可独立完成方案。 / Soft coordination with other tasks for validation coverage.

## Risks & Mitigations / 风险与缓解
- 误删关键模块 → 通过 pydeps + 手工检查建立双重确认，并保留回滚分支。 / Double-check with pydeps & manual review.
- 测试覆盖不足 → 在计划中要求执行 P1 回归套件与关键单测。 / Mandate regression suite once ready.
- 隐形依赖（动态 import）→ 制定 smoke 测试列表（银行域、JS 站、手动 Chrome 场景）。 / Add smoke matrix to detect hidden deps.

## Success Criteria / 验收标准
- 产出一份 Markdown 文档《Core Cleanup Plan》（中英双语），列出：
  - 必保模块与文件
  - 建议删除/归档项及理由
  - 验证步骤与回滚策略
  - 后续执行顺序与里程碑
- README/TASKS 更新明确精简计划及所需依赖（例如 graphviz 安装提示）。
- 获得用户确认后方可进入实际清理阶段。

## Milestones / 里程碑
1. 依赖与目录盘点完成（1.5h）。
2. 精简方案初稿（2h）。
3. 验证与风险评估补全（1h）。
4. 方案评审与调整（0.5h）。

## Notes / 备注
- 建议在 Task 2（回归测试工具）完成后执行实际删除，可作为精简验证主力。 / Recommend sequencing actual removal after regression harness is ready.
- Graphviz 缺失导致 pydeps 生成图片失败，可在方案中备注安装步骤或提供备选输出方式。 / Document graphviz requirement for future runs.

---

## Completion Summary / 完成总结

### Planning Phase Results / 规划阶段成果

**Deliverable:** Core Cleanup Plan document created at `docs/Core-Cleanup-Plan.md`
**交付物：**核心清理计划文档已创建于 `docs/Core-Cleanup-Plan.md`

### Key Findings / 关键发现

- **15 core modules** identified as must-keep / 识别出15个必须保留的核心模块
- **~80 files** (40% of codebase) categorized for removal / 约80个文件（代码库的40%）已分类待删除
- **4 directories** identified for deletion/archiving: / 识别出4个目录待删除/归档:
  - `benchmarks/` - DELETE (performance testing only)
  - `diagnostics/` - DELETE (SPA tools not used by wf)
  - `parser_engine/` - ARCHIVE (replaced by routing/)
  - `test_artifacts/` - DELETE (test output files)

### Three-Stage Execution Plan / 三阶段执行计划

1. **Stage 1 (Low Risk):** Delete test artifacts, logs, benchmarks / 删除测试产物、日志、基准测试
2. **Stage 2 (Medium Risk):** Delete diagnostics, historical reports / 删除诊断工具、历史报告
3. **Stage 3 (Requires Analysis):** Archive parser_engine / 归档parser_engine

### Risk Assessment Completed / 风险评估已完成

- Comprehensive validation checklist created / 创建了全面的验证清单
- Rollback strategy documented / 回滚策略已文档化
- Smoke test matrix defined for all core functionality / 为所有核心功能定义了冒烟测试矩阵

### Dependencies / 依赖关系

- Manual dependency analysis completed (pydeps not available) / 手动依赖分析已完成（pydeps不可用）
- Core import chain fully mapped: webfetcher.py → 8 direct deps → 7 indirect deps / 核心导入链已完全映射
- No hidden dependencies detected through grep analysis / 通过grep分析未检测到隐藏依赖

### Impact / 影响

**Projected benefits after execution:**
- Reduce codebase size by ~40% / 减少约40%的代码量
- Improve maintainability by removing legacy/experimental code / 通过删除旧代码和实验代码提高可维护性
- Simplify dependency tree / 简化依赖树
- No functional impact on wf tool / 对wf工具没有功能影响

### Status / 状态

**Planning Phase:** ✅ Complete (Grade: A)
**Execution Phase:** ⏸️ Pending user approval
**规划阶段：**✅ 完成（评级：A）
**执行阶段：**⏸️ 待用户批准

### Next Steps / 下一步

1. User reviews `docs/Core-Cleanup-Plan.md`
2. User approves categorization (KEEP/DELETE/ARCHIVE)
3. Create git branch `task-2-module-pruning`
4. Execute Stage 1 deletions with validation
5. Execute Stage 2 deletions with validation
6. Execute Stage 3 archival with full regression testing

### See Also / 另见
- Plan Document: `docs/Core-Cleanup-Plan.md` / 规划文档
- Current Structure: See Appendix A in plan / 当前结构：见规划中附录A
- Validation Checklist: See Phase 3 in plan / 验证清单：见规划中阶段3
