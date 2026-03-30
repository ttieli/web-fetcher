# Headless Chrome 自动启动支持

> 创建时间：2026-03-30
> 管线：superpower-chain Pipeline B
> 状态：收集中

## 原始需求

当前 wf 使用 CDP 抓取 JS 重度站点（如小红书）时，需要用户手动启动前台 Chrome（config/chrome-debug.sh），Chrome 窗口会一直显示在前台，用完还得手动关闭。用户希望 Chrome 能在后台自动启动，不显示窗口，用完自动关闭。

## 已验证可行性

`--headless=new` 模式的 Chrome + CDP 可正常抓取小红书，内容完整（标题+正文+图片链接）。测试耗时 46s，与前台 Chrome 的 34-57s 相当。

测试命令：
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new \
  --remote-debugging-port=9333 \
  --user-data-dir=/tmp/chrome-headless-test \
  --no-first-run --no-default-browser-check --disable-gpu &
```

## 需求列表

| # | 需求 | 复杂度 | 优先级 | 技术要点 | 批次 |
|---|------|--------|--------|----------|------|
| 1 | CDP 检测不到 Chrome 时自动启动 headless Chrome | M | P1 | 检测端口→启动进程→等待就绪→返回连接 | - |
| 2 | wf 命令结束后自动清理 headless Chrome 进程 | S | P1 | atexit/signal handler, 进程管理 | - |
| 3 | 优先使用已有前台 Chrome debug 实例（端口9222） | S | P1 | 端口检测逻辑前置 | - |
| 4 | 新增 CLI 参数 `--headless` 显式控制 | S | P2 | argparse 新参数, 三态: auto/on/off | - |
| 5 | 使用独立 user-data-dir 避免冲突 | S | P1 | ~/.chrome-wf-headless | - |
| 6 | 向后兼容，不改变现有前台 Chrome 工作方式 | S | P1 | 仅在无 Chrome 时才启动 headless | - |

## 细化记录（B1 填写）

### 技术分析

**现有架构**：
- `CDPFetcher`（`cdp_fetcher.py`）：核心 CDP 抓取器，连接 `127.0.0.1:9222`
- `_try_cdp_fetch()`（`core.py:1895`）：CDP 抓取入口，调用 `ensure_chrome_debug()` 检查 Chrome
- `ensure_chrome_debug()`（`core.py:1150`）：检查 Chrome 是否运行，不可用时调用 `ensure-chrome-debug.sh` 脚本
- `fetch_with_cdp()`（`cdp_fetcher.py:417`）：简化接口，创建 CDPFetcher → fetch → close
- CLI 参数 `--fetch-mode cdp`（`core.py:5073`）：强制 CDP 模式
- 环境变量 `CDP_PORT`：可覆盖默认端口（CDPFetcher 构造函数不读取，但 wf 测试时用过）

**改动策略**：
- 核心改动在 `cdp_fetcher.py`，新增 headless Chrome 管理模块
- `core.py` 中 `_try_cdp_fetch()` 调用 headless 管理器替代 `ensure_chrome_debug()`
- CLI 增加 `--headless` 参数
- 不改 `ensure-chrome-debug.sh`（前台 Chrome 管理脚本）

**端口策略**：
- 优先检测 9222（前台 Chrome）
- 9222 不可用时，启动 headless Chrome 在 9222（复用默认端口，避免端口不一致）
- 如果 9222 被非 Chrome 进程占用，使用备用端口 9333

**进程生命周期**：
- 使用 `atexit` + `signal` handler 确保进程清理
- PID 文件记录在 `~/.chrome-wf-headless/.headless.pid`
- 支持跨次调用复用（如果 headless 还在运行就直接连接）

### 需求更新

| # | 需求 | 复杂度 | 优先级 | 技术要点 | 批次 |
|---|------|--------|--------|----------|------|
| 1 | headless Chrome 启动/检测/复用模块 | M | P1 | HeadlessChromeManager 类，端口检测→启动→等待就绪 | Batch 1 |
| 2 | 进程清理（atexit + signal） | S | P1 | atexit.register, signal.SIGTERM/SIGINT | Batch 1 |
| 3 | 优先使用已有前台 Chrome（9222） | S | P1 | quick_chrome_check 前置 | Batch 1 |
| 4 | 集成到 _try_cdp_fetch 流程 | S | P1 | 替换 ensure_chrome_debug 调用 | Batch 1 |
| 5 | CLI 参数 --headless | S | P2 | 三态: auto(默认)/always/never | Batch 1 |
| 6 | PID 文件管理，支持跨次复用 | S | P2 | ~/.chrome-wf-headless/.headless.pid | Batch 1 |

## 分批计划（B2 填写）

所有需求均为 S/M 级且同优先级范围，合为一个批次：

| 批次 | 优先级 | 包含需求 | 预估工作量 |
|------|--------|----------|-----------|
| Batch 1 | P1-P2 | #1-#6 | M |

## 评审记录（B4）

### Batch 1 需求评审 — 2026-03-30

| 专家 | 总体 | 要点 |
|------|------|------|
| Python系统编程 | 🟡 | #2 进程清理需链式 signal handler 保护；fetch_with_cdp 需 port 参数；start_new_session=True |
| Chrome/CDP | 🟢 | headless=new 与前台 CDP 协议完全兼容；Stealth JS 有效；建议独立模块 headless_manager.py |
| CLI设计 | 🟢 | --headless 与 --render 有命名冲突风险；建议统一 always/never 风格；需明确与 --fetch-mode 交互 |

**关键设计决策（评审共识）**：
1. 新建 `src/webfetcher/fetchers/headless_manager.py`，不在 cdp_fetcher.py 中膨胀
2. `fetch_with_cdp()` 增加 `port` 参数（3位一致，是集成的前置依赖）
3. signal handler 必须保存并链式调用 old_handler，不能覆盖
4. Chrome 启动参数增加 `--disable-dev-shm-usage`、`--disable-software-rasterizer`
5. PID 文件用原子写入（tmp + os.replace）
6. `--headless` 保持此命名，help 文本中明确区分 vs `--render`

**结论**：通过，进入设计方案
