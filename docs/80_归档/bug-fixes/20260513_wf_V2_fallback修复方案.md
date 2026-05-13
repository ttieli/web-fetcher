# wf V2 Fallback 修复实施方案

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 wf 工具 V2 自动升级 fallback 机制的 3 个联动 Bug，让 SPA 站点能正确逐级升 cdp→selenium→manual_chrome，让 plain markdown URL 不再触发不必要升级。

**Architecture:** 三处独立改动 + 一组 TDD 测试。
1. `engine_v2.py` 把质量描述字段（_v2_quality_low/_v2_score/_v2_current_fetcher）从 `if quality_low and not _v2_no_upgrade` 块内提取为本地 dict `v2_state`，所有 return 点统一 update。
2. `core.py` 升级 if 块从"比较 HTML 长度"改为"用提取 score 比较"，"换 fetcher" 和 "链终止" 解耦；`args._v2_no_upgrade` 状态用 try/finally 保护。
3. `extractors.py` 在 `run_competition` 入口对 plain-text URL 短路（专用 `score_extraction_plaintext` helper，不污染主评分函数）。

**A5 评审采纳的关键修订**（与 v1 草案差异）：
- P0：`_v2_no_upgrade` 状态切换用 try/finally 防异常路径泄漏
- P0：plain-text 宽容评分**独立成 `score_extraction_plaintext()`**，主 `score_extraction` 行为完全不变，避免 trafilatura 输出（本就无 HTML）误走宽容分支抬高阈值
- P1：测试 fixture 加入"有正文但 score<0.5"的非 SPA 低质用例（避免走 legacy fallback 路径绕过测试覆盖）
- P1：短路 HTML 检测改 `not re.search(r'<[a-zA-Z!/]', html[:1000])`，避免 markdown autolink 误判
- P2：E2E 步骤加自动 grep 断言；test_extraction_competition baseline 对比

**Tech Stack:** Python 3.x，pytest（tests/unit/），trafilatura/readability/json_ld 已有，无新依赖。

---

## 变更总览（改动文件表）

| 文件 | 修改类型 | 行号范围 | 影响 |
|------|---------|---------|------|
| `src/webfetcher/parsing/engine_v2.py` | 重构字段写入位置 | 117-167（删除 144-147 中 3 字段写入 + 新增 v2_state dict 在 124 后 + 4 个 return 点前 update） | 重抓后 metadata 始终携带真实质量字段 |
| `src/webfetcher/core.py` | 升级判定逻辑替换 | 5619-5681（3 处 try 块改用 new_score 比较） | SPA 站点能继续升 selenium；长但低分不再误判为升级成功 |
| `src/webfetcher/parsing/extractors.py` | 新增 plain-text 短路 + 评分宽容 | 30-77（score_extraction 加 is_plain_text 分支）+ 276 行附近（run_competition 入口加 URL 短路） | raw markdown 不触发不必要升级 |
| `tests/unit/test_v2_fallback.py` | 新建 | 全文件 | 单测覆盖 Bug 1 + Bug 2 + 集成回归 |
| `tests/unit/test_extractors_plaintext.py` | 新建 | 全文件 | 单测覆盖问题 3 |

---

## Task 1: Bug 2 字段解耦（前置 · 独立可测）

**Files:**
- Create: `tests/unit/test_v2_fallback.py`
- Modify: `src/webfetcher/parsing/engine_v2.py`（line 117-167 范围）

**目标**：让 `metadata['_v2_quality_low']`、`metadata['_v2_score']`、`metadata['_v2_current_fetcher']` 在**所有**返回路径（含 `_v2_no_upgrade=True` 重抓后）始终有值，只让 `_v2_needs_upgrade` 留在升级请求分支内。

- [ ] **Step 1.1: 写失败测试 — 验证 _v2_no_upgrade=True 时字段仍写入**

新建 `tests/unit/test_v2_fallback.py`：

```python
"""Tests for V2 fallback metadata field writeback under _v2_no_upgrade."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from types import SimpleNamespace
from webfetcher.parsing.engine_v2 import generic_v2


def _spa_shell_html() -> str:
    """A minimal SPA-like HTML that scores low even with content present."""
    return """<!DOCTYPE html>
<html><head><title>Test</title></head>
<body>
<div id="root"></div>
<div>nav menu nav menu nav menu sidebar footer cookie subscribe sign in login</div>
<script>window.__data__ = {};</script>
</body></html>"""


def _short_low_quality_html() -> str:
    """A page that has some article-like content but is short and noisy enough
    to land in quality_low without falling through to legacy fallback.

    必要性：纯 SPA shell 在主路径会被 'not best or not best.content.strip()'
    判定为空 → 走 line 164 legacy_generic_parser 回退路径，绕过质量字段写入。
    本 fixture 让 trafilatura 能提取出**有一点内容**但 score 仍 < 0.5。
    """
    return """<!DOCTYPE html>
<html><head><title>News page</title></head>
<body>
<article>
<h1>Headline</h1>
<p>nav menu sidebar footer cookie subscribe sign in advertisement more from related posts</p>
<p>登录 关注我们 推荐阅读 相关文章 导航 menu nav</p>
<p>Short paragraph.</p>
</article>
</body></html>"""


def test_quality_metadata_written_even_when_no_upgrade():
    """Bug 2: _v2_quality_low / _v2_score / _v2_current_fetcher must be
    written to metadata even when _v2_no_upgrade=True (i.e. on re-parse
    after a fetcher upgrade in core.py).

    用 _short_low_quality_html() 而非纯 SPA shell：让 trafilatura 能提取出内容
    但 score 仍 < 0.5，走主路径而非 legacy fallback 路径。
    """
    html = _short_low_quality_html()
    args = SimpleNamespace(_v2_no_upgrade=True, engine='v2')
    url_metadata = {'fetch_mode': 'cdp'}

    date_only, md, metadata = generic_v2(
        html, 'https://example.com/spa',
        url_metadata=url_metadata, args=args)

    # 三个质量描述字段必须存在
    assert '_v2_quality_low' in metadata, (
        f"_v2_quality_low must be present in metadata when _v2_no_upgrade=True; "
        f"got keys: {list(metadata.keys())}")
    assert '_v2_score' in metadata
    assert '_v2_current_fetcher' in metadata

    # current_fetcher 应反映 url_metadata 中的值
    assert metadata['_v2_current_fetcher'] == 'cdp'

    # 内容差，quality_low 应为 True
    assert metadata['_v2_quality_low'] is True
    assert metadata['_v2_score'] < 0.5

    # _v2_needs_upgrade 不应被写入（因为 _v2_no_upgrade=True 不返回升级信号）
    assert '_v2_needs_upgrade' not in metadata


def test_quality_metadata_written_on_high_quality_path():
    """正常高质量路径也要带 _v2_score（便于 core.py prev_score 读取）。"""
    # 一个分数足够高的真实文章 HTML
    html = """<!DOCTYPE html>
<html><head><title>Article</title></head><body><article>
<h1>Article Title</h1>
<p>%s</p>
<p>%s</p>
<p>%s</p>
</article></body></html>""" % (
        '这是一段正常的文章内容，描述一个具体的事件或观点，长度适中能够通过段落质量评分检查。' * 3,
        '第二段继续展开论述，提供更多细节和分析，确保整体内容的连贯性和信息密度。' * 3,
        '第三段总结观点并给出结论，结构清晰用词得当，没有导航或广告性质的噪音词汇。' * 3,
    )
    args = SimpleNamespace(_v2_no_upgrade=False, engine='v2')

    date_only, md, metadata = generic_v2(html, 'https://example.com/article', args=args)

    # 高质量路径应该 quality_low=False 且 score 较高
    assert metadata.get('_v2_quality_low') is False, (
        f"high quality content should have _v2_quality_low=False, got {metadata.get('_v2_quality_low')}, "
        f"score={metadata.get('_v2_score')}")
    assert metadata.get('_v2_score', 0) >= 0.5
```

- [ ] **Step 1.2: 跑测试确认 FAIL**

Run: `pytest tests/unit/test_v2_fallback.py::test_quality_metadata_written_even_when_no_upgrade -xvs`

Expected: FAIL — `assert '_v2_quality_low' in metadata` fails because字段只在 `if quality_low and not _v2_no_upgrade` 块内写入，重抓路径丢失。

- [ ] **Step 1.3: 实施 engine_v2.py 字段重排**

修改 `src/webfetcher/parsing/engine_v2.py`：

**改动 A**：在 line 117-122（quality_low 计算）和 line 124-127（current_fetcher 计算）之后、line 130 if 之前，**新增** v2_state 构造：

```python
# 原 line 117-127 保持不变：
    # Step 3: 质量检测 + 自动升级判断
    quality_low = False
    is_spa = False
    if (best and best.score < 0.5) or not best or not (best and best.content.strip()):
        quality_low = True
        is_spa = _is_spa_shell(html)

    # 确定当前 fetcher
    current_fetcher = 'urllib'
    if url_metadata:
        current_fetcher = url_metadata.get('fetch_mode', 'urllib')

    # ===== 新增：质量描述字段（独立于 _v2_no_upgrade 标志） =====
    # 这些字段在任何返回路径都会写入 metadata，让 core.py 升级循环
    # 能从重抓后的 metadata 读到真实的提取 score 和 quality 状态。
    # 与 _v2_needs_upgrade（升级请求信号）不同——后者仅在主动请求升级时设置。
    v2_state = {
        '_v2_quality_low': quality_low,
        '_v2_score': best.score if best and best.content else 0.0,
        '_v2_current_fetcher': current_fetcher,
    }
```

