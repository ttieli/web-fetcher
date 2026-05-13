#!/usr/bin/env python3
"""
wf - WebFetcher的便捷命令行工具
让网页内容获取更简单高效

输出路径优先级（从高到低）：
1. 命令行参数指定（位置参数或-o）
2. 环境变量 WF_OUTPUT_DIR
3. 默认值 ./output/
"""
import sys
import os
from pathlib import Path
import logging
import re
import warnings

# Suppress SyntaxWarning from parser_engine docstrings
warnings.filterwarnings('ignore', category=SyntaxWarning)

# Pre-compiled URL patterns for extract_url_from_text()
_CLEAN_URL_RE = re.compile(r'^https?://[^\s]+$')
_URL_EXTRACT_PATTERNS = [
    re.compile(r'(https?://mp\.weixin\.qq\.com/s/[^\s\u4e00-\u9fff]+)', re.IGNORECASE),
    re.compile(r'(mp\.weixin\.qq\.com/s/[^\s\u4e00-\u9fff]+)', re.IGNORECASE),
    re.compile(r'(?:^|\s)((?:xhslink|t|dwz|url|c|6|bit|tinyurl)\.(?:com|cn|co|ly|me)/[^\s\u4e00-\u9fff]+)', re.IGNORECASE),
    re.compile(r'https?://[^\s"\']+', re.IGNORECASE),
]
_TRAILING_PUNCT_RE = re.compile(r'[,!?。，！？、）)】」』》\uff09]+$')

# Import ChromeDriver version management
try:
    from webfetcher.drivers import check_chrome_driver_compatibility
except ImportError:
    check_chrome_driver_compatibility = None

# 获取项目根目录（从包安装位置向上查找）
def get_project_root():
    """获取项目根目录（包含config/目录的位置）"""
    # 尝试从当前工作目录查找
    cwd = Path.cwd()
    if (cwd / 'config').exists():
        return cwd

    # 尝试从包安装位置向上查找
    pkg_path = Path(__file__).resolve().parent.parent.parent
    if (pkg_path / 'config').exists():
        return pkg_path

    # 默认返回当前目录
    return cwd

PROJECT_ROOT = get_project_root()

# 默认输出目录
DEFAULT_OUTPUT_DIR = "./output"

# Configure logging for user feedback
# A1: 默认 INFO（保留路由决策/V2 升级/短路等业务日志）；
#     启动横幅（CDP fetcher available 等 4 处）单独降为 DEBUG，配合 --debug 才显示
#     --debug / WF_DEBUG=1 → DEBUG 级（含启动横幅 + traceback）
_debug_env = bool(int(os.environ.get('WF_DEBUG', '0') or '0'))
_verbose_env = bool(int(os.environ.get('WF_VERBOSE', '0') or '0'))
_debug_flag = ('--debug' in sys.argv) or _debug_env
_verbose_flag = ('-v' in sys.argv or '--verbose' in sys.argv) or _verbose_env
_default_level = logging.DEBUG if _debug_flag else logging.INFO

