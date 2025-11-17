# CDP (Chrome DevTools Protocol) 使用指南

## 概述

WebFetcher 现已集成 CDP (Chrome DevTools Protocol) 抓取功能，提供强大的浏览器自动化能力。CDP 直接与 Chrome 浏览器通信，适用于需要复杂交互、保持登录状态或处理高度反爬的网站。

## 功能特性

✅ **复用真实浏览器会话** - 保持登录状态和 cookies
✅ **提取渲染后的 DOM** - 完整的 JavaScript 渲染支持
✅ **执行自定义 JavaScript** - 灵活的页面操作能力
✅ **网络请求监听** - 捕获 API 调用和数据流
✅ **截图功能** - 页面状态可视化
✅ **会话状态导出** - 保存 cookies/localStorage/sessionStorage
✅ **智能回退机制** - urllib 和 Selenium 失败后自动切换

## 快速开始

### 1. 安装依赖

```bash
# 安装 CDP 依赖
pip install webfetcher[cdp]

# 或直接安装 pychrome
pip install pychrome
```

### 2. 启动 Chrome 调试模式

CDP 需要 Chrome 在远程调试模式下运行：

```bash
# 使用提供的脚本启动 Chrome (推荐)
./scripts/start_chrome.sh

# 或手动启动 (macOS)
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome-CDP" &

# Linux
google-chrome --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.config/google-chrome-cdp" &

# Windows (PowerShell)
& "C:\Program Files\Google\Chrome\Application\chrome.exe" `
  --remote-debugging-port=9222 `
  --user-data-dir="$env:LOCALAPPDATA\Google\Chrome\CDP"
```

启动后，Chrome 会在独立的用户数据目录运行，不影响你的正常浏览器。

### 3. 验证 CDP 连接

访问 http://localhost:9222/json 查看调试端口状态，应该能看到 Chrome 的版本信息。

## 使用方法

### 方式 1: 显式使用 CDP 模式

直接使用 CDP 抓取网页（最可靠）：

```bash
# 使用 --use-cdp 快捷参数
wf https://example.com --use-cdp

# 或使用 --fetch-mode cdp
wf https://example.com --fetch-mode cdp

# 自定义超时时间
wf https://example.com --use-cdp --cdp-timeout 60
```

### 方式 2: 自动回退模式 (推荐)

默认的 `auto` 模式会自动尝试 urllib → Selenium → CDP 的回退链：

```bash
# 默认就是 auto 模式
wf https://example.com

# 显式指定 auto
wf https://example.com --fetch-mode auto
```

**回退逻辑：**
1. 首先尝试 urllib (最快)
2. 如果 urllib 失败，尝试 Selenium
3. 如果 Selenium 也失败，最后尝试 CDP
4. 仍然失败则尝试 manual chrome 模式

### 方式 3: 仅 urllib → CDP 回退

跳过 Selenium，直接从 urllib 回退到 CDP：

```bash
# 禁用 Selenium，只用 CDP 作为回退
wf https://example.com --fetch-mode auto
# (当 Selenium 不可用时会自动跳过并使用 CDP)
```

## 使用场景

### 场景 1: 需要登录的网站

CDP 会复用你在 Chrome 中的登录状态：

```bash
# 1. 启动 CDP Chrome
./scripts/start_chrome.sh

# 2. 在打开的 Chrome 窗口中手动登录目标网站
# 3. 使用 CDP 抓取 (会保持登录状态)
wf https://example.com/private-page --use-cdp
```

### 场景 2: 反爬严格的网站

对于检测自动化工具的网站，CDP 使用真实浏览器，更难被检测：

```bash
# CDP 不会被 webdriver 检测
wf https://anti-scraping-site.com --use-cdp
```

### 场景 3: 需要复杂 JavaScript 渲染

对于 SPA (Single Page Application) 应用：

```bash
# CDP 完全渲染 React/Vue/Angular 应用
wf https://spa-app.com --use-cdp
```

### 场景 4: 网络请求监听

CDP 可以捕获页面发出的所有 API 请求（需要在代码中启用）。

## 编程使用

### Python 直接调用

```python
from webfetcher.fetchers.cdp_scraper import CDPScraper

# 创建 scraper
scraper = CDPScraper()

# 抓取页面
html, metrics = scraper.fetch_page(
    "https://example.com",
    wait_load=2.0,
    scroll_bottom=True,
    enable_network_watch=True
)

print(f"HTML 长度: {len(html)}")
print(f"抓取耗时: {metrics.total_time:.2f}s")
print(f"成功状态: {metrics.success}")
```

### 高级用法

```python
from webfetcher.fetchers.cdp_scraper import CDPScraper

scraper = CDPScraper()

# 创建标签页并导航
tab = scraper.new_tab("https://example.com")

# 等待特定元素出现
scraper.wait_for_selector(tab, ".content", timeout=10)

# 执行 JavaScript
title = scraper.eval_js(tab, "document.title")
print(f"页面标题: {title}")

# 提取特定内容
items = scraper.query_selector_all(tab, ".item-title")
print(f"找到 {len(items)} 个项目")

# 截图
scraper.screenshot(tab, "screenshot.png")

# 导出会话状态 (cookies, localStorage)
session = scraper.export_session(tab, "session.json")

# 获取 HTML
html = scraper.get_html(tab)

# 关闭标签页
scraper.close_tab(tab)
```