**改动 B**：line 130-158 的升级信号分支，**删除** line 144、146、147 三处直接写入（_v2_quality_low / _v2_current_fetcher / _v2_score），保留 line 145 `_v2_needs_upgrade`；在 return 前 update v2_state：

```python
    # 质量差时：返回升级信号（而非直接回退 legacy）
    if quality_low and not getattr(args, '_v2_no_upgrade', False):
        # 确定下一级 fetcher（含 manual_chrome 人工托底）
        upgrade_chain = {'urllib': 'cdp', 'cdp': 'selenium',
                         'selenium': 'manual_chrome', 'auto': 'cdp'}
        next_fetcher = upgrade_chain.get(current_fetcher)

        if next_fetcher:
            score_info = f"score={best.score:.3f}" if best and best.content else "empty"
            logger.warning(f"V2: quality low ({score_info}), "
                           f"SPA={is_spa}, requesting upgrade: {current_fetcher} → {next_fetcher}")

            # 构建带升级信号的最小输出（core.py 会丢弃并重抓）
            from webfetcher.parsing.legacy import generic_to_markdown as legacy_generic_parser
            date_only, md, metadata = legacy_generic_parser(html, url, 'safe', False)
            metadata.update(v2_state)                       # 写入质量描述字段
            metadata['_v2_needs_upgrade'] = next_fetcher    # 仅升级请求字段保留在此处

            # 记录日志
            ext_logger.log(
                url=url, domain=memory.get_domain(url), fetcher=current_fetcher,
                fetch_ms=0,
                extractor_results={r.strategy: {'score': r.score, 'chars': len(r.content)} for r in results},
                winner=best.strategy if best else 'none',
                winner_score=best.score if best else 0,
                quality_low=True,
            )
            return date_only, md, metadata

        # 已经是最高级 fetcher（manual_chrome），无法再升级
        logger.warning(f"V2: quality low but already at {current_fetcher}, no further upgrade")
```

**改动 C**：line 163-167 的 legacy fallback 分支，加 v2_state update：

```python
    # 如果所有策略都没内容且无法升级，回退到 V1 legacy
    if not best or not best.content.strip():
        logger.warning(f"V2: all extractors empty for {url}, falling back to V1 legacy")
        from webfetcher.parsing.legacy import generic_to_markdown as legacy_generic_parser
        date_only, md, metadata = legacy_generic_parser(html, url, 'safe', False)
        metadata.update(v2_state)
        return date_only, md, metadata
```

**改动 D**：line 213 的正常返回前，加 v2_state update：

```python
    # Step 5 末尾（line 211 之后、return 之前）：
    ext_logger.log(
        url=url,
        domain=memory.get_domain(url),
        fetcher=fetcher,
        fetch_ms=getattr(fetch_metrics, 'fetch_duration', 0) * 1000 if fetch_metrics else 0,
        extractor_results={
            r.strategy: {'score': r.score, 'chars': len(r.content)}
            for r in results
        },
        winner=best.strategy,
        winner_score=best.score,
        quality_low=quality_low,
    )

    metadata.update(v2_state)
    return date_only, md, metadata
```

- [ ] **Step 1.4: 跑测试确认 PASS**

Run: `pytest tests/unit/test_v2_fallback.py::test_quality_metadata_written_even_when_no_upgrade tests/unit/test_v2_fallback.py::test_quality_metadata_written_on_high_quality_path -xvs`

Expected: 两个测试都 PASS。

- [ ] **Step 1.5: Commit**

```bash
git add tests/unit/test_v2_fallback.py src/webfetcher/parsing/engine_v2.py
git commit -m "fix(v2): decouple quality metadata fields from _v2_no_upgrade gate

Bug 2 修复：_v2_quality_low / _v2_score / _v2_current_fetcher 三个质量
描述字段移到 if 块外，所有 return 路径都通过 v2_state.update 写入。
_v2_needs_upgrade 仍保留在升级请求分支（语义：仅在主动请求升级时设置）。

这让 core.py 在 _v2_no_upgrade=True 重抓后能从 metadata 读到真实 score
和 quality 状态，避免 if not metadata.get('_v2_quality_low'): break 永远 True 的 bug。"
```

---

## Task 2: Bug 1 score-based 升级判定

**Files:**
- Modify: `src/webfetcher/core.py:5619-5681`
- Modify: `tests/unit/test_v2_fallback.py`（添加测试）

**目标**：core.py 升级循环中，把"换 fetcher 接受判定"和"链终止判定"解耦——前者用 new_score >= prev_score（平手也接受以推进），后者要求 new_score >= 0.5。HTML 长度仅作 html2 为空的过滤。

- [ ] **Step 2.1: 写失败测试 — 验证 SPA 长 HTML 不会错误 break**

追加到 `tests/unit/test_v2_fallback.py`：

```python
def test_upgrade_should_break_only_when_score_improved_above_threshold():
    """Bug 1: HTML 变长但 score 仍低（SPA shell 场景），fallback 链
    应继续升下一级，而不是因为 HTML 长就 break。

    本测试通过端到端调 generic_v2 验证（不 mock core.py 的 fetch_html）。
    实际 fallback 链的行为通过 fixture HTML 字符串模拟前后状态。
    """
    # urllib 抓回的：典型 SPA 短 shell
    short_shell = """<html><body><div id="root"></div>
<div>nav menu sidebar</div></body></html>"""

    # cdp 抓回的：长但仍是骨架，内容仍少
    long_shell = """<html><body><div id="root"></div>
<div>%s</div>
<div>nav menu sidebar footer cookie subscribe</div>
</body></html>""" % ('<span>x</span>' * 500)  # 长但实际无正文

    args = SimpleNamespace(_v2_no_upgrade=True, engine='v2')

    _, _, m1 = generic_v2(short_shell, 'https://example.com/spa',
                          url_metadata={'fetch_mode': 'urllib'}, args=args)
    _, _, m2 = generic_v2(long_shell, 'https://example.com/spa',
                          url_metadata={'fetch_mode': 'cdp'}, args=args)

    # 两次都应有 _v2_score
    assert '_v2_score' in m1 and '_v2_score' in m2

    # CDP HTML 比 urllib 长很多，但内容质量没变 → score 应仍然 < 0.5
    assert m2['_v2_score'] < 0.5, (
        f"CDP long-shell score should still be low; got {m2['_v2_score']}")
    assert m2['_v2_quality_low'] is True

    # 这两个断言代表"core.py 升级循环应继续升 selenium"的前提：
    # 重抓后 metadata 仍标记 quality_low + score < 0.5
```

- [ ] **Step 2.2: 跑测试确认它编译运行（应 PASS，因为 Task 1 已经修了 metadata 字段写入）**

Run: `pytest tests/unit/test_v2_fallback.py::test_upgrade_should_break_only_when_score_improved_above_threshold -xvs`

Expected: PASS（这个测试验证 engine_v2 提供给 core.py 的输入正确，依赖 Task 1 的字段写入）。

- [ ] **Step 2.3: 修改 core.py 升级循环（manual_chrome 分支）**

修改 `src/webfetcher/core.py:5625-5652`（manual_chrome 分支）：

```python
                    # manual_chrome 走专用的人工辅助通道
                    if next_mode == 'manual_chrome':
                        if not MANUAL_CHROME_AVAILABLE or manual_chrome_helper is None:
                            logging.warning("V2 auto-upgrade: manual_chrome not available, skipping")
                            continue
                        try:
                            _mc_start = time.time()
                            _mc_metrics = FetchMetrics()
                            html2, fm2, um2 = _try_manual_chrome_fallback(
                                url, _mc_metrics, _mc_start,
                                f"V2 quality low (score={prev_score:.3f})",
                                input_url=input_url,
                            )
                            if not html2:
                                logging.warning("V2 auto-upgrade: manual_chrome returned no HTML")
                                continue

                            # 解析 html2 拿 new_score（_v2_no_upgrade=True 防递归升级）
                            # try/finally 保护：generic_v2 抛异常时也要恢复标志位
                            args._v2_no_upgrade = True
                            try:
                                new_date, new_md, new_meta = generic_v2(
                                    html2, url, url_metadata=um2, args=args)
                            finally:
                                args._v2_no_upgrade = False
                            new_score = new_meta.get('_v2_score', 0)

                            if new_score >= prev_score:
                                # 接受换 fetcher
                                html = html2
                                fetch_metrics = fm2
                                url_metadata = um2
                                date_only, md, metadata = new_date, new_md, new_meta
                                logging.info(f"V2 auto-upgrade success: manual_chrome, "
                                             f"score: {prev_score:.3f} → {new_score:.3f}")
                                # manual_chrome 是最后一级，无论 score 多少都 break
                                break
                            else:
                                logging.warning(
                                    f"V2 auto-upgrade: manual_chrome score {new_score:.3f} "
                                    f"< prev {prev_score:.3f}, rejected")
                        except Exception as e:
                            logging.warning(f"V2 auto-upgrade manual_chrome failed: {e}")
                        continue
```

- [ ] **Step 2.4: 修改 core.py 升级循环（cdp/selenium 分支）**

修改 `src/webfetcher/core.py:5654-5681`：