logging.basicConfig(
    level=_default_level,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('wf')

# Expose flags for downstream modules / top-level error handler
DEBUG_MODE = _debug_flag
VERBOSE_MODE = _verbose_flag

def parse_output_dir(args):
    """
    解析输出目录参数
    优先级：
    1. 命令行-o/--outdir参数（最明确）
    2. -- 分隔符后的第一个参数（明确分界）
    3. 位置参数（第一个看起来像路径的参数）
    4. 环境变量WF_OUTPUT_DIR
    5. 默认值./output/

    返回: (output_dir, remaining_args)
    """
    output_dir = None
    remaining_args = args[:]

    # 方案1：检查-o/--outdir参数（最高优先级）
    for i, arg in enumerate(args):
        if arg in ['-o', '--outdir']:
            if i + 1 < len(args):
                output_dir = args[i + 1]
                # 移除-o和其值
                remaining_args = args[:i] + args[i+2:]
                # 如果使用了-o，还需要清理可能存在的其他输出目录指示
                # 移除 -- 分隔符及其后的第一个参数（如果存在）
                if '--' in remaining_args:
                    sep_index = remaining_args.index('--')
                    if sep_index + 1 < len(remaining_args):
                        # 检查--后面是否为路径
                        next_arg = remaining_args[sep_index + 1]
                        if (next_arg.startswith('/') or next_arg.startswith('~/') or
                            next_arg.startswith('./') or next_arg.startswith('../') or
                            next_arg in ['.', '..', '~']):
                            remaining_args = remaining_args[:sep_index] + remaining_args[sep_index+2:]
                        else:
                            # 如果不是路径，只移除--
                            remaining_args = remaining_args[:sep_index] + remaining_args[sep_index+1:]
                # 移除位置参数中的路径
                for j, r_arg in enumerate(remaining_args[:]):
                    if (r_arg.startswith('~/') or r_arg in ['~', '.', '..'] or
                        r_arg.startswith('./') or r_arg.startswith('../')):
                        remaining_args.remove(r_arg)
                        break
                break

    # 方案2：检查 -- 分隔符（如果没有使用-o）
    if not output_dir and '--' in remaining_args:
        sep_index = remaining_args.index('--')
        if sep_index + 1 < len(remaining_args):
            # -- 后的第一个参数作为输出目录
            output_dir = remaining_args[sep_index + 1]
            # 移除 -- 和输出目录
            remaining_args = remaining_args[:sep_index] + remaining_args[sep_index+2:]

    # 方案3：智能检测位置参数（保持向后兼容）
    if not output_dir and len(remaining_args) >= 1:
        # 查找第一个看起来像路径的参数
        for i, arg in enumerate(remaining_args):
            # 跳过明显的URL
            if arg.startswith('http://') or arg.startswith('https://'):
                continue

            # 跳过看起来像域名的参数（包含点但不以路径分隔符开头）
            # 但要排除 ./ 和 ../ 这样的相对路径
            if ('.' in arg and not arg.startswith('/') and not arg.startswith('~')
                and arg not in ['./', '../', '.', '..']):
                # 但如果包含路径分隔符且不是第一个字符，可能是URL路径
                if '/' in arg and not arg.startswith('./') and not arg.startswith('../'):
                    continue

            # 检测路径特征
            is_path = False

            # 明确的路径标志
            if (arg.startswith('/') or      # 绝对路径
                arg.startswith('~/') or     # home目录
                arg.startswith('./') or     # 当前目录
                arg.startswith('../') or    # 父目录
                arg in ['.', '..', '~'] or  # 特殊目录
                arg in ['./', '../'] or      # 带斜杠的特殊目录
                arg.endswith('/')):          # 以/结尾的目录
                is_path = True

            # 已存在的目录
            elif os.path.isdir(os.path.expanduser(arg)):
                is_path = True

            # 看起来像输出路径（包含常见目录名）
            elif any(name in arg.lower() for name in ['output', 'download', 'desktop', 'documents']):
                is_path = True

            if is_path:
                output_dir = arg
                remaining_args = remaining_args[:i] + remaining_args[i+1:]
                break

    # 如果还没有，检查环境变量
    if not output_dir:
        output_dir = os.environ.get('WF_OUTPUT_DIR')

    # 最后使用默认值
    if not output_dir:
        output_dir = DEFAULT_OUTPUT_DIR

    # 展开路径
    output_dir = os.path.expanduser(output_dir)
    output_dir = os.path.abspath(output_dir)

    return output_dir, remaining_args

def ensure_output_dir(output_dir):
    """确保输出目录存在"""
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"警告: 无法创建输出目录 {output_dir}: {e}")
        return False

def clean_wechat_url(url: str) -> str:
    """
    Clean WeChat URL by removing problematic parameters like poc_token.
    poc_token causes WeChat to return error pages instead of content.

    Args:
        url: WeChat URL that may contain poc_token

    Returns:
        str: Cleaned URL without poc_token
    """
    if 'mp.weixin.qq.com' in url and 'poc_token=' in url:
        # Remove poc_token parameter
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)

        # Remove poc_token from parameters
        if 'poc_token' in params:
            del params['poc_token']

        # Rebuild query string
        new_query = urllib.parse.urlencode(params, doseq=True)

        # Rebuild URL
        cleaned_url = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))

        logger.info(f"✓ 已移除poc_token参数（该参数会导致微信返回错误页面）")
        return cleaned_url

    return url

def extract_url_from_text(text: str) -> tuple:
    """
    Extract URL from mixed text content (e.g., social media copy-paste).

    Args:
        text: Input text that may contain URLs

    Returns:
        tuple: (url_or_original_text, was_extracted)
            - url_or_original_text: Extracted URL if found, otherwise original text
            - was_extracted: True if URL was extracted from mixed text

    Examples:
        >>> extract_url_from_text("Check http://example.com for details")
        ('http://example.com', True)
        >>> extract_url_from_text("http://example.com")
        ('http://example.com', False)
    """
    # If input is already a clean URL, return as-is
    if _CLEAN_URL_RE.match(text.strip()):
        return text.strip(), False

    for pattern in _URL_EXTRACT_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            # Extract first URL found
            url = matches[0] if isinstance(matches[0], str) else matches[0][0]
            # Remove trailing Chinese/English punctuation
            url = _TRAILING_PUNCT_RE.sub('', url)
            # Add protocol if missing
            if not url.startswith('http'):
                url = 'https://' + url
            return url, True

    # No URL found
    return text, False

