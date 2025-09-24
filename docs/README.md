# Web_Fetcher / 网页内容提取器

[English](#english) | [中文](#中文)

## English

A comprehensive web content extraction and processing tool that intelligently fetches, parses, and converts web content to clean Markdown format. Supports specialized parsing for popular platforms like WeChat, Xiaohongshu, and Dianping, with intelligent fallback to generic parsing for other sites.

## 中文

智能网页内容提取和处理工具，能够智能获取、解析并将网页内容转换为干净的Markdown格式。支持微信、小红书、大众点评等热门平台的专用解析，并为其他网站提供智能通用解析功能。

## Features and Capabilities / 功能特性

### Core Features / 核心功能
- **Multi-Method Content Fetching / 多方式内容获取**: Static HTTP requests with fallback to headless browser rendering (Playwright) / 静态HTTP请求，支持无头浏览器渲染(Playwright)回退
- **Intelligent Parser Selection / 智能解析器选择**: Automatic detection and specialized parsing for different content types / 自动检测不同内容类型并选择专用解析器
- **Site-Specific Adapters / 站点专用适配器**: Optimized parsers for WeChat articles, Xiaohongshu posts, Dianping reviews, and documentation sites / 针对微信文章、小红书帖子、大众点评评论和文档站点的优化解析器
- **Content Quality Control / 内容质量控制**: Multiple filtering levels to remove navigation, ads, and metadata / 多级过滤器移除导航、广告和元数据
- **Asset Management / 资源管理**: Optional image downloading and local asset management / 可选的图片下载和本地资源管理
- **Batch Processing / 批量处理**: Handle multiple URLs and entire site crawling / 处理多个URL和整站爬取
- **Format Options / 格式选项**: Clean Markdown output with optional JSON metadata / 干净的Markdown输出，可选JSON元数据

### Supported Content Types / 支持的内容类型
- **Social Media / 社交媒体**: WeChat articles (mp.weixin.qq.com), Xiaohongshu posts, Dianping reviews / 微信文章、小红书帖子、大众点评评论
- **Documentation / 文档**: MkDocs, Docusaurus, and generic documentation sites / MkDocs、Docusaurus和通用文档站点
- **Generic Web Pages / 通用网页**: Blog posts, news articles, and standard web content / 博客文章、新闻报道和标准网页内容
- **Binary Files / 二进制文件**: Direct download of PDFs, images, and other file types / 直接下载PDF、图片和其他文件类型
- **List Pages / 列表页面**: Automatic detection and processing of index/listing pages / 自动检测和处理索引/列表页面

### Processing Capabilities / 处理能力
- Smart encoding detection and handling / 智能编码检测和处理
- Multi-page document aggregation (pagination support) / 多页文档聚合（分页支持）
- Content structure analysis and type detection / 内容结构分析和类型检测
- Configurable content filtering (none/safe/moderate/aggressive) / 可配置内容过滤（无/安全/适中/激进）
- Performance metrics and detailed logging / 性能指标和详细日志

## Installation and Setup / 安装和设置

### Prerequisites / 前置要求
- Python 3.7+ / Python 3.7以上版本
- Optional: Playwright for JavaScript-heavy sites / 可选：用于JavaScript密集型站点的Playwright

### Basic Installation / 基础安装
```bash
# Clone the repository / 克隆仓库
git clone <repository-url>
cd Web_Fetcher

# Install Python dependencies (if any additional packages needed)
# 安装Python依赖（如需要额外包）
# The core tool uses only Python standard library
# 核心工具仅使用Python标准库

# Optional: Install Playwright for enhanced JavaScript support
# 可选：安装Playwright以增强JavaScript支持
pip install playwright
playwright install chromium
```

### Quick Setup with wf.py / 使用wf.py快速设置
The `wf.py` script provides a convenient wrapper with output directory management:
`wf.py`脚本提供了便捷的包装器，支持输出目录管理：

```bash
# Make executable / 设置可执行权限
chmod +x wf.py

# Set default output directory (optional) / 设置默认输出目录（可选）
export WF_OUTPUT_DIR="./output"
```

## Usage Examples / 使用示例

### Basic URL Extraction / 基础URL提取
```bash
# Extract single article / 提取单篇文章
python webfetcher.py "https://example.com/article"

# Use wf wrapper with output directory / 使用wf包装器指定输出目录
./wf.py "https://example.com/article" ./output/

# Extract with verbose logging / 启用详细日志提取
python webfetcher.py "https://example.com/article" --verbose
```

### Platform-Specific Examples / 平台特定示例
```bash
# WeChat article / 微信文章
python webfetcher.py "https://mp.weixin.qq.com/s/article-id"

# Xiaohongshu post (with rendering) / 小红书帖子（启用渲染）
python webfetcher.py "https://xiaohongshu.com/discovery/item/post-id" --render always

# Documentation site / 文档站点
python webfetcher.py "https://docs.example.com/guide" --follow-pagination
```

### Advanced Processing Options / 高级处理选项
```bash
# Raw content preservation / 原始内容保存
python webfetcher.py "https://example.com" --raw

# Custom filtering level / 自定义过滤级别
python webfetcher.py "https://example.com" --filter aggressive

# Download assets locally / 本地下载资源
python webfetcher.py "https://example.com" --download-assets

# Save processing snapshot / 保存处理快照
python webfetcher.py "https://example.com" --save-html --json
```

### Batch and Site Processing / 批量和站点处理
```bash
# Crawl entire site / 爬取整个站点
python webfetcher.py "https://docs.example.com" --crawl-site --max-pages 100

# Batch processing with custom output / 自定义输出的批量处理
./wf.py batch_urls.txt ./output/ --filter moderate
```

## Detailed Process Flow / 详细处理流程

### 1. URL Input and Validation / URL输入和验证
```
URL Input → URL Parsing → Host Detection → User Agent Selection
URL输入 → URL解析 → 主机检测 → 用户代理选择
```
- Validates URL format and accessibility / 验证URL格式和可访问性
- Extracts hostname for platform-specific handling / 提取主机名进行平台特定处理
- Selects appropriate User-Agent string based on target site / 根据目标站点选择合适的User-Agent字符串

### 2. Content Fetching Pipeline / 内容获取管道
```
Static Fetch (urllib) → [SSL Issues?] → Curl Fallback → [JS Required?] → Playwright Rendering
静态获取(urllib) → [SSL问题?] → Curl回退 → [需要JS?] → Playwright渲染
```

#### Primary Method: Static HTTP / 主要方式：静态HTTP
- Uses `urllib.request` with SSL context / 使用带SSL上下文的`urllib.request`
- Headers optimized for target platform / 针对目标平台优化的请求头
- Configurable timeout (default: 60s) / 可配置超时时间（默认：60秒）

#### Fallback Method: Curl / 回退方式：Curl
- Activated on SSL/certificate issues / 在SSL/证书问题时激活
- Bypasses Python SSL limitations / 绕过Python SSL限制
- Maintains same header configuration / 保持相同的请求头配置

#### Enhanced Method: Playwright Rendering / 增强方式：Playwright渲染
- For JavaScript-heavy sites (Xiaohongshu, Dianping) / 用于JavaScript密集型站点（小红书、大众点评）
- Configurable rendering timeout (default: 90s) / 可配置渲染超时时间（默认：90秒）
- Full browser environment with dynamic content / 完整浏览器环境支持动态内容

### 3. Content Type Detection
```
HTML Analysis → Page Type Detection → Parser Selection
```

#### Page Type Classification
The system uses intelligent analysis to determine content type:

```python
# Detection Algorithm
Link Density Analysis → Structure Recognition → Content Pattern Matching
```

**Detection Criteria:**
- **Article Pages**: Low link density, structured content, clear headings
- **List/Index Pages**: High link density, repeated patterns, navigation elements
- **Documentation**: Specific CSS classes, navigation structures
- **Social Media**: Platform-specific indicators and metadata

### 4. Parser Selection Logic
```
Host-Based Detection → Content Pattern Analysis → Parser Assignment
```

#### Selection Hierarchy:
1. **User Override**: `--raw` flag forces raw parser
2. **Host-Based**: Direct mapping for known platforms
3. **Content Analysis**: Pattern matching for documentation types
4. **Generic Fallback**: Default HTML-to-Markdown conversion

#### Supported Parsers:
- **WeChat Parser**: Optimized for mp.weixin.qq.com articles
- **Xiaohongshu Parser**: Handles XHS posts and image galleries
- **Dianping Parser**: Processes reviews and business listings
- **Docusaurus Parser**: Documentation framework support
- **MkDocs Parser**: Material theme and standard MkDocs
- **Generic Parser**: Universal HTML processing with smart content detection
- **Raw Parser**: Complete content preservation

### 5. Content Processing Pipeline
```
HTML Input → Content Filtering → Structure Analysis → Markdown Conversion → Asset Processing
```

#### Content Filtering Levels:
- **None**: No filtering, preserve all content
- **Safe** (default): Remove scripts, ads, tracking elements
- **Moderate**: Additional removal of navigation and sidebar content
- **Aggressive**: Strip metadata, social widgets, and promotional content

#### Structure Analysis:
- Main content identification using multiple heuristics
- Header hierarchy detection and preservation
- List and table structure recognition
- Image and media element processing

### 6. Output Generation
```
Markdown Generation → Asset Management → Metadata Extraction → File Naming → Storage
```

#### File Naming Convention:
```
YYYY-MM-DD - [Article Title].md
```

#### Output Formats:
- **Primary**: Clean Markdown with preserved formatting
- **Optional**: JSON metadata with processing details
- **Assets**: Local image downloads with rewritten links

## Processing Pipeline Diagram

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│  URL Input  │───▶│ URL Validate │───▶│  Host Analysis  │
└─────────────┘    └──────────────┘    └─────────────────┘
                                                │
                                                ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ User Agent  │◄───│Content Fetch │◄───│ Fetch Strategy  │
│ Selection   │    │   Pipeline   │    │   Selection     │
└─────────────┘    └──────────────┘    └─────────────────┘
                           │
                           ▼
            ┌─────────────────────────────────┐
            │        Fetch Method             │
            │  ┌─────────┐  ┌──────────────┐  │
            │  │ Static  │  │ Playwright   │  │
            │  │ urllib  │  │ Rendering    │  │
            │  └─────────┘  └──────────────┘  │
            │       │             │          │
            │       ▼             ▼          │
            │  ┌─────────┐  ┌──────────────┐  │
            │  │  Curl   │  │   Enhanced   │  │
            │  │Fallback │  │   Content    │  │
            │  └─────────┘  └──────────────┘  │
            └─────────────────────────────────┘
                           │
                           ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│Page Type    │◄───│Content Type  │───▶│ Parser Selection│
│Detection    │    │  Analysis    │    │    Logic        │
└─────────────┘    └──────────────┘    └─────────────────┘
       │                                        │
       ▼                                        ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│Article Page │    │ List Page    │    │Specialized Parser│
│Processing   │    │ Processing   │    │   (WX/XHS/etc)  │
└─────────────┘    └──────────────┘    └─────────────────┘
       │                   │                    │
       └───────────────────┼────────────────────┘
                           ▼
            ┌─────────────────────────────────┐
            │      Content Processing         │
            │  ┌─────────┐  ┌──────────────┐  │
            │  │Content  │  │ Structure    │  │
            │  │Filter   │  │ Analysis     │  │
            │  └─────────┘  └──────────────┘  │
            │       │             │          │
            │       ▼             ▼          │
            │  ┌─────────┐  ┌──────────────┐  │
            │  │Markdown │  │Asset         │  │
            │  │Convert  │  │Management    │  │
            │  └─────────┘  └──────────────┘  │
            └─────────────────────────────────┘
                           │
                           ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│File Naming  │◄───│Output        │───▶│ Storage &       │
│Convention   │    │Generation    │    │ Verification    │
└─────────────┘    └──────────────┘    └─────────────────┘
```

### Decision Points and Branching Logic

#### Mode-Aware Detection
The system operates differently based on processing mode:

**Single URL Mode:**
- Focuses on content quality and completeness
- Applies full filtering and structure analysis
- Optimizes for reading experience

**Crawl Mode:**
- Prioritizes processing speed and consistency
- Uses batch-optimized parser detection
- Maintains site-wide formatting consistency

#### JavaScript Detection Logic
```python
if render_mode == 'always':
    use_playwright()
elif render_mode == 'auto':
    if is_js_heavy_site(hostname):  # XHS, Dianping
        use_playwright()
    else:
        use_static_fetch()
else:  # render_mode == 'never'
    use_static_fetch()
```

## Advanced Features

### Batch Processing
```bash
# Process multiple URLs from file
./wf.py urls.txt ./output/ --filter moderate

# Each URL processed independently
# Automatic retry logic for failed requests
# Consolidated reporting and logging
```

### Site Crawling
```bash
# Comprehensive site crawling
python webfetcher.py "https://docs.example.com" --crawl-site \
    --max-depth 5 --max-pages 200 --crawl-delay 1.0

# Intelligent content aggregation
# Duplicate detection and filtering
# Breadth-first traversal with depth limits
```

### Content Filtering Levels

#### Safe (Default)
- Removes: Scripts, ads, tracking pixels, analytics
- Preserves: Main content, navigation, metadata

#### Moderate
- Removes: All safe items + navigation, sidebars, related content
- Preserves: Main content, essential metadata

#### Aggressive
- Removes: All moderate items + social widgets, comments, promotional content
- Preserves: Core article content only

### Binary File Support
```bash
# Automatic detection and download
python webfetcher.py "https://example.com/document.pdf"

# Supported formats: PDF, images, archives, documents
# Preserves original filename and metadata
# Handles large file downloads efficiently
```

## Technical Architecture

### Core Components

#### webfetcher.py
**Primary Module** - Complete web fetching and processing system
- **Size**: ~5000+ lines of specialized parsing logic
- **Responsibilities**:
  - HTTP client with fallback mechanisms
  - Platform-specific parsers (WeChat, Xiaohongshu, etc.)
  - Content filtering and structure analysis
  - Markdown generation and asset management
  - Site crawling and batch processing

#### wf.py
**Convenience Wrapper** - Simplified command-line interface
- **Size**: ~200 lines of workflow automation
- **Responsibilities**:
  - Output directory management and defaults
  - Environment variable integration
  - User-friendly argument parsing
  - Batch file processing workflows

### Supported Sites and Parsers

#### Social Media Platforms
- **WeChat (mp.weixin.qq.com)**: Article extraction with media handling
- **Xiaohongshu**: Post content with image gallery support
- **Dianping**: Review and business information extraction

#### Documentation Frameworks
- **Docusaurus**: Modern documentation with theme support
- **MkDocs**: Material theme and standard configurations
- **Generic Docs**: Automatic detection of documentation patterns

#### Content Management Systems
- **WordPress**: Standard blog and CMS content
- **Ghost**: Modern publishing platform
- **Medium**: Article extraction with formatting preservation

### Performance Optimizations

#### Content Processing
- **Parallel Processing**: Concurrent handling of assets and content
- **Memory Efficiency**: Streaming processing for large documents
- **Cache Management**: Intelligent caching of repeated requests

#### Network Operations
- **Connection Pooling**: Reuse connections for batch operations
- **Rate Limiting**: Configurable delays to respect server limits
- **Retry Logic**: Exponential backoff for failed requests

## Command-Line Reference / 命令行参考

### Core Arguments / 核心参数
```bash
python webfetcher.py <URL> [OPTIONS]
```

| Option / 选项 | Description / 描述 | Default / 默认值 |
|---------------|-------------------|------------------|
| `--outdir, -o` | Output directory / 输出目录 | `.` |
| `--render` | Rendering mode: auto/always/never / 渲染模式：自动/总是/从不 | `auto` |
| `--timeout` | Network timeout (seconds) / 网络超时（秒） | `60` |
| `--render-timeout` | Playwright timeout (seconds) / Playwright超时（秒） | `90` |

### Content Control / 内容控制
| Option / 选项 | Description / 描述 | Default / 默认值 |
|---------------|-------------------|------------------|
| `--filter` | Filtering level: none/safe/moderate/aggressive / 过滤级别：无/安全/适中/激进 | `safe` |
| `--raw` | Use raw parser (no filtering) / 使用原始解析器（无过滤） | `false` |
| `--follow-pagination` | Process multi-page documents / 处理多页文档 | `false` |

### Asset Management / 资源管理
| Option / 选项 | Description / 描述 | Default / 默认值 |
|---------------|-------------------|------------------|
| `--download-assets` | Download images locally / 本地下载图片 | `false` |
| `--assets-root` | Assets directory name / 资源目录名称 | `assets` |

### Output Options / 输出选项
| Option / 选项 | Description / 描述 | Default / 默认值 |
|---------------|-------------------|------------------|
| `--json` | Generate JSON metadata / 生成JSON元数据 | `false` |
| `--save-html` | Save HTML snapshot / 保存HTML快照 | `false` |
| `--verbose` | Enable detailed logging / 启用详细日志 | `false` |

### Crawling Options / 爬取选项
| Option / 选项 | Description / 描述 | Default / 默认值 |
|---------------|-------------------|------------------|
| `--crawl-site` | Enable site crawling / 启用站点爬取 | `false` |
| `--max-crawl-depth` | Maximum crawl depth / 最大爬取深度 | `10` |
| `--max-pages` | Maximum pages to crawl / 最大爬取页面数 | `1000` |
| `--crawl-delay` | Delay between requests (seconds) / 请求间延迟（秒） | `0.5` |

## Use Cases and Examples / 使用场景和示例

### Single Article Extraction / 单篇文章提取
```bash
# Basic article extraction / 基础文章提取
python webfetcher.py "https://blog.example.com/post"

# With asset download and JSON metadata / 下载资源并生成JSON元数据
python webfetcher.py "https://blog.example.com/post" \
    --download-assets --json --verbose
```

### Documentation Processing / 文档处理
```bash
# MkDocs documentation with pagination / 带分页的MkDocs文档
python webfetcher.py "https://docs.example.com/guide/" \
    --follow-pagination --filter moderate

# Complete documentation site crawl / 完整文档站点爬取
python webfetcher.py "https://docs.example.com" \
    --crawl-site --max-depth 3 --max-pages 50
```

### Social Media Content / 社交媒体内容
```bash
# WeChat article / 微信文章
python webfetcher.py "https://mp.weixin.qq.com/s/article-id" \
    --download-assets

# Xiaohongshu post with forced rendering / 强制渲染的小红书帖子
python webfetcher.py "https://xiaohongshu.com/discovery/item/post-id" \
    --render always --filter safe
```

### Batch Processing Workflow / 批量处理工作流
```bash
# Create URL list file / 创建URL列表文件
echo "https://example1.com" > urls.txt
echo "https://example2.com" >> urls.txt

# Process batch with wf wrapper / 使用wf包装器批量处理
./wf.py urls.txt ./output/ --filter moderate --json

# Results in organized output directory structure / 结果按组织结构存储在输出目录
```

### Content Quality Control / 内容质量控制
```bash
# Maximum content preservation / 最大内容保留
python webfetcher.py "https://example.com" --raw

# Clean article-focused output / 清洁的文章导向输出
python webfetcher.py "https://example.com" --filter aggressive

# Balanced processing with assets / 平衡处理并下载资源
python webfetcher.py "https://example.com" \
    --filter safe --download-assets
```

## Performance Metrics and Monitoring / 性能指标和监控

The system provides comprehensive metrics for each processing operation:
系统为每个处理操作提供全面的指标：

### Fetch Metrics / 获取指标
- **Method Used / 使用方法**: urllib/curl/playwright/local_file
- **Fallback Status / 回退状态**: Whether fallback methods were required / 是否需要回退方法
- **Timing Data / 时间数据**: Fetch duration, rendering duration / 获取时长、渲染时长
- **Success Rates / 成功率**: Attempt counts and final status / 尝试次数和最终状态

### Content Metrics / 内容指标
- **Parser Selection / 解析器选择**: Which parser was chosen and why / 选择了哪个解析器及原因
- **Content Quality / 内容质量**: Filtering statistics and content preservation / 过滤统计和内容保留
- **Asset Processing / 资源处理**: Download counts and success rates / 下载次数和成功率

### Example Metrics Output / 示例指标输出
```
Fetched via: urllib | Duration: 2.34s | Parser: Generic
获取方式：urllib | 时长：2.34秒 | 解析器：通用
Content: 2,456 words | Images: 12 processed | Filter: safe
内容：2,456词 | 图片：已处理12张 | 过滤器：安全
```

This comprehensive tool provides robust, intelligent web content extraction with extensive customization options for various use cases, from single article processing to complete site documentation extraction.

这个综合工具提供强大、智能的网页内容提取功能，具有广泛的自定义选项，适用于从单篇文章处理到完整站点文档提取的各种使用场景。