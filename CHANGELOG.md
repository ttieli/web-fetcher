# Changelog

All notable changes to this project will be documented in this file.

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