def diagnose_system():
    """Diagnose system configuration and ChromeDriver compatibility"""
    print("=" * 70)
    print("WebFetcher System Diagnostic / WebFetcher系统诊断")
    print("=" * 70 + "\n")

    exit_code = 0

    # 1. Python version check
    print("1. Python Version Check / Python版本检查")
    print("-" * 70)
    python_version = sys.version.split()[0]
    print(f"   Python Version / Python版本: {python_version}")
    if sys.version_info >= (3, 7):
        print(f"   ✓ Python version is compatible / Python版本兼容\n")
    else:
        print(f"   ⚠️  Python 3.7+ is recommended / 建议使用Python 3.7+\n")
        exit_code = 1

    # 2. Working directory check
    print("2. Working Directory / 工作目录")
    print("-" * 70)
    print(f"   Current directory / 当前目录: {os.getcwd()}")
    print(f"   Project root / 项目根目录: {PROJECT_ROOT}")
    config_path = PROJECT_ROOT / "config"
    if config_path.exists():
        print(f"   ✓ Config directory found / 找到配置目录\n")
    else:
        print(f"   ❌ Config directory not found / 未找到配置目录\n")
        exit_code = 2

    # 3. ChromeDriver version check
    print("3. ChromeDriver Version Check / ChromeDriver版本检查")
    print("-" * 70)

    if check_chrome_driver_compatibility is None:
        print("   ⚠️  ChromeDriver management module not available")
        print("   ⚠️  ChromeDriver管理模块不可用\n")
    else:
        try:
            result = check_chrome_driver_compatibility()
            print(f"   Chrome: {result.chrome_version or 'NOT FOUND / 未找到'}")
            print(f"   ChromeDriver: {result.driver_version or 'NOT FOUND / 未找到'}")
            print(f"   Status / 状态: {result.status.value}")
            print(f"   {result.message_en}")
            print(f"   {result.message_cn}")

            if not result.is_compatible:
                print(f"\n   ⚠️  WARNING: Version mismatch detected!")
                print(f"   ⚠️  警告：检测到版本不匹配！")
                print(f"   Fix / 修复: Run 'python scripts/manage_chromedriver.py sync'")
                print(f"   修复: 运行 'python scripts/manage_chromedriver.py sync'\n")
                exit_code = 3  # Specific exit code for version mismatch
            else:
                print(f"   ✓ ChromeDriver is compatible / ChromeDriver兼容\n")
        except Exception as e:
            print(f"   ❌ Error checking ChromeDriver / 检查ChromeDriver时出错: {e}\n")
            exit_code = 2

    # 4. Output directory check
    print("4. Output Directory / 输出目录")
    print("-" * 70)
    default_output = os.environ.get('WF_OUTPUT_DIR', DEFAULT_OUTPUT_DIR)
    print(f"   Default output / 默认输出: {default_output}")
    if os.path.exists(default_output):
        print(f"   ✓ Output directory exists / 输出目录存在\n")
    else:
        print(f"   ℹ️  Output directory will be created on first use")
        print(f"   ℹ️  首次使用时将创建输出目录\n")

    # Summary
    print("=" * 70)
    print("Diagnostic Summary / 诊断摘要")
    print("=" * 70)
    if exit_code == 0:
        print("✓ System is healthy / 系统正常")
        print("  Ready to fetch web content / 准备抓取网页内容")
    elif exit_code == 1:
        print("⚠️  System has warnings / 系统有警告")
        print("   System may work but not optimally / 系统可能工作但不是最佳状态")
    elif exit_code == 3:
        print("⚠️  ChromeDriver version mismatch / ChromeDriver版本不匹配")
        print("   Run: python scripts/manage_chromedriver.py sync")
        print("   运行: python scripts/manage_chromedriver.py sync")
    else:
        print("❌ System has errors / 系统有错误")
        print("   Please fix the issues above / 请修复上述问题")

    sys.exit(exit_code)

def _prepare_url(mode_name, url_input):
    """Extract URL from text, add protocol, clean WeChat tokens.

    Args:
        mode_name: Mode label for logging (e.g. 'Fast', 'Raw')
        url_input: Raw URL input string

    Returns:
        Cleaned URL string ready for fetching
    """
    url, was_extracted = extract_url_from_text(url_input)
    if was_extracted:
        logger.info(f"✓ {mode_name}：已从文本中提取URL: {url}")
    if not url.startswith('http'):
        url = f'https://{url}'
    return clean_wechat_url(url)


def _prepare_and_run(webfetcher_module, url, raw_args_rest, stdout_mode, extra_args=None):
    """Parse output dir, ensure it exists, and run webfetcher.

    Args:
        webfetcher_module: The core module
        url: Prepared URL
        raw_args_rest: Remaining args after URL (for output dir parsing)
        stdout_mode: Whether --stdout is enabled
        extra_args: Additional args to insert (e.g. ['--render', 'never'])
    """
    output_dir, remaining_args = parse_output_dir(raw_args_rest)
    if not stdout_mode:
        ensure_output_dir(output_dir)
    stdout_args = ['--stdout'] if stdout_mode else []
    cmd_args = [url, '-o', output_dir] + (extra_args or []) + remaining_args + stdout_args
    run_webfetcher(webfetcher_module, cmd_args)


