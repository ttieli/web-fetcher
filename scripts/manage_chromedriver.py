#!/usr/bin/env python3
"""
ChromeDriver Version Management CLI
ChromeDriver版本管理命令行工具

Usage:
    manage_chromedriver.py check       # Check current versions
    manage_chromedriver.py sync        # Download matching version
    manage_chromedriver.py doctor      # Full diagnostic
    manage_chromedriver.py list        # List cached versions
    manage_chromedriver.py clean       # Remove old versions
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from drivers import (
    VersionDetector,
    VersionCache,
    VersionDownloader,
    check_chrome_driver_compatibility,
    download_compatible_driver,
    DownloadError
)

def cmd_check(args):
    """Check current Chrome and ChromeDriver versions"""
    print("Checking Chrome and ChromeDriver versions...")
    print("正在检查Chrome和ChromeDriver版本...\n")

    result = check_chrome_driver_compatibility()

    # Display versions
    print(f"Chrome Version / Chrome版本: {result.chrome_version or 'Not Found / 未找到'}")
    print(f"ChromeDriver Version / ChromeDriver版本: {result.driver_version or 'Not Found / 未找到'}")
    print(f"\nStatus / 状态: {result.status.value}")
    print(f"English / 英文: {result.message_en}")
    print(f"Chinese / 中文: {result.message_cn}")

    # Return appropriate exit code
    if result.is_compatible:
        return 0
    else:
        print(f"\n⚠️  Recommendation / 建议:")
        print(f"   Run 'manage_chromedriver.py sync' to download matching version")
        print(f"   运行 'manage_chromedriver.py sync' 下载匹配版本")
        return 1

def cmd_sync(args):
    """Download and sync ChromeDriver to match Chrome version"""
    print("Synchronizing ChromeDriver with Chrome...")
    print("正在同步ChromeDriver与Chrome版本...\n")

    detector = VersionDetector()
    chrome_version = detector.get_chrome_version()

    if not chrome_version:
        print("❌ Error: Chrome not found / 错误：未找到Chrome")
        return 2

    print(f"Target Chrome version / 目标Chrome版本: {chrome_version}")

    # Check if already cached
    cache = VersionCache()
    if cache.is_cached(chrome_version):
        print(f"✓ ChromeDriver {chrome_version} already cached / 已缓存")

        if args.force:
            print("Forcing re-download... / 强制重新下载...")
        else:
            cache.set_active(chrome_version)
            print(f"✓ Set as active version / 设为活动版本")
            return 0

    # Download
    try:
        print(f"Downloading ChromeDriver {chrome_version}... / 正在下载...")

        def progress_callback(downloaded, total):
            if total > 0:
                percent = (downloaded / total) * 100
                print(f"\rProgress / 进度: {percent:.1f}% ({downloaded}/{total} bytes)", end='')

        downloader = VersionDownloader(cache)
        driver_path = downloader.download_version(chrome_version, progress_callback)

        print(f"\n✓ Downloaded to: {driver_path}")
        print(f"✓ 已下载到: {driver_path}")

        # Set as active
        cache.set_active(chrome_version)
        print(f"✓ Set as active version / 设为活动版本")

        # Verify
        if downloader.verify_download(driver_path):
            print(f"✓ Verification successful / 验证成功")
            return 0
        else:
            print(f"⚠️  Warning: Verification failed / 警告：验证失败")
            return 1

    except DownloadError as e:
        print(f"\n❌ Download failed / 下载失败: {e}")
        return 2

def cmd_doctor(args):
    """Full diagnostic of ChromeDriver setup"""
    print("=" * 70)
    print("ChromeDriver Doctor / ChromeDriver诊断")
    print("=" * 70 + "\n")

    # 1. Version check
    print("1. Version Compatibility Check / 版本兼容性检查")
    print("-" * 70)
    result = check_chrome_driver_compatibility()
    print(f"   Chrome: {result.chrome_version or 'NOT FOUND / 未找到'}")
    print(f"   ChromeDriver: {result.driver_version or 'NOT FOUND / 未找到'}")
    print(f"   Status: {result.status.value}")
    print(f"   {result.message_en}")
    print(f"   {result.message_cn}\n")

    # 2. Cache status
    print("2. Cache Status / 缓存状态")
    print("-" * 70)
    cache = VersionCache()
    cached_versions = cache.list_cached_versions()
    active = cache.get_active_version()

    print(f"   Cache location / 缓存位置: {cache.cache_base}")
    print(f"   Cached versions / 已缓存版本: {len(cached_versions)}")
    for version in cached_versions:
        marker = "→" if version == active else " "
        print(f"     {marker} {version}")
    print(f"   Active version / 活动版本: {active or 'None / 无'}\n")

    # 3. Recommendations
    print("3. Recommendations / 建议")
    print("-" * 70)

    if not result.is_compatible:
        print(f"   ⚠️  Action required / 需要操作:")
        print(f"   Run: manage_chromedriver.py sync")
        print(f"   运行: manage_chromedriver.py sync")
        return 1
    else:
        print(f"   ✓ System is healthy / 系统正常")
        return 0

def cmd_list(args):
    """List all cached ChromeDriver versions"""
    cache = VersionCache()
    cached_versions = cache.list_cached_versions()
    active = cache.get_active_version()

    print(f"Cached ChromeDriver versions / 已缓存的ChromeDriver版本:")
    print(f"Cache location / 缓存位置: {cache.cache_base}\n")

    if not cached_versions:
        print("No cached versions / 无缓存版本")
        return 0

    for version in cached_versions:
        marker = "→" if version == active else " "
        active_text = " (active / 活动)" if version == active else ""
        print(f"{marker} {version}{active_text}")

    print(f"\nTotal / 总计: {len(cached_versions)} versions / 个版本")
    return 0

def cmd_clean(args):
    """Remove old cached versions (keep latest 2)"""
    cache = VersionCache()
    cached_versions = cache.list_cached_versions()

    if len(cached_versions) <= 2:
        print("No old versions to clean / 无需清理旧版本")
        return 0

    # Keep latest 2 versions
    to_remove = cached_versions[2:]

    print(f"Removing {len(to_remove)} old versions / 移除 {len(to_remove)} 个旧版本:")
    for version in to_remove:
        version_dir = cache.get_cache_path(version)
        print(f"  Removing / 移除: {version}")
        import shutil
        shutil.rmtree(version_dir)

    print(f"✓ Cleanup complete / 清理完成")
    return 0

def main():
    parser = argparse.ArgumentParser(
        description='ChromeDriver Version Management CLI / ChromeDriver版本管理工具'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands / 命令')

    # check command
    parser_check = subparsers.add_parser(
        'check',
        help='Check version compatibility / 检查版本兼容性'
    )
    parser_check.set_defaults(func=cmd_check)

    # sync command
    parser_sync = subparsers.add_parser(
        'sync',
        help='Download matching ChromeDriver / 下载匹配的ChromeDriver'
    )
    parser_sync.add_argument(
        '--force',
        action='store_true',
        help='Force re-download / 强制重新下载'
    )
    parser_sync.set_defaults(func=cmd_sync)

    # doctor command
    parser_doctor = subparsers.add_parser(
        'doctor',
        help='Full diagnostic / 完整诊断'
    )
    parser_doctor.set_defaults(func=cmd_doctor)

    # list command
    parser_list = subparsers.add_parser(
        'list',
        help='List cached versions / 列出缓存版本'
    )
    parser_list.set_defaults(func=cmd_list)

    # clean command
    parser_clean = subparsers.add_parser(
        'clean',
        help='Remove old versions / 移除旧版本'
    )
    parser_clean.set_defaults(func=cmd_clean)

    args = parser.parse_args()

    if not hasattr(args, 'func'):
        parser.print_help()
        return 1

    try:
        return args.func(args)
    except Exception as e:
        print(f"\n❌ Error / 错误: {e}")
        return 2

if __name__ == '__main__':
    sys.exit(main())
