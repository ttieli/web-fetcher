# CDP 资源拦截加速（--lite 模式）设计探索

> 创建时间：2026-04-01
> 阶段：superpower-chain B1 设计探索

## 关键发现

**图片链接不会丢失。** CDP 拦截的是 HTTP 下载请求，不是 HTML 标签属性。拦截 image 类型请求后：
- `<img src="...">` 和 `data-src="..."` 属性仍在 DOM 中
- wf 的图片提取管线（微信 `data-src` 选择器、小红书 `data-src` 选择器、legacy 正则）全部基于属性解析，不依赖图片实际下载
- Markdown 输出中照样有 `![](url)` 图片链接
- 唯一跳过的是浏览器下载图片字节 → 这正是 80-90% 的网络传输量

**`readyState === 'complete'` 会更快到达。** 当前 `_wait_for_ready()` 等待 `readyState` 变为 `complete`（即所有资源加载完成）。拦截图片/CSS/字体后，需要加载的资源大幅减少，`complete` 状态会在几秒内到达，而非等待数十秒。

## 设计决策

### 1. 命名：`--lite`

- CLI flag：`--lite`（argparse 参数）
- 不新增子命令（避免与 `wf fast` 混淆）
- 用法：`wf "URL" --stdout --lite`
- 语义：轻量抓取，内容相同，速度快 3-5x

### 2. 资源拦截策略

拦截以下 4 类资源的 HTTP 请求：
- `Image` — 图片（最大省时点）
- `Stylesheet` — CSS 样式表
- `Font` — 字体文件
- `Media` — 音视频

**不拦截**：`Document`、`Script`、`XHR`、`Fetch`、`WebSocket` — 这些对页面 JS 执行和 DOM 构建有影响。

### 3. 实现层：仅 CDP fetcher

在 `cdp_fetcher.py` 的 `CDPFetcher.fetch()` 中实现，通过 `Fetch.enable` + `Fetch.requestPaused` 事件拦截（pychrome 支持的现代 CDP 协议，替代已废弃的 `Network.setRequestInterception`）。

不在 Playwright render 层实现（当前 Playwright 路径不是主要瓶颈，且后续可能迁移到纯 CDP）。

### 4. 升降级策略：显式选择，不自动

- 不做自动升降级（增加复杂度，收益不明确）
- 由调用方（AI agent 或用户）显式选择 `--lite` 或默认模式
- 在 Fetch Metrics 中标注模式，方便调用方事后判断

理由：图片链接已保留，内容完整性无差异。唯一差别是 `--download-assets` 不可用。AI agent 根据场景选择即可。

### 5. 与 `--download-assets` 的交互

- `--lite` + `--download-assets` = **自动禁用 lite**（download-assets 需要实际下载图片，与 lite 矛盾）
- 打印警告：`--download-assets 需要完整加载，已自动禁用 --lite`
- 不报错，不中断

### 6. Fetch Metrics 输出标记

在已有的 `<!-- Fetch Metrics: -->` 块中新增字段：
```
<!-- Fetch Metrics:
  Method: cdp
  Mode: lite              ← 新增
  Resources Blocked: image,stylesheet,font,media  ← 新增
  ...
-->
```

AI agent 可以解析此标记判断当前模式。

### 7. help 文本（面向 AI agent）

```
--lite    Lightweight CDP fetch: blocks image/CSS/font/media downloads
          during page rendering for 3-5x speed improvement.
          Content and image URLs are fully preserved in output.
          Use for: reading article text, AI analysis, quick extraction.
          Not for: saving articles with downloaded images (use default + --download-assets).
          Only effective with --fetch-mode cdp/auto. (default: off)
```

### 8. 超时容错（附带优化）

在 `_wait_for_ready()` 超时后，不直接返回空，而是尝试提取已加载的 DOM 内容。这是独立于 `--lite` 的改进，但可以一起实施。

### 9. 对现有行为的影响

| 场景 | 行为变化 |
|------|---------|
| `wf url --stdout` | 无变化（默认不开 lite） |
| `wf url --stdout --lite` | 新功能：资源拦截加速 |
| `wf url --stdout --lite -c` | 同上（-c 是 CDP 快捷方式） |
| `wf fast url --stdout` | 无变化（仍是 --render never） |
| `wf url --download-assets --lite` | 自动禁用 lite，打印警告 |
| `wf url --stdout -u --lite` | lite 无效（urllib 模式无浏览器），静默忽略 |

## 风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 某些站点 JS 因图片 onerror 事件改变 DOM | 低 | 正文缺失 | lite 是可选模式，遇到问题切回默认 |
| CSS 拦截导致 JS 依赖的布局信息丢失 | 极低 | 正文提取不受布局影响 | wf 提取的是 DOM 文本，不是渲染结果 |
| pychrome 的 Fetch domain 支持问题 | 低 | 功能不可用 | 回退到 Network.setRequestInterception |

## 实施建议

单批次，4 个 Task：
1. `CDPFetcher` 新增 `lite_mode` 参数 + 资源拦截逻辑
2. `fetch_with_cdp()` 和 `_try_cdp_fetch()` 透传 lite 参数
3. CLI `--lite` 参数 + help 文本 + download-assets 互斥处理
4. Fetch Metrics 新增 Mode 和 Resources Blocked 字段
