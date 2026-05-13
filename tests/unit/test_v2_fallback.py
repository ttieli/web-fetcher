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
