# 项目记忆 — Web_Fetcher

## 会话记录

### 2026-04-03 12:15:00 (会话ID: k7m2)

#### ✅ 完成

- **Config-driven routing 降级链修复**（v1.3.1, `9850116`）— CDP/Selenium 路由验证失败后现在正确调用 `_try_fallback_for_invalid_content()` 降级到 manual_chrome，通过 `tried_fetchers` 防止重复尝试
- **路由配置注释增强** — routing.yaml 顶部新增降级链说明（urllib→CDP→manual_chrome），微信和小红书规则标注实际降级路径和已知风控状态
- **三份 routing.yaml 同步** — 运行时（~/.config/webfetcher/）、源码（src/webfetcher/config/）、项目根（config/）三份配置统一
- **Superpower Chain Pipeline A 完整执行** — A1问题记录→A2分析→A3评审（3专家全🔴确认）→A4修复方案→A5实施评审（2专家全🟢）→A6实施→A7版本bump→A8归档

#### ⏸️ 未完成

- 小红书采集仍依赖 manual_chrome（用户本地已登录 Chrome），当前环境 manual_chrome helper 未配置，降级链触发但跳过
- wf 尚无连接用户已运行 Chrome（debug 端口模式）的能力，需要新功能开发

#### ⚠️ 问题

- 小红书 IP 风控（error_code=300012）持续生效，headless Chrome 被拦截，需用户浏览器登录态
- manual_chrome helper 依赖 Selenium 连接用户 Chrome debug 端口，当前环境未安装/配置

#### 💡 备注

- 通过 Claude-in-Chrome 连接用户本地 Chrome 可成功采集小红书内容（验证了登录态+cookie 绕过风控的可行性）
- Surge 代理配置：系统 HTTP proxy 开启（127.0.0.1:6152），增强模式（TUN）已启用，FINAL 规则走 Proxy，小红书无专用规则
- 容错专家评审发现关键约束：修复时必须传入 tried_fetchers 防止 fallback_chain 重复调用已失败的 fetcher

### 2026-04-01 14:30:00 (会话ID: w8f2)

#### ✅ 完成

- **Headless Chrome 自动启动**（v1.1.0, `274c6f9`）— 新建 `headless_manager.py`，CDP 无 Chrome 时自动启动 `--headless=new` 后台 Chrome，atexit+signal 自动清理，PID 文件跨次复用，CLI `--headless` 参数(auto/always/never)
- **采集日志系统**（v1.2.0, `cc8ead2`）— `persist_fetch_success()` 记录每次成功采集到 `~/.wf/fetch_history.jsonl`，新增 `wf stats` CLI 命令（成功率/fetcher 占比/热门域名/耗时/headless 统计）
- **--lite 资源拦截加速**（v1.3.0, `13fd2a8`）— CDP Fetch domain 拦截 image/CSS/font/media HTTP 下载，图片 URL 保留在 HTML 中，Markdown 输出不受影响，Fetch Metrics 新增 Mode/Resources Blocked 字段
- **域名路由表扩展**（`ddece9b`）— routing.yaml 从 7→13 条规则，新增微信/知乎/掘金/B站/大众点评/字节跳动→CDP 直连，跳过 urllib 无效尝试省 2-5s
- **降级链简化**（`71c8dac`）— auto 模式从 urllib→Playwright→CDP→Selenium→manual_chrome 简化为 urllib→CDP→manual_chrome，去掉能力重叠的 Playwright/Selenium 中间层
- **help 文本更新**（`63e4909`, `67617ab`）— wf help 新增 --lite 说明、降级链更新、--headless 参数、路由表说明
- **my-cli-tools skill 更新** — 新增 --lite 模式选择指南、自动路由说明、wf stats 命令、去掉过时的降级建议
- **pipx 修复** — 修复了 pipx broken symlink（python3.13 路径变更），重新通过 brew 安装 pipx

#### 📋 计划

（无）

#### ⏸️ 未完成

- `wf learn` 增强（读取成功日志优化路由建议）— P2，数据积累后再做
- 超时容错（超时也取已有内容）— P2，可独立实施

#### ⚠️ 问题

- 小红书 IP 被风控（`IP存在风险`），与代码改动无关，需要切换网络或等待解除
- `core.py` 中仍有大量硬编码域名判断（微信 UA、下载资源、解析器选择），理想状态是全部迁移到配置驱动，但改动量大，暂不动

#### 💡 备注

- 版本从 1.0.0 → 1.3.0，三次 minor bump
- 所有改动通过 superpower chain 流程（需求评审/设计探索/代码实施/验证）
- CDP 拦截关键发现：拦截 HTTP 请求不影响 HTML 属性，图片 URL 保留在 DOM 中
- Playwright 和 CDP 底层都是 Chrome DevTools Protocol，能力完全重叠，auto 模式不再需要 Playwright
- routing.yaml 是运行时配置（~/.config/webfetcher/routing.yaml），需同步到源码（src/webfetcher/config/routing.yaml）

### 2026-02-14 09:30:22 (会话ID: 74gw)

#### ✅ 完成

- **续接上一会话收尾** — 完成项目记忆保存的 git commit（`3c2627c`），清理临时 session 文件