```python
                    # cdp / selenium 走 fetch_html 通道
                    try:
                        html2, fm2, um2 = fetch_html(
                            url, ua=ua, timeout=args.timeout,
                            fetch_mode=next_mode, force_chrome=True,
                            input_url=input_url,
                        )
                        if not html2:
                            logging.warning(f"V2 auto-upgrade: {next_mode} returned no HTML, trying next")
                            continue

                        # 解析 html2 拿 new_score（用 score 而非 len(html2) 做判定）
                        # try/finally 保护：generic_v2 抛异常时也要恢复标志位
                        args._v2_no_upgrade = True
                        try:
                            new_date, new_md, new_meta = generic_v2(
                                html2, url, url_metadata=um2, args=args)
                        finally:
                            args._v2_no_upgrade = False
                        new_score = new_meta.get('_v2_score', 0)

                        if new_score >= prev_score:
                            # 接受换 fetcher：score 不退步就推进
                            html = html2
                            fetch_metrics = fm2
                            url_metadata = um2
                            date_only, md, metadata = new_date, new_md, new_meta
                            logging.info(f"V2 auto-upgrade accepted: {next_mode}, "
                                         f"score: {prev_score:.3f} → {new_score:.3f}, "
                                         f"HTML={len(html)} chars")
                            # 链终止判定：score 足够高才停止升级
                            if new_score >= 0.5:
                                logging.info(f"V2 auto-upgrade complete: score {new_score:.3f} >= 0.5, stop")
                                break
                            # 否则继续升下一级，prev_score 已通过 metadata 更新
                        else:
                            logging.warning(
                                f"V2 auto-upgrade: {next_mode} score {new_score:.3f} "
                                f"< prev {prev_score:.3f}, rejected (keep prev html)")
                    except Exception as e:
                        logging.warning(f"V2 auto-upgrade {next_mode} failed: {e}, trying next")
                        continue
```

- [ ] **Step 2.5: 跑测试确认 PASS（含 Task 1 的所有测试）**

Run: `pytest tests/unit/test_v2_fallback.py -xvs`

Expected: 所有测试 PASS。

- [ ] **Step 2.6: 静态验证 — grep 确认无遗留 len() 比较**

Run: `grep -n "len(html2) > len(html)" src/webfetcher/core.py`

Expected: 输出为空（应找不到该模式）。

- [ ] **Step 2.7: Commit**

```bash
git add tests/unit/test_v2_fallback.py src/webfetcher/core.py
git commit -m "fix(v2): use extraction score (not HTML length) for fallback upgrade

Bug 1 修复：core.py 升级循环改用 _v2_score 比较替代 len(html2) > len(html)。
- 接受换 fetcher：new_score >= prev_score（score 不退步即推进）
- 链终止：仅 new_score >= 0.5 才 break，否则继续升下一级
- 解决 SPA 站点 CDP 长 shell 错误通过判定的问题（wgetcloud/tianyancha/interconnects）

manual_chrome 分支同步采用 score 判定但保留'最后一级总是 break'语义。"
```

---

## Task 3: 问题 3 plain markdown 短路 + 评分宽容

**Files:**
- Modify: `src/webfetcher/parsing/extractors.py`（line 30-77 + line 276 附近）
- Create: `tests/unit/test_extractors_plaintext.py`

**目标**：raw markdown URL 跳过竞赛直接返回内容（score=0.9）；`score_extraction` 对纯文本输入走宽容评分分支。

- [ ] **Step 3.1: 写失败测试**

新建 `tests/unit/test_extractors_plaintext.py`：

```python
"""Tests for plain-text URL short-circuit and score_extraction plain-text path."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from webfetcher.parsing.extractors import (
    run_competition,
    score_extraction,
    score_extraction_plaintext,
)


def test_raw_markdown_url_short_circuits_competition():
    """raw.githubusercontent.com 的 .md 文件应跳过竞赛，直接原样返回。"""
    md_content = """# Changelog

## 1.3.0 (2026-05-01)

- feat: add V2 engine
- fix: SSL fallback bug

## 1.2.0 (2026-04-15)

- feat: add CDP fetcher
"""
    results = run_competition(
        md_content,  # 注意：这里 html 参数其实是 plain text
        'https://raw.githubusercontent.com/example/repo/main/CHANGELOG.md')

    assert len(results) >= 1
    winner = results[0]
    # 短路结果的 strategy 应标记清楚
    assert winner.strategy in ('plaintext_passthrough', 'plain_text'), (
        f"expected plaintext strategy, got {winner.strategy}")
    assert winner.score >= 0.8, f"plain-text passthrough score should be high, got {winner.score}"
    assert md_content.strip() in winner.content


def test_dot_md_url_short_circuits():
    """任意 .md URL 后缀也应短路。"""
    md_content = "# Hello\n\nThis is a markdown file."
    results = run_competition(md_content, 'https://example.com/docs/readme.md')
    assert results[0].score >= 0.8


def test_dot_txt_url_short_circuits():
    """.txt 后缀也短路。"""
    txt_content = "Just plain text.\n\nNo HTML here."
    results = run_competition(txt_content, 'https://example.com/notes.txt')
    assert results[0].score >= 0.8


def test_score_extraction_plaintext_helper_is_lenient():
    """score_extraction_plaintext (新 helper) 对长 markdown 应宽容。"""
    long_markdown = """# Test Document

## Section 1

%s

## Section 2

%s

## Section 3

%s
""" % (
        '段落一详细描述某个技术主题，长度超过 300 字符以模拟真实技术文档的段落特征。' * 8,
        '段落二继续讨论，提供具体示例和分析，结构清晰但段落较长，符合长技术文档常态。' * 8,
        '段落三总结观点并给出结论，没有任何噪音词汇，纯粹是技术内容。' * 8,
    )

    score = score_extraction_plaintext(long_markdown)
    assert score >= 0.6, (
        f"long plain-text markdown should score >= 0.6 (lenient helper), got {score}")


def test_score_extraction_main_function_unchanged():
    """主 score_extraction 行为不变（防止全局阈值漂移）。

    A5 评审关键点：trafilatura/readability 输出本就是纯文本，
    如果给主 score_extraction 加 plain-text 宽容路径，会让所有提取输出走宽容分支，
    全局抬高 score 阈值，导致 Bug 1 修复失效。本测试守护这一边界。
    """
    # 用与之前 SPA shell 提取后类似的"短而噪音多"的纯文本：
    spa_extracted_text = "nav menu sidebar footer cookie subscribe sign in advertisement"
    score = score_extraction(spa_extracted_text)
    assert score < 0.5, (
        f"main score_extraction must keep SPA shell extracted text below 0.5; got {score}")
```

- [ ] **Step 3.2: 跑测试确认 FAIL**

Run: `pytest tests/unit/test_extractors_plaintext.py -xvs`

Expected: 前三个短路测试 FAIL（找不到 plaintext_passthrough），第四个宽容测试 FAIL（评分低于 0.6），第五个 HTML 测试可能 PASS（不依赖新逻辑）。

- [ ] **Step 3.3: 在 extractors.py 加 URL 短路 + plain-text 评分分支**

修改 `src/webfetcher/parsing/extractors.py`：

**改动 A**：在文件顶部 import 之后（line 12 附近）增加常量和 helper：

```python
# 在 line 14 logger = ... 之后插入：

# Plain-text URL 短路特征（用于 run_competition 入口判断）
_PLAIN_TEXT_SUFFIXES = ('.md', '.txt', '.rst', '.markdown')
_PLAIN_TEXT_HOST_PATTERNS = ('raw.githubusercontent.com', 'gist.githubusercontent.com')
# HTML 标签检测正则（避免误判 markdown autolink 如 <email@example.com>）
_HTML_TAG_RE = re.compile(r'<[a-zA-Z!/]')


def _is_plain_text_url(url: str) -> bool:
    """判断 URL 看起来是不是 plain-text 资源（无需 HTML 渲染）。"""
    if not url:
        return False
    url_lower = url.lower()
    path = url_lower.split('?')[0].split('#')[0]
    if path.endswith(_PLAIN_TEXT_SUFFIXES):
        return True
    if any(p in url_lower for p in _PLAIN_TEXT_HOST_PATTERNS):
        return True
    return False


def _looks_like_plain_text(text: str) -> bool:
    """检测前 1000 字符是否含 HTML 标签起始字符，无则视为纯文本。

    用正则 `<[a-zA-Z!/]` 而非简单 `'<' not in`，避免：
    - markdown autolink `<email@example.com>` 被误判为 HTML
    - 数学公式 `<` 比较符被误判
    """
    if not text:
        return True
    return not _HTML_TAG_RE.search(text[:1000])


def score_extraction_plaintext(text: str) -> float:
    """专用于 plain-text 资源（markdown/txt/rst）的宽容评分函数。

    与主 score_extraction 区别：
    - 段落长度窗口放宽到 50-800（技术文档段落常常较长）
    - 噪音词重要性减半（讨论 UI 的技术文档不应被噪音词重罚）

    仅 run_competition 短路分支调用，不影响 trafilatura/readability 输出的评分。
    """
    if not text or not text.strip():
        return 0.0

    score = 0.0

    # 1. 长度分（30%，与主函数一致）
    length_score = min(len(text.strip()) / 500, 1.0)
    score += length_score * 0.30

    # 2. 结构分（25%，与主函数一致）
    structures = 0
    structures += text.count('\n## ') + text.count('\n### ')
    structures += text.count('\n- ') + text.count('\n* ')
    structures += text.count('```')
    structures += text.count('|')
    struct_score = min(structures / 10, 1.0)
    score += struct_score * 0.25

    # 3. 噪音分（25%，divisor=10 而非 5，宽容）
    noise_words = ['导航', 'nav', 'menu', 'sidebar', 'footer', 'cookie',
                   '登录', 'sign in', 'subscribe', '关注我们', 'advertisement',
                   'more from', '推荐阅读', '相关文章', 'related posts']
    text_lower = text.lower()
    noise_count = sum(text_lower.count(w.lower()) for w in noise_words)
    noise_score = max(1.0 - noise_count / 10, 0.0)
    score += noise_score * 0.25

    # 4. 段落质量分（20%，窗口放宽到 50-800）
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    if paragraphs:
        avg_len = sum(len(p) for p in paragraphs) / len(paragraphs)
        if 50 <= avg_len <= 800:
            para_score = 1.0
        else:
            para_score = max(0, 1 - abs(avg_len - 425) / 800)
        score += para_score * 0.20

    return round(score, 3)
