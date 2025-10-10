# Task 1: Config-Driven Routing System / 配置驱动路由系统

## Status / 状态
- Ready to build / 待开发

## Priority / 优先级
- P1 – Core crawling reliability / 核心保障优先级

## Estimated Effort / 预计工时
- 5 hours / 5小时

## Overview / 概述
- Move hard-coded fetcher routing rules out of `webfetcher.py` into a declarative YAML file so crawl strategies can be tuned without touching code, ensuring problematic站点能快速切换抓取方案。/ 将 `webfetcher.py` 中硬编码的抓取路由迁移到声明式 YAML 配置，确保遇到问题站点时可以无需改代码快速调整策略。

## Objectives / 关键目标
- Layered rule evaluation covering domain、URL 模式、内容特征，输出首选抓取器（urllib / selenium / manual_chrome）。
- Hot reload & validation pipeline to安全加载配置变更，避免意外中断抓取。
- Rule-level overrides for手动 Chrome 兜底，使特定站点可直接切换人工模式。
- Clear logging + dry-run CLI 帮助验证配置，保证每条规则可追踪。

## In Scope / 工作范围
- 定义 `config/routing.yaml` 结构（版本号、全局设置、规则列表）。
- 实现 `routing` 服务：优先级队列、条件匹配、缓存，提供同步 API。
- CLI 工具：`scripts/routing_ctl.py`，支持 lint / dry-run / reload。
- 修改 `webfetcher.py` 接入路由服务，保持原有回退链结构。

## Out of Scope / 非范围事项
- 不实现 Web UI 或远程配置中心。
- 不引入复杂实验 / A-B 测试机制，本迭代仅支持确定性规则。

## Dependencies / 依赖
- 仅依赖现有的错误分类缓存与日志体系；无其他任务前置。 / Uses current error cache & logging only; no other task prerequisites.

## Risks & Mitigations / 风险与缓解
- 配置书写错误 → 通过 JSON Schema 校验 + dry-run 模式提前拦截。
- 热重载竞争 → 使用读写锁或原子引用切换避免请求阻塞。
- 规则覆盖度不足 → 提供命中统计日志帮助迭代规则。

## Success Criteria / 验收标准
- 每次路由决策耗时 <5ms（带缓存）。
- 配置变更热加载 ≤2s 生效且不中断在途抓取。
- 至少 3 个示例站点（银行 / JS 站 / 静态站）通过自动化测试验证路由结果。
- CLI dry-run 能输出命中规则与最终抓取器，便于人工确认。

## Milestones / 里程碑
1. 完成配置 Schema 与校验工具（1.5h）。
2. 路由引擎 + 单元测试落地（2h）。
3. 与 `webfetcher.py` 集成及 CLI 发布（1.5h）。

## Notes / 备注
- 配置文件需双语注释，方便后续扩展；上线前在本地针对高风险域名手动验证。/ Add bilingual comments in config and manually verify high-risk domains locally before rollout.
