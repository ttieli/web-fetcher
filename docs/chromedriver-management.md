# ChromeDriver Version Management / ChromeDriver版本管理

## Overview / 概述

The ChromeDriver Version Management system automatically detects and synchronizes ChromeDriver versions with your installed Chrome browser.

ChromeDriver版本管理系统自动检测并同步ChromeDriver版本与已安装的Chrome浏览器。

## Quick Start / 快速入门

### Check Compatibility / 检查兼容性

```bash
python scripts/manage_chromedriver.py check
```

### Auto-Sync Versions / 自动同步版本

```bash
python scripts/manage_chromedriver.py sync
```

### Full Diagnostic / 完整诊断

```bash
python scripts/manage_chromedriver.py doctor
```

## Commands / 命令

### `check` - Version Check

Displays current Chrome and ChromeDriver versions and compatibility status.

显示当前Chrome和ChromeDriver版本及兼容性状态。

**Usage:**
```bash
python scripts/manage_chromedriver.py check
```

**Output:**
- Chrome version / Chrome版本
- ChromeDriver version / ChromeDriver版本
- Compatibility status / 兼容性状态
- Recommendations / 建议

**Exit Codes:**
- `0`: Compatible / 兼容
- `1`: Mismatch / 不匹配
- `2`: Error / 错误

### `sync` - Download Matching Version

Downloads ChromeDriver matching your Chrome version.

下载与Chrome版本匹配的ChromeDriver。

**Usage:**
```bash
python scripts/manage_chromedriver.py sync [--force]
```

**Options:**
- `--force`: Force re-download even if cached / 即使已缓存也强制重新下载

**Features:**
- Automatic version detection / 自动版本检测
- Progress bar display / 进度条显示
- Download retry with exponential backoff / 指数退避重试
- Automatic fallback to selenium-manager / 自动回退到selenium-manager

### `doctor` - Full Diagnostic

Comprehensive system diagnostic.

全面系统诊断。

**Checks:**
1. Version compatibility / 版本兼容性
2. Cache status / 缓存状态
3. Active version / 活动版本
4. Recommendations / 建议

### `list` - List Cached Versions

Shows all cached ChromeDriver versions.

显示所有已缓存的ChromeDriver版本。

**Usage:**
```bash
python scripts/manage_chromedriver.py list
```

### `clean` - Remove Old Versions

Removes old cached versions (keeps latest 2).

移除旧的缓存版本（保留最新2个）。

**Usage:**
```bash
python scripts/manage_chromedriver.py clean
```

## Integration with wf.py

The version check is integrated into the wf.py diagnostic command:

```bash
python wf.py diagnose
# or
python wf.py --diagnose
```

This will:
1. Check Python version / 检查Python版本
2. Check working directory / 检查工作目录
3. Check ChromeDriver compatibility / 检查ChromeDriver兼容性
4. Check output directory / 检查输出目录
5. Exit with code 3 if ChromeDriver mismatch detected / 如果检测到ChromeDriver不匹配则以代码3退出
6. Provide fix instructions / 提供修复说明

## Cache Structure / 缓存结构

```
~/.webfetcher/drivers/
├── 141.0.6496.0/
│   └── chromedriver
├── 140.0.6476.0/
│   └── chromedriver
└── current -> 141.0.6496.0/chromedriver
```

## Troubleshooting / 故障排除

### Chrome Not Found / Chrome未找到

**Problem:** `Chrome browser not found on this system`

**Solution:**
- Install Google Chrome
- macOS: Check `/Applications/Google Chrome.app` exists

### Download Fails / 下载失败

**Problem:** Network errors or download failures

**Solution:**
1. Check internet connection / 检查网络连接
2. Try again (automatic retry with backoff) / 重试（自动退避重试）
3. Use `--force` to force re-download / 使用 `--force` 强制重新下载

### Permission Denied / 权限被拒绝

**Problem:** Cannot write to cache directory

**Solution:**
```bash
chmod 755 ~/.webfetcher/drivers
```

## Platform Support / 平台支持

- ✅ macOS (fully supported / 完全支持)
- ⚠️ Linux (planned / 计划中)
- ⚠️ Windows (planned / 计划中)

Current release is macOS-only. Cross-platform support coming in future versions.

当前版本仅支持macOS。跨平台支持将在未来版本中提供。

## API Usage / API使用

```python
from drivers import (
    check_chrome_driver_compatibility,
    download_compatible_driver
)

# Check compatibility
result = check_chrome_driver_compatibility()
if not result.is_compatible:
    print(f"Mismatch: {result.message_en}")

    # Auto-download matching version
    driver_path = download_compatible_driver()
    print(f"Downloaded to: {driver_path}")
```

## FAQ

**Q: How often should I run sync?**
A: Run after Chrome updates, or when you see version mismatch errors.

**Q: Can I use multiple ChromeDriver versions?**
A: Yes, all versions are cached. Use `list` to see them, `sync` switches to matching version.

**Q: What if download fails?**
A: The system automatically retries with exponential backoff and falls back to selenium-manager.

---

**Last Updated:** 2025-10-10
**Version:** 1.0.0