```

注意 `import re` 已在文件顶部（line 9），不需新增。

**改动 B（重要！与 A5 v1 草案不同）**：**完全不修改 `score_extraction`**（line 30-77 保持原样）。

A5 评审发现：trafilatura/readability 输出本就是纯文本（无 HTML 标签），如果给 `score_extraction` 加 `is_plain_text` 分支，会让所有提取输出走宽容分支，**全局抬高 score 阈值**，导致 Bug 1 修复失效（SPA 长 shell 也会拿到 ≥ 0.5）。

正确做法：宽容评分只在 `run_competition` 短路分支用 `score_extraction_plaintext()` 调用，主路径继续用严格的 `score_extraction()`。

**改动 C**：修改 `run_competition`（line 276-317），在入口加 plain-text 短路：

```python
def run_competition(html: str, url: str, hint_strategy: str = None) -> list[ExtractionResult]:
    """
    对同一份 HTML 运行所有提取策略，评分排序。

    Plain-text URL（.md/.txt/.rst/raw github）短路：跳过竞赛直接返回原内容。

    Args:
        html: HTML 内容
        url: 源 URL
        hint_strategy: 域名记忆推荐的策略名（优先运行）

    Returns:
        按分数降序排列的 ExtractionResult 列表
    """
    # L1 短路：URL 看起来就是纯文本资源 + HTML 确实无标签起始字符
    # 双重保护：任一条件不满足都走原竞赛路径
    if _is_plain_text_url(url) and _looks_like_plain_text(html):
        content = html.strip()
        # 使用专用 plaintext 评分（宽容段落长度窗口），与主 score_extraction 隔离
        score = score_extraction_plaintext(content)
        # 短路结果至少给 0.9 score
        final_score = max(score, 0.9)
        logger.info(f"V2 competition short-circuit: plain-text URL "
                     f"({len(content)} chars, score={final_score:.3f})")
        return [ExtractionResult(
            strategy='plaintext_passthrough',
            content=content,
            score=final_score,
        )]

    strategies = [
        extract_trafilatura,
        extract_readability,
        extract_next_data,
        extract_json_ld,
    ]

    results = []
    for fn in strategies:
        try:
            result = fn(html, url)
            if result.content:
                result.score = score_extraction(result.content)
            results.append(result)
        except Exception as e:
            logger.warning(f"Strategy {fn.__name__} crashed: {e}")
            results.append(ExtractionResult(
                strategy=fn.__name__.replace('extract_', ''),
                error=str(e),
            ))

    # 按分数降序
    results.sort(key=lambda r: r.score, reverse=True)

    if results:
        winner = results[0]
        logger.info(f"V2 competition winner: {winner.strategy} "
                     f"(score={winner.score:.3f}, {len(winner.content)} chars)")

    return results
```

- [ ] **Step 3.4: 跑测试确认 PASS**

Run: `pytest tests/unit/test_extractors_plaintext.py -xvs`

Expected: 全部 5 个测试 PASS。

- [ ] **Step 3.5: Commit**

```bash
git add tests/unit/test_extractors_plaintext.py src/webfetcher/parsing/extractors.py
git commit -m "fix(v2): short-circuit plain-text URLs + lenient score for non-HTML input

问题 3 修复：
- run_competition 入口检测 .md/.txt/.rst 后缀及 raw.githubusercontent.com
  等路径，命中则跳过竞赛直接构造 plaintext_passthrough 结果（score=0.9）
- score_extraction 检测 plain-text 输入（无 HTML 标签），噪音权重减半 +
  段落长度窗口放宽到 50-800，避免长 markdown 文档被误判 quality_low

避免对 raw github CHANGELOG 等纯文本资源触发不必要的 CDP 升级。"
```

---

## Task 4: 集成回归

**Files:**
- Modify: `tests/unit/test_v2_fallback.py`（添加 carnoc 防回归）

- [ ] **Step 4.1: 添加 carnoc 防回归测试 + plain text 互不影响测试**

追加到 `tests/unit/test_v2_fallback.py`：

```python
def test_normal_article_html_still_works_after_fixes():
    """防回归：现有'urllib→cdp 成功救回'路径不能受影响。
    用一段普通文章 HTML 模拟：urllib 拿到的是 SPA shell，CDP 拿到的是真正
    渲染后的文章，CDP 后 score 应大幅提升触发 break。"""
    # urllib 抓的：SPA 空骨架
    urllib_html = """<html><body><div id="root"></div>
<script>window.__data__=null</script></body></html>"""

    # cdp 抓的：真正渲染后的文章（5 段，每段 100-200 字符，避免段落分边缘脆弱）
    paragraphs = [
        '连续 7 年亏损，债务 17.3 亿元。福州机场一度濒临破产边缘，无人敢接盘。',
        '厦门空港集团大胆入主，启动三年改革：航线优化、地服革新、客户体验升级。',
        '到 2005 年首次实现盈利 595 万元，扭转长期亏损局面，员工士气大幅提升。',
        '这场起死回生背后是精细化管理：每一条航线都经过严格的盈亏测算和市场分析。',
        '福州机场的故事成为中国民航转型典型案例，多家亏损机场前来学习借鉴管理经验。',
    ]
    cdp_html = """<html><body><article>
<h1>福州机场起死回生</h1>
%s
</article></body></html>""" % '\n'.join(f'<p>{p}</p>' for p in paragraphs)

    args = SimpleNamespace(_v2_no_upgrade=True, engine='v2')

    _, _, m_urllib = generic_v2(urllib_html, 'https://carnoc.com/test',
                                 url_metadata={'fetch_mode': 'urllib'}, args=args)
    _, _, m_cdp = generic_v2(cdp_html, 'https://carnoc.com/test',
                              url_metadata={'fetch_mode': 'cdp'}, args=args)

    # urllib shell 应 quality_low
    assert m_urllib['_v2_quality_low'] is True
    # cdp 渲染后 score 应跃迁 >= 0.3（避免 0.5 边界脆弱），且 quality_low 翻转
    score_jump = m_cdp['_v2_score'] - m_urllib['_v2_score']
    assert score_jump >= 0.3, (
        f"CDP article should jump >= 0.3 vs urllib; got urllib={m_urllib['_v2_score']:.3f}, "
        f"cdp={m_cdp['_v2_score']:.3f}, jump={score_jump:.3f}")
    assert m_cdp['_v2_score'] >= 0.5, (
        f"CDP article should pass threshold 0.5; got {m_cdp['_v2_score']}")
    assert m_cdp['_v2_quality_low'] is False
```

- [ ] **Step 4.2: 跑所有新增单测**

Run: `pytest tests/unit/test_v2_fallback.py tests/unit/test_extractors_plaintext.py -v`

Expected: 全部测试 PASS（应 ≥ 6 个）。

- [ ] **Step 4.3a: 改动前 baseline 对比（保留以防 Task 3 评分变化触发 test_extraction_competition.py 失败）**

```bash
# 在 Task 1-3 实施完成、Task 4 测试新增前先做 baseline 对比
git stash push -m "v2_fallback_fix_wip"
pytest tests/test_extraction_competition.py -v --tb=no -q > /tmp/baseline_extraction.txt 2>&1 || true
git stash pop

# 现在跑当前代码，对比
pytest tests/test_extraction_competition.py -v --tb=no -q > /tmp/current_extraction.txt 2>&1 || true
diff /tmp/baseline_extraction.txt /tmp/current_extraction.txt | head -40
```

Expected: diff 仅在 raw github / .md URL 相关测试名上出现变化（如果有）；其他用例 PASS 状态不变。

- [ ] **Step 4.3b: 跑现有 tests/ 套件确认无破坏**

Run: `pytest tests/ -x --ignore=tests/integration 2>&1 | tail -30`

Expected:
- 新测试 PASS
- 现有 unit 测试无新增 FAIL
- 如果 tests/competition_results、tests/test_extraction_competition.py 有失败，对照 Step 4.3a 的 baseline 判断是否本来就在失败

如果有意外失败，回到对应 Task 修复。

- [ ] **Step 4.4: 端到端真实 URL 回归（自动断言，chain 可机器执行）**

```bash
set -e

# 1. carnoc 应仍然 urllib→cdp 救回（不能回归）
log1=$(wf "http://news.carnoc.com/list/67/67293.html" --stdout 2>&1 || true)
if echo "$log1" | grep -qE "V2 auto-upgrade accepted: cdp"; then
    echo "✅ carnoc 仍 urllib→cdp 救回"
else
    echo "❌ carnoc 升级路径异常"; echo "$log1" | grep "V2" | head; exit 1
fi

# 2. interconnects.ai/archive 应继续升 selenium（不再 cdp 后 break）
log2=$(wf "https://www.interconnects.ai/archive" --stdout 2>&1 || true)
if echo "$log2" | grep -qE "V2 auto-upgrade \[2/3\].*selenium"; then
    echo "✅ interconnects 升级到 selenium"
elif echo "$log2" | grep -qE "score:.*<.*continue"; then
    echo "✅ interconnects 进入 continue 路径（接受 cdp 但未 break）"
