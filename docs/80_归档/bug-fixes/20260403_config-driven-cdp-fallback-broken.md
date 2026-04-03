# Config-driven CDP 路径降级链断裂

> 创建时间：2026-04-03
> 管线：superpower-chain Pipeline A
> 状态：分析中

## 现象

当 routing.yaml 将某域名（如小红书）路由到 CDP fetcher 时，CDP 成功获取了 HTML 但内容验证失败（如 `spa_shell` — 空壳页），wf 直接返回该无效内容，没有继续尝试 manual_chrome 降级。

具体表现：小红书被 IP 风控拦截（error_code=300012），CDP 拿到的是登录错误页而非笔记内容，但 wf 直接输出了这个空壳页。

## 复现条件

- **环境**：macOS Darwin 25.3.0，Python 3.13，webfetcher 1.3.0
- **步骤**：
  1. `wf "http://xhslink.com/o/2zF9A248bWB" --stdout`
  2. 路由匹配 `XiaoHongShu - CDP, priority: 75`，走 config-driven CDP 路径
  3. CDP 返回 85489 chars HTML，但验证失败：`Config-driven CDP content validation failed: spa_shell`
  4. **期望**：继续尝试 manual_chrome 降级
  5. **实际**：直接返回无效 HTML，输出"安全限制"空壳页
- **频率**：必现（小红书 IP 风控持续生效时）

## 相关日志

```
Routing decision: cdp for http://xhslink.com/o/2zF9A248bWB (rule: XiaoHongShu - CDP, priority: 75)
🚀 Config-driven routing: Using CDP for http://xhslink.com/o/2zF9A248bWB
✓ CDP fetch completed in 4.53s
  HTML length: 85489 chars
  Final URL: https://www.xiaohongshu.com/website-login/error?...error_code=300012&error_msg=IP存在风险
Config-driven CDP content validation failed: spa_shell
```

## 影响范围

- 所有通过 routing.yaml 路由到 CDP 的站点，在 CDP 内容验证失败时都无法降级到 manual_chrome
- 同理，routing 到 selenium 的站点在验证失败时也直接返回（第 1711 行同样 pattern）
- 严重程度：P1 严重 — 降级链是 wf 可靠性的核心机制，断裂导致强风控站点完全无法采集

---

## 根因分析（A2 填写）

### 代码追踪

| 文件 | 行号 | 说明 |
|------|------|------|
| `src/webfetcher/core.py` | L1717-1741 | config-driven CDP 分支：验证失败后第 1737 行直接 `return` |
| `src/webfetcher/core.py` | L1692-1715 | config-driven Selenium 分支：同样 pattern，第 1711 行直接 `return` |
| `src/webfetcher/core.py` | L1574-1631 | urllib 路径的 fallback_chain：包含 CDP → manual_chrome，正常工作 |

### 证据链

1. **入口**：`fetch_html_with_retry()` 函数，`fetch_mode == 'auto'` 时进入 config-driven routing 分支
2. **路径**：`_determine_fetcher_via_routing(url)` 返回 `'cdp'` → 进入第 1717 行 `elif fetcher_choice == 'cdp'` 分支
3. **问题代码**（L1723-1737）：
   ```python
   html, metrics, url_metadata = _try_cdp_fetch(...)
   is_valid, reason = validate_fetched_html(html, url)
   if not is_valid:
       # 记录失败日志...但紧接着就：
       pass  # 没有 break 或 continue
   return html, metrics, url_metadata  # ← 无论验证通过与否，都直接返回！
   ```
4. **对比正常路径**（L1574-1631）：urllib 验证失败后进入 `fallback_chain` 循环，依次尝试 cdp → manual_chrome，验证通过才返回
5. **为什么之前没发现**：大多数 CDP 路由的站点（微信、知乎、掘金等）CDP 能正常工作，只有小红书这种 IP 级风控才暴露降级链断裂

### 根因结论

`fetch_html_with_retry()` 中 config-driven routing 的 CDP/Selenium 分支，在内容验证失败后无条件 `return`，没有 fall through 到 manual_chrome 降级链。urllib 路径有完整的 fallback_chain 但 config-driven 路径绕过了它。

---

## 评审记录（A3 辩论式评审）

| 专家 | 评级 | 要点 |
|------|------|------|
| 爬虫架构师 | 🔴 | 确认 CDP(L1737) 和 Selenium(L1711) 两条路径验证失败后直接 return。异常路径（except）正确 fall through，问题仅在"成功获取但内容无效"场景 |
| 容错系统专家 | 🔴 | 确认根因。**关键发现**：修复时需将已尝试的 fetcher 传入 tried_fetchers（如 `{'cdp'}`），否则 fallback_chain 会重复调用 CDP 造成循环 |
| 测试工程师 | 🔴 | 确认根因。tests/ 目录下零测试覆盖 config-driven routing fallback 场景，该路径从未被验证过 |

**结论**：三位专家全票 🔴，根因确认通过。

**额外发现**：
1. 修复需防重复尝试（tried_fetchers 传递）
2. 缺乏测试覆盖是该 Bug 长期存在的原因
3. 仅影响"内容验证失败"场景，CDP/Selenium 异常时的降级路径正常
