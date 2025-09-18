# Web Fetcher - 智能网页采集与转换工具

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-orange)](https://github.com/webfetcher)
[![Code Lines](https://img.shields.io/badge/lines-1823-lightgrey)](webfetcher.py)

**一个高性能、单文件、零依赖的网页内容采集工具，支持多平台内容提取与智能解析**

</div>

## 📋 项目概述

Web Fetcher 是一个专业的网页内容采集工具，采用单文件架构设计，无需安装任何第三方依赖即可运行。它能够智能识别并解析多种主流网站的内容结构，将网页转换为结构化的 Markdown 文档，特别适合内容存档、知识管理、文档迁移等场景。

### 核心价值

- **极简部署**：单文件设计，无需安装配置，开箱即用
- **智能解析**：自动识别网站类型，选择最优解析策略
- **全站采集**：支持 BFS 算法递归采集整站内容
- **高可靠性**：内置重试机制、错误处理、内存保护
- **结构化输出**：生成规范的 Markdown 文档，支持 JSON 导出

## 🚀 主要功能特性

### 1. 多平台内容解析
- **社交媒体平台**
  - 微信公众号（mp.weixin.qq.com）：文章内容、作者信息、发布时间
  - 小红书（xiaohongshu.com）：笔记内容、图片画廊、用户信息
  - 大众点评（dianping.com）：商家信息、评分、营业时间、地址

- **文档框架支持**
  - Docusaurus：自动识别文档结构，支持分页聚合
  - MkDocs：智能提取技术文档，保留代码高亮
  - 通用网页：JSON-LD 结构化数据优先提取

### 2. 高级采集能力
- **全站爬取**：BFS 广度优先遍历，智能 URL 去重
- **分页聚合**：自动检测并跟踪文档分页导航
- **智能过滤**：自动排除二进制文件、API 接口、构建产物
- **礼貌采集**：可配置延迟，避免对目标服务器造成压力

### 3. 容错与优化
- **指数退避重试**：网络错误自动重试（最多 3 次）
- **内存保护**：单页面 10MB 限制，防止内存溢出
- **智能 UA 切换**：根据目标网站自动选择合适的 User-Agent
- **子目录感知**：正确处理 GitHub Pages 等子目录部署

### 4. 数据处理
- **资源下载**：可选下载图片等静态资源到本地
- **链接重写**：自动更新资源链接为本地相对路径
- **元数据提取**：保留发布时间、作者、描述等关键信息
- **HTML 快照**：可选保存原始 HTML 用于调试

## 🏗️ 技术架构

### 设计理念

Web Fetcher 采用**渐进式架构设计**（Progressive Architecture），核心原则包括：

1. **单文件自包含**：所有功能集成在一个 Python 文件中，降低部署复杂度
2. **零依赖原则**：仅使用 Python 标准库，可选 Playwright 渲染支持
3. **策略模式**：不同网站类型使用专门的解析器，易于扩展
4. **防御性编程**：全面的异常处理和边界检查

### 核心组件

```
webfetcher.py
├── URL 处理层
│   ├── normalize_url_for_dedup()  # URL 标准化去重
│   ├── resolve_url_with_context() # 智能 URL 解析
│   └── should_crawl_url()         # URL 过滤判断
│
├── 网络请求层
│   ├── fetch_html_with_retry()    # 带重试的 HTML 获取
│   ├── try_render()                # Playwright 动态渲染
│   └── calculate_backoff_delay()  # 指数退避延迟计算
│
├── 内容解析器
│   ├── wechat_to_markdown()       # 微信公众号解析器
│   ├── xhs_to_markdown()          # 小红书解析器
│   ├── dianping_to_markdown()     # 大众点评解析器
│   ├── docusaurus_to_markdown()   # Docusaurus 解析器
│   ├── mkdocs_to_markdown()       # MkDocs 解析器
│   └── generic_to_markdown()      # 通用解析器
│
├── 采集引擎
│   ├── crawl_site()               # BFS 全站采集
│   ├── process_pagination()       # 分页处理
│   └── extract_internal_links()   # 内部链接提取
│
└── 输出处理
    ├── rewrite_and_download_assets() # 资源本地化
    ├── aggregate_crawled_site()      # 多页聚合
    └── ensure_unique_path()          # 文件名去重
```

## 📦 安装和使用指南

### 系统要求

- Python 3.8 或更高版本
- 操作系统：Windows、macOS、Linux
- 可选：Playwright（用于 JavaScript 渲染）

### 快速开始

1. **基础使用** - 抓取单个网页
```bash
python3 webfetcher.py https://example.com
```

2. **指定输出目录**
```bash
python3 webfetcher.py https://example.com -o ./output
```

3. **查看详细日志**
```bash
python3 webfetcher.py https://example.com --verbose
```

### 高级用法

#### 全站采集
```bash
# 采集整个文档站点（最多 500 页，深度 5）
python3 webfetcher.py https://docs.example.com \
  --crawl-site \
  --max-pages 500 \
  --max-crawl-depth 5 \
  --crawl-delay 1.0
```

#### 多页文档聚合
```bash
# 自动跟踪文档的分页导航
python3 webfetcher.py https://docs.site.com/guide/intro \
  --follow-pagination
```

#### 资源本地化
```bash
# 下载所有图片到本地 assets 目录
python3 webfetcher.py https://article.site.com \
  --download-assets \
  --assets-root images
```

#### 动态渲染（需要 Playwright）
```bash
# 安装 Playwright
pip install playwright
playwright install chromium

# 使用动态渲染
python3 webfetcher.py https://spa-site.com --render always
```

#### 导出 JSON 格式
```bash
# 同时生成 Markdown 和 JSON
python3 webfetcher.py https://example.com --json
```

#### 保存 HTML 快照
```bash
# 保存原始 HTML 用于调试
python3 webfetcher.py https://example.com --save-html
```

## 📖 API 文档

### 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `url` | - | 目标 URL（必需） | - |
| `--outdir` | `-o` | 输出目录 | 当前目录 |
| `--render` | - | 渲染模式：auto/always/never | auto |
| `--timeout` | - | 网络超时（秒） | 60 |
| `--render-timeout` | - | 渲染超时（秒） | 90 |
| `--html` | - | 使用本地 HTML 文件 | - |
| `--download-assets` | - | 下载静态资源 | false |
| `--assets-root` | - | 资源保存目录名 | assets |
| `--save-html` | - | 保存 HTML 快照 | false |
| `--json` | - | 输出 JSON 格式 | false |
| `--verbose` | - | 详细日志输出 | false |
| `--follow-pagination` | - | 跟踪分页导航 | false |
| `--crawl-site` | - | 采集整个站点 | false |
| `--max-crawl-depth` | - | 最大采集深度 | 10 |
| `--max-pages` | - | 最大采集页面数 | 1000 |
| `--crawl-delay` | - | 采集请求延迟（秒） | 0.5 |

### 输出格式

#### Markdown 文档结构
```markdown
# 文章标题

- 标题: 文章标题
- 作者: 作者名称（如适用）
- 发布时间: YYYY-MM-DD HH:MM:SS
- 来源: [URL](URL)
- 抓取时间: YYYY-MM-DD HH:MM:SS

正文内容...

## 图片

![](image1.jpg)
![](image2.jpg)
```

#### JSON 数据结构
```json
{
  "url": "原始URL",
  "title": "文档标题",
  "date": "发布日期时间",
  "content": "Markdown内容",
  "images": ["图片URL列表"],
  "metadata": {
    "description": "描述",
    "author": "作者",
    "publish_time": "发布时间",
    "parser_used": "使用的解析器",
    "fetch_method": "获取方法",
    "scraped_at": "抓取时间"
  }
}
```

## ⚙️ 配置说明

### 内置常量配置

```python
# 分页深度限制
MAX_PAGINATION_DEPTH = 5

# 站点采集限制
MAX_CRAWL_DEPTH = 10      # 最大采集深度
MAX_CRAWL_PAGES = 1000    # 最大页面数量
DEFAULT_CRAWL_DELAY = 0.5 # 默认延迟（秒）

# 内存保护
MAX_PAGE_SIZE = 10 * 1024 * 1024  # 10MB

# 重试配置
MAX_RETRIES = 3           # 最大重试次数
BASE_DELAY = 1.0          # 基础延迟（秒）
MAX_JITTER = 0.1          # 随机抖动
```

### User-Agent 策略

工具会根据目标网站自动选择合适的 User-Agent：

- **微信公众号**：移动端微信 UA
- **小红书**：移动端浏览器 UA
- **大众点评**：移动端 Safari UA
- **其他网站**：桌面端 Chrome UA

## 📁 项目结构

```
Web_Fetcher/
├── README.md           # 项目文档
└── webfetcher.py      # 主程序（1823 行）
```

生成的文件结构：
```
output/
├── 2024-01-15-143022 - 文章标题.md  # Markdown 文档
├── 2024-01-15-143022 - 文章标题.json # JSON 数据（可选）
├── snapshot_example_20240115_143022.html # HTML 快照（可选）
└── assets/            # 静态资源（可选）
    └── 2024-01-15-143022 - 文章标题/
        ├── 01.jpg
        ├── 02.png
        └── ...
```

## 🔧 依赖说明

### 核心依赖（Python 标准库）

- `urllib`：网络请求处理
- `html.parser`：HTML 解析
- `json`：JSON 数据处理
- `re`：正则表达式
- `pathlib`：文件路径操作
- `datetime`：时间处理
- `argparse`：命令行参数
- `logging`：日志记录

### 可选依赖

- `playwright`：JavaScript 动态渲染支持（仅在需要时安装）

## ⚠️ 注意事项

### 使用限制

1. **采集频率**：请合理设置 `--crawl-delay`，避免对目标服务器造成压力
2. **页面数量**：全站采集时注意设置合理的 `--max-pages` 限制
3. **内存使用**：单页面限制 10MB，超大页面会被截断
4. **网络重试**：自动重试可能延长总体执行时间

### 最佳实践

1. **增量采集**：对于大型站点，建议分批次采集
2. **错误处理**：使用 `--verbose` 查看详细错误信息
3. **资源管理**：定期清理下载的静态资源
4. **备份原始数据**：使用 `--save-html` 保存原始 HTML

### 已知限制

- 不支持需要登录认证的页面
- 不支持 WebSocket 实时数据
- 不处理 Canvas 渲染的内容
- 视频内容仅保留链接，不下载

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request。在添加新的网站解析器时，请遵循现有的代码结构：

1. 在 `webfetcher.py` 中添加新的解析函数
2. 函数命名格式：`sitename_to_markdown()`
3. 返回格式：`(date_only, markdown_content, metadata)`
4. 在主函数中添加域名判断逻辑

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 🔗 相关链接

- [Python 官网](https://www.python.org/)
- [Playwright 文档](https://playwright.dev/python/)
- [Markdown 语法](https://www.markdownguide.org/)

---

<div align="center">

**简洁而不简单** - 1 个文件，1823 行代码，无限可能

*Web Fetcher - 让网页内容采集变得简单高效*

</div>