def _run_stats(args):
    """Show fetch statistics from history and failure logs.

    Usage:
        wf stats                  # Show stats for last 30 days
        wf stats --since 7d       # Only last 7 days
        wf stats --all            # All time
    """
    import json
    from datetime import datetime, timedelta
    from collections import defaultdict
    from urllib.parse import urlparse

    history_path = Path.home() / '.wf' / 'fetch_history.jsonl'
    failure_path = Path.home() / '.wf' / 'fetch_failures.jsonl'

    # Parse --since argument (default: 30 days)
    since = datetime.now() - timedelta(days=30)
    show_all = '--all' in args
    if show_all:
        since = None
    else:
        for i, arg in enumerate(args):
            if arg == '--since' and i + 1 < len(args):
                val = args[i + 1]
                days = int(val.rstrip('d')) if val.endswith('d') else int(val)
                since = datetime.now() - timedelta(days=days)

    def _read_log(path):
        entries = []
        if not path.exists():
            return entries
        for line in path.read_text(encoding='utf-8').strip().split('\n'):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if since:
                    ts = datetime.fromisoformat(entry.get('ts', ''))
                    if ts < since:
                        continue
                entries.append(entry)
            except (json.JSONDecodeError, ValueError):
                continue
        return entries

    successes = _read_log(history_path)
    failures = _read_log(failure_path)
    total = len(successes) + len(failures)

    if total == 0:
        print("No fetch records found. Run wf to fetch some pages first.")
        return

    period = "all time" if show_all else f"last {(datetime.now() - since).days}d" if since else "all time"
    success_rate = len(successes) / total * 100 if total > 0 else 0

    print(f"\n📊 wf 采集统计 ({period})")
    print("=" * 60)
    print(f"总采集: {total} 次 | 成功: {len(successes)} ({success_rate:.0f}%) | 失败: {len(failures)} ({100-success_rate:.0f}%)")
    print()

    # Fetcher usage from successes
    if successes:
        method_counts = defaultdict(int)
        method_durations = defaultdict(list)
        for s in successes:
            m = s.get('primary_method', 'unknown')
            method_counts[m] += 1
            method_durations[m].append(s.get('duration_seconds', 0))

        print("Fetcher 使用:")
        max_count = max(method_counts.values()) if method_counts else 1
        for method, count in sorted(method_counts.items(), key=lambda x: -x[1]):
            bar_len = int(count / max_count * 20)
            bar = '█' * bar_len
            pct = count / len(successes) * 100
            avg_dur = sum(method_durations[method]) / len(method_durations[method])
            print(f"  {method:<10}: {bar:<20} {count:>3} ({pct:.0f}%) avg {avg_dur:.1f}s")
        print()

    # Domain stats from successes
    if successes:
        domain_stats = defaultdict(lambda: {'count': 0, 'methods': defaultdict(int), 'durations': []})
        for s in successes:
            d = s.get('domain', urlparse(s.get('url', '')).netloc or 'unknown')
            domain_stats[d]['count'] += 1
            domain_stats[d]['methods'][s.get('primary_method', 'unknown')] += 1
            domain_stats[d]['durations'].append(s.get('duration_seconds', 0))

        top_domains = sorted(domain_stats.items(), key=lambda x: -x[1]['count'])[:10]
        if top_domains:
            print(f"热门域名 (Top {min(10, len(top_domains))}):")
            for domain, stats in top_domains:
                top_method = max(stats['methods'], key=stats['methods'].get)
                top_pct = stats['methods'][top_method] / stats['count'] * 100
                avg_dur = sum(stats['durations']) / len(stats['durations'])
                print(f"  {domain:<30}: {stats['count']:>3} 次 | {top_method} {top_pct:.0f}% | avg {avg_dur:.1f}s")
            print()

    # Headless Chrome stats
    headless_launched = sum(1 for s in successes if s.get('headless_auto_launched'))
    if headless_launched > 0:
        print(f"Headless Chrome: 自动启动 {headless_launched} 次 / {len(successes)} 次成功采集")
        print()

    # Top failure reasons
    if failures:
        reason_counts = defaultdict(int)
        for f in failures:
            reason_counts[f.get('failure_reason', 'unknown')] += 1
        top_reasons = sorted(reason_counts.items(), key=lambda x: -x[1])[:5]
        print(f"失败原因 Top {min(5, len(top_reasons))}:")
        for reason, count in top_reasons:
            print(f"  {reason:<40}: {count} 次")
        print()


