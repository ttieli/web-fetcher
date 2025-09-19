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
- **Site Mode**: Complete website crawling with 15-21% performance improvement
- **Raw Mode**: Original HTML without processing

#### 🏛️ Government Website Optimization
Enhanced content extraction for government and official websites:
- Ministry of Justice (司法部) - optimized content parsing
- Communist Party Member Network (12371.cn) - Priority 1.8 special handling
- Government portals with complex layouts
- Official news and announcement pages

#### 📋 List Page Intelligence
Smart page type detection and structured extraction:
- Automatic detection of list/index pages
- Structured extraction of article lists
- Navigation and pagination handling
- Mixed content type recognition

#### 🌐 Platform Support
- WeChat Articles (with JavaScript filtering)
- Xiaohongshu (with image extraction)
- Government websites (specialized parsing)
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

#### Government Website Content
```bash
# Ministry of Justice article
wf https://www.moj.gov.cn/pub/sfbgw/article

# Communist Party Member Network
wf https://www.12371.cn/special/article

# Government portal list page
wf https://www.gov.cn/news/list
```

#### List Page Extraction
```bash
# Extract structured list from index page
wf https://example.com/news/index.html

# Process navigation with multiple pages
wf full https://example.com/articles/page/1
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

### Technical Architecture

#### Page Type Detection
The system employs intelligent page type detection:
- Analyzes DOM structure and content patterns
- Identifies list pages vs. article pages
- Adapts extraction strategy based on page type
- Provides structured output for different content types

#### Performance Optimizations
- 15-21% improvement in full-site crawling speed
- Intelligent caching for repeated requests
- Parallel processing for multi-page sites
- Memory-efficient content streaming

### Known Issues

- **Page Type Misidentification**: Some complex layouts may be incorrectly classified. Use `--verbose` to debug.
- **Dynamic Content**: JavaScript-heavy sites may require additional processing time.
- **Government Sites**: Some government portals use non-standard encoding; the tool handles most cases automatically.
- **List Pagination**: Infinite scroll pages require special handling (use `full` mode).

### Error Handling

The tool includes:
- Automatic retry mechanism for failed requests
- Intelligent content extraction fallbacks
- Comprehensive error logging with `--verbose` flag
- Graceful degradation for unsupported content types

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
- **站点模式**: 完整网站爬取，性能提升15-21%
- **原始模式**: 不处理的原始HTML

#### 🏛️ 政府网站优化
针对政府和官方网站的内容提取增强：
- 司法部网站 - 优化内容解析
- 共产党员网（12371.cn）- Priority 1.8特殊处理
- 复杂布局的政府门户网站
- 官方新闻和公告页面

#### 📋 列表页面智能识别
智能页面类型检测和结构化提取：
- 自动检测列表/索引页面
- 结构化提取文章列表
- 导航和分页处理
- 混合内容类型识别

#### 🌐 平台支持
- 微信公众号文章（过滤JavaScript代码）
- 小红书内容（支持图片提取）
- 政府网站（专门化解析）
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

#### 政府网站内容提取
```bash
# 司法部文章
wf https://www.moj.gov.cn/pub/sfbgw/article

# 共产党员网专题
wf https://www.12371.cn/special/article

# 政府门户列表页
wf https://www.gov.cn/news/list
```

#### 列表页面提取
```bash
# 从索引页提取结构化列表
wf https://example.com/news/index.html

# 处理带分页的导航
wf full https://example.com/articles/page/1
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

### 技术架构

#### 页面类型检测
系统采用智能页面类型检测：
- 分析DOM结构和内容模式
- 识别列表页面与文章页面
- 根据页面类型调整提取策略
- 为不同内容类型提供结构化输出

#### 性能优化
- 全站爬取速度提升15-21%
- 智能缓存重复请求
- 多页面站点并行处理
- 内存高效的内容流式传输

### 已知问题

- **页面类型误判**: 某些复杂布局可能被错误分类。使用 `--verbose` 进行调试。
- **动态内容**: JavaScript密集型网站可能需要额外处理时间。
- **政府网站**: 某些政府门户使用非标准编码；工具自动处理大多数情况。
- **列表分页**: 无限滚动页面需要特殊处理（使用 `full` 模式）。

### 错误处理

工具包含：
- 失败请求的自动重试机制
- 智能内容提取降级策略
- 使用 `--verbose` 标志的全面错误日志
- 对不支持的内容类型进行优雅降级

### 技术特性

- 支持带引号和不带引号的HTML链接
- 智能内容提取，支持现代网站架构
- 全面的错误处理和重试机制
- 性能优化的爬取算法
- 专门针对中文内容的解析优化

---

## Recent Updates | 最新更新

### v2.1.0 (Latest)
- 🏛️ **Government Website Enhancement**: Fixed content extraction for Ministry of Justice and Communist Party Member Network
- 📋 **List Page Intelligence**: Added automatic page type detection for list/index pages
- 🎯 **12371.cn Optimization**: Special Priority 1.8 handling for Communist Party Member Network
- 🔗 **Smart URL Extraction**: Enhanced support for mixed Chinese/English text URL extraction
- ⚡ **Performance Boost**: 15-21% improvement in full-site crawling performance

### v2.0.0
- 🚀 Multiple crawling modes (fast, full, site, raw)
- 🌐 Platform-specific optimizations
- 📸 Enhanced image handling capabilities

---

## Contributing | 贡献

Contributions are welcome! Please feel free to submit a Pull Request.

欢迎贡献！请随时提交Pull Request。

## License | 许可证

[Your License Here]

## Support | 支持

For issues and questions, please open an issue on GitHub.

如有问题和疑问，请在GitHub上开issue。