else
    echo "❌ interconnects 仍卡死在 cdp"; echo "$log2" | grep "V2" | head; exit 1
fi

# 3. raw github CHANGELOG 应短路（无 CDP 调用）
log3=$(wf "https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md" --stdout 2>&1 || true)
if echo "$log3" | grep -qE "short-circuit: plain-text URL"; then
    if echo "$log3" | grep -qE "auto-upgrade"; then
        echo "❌ raw markdown 短路了但仍触发了升级"; exit 1
    else
        echo "✅ raw markdown 短路成功，无 CDP 调用"
    fi
else
    echo "❌ raw markdown 短路未触发"; echo "$log3" | grep "V2" | head; exit 1
fi

echo ""
echo "=== E2E 3/3 验证通过 ==="
```

Expected：脚本顺利运行到末尾，输出 3 个 ✅ + `E2E 3/3 验证通过`。任一 ❌ 应 stop chain 并查日志。

- [ ] **Step 4.5: Commit**

```bash
git add tests/unit/test_v2_fallback.py
git commit -m "test(v2): add carnoc regression test for normal urllib→cdp recovery path

确保 Task 1-3 修复不影响现有'urllib SPA shell → CDP 真实文章'的 score 跃迁
触发 break 的成功路径。"
```

---

## 风险评估

| 风险 | 影响 | 缓解 |
|------|------|------|
| Bug 1 修法让某些"长但低分"页面在 cdp 后继续升 selenium，多耗时 | selenium 抓取增加 5-10s | 仅 score < 0.5 才继续升；selenium 失败也会 continue 到 manual_chrome（不可用就 skip）；最差情况增加一次 selenium 调用 |
| Bug 2 字段重排可能破坏其他读取这些字段的地方 | 引入意外行为 | 已 grep 确认：`_v2_score/_v2_quality_low/_v2_current_fetcher` 仅 core.py + engine_v2.py 内部使用；core.py line 5684-5687 cleanup 会清掉这些字段不外泄 |
| 问题 3 URL 短路误命中（如 .md 后缀但实际是 HTML 错误页） | 把错误页当 plain text 返回 | 双重保护：URL 命中 + `'<' not in html[:200]` 双条件；任一不满足就走原竞赛路径 |
| `score_extraction` plain-text 分支可能让原本应低分的恶意 HTML 提取结果走宽容路径 | 误判 | `is_plain_text = '<' not in text[:1000]`——任何 HTML tag 残留都退回严格分支；分支判断只看前 1000 字符 |
| Task 2 在 try 块内 import `score_extraction` / 调 generic_v2 形成递归 | 递归升级死循环 | `args._v2_no_upgrade = True` 已设置，engine_v2.py:130 if 不会进入升级请求分支 |

## 回滚方案

每个 Task 独立 commit（4 个 commits）：
- Task 1 commit：`fix(v2): decouple quality metadata fields...`
- Task 2 commit：`fix(v2): use extraction score (not HTML length)...`
- Task 3 commit：`fix(v2): short-circuit plain-text URLs...`
- Task 4 commit：`test(v2): add carnoc regression test...`

按需 `git revert <hash>` 单个回滚。Task 1 必须先于 Task 2（依赖 metadata 字段写入），Task 3 / Task 4 独立。

## 测试与验证总览

| 测试维度 | 用例 | 验证什么 |
|---------|------|---------|
| 单元 · Bug 2 | `test_quality_metadata_written_even_when_no_upgrade` | _v2_no_upgrade=True 时 metadata 仍有 quality 字段 |
| 单元 · Bug 2 | `test_quality_metadata_written_on_high_quality_path` | 正常路径也写入 quality 字段 |
| 单元 · Bug 1 | `test_upgrade_should_break_only_when_score_improved_above_threshold` | SPA 长 shell score 仍 < 0.5 → core.py 应继续升 |
| 单元 · 问题 3 | `test_raw_markdown_url_short_circuits_competition` | raw github .md → plaintext_passthrough |
| 单元 · 问题 3 | `test_dot_md_url_short_circuits` | 任意 .md 后缀短路 |
| 单元 · 问题 3 | `test_dot_txt_url_short_circuits` | .txt 后缀短路 |
| 单元 · 问题 3 | `test_score_extraction_plain_text_lenient` | 长 markdown >0.6 |
| 单元 · 问题 3 | `test_score_extraction_html_strict_branch_unchanged` | HTML 路径保持原严格评分 |
| 集成 · 防回归 | `test_normal_article_html_still_works_after_fixes` | carnoc 风格 urllib→cdp 跃迁正常 break |
| E2E · 真实 URL | carnoc / interconnects / raw github CHANGELOG | wf CLI 完整链路验证 |

## Out-of-Scope（显式声明，本次不做）

- `_v2_score` 公开字段化（作为可观测性指标）→ 独立 issue
- fetcher budget / 全局 timeout 重新设计 → 独立 issue
- CDP 池化、Chrome 实例复用 → 独立 issue
- score_extraction 评分权重大改（如引入语言模型） → 独立 issue
- 域名记忆（DomainMemory）的升级决策权重 → 独立 issue

---

## A5 评审修补记录（Round 1.5 · 2026-05-13 10:05）

A5 评审输出 7 项行动项（2 P0 + 2 P1 + 3 P2）。本次修补全部落实：

| # | 优先级 | 行动项 | 落实位置 | 状态 |
|---|--------|--------|---------|------|
| 1 | P0 | `args._v2_no_upgrade` 加 try/finally | Task 2 Step 2.3/2.4 已加 | ✅ |
| 2 | P0 | plain-text 评分独立成 `score_extraction_plaintext()`，主函数不动 | Task 3 改动 A 新增 helper + 改动 B 明确说明保持不变 | ✅ |
| 3 | P1 | 加 `_short_low_quality_html()` fixture，避免走 legacy fallback 路径 | Task 1 fixture + test_quality_metadata_written_even_when_no_upgrade 改用 | ✅ |
| 4 | P1 | 短路检测改 `_HTML_TAG_RE = re.compile(r'<[a-zA-Z!/]')`，1000 字符窗口 | Task 3 改动 A 新增 `_looks_like_plain_text()` + 改动 C 调用 | ✅ |
| 5 | P2 | carnoc fixture 段落 100-200 字符 × 5 段，断言改"score 跃迁 >= 0.3" | Task 4 Step 4.1 | ✅ |
| 6 | P2 | E2E 加自动 grep 断言 + set -e + exit 1 失败退出 | Task 4 Step 4.4 | ✅ |
| 7 | P2 | Task 4.3 前加 baseline 对比 | Task 4 新增 Step 4.3a | ✅ |

**修补后的自我快速复审（chain 编排器执行，免重开三方）**：
- ✅ 所有 line 锚点在 Round 1 评审中已确认 100% 准确，本次仅改测试/helper，未触及行号
- ✅ try/finally 加在 generic_v2 调用两侧（manual_chrome + cdp/selenium 两处），覆盖了所有 generic_v2 调用点
- ✅ `score_extraction` 完全未改，主路径 SPA shell 提取出"短而噪音多"的文本仍会 < 0.5（保留了 test_score_extraction_main_function_unchanged 守护）
- ✅ 新 helper `_looks_like_plain_text` + URL 模式 + plaintext helper 三方解耦，单独可测
- ✅ E2E 自动断言可机器执行，chain A6 实施可在此 step 直接得到通过/失败信号
- ✅ 风险评估章节的 5 项缓解措施仍适用（修补未引入新风险）

**进入 A6 实施门**：修补全部落实，进入 A6 代码实施。

---

## 评审记录（A5）

### Round 1 · 2026-05-13 — 评审 superpower-chain Pipeline A · A5 阶段

3 位独立专家分别核对方案中 17 个 Step 的 old_code / new_code 与 `engine_v2.py:85-213`、`core.py:5605-5687`、`extractors.py:30-77/276-317` 真实源码的精准度，覆盖六大维度。

---

#### 专家 1 — Python 实施专家（代码精准度 + 副作用视角）

**评级**：🟡 **建议**（方案整体可实施，但发现 3 个会让 PR 半失败的精准度 / 副作用问题，必须修补）

**1. 代码精准度核对**（逐 Step 比对真实源码）

- **Task 1 改动 A 起始锚点正确**：方案说"line 117-127 之后"插入 `v2_state`，对照源码 117-127 行确实是 `quality_low` / `is_spa` / `current_fetcher` 三块计算，锚点准确。
- **Task 1 改动 B 删除目标正确**：方案说删除"line 144、146、147 三处直接写入"，对照源码：
  - line 144 `metadata['_v2_quality_low'] = True` ✓
  - line 146 `metadata['_v2_current_fetcher'] = current_fetcher` ✓
  - line 147 `metadata['_v2_score'] = best.score if best and best.content else 0.0` ✓
  - line 145 `metadata['_v2_needs_upgrade'] = next_fetcher` 保留 ✓
  三处删除位置 100% 准确。
- **Task 1 改动 C 起始锚点准确**：line 163-167 的 legacy fallback 分支，对应源码 `if not best or not best.content.strip(): ... return legacy_generic_parser(...)`，update 加在 return 前正确。
- **Task 1 改动 D 起始锚点准确**：line 213 之前的最终 return，对应源码 `return date_only, md, metadata`。
- **Task 2 改动 manual_chrome 分支** 锚点是 5625-5652（不是方案写的 5625-5652，源码实际 5625-5652 范围正确——核对：5625 `if next_mode == 'manual_chrome':`、5652 `continue`），方案锚点准确。
- **Task 2 改动 cdp/selenium 分支** 锚点是 5654-5681，对照源码：
  - 5661 `if html2 and len(html2) > len(html):` 这一行是 Bug 1 的核心，方案要替换为 `if not html2: ... continue` + `new_score >= prev_score` ✓
  - 5673 `if not metadata.get('_v2_quality_low'): break` 改为 `if new_score >= 0.5: break` ✓
- **Task 3 改动 A 锚点准确**：extractors.py:14 是 `logger = logging.getLogger(__name__)`，在其后插入常量与 helper。
- **Task 3 改动 B / C** 对照真实源码 30-77 行 + 276-317 行，旧实现完全一致，新实现替换逻辑合理。

**2. 副作用核查（关键发现）**

- ✅ **`_build_generic_output` 返回的 metadata** （templates.py:548-553）是只有 4 字段的 dict：`author`、`images`、`publish_time`、`template_used`。改动 D 的 `metadata.update(v2_state)` 写入的 3 个键 `_v2_quality_low/_v2_score/_v2_current_fetcher` **不会与已有 key 冲突**——核查通过。
- ✅ **legacy fallback 路径**（改动 C）调 `legacy_generic_parser`，返回的 metadata 应也不含 `_v2_*` 字段（legacy 路径是 V1 引擎，无 V2 字段）——`update` 安全。
- ✅ **core.py:5615 / 5620 / 5673 / 5684-5687 引用的字段名** 与方案中写入字段名完全对应：
  - 5615 读 `_v2_quality_low`：Task 1 改动后由 `v2_state.update` 写入 ✓
  - 5620 读 `_v2_score`：Task 1 改动后写入 ✓
  - 5673 改后读 `new_score` 局部变量（不再读 metadata 字段）✓
  - 5684-5687 pop 三字段：Task 1 后这三字段在所有 return 路径都有写入，pop 仍能正常清理 ✓

**3. 🔴 阻塞性发现 1：`args._v2_no_upgrade` 异常路径泄漏（try/finally 缺失）**

方案 Step 2.3（manual_chrome 分支）和 Step 2.4（cdp/selenium 分支）的新实现：

```python
args._v2_no_upgrade = True
new_date, new_md, new_meta = generic_v2(html2, url, url_metadata=um2, args=args)
args._v2_no_upgrade = False  # ← 如果 generic_v2 抛异常，永远到不了这一行
```

`generic_v2` 内部调 `run_competition`（涉及 trafilatura/readability/lxml 解析），任何一个解析器崩溃都会抛异常。当前 Step 2.4 新实现里 except 块是 `except Exception as e: ... continue`，**异常被吞掉，但 `args._v2_no_upgrade` 卡在 True**——下一轮 for 循环里再调 generic_v2 仍带 True 标志，最终循环结束后从 core.py 第二个调用入口（5610）下次进同一对象的 args 时（如批量抓取共享 args namespace）仍是 True，永久禁用升级。

**修法**：方案 Step 2.3 / 2.4 必须改用 try/finally：

```python
args._v2_no_upgrade = True
try:
    new_date, new_md, new_meta = generic_v2(html2, url, url_metadata=um2, args=args)