def _run_learn(args):
    """Analyze fetch failure logs and suggest routing rules.

    Usage:
        wf learn                  # Show failure analysis + routing suggestions
        wf learn --since 7d       # Only analyze last 7 days
        wf learn --apply          # Auto-append suggestions to routing.yaml
    """
    import json
    from datetime import datetime, timedelta
    from collections import defaultdict
    from urllib.parse import urlparse

    log_path = Path.home() / '.wf' / 'fetch_failures.jsonl'
    if not log_path.exists():
        print("No failure log found (~/.wf/fetch_failures.jsonl)")
        print("Run wf to fetch some pages first — failures are logged automatically.")
        return

    # Parse --since argument
    since = None
    apply_mode = '--apply' in args
    for i, arg in enumerate(args):
        if arg == '--since' and i + 1 < len(args):
            val = args[i + 1]
            days = int(val.rstrip('d')) if val.endswith('d') else int(val)
            since = datetime.now() - timedelta(days=days)

    # Read and parse log entries
    entries = []
    for line in log_path.read_text().strip().split('\n'):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            if since:
                ts = datetime.fromisoformat(entry.get('ts', ''))
                if ts < since:
                    continue
            entries.append(entry)
        except (json.JSONDecodeError, ValueError):
            continue

    if not entries:
        print("No failure entries found" + (f" since {since.date()}" if since else "") + ".")
        return

    # Aggregate by domain
    domain_stats = defaultdict(lambda: {'count': 0, 'types': defaultdict(int), 'reasons': defaultdict(int)})
    for entry in entries:
        url = entry.get('url', '')
        domain = urlparse(url).netloc or url
        stats = domain_stats[domain]
        stats['count'] += 1
        stats['types'][entry.get('failure_type', 'unknown')] += 1
        stats['reasons'][entry.get('failure_reason', 'unknown')] += 1

    # Sort by failure count descending
    sorted_domains = sorted(domain_stats.items(), key=lambda x: x[1]['count'], reverse=True)

    # Display analysis
    print(f"\n📊 Fetch Failure Analysis ({len(entries)} failures, {len(sorted_domains)} domains)")
    print("=" * 70)

    suggestions = []
    for domain, stats in sorted_domains:
        count = stats['count']
        top_reason = max(stats['reasons'], key=stats['reasons'].get)
        top_type = max(stats['types'], key=stats['types'].get)
        print(f"\n  {domain}: {count} failures")
        print(f"    Type: {top_type} | Reason: {top_reason}")

        # Generate routing suggestion for domains with 3+ failures
        if count >= 3:
            if 'spa_shell' in top_reason:
                fetcher = 'cdp'
                reason = 'SPA shell detected, needs JS rendering'
            elif 'antibot' in top_reason:
                fetcher = 'selenium'
                reason = 'Anti-bot detected, needs stealth browser'
            elif 'too_short' in top_reason:
                fetcher = 'cdp'
                reason = 'Content too short, likely needs JS rendering'
            elif 'ssl' in top_reason.lower() or 'SSL' in str(stats['reasons']):
                fetcher = 'selenium'
                reason = 'SSL issues, use browser fallback'
            else:
                fetcher = 'cdp'
                reason = f'Frequent failures ({count}x): {top_reason}'

            suggestions.append({
                'domain': domain,
                'fetcher': fetcher,
                'reason': reason,
                'count': count,
            })

    # Display suggestions
    if suggestions:
        print(f"\n\n💡 Routing Suggestions ({len(suggestions)} domains)")
        print("=" * 70)
        for s in suggestions:
            print(f"\n  - name: \"{s['domain']} - Auto-learned\"")
            print(f"    priority: 80")
            print(f"    conditions:")
            print(f"      domain: \"{s['domain']}\"")
            print(f"    action:")
            print(f"      fetcher: \"{s['fetcher']}\"")
            print(f"      reason: \"{s['reason']}\"")

        if apply_mode:
            # Find routing.yaml
            routing_paths = [
                Path.home() / '.config' / 'webfetcher' / 'routing.yaml',
                Path(__file__).parent.parent.parent / 'config' / 'routing.yaml',
            ]
            routing_path = None
            for p in routing_paths:
                if p.exists():
                    routing_path = p
                    break

            if routing_path:
                import yaml
                with open(routing_path, 'r') as f:
                    config = yaml.safe_load(f) or {}

                rules = config.get('rules', [])
                existing_domains = {r.get('conditions', {}).get('domain', '') for r in rules}
                added = 0
                for s in suggestions:
                    if s['domain'] not in existing_domains:
                        rules.append({
                            'name': f"{s['domain']} - Auto-learned",
                            'priority': 80,
                            'conditions': {'domain': s['domain']},
                            'action': {'fetcher': s['fetcher'], 'reason': s['reason']},
                        })
                        added += 1

                if added:
                    config['rules'] = rules
                    with open(routing_path, 'w') as f:
                        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
                    print(f"\n✅ Added {added} rules to {routing_path}")
                else:
                    print(f"\nAll suggested domains already have rules in {routing_path}")
            else:
                print("\n⚠️  No routing.yaml found. Create one at ~/.config/webfetcher/routing.yaml")
        else:
            print(f"\n\nRun `wf learn --apply` to auto-add these rules to routing.yaml")
    else:
        print("\n\nNo domains with 3+ failures — no routing suggestions yet.")

    print()


