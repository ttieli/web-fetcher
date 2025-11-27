# 架构优化与审查 / Architecture Optimization & Review

## 概述 / Overview

本文档分析 `webfetcher` 架构，特别关注获取器回退机制（`urllib` -> `CDP` -> `Selenium`）、资源管理和优化机会。

This document analyzes the `webfetcher` architecture, specifically focusing on the fetcher fallback mechanism (`urllib` -> `CDP` -> `Selenium`), resource management, and opportunities for optimization.

## 当前架构 / Current Architecture

### 1. 工作流 (`fetch_html_with_retry`)

主入口点是 `src/webfetcher/core.py` 中的 `fetch_html_with_retry`。它实现了一个顺序回退链：

The main entry point is `fetch_html_with_retry` in `src/webfetcher/core.py`. It implements a sequential fallback chain:

1.  **配置驱动路由 / Config-Driven Routing:** 通过 `RoutingEngine` 检查 `routing.yaml`。如果指定了特定的获取器（例如，`xiaohongshu.com` 使用 `selenium`），它会直接跳转到该获取器。

2.  **默认流程（自动模式）/ Default Flow (Auto Mode):**
    *   **步骤1：`urllib`（标准请求）/ Step 1: `urllib` (Standard Request):**
        *   尝试使用 `urllib.request` 获取内容。
        *   **重试逻辑 / Retry Logic:** 对瞬时错误（超时、网络问题）最多重试3次。
        *   **优化机会 / Optimization Opportunity:** 当前重试逻辑是"重试优先"。对于特定错误如403（禁止访问/反机器人）或412（前提条件失败），重试 `urllib` 通常是无用的。应该实现"快速失败"机制，跳过重试，立即回退到CDP/Selenium处理这些特定状态码。
    *   **步骤2：CDP回退 / Step 2: CDP Fallback:**
        *   当 `urllib` 失败时触发（重试次数用尽或遇到致命错误）。
        *   使用 `CDPFetcher`（`pychrome`）连接到端口9222上的Chrome实例。
        *   **机制 / Mechanism:** 它尝试附加到现有标签页或创建新标签页，等待页面加载（默认3秒），并获取渲染后的DOM（`outerHTML`）。
        *   **优势 / Advantage:** 比Selenium轻量得多；重用浏览器会话（cookies/登录状态）。
    *   **步骤3：Selenium回退 / Step 3: Selenium Fallback:**
        *   当CDP失败时触发（例如，Chrome未运行，连接被拒绝）。
        *   使用 `ensure_chrome_debug.sh` 检查/启动Chrome。
        *   使用Selenium Remote WebDriver连接。
        *   **观察 / Observation:** 如果CDP正常工作，这一步在很大程度上是冗余的，因为两者都依赖相同的底层Chrome实例。但是，如果需要深度交互，Selenium提供更好的驱动程序管理和元素交互。
    *   **步骤4：手动Chrome（最后手段）/ Step 4: Manual Chrome (Last Resort):**
        *   如果所有自动化都失败，它会提示用户手动打开浏览器。

### 2. 资源管理 / Resource Management

*   **CDP连接 / CDP Connections:** `CDPFetcher` 为每个获取请求初始化一个新的 `pychrome.Browser` 连接（`connect` 方法）。
    *   **优化 / Optimization:** 对于批处理（未来功能），持久化的浏览器连接对象会减少开销。对于CLI单URL使用，当前方法是可以接受的。
*   **Chrome进程 / Chrome Process:** 系统依赖于外部Chrome进程（通过 `src/webfetcher/config/` 中的shell脚本管理）。`ensure_chrome_debug.sh` 脚本很健壮（处理PID检查、端口冲突和超时）。

## 提议的优化 / Proposed Optimizations

### 1. `urllib` 的快速失败策略 / Fail-Fast Strategy for `urllib`

当前，`fetch_html_with_retry` 重试所有异常。我们应该修改它，为明确的反机器人信号立即触发回退。

Currently, `fetch_html_with_retry` retries all exceptions. We should modify it to immediately trigger fallback for definitive anti-bot signals.

**实施计划 / Implementation Plan:**
- 在 `fetch_html_with_retry` 中，捕获 `urllib.error.HTTPError`。
- 如果状态码是 `403`、`412` 或 `429`，跳过剩余的 `urllib` 重试，立即调用 `_try_cdp_fallback_after_urllib_failure`。

### 2. "空内容"检测 / "Empty Content" Detection

SPA（单页应用）网站的一个常见问题是 `urllib` 返回 `200 OK`，但内容基本上是空的（例如，只有 `<div id="root"></div>` 和 `<script>` 标签）。当前逻辑认为这是"成功"，导致空的Markdown文件。

A common issue with SPA (Single Page Application) sites is that `urllib` returns `200 OK` but the content is essentially empty (e.g., just `<div id="root"></div>` and `<script>` tags). The current logic considers this a "success", leading to empty Markdown files.

**实施计划 / Implementation Plan:**
- 在 `fetch_html_original` 中（或之后立即），检查获取的HTML。
- **启发式方法 / Heuristic:** 如果 `len(html) < 500` 字节（可配置）或者脚本标签与文本内容的比率极高，将其视为"软失败"。
- 即使HTTP状态是200，也为这些"软失败"触发CDP回退。

### 3. 增强的错误报告 / Enhanced Error Reporting

错误链可能很模糊（例如，"urllib失败... CDP失败..."）。

The error chain can be obscure (e.g., "urllib failed... CDP failed...").

**实施计划 / Implementation Plan:**
- 改进 `FetchMetrics` 对象，存储每种方法失败原因的跟踪（例如，"urllib: 403 Forbidden" -> "CDP: Connection Refused" -> "Selenium: Success"）。
- 确保这些细节在 `wf --diagnose` 命令和最终Markdown页脚中暴露出来。

### 4. CDP会话持久化（未来）/ CDP Session Persistence (Future)

对于 `wf batch` 命令：

For `wf batch` command:
- 重构 `CDPFetcher` 以接受现有的 `browser` 实例。
- 在 `cli.py` 的批处理循环中，实例化 `CDPFetcher` 一次并传递给处理函数。

## 建议总结 / Summary of Recommendations

1.  **在 `fetch_html_with_retry` 中实施"快速失败"/ Implement "Fail-Fast" in `fetch_html_with_retry`** 针对403/412错误。
2.  **实施SPA检测/ Implement SPA Detection:** 将"200 OK"但为空/仅脚本的响应视为失败，触发CDP回退。
3.  **持久化模板名称/ Persist Template Name:** 确保解析器模板名称始终记录在元数据中（在v1.1.1中完成）。
4.  **标准化超时/ Standardize Timeout:** 确保 `ensure_chrome_debug.sh` 和Python超时对齐（已完成：两者现在都使用约15秒）。
