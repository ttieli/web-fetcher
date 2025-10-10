# Task 1: Regression Test Harness / 回归测试工具

## Status / 状态
- Drafted, pending implementation / 已立项，待实施

## Priority / 优先级
- P1 – Safeguard crawl reliability / 一类优先级，保障抓取稳定性

## Estimated Effort / 预计工时
- 6 hours / 6小时

## Overview / 概述
- Build a reusable testing harness that reads an editable plain-text URL list, executes all supported采集方式（urllib、selenium、manual_wf 等），并生成可比对的回归报告，便于每次升级后快速验证功能与优化是否达标。/ 构建可复用的回归测试工具：读取可编辑 TXT 常用网址清单，按多种抓取方式执行测试并输出报告，以保证每次升级后功能无回退、优化可量化。

## Objectives / 关键目标
- Allow user-maintained URL list (`tests/url_suite.txt`) with bilingual instructions. / 支持用户维护的 `tests/url_suite.txt` 双语说明列表。
- Automated runner executes urllib、selenium、manual_wf（必要时跳过人工步骤）等策略。 / 自动化执行 urllib、selenium、manual_wf 等策略。
- Produce markdown/JSON summary comparing响应时间、成功状态、错误信息、HTML 大小等指标。 / 生成 Markdown/JSON 报告对比响应时间、成功状态、错误、HTML 大小。
- Provide CLI commands for全量回归、单站点测试、结果对比基线。 / CLI 支持全量回归、单站点校验与基线对比。

## In Scope / 工作范围
- 新建 `tests/url_suite.txt` 模板与维护指南。 / Create editable URL suite template.
- 实现 `scripts/run_regression_suite.py`（或同等）执行多策略抓取与结果收集。 / Implement regression runner script.
- 报告生成：`reports/regression/YYYYMMDD/` 内输出 Markdown + JSON。 / Generate reports into dated directories.
- 集成 `manual_mode_cli.py` 可选参数，在无交互环境下跳过需人工确认的步骤并标记状态。 / Integrate manual mode optional flag for non-interactive runs.
- 单元/集成测试覆盖：至少验证 URL 解析、报告生成、异常处理路径。 / Add tests covering parsing, reporting, and error handling.

## Out of Scope / 非范围事项
- 不实现 Web UI 或图形化出报告（仅限 CLI + 文件）。 / No web dashboard.
- 不负责真实手动浏览器操作自动化，仅标记手动模式需要人工确认。 / No automation of manual browsing itself.

## Dependencies / 依赖
- 复用现有 `webfetcher.py` 抓取接口、`manual_chrome` 模块、日志体系。 / Depends on current fetcher stack.
- 若使用 pandas 等分析库需提前评估体积；默认仅使用标准库。 / Additional heavy libs discouraged.

## Risks & Mitigations / 风险与缓解
- URL 列表过大导致运行时间长 → 支持分组/筛选执行。 / Add grouping filters.
- 手动模式在无交互环境失败 → 提供 `--skip-manual`、`--mark-pending` 选项并在报告中标注。 / Provide skip flag with reporting.
- 报告难以对比 → 保留历史基线并提供 diff 命令。 / Store baselines for diff.

## Success Criteria / 验收标准
- 支持≥20个 URL 的批量测试，可在≤10分钟内完成（跳过手动站点）。 / Batch run 20 URLs within 10 minutes (manual skipped).
- 报告包含：成功/失败比例、各策略耗时、错误清单、人工介入清单。 / Report details success rate, timings, errors, manual requirements.
- CLI 返回码用于 CI：全部通过返回0，出现回归返回非零。 / CLI exit codes suitable for CI.
- 文档完整：README/帮助信息中英双语说明如何维护 URL 列表与解读报告。 / Documentation bilingual.

## Milestones / 里程碑
1. URL 列表模板 + 文档完成（1h）。
2. 回归运行器开发 + 基础测试（3h）。
3. 报告生成与 CLI 选项完善（1h）。
4. 文档与示例报告交付（1h）。

## Notes / 备注
- 可考虑与 Task 1 路由系统联动，在报告中附带路由决策结果，帮助验证策略。 / Optional tie-in with routing task to log chosen fetcher.
- 首次跑完后保存基线报告，后续升级可自动对比差异。 / Store initial baseline for future comparisons.