def main():
    # Check for updates (async, non-blocking)
    try:
        from webfetcher.version_checker import check_for_updates
        check_for_updates()
    except Exception:
        pass  # Never let version check crash the program

    if len(sys.argv) < 2:
        print_help()
        return

    # Import webfetcher.core here to avoid circular imports
    from webfetcher import core as webfetcher_module

    # Parse arguments
    raw_args = sys.argv[1:]

    # Extract --stdout flag before mode dispatch
    stdout_mode = '--stdout' in raw_args
    if stdout_mode:
        raw_args = [a for a in raw_args if a != '--stdout']

    if not raw_args:
        print_help()
        return

    cmd = raw_args[0]

    # URL extraction from mixed text (new feature)
    extracted_url = None
    extraction_performed = False

    # Skip extraction for known commands
    skip_commands = ['help', '-h', '--help', 'fast', 'full', 'site', 'raw', 'batch', 'v1', 'v2', 'learn', 'stats', 'diagnose']

    if cmd not in skip_commands:
        # Attempt to extract URL from mixed text
        original_cmd = cmd
        cmd, extraction_performed = extract_url_from_text(cmd)

        if extraction_performed:
            # Provide user feedback about extraction
            logger.info(f"✓ 已从文本中提取URL: {cmd}")
            if len(original_cmd) > 80:
                logger.info(f"  原始输入: {original_cmd[:80]}...")
            else:
                logger.info(f"  原始输入: {original_cmd}")
            extracted_url = cmd

    # Quick grab mode - detect URL (modified condition)
    if extracted_url or 'http://' in cmd or 'https://' in cmd or 'file://' in cmd or ('.' in cmd and cmd not in ['help', '-h', '--help']):
        if extracted_url:
            url = extracted_url
        elif cmd.startswith(('http://', 'https://', 'file://')):
            url = cmd
        else:
            url = f'https://{cmd}'
        url = clean_wechat_url(url)
        _prepare_and_run(webfetcher_module, url, raw_args[1:], stdout_mode)

    # 快速模式
    elif cmd == 'fast':
        if len(raw_args) < 2:
            print("错误: fast模式需要提供URL")
            print("用法: wf fast <URL> [输出目录]")
            return
        url = _prepare_url('Fast模式', raw_args[1])
        _prepare_and_run(webfetcher_module, url, raw_args[2:], stdout_mode,
                         ['--render', 'never', '--timeout', '30'])

    # 完整模式
    elif cmd == 'full':
        if len(raw_args) < 2:
            print("错误: full模式需要提供URL")
            print("用法: wf full <URL> [输出目录]")
            return
        url = _prepare_url('Full模式', raw_args[1])
        _prepare_and_run(webfetcher_module, url, raw_args[2:], stdout_mode,
                         ['--download-assets', '--render', 'auto'])

    # 站点爬虫
    elif cmd == 'site':
        if len(raw_args) < 2:
            print("错误: site模式需要提供URL")
            print("用法: wf site <URL> [输出目录] [选项]")
            print("\n可用选项 / Available options:")
            print("  --max-pages N          最大爬取页面数 (默认: 100) / Max pages to crawl (default: 100)")
            print("  --max-depth N          最大爬取深度 (默认: 5) / Max crawl depth (default: 5)")
            print("  --delay SECONDS        请求间隔秒数 (默认: 0.5) / Request delay in seconds (default: 0.5)")
            print("  --follow-pagination    跟随分页链接 / Follow pagination links")
            print("  --same-domain-only     仅爬取同域名 (默认启用) / Only crawl same domain (default enabled)")
            print("  --use-sitemap          使用sitemap.xml进行爬取 / Use sitemap.xml for crawling")
            return

        url = _prepare_url('Site模式', raw_args[1])
        output_dir, remaining_args = parse_output_dir(raw_args[2:])
        if not stdout_mode:
            ensure_output_dir(output_dir)

        # Build webfetcher command with configurable parameters
        cmd_args = [url, '-o', output_dir, '--crawl-site']

        # Extract user-specified parameters or use defaults
        param_map = {'--max-pages': None, '--max-crawl-depth': None, '--max-depth': None,
                     '--delay': None, '--crawl-delay': None}
        i = 0
        while i < len(remaining_args):
            arg = remaining_args[i]
            if arg in param_map and i + 1 < len(remaining_args):
                param_map[arg] = remaining_args[i + 1]
                i += 2
                continue
            i += 1

        max_pages_value = param_map['--max-pages'] or '100'
        max_depth_value = param_map['--max-crawl-depth'] or param_map['--max-depth'] or '5'
        delay_value = param_map['--delay'] or param_map['--crawl-delay'] or '0.5'

        cmd_args.extend(['--max-pages', max_pages_value])
        cmd_args.extend(['--max-crawl-depth', max_depth_value])
        cmd_args.extend(['--crawl-delay', delay_value])

        # Add boolean flags if present
        if '--follow-pagination' in remaining_args:
            cmd_args.append('--follow-pagination')
        if '--use-sitemap' in remaining_args:
            cmd_args.append('--use-sitemap')
            logger.info("Sitemap-first crawling enabled / 已启用sitemap优先爬取")
        cmd_args.append('--same-domain-only')

        # Add any other remaining args (like --fetch-mode, etc.)
        consumed_params = set(param_map.keys()) | {'--follow-pagination', '--same-domain-only', '--use-sitemap'}
        for arg in remaining_args:
            if arg not in consumed_params and not (arg.replace('.', '').isdigit() or arg.startswith('/')):
                cmd_args.append(arg)

        logger.info(f"Site crawling with: max-pages={max_pages_value}, max-depth={max_depth_value}, delay={delay_value}")
        stdout_args = ['--stdout'] if stdout_mode else []
        run_webfetcher(webfetcher_module, cmd_args + stdout_args)

    # Raw模式
    elif cmd == 'raw':
        if len(raw_args) < 2:
            print("错误: raw模式需要提供URL")
            print("用法: wf raw <URL> [输出目录]")
            return
        url = _prepare_url('Raw模式', raw_args[1])
        _prepare_and_run(webfetcher_module, url, raw_args[2:], stdout_mode, ['--raw'])

    # V1引擎模式（显式降级）
    elif cmd == 'v1':
        if len(raw_args) < 2:
            print("错误: v1模式需要提供URL")
            print("用法: wf v1 <URL> [输出目录]")
            print("\nV1引擎为原始解析器（降级使用）")
            return
        url = _prepare_url('V1模式', raw_args[1])
        _prepare_and_run(webfetcher_module, url, raw_args[2:], stdout_mode,
                         extra_args=['--engine', 'v1'])

    # V2引擎模式（显式指定，等价于默认）
    elif cmd == 'v2':
        if len(raw_args) < 2:
            print("错误: v2模式需要提供URL")
            print("用法: wf v2 <URL> [输出目录]")
            print("\nV2引擎使用多策略竞赛提取 + 质量检测 + 域名记忆")
            return
        url = _prepare_url('V2模式', raw_args[1])
        _prepare_and_run(webfetcher_module, url, raw_args[2:], stdout_mode,
                         extra_args=['--engine', 'v2'])

    # 批量抓取
    elif cmd == 'batch':
        if stdout_mode:
            print("错误: --stdout 不支持批量模式", file=sys.stderr)
            return
        if len(raw_args) < 2:
            print("错误: batch模式需要提供URL文件")
            print("用法: wf batch <urls.txt> [输出目录]")
            return
        urls_file = raw_args[1]
        if not os.path.exists(urls_file):
            print(f"错误: 文件 {urls_file} 不存在")
            return

        output_dir, remaining_args = parse_output_dir(raw_args[2:])
        ensure_output_dir(output_dir)

        with open(urls_file) as f:
            urls = [line.strip() for line in f if line.strip()]

        print(f"准备抓取 {len(urls)} 个URL...")
        print(f"输出目录: {output_dir}")
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] 抓取: {url}")
            if not url.startswith('http'):
                url = f'https://{url}'
            run_webfetcher(webfetcher_module, [url, '-o', output_dir] + remaining_args)

    # 失败日志分析 + 路由学习
    elif cmd == 'learn':
        _run_learn(raw_args[1:])

    # 采集统计
    elif cmd == 'stats':
        _run_stats(raw_args[1:])

    # 诊断系统
    elif cmd == 'diagnose' or cmd == '--diagnose':
        diagnose_system()

    # 帮助
    elif cmd in ['-h', '--help', 'help']:
        print_help()

    # 默认：传递给webfetcher
    else:
        output_dir, remaining_args = parse_output_dir(raw_args)
        if not stdout_mode:
            ensure_output_dir(output_dir)
        stdout_args = ['--stdout'] if stdout_mode else []
        run_webfetcher(webfetcher_module, ['-o', output_dir] + remaining_args + stdout_args)

