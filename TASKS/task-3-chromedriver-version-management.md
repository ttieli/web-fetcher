# Task 3: ChromeDriver Version Management / ChromeDriver版本管理

## Status / 状态
- Pending execution / 待实施

## Priority / 优先级
- P3 – 保证手动与Selenium兜底可持续 / third priority focused on fallback stability

## Estimated Effort / 预计工时
- 4 hours / 4小时

## Overview / 概述
- 自动检测并同步 Chrome 与 ChromeDriver 版本，避免因版本漂移导致 Selenium 或手动 Chrome 兜底失效。/ Automate Chrome vs ChromeDriver version checks so fallback chains remain可靠。

## Current Pain Point / 当前痛点
- 本地环境已出现 Chrome 141 / chromedriver 140 不匹配，只能依赖调试端口勉强工作。
- 手动更新流程复杂易忘，一旦浏览器自动升级可能立即造成抓取失败。

## Objectives / 关键目标
- 检测 macOS 上已安装的 Chrome 版本与当前 chromedriver 版本。
- 比较主版本差异并输出可操作告警。
- 自动下载并缓存匹配版本（优先使用官方源，可回退到 Selenium Manager）。
- 诊断 CLI：`manual_mode_cli.py --diagnose` 集成版本检测，必要时给出修复建议。

## Scope / 工作范围
- 新增 `drivers/version_manager.py`（或同等模块）封装检测、下载、切换逻辑。
- 实现 `scripts/manage_chromedriver.py` CLI，提供 `check` / `sync` / `doctor` 子命令。
- 编写单测：mock 系统命令、下载流程、错误分支。
- 更新文档说明版本管理流程与常见问题。

## Out of Scope / 非范围事项
- 初版仅支持 macOS；其他平台留在文档中标注限制。
- 不负责管理 Chrome 浏览器升级策略。

## Dependencies / 依赖
- 需要网络访问以拉取驱动（若离线则仅提示手动操作）；除此之外无任务依赖。/ Requires network for downloads; otherwise independent.

## Risks & Mitigations / 风险与缓解
- 下载受限或失败 → 增加重试、校验 SHA256，并提供手动下载指引。
- 无网络场景 → CLI 在离线模式仅报告状态，不尝试下载。
- 自动替换驱动风险 → 使用临时目录 + 原子替换，失败时回滚旧驱动。

## Success Criteria / 验收标准
- CLI `check` 能输出当前版本及兼容性结论，中英双语提示。
- `sync` 成功后将驱动放入 `~/.webfetcher/drivers/<version>/chromedriver` 并更新路径。
- `manual_mode_cli.py --diagnose` 遇到不匹配时以非零状态退出并提供下一步指引。
- 单测覆盖检测、下载成功、下载失败、离线模式等路径。

## Milestones / 里程碑
1. 版本检测与告警实现（1h）。
2. 自动下载 + 缓存管线与测试（2h）。
3. CLI 集成与文档更新（1h）。

## Notes / 备注
- 在替换驱动前先备份旧版本，必要时可通过 `manage_chromedriver.py restore` 命令回滚（可选增强）。/ Optional enhancement: add restore command after initial release.
