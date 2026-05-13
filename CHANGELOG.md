# Changelog

All notable changes to this project will be documented in this file.

## [1.3.5] - 2026-05-13

### Added — AI agent 友好输出优化（来自 AI agent 使用反馈清单）

- **结构化错误输出**（替代 Python traceback）
  - 新增 `src/webfetcher/errors/user_facing.py` 模块
  - `UserErrorCategory` enum 9 种：URL_INVALID / DNS_FAILURE / SSL_ERROR / HTTP_4XX / HTTP_5XX / TIMEOUT / CDP_LAUNCH_FAILED / CONFIG_ERROR / UNKNOWN
  - `classify_user_error()` 自动从 Python exception 推断分类（按 type + message 正则）
  - `format_user_error()` 输出三段式："错误类型 / 说明 / 建议"
  - cli.py 顶层 try/except 改用结构化输出，默认隐藏 traceback
- **`--debug` 标志**：仅 debug 模式打 Python traceback + DEBUG 级日志（含启动横幅）
- **`-v/--verbose` 标志**（与既有保持一致）：INFO 级日志
- **重试失败终结摘要行**：`format_retry_summary()` 在 fetch_html_with_retry 重试耗尽时打一行 "重试 N 次仍失败，最终错误: <CATEGORY> — <explanation>"，让 AI 在长日志里能 grep 抓结论
- **`wf --help` 增强**：
  - 新增"AI agent 场景速查"段（按场景列命令）
  - 新增"错误输出（AI 友好）"段（说明三段式格式 + 9 种分类）
  - 新增"日志级别"段（默认 / -v / --debug）
  - 新增"陷阱与限制"段（--lite + 图片 / 微信小红书自动路由 / batch + stdout 冲突等）

### Changed

- **启动横幅静默化**：4 处 module-level `logger.info` → `logger.debug`
  - core.py: `"CDP fetcher available"` / `"Config-driven routing system initialized"`
  - routing/config_loader.py: `"Loaded configuration from: ..."`
  - routing/engine.py: `"Compiled N routing rules"`
  - 业务级 logger.info（V2 升级链、短路、路由决策）保持不变，AI 仍能从日志读到关键事件
- **未知错误日志改人类可读**：core.py:1821 内部 `"Error classified as unknown"` 改为 `"未知错误（重试策略分类器未识别），原始: <type>: <msg>; 将按保守策略重试"`
- **环境变量支持**：`WF_DEBUG=1` / `WF_VERBOSE=1` 等价于 CLI flag

### Tests

- 新增 `tests/unit/test_user_errors.py` 18 个用例覆盖 9 种分类 + 格式化 + retry summary

### Verified

- 单元测试：29 个全 PASS
- V2 行为回归：short-circuit 2/2 + spa-stuck 6/6 + fallback-rescue 6/6 = 14/14 PASS
- smoke 回归：fast tag 子集（13 URL）全 PASS

### Note

- CLI 调用方式完全不变；只是错误输出格式更友好 + 日志噪音降低
- 接口完全向后兼容（既有 `--verbose` 仍可用）

## [1.3.4] - 2026-05-13

### Changed
- **公有 repo 准备**：移除 `tests/url_suite.txt` 中 4 个含个人工作查询关键词的搜索引擎 URL（baidu/google/tianyancha/qcc 的 search? URL）
- `scripts/build_regression_suite.py` 新增 `_is_search_query_url()` 隐私过滤：再生成 url_suite.txt 时自动跳过含搜索 query 的 URL，防止泄露查询关键词
- 扩展 `.gitignore`：`sample/`（含真实抓取数据）、`*.backup`、机器特定 Chrome 启动脚本、`.claude/{agents,skills,sessions,archive,project-memory.md,settings.local.json}`（个人 Claude Code 配置不入库）

### Added
- `config/routing_schema.json` 入库（routing.yaml 的 JSON Schema 验证）
- `scripts/{routing_ctl.py,run_regression_suite.py,template_tool.py}` 入库（公共开发工具）

### Note
- 接口完全不变；本机使用无感知
- 准备公有 repo 发布前的最后一次清理

## [1.3.3] - 2026-05-13

### Fixed
- **补提交工作树中长期未入库的核心依赖**（git 状态修复，影响其他机器装 wheel）
  - `src/webfetcher/memory.py` 入库：V2 引擎的 `DomainMemory` + `ExtractionLogger` 核心依赖（`engine_v2.py:92` 一直 import 它）
  - `src/webfetcher/parsing/templates.py` 中 `apply_yaml_frontmatter()` 函数入库：`--frontmatter yaml` CLI 参数的实现（`core.py:159/5418/5769` 一直 import 它）
  - **影响**：之前 1.3.0/1.3.1 的 wheel 在非 editable 安装时缺这两处实际依赖，V2 引擎和 `--frontmatter yaml` 都会 ImportError；本机 editable 安装因为读源码树看不到这个问题

### Changed
- `qcc_com/template.yaml` 中 `version: 1.0` → `"1.0"`，避免 YAML 解析为 float 导致精度截断
- `routing/config_loader.py` 中 schema 文件不存在的日志从 `warning` 降为 `debug`（schema 文件本来就是可选的，不应每次都报警）

