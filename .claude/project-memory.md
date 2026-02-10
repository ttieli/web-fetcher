# 项目记忆 — Web_Fetcher

## 会话记录

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
