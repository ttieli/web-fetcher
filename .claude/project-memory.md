# 项目记忆 — Web_Fetcher

## 会话记录

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