def run_webfetcher(webfetcher_module, args):
    """运行webfetcher.core并传递参数"""
    try:
        # Temporarily modify sys.argv to pass arguments to webfetcher
        original_argv = sys.argv
        sys.argv = ['webfetcher'] + args

        try:
            # Call the main function
            webfetcher_module.main()
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    except KeyboardInterrupt:
        print("\n已取消", file=sys.stderr)
        sys.exit(130)
    except SystemExit:
        # argparse / explicit sys.exit() — 透传退出码
        raise
    except Exception as e:
        # B1+B2+B5: 结构化错误输出，默认不显示 traceback；--debug 才打
        from webfetcher.errors.user_facing import classify_user_error, format_user_error
        err = classify_user_error(e)
        print(format_user_error(err), file=sys.stderr)
        if DEBUG_MODE:
            import traceback
            print("\n--- traceback (--debug) ---", file=sys.stderr)
            traceback.print_exc()
        sys.exit(err.exit_code)

def print_help():
    # 获取当前环境变量
    env_output = os.environ.get('WF_OUTPUT_DIR', '未设置')

    print(f"""
wf - WebFetcher便捷命令

AI agent 场景速查（按场景选命令，比按参数堆更友好）:
  含 URL 的混合文本（自动提取）:  wf "<原文 + URL>" --stdout
  读文章正文（最常用 stdout）:    wf <URL> --stdout
  读文章正文 + 加速（拦截图片）:   wf <URL> --stdout --lite
  存网页含图（含资源）:           wf <URL> -o ./out/
  静态站快速模式:                 wf fast <URL> --stdout
  批量抓取（不支持 stdout）:      wf batch urls.txt -o ./out/
  原始 HTML（不解析）:            wf raw <URL> -o ./out/

错误输出（AI 友好）:
  默认错误是三段式（错误类型/说明/建议），无 Python traceback。
  错误分类示例：URL_INVALID / DNS_FAILURE / SSL_ERROR / HTTP_4XX / HTTP_5XX
                / TIMEOUT / CDP_LAUNCH_FAILED / CONFIG_ERROR / UNKNOWN
  按"建议:"字段路由下一步操作即可。
  调试需要看 traceback：加 --debug

日志级别:
  默认       静默（仅警告/错误）
  -v/--verbose   显示 INFO 级（含启动横幅、路由决策）
  --debug    显示 DEBUG 级 + 失败时打 traceback

陷阱与限制（避开常见误用）:
  --lite 拦截图片资源 → 想存图就别加 --lite
  微信/小红书自动走 CDP → 用户不需手动加，路由表会处理
  登录态站点 → 需要 manual_chrome（chrome 已登录的本机会话）
  --stdout + batch 模式 = 冲突（batch 写文件，不输 stdout）
  selenium/manual_chrome 依赖本机 Chrome；未装时会自动 skip

输出目录指定方式（按优先级排序）:
  1. 使用 -o 参数（最明确，推荐用于复杂URL）:
     wf example.com/path -o ~/Desktop/
     wf -o ~/Desktop/ example.com/path

输出目录指定方式（按优先级排序）:
  1. 使用 -o 参数（最明确，推荐用于复杂URL）:
     wf example.com/path -o ~/Desktop/
     wf -o ~/Desktop/ example.com/path

  2. 使用 -- 分隔符（明确分界）:
     wf example.com/path -- ~/Desktop/

  3. 智能位置参数（简洁，适合简单URL）:
     wf example.com ~/Desktop/
     wf example.com ./output/

  4. 环境变量（设置默认目录）:
     export WF_OUTPUT_DIR=~/Documents/fetched

  5. 默认目录: ./output/

  当前环境变量 WF_OUTPUT_DIR: {env_output}

最简用法:
  wf example.com                    # 保存到./output/
  wf example.com ~/Desktop/         # 智能检测输出目录
  wf example.com -o ~/Desktop/      # 明确指定输出目录
  wf example.com -- ~/Desktop/      # 使用分隔符

自动URL提取:
  wf "文本内容 http://example.com 其他文字"  # 自动提取URL
  wf "mp.weixin.qq.com/s/xxx 微信文章"       # 提取微信链接
  wf "http://xhslink.com/abc 小红书笔记"     # 提取小红书链接

  支持的模式：
  - 标准HTTP/HTTPS链接
  - 短链接（xhslink, t.cn, bit.ly等）
  - 微信文章链接
  - 自动添加https://协议

快捷模式:
  wf fast URL [输出目录]            # 快速模式（不渲染JS）
  wf full URL [输出目录]            # 完整模式（含资源）
  wf raw URL [输出目录]             # Raw模式（完整内容）
  wf v1 URL [输出目录]              # V1引擎（原始解析器，降级使用）
  wf v2 URL [输出目录]              # V2引擎（竞赛提取+域名记忆，等价于默认）
  wf site URL [输出目录]            # 整站爬虫
  wf batch urls.txt [输出目录]     # 批量抓取
  wf diagnose                       # 系统诊断（含ChromeDriver检查）
  wf learn                          # 分析失败日志，建议路由规则
  wf learn --apply                  # 自动将建议写入routing.yaml
  wf learn --since 7d               # 只分析最近7天

Stdout模式:
  wf example.com --stdout             # 输出到终端（stdout），不保存文件
  wf --stdout example.com             # 同上，参数位置灵活
  wf fast example.com --stdout        # 快速模式 + stdout
  wf example.com --stdout | pbcopy    # 配合管道使用

处理复杂URL的示例:
  # URL包含路径时，推荐使用-o或--
  wf example.com/path/to/page -o ~/Desktop/
  wf example.com/path/to/page -- ~/Documents/

  # 简单URL可直接使用位置参数
  wf example.com ~/Desktop/
  wf mp.weixin.qq.com/s/xxx ./articles/

  # 批量和站点模式
  wf site docs.python.org -o ./python-docs/
  wf batch ./urls.txt -- ~/Downloads/

高级用法:
  # 组合多个参数
  wf fast example.com -o ./output --timeout 10
  wf site python.org -- ~/docs/ --max-pages 100

  # Selenium集成
  wf example.com --fetch-mode selenium    # 强制使用Selenium
  wf example.com --fetch-mode auto        # 自动回退（默认）
  wf example.com --selenium-timeout 60    # 设置Selenium超时

  # 设置默认输出目录后
  export WF_OUTPUT_DIR=~/Documents/web-content
  wf example.com                    # 自动保存到~/Documents/web-content

抓取方法说明 (Fetch Methods):
  -m auto / --fetch-mode auto     # urllib→CDP智能降级（默认，已知JS站直接走CDP）
  -m urllib / -u                  # 仅使用urllib（轻量级，静态站点）
  -m cdp / -c                     # 仅使用CDP（JS渲染+保留登录态，推荐）
  -m selenium / -s                # 仅使用Selenium（备选，显式指定时可用）
  --headless auto/always/never    # Headless Chrome控制（默认auto：按需自动启动）
  --selenium-timeout 30           # Selenium/CDP页面加载超时（秒）

  auto模式降级链: urllib → CDP(自动headless) → 人工兜底
  已知JS站点(微信/小红书/知乎/掘金/B站等)通过路由表直接走CDP，跳过urllib
  CDP优势：轻量、快速、保留登录状态、自动启动headless Chrome

  快捷示例:
  wf -c example.com               # 使用CDP
  wf -u example.com               # 使用urllib
  wf -s example.com               # 使用Selenium

加速模式:
  wf example.com --lite --stdout     # 轻量CDP抓取，跳过图片/CSS/字体下载，快3-5x
  wf example.com --lite -c --stdout  # 同上（显式CDP）
  --lite 说明：
    - 拦截image/CSS/font/media的HTTP下载，页面渲染更快
    - 图片URL仍保留在输出中（只是不下载图片字节）
    - 适合：AI分析文章内容、快速提取正文
    - 不适合：需要下载图片保存的场景（用默认模式 + --download-assets）
    - 仅对CDP/auto模式有效，urllib/selenium模式下自动忽略
    - --lite + --download-assets 时自动禁用lite

采集统计与路由学习:
  wf stats                          # 查看采集统计（成功率/Fetcher/域名/耗时）
  wf stats --since 7d               # 只看最近7天
  wf stats --all                    # 查看全部历史
  wf learn                          # 查看采集失败统计（按域名聚合）
  wf learn --apply                  # 一键将建议写入routing.yaml
  wf learn --since 7d               # 只看最近7天

  所有采集自动记录到 ~/.wf/（成功: fetch_history.jsonl, 失败: fetch_failures.jsonl）
  积累数据后运行 wf stats 查看全局概况，wf learn 优化路由规则

原始命令:
  wf [任何webfetcher参数]           # 直接传递给webfetcher.py

查看完整帮助:
  wf --help                         # 显示webfetcher的完整帮助
""")

if __name__ == '__main__':
    main()