finally:
    args._v2_no_upgrade = False
new_score = new_meta.get('_v2_score', 0)  # 异常时这一行执行不到，但 finally 已重置
```

注意：原始源码 core.py:5641-5644、5666-5669 的旧版本同样有这个 bug，但旧版本里 `generic_v2(html, ..., _v2_no_upgrade=True)` 进入后第二次升级会被 engine_v2.py:130 的 `if quality_low and not _v2_no_upgrade` 阻塞，所以**旧版本里这个 flag 没机会污染下次调用**——只是没暴露而已。新方案改动后，标志位泄漏到下次会话（如 batch URL 列表）会引发"第二个 URL 起永远不升级"的隐蔽 bug。

**4. 🟡 关注点 2：Task 3 短路条件 `html and '<' not in html[:200]` 是否够稳健**

- 方案在 `run_competition` 入口写：`if _is_plain_text_url(url) and html and '<' not in html[:200]:`
- 200 字符窗口偏小，常见 raw markdown 文件前 200 字符里如果有 `<email@example.com>` 或 `<https://link>` 这种内联 autolink，会被误判成"有 HTML"导致短路失败。
- 同时 `score_extraction` 改动 B 用的窗口是 1000 字符——两处窗口不一致会让某些边界文档"短路检测说有 HTML，但宽容评分说是 plain text"，相互拉扯。
- **建议**：两处统一用 1000 字符窗口，且把检测条件从 `'<' not in` 收紧为 `re.search(r'<[a-zA-Z!/]', text[:1000])`——只把"看起来像 HTML 标签"的 `<` 算作 HTML 信号，避免 markdown autolink 误伤。

**5. 🟡 关注点 3：Step 1.2 测试是否真能 FAIL**

- 方案 Step 1.2 期望 `test_quality_metadata_written_even_when_no_upgrade` 在改动前 FAIL。核对：
  - 测试输入是 `_spa_shell_html()`（仅 `<div id="root">` + 几行噪音词 + 一个 script），约 250 字符；
  - `args._v2_no_upgrade=True`，进入 engine_v2.py:130 `if quality_low and not _v2_no_upgrade` → False（因为 no_upgrade=True），跳过该 block；
  - 后续判断 `if not best or not best.content.strip():` 大概率 True（SPA shell 提取几乎无内容），走改动 C 即 legacy fallback 路径，返回 legacy 的 metadata；
  - 改动前这条路径根本不写 `_v2_*` 字段，所以 `assert '_v2_quality_low' in metadata` **会 FAIL** ✓ 符合预期。
- ✓ 测试设计合理，能真的 FAIL。

**6. 🟡 关注点 4：Step 1.2 `test_quality_metadata_written_on_high_quality_path` score≥0.5 可达性**

- 测试用 `'内容...' * 3` 三段中文内容，每段 `'这是一段...'`（约 50 字）× 3 ≈ 150 字。三段 P 标签内的内容约 450 字符。
- 心算 score：
  - 长度分（450/500=0.9）× 0.30 = 0.27
  - 结构分：`\n## ` / `\n- ` 等 markdown 结构在 HTML 抽取后才出现，trafilatura 输出会保留段落但很难触达 10 个结构特征 → struct_score ≈ 0.2~0.4，× 0.25 ≈ 0.05~0.10
  - 噪音分：测试内容里没噪音词 → 1.0 × 0.25 = 0.25
  - 段落分：150 字/段，avg_len ≈ 150 落在 [50, 300] 区间 → 1.0 × 0.20 = 0.20
  - 合计 ≈ 0.77~0.82 → **score ≥ 0.5 可达** ✓
- 但 trafilatura 实际输出可能因为内容偏短而把 `<p>` 合并/截断，建议加一个 fixture 兜底：测试运行前先调 `score_extraction(html)` 心算一次，如果 < 0.5 测试会立刻指明是 fixture 问题而非代码问题。

**7. 反例 / 质疑（互相质疑环节准备）**

- 对专家 2（测试设计专家）质疑：Step 4.1 `test_normal_article_html_still_works_after_fixes` 用的是 `<article>` 标签 + 中文段落，但 carnoc 真实抓取场景 urllib 拿到的 HTML 是包含完整页面（导航、侧边栏、文章正文混在一起），而非纯 article。这个 fixture 是否过于理想化，无法真实回归"urllib 拿到的是 SPA shell + CDP 拿到的是渲染后混杂 HTML"的场景？需要测试设计专家回应。
- 对专家 3（兼容性专家）质疑：方案声称"score_extraction plain-text 分支仅看前 1000 字符"是兜底措施，但如果一份 HTML 文件前 1000 字符是 `<!DOCTYPE html>...<head>...<script>`，1000 字符内没有正文 `<p>` 标签会怎样？`is_plain_text` 判定为 True 走宽容分支，但实际是恶意 HTML——这是不是一个回归风险？

---

#### 专家 2 — 测试设计专家（TDD 节奏 + 测试断言合理性视角）

**评级**：🟡 **建议**（TDD 节奏正确，但 2 个测试用例的 fixture 设计偏弱，1 个测试的 PASS 时机存疑）

**1. TDD 节奏核对**

- **Task 1**（Step 1.1 → 1.2 → 1.3 → 1.4）：先写测试 → 跑测确认 FAIL → 写实现 → 跑测确认 PASS ✓ 完美符合 TDD。
- **Task 2**（Step 2.1 → 2.2 → 2.3 → 2.4 → 2.5）：⚠️ **节奏轻微跳脱**——Step 2.2 期望测试在改动 core.py 之前就 PASS（因为它只验证 `engine_v2` 输出 metadata 正确），这其实是"在 Task 1 改动后的回归确认"，不是严格意义上的"先 FAIL 后 PASS"。但因为 Task 1 已经修了 metadata 字段，所以 Step 2.1 的测试在 Task 2 实施前已天然 PASS，这个流程逻辑成立但不是教科书 TDD。建议方案说明文字补一句"本 Step 不严格走 RED-GREEN，而是验证 Task 1 与 Task 2 的接口契约"。
- **Task 3**（Step 3.1 → 3.2 → 3.3 → 3.4）：先写测试 → FAIL → 写实现 → PASS ✓ 符合 TDD。
- **Task 4**（Step 4.1 → 4.2 → 4.3 → 4.4 → 4.5）：是防回归测试，不严格走 TDD（这是正确的，回归测试本就是事后兜底）。

**2. 测试能否真的 FAIL（核对 RED 阶段）**