### Note
- 调用方接口完全不变（CLI 参数、输出格式、Python API 都无变化）
- 已通过 11 unit tests + V2 fallback verify (short-circuit/spa-stuck/fallback-rescue 各 2/2 + 8/8 + 8/8)

## [1.3.2] - 2026-05-13

### Fixed
- **V2 自动升级 fallback 机制三处缺陷修复**（superpower-chain Pipeline A）

  - **Bug 1**：升级成功判定从 `len(html2) > len(html)` 改为提取 score 比较
    - `new_score >= prev_score` → 接受换 fetcher
    - `new_score >= 0.5` → 才停止升级链
    - 解决 SPA 站点（wgetcloud / tianyancha / interconnects）CDP 长 shell 错误通过判定的问题
    - 文件：`src/webfetcher/core.py:5615-5687`

  - **Bug 2**：质量描述字段（`_v2_quality_low / _v2_score / _v2_current_fetcher`）从 `if quality_low and not _v2_no_upgrade` 块内提取到本地 `v2_state` dict，所有返回路径统一 update
    - 让 core.py 在重抓后能从 metadata 读到真实 score
    - 文件：`src/webfetcher/parsing/engine_v2.py:117-213`

  - **问题 3**：plain-text URL 短路 + `<pre>`-wrapped raw markdown 解包
    - 检测 `.md/.txt/.rst/.markdown` 后缀及 `raw.githubusercontent.com/gist.githubusercontent.com` 路径
    - 解包 raw github 服务端的 `<html><body><pre>...</pre></body></html>` 包裹
    - 新增独立 `score_extraction_plaintext()` helper，主 `score_extraction` 行为不变
    - 文件：`src/webfetcher/parsing/extractors.py`

- **`args._v2_no_upgrade` 状态切换** 用 try/finally 保护，避免 generic_v2 异常时标志位卡在 True
- **版本号一致性** 修复 core.py 中残留的 `__version__ = "1.3.0"` → 与 pyproject.toml / __init__.py 同步为 1.3.2

### Added
- `tests/unit/test_v2_fallback.py` (4 tests) — Bug 1/2 + 防回归
- `tests/unit/test_extractors_plaintext.py` (7 tests) — 短路 + helper + pre 解包 + HTML 实体反转

### Verified
- E2E：raw github CHANGELOG → 短路（无 CDP 调用）
- E2E：carnoc → urllib(0) → cdp(0.75) → break ✓
- E2E：interconnects.ai/archive → urllib → cdp → selenium → manual_chrome（之前永久卡在 cdp）

## [1.3.1] - 2026-04-03

### Fixed
- **Config-driven routing 降级链修复**: CDP/Selenium 路由验证失败后现在正确降级到 manual_chrome，而非直接返回无效内容
  - 修复 `fetch_html_with_retry()` 中 config-driven CDP 分支（原 L1737）和 Selenium 分支（原 L1711）的无条件 return
  - 通过 `tried_fetchers` 参数防止降级链中重复尝试已失败的 fetcher
  - 影响：小红书等被 IP 风控拦截的站点现在可以正确触发 manual_chrome 降级

### Changed
- **路由配置注释增强**: routing.yaml 新增降级链说明，微信和小红书规则标注实际降级路径和已知风控状态

## [1.2.0] - 2026-02-20

### Added
- **YAML Front Matter 输出**: `--frontmatter yaml` 参数，将内嵌元数据转换为标准 YAML front matter 格式
  - 兼容 Hugo / Jekyll / Obsidian 等工具
  - 支持单页模式和爬虫模式
  - 默认行为不变（`--frontmatter none`）

## [1.1.0] - 2025-11-18

### Added
- **Google搜索优化**: 完整的搜索结果提取（含snippet、图片、相关搜索）
- **Snippet提取**: 优化snippet提取逻辑，提供纯净的描述性文字
- **图片展示**: 提取3+张搜索结果图片及缩略图
- **URL格式化**: 所有链接格式化为Markdown超链接
- **项目文档**: 重构README.md，添加徽章、FAQ、贡献指南

### Changed
- 清理output文件夹的测试输出文件
- 整理docs文件夹结构，移除空文件夹
- 移动开发文档到docs/目录

### Fixed
- Google搜索snippet提取过滤条件过严问题
- 文档结构混乱，难以导航问题

## [1.0.0] - 2025-11-17

### Added
- **CDP集成**: 完整的Chrome DevTools Protocol支持
- **三级回退**: urllib → CDP → Selenium智能回退机制
- **模块化重组**: 清晰的项目结构
- **一键部署**: bootstrap.sh/ps1自动安装脚本
- **智能路由**: 基于域名和内容类型的自动路由

### Features
- 微信公众号内容提取
- 小红书图文内容提取
- Wikipedia多语言支持
- 通用网站自动适配
- YAML模板系统

## [0.9.0] - Initial Release

- 基础网页抓取功能
- Selenium集成
- Markdown输出
