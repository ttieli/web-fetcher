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
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('wf')

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
    clean_url_pattern = r'^https?://[^\s]+$'
    if re.match(clean_url_pattern, text.strip()):
        return text.strip(), False

    # Comprehensive URL extraction patterns for Chinese social media
    url_patterns = [
        # WeChat article links (high priority for business use)
        r'(https?://mp\.weixin\.qq\.com/s/[^\s\u4e00-\u9fff]+)',
        r'(mp\.weixin\.qq\.com/s/[^\s\u4e00-\u9fff]+)',
        # Specific short-link domains
        r'(?:^|\s)((?:xhslink|t|dwz|url|c|6|bit|tinyurl)\.(?:com|cn|co|ly|me)/[^\s\u4e00-\u9fff]+)',
        # Standard URLs LAST (most generic)
        r'https?://[^\s"\']+',
    ]

    for pattern in url_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Extract first URL found
            url = matches[0] if isinstance(matches[0], str) else matches[0][0]
            # Remove trailing Chinese/English punctuation
            url = re.sub(r'[,!?。，！？、）)】」』》\uff09]+$', '', url)
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

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    # Import webfetcher.core here to avoid circular imports
    from webfetcher import core as webfetcher_module

    # Parse arguments
    raw_args = sys.argv[1:]
    cmd = raw_args[0]

    # URL extraction from mixed text (new feature)
    extracted_url = None
    extraction_performed = False

    # Skip extraction for known commands
    skip_commands = ['help', '-h', '--help', 'fast', 'full', 'site', 'raw', 'batch']

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
        # Use extracted URL if available, otherwise process normally
        # Support file:// protocol for local files
        if extracted_url:
            url = extracted_url
        elif cmd.startswith(('http://', 'https://', 'file://')):
            url = cmd
        else:
            url = f'https://{cmd}'
        # Clean WeChat URLs (remove poc_token that causes errors)
        url = clean_wechat_url(url)
        # Parse output directory
        output_dir, remaining_args = parse_output_dir(raw_args[1:])
        ensure_output_dir(output_dir)
        # Run webfetcher
        run_webfetcher(webfetcher_module, [url, '-o', output_dir] + remaining_args)

    # 快速模式
    elif cmd == 'fast':
        if len(raw_args) < 2:
            print("错误: fast模式需要提供URL")
            print("用法: wf fast <URL> [输出目录]")
            return

        # Extract URL from potentially mixed text
        url_input = raw_args[1]
        url, was_extracted = extract_url_from_text(url_input)

        if was_extracted:
            logger.info(f"✓ Fast模式：已从文本中提取URL: {url}")

        if not url.startswith('http'):
            url = f'https://{url}'

        # Clean WeChat URLs (remove poc_token that causes errors)
        url = clean_wechat_url(url)

        # Parse output directory
        output_dir, remaining_args = parse_output_dir(raw_args[2:])
        ensure_output_dir(output_dir)
        run_webfetcher(webfetcher_module, [url, '-o', output_dir, '--render', 'never', '--timeout', '30'] + remaining_args)

    # 完整模式
    elif cmd == 'full':
        if len(raw_args) < 2:
            print("错误: full模式需要提供URL")
            print("用法: wf full <URL> [输出目录]")
            return

        # Extract URL from potentially mixed text
        url_input = raw_args[1]
        url, was_extracted = extract_url_from_text(url_input)

        if was_extracted:
            logger.info(f"✓ Full模式：已从文本中提取URL: {url}")

        if not url.startswith('http'):
            url = f'https://{url}'

        # Parse output directory
        output_dir, remaining_args = parse_output_dir(raw_args[2:])
        ensure_output_dir(output_dir)
        run_webfetcher(webfetcher_module, [url, '-o', output_dir, '--download-assets', '--render', 'auto'] + remaining_args)

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
            print("  --use-sitemap          使用sitemap.xml进行爬取 / Use sitemap.xml for crawling (Phase 2)")
            return

        # Extract URL from potentially mixed text
        url_input = raw_args[1]
        url, was_extracted = extract_url_from_text(url_input)

        if was_extracted:
            logger.info(f"✓ Site模式：已从文本中提取URL: {url}")

        if not url.startswith('http'):
            url = f'https://{url}'

        # Parse output directory and extract parameters
        output_dir, remaining_args = parse_output_dir(raw_args[2:])
        ensure_output_dir(output_dir)

        # Build webfetcher command with configurable parameters
        cmd_args = [url, '-o', output_dir, '--crawl-site']

        # Extract user-specified parameters or use defaults
        max_pages_value = None
        max_depth_value = None
        delay_value = None

        # Extract parameters manually (simple approach)
        i = 0
        while i < len(remaining_args):
            arg = remaining_args[i]

            if arg in ['--max-pages', '--max-crawl-depth', '--max-depth', '--delay', '--crawl-delay']:
                if i + 1 < len(remaining_args):
                    value = remaining_args[i + 1]

                    if arg == '--max-pages':
                        max_pages_value = value
                    elif arg in ['--max-crawl-depth', '--max-depth']:
                        max_depth_value = value
                    elif arg in ['--delay', '--crawl-delay']:
                        delay_value = value

                    # Skip next item (the value)
                    i += 2
                    continue

            i += 1

        # Apply defaults
        if max_pages_value is None:
            max_pages_value = '100'
        if max_depth_value is None:
            max_depth_value = '5'
        if delay_value is None:
            delay_value = '0.5'

        cmd_args.extend(['--max-pages', max_pages_value])
        cmd_args.extend(['--max-crawl-depth', max_depth_value])
        cmd_args.extend(['--crawl-delay', delay_value])

        # Add boolean flags if present
        if '--follow-pagination' in remaining_args:
            cmd_args.append('--follow-pagination')

        if '--use-sitemap' in remaining_args:
            cmd_args.append('--use-sitemap')
            logger.info("Sitemap-first crawling enabled / 已启用sitemap优先爬取")

        # same-domain-only is default, explicitly add it
        cmd_args.append('--same-domain-only')

        # Add any other remaining args (like --fetch-mode, etc.)
        for arg in remaining_args:
            if arg not in ['--max-pages', '--max-depth', '--max-crawl-depth',
                          '--delay', '--crawl-delay', '--follow-pagination', '--same-domain-only', '--use-sitemap']:
                # Check if it's a value (next to a parameter we already processed)
                if not (arg.replace('.', '').isdigit() or arg.startswith('/')):
                    cmd_args.append(arg)

        logger.info(f"Site crawling with: max-pages={max_pages_value}, max-depth={max_depth_value}, delay={delay_value}")
        run_webfetcher(webfetcher_module, cmd_args)

    # Raw模式
    elif cmd == 'raw':
        if len(raw_args) < 2:
            print("错误: raw模式需要提供URL")
            print("用法: wf raw <URL> [输出目录]")
            return

        # Extract URL from potentially mixed text
        url_input = raw_args[1]
        url, was_extracted = extract_url_from_text(url_input)

        if was_extracted:
            logger.info(f"✓ Raw模式：已从文本中提取URL: {url}")

        if not url.startswith('http'):
            url = f'https://{url}'

        # Parse output directory
        output_dir, remaining_args = parse_output_dir(raw_args[2:])
        ensure_output_dir(output_dir)
        run_webfetcher(webfetcher_module, [url, '-o', output_dir, '--raw'] + remaining_args)

    # 批量抓取
    elif cmd == 'batch':
        if len(raw_args) < 2:
            print("错误: batch模式需要提供URL文件")
            print("用法: wf batch <urls.txt> [输出目录]")
            return
        urls_file = raw_args[1]
        if not os.path.exists(urls_file):
            print(f"错误: 文件 {urls_file} 不存在")
            return

        # 解析输出目录
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

    # 诊断系统
    elif cmd == 'diagnose' or cmd == '--diagnose':
        diagnose_system()

    # 帮助
    elif cmd in ['-h', '--help', 'help']:
        print_help()

    # 默认：传递给webfetcher
    else:
        # 对于其他命令，也处理输出目录
        output_dir, remaining_args = parse_output_dir(raw_args)
        ensure_output_dir(output_dir)
        run_webfetcher(webfetcher_module, ['-o', output_dir] + remaining_args)

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
        print("\n已取消")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def print_help():
    # 获取当前环境变量
    env_output = os.environ.get('WF_OUTPUT_DIR', '未设置')

    print(f"""
wf - WebFetcher便捷命令

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
  wf site URL [输出目录]            # 整站爬虫
  wf batch urls.txt [输出目录]     # 批量抓取
  wf diagnose                       # 系统诊断（含ChromeDriver检查）

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

Selenium集成说明:
  --fetch-mode auto     # urllib失败时自动切换到Selenium（默认）
  --fetch-mode urllib   # 仅使用urllib
  --fetch-mode selenium # 仅使用Selenium（需要Chrome调试会话）
  --selenium-timeout 30 # Selenium页面加载超时（秒）

  启动Chrome调试会话: ./config/chrome-debug.sh

原始命令:
  wf [任何webfetcher参数]           # 直接传递给webfetcher.py

查看完整帮助:
  wf --help                         # 显示webfetcher的完整帮助
""")

if __name__ == '__main__':
    main()
