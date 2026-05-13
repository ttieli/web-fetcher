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
        html, 'https://no-template-match-xyz789.test/spa',
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

    date_only, md, metadata = generic_v2(html, 'https://no-template-match-xyz789.test/article', args=args)

    # 高质量路径应该 quality_low=False 且 score 较高
    assert metadata.get('_v2_quality_low') is False, (
        f"high quality content should have _v2_quality_low=False, got {metadata.get('_v2_quality_low')}, "
        f"score={metadata.get('_v2_score')}")
    assert metadata.get('_v2_score', 0) >= 0.5


def test_upgrade_should_break_only_when_score_improved_above_threshold():
    """Bug 1: HTML 变长但 score 仍低（SPA shell 场景），fallback 链
    应继续升下一级，而不是因为 HTML 长就 break。

    本测试通过端到端调 generic_v2 验证（不 mock core.py 的 fetch_html）：
    重抓的 metadata 是否带回真实 score，供 core.py 升级循环判断"换 fetcher" + "链终止"。
    """
    # urllib 抓回的：典型 SPA 短 shell
    short_shell = """<html><body><div id="root"></div>
<div>nav menu sidebar</div></body></html>"""

    # cdp 抓回的：长但仍是 SPA 骨架——大量 script + 噪音词 + 短内容片段
    long_shell = """<html><body><div id="root"></div>
<nav>nav menu sidebar footer cookie subscribe sign in advertisement</nav>
<div>登录 关注我们 推荐阅读 相关文章 更多 menu nav sidebar footer cookie</div>
<aside>more from related posts subscribe footer sidebar advertisement</aside>
<p>Short.</p>
<script>%s</script>
</body></html>""" % ('window.__data__={};' * 300)

    args = SimpleNamespace(_v2_no_upgrade=True, engine='v2')

    _, _, m1 = generic_v2(short_shell, 'https://no-template-match-xyz789.test/spa',
                          url_metadata={'fetch_mode': 'urllib'}, args=args)
    _, _, m2 = generic_v2(long_shell, 'https://no-template-match-xyz789.test/spa',
                          url_metadata={'fetch_mode': 'cdp'}, args=args)

    # 两次都应有 _v2_score
    assert '_v2_score' in m1 and '_v2_score' in m2

    # CDP HTML 比 urllib 长很多，但内容质量没变 → score 应仍然 < 0.5
    assert m2['_v2_score'] < 0.5, (
        f"CDP long-shell score should still be low; got {m2['_v2_score']}")
    assert m2['_v2_quality_low'] is True


def test_normal_article_html_still_works_after_fixes():
    """防回归：现有'urllib→cdp 成功救回'路径不能受影响。
    用一段普通文章 HTML 模拟：urllib 拿到的是 SPA shell，CDP 拿到的是真正
    渲染后的文章，CDP 后 score 应大幅提升触发 break。"""
    # urllib 抓的：SPA 空骨架
    urllib_html = """<html><body><div id="root"></div>
<script>window.__data__=null</script></body></html>"""

    # cdp 抓的：真正渲染后的文章（5 段，每段 100-200 字符）
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

    _, _, m_urllib = generic_v2(urllib_html, 'https://no-template-match-xyz789.test/article',
                                 url_metadata={'fetch_mode': 'urllib'}, args=args)
    _, _, m_cdp = generic_v2(cdp_html, 'https://no-template-match-xyz789.test/article',
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
