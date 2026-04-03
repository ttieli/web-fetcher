# 修复方案：Config-driven CDP/Selenium 降级链断裂

> 创建时间：2026-04-03
> 管线：superpower-chain Pipeline A
> 关联：docs/10_分析/20260403_config-driven-cdp-fallback-broken.md

## 概述

当 config-driven routing 将 URL 路由到 CDP 或 Selenium 时，内容验证失败后直接 return 无效内容，绕过了 manual_chrome 降级链。修复方法：验证失败时调用已有的 `_try_fallback_for_invalid_content()` 函数，传入 `tried_fetchers` 防止重复尝试。

## 改动总览

| 文件 | 类型 | 说明 |
|------|------|------|
| `src/webfetcher/core.py` | 修改 | CDP 和 Selenium 分支验证失败后调用 fallback 函数 |

## 详细设计

### 修改 1：CDP 分支（L1717-1741）

**改动文件**：`src/webfetcher/core.py`

**旧代码**（L1717-1741）：
```python
        elif fetcher_choice == 'cdp':
            # CDP requested by routing config (e.g., for Google Search)
            print(f"🚀 Config-driven routing: Using CDP for {url}", file=sys.stderr)
            logging.info(f"🚀 Config-driven routing to CDP: {url}")
            metrics.primary_method = "cdp_direct"

            try:
                html, metrics, url_metadata = _try_cdp_fetch(url, ua, timeout, metrics, start_time, input_url)
                is_valid, reason = validate_fetched_html(html, url)
                if not is_valid:
                    logging.warning(f"Config-driven CDP content validation failed: {reason}")
                    metrics.validation_failures.append(('cdp', reason))
                    persist_fetch_failure(
                        url=url, input_url=input_url or url,
                        fetchers_tried=['cdp'], failure_type='content_invalid',
                        failure_reason=reason, last_error='',
                        html_size=len(html) if html else 0,
                        validation_details=[f'cdp:{reason}'],
                        fetch_mode='cdp_direct', duration_seconds=time.time() - start_time,
                    )
                return html, metrics, url_metadata
            except Exception as e:
                logging.warning(f"CDP fetch failed for {url}, falling back to urllib: {e}")
                metrics.primary_method = "urllib"
                # Continue to urllib logic below
```

**新代码**：
```python
        elif fetcher_choice == 'cdp':
            # CDP requested by routing config (e.g., for Google Search)
            print(f"🚀 Config-driven routing: Using CDP for {url}", file=sys.stderr)
            logging.info(f"🚀 Config-driven routing to CDP: {url}")
            metrics.primary_method = "cdp_direct"

            try:
                html, metrics, url_metadata = _try_cdp_fetch(url, ua, timeout, metrics, start_time, input_url)
                is_valid, reason = validate_fetched_html(html, url)
                if not is_valid:
                    logging.warning(f"Config-driven CDP content validation failed: {reason}")
                    metrics.validation_failures.append(('cdp', reason))
                    # Try fallback chain (skip CDP since we already tried it)
                    logging.info(f"Config-driven CDP fallback: trying manual_chrome for {url}")
                    return _try_fallback_for_invalid_content(
                        url, html, reason, ua, timeout, metrics, start_time,
                        input_url=input_url, force_chrome=force_chrome,
                        tried_fetchers={'cdp'},
                    )
                return html, metrics, url_metadata
            except Exception as e:
                logging.warning(f"CDP fetch failed for {url}, falling back to urllib: {e}")
                metrics.primary_method = "urllib"
                # Continue to urllib logic below
```

**关键变化**：
- 移除验证失败后的 `persist_fetch_failure` + 无条件 `return`
- 改为调用 `_try_fallback_for_invalid_content()`，传入 `tried_fetchers={'cdp'}` 防止 CDP 被重复调用
- `_try_fallback_for_invalid_content` 内部已有 `persist_fetch_failure` 逻辑，避免重复记录

