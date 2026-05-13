"""
V2 解析引擎 — 多策略竞赛 + 质量检测 + 域名记忆

作为 generic_to_markdown() 的平行替代路径，
通过 --engine v2 或 wf v2 命令触发。
V1 的 generic_to_markdown() 完全不受影响。
"""

import logging
import re

logger = logging.getLogger(__name__)


def _is_spa_shell(html: str) -> bool:
    """检测 SPA 空壳页面（需要 CDP 才能获取内容）"""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')

        # body 文本长度
        body = soup.find('body')
        if not body:
            return False
        body_text = body.get_text(strip=True)
        body_text_len = len(body_text)

        # script 数量占比
        scripts = soup.find_all('script')
        total_tags = len(soup.find_all())
        script_ratio = len(scripts) / max(total_tags, 1)

        # 常见 SPA 框架根节点标志
        spa_markers = soup.select('#app, #root, #__next, #__nuxt, [data-reactroot]')

        if script_ratio > 0.3 and body_text_len < 500 and spa_markers:
            logger.info(f"SPA shell detected: script_ratio={script_ratio:.2f}, "
                        f"body_text={body_text_len}, markers={len(spa_markers)}")
            return True
    except Exception as e:
        logger.debug(f"SPA detection error: {e}")

    return False


def _run_template_parser(html: str, url: str):
    """
    运行 TemplateParser（复用 V1 的站点特化模板）。

    如果匹配到非 generic 模板并产生内容，返回 (date_only, md, metadata)。
    否则返回 None。
    """
    import os
    from .engine.template_parser import TemplateParser
    from .templates import _build_generic_output

    template_dir = os.path.join(os.path.dirname(__file__), 'engine', 'templates')
    parser = TemplateParser(template_dir=template_dir)
    parser.reload_templates()

    try:
        result = parser.parse(html, url)
        if result.success:
            template_name = result.template_name or ''
            is_generic = 'generic' in template_name.lower()

            if not is_generic and (result.content or '').strip():
                return _build_generic_output(
                    title=result.title or '',
                    author=result.metadata.get('author', ''),
                    publish_time=result.metadata.get('date', ''),
                    content=result.content,
                    images=result.metadata.get('images', []),
                    url=url,
                    template_name=template_name,
                )
    except Exception as e:
        logger.debug(f"V2 TemplateParser: {e}")

    return None


def generic_v2(html: str, url: str, *,
               fetch_metrics=None, url_metadata=None, args=None
               ) -> tuple[str, str, dict]:
    """
    V2 通用解析器，返回值与 V1 的 generic_to_markdown() 完全兼容：
    (date_only, markdown_content, metadata)
    """
    from .extractors import run_competition, score_extraction
    from .templates import _build_generic_output
    from webfetcher.memory import DomainMemory, ExtractionLogger

    memory = DomainMemory()
    ext_logger = ExtractionLogger()

    # Step 0: 查询域名记忆
    hint = memory.lookup(url)
    hint_strategy = None
    if hint and hint.get('confidence') in ('high', 'medium'):
        hint_strategy = hint.get('best_extractor')
        logger.info(f"V2 domain memory hint: {hint_strategy} "
                     f"(confidence={hint['confidence']}, score={hint.get('score', 0):.3f})")

    # Step 1: TemplateParser（复用 V1 站点特化模板）
    tp_result = _run_template_parser(html, url)
    if tp_result:
        logger.info("V2: site-specific template matched, using template result")
        return tp_result

    # Step 2: 多策略竞赛
    results = run_competition(html, url, hint_strategy=hint_strategy)

    # 找到最佳结果
    best = results[0] if results and results[0].content else None

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

    # 质量描述字段（独立于 _v2_no_upgrade 标志位）
    # 任何返回路径都会通过 metadata.update(v2_state) 写入，让 core.py 升级循环
    # 能从重抓后的 metadata 读到真实的提取 score 和 quality 状态。
    # 与 _v2_needs_upgrade（升级请求信号）不同——后者仅在主动请求升级时设置。
    v2_state = {
        '_v2_quality_low': quality_low,
        '_v2_score': best.score if best and best.content else 0.0,
        '_v2_current_fetcher': current_fetcher,
    }

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
            metadata.update(v2_state)                       # 质量描述字段
            metadata['_v2_needs_upgrade'] = next_fetcher    # 升级请求字段

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

    # 如果所有策略都没内容且无法升级，回退到 V1 legacy
    if not best or not best.content.strip():
        logger.warning(f"V2: all extractors empty for {url}, falling back to V1 legacy")
        from webfetcher.parsing.legacy import generic_to_markdown as legacy_generic_parser
        date_only, md, metadata = legacy_generic_parser(html, url, 'safe', False)
        metadata.update(v2_state)
        return date_only, md, metadata

    # Step 4: 构建输出（复用 V1 的 _build_generic_output）
    # 从 TemplateParser 提取元数据补充
    tp_meta = _extract_tp_metadata(html, url)
    title = best.title or tp_meta.get('title', '') or '未命名'
    author = best.author or tp_meta.get('author', '')
    publish_time = best.date or tp_meta.get('date', '')

    date_only, md, metadata = _build_generic_output(
        title=title,
        author=author,
        publish_time=publish_time,
        content=best.content,
        images=tp_meta.get('images', []),
        url=url,
        template_name=f'v2/{best.strategy}',
    )

    # Step 5: 记录域名记忆 + 日志
    fetcher = 'urllib'
    if url_metadata:
        fetcher = url_metadata.get('fetch_mode', 'urllib')
    elif fetch_metrics and hasattr(fetch_metrics, 'fetch_mode'):
        fetcher = fetch_metrics.fetch_mode

    memory.update(
        url, fetcher=fetcher, extractor=best.strategy,
        score=best.score,
        all_scores={r.strategy: r.score for r in results if r.score > 0},
    )

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


def _extract_tp_metadata(html: str, url: str) -> dict:
    """从 TemplateParser 提取元数据（标题、作者、日期），不提取正文内容"""
    import os
    from .engine.template_parser import TemplateParser

    template_dir = os.path.join(os.path.dirname(__file__), 'engine', 'templates')
    parser = TemplateParser(template_dir=template_dir)
    parser.reload_templates()

    meta = {'title': '', 'author': '', 'date': '', 'images': []}
    try:
        result = parser.parse(html, url)
        if result.success:
            meta['title'] = result.title or ''
            meta['author'] = result.metadata.get('author', '')
            meta['date'] = result.metadata.get('date', '')
            meta['images'] = result.metadata.get('images', [])
    except Exception:
        pass
    return meta