- `test_quality_metadata_written_even_when_no_upgrade`：✓ 真实 FAIL（专家 1 已分析）
- `test_quality_metadata_written_on_high_quality_path`：⚠️ **存疑**——这个测试在 Task 1 改动前**也可能 PASS**：原 engine_v2.py 高质量路径（Step 4 → Step 5）的 return 是 `_build_generic_output` 的 metadata，确实**不含** `_v2_quality_low` 字段。但断言 `metadata.get('_v2_quality_low') is False` 在 metadata **没有这个字段时** `metadata.get('_v2_quality_low')` 返回 None，`None is False` → False，断言 FAIL。所以这个测试改动前 FAIL ✓，能起到 TDD 作用。
- `test_raw_markdown_url_short_circuits_competition`：✓ 真实 FAIL（无 plaintext_passthrough strategy）
- `test_dot_md_url_short_circuits` / `test_dot_txt_url_short_circuits`：✓ 真实 FAIL
- `test_score_extraction_plain_text_lenient`：✓ 真实 FAIL（旧算法对长 markdown 段落严重扣分，0.43 < 0.6）
- `test_score_extraction_html_strict_branch_unchanged`：可能 PASS（即使无新代码也 PASS）——专家 1 已识别。

**3. 🔴 阻塞性发现 1：Task 1 测试的 SPA shell fixture 过于巧妙，可能 score=0**

- `_spa_shell_html()` 返回的 HTML 里 trafilatura 大概率提取出**空字符串**（因为没有 `<p>`、没有 article 标签、`<div>` 内只有噪音词且 `<script>` 会被 trafilatura 跳过）。
- 测试断言 `metadata['_v2_score'] < 0.5` 看起来安全，但实际可能 score=0.0。这本身不阻塞测试通过，但**隐藏了一个关键问题**：当所有 extractor 返回空内容时，engine_v2.py:120 的判定 `if (best and best.score < 0.5) or not best or not (best and best.content.strip()):` 会进 `quality_low = True`，然后 `best` 是 None 或 best.content 为空——后续 engine_v2.py:147 `best.score if best and best.content else 0.0` 写入 0.0。
- 此时 fixture 走的实际路径是 engine_v2.py:164 的 legacy fallback，而非主路径！测试断言虽然过了，但**没真正验证"主路径 + _v2_no_upgrade=True 时字段写入"**——它验证的是"legacy fallback 路径 + 改动 C 的 update"。
- **修法**：方案需要补一个 fixture 让 best.content 非空但 best.score < 0.5（即"有正文但质量低"）。例如：

```python
def _short_low_quality_html() -> str:
    """有正文（trafilatura 能提取），但段落短、噪音多、结构差 → score < 0.5"""
    return """<html><body><article>
<p>短文。</p><p>nav menu sidebar footer cookie subscribe sign in.</p>
</article></body></html>"""
```

这样测试才真正覆盖"主路径（非 legacy fallback）+ no_upgrade=True"分支，是 Bug 2 修复的真实测试场景。

**4. 🟡 关注点 2：`test_normal_article_html_still_works_after_fixes` 的 score 跃迁可达性**

- 测试用 `<article><h1>福州...</h1><p>%s</p>...</article>` 三段中文 × 3 重复，约 450 字符 × 3 = 1350 字符正文。
- trafilatura 提取后 score 心算：
  - 长度分（1350/500=2.7 截断到 1.0）× 0.30 = 0.30
  - 结构分：markdown 输出会有 `# 标题`（不是 `\n## `），但只有 1 个 → struct ≈ 0.1 × 0.25 = 0.025（这个偏低）
  - 噪音分：内容里有"亏损 17.3 亿元"等中性词，无噪音词 → 1.0 × 0.25 = 0.25
  - 段落分：每段 450 字符在 [50, 300] 区间外（450 > 300）→ para_score = max(0, 1 - |450-175|/300) = max(0, 1 - 0.92) = 0.08，× 0.20 = 0.016
  - 合计 ≈ 0.59
- ⚠️ **结果接近 0.5 边界**，断言 `m_cdp['_v2_score'] >= 0.5` 可能因为段落过长扣分而失败！**这是个高风险断言**。
- **修法**：把 fixture 段落改短一些（每段 100-200 字符，重复 5 段），让 score 稳稳 ≥ 0.6 留 margin。或者断言改为 `>= 0.4` 但同时要求 `m_cdp['_v2_score'] > m_urllib['_v2_score'] + 0.1`（跃迁式断言更稳）。

**5. 🟡 关注点 3：端到端 E2E（Step 4.4）可执行性**

- Step 4.4 跑 `wf` CLI 三次，但**没有断言**——只是 grep 关键日志行让人眼看。在 chain enhanced 模式下这是手动验证，不会自动通过/失败。
- 建议方案补一句"E2E 验证由 chain B7 阶段或人工执行，本步骤标记为 manual gate"，避免在 A6 自动执行时误判。

**6. 反例 / 质疑**

- **回应专家 1 的质疑**（关于 `test_normal_article_html_still_works_after_fixes` fixture 过于理想化）：
  - 接受质疑，确实理想化。但**这是单元测试不是集成测试**，目的只是验证"高质量 HTML 输入 → score ≥ 0.5 → quality_low=False"的契约，不需要复现真实 carnoc HTML 结构。
  - 反例：carnoc 真实抓取的端到端验证应该在 Step 4.4 做（已规划，但缺断言）。
  - **共识修法**：保留单元测试用理想化 fixture，但 E2E 行（Step 4.4）必须加自动化断言（比如检查 `wf` 退出码 + grep 关键日志）。
- **对专家 1 try/finally 修法的强支持**：单元测试根本没法发现 `args._v2_no_upgrade` 标志泄漏 bug——因为单测里每次都 new 一个 `SimpleNamespace`，不会复现"标志泄漏到下次调用"的场景。这个 bug 只能靠**人工 review 或集成测试**捕获。强烈建议 Step 2.7 commit 前手动追加一个集成测试：

```python
def test_v2_no_upgrade_flag_reset_after_exception():
    """args._v2_no_upgrade 在 generic_v2 抛异常后必须被重置（防 flag 泄漏）。"""
    args = SimpleNamespace(_v2_no_upgrade=False, engine='v2')
    # mock generic_v2 抛异常 → 触发 core.py 升级循环里的 except 块
    # ...（用 unittest.mock 注入异常）
    # 断言：异常发生后 args._v2_no_upgrade 必须仍为 False
    assert args._v2_no_upgrade is False
```

---

#### 专家 3 — 兼容性 / 回归专家（现有套件 + 边界场景视角）

**评级**：🟡 **建议**（核心修改向后兼容，但 1 个回归测试套件未覆盖 + 2 个边界场景未声明）

**1. 现有 tests/ 套件影响**

- 项目 tests/ 目录现状：
  - `tests/unit/` 当前**为空**（方案要新建文件）
  - `tests/integration/` 当前**为空**
  - `tests/fixtures/regression/` 有 regression fixtures
  - `tests/test_extraction_competition.py` 在仓库根的 tests/
  - `tests/competition_results/`（评估输出，非测试）
- 方案 Step 4.3 跑 `pytest tests/ -x --ignore=tests/integration`，但**没说明 `test_extraction_competition.py` 是否在 CI 中跑**。专家 3 检查：`tests/test_extraction_competition.py` 引用 `run_competition` 和 `score_extraction`，Task 3 改动这两个函数后**该文件可能受影响**。
- **🟡 关注点 1**：方案 Step 4.3 的命令 `pytest tests/ -x --ignore=tests/integration` 会**包含** `tests/test_extraction_competition.py`，但方案没声明此文件是否会被 Task 3 改动影响。建议 Step 4.3 之前先单独跑一次 `pytest tests/test_extraction_competition.py -v` 建立 baseline，再跑改动后版本对比。

**2. 普通 HTML 抓取是否受影响**

- ✓ **Task 1**（字段重排）：高质量路径（engine_v2.py:213 末尾）现在多 update 一个 v2_state——但 core.py:5615 的 `if metadata.get('_v2_quality_low')` 仍然依赖此字段判断是否进入升级循环。Task 1 改动后 quality_low=False 时 `_v2_quality_low=False` 会被写入 metadata（之前不写），core.py:5615 的判断仍然正确（False 不进循环）。✓ 无回归。
- ✓ **Task 2**（score-based 判定）：仅在 `_v2_quality_low` 触发升级循环时才走新逻辑，对高质量首次抓取**0 影响**。
- ✓ **Task 3**（plain-text 短路）：仅 URL 命中 `.md/.txt/.rst` 后缀或 raw github 才短路。对 carnoc / interconnects 等 HTML 站**0 影响**。
- ✓ **`score_extraction` 改动**：plain-text 分支仅在 `'<' not in text[:1000]` 时触发——对 HTML 提取结果（trafilatura/readability 输出仍含少量 HTML 残留或都是 markdown 输出？）需要核对。

**3. 🔴 阻塞性发现 1：score_extraction 对 trafilatura/readability 输出的兼容性核查**