#### 📋 计划

（无）

#### ⏸️ 未完成

（无）

#### ⚠️ 问题

（无）

#### 💡 备注

- 本会话为上一会话（9yem）的延续，仅完成了遗留的记忆提交任务
- 上一会话的主要工作已记录在 9yem 中（trafilatura 替代、开源修复、WeChat 反爬+图集+格式清理）

### 2026-02-13 23:52:18 (会话ID: 9yem)

#### ✅ 完成

- **trafilatura 替代 CSS 选择器堆砌** — 通用解析器重构
  - `pyproject.toml`: 添加 `trafilatura>=2.0.0` 依赖
  - `generic.yaml`: 从 685 行精简到 96 行，删除 50+ 内容选择器和无代码消费段（cms_patterns, post_process, exclude_patterns, quality, strategies, performance, output）
  - `templates.py:generic_to_markdown()`: 三级 fallback — site 模板 → trafilatura `bare_extraction(as_dict=True)` → legacy
  - 提取 `_build_generic_output()` 公共 helper 消除重复
  - 注意：trafilatura 2.0 `bare_extraction` 默认返回 Document 对象而非 dict，需 `as_dict=True`

- **开源就绪修复**
  - 新增 MIT LICENSE 文件（与 pyproject.toml 声明一致）
  - `core.py:414-415` docstring 示例路径 `/Users/name/` → `/tmp/`
  - `tests/compare_urllib_cdp.py:316` 默认路径改为 `./output`
  - 开源扫描 Verdict: PASS ✓（0 issues）

- **WeChat 反爬检测 + CDP 自动回退**
  - 新增 `AntiBotDetectedError` 异常类
  - `_detect_wechat_antibot()`: 检测"环境异常"反爬页和无 `js_content` 的 JS 渲染页
  - `core.py` 解析阶段捕获异常 → 自动 CDP 重新采集（wait_time=5s）
  - `parser.py` 透传 `AntiBotDetectedError`

- **WeChat 图集文章图片提取**
  - `_extract_wechat_gallery_images()`: 从 `<div data-src>` 和 CSS `background-image` 提取 mmbiz 图片
  - `wechat_to_markdown()` 将图片嵌入 markdown 输出

- **WeChat 输出格式清理**
  - `_clean_wechat_content()`: 过滤赞赏弹窗、数字键盘、重复标题等 UI 噪音
  - 图集文章（`js_image_content`）丢弃无意义文本，只保留图片
  - 无发布时间时不输出空行

#### 📋 计划

（无）

#### ⏸️ 未完成

（无）

#### ⚠️ 问题

- WeChat 图集文章"作者"字段实际提取到的是地区标签（如"辽宁"），非真实作者名。属于数据源限制。
- WeChat 反爬拦截是间歇性的，同一 URL 有时 urllib 能通过有时不行。

#### 💡 备注

- 修改文件：`pyproject.toml`, `generic.yaml`, `templates.py`, `core.py`, `parser.py`, `LICENSE`, `tests/compare_urllib_cdp.py`
- 4 个 commit: c172f7a, 5e32c0f, 65e5a9e, fc7c95e — 全部已推送到 GitHub

### 2026-02-10 10:17:04 (会话ID: jdn1)

#### ✅ 完成

- **`wf --stdout` 功能实现** — 为 `wf` 命令添加 `--stdout` 参数，使 markdown 内容直接输出到 stdout，跳过文件写入
  - `core.py`: 添加 `--stdout` argparse 参数，条件跳过 `outdir.mkdir()`
  - `core.py`: 爬虫模式和单页模式在 `insert_dual_url_section()` 后插入 stdout 输出并 return
  - `core.py`: 三处失败报告路径增加 stdout 分支（fetch failed / selenium error / generic exception）
  - `core.py`: stdout 模式跳过二进制文件下载（`SimpleDownloader`）和 HTML snapshot 保存
  - `cli.py`: 在模式分发前提取 `--stdout` 标志（位置灵活，支持 `wf --stdout URL` 和 `wf URL --stdout`）
  - `cli.py`: 所有模式分支（default/fast/full/raw/site/fallthrough）条件跳过 `ensure_output_dir()` 并传递 `--stdout`
  - `cli.py`: batch 模式拒绝 `--stdout`（输出错误信息到 stderr）
  - `cli.py`: 更新 `print_help()` 添加 Stdout模式说明
  - `pipx install -e . --force` 更新本地命令
  - 验证通过：`wf example.com --stdout`、`wf --stdout example.com`、`wf fast example.com --stdout`、batch 拒绝

#### 📋 计划

（无）

#### ⏸️ 未完成

（无）

#### ⚠️ 问题

- 模板加载警告（qcc_com template.yaml 的 version 字段类型问题）会输出到 stdout 而非 stderr，在 `--stdout` 管道使用时可能混入内容。这是已有问题，非本次引入。需后续排查 Python warnings 模块输出目标。

#### 💡 备注

- `--stdout` 设计思路参考 `macocr --stdout`，让 Claude Code 能直接读取 wf 输出而无需再读文件
- 修改涉及 `core.py`（~7 处）和 `cli.py`（~10 处），改动集中在输出路径控制
