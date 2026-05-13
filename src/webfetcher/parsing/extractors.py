"""
V2 多策略提取器 + 评分器 + 竞赛调度

从 tests/test_extraction_competition.py 验证过的逻辑迁移而来，
作为 V2 引擎 (engine_v2.py) 的核心组件。
"""

import json
import re
import time
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


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


# raw.githubusercontent.com 等服务端对部分 UA 会把 plain text 包一层 <html><body><pre>...</pre></body></html>
# 用此正则提取 <pre>...</pre> 内的真实内容。
_PRE_WRAPPED_RE = re.compile(
    r'^\s*<html[^>]*>.*?<body[^>]*>\s*<pre[^>]*>(?P<inner>.*?)</pre>\s*</body>\s*</html>\s*$',
    re.DOTALL | re.IGNORECASE,
)


def _unwrap_pre_html(text: str) -> str | None:
    """如果 text 是 <html><body><pre>...</pre></body></html> 形式，返回 pre 内文本；否则返回 None。"""
    if not text:
        return None
    m = _PRE_WRAPPED_RE.match(text)
    if not m:
        return None
    import html as _html_mod
    inner = m.group('inner')
    # HTML 实体反转（&amp; → &, &lt; → < 等）
    return _html_mod.unescape(inner)


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

    # 1. 长度分（30%）
    length_score = min(len(text.strip()) / 500, 1.0)
    score += length_score * 0.30

    # 2. 结构分（25%）
    structures = 0
    structures += text.count('\n## ') + text.count('\n### ')
    structures += text.count('\n- ') + text.count('\n* ')
    structures += text.count('```')
    structures += text.count('|')
    struct_score = min(structures / 10, 1.0)
    score += struct_score * 0.25

    # 3. 噪音分（25%，divisor=10 而非 5）
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


@dataclass
class ExtractionResult:
    """单个策略的提取结果"""
    strategy: str
    content: str = ''
    title: str = ''
    author: str = ''
    date: str = ''
    score: float = 0.0
    error: str = ''
    duration_ms: float = 0.0


def score_extraction(text: str) -> float:
    """
    对提取结果打分。

    评分因子：
    1. 内容长度（30%）— 归一化到 0-1，500 字符满分
    2. 结构丰富度（25%）— 标题/列表/表格/代码块
    3. 噪音比率（25%）— 导航词、广告词占比（越低越好）
    4. 段落质量（20%）— 平均段落长度
    """
    if not text or not text.strip():
        return 0.0

    score = 0.0

    # 1. 长度分
    length_score = min(len(text.strip()) / 500, 1.0)
    score += length_score * 0.30

    # 2. 结构分
    structures = 0
    structures += text.count('\n## ') + text.count('\n### ')
    structures += text.count('\n- ') + text.count('\n* ')
    structures += text.count('```')
    structures += text.count('|')
    struct_score = min(structures / 10, 1.0)
    score += struct_score * 0.25

    # 3. 噪音分（反向）
    noise_words = ['导航', 'nav', 'menu', 'sidebar', 'footer', 'cookie',
                   '登录', 'sign in', 'subscribe', '关注我们', 'advertisement',
                   'more from', '推荐阅读', '相关文章', 'related posts']
    text_lower = text.lower()
    noise_count = sum(text_lower.count(w.lower()) for w in noise_words)
    noise_score = max(1.0 - noise_count / 5, 0.0)
    score += noise_score * 0.25

    # 4. 段落质量分
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    if paragraphs:
        avg_len = sum(len(p) for p in paragraphs) / len(paragraphs)
        if 50 <= avg_len <= 300:
            para_score = 1.0
        else:
            para_score = max(0, 1 - abs(avg_len - 175) / 300)
        score += para_score * 0.20

    return round(score, 3)


# ============================================================
# 提取策略
# ============================================================

def extract_trafilatura(html: str, url: str) -> ExtractionResult:
    """策略 A: trafilatura（wf V1 主力引擎）"""
    t0 = time.time()
    try:
        from trafilatura import bare_extraction
        extracted = bare_extraction(
            html, url=url,
            include_tables=True, include_links=True,
            include_images=True, include_formatting=True,
            favor_precision=False, as_dict=True,
        )
        content = ''
        title = ''
        author = ''
        date = ''
        if extracted:
            content = extracted.get('text') or ''
            title = extracted.get('title') or ''
            author = extracted.get('author') or ''
            date = extracted.get('date') or ''
        return ExtractionResult(
            strategy='trafilatura',
            content=content, title=title, author=author, date=date,
            duration_ms=(time.time() - t0) * 1000,
        )
    except Exception as e:
        return ExtractionResult(strategy='trafilatura', error=str(e),
                                duration_ms=(time.time() - t0) * 1000)


