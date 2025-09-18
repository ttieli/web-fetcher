# Web_Fetcher

A powerful and intelligent web content extraction tool with multi-mode crawling capabilities and smart URL parsing.

一个功能强大的智能网络内容提取工具，具备多模式爬取能力和智能URL解析功能。

[English](#english) | [中文](#中文)

---

## English

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Web_Fetcher

# Install dependencies
pip install -r requirements.txt

# Make the script executable (optional)
chmod +x wf.py
```

### Quick Start

```bash
# Basic usage - extract content from a URL
wf https://example.com

# Extract URL from mixed text (Chinese/English)
wf "Check this article 看这篇文章 http://example.com/article"

# Fast mode - quick content extraction
wf fast https://example.com

# Full mode - comprehensive extraction
wf full https://example.com

# Site mode - crawl entire website
wf site https://example.com

# Raw mode - get original HTML
wf raw https://example.com
```

### Features

#### 🎯 Smart URL Extraction
Automatically extracts URLs from mixed language text, supporting various platforms including WeChat articles and Xiaohongshu posts.

#### 🚀 Multiple Crawling Modes
- **Single Page**: Default mode for single page content
- **Fast Mode**: Quick extraction with minimal processing
- **Full Mode**: Comprehensive content extraction
- **Site Mode**: Complete website crawling
- **Raw Mode**: Original HTML without processing

#### 🌐 Platform Support
- WeChat Articles (with JavaScript filtering)
- Xiaohongshu (with image extraction)
- Hugo/Jekyll static sites
- General web pages

#### 📸 Image Handling
```bash
# Default - show image URLs only
wf https://example.com

# Download images
wf https://example.com --download-assets

# Legacy compatibility mode
WF_LEGACY_IMAGE_MODE=1 wf https://example.com
```

#### 📁 Output Control
```bash
# Custom output directory
wf https://example.com -o ./my-output

# Verbose logging
wf https://example.com --verbose

# Raw HTML output
wf https://example.com --raw
```

### Common Use Cases

#### Extract WeChat Article
```bash
wf "https://mp.weixin.qq.com/s/<article-id>"
```

#### Crawl Documentation Site
```bash
wf site https://example.com -o ./docs-backup
```

#### Quick Content Check
```bash
wf fast https://example.com/latest
```

#### Download Article with Images
```bash
wf https://example.com/post --download-assets
```

### Advanced Usage

#### Environment Variables
```bash
# Enable legacy image mode
export WF_LEGACY_IMAGE_MODE=1

# Set default output directory
export WF_OUTPUT_DIR=/path/to/output
```

#### Batch Processing
```bash
# Process multiple URLs from a file
while IFS= read -r url; do
    wf "$url" -o ./batch-output
done < urls.txt
```

### Requirements

- Python 3.7+
- BeautifulSoup4
- Requests
- Other dependencies listed in requirements.txt

### Error Handling

The tool includes:
- Automatic retry mechanism for failed requests
- Intelligent content extraction fallbacks
- Comprehensive error logging with `--verbose` flag

---

## 中文

### 安装

```bash
# 克隆仓库
git clone <repository-url>
cd Web_Fetcher

# 安装依赖
pip install -r requirements.txt

# 设置脚本可执行权限（可选）
chmod +x wf.py
```

### 快速开始

```bash
# 基础用法 - 从URL提取内容
wf https://example.com

# 从混合文本中提取URL（中英文）
wf "查看这篇文章 Check this article http://example.com/article"

# 快速模式 - 快速内容提取
wf fast https://example.com

# 完整模式 - 全面内容提取
wf full https://example.com

# 站点模式 - 爬取整个网站
wf site https://example.com

# 原始模式 - 获取原始HTML
wf raw https://example.com
```

### 功能特性

#### 🎯 智能URL提取
自动从混合语言文本中提取URL，支持微信文章、小红书等多种平台。

#### 🚀 多种爬取模式
- **单页模式**: 默认模式，用于单页内容提取
- **快速模式**: 快速提取，最少处理
- **完整模式**: 全面内容提取
- **站点模式**: 完整网站爬取
- **原始模式**: 不处理的原始HTML

#### 🌐 平台支持
- 微信公众号文章（过滤JavaScript代码）
- 小红书内容（支持图片提取）
- Hugo/Jekyll静态网站
- 通用网页

#### 📸 图片处理
```bash
# 默认 - 仅显示图片URL
wf https://example.com

# 下载图片
wf https://example.com --download-assets

# 兼容模式
WF_LEGACY_IMAGE_MODE=1 wf https://example.com
```

#### 📁 输出控制
```bash
# 自定义输出目录
wf https://example.com -o ./my-output

# 详细日志
wf https://example.com --verbose

# 原始HTML输出
wf https://example.com --raw
```

### 常用场景

#### 提取微信文章
```bash
wf "https://mp.weixin.qq.com/s/<article-id>"
```

#### 爬取文档网站
```bash
wf site https://example.com -o ./docs-backup
```

#### 快速内容检查
```bash
wf fast https://example.com/latest
```

#### 下载文章及图片
```bash
wf https://example.com/post --download-assets
```

#### 处理小红书链接
```bash
wf "不是办公70% 的人用 ChatGPT 居然是为了？ http://xhslink.com/<link-id> 复制后打开【小红书】"
```

### 高级用法

#### 环境变量
```bash
# 启用兼容图片模式
export WF_LEGACY_IMAGE_MODE=1

# 设置默认输出目录
export WF_OUTPUT_DIR=/path/to/output
```

#### 批量处理
```bash
# 从文件中批量处理多个URL
while IFS= read -r url; do
    wf "$url" -o ./batch-output
done < urls.txt
```

### 系统要求

- Python 3.7+
- BeautifulSoup4
- Requests
- 其他依赖见 requirements.txt

### 错误处理

工具包含：
- 失败请求的自动重试机制
- 智能内容提取降级策略
- 使用 `--verbose` 标志的全面错误日志

### 技术特性

- 支持带引号和不带引号的HTML链接
- 智能内容提取，支持现代网站架构
- 全面的错误处理和重试机制
- 性能优化的爬取算法

---

## Contributing | 贡献

Contributions are welcome! Please feel free to submit a Pull Request.

欢迎贡献！请随时提交Pull Request。

## License | 许可证

[Your License Here]

## Support | 支持

For issues and questions, please open an issue on GitHub.

如有问题和疑问，请在GitHub上开issue。