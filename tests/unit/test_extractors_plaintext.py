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
        md_content,
        'https://raw.githubusercontent.com/example/repo/main/CHANGELOG.md')

    assert len(results) >= 1
    winner = results[0]
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


def test_pre_wrapped_raw_markdown_unwraps_and_short_circuits():
    """raw.githubusercontent.com 服务端对部分 UA 会把 plain text 包一层
    <html><head>...</head><body><pre>raw_markdown</pre></body></html>。
    短路逻辑应解包后识别为 plain text 并跳过竞赛。"""
    wrapped = (
        '<html><head><meta name="color-scheme" content="light dark"></head>'
        '<body><pre style="word-wrap: break-word; white-space: pre-wrap;">'
        '# Changelog\n\n## 1.0\n\n- Initial release\n- Add feature X\n'
        '</pre></body></html>'
    )
    results = run_competition(
        wrapped,
        'https://raw.githubusercontent.com/example/repo/main/CHANGELOG.md')

    assert len(results) >= 1
    winner = results[0]
    assert winner.strategy == 'plaintext_passthrough', (
        f"expected plaintext_passthrough after unwrap, got {winner.strategy}")
    assert winner.score >= 0.8
    # 解包后的内容不应再含 <html> / <pre> 标签
    assert '<pre' not in winner.content
    assert '<html' not in winner.content
    assert '# Changelog' in winner.content


def test_pre_wrapped_with_html_entities_unescaped():
    """<pre> 内的 HTML 实体（&amp;, &lt;, &gt;）应正确反转。"""
    wrapped = (
        '<html><body><pre>'
        '# Test\n\nUse `if a &lt; b &amp;&amp; c &gt; 0` syntax.'
        '</pre></body></html>'
    )
    results = run_competition(
        wrapped,
        'https://raw.githubusercontent.com/example/repo/main/notes.md')
    winner = results[0]
    assert winner.strategy == 'plaintext_passthrough'
    assert 'if a < b && c > 0' in winner.content, (
        f"HTML entities should be unescaped; got: {winner.content!r}")


def test_score_extraction_main_function_unchanged():
    """主 score_extraction 行为不变（防止全局阈值漂移）。

    A5 评审关键点：trafilatura/readability 输出本就是纯文本，
    如果给主 score_extraction 加 plain-text 宽容路径，会让所有提取输出走宽容分支，
    全局抬高 score 阈值，导致 Bug 1 修复失效。本测试守护这一边界。
    """
    spa_extracted_text = "nav menu sidebar footer cookie subscribe sign in advertisement"
    score = score_extraction(spa_extracted_text)
    assert score < 0.5, (
        f"main score_extraction must keep SPA shell extracted text below 0.5; got {score}")