def extract_readability(html: str, url: str) -> ExtractionResult:
    """策略 B: readability-lxml（Mozilla Readability Python 实现）"""
    t0 = time.time()
    try:
        from readability import Document
        import html2text

        doc = Document(html, url=url)
        content_html = doc.summary()
        title = doc.short_title()

        h = html2text.HTML2Text()
        h.body_width = 0
        h.ignore_links = False
        h.ignore_images = False
        content = h.handle(content_html).strip()

        # 内容太少时尝试宽松模式
        if len(content) < 120:
            doc2 = Document(html, url=url,
                            positive_keywords=["article", "content", "post", "entry", "text"])
            content_html2 = doc2.summary()
            content2 = h.handle(content_html2).strip()
            if len(content2) > len(content):
                content = content2

        return ExtractionResult(
            strategy='readability',
            content=content, title=title,
            duration_ms=(time.time() - t0) * 1000,
        )
    except ImportError:
        return ExtractionResult(strategy='readability',
                                error='readability-lxml not installed',
                                duration_ms=(time.time() - t0) * 1000)
    except Exception as e:
        return ExtractionResult(strategy='readability', error=str(e),
                                duration_ms=(time.time() - t0) * 1000)


def extract_next_data(html: str, url: str) -> ExtractionResult:
    """策略 C: Next.js __NEXT_DATA__ 提取"""
    t0 = time.time()
    try:
        match = re.search(
            r'<script\s+id="__NEXT_DATA__"\s+type="application/json">(.*?)</script>',
            html, re.DOTALL
        )
        if not match:
            return ExtractionResult(strategy='next_data', content='',
                                    duration_ms=(time.time() - t0) * 1000)

        data = json.loads(match.group(1))
        props = data.get('props', {}).get('pageProps', {})

        # 尝试常见字段名
        content = ''
        for key in ['content', 'body', 'article', 'post', 'markdown', 'html', 'text']:
            val = props.get(key)
            if isinstance(val, str) and len(val) > 100:
                content = val
                break

        # 深层搜索
        if not content:
            content = _deep_find_content(props)

        title = ''
        for key in ['title', 'name', 'headline']:
            val = props.get(key)
            if isinstance(val, str) and val:
                title = val
                break

        # HTML 内容转 markdown
        if content and '<' in content and '>' in content:
            try:
                import html2text
                h = html2text.HTML2Text()
                h.body_width = 0
                content = h.handle(content)
            except ImportError:
                pass

        author_raw = props.get('author', '')
        author = ''
        if isinstance(author_raw, dict):
            author = author_raw.get('name', '')
        elif isinstance(author_raw, str):
            author = author_raw

        date = props.get('date', '') or props.get('publishedAt', '') or props.get('createdAt', '')

        return ExtractionResult(
            strategy='next_data',
            content=content.strip() if content else '',
            title=title, author=author, date=str(date),
            duration_ms=(time.time() - t0) * 1000,
        )
    except Exception as e:
        return ExtractionResult(strategy='next_data', error=str(e),
                                duration_ms=(time.time() - t0) * 1000)


def _deep_find_content(obj, depth=0, max_depth=5):
    """递归搜索 JSON 中最长的文本字段"""
    if depth > max_depth:
        return ''
    if isinstance(obj, str):
        return obj if len(obj) > 200 else ''
    if isinstance(obj, dict):
        best = ''
        for k, v in obj.items():
            if k in ('content', 'body', 'text', 'article', 'markdown', 'html', 'description'):
                candidate = _deep_find_content(v, depth + 1)
                if len(candidate) > len(best):
                    best = candidate
        return best
    if isinstance(obj, list):
        for item in obj[:10]:
            candidate = _deep_find_content(item, depth + 1)
            if len(candidate) > 200:
                return candidate
    return ''


def extract_json_ld(html: str, url: str) -> ExtractionResult:
    """策略 D: JSON-LD 结构化数据提取（复用 legacy.py 已有代码）"""
    t0 = time.time()
    try:
        from webfetcher.parsing.legacy import extract_json_ld_content

        data = extract_json_ld_content(html)
        if not data:
            return ExtractionResult(strategy='json_ld', content='',
                                    duration_ms=(time.time() - t0) * 1000)

        content = data.get('articleBody', '') or data.get('description', '')
        title = data.get('headline', '') or data.get('name', '')
        author = ''
        author_raw = data.get('author', '')
        if isinstance(author_raw, dict):
            author = author_raw.get('name', '')
        elif isinstance(author_raw, str):
            author = author_raw
        date = data.get('datePublished', '')

        return ExtractionResult(
            strategy='json_ld',
            content=content.strip() if content else '',
            title=title, author=author, date=date,
            duration_ms=(time.time() - t0) * 1000,
        )
    except Exception as e:
        return ExtractionResult(strategy='json_ld', error=str(e),
                                duration_ms=(time.time() - t0) * 1000)


# ============================================================
# 竞赛调度器
# ============================================================

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
    # L1 短路：URL 看起来就是纯文本资源
    # - 如果 HTML 确实是纯文本（无标签起始字符），直接短路
    # - 如果 HTML 是 <html><body><pre>raw_text</pre></body></html> 形式
    #   （raw.githubusercontent.com 服务端包壳），解包后短路
    if _is_plain_text_url(url) and html:
        content = None
        if _looks_like_plain_text(html):
            content = html.strip()
        else:
            unwrapped = _unwrap_pre_html(html)
            if unwrapped is not None and _looks_like_plain_text(unwrapped):
                content = unwrapped.strip()
                logger.info(f"V2 plain-text URL: unwrapped <pre>-wrapped HTML "
                             f"({len(html)} → {len(content)} chars)")

        if content is not None:
            score = score_extraction_plaintext(content)
            # 短路结果至少给 0.9 score（避免 plain text 段落质量因子误伤）
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