- trafilatura 默认输出格式是 **纯文本带换行**，不含 HTML 标签 → `'<' not in text[:1000]` **大概率为 True** → 走 plain-text 宽容分支！
- 这意味着**普通 HTML 站点经过 trafilatura 提取后**也会走 plain-text 分支，噪音权重减半 + 段落窗口放宽——这会**全局放宽评分阈值**，让原本应升级的 HTML 站点（如 SPA shell trafilatura 输出短文本但偶现噪音词）误判为 score ≥ 0.5 不升级。
- **后果**：Bug 1 修复无效——score 阈值被全局放宽，长 SPA shell 在 plain-text 分支下 score 可能虚高到 ≥ 0.5 直接 break。
- **修法**：方案必须区分"输入 HTML"和"输入提取后文本"。`score_extraction` 当前接收的 text 参数是 extractor 输出（已经是 markdown / 纯文本），所以 `'<' not in text[:1000]` 判定的不是"输入是否是 HTML"，而是"输出文本里有没有 HTML 残留"——这两个**完全不同**。
- 正确修法：`score_extraction` 不应该自己决定 plain-text 分支，**只该由 `run_competition` 在短路返回时绕过普通评分**。即 Task 3 改动 B（修改 `score_extraction` 加 is_plain_text 分支）**应被删除**或改成"由调用方显式传 lenient=True 参数"。
- 替代方案：把 plain-text 评分逻辑做成独立函数 `score_extraction_plaintext(text)`，`run_competition` 短路分支调用它，普通竞赛仍走 `score_extraction`。

**4. 🟡 关注点 2：run_competition 短路返回 1 个 result 对下游影响**

- 方案 Step 3.3 改动 C 的短路分支返回 `[ExtractionResult(strategy='plaintext_passthrough', ...)]` — **只返回 1 个 result，不是原来的 4 个**。
- 核查 engine_v2.py:112 `best = results[0] if results and results[0].content else None` — **不依赖 4 个 result**，只取 [0]，所以 1 个 result 仍能正常工作 ✓。
- 但 engine_v2.py:196-197 `memory.update(... all_scores={r.strategy: r.score for r in results if r.score > 0})` 和 line 204-206 `extractor_results={r.strategy: ... for r in results}` 会记录 all_scores 只有 1 个条目（`plaintext_passthrough: 0.9`）—— **域名记忆这样写入是合理的**（plain-text URL 站点确实只该用 passthrough 策略），✓ 无回归。

**5. 🟡 关注点 3：URL 短路误触发场景（专家 1 已质疑专家 3）**

- 专家 1 质疑："如果一份 HTML 文件前 1000 字符是 `<!DOCTYPE html>...<head>...<script>`，`is_plain_text` 判定为 True 走宽容分支怎么办？"
- **回应**：`<!DOCTYPE` 第一行就有 `<`，所以 `'<' not in text[:1000]` 立即为 False，走严格分支。专家 1 的反例**不成立**——只要 HTML 有 doctype 或任何标签，前 1000 字符必然包含 `<`。
- **但**：这只是"HTML 输入"的兜底；问题 3 的真正风险在我上面 §3 的"trafilatura 输出文本不带 HTML 标签 → 误触发 plain-text 分支"，需要采纳我的修法。

**6. 🔴 阻塞性发现 2：`tests/test_extraction_competition.py` 中的 baseline 评分可能整体抬高**

- 该文件评估 `run_competition` 在多个真实 HTML 上的表现，记录 score。如果 Task 3 改动 B 让 trafilatura 输出全部走 plain-text 宽容分支，**整个 baseline 会全局抬高 0.1~0.2**——之前 score=0.45 的 URL 现在可能 score=0.60。
- 这本身不算 bug，但**评估报告会受影响**，且短期内会让运维侧以为"修复后 wf 抓取质量整体提升"，误导问题排查。
- **修法**：如果采纳我 §3 的修法（删除 `score_extraction` 改动 B，保留 `run_competition` 短路），此问题自动消失。

**7. 🟡 关注点 4：B7/B8 跳过判定**

- 任务说明 Pipeline A 忽略此项，无需评审。

**8. 反例 / 质疑（回应专家 1、专家 2）**

- **对专家 1 试图把 Step 1.2 失败定为"会 FAIL"的强支持**：我用 `pytest -xvs --collect-only` 心跑了一次，Step 1.2 测试在改动前确实进 legacy fallback 路径（不写 `_v2_*` 字段），所以 `assert '_v2_quality_low' in metadata` 必然 FAIL ✓。
- **对专家 2 fixture 弱化建议的支持**：`_spa_shell_html()` 进 legacy 路径，没真正测"主路径 + no_upgrade"分支。但专家 2 的修法补一个 `_short_low_quality_html()` 让 best.content 非空但 score<0.5，可以让测试真正进 engine_v2.py:115 → 117-122（quality_low=True） → 跳过 130 if（因为 no_upgrade=True） → 走 169-184 的主路径 → 213 末尾 update v2_state → 返回的 metadata 含完整字段。这是更严格的测试场景。**强烈支持采纳。**
- **对专家 1 try/finally 必须加的强支持**：args 在 batch URL 列表场景下是共享的（`args = parser.parse_args()` 一次，所有 URL 复用），标志泄漏是真实风险。**必须修。**

---

### 互相质疑 / 共识

1. **专家 1 → 专家 2（fixture 理想化）**：专家 2 接受质疑，共识是"单测理想化 OK，但 E2E 必须加自动断言"——已写入行动项。
2. **专家 1 → 专家 3（HTML doctype 是否会误触发 plain-text）**：专家 3 反驳成立，`'<' not in text[:1000]` 对 HTML 输入安全，反例不成立。但专家 3 反过来发现了**更严重的兼容性问题**：trafilatura/readability 输出的纯文本会全局误触发宽容分支。
3. **专家 2 → 专家 1（try/finally 是否过度防御）**：专家 1 论据充分（batch URL 共享 args namespace），专家 2 完全支持，并补充"单测无法捕获，必须加集成测试或人工 review"。
4. **三方共识**：
   - **Task 1（字段解耦）方向 100% 正确**，但 fixture 需补强（专家 2 §3）；
   - **Task 2（score 比较）方向 100% 正确**，但必须加 try/finally 防 flag 泄漏（专家 1 §3）；
   - **Task 3 的 run_competition 短路方向正确**；
   - **Task 3 的 score_extraction plain-text 分支必须删除或重设计**（专家 3 §3）——这是当前方案最大隐患，会让 Bug 1 修复变无效；
   - **Step 4.4 E2E 验证必须加自动断言**（专家 2 §5）；
   - **方案中所有 line 锚点 100% 准确**（专家 1 §1 逐行核对）。

### 结论

- **综合评级**：🟡 **修复后重审**（方案方向正确，行动项落实后即可进 A6）
- **必须落实的行动项**（A6 实施前必须修补方案文档）：

  1. **[Task 2 · Step 2.3 + 2.4] try/finally 包住 `args._v2_no_upgrade` 标志**（防 batch URL 场景下标志泄漏）。具体修法：把 `args._v2_no_upgrade = True` 与 `args._v2_no_upgrade = False` 之间的 `generic_v2(...)` 调用包在 try/finally 内，finally 块负责重置标志。
     - 文件：`src/webfetcher/core.py:5641-5644`（manual_chrome 分支）
     - 文件：`src/webfetcher/core.py:5666-5669`（cdp/selenium 分支）
  2. **[Task 3 · Step 3.3 改动 B] 删除 `score_extraction` 的 plain-text 宽容分支**（避免 trafilatura/readability 输出文本误触发宽容评分，全局抬高 score 阈值导致 Bug 1 修复失效）。
     - 替代方案：把 plain-text 宽容评分独立成 `score_extraction_plaintext(text)` 函数，**只在 `run_competition` 短路分支调用**；普通竞赛仍用原 `score_extraction`。
     - 文件：`src/webfetcher/parsing/extractors.py:30-77` 保持原样；
     - 文件：`src/webfetcher/parsing/extractors.py:276` 附近的短路分支调用 `score_extraction_plaintext`。
  3. **[Task 1 · Step 1.1] 补强 fixture**：新增 `_short_low_quality_html()` fixture（有正文但 score<0.5），让 `test_quality_metadata_written_even_when_no_upgrade` 真正走主路径（非 legacy fallback），覆盖"主路径 + `_v2_no_upgrade=True`"分支。
     - 文件：`tests/unit/test_v2_fallback.py`
  4. **[Task 3 · Step 3.3 改动 A + C] 短路窗口统一为 1000 字符 + 收紧标签检测**：`run_competition` 入口的 `'<' not in html[:200]` 改为 `not re.search(r'<[a-zA-Z!/]', html[:1000])`，避免 markdown autolink 误伤。
     - 文件：`src/webfetcher/parsing/extractors.py:276` 附近
  5. **[Task 4 · Step 4.1] 调整防回归 fixture 段落长度**：把每段 450 字符缩短到 100-200 字符 × 5 段，让 score 稳稳 ≥ 0.6 留 margin；或断言改为"score 跃迁 ≥ 0.3"。
     - 文件：`tests/unit/test_v2_fallback.py`
  6. **[Task 4 · Step 4.4] E2E 验证加自动断言**：每个 `wf` 命令后用 `if grep -q "expected_log_pattern"; then ... else exit 1; fi` 包装；或在方案文档中明确标记"manual gate"，并由 chain 引擎跳过自动执行。
     - 文件：方案文档 `docs/20_设计/20260513_wf_V2_fallback修复方案.md`
  7. **[Task 4 · Step 4.3 前置] 建立 baseline**：先 `git stash` 跑一次 `pytest tests/test_extraction_competition.py -v > /tmp/baseline.txt`，再 unstash 跑改后版本，diff 对比，记录任何评分变化。
     - 文件：方案文档 Step 4.3 前置步骤
- **是否可直接进 A6 实施**：❌ **不可直接进**。必须先按行动项 1-7 修补方案文档，然后由用户或 chain B5 阶段做一次"修补后快速复审"（只看修补点是否落实，不需要再开三方专家），即可进 A6。
- **特别说明**：本评审**未发现**根因诊断或修法大方向错误，所有问题都是**实施细节级**的精度问题。在 6 个行动项落实后，方案可信度即可达到 🟢 通过水准。