## 常见问题

### Q1: CDP 连接失败

**错误信息:**
```
CDP连接失败: [Errno 61] Connection refused
```

**解决方法:**
1. 确认 Chrome 已启动: `./scripts/start_chrome.sh`
2. 检查端口 9222 是否被占用: `lsof -i:9222`
3. 访问 http://localhost:9222/json 确认调试端口可用

### Q2: pychrome 未安装

**错误信息:**
```
CDP integration not available - install pychrome
```

**解决方法:**
```bash
pip install pychrome
# 或
pip install webfetcher[cdp]
```

### Q3: Chrome 窗口关闭后无法使用 CDP

CDP 需要 Chrome 进程保持运行。如果关闭了 Chrome 窗口：

```bash
# 重新启动 Chrome 调试模式
./scripts/start_chrome.sh
```

### Q4: 端口 9222 被占用

**解决方法:**
```bash
# macOS/Linux
lsof -ti:9222 | xargs kill -9

# 然后重新启动
./scripts/start_chrome.sh
```

### Q5: 多个 Chrome 实例冲突

使用独立的用户数据目录避免冲突。`start_chrome.sh` 脚本已自动处理。

## 性能对比

| 方法      | 速度  | JS 渲染 | 登录状态 | 反检测 | 网络监听 |
|-----------|-------|---------|----------|--------|----------|
| urllib    | ⭐⭐⭐⭐⭐ | ❌      | ❌       | ❌     | ❌       |
| Selenium  | ⭐⭐⭐  | ✅      | ✅       | ⭐     | ⭐       |
| CDP       | ⭐⭐⭐⭐ | ✅      | ✅       | ✅     | ✅       |

**选择建议:**
- **静态页面** → urllib (最快)
- **简单 JS 渲染** → Selenium
- **需要登录/反爬** → CDP
- **网络分析** → CDP
- **不确定** → auto 模式 (自动选择最佳方法)

## 命令行参数

```bash
# CDP 相关参数
--use-cdp                    # 使用 CDP 模式 (快捷方式)
--fetch-mode cdp             # 显式指定 CDP 模式
--cdp-timeout <seconds>      # CDP 超时时间 (默认: 30)

# 组合使用
wf https://example.com \
   --use-cdp \
   --cdp-timeout 60 \
   --verbose \
   --outdir ./output
```

## 技术细节

### 架构

```
WebFetcher CLI
    ↓
fetch_html_with_retry()
    ↓
┌─────────────────────────────┐
│  尝试 urllib (快速)         │
└─────────────────────────────┘
          ↓ 失败
┌─────────────────────────────┐
│  尝试 Selenium (中速)       │
└─────────────────────────────┘
          ↓ 失败
┌─────────────────────────────┐
│  尝试 CDP (可靠)            │  ← 新增
└─────────────────────────────┘
          ↓ 失败
┌─────────────────────────────┐
│  Manual Chrome (最后手段)   │
└─────────────────────────────┘
```

### CDP 通信流程

1. WebFetcher → Chrome (port 9222)
2. Chrome 返回调试端点列表
3. WebFetcher 连接到标签页
4. 发送 CDP 命令 (导航、执行 JS、获取 DOM 等)
5. 接收响应数据
6. 关闭连接

## 示例脚本

### 批量抓取 (使用 CDP)

```bash
#!/bin/bash

# 启动 Chrome
./scripts/start_chrome.sh

# 等待 Chrome 启动
sleep 2

# 批量抓取 (利用 CDP 保持会话)
urls=(
    "https://example.com/page1"
    "https://example.com/page2"
    "https://example.com/page3"
)

for url in "${urls[@]}"; do
    echo "抓取: $url"
    wf "$url" --use-cdp --outdir ./output
    sleep 1  # 避免过快请求
done

echo "完成!"
```

## 调试技巧

### 启用详细日志

```bash
wf https://example.com --use-cdp --verbose
```

### 查看 Chrome 调试信息

访问: http://localhost:9222

可以看到:
- 所有打开的标签页
- 网络请求
- Console 日志
- DOM 结构

### 保存 HTML 快照

```bash
wf https://example.com --use-cdp --save-html snapshot.html
```

## 未来扩展

计划中的功能:
- [ ] 自动等待元素加载
- [ ] 智能滚动加载
- [ ] 反检测伪装 (User-Agent, WebDriver 检测规避)
- [ ] GraphQL/REST API 自动抓取
- [ ] 代理支持
- [ ] 多标签页并发

## 参考资料

- [Chrome DevTools Protocol 文档](https://chromedevtools.github.io/devtools-protocol/)
- [pychrome GitHub](https://github.com/fate0/pychrome)
- [WebFetcher 项目主页](https://github.com/ttieli/web-fetcher)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
