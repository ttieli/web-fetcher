#!/usr/bin/env python3
"""
从历史日志（~/.config/webfetcher/extraction_log.jsonl + ~/.wf/fetch_history.jsonl
+ ~/.wf/fetch_failures.jsonl）抽取一个精简的回归 URL 套件。

按类别打标签，输出格式与 tests/url_suite.txt 兼容：
    <url> | <description> | <expected_strategy> | <tags>

类别策略（每类抽 3-8 个，目标总数 30-50）：
    - urllib-ok       urllib 即可拿到高分（score >= 0.6）
    - cdp-rescued     urllib 失败 → cdp 救回（最终 score >= 0.5）
    - spa-stuck       本次修复前 cdp 后被错判为"升级成功"实际仍低分（v2-fallback-fix）
    - raw-markdown    .md/.txt 资源或 raw github（应短路）
    - terminal-fail   历史多次尝试仍失败（quality 永远低）
    - template        命中站点 template（如微信、企查查、carnoc）

用法：
    python scripts/build_regression_suite.py > tests/url_suite.txt
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

CONFIG_LOG = Path.home() / '.config/webfetcher/extraction_log.jsonl'
WF_HISTORY = Path.home() / '.wf/fetch_history.jsonl'
WF_FAILURES = Path.home() / '.wf/fetch_failures.jsonl'


def load_jsonl(path: Path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def parse_ts(ts: str):
    if not ts:
        return datetime.min
    return datetime.fromisoformat(ts.split('.')[0])


def group_by_url(records: list, ts_key: str = 'ts'):
    """同 URL 按时间排序的多次记录分组。"""
    groups = defaultdict(list)
    for r in records:
        url = r.get('url')
        if not url:
            continue
        groups[url].append(r)
    for url in groups:
        groups[url].sort(key=lambda r: parse_ts(r.get(ts_key, '')))
    return groups


# 隐私过滤：跳过含搜索词 query 参数的 URL（可能含工作/个人查询关键词）
# 普通文章 URL 路径 OK，仅命中 search engine + query 模式
_PRIVACY_BLOCK_PATTERNS = (
    'baidu.com/s?',
    'google.com/search?',
    'bing.com/search?',
    'tianyancha.com/search?',
    'qcc.com/search?',
    'sogou.com/web?',
    'so.com/s?',
)

# 必含的回归测试 URL（即使历史日志没记录也强制入选）
# 用于守护已修复 bug 的回归
_PINNED_URLS = [
    {
        'url': 'https://mp.weixin.qq.com/s/teDI2pT7DODpZbpKaBETKQ',
        'description': 'mp.weixin.qq.com - WeChat 普通文章正文不能空（防 1.3.6 og:image 反推 gallery 回归）',
        'expected_strategy': 'urllib',
        'tags': {'cn', 'fast', 'template', 'wechat', 'regression-1.3.6'},
        'category': 'template',
        'domain': 'mp.weixin.qq.com',
    },
]


def _is_search_query_url(url: str) -> bool:
    """识别可能含工作/个人查询关键词的搜索引擎 query URL。"""
    url_low = url.lower()
    return any(p in url_low for p in _PRIVACY_BLOCK_PATTERNS)


def classify(extraction_groups: dict, history_groups: dict):
    """
    根据历史决定每个 URL 的类别 + 标签。

    返回：dict url -> dict(description, expected_strategy, tags, score_hint)
    """
    classified = {}

    for url, ext_records in extraction_groups.items():
        # 隐私过滤：搜索 query URL 跳过（避免泄露查询关键词）
        if _is_search_query_url(url):
            continue
        latest = ext_records[-1]
        domain = latest.get('domain', '')
        fetcher = latest.get('fetcher', 'urllib')
        score = latest.get('winner_score', 0)
        quality_low = latest.get('quality_low', False)

        # 同 URL 在 fetch_history 中的最近记录（看升级链路径）
        hist = history_groups.get(url, [])
        last_hist = hist[-1] if hist else {}
        fetchers_tried = last_hist.get('fetchers_tried', [])

        # 判定主类别
        tags = set()
        category = None
        description = f"{domain} - "

        # --- 1. raw markdown / plain text 资源 ---
        # 仅 raw 服务（raw.githubusercontent.com/gist）或后缀类原始资源
        # github.com/.../blob/.../*.md 是 GitHub UI HTML，不算 raw（不会短路）
        url_low = url.lower()
        path = url_low.split('?')[0].split('#')[0]
        is_github_blob_html = ('github.com' in url_low and '/blob/' in url_low)
        is_raw_service = ('raw.githubusercontent.com' in url_low or
                          'gist.githubusercontent.com' in url_low)
        has_text_suffix = path.endswith(('.md', '.txt', '.rst', '.markdown'))
        if is_raw_service or (has_text_suffix and not is_github_blob_html):
            category = 'raw-markdown'
            tags.update(['markdown', 'short-circuit', 'fast', 'v2-fallback-fix'])
            description += "raw markdown/text resource"
            expected = 'urllib'

        # --- 2. spa-stuck：cdp 后 score 仍 < 0.5 且最终 fetcher=cdp ---
        elif quality_low and fetcher in ('cdp', 'selenium') and 0 < score < 0.5:
            category = 'spa-stuck'
            tags.update(['spa', 'slow', 'v2-fallback-fix'])
            description += f"SPA stuck on {fetcher} (score={score:.2f})"
            expected = 'auto'

        # --- 3. cdp-rescued：urllib 失败 cdp 救回（多次尝试，最终 score >= 0.5） ---
        elif (len(ext_records) > 1 or len(fetchers_tried) > 1) and score >= 0.5 and fetcher in ('cdp', 'selenium'):
            category = 'cdp-rescued'
            tags.update(['fallback-rescue', 'slow'])
            description += f"urllib failed, {fetcher} rescued (score={score:.2f})"
            expected = 'auto'

        # --- 4. terminal-fail：多次尝试仍失败 ---
        elif quality_low and score == 0:
            category = 'terminal-fail'
            tags.update(['failure', 'slow'])
            description += "terminal failure (empty extraction)"
            expected = 'auto'

        # --- 5. template：命中站点 template ---
        elif any(p in domain for p in ('mp.weixin.qq.com', 'xiaohongshu.com',
                                        'qcc.com', 'tianyancha.com',
                                        'carnoc.com', 'douban.com')):
            category = 'template'
            tags.update(['template', 'fast'])
            description += "site-specific template path"
            expected = 'urllib' if 'weixin' in domain else 'auto'

        # --- 6. urllib-ok：urllib 直接拿高分 ---
        elif fetcher == 'urllib' and score >= 0.6 and not quality_low:
            category = 'urllib-ok'
            tags.update(['static', 'fast'])
            description += f"urllib OK (score={score:.2f})"
            expected = 'urllib'

        else:
            # 跳过模糊用例
            continue

        # 通用 hint：domestic vs international
        cn_hints = ('.cn', '.com.cn', 'weixin', 'baidu', 'sina', 'qcc',
                    'tianyancha', '12371', 'carnoc', 'xueqiu', 'xiaohongshu')
        if any(h in domain.lower() for h in cn_hints):
            tags.add('cn')
        else:
            tags.add('en')

        classified[url] = {
            'category': category,
            'description': description,
            'expected_strategy': expected,
            'tags': tags,
            'score_hint': score,
            'domain': domain,
        }

    return classified


def select_per_category(classified: dict, per_cat_target: dict) -> list:
    """每类按目标数采样，优先选不同 domain 增加覆盖度。"""
    by_cat = defaultdict(list)
    for url, info in classified.items():
        by_cat[info['category']].append((url, info))

    selected = []
    for cat, urls in by_cat.items():
        target = per_cat_target.get(cat, 5)
        # 同 domain 至多取 2 个，分散覆盖
        seen_domain_count = defaultdict(int)
        picked = []
        for url, info in urls:
            if seen_domain_count[info['domain']] >= 2:
                continue
            picked.append((url, info))
            seen_domain_count[info['domain']] += 1
            if len(picked) >= target:
                break
        selected.extend(picked)

    return selected


def write_suite(selected: list, out=sys.stdout):
    """按类别分组输出 url_suite.txt 格式。"""
    print("# Regression Test URL Suite (auto-generated from history)", file=out)
    print("# ============================================================", file=out)
    print("#", file=out)
    print(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", file=out)
    print("# Source: ~/.config/webfetcher/extraction_log.jsonl + ~/.wf/fetch_history.jsonl", file=out)
    print("#", file=out)
    print("# Format: <url> | <description> | <expected_strategy> | <tags>", file=out)
    print("#", file=out)
    print("# Categories tagged for filtering:", file=out)
    print("#   v2-fallback-fix  - URLs touching V2 fallback fix (spa-stuck/raw-md)", file=out)
    print("#   short-circuit    - plain-text URLs that should bypass competition", file=out)
    print("#   fallback-rescue  - urllib fails, cdp/selenium rescues", file=out)
    print("#   spa              - SPA sites (slow)", file=out)
    print("#   template         - site-specific template path", file=out)
    print("#   static           - basic static sites", file=out)
    print("#   fast / slow      - speed hints for CI filtering", file=out)
    print("#", file=out)
    print("# ============================================================", file=out)
    print("", file=out)

    # 按类别分组
    by_cat = defaultdict(list)
    for url, info in selected:
        by_cat[info['category']].append((url, info))

    cat_order = ['urllib-ok', 'template', 'cdp-rescued',
                 'spa-stuck', 'raw-markdown', 'terminal-fail']
    cat_titles = {
        'urllib-ok': 'urllib 直接拿到高分（静态页/快路径）',
        'template': '站点特化 template 路径',
        'cdp-rescued': 'urllib 失败 → cdp/selenium 救回',
        'spa-stuck': '本次 V2 修复关注：SPA 站升级链验证',
        'raw-markdown': '本次 V2 修复关注：plain text 短路',
        'terminal-fail': '历史持续失败 URL（标识真实失败 vs 修复后救回）',
    }

    for cat in cat_order:
        urls = by_cat.get(cat, [])
        if not urls:
            continue
        print(f"# {cat_titles[cat]}", file=out)
        print(f"# {'-' * 60}", file=out)
        for url, info in urls:
            tags_str = ','.join(sorted(info['tags']))
            print(f"{url} | {info['description']} | {info['expected_strategy']} | {tags_str}", file=out)
        print("", file=out)


def main():
    print("Loading history logs...", file=sys.stderr)
    extraction = load_jsonl(CONFIG_LOG)
    history = load_jsonl(WF_HISTORY)
    print(f"  ~/.config/webfetcher/extraction_log.jsonl: {len(extraction)} records",
          file=sys.stderr)
    print(f"  ~/.wf/fetch_history.jsonl:                 {len(history)} records",
          file=sys.stderr)

    ext_groups = group_by_url(extraction)
    hist_groups = group_by_url(history)
    print(f"  unique URLs in extraction log: {len(ext_groups)}", file=sys.stderr)

    classified = classify(ext_groups, hist_groups)
    by_cat = defaultdict(int)
    for info in classified.values():
        by_cat[info['category']] += 1
    print("Classification:", file=sys.stderr)
    for cat, n in sorted(by_cat.items()):
        print(f"  {cat:20s}: {n}", file=sys.stderr)

    # 每类目标数量（总计目标 30-50）
    per_cat_target = {
        'urllib-ok': 8,
        'template': 6,
        'cdp-rescued': 8,
        'spa-stuck': 8,
        'raw-markdown': 4,
        'terminal-fail': 6,
    }

    selected = select_per_category(classified, per_cat_target)

    # 合并必含 URL（去重：以 URL 为 key）
    selected_urls = {url for url, _ in selected}
    pinned_added = 0
    for pinned in _PINNED_URLS:
        if pinned['url'] not in selected_urls:
            selected.append((pinned['url'], pinned))
            pinned_added += 1
    print(f"\nSelected {len(selected)} URLs for regression suite "
          f"({pinned_added} pinned regression URLs added)", file=sys.stderr)

    write_suite(selected)


if __name__ == '__main__':
    main()
