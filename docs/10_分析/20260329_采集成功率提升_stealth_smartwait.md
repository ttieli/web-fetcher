# 采集成功率提升 — 浏览器隐身 + 智能等待 + 路由学习

> 创建时间：2026-03-29
> 管线：superpower-chain Pipeline B
> 状态：收集中

## 原始需求

wf 的 CDP/Selenium fetcher 裸跑无反检测措施，遇到 Cloudflare/Akamai 等反爬直接失败（成功率约 25%）。同时 wait_time 硬编码 3s，对 SPA 站点不够。

## 需求列表

| # | 需求 | 复杂度 | 优先级 | 技术要点 | 批次 |
|---|------|--------|--------|----------|------|
| 1 | CDP stealth JS 注入 | S | P0 | 在 cdp_fetcher.py 的 fetch() 导航前注入反检测 JS | Batch 1 |
| 2 | Selenium stealth JS 注入 | S | P0 | 在 selenium.py 的 fetch_html_selenium() 导航后注入反检测 JS + Chrome 启动参数 | Batch 1 |
| 3 | CDP 智能等待 | M | P1 | 替代 _wait_for_ready 的固定轮询，用 DOM 变化检测 + 内容长度稳定判断 | Batch 1 |
| 4 | 失败日志路由学习 | M | P2 | wf learn 子命令，分析 fetch_failures.jsonl 输出路由建议 | Batch 2 |

## 细化记录（B1）

### 需求 1: CDP stealth JS 注入

**注入点**：`cdp_fetcher.py` 的 `fetch()` 方法，导航前通过 `tab.Runtime.evaluate()` 注入

**stealth JS 脚本**（纯 JS，无外部依赖）：
```javascript
// 1. 移除 webdriver 标记
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

// 2. 伪造 chrome.runtime（Cloudflare 检测项）
window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){} };

// 3. 伪造 plugins 数组（空 plugins 是自动化浏览器特征）
Object.defineProperty(navigator, 'plugins', {
  get: () => [1, 2, 3, 4, 5],
});

// 4. 伪造 languages（部分反爬检查 navigator.languages）
Object.defineProperty(navigator, 'languages', {
  get: () => ['zh-CN', 'zh', 'en-US', 'en'],
});

// 5. 覆盖 permissions.query（Notification permission 检测）
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) =>
  parameters.name === 'notifications'
    ? Promise.resolve({ state: Notification.permission })
    : originalQuery(parameters);
```

**注意**：CDP 支持 `Page.addScriptToEvaluateOnNewDocument` 命令，可以在每次导航前自动注入 JS，比手动在导航后注入更可靠（避免时序竞态）。但 pychrome 可能不直接支持此命令，需验证。fallback 方案是导航后立即 `Runtime.evaluate`。

### 需求 2: Selenium stealth JS 注入

**两层防护**：

A) Chrome 启动参数（在 selenium.py 连接配置中添加）：
```python
options.add_argument('--disable-blink-features=AutomationControlled')
```
这个参数**从 Chrome 引擎层面**禁用自动化检测标志，比 JS 注入更底层更可靠。

B) JS 注入（在 `driver.get(url)` 后立即执行，与 CDP 相同的 stealth 脚本）：
```python
self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': STEALTH_JS
})
```
Selenium 4+ 支持 `execute_cdp_cmd` 直接调用 CDP 命令，可以用 `Page.addScriptToEvaluateOnNewDocument` 实现导航前注入。

**注意**：wf 的 Selenium 是连接已有 Chrome debug session（非自启动），所以 `--disable-blink-features` 需要在启动 Chrome 时就加上，不能在连接时追加。应在 `config/chrome-debug.sh` 或文档中提示。

### 需求 3: CDP 智能等待

**替代 `_wait_for_ready()` 中的固定轮询**，新逻辑：
1. 等 `document.readyState === 'complete'`（已有）
2. **新增**：readyState complete 后，继续监听 DOM 内容长度变化
3. 每 0.5s 检查 `document.body.innerHTML.length`
4. 连续 2 次检查长度不变 → 内容稳定，退出等待
5. 最大等待 15s（hard cap），最小 0.5s

**JS 检查脚本**：
```javascript
(() => {
  const state = document.readyState;
  const bodyLen = document.body ? document.body.innerHTML.length : 0;
  const pendingXHR = (window.XMLHttpRequest && window.XMLHttpRequest._pending) || 0;
  return JSON.stringify({ state, bodyLen, pendingXHR });
})()
```

**优势**：快站（静态 HTML）0.5-1s 就退出，SPA 站（React/Vue 异步渲染）等到内容稳定后才退出。

### 需求 4: 失败日志路由学习

**wf learn 子命令**：
```bash
wf learn                    # 分析失败日志，输出路由建议
wf learn --apply            # 自动追加建议到 routing.yaml
wf learn --since 7d         # 只分析最近 7 天
```

**分析逻辑**：
1. 读取 `~/.wf/fetch_failures.jsonl`
2. 按域名聚合，统计失败次数和失败类型
3. 失败 ≥ 3 次的域名生成路由建议：
   - `failure_type == 'content_invalid' + reason contains 'spa_shell'` → 建议 `fetcher: cdp`
   - `failure_type == 'content_invalid' + reason contains 'antibot'` → 建议 `fetcher: selenium`
   - `failure_type == 'fetch_error' + SSL` → 建议 `fetcher: selenium`
4. 输出 YAML 格式的路由规则建议

## 分批计划（B2）

| 批次 | 优先级 | 包含需求 | 预估工作量 |
|------|--------|----------|-----------|
| Batch 1 | P0+P1 | #1(CDP stealth), #2(Selenium stealth), #3(智能等待) | M |
| Batch 2 | P2 | #4(路由学习) | M |

Batch 1 三个需求紧密相关（都改 fetcher 层），合为一批。
Batch 2 独立（CLI 子命令 + 日志分析），单独成批。