### 修改 2：Selenium 分支（L1692-1715）

**改动文件**：`src/webfetcher/core.py`

**旧代码**（L1692-1711）：
```python
        if fetcher_choice == 'selenium':
            print(f"🚀 Config-driven routing: Using Selenium for {url}", file=sys.stderr)
            logging.info(f"🚀 Config-driven routing to Selenium: {url}")
            metrics.primary_method = "selenium_direct"

            try:
                html, metrics, url_metadata = _try_selenium_fetch(url, ua, timeout, metrics, start_time, force_chrome, input_url)
                is_valid, reason = validate_fetched_html(html, url)
                if not is_valid:
                    logging.warning(f"Config-driven Selenium content validation failed: {reason}")
                    metrics.validation_failures.append(('selenium', reason))
                    persist_fetch_failure(
                        url=url, input_url=input_url or url,
                        fetchers_tried=['selenium'], failure_type='content_invalid',
                        failure_reason=reason, last_error='',
                        html_size=len(html) if html else 0,
                        validation_details=[f'selenium:{reason}'],
                        fetch_mode='selenium_direct', duration_seconds=time.time() - start_time,
                    )
                return html, metrics, url_metadata
            except Exception as e:
                logging.warning(f"Selenium fetch failed for {url}, falling back to urllib: {e}")
                metrics.primary_method = "urllib"
                # Continue to urllib logic below
```

**新代码**：
```python
        if fetcher_choice == 'selenium':
            print(f"🚀 Config-driven routing: Using Selenium for {url}", file=sys.stderr)
            logging.info(f"🚀 Config-driven routing to Selenium: {url}")
            metrics.primary_method = "selenium_direct"

            try:
                html, metrics, url_metadata = _try_selenium_fetch(url, ua, timeout, metrics, start_time, force_chrome, input_url)
                is_valid, reason = validate_fetched_html(html, url)
                if not is_valid:
                    logging.warning(f"Config-driven Selenium content validation failed: {reason}")
                    metrics.validation_failures.append(('selenium', reason))
                    # Try fallback chain (skip selenium, CDP may still help)
                    logging.info(f"Config-driven Selenium fallback: trying CDP/manual_chrome for {url}")
                    return _try_fallback_for_invalid_content(
                        url, html, reason, ua, timeout, metrics, start_time,
                        input_url=input_url, force_chrome=force_chrome,
                        tried_fetchers={'selenium'},
                    )
                return html, metrics, url_metadata
            except Exception as e:
                logging.warning(f"Selenium fetch failed for {url}, falling back to urllib: {e}")
                metrics.primary_method = "urllib"
                # Continue to urllib logic below
```

**关键变化**：同 CDP 分支，传入 `tried_fetchers={'selenium'}` — Selenium 失败后仍可尝试 CDP 和 manual_chrome。

## 风险评估

- **重复尝试**：通过 `tried_fetchers` 集合避免。CDP 分支传 `{'cdp'}`，Selenium 分支传 `{'selenium'}`
- **超时控制**：`_try_fallback_for_invalid_content` 内部有 `_FETCH_TOTAL_DEADLINE` 检查（L1590），不会无限等待
- **persist_fetch_failure 重复**：移除了 config-driven 路径的 persist 调用，fallback 函数内部会统一处理
- **副作用**：无。仅在原本返回无效内容的场景增加了一次降级尝试

---

## 评审记录（A5 多角度审查）

| 专家 | 评级 | 要点 |
|------|------|------|
| 代码验证专家 | 🟢 | 签名匹配、tried_fetchers 跳过机制验证、旧代码与实际一致、force_chrome 参数可用 |
| 副作用审查专家 | 🟢 | fallback 全失败返回 degraded output 安全、persist 由函数内部兜底不重复、metrics 追加模式正确、唯一调用点不冲突 |

**结论**：通过，方案安全可执行
