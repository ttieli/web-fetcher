# Task 2: Parser Template Creator Tools / 解析模板创作工具

## Status / 状态
- Phases 1–3 complete, Phase 4 pending / 第1-3阶段已完成，第4阶段待启动

## Priority / 优先级
- P2 – Finish parser modernization / 第二优先级，用于收官解析器现代化

## Estimated Effort / 预计工时
- 3 hours / 3小时

## Overview / 概述
- Provide tooling so new网站模板可以在不改动核心代码的情况下快速生成、校验并发布，保持抓取能力的可持续扩展。/ 构建模板创作工具链，支持无代码方式新增站点解析模板，确保抓取能力持续扩展。

## Current Baseline / 现状基线
- 模板运行时 v2 已部署至 WeChat、XHS、Generic 解析器，测试 100% 通过。
- 平均解析性能 4.05ms/页（247 页/秒），代码结构稳定。
- Phase 4（模板创作工具）仍缺失，新增站点需手写代码。

## Objectives / 关键目标
- CLI 脚手架：生成带元数据的模板骨架（YAML/JSON +占位测试）。
- 校验套件：对比 urllib 与 Selenium 输出，保证解析一致性。
- 预览工具：从本地 HTML 生成 Markdown 预览，辅助迭代。
- 文档生成：输出模板说明（字段、选择器、测试覆盖）。

## Scope / 工作范围
- 新增 `parser_engine/tools/` 模块，包含 CLI、校验、预览、文档组件。
- 补充单元/集成测试，涵盖成功与失败场景。
- 更新开发者指引，描述模板创建与发布流程。

## Dependencies / 依赖
- 仅使用现有模板加载器与 Selenium 测试夹具；无其他任务依赖。/ Depends only on existing template loaders and Selenium fixtures available today.

## Risks & Mitigations / 风险与缓解
- 工具与运行时 Schema 漂移 → 复用共享枚举/常量并加入单测。
- CLI 使用门槛过高 → 提供默认参数与示例模板降低输入成本。
- 校验耗时增加 → 针对大型页面引入采样或缓存策略。

## Success Criteria / 验收标准
- 新模板从生成到上线≤30分钟（含校验与文档）。
- CLI 提供 `init` / `validate` / `preview` / `doc` 四个子命令，帮助信息中英双语。
- 校验流程能输出可执行差异（字段、图片、链接）。
- 文档生成器自动产出 Markdown，并在仓库内留存版本记录。

## Milestones / 里程碑
1. 完成 CLI 脚手架与共享 Schema（1h）。
2. 校验 & 预览流水线 + 测试（1h）。
3. 文档生成器与开发者指南更新（1h）。

## Notes / 备注
- 发布前使用 CEB、小红书、微信样例进行手工试用，确保不同类型站点都能覆盖。/ Before release run manual trials with CEB, Xiaohongshu, WeChat samples to validate coverage.
