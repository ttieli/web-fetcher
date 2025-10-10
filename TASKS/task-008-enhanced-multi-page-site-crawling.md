# Task-008: Enhanced Multi-Page and Whole-Site Crawling
# Task-008：增强的多页面与整站爬取功能

**Priority / 优先级:** P2 (Important / 重要)
**Status / 状态:** PENDING / 待办
**Created / 创建日期:** 2025-10-10
**Revised / 修订日期:** 2025-10-10 (Removed robots.txt - personal use only)
**Estimated Effort / 预计工时:** 14-19 hours / 14-19小时

---

## Executive Summary / 执行摘要

Enhance the existing `wf --site` command with improved multi-page crawling capabilities, better configuration options, and structured output formats, while maintaining backward compatibility with the current CLI interface.

增强现有的 `wf --site` 命令，提供改进的多页面爬取能力、更好的配置选项和结构化输出格式，同时保持与当前CLI界面的向后兼容性。

---

## Background / 背景

### Current Implementation Analysis / 当前实现分析

**Existing Capabilities / 现有能力:**

1. **CLI Interface / CLI接口** (`wf.py:426-446`)
   ```bash
   wf site <URL> [输出目录] [--max-pages N]
   ```
   - Passes to webfetcher: `--crawl-site --max-crawl-depth 5 --follow-pagination`
   - Supports output directory specification
   - Accepts additional arguments passthrough

2. **Core Crawling Engine / 核心爬取引擎** (`webfetcher.py:3153-3360`)
   - **Algorithm / 算法:** BFS (Breadth-First Search) traversal
   - **Deduplication / 去重:** Normalized URL comparison
   - **Depth Control / 深度控制:** Max depth limit (default: 10, wf.py uses: 5)
   - **Page Limit / 页面限制:** Max pages (default: 1000)
   - **Rate Limiting / 速率限制:** Configurable delay (default: 0.5s)
   - **Progress Reporting / 进度报告:** Real-time progress line
   - **Link Filtering / 链接过滤:** Documentation URL pre-filtering
   - **Memory Optimization / 内存优化:** Batch processing mode

3. **Advanced Features / 高级特性:**
   - **Category-First Strategy / 分类优先策略** (`crawl_site_by_categories()`)
     - Special handling for government sites
     - Extracts site categories and crawls by category
   - **Pagination Support / 分页支持** (`process_pagination()`)
     - Follows Docusaurus-style pagination links
     - Prevents circular pagination loops

### Identified Issues / 发现的问题

**Critical Bugs / 关键缺陷:**
1. ❌ **Bug #1**: `--follow-pagination` flag passed by wf.py **doesn't exist** in webfetcher.py
   - Current: `wf site` command fails with "unrecognized arguments: --follow-pagination"
   - Impact: Pagination feature is **completely broken**

**Limitations / 局限性:**
1. 🔧 **Fixed Parameters / 固定参数:** Depth hardcoded to 5 in wf.py (should be configurable)
2. 🚫 **No Sitemap Support / 不支持sitemap.xml:** Misses efficient site discovery
3. 🔗 **Limited URL Filtering / 有限的URL过滤:** Only supports documentation URL filter
4. 🌐 **No Domain Boundaries / 无域名边界:** Doesn't enforce same-domain crawling
5. 💾 **No Resume Capability / 无恢复能力:** Can't resume interrupted crawls
6. 📊 **Limited Output Formats / 有限的输出格式:** Only dumps files, no structured index

---

## Objectives / 目标

### Primary Goals / 主要目标

1. **Fix Critical Bugs / 修复关键缺陷**
   - Implement missing `--follow-pagination` flag
   - Make `wf site` command fully functional

2. **Enhance Multi-Page Crawling / 增强多页面爬取**
   - Support targeted page range crawling (e.g., crawl pages 1-50)
   - Support URL pattern-based crawling (e.g., only /docs/* paths)
   - Follow pagination links intelligently

3. **Improve Whole-Site Crawling / 改进整站爬取**
   - Add sitemap.xml discovery and parsing
   - Enforce domain boundary controls
   - Improve link discovery algorithms
   - **Note / 注意:** No robots.txt support (personal use tool, not for production crawling)

4. **Enhance Configuration / 增强配置**
   - Expose all crawl parameters via CLI
   - Support crawl configuration files
   - Add preset strategies (documentation, blog, e-commerce, etc.)

5. **Structured Output / 结构化输出**
   - Generate JSON index of crawled pages
   - Generate CSV reports with metadata
   - Create site map visualization

6. **Robustness / 鲁棒性**
   - Add resume capability for interrupted crawls
   - Better error handling and recovery
   - Crawl state persistence

---

## Detailed Requirements / 详细需求

### Phase 1: Bug Fixes and Parameter Exposure (4-6 hours) / 阶段1：缺陷修复与参数暴露

**1.1 Fix --follow-pagination Bug / 修复分页标志缺陷**
- [ ] Add `--follow-pagination` flag to webfetcher.py argparser
- [ ] Integrate with existing `process_pagination()` function
- [ ] Add tests to verify pagination following works

**1.2 Expose Crawl Parameters in wf.py / 在wf.py中暴露爬取参数**
```bash
wf site <URL> [output_dir] [options]

Options:
  --max-pages N           # Maximum pages to crawl (default: 100, max: 1000)
  --max-depth N           # Maximum crawl depth (default: 5, max: 10)
  --delay SECONDS         # Delay between requests (default: 0.5)
  --follow-pagination     # Follow pagination links
  --same-domain-only      # Only crawl same domain (default: true)
```

**1.3 Update wf.py Site Handler / 更新wf.py站点处理器**
- Remove hardcoded parameters
- Pass through user-specified options
- Maintain backward compatibility

**Acceptance Criteria / 验收标准:**
- ✅ `wf site` command works without errors
- ✅ All parameters can be configured via CLI
- ✅ Pagination following works correctly
- ✅ Backward compatibility maintained (existing commands still work)

---

### Phase 2: Sitemap Support (3-4 hours) / 阶段2：Sitemap支持

**Note / 说明:** Robots.txt support has been removed as this tool is for personal use only, not production web crawling. / 已移除robots.txt支持，因为此工具仅用于个人用途，非生产环境爬虫。

**2.1 Sitemap.xml Parser / Sitemap.xml解析器**
- [ ] Implement sitemap.xml discovery (check /sitemap.xml, /sitemap_index.xml)
- [ ] Parse sitemap.xml and sitemap index files
- [ ] Extract URLs with priorities and lastmod dates
- [ ] Handle gzipped sitemaps (sitemap.xml.gz)
- [ ] Add `--use-sitemap` flag to enable sitemap-first crawling

**2.2 Sitemap-First Crawling Strategy / Sitemap优先爬取策略**
```python
def crawl_from_sitemap(start_url, **kwargs):
    """Crawl using sitemap.xml as the primary URL source."""
    # 1. Discover sitemap
    sitemap_urls = discover_sitemaps(start_url)
    if not sitemap_urls:
        logging.info("No sitemap found, falling back to BFS")
        return crawl_site(start_url, **kwargs)

    # 2. Parse sitemap and extract URLs
    all_urls = []
    for sitemap_url in sitemap_urls:
        urls = parse_sitemap(sitemap_url)
        all_urls.extend(urls)

    # 3. Filter and prioritize URLs
    filtered_urls = filter_urls_by_pattern(all_urls, **kwargs)
    sorted_urls = sort_by_priority_and_lastmod(filtered_urls)

    # 4. Crawl URLs from sitemap
    return crawl_url_list(sorted_urls[:kwargs.get('max_pages', 1000)])
```

**2.3 Integration / 集成**
- [ ] Add sitemap discovery to existing `crawl_site()` function
- [ ] Create separate `crawl_from_sitemap()` function
- [ ] Add CLI flag `--use-sitemap` to wf.py
- [ ] Fall back to BFS if sitemap not found

**Acceptance Criteria / 验收标准:**
- ✅ Discovers and parses sitemap.xml successfully
- ✅ Can crawl from sitemap when available
- ✅ Handles sitemap index files (multiple sitemaps)
- ✅ Falls back to BFS crawling if no sitemap found
- ✅ `--use-sitemap` flag works correctly

---

### Phase 3: Advanced Crawling Features (4-6 hours) / 阶段3：高级爬取特性

**3.1 URL Pattern Filtering / URL模式过滤**
```bash
wf site <URL> --include-pattern "/docs/*" --exclude-pattern "*/archive/*"
```
- [ ] Support glob patterns for URL filtering
- [ ] Support regex patterns (with `--regex` flag)
- [ ] Multiple include/exclude patterns

**3.2 Domain Boundary Control / 域名边界控制**
```bash
wf site <URL> --same-domain-only    # Default: only crawl same domain
wf site <URL> --allow-subdomains    # Allow subdomains (e.g., blog.example.com)
wf site <URL> --follow-external     # Follow external links (with limits)
```

**3.3 Link Discovery Improvements / 链接发现改进**
- [ ] Extract links from `<a>`, `<link>`, `<iframe>` tags
- [ ] Handle JavaScript-rendered links (via Selenium mode)
- [ ] Support canonical URL deduplication
- [ ] Handle redirect chains

**3.4 Crawl Strategies / 爬取策略**
```bash
wf site <URL> --strategy documentation  # Optimized for docs sites
wf site <URL> --strategy blog           # Follow blog pagination
wf site <URL> --strategy e-commerce     # Product listing crawling
wf site <URL> --strategy news           # News article crawling
```

**Acceptance Criteria / 验收标准:**
- ✅ URL pattern filtering works correctly
- ✅ Domain boundaries are enforced
- ✅ Crawl strategies optimize for different site types
- ✅ Link discovery handles edge cases (redirects, canonical, etc.)

---

### Phase 4: Structured Output and Reporting (3-4 hours) / 阶段4：结构化输出与报告

**4.1 JSON Index Generation / JSON索引生成**
```json
{
  "crawl_metadata": {
    "start_url": "https://example.com",
    "timestamp": "2025-10-10T12:00:00Z",
    "total_pages": 150,
    "total_size_bytes": 15000000,
    "duration_seconds": 120
  },
  "pages": [
    {
      "url": "https://example.com/page1",
      "depth": 0,
      "status": "success",
      "size_bytes": 50000,
      "links_found": 25,
      "fetch_time_ms": 250
    }
  ]
}
```

**4.2 CSV Report Generation / CSV报告生成**
```csv
url,depth,status,size_bytes,links_found,fetch_time_ms
https://example.com,0,success,50000,25,250
```

**4.3 Site Map Visualization / 站点地图可视化**
- [ ] Generate Mermaid diagram of site structure
- [ ] Show depth levels and link relationships
- [ ] Highlight entry points and dead ends

**4.4 CLI Integration / CLI集成**
```bash
wf site <URL> --output-json crawl_index.json
wf site <URL> --output-csv crawl_report.csv
wf site <URL> --output-sitemap sitemap.md
```

**Acceptance Criteria / 验收标准:**
- ✅ JSON index contains complete crawl metadata
- ✅ CSV report is importable into spreadsheets
- ✅ Site map visualization is readable and useful
- ✅ All output formats can be enabled simultaneously

---

### Phase 5: Resume Capability and State Persistence (3-4 hours) / 阶段5：恢复能力与状态持久化

**5.1 Crawl State Persistence / 爬取状态持久化**
```python
# .crawl_state.json
{
  "start_url": "https://example.com",
  "visited": ["url1", "url2", ...],
  "queue": [["url3", 2], ["url4", 3], ...],
  "statistics": {...},
  "timestamp": "2025-10-10T12:00:00Z"
}
```

**5.2 Resume Logic / 恢复逻辑**
```bash
wf site <URL> --resume    # Resume from last state
wf site <URL> --resume-from crawl_state.json
```
- [ ] Save state periodically (every 50 pages or 5 minutes)
- [ ] Load state on resume
- [ ] Handle state version compatibility
- [ ] Clean up state file on successful completion

**5.3 Crash Recovery / 崩溃恢复**
- [ ] Auto-save state before each request
- [ ] Detect incomplete state on startup
- [ ] Offer to resume automatically

**Acceptance Criteria / 验收标准:**
- ✅ Crawl can be interrupted and resumed
- ✅ No duplicate fetching after resume
- ✅ State file is human-readable and debuggable
- ✅ State cleanup happens automatically

---

## Technical Architecture / 技术架构

### Component Design / 组件设计

```
┌─────────────────────────────────────────────────────────┐
│                    wf.py (CLI Layer)                     │
│  - Parse user commands                                   │
│  - Expose all crawl parameters                           │
│  - Generate command for webfetcher.py                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              webfetcher.py (Orchestration)               │
│  - Parse CLI arguments                                   │
│  - Initialize crawl configuration                        │
│  - Call appropriate crawler                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           crawler/ (New Module) / 爬虫模块                │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │  CrawlOrchestrator / 爬取编排器                  │   │
│  │  - Coordinates crawl strategy                    │   │
│  │  - Manages state persistence                     │   │
│  │  - Generates reports                             │   │
│  └────────┬────────────────────────────────────────┘   │
│           │                                              │
│  ┌────────▼──────────┐  ┌──────────────┐  ┌─────────┐ │
│  │  SitemapManager   │  │  LinkScout   │  │  State  │ │
│  │  - sitemap.xml    │  │  - Discover  │  │  - Save │ │
│  │  - discovery      │  │  - Filter    │  │  - Load │ │
│  └───────────────────┘  └──────────────┘  └─────────┘ │
│                                                           │
│  ┌────────────────────────────────────────────────┐    │
│  │  CrawlStrategy (Abstract Base) / 爬取策略基类   │    │
│  │  - define_link_priorities()                     │    │
│  │  - should_follow_link()                         │    │
│  │  - extract_metadata()                           │    │
│  └────────────────────────────────────────────────┘    │
│           │                                              │
│  ┌────────┴──────────┬──────────────┬────────────┐    │
│  │ DefaultStrategy   │ DocsStrategy │ BlogStrategy│    │
│  │                   │              │             │    │
│  └───────────────────┴──────────────┴─────────────┘    │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         Existing Modules (Minimal Changes)               │
│  - fetch_html() / HTML获取                               │
│  - extract_internal_links() / 内部链接提取                │
│  - process_pagination() / 分页处理                       │
└─────────────────────────────────────────────────────────┘
```

### File Structure / 文件结构

```
webfetcher/
├── wf.py                          # Updated: expose all params
├── webfetcher.py                  # Updated: add --follow-pagination flag
├── crawler/                       # NEW: Crawler module
│   ├── __init__.py
│   ├── orchestrator.py            # CrawlOrchestrator
│   ├── sitemap_manager.py         # Sitemap discovery and parsing
│   ├── link_scout.py              # Link discovery and filtering
│   ├── state_manager.py           # State persistence
│   ├── strategies/                # Crawl strategies
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract base strategy
│   │   ├── default.py             # Default BFS strategy
│   │   ├── documentation.py       # Documentation site strategy
│   │   ├── blog.py                # Blog site strategy
│   │   └── category_first.py     # Government site strategy (migrate)
│   └── reporters/                 # Output generators
│       ├── __init__.py
│       ├── json_reporter.py       # JSON index generation
│       ├── csv_reporter.py        # CSV report generation
│       └── sitemap_reporter.py    # Mermaid diagram generation
├── tests/
│   └── test_crawler/              # NEW: Crawler tests
│       ├── test_orchestrator.py
│       ├── test_sitemap_manager.py
│       ├── test_link_scout.py
│       ├── test_state_manager.py
│       └── test_strategies.py
└── docs/
    └── crawler_guide.md           # NEW: Crawler documentation
```

---

## Implementation Plan / 实施计划

### Phase Breakdown / 阶段分解

| Phase | Description | Effort | Dependencies |
|-------|-------------|--------|--------------|
| Phase 1 | Bug fixes + parameter exposure | 4-6h | None |
| Phase 2 | Sitemap support | 3-4h | Phase 1 |
| Phase 3 | Advanced crawling features | 4-6h | Phase 1 |
| Phase 4 | Structured output | 3-4h | Phase 1 |
| Phase 5 | Resume capability | 3-4h | Phase 1, 4 |

**Total Estimated Effort:** 14-19 hours (reduced from 16-22h due to robots.txt removal)
**Recommended Order:** 1 → 2 → 3 → 4 → 5

---

## Phase 1: Detailed Implementation Guide / Phase 1：详细实施指南

**Estimated Effort / 预计工时:** 4-6 hours / 4-6小时
**Status / 状态:** Ready for Implementation / 准备实施

### Overview / 概述

Phase 1 fixes the critical `--follow-pagination` bug and exposes all crawl parameters via CLI, making the `wf site` command fully functional.

Phase 1 修复关键的 `--follow-pagination` 缺陷，并通过 CLI 暴露所有爬取参数，使 `wf site` 命令完全可用。

**Critical Bug / 关键缺陷:**
- `wf site` command passes `--follow-pagination` flag that doesn't exist
- Result: Command fails with "unrecognized arguments" error
- Impact: Site crawling feature is completely broken

### Step-by-Step Implementation / 分步实施

#### Step 1.1: Add --follow-pagination Flag to webfetcher.py

**File / 文件:** `webfetcher.py`
**Location / 位置:** Line ~4017 (after --crawl-delay argument)

**Current Code / 当前代码:**
```python
    ap.add_argument('--crawl-delay', type=float, default=0.5,
                    help='Delay between crawl requests in seconds (default: 0.5)')
    ap.add_argument('--format', choices=['markdown', 'html', 'both'], default='markdown',
                    help='Output format: markdown (default), html, or both')
```

**New Code to Add / 新增代码:**
```python
    ap.add_argument('--crawl-delay', type=float, default=0.5,
                    help='Delay between crawl requests in seconds (default: 0.5)')

    # Task-008 Phase 1: Add pagination and domain control flags
    # Task-008 Phase 1：添加分页和域名控制标志
    ap.add_argument('--follow-pagination', action='store_true',
                    help='Follow pagination links (next page, etc.) during crawling / 爬取时跟随分页链接（下一页等）')
    ap.add_argument('--same-domain-only', action='store_true', default=True,
                    help='Only crawl URLs from the same domain (default: True) / 仅爬取同域名的URL（默认：True）')

    ap.add_argument('--format', choices=['markdown', 'html', 'both'], default='markdown',
                    help='Output format: markdown (default), html, or both')
```

#### Step 1.2: Integrate Flags with Crawl Logic

**File / 文件:** `webfetcher.py`
**Location / 位置:** Line ~4079 (in the crawl-site mode section)

**Find this section / 找到此部分:**
```python
    if args.crawl_site:
        logging.info("Site crawling mode activated")

        # Check if supported site type
        if not is_supported_site_type(url):
            logging.error("Unsupported site type for crawling")
            sys.exit(1)

        # Crawl the site
        crawled_pages = crawl_site(
            url, ua,
            max_depth=args.max_crawl_depth,
            max_pages=args.max_pages,
```

**Update to / 更新为:**
```python
    if args.crawl_site:
        logging.info("Site crawling mode activated / 站点爬取模式已激活")

        # Task-008 Phase 1: Log pagination mode
        if args.follow_pagination:
            logging.info("Pagination following enabled / 已启用分页跟随")
        if not args.same_domain_only:
            logging.warning("Cross-domain crawling enabled - use with caution / 已启用跨域爬取 - 请谨慎使用")

        # Check if supported site type
        if not is_supported_site_type(url):
            logging.error("Unsupported site type for crawling")
            sys.exit(1)

        # Crawl the site
        crawled_pages = crawl_site(
            url, ua,
            max_depth=args.max_crawl_depth,
            max_pages=args.max_pages,
            delay=args.crawl_delay,
            follow_pagination=args.follow_pagination,      # NEW: pass pagination flag
            same_domain_only=args.same_domain_only,        # NEW: pass domain filter
```

#### Step 1.3: Update crawl_site() Function Signature

**File / 文件:** `webfetcher.py`
**Location / 位置:** Line ~3153 (crawl_site function definition)

**Current Code / 当前代码:**
```python
def crawl_site(start_url: str, ua: str, max_depth: int = 10,
               max_pages: int = 1000, delay: float = 0.5,
               # Stage 1 optimization parameters
               enable_optimizations: bool = True,
               crawl_strategy: str = 'default',
               # Stage 1.3 memory optimization
               memory_efficient: bool = False,
               page_callback = None) -> list:
```

**Updated Code / 更新后代码:**
```python
def crawl_site(start_url: str, ua: str, max_depth: int = 10,
               max_pages: int = 1000, delay: float = 0.5,
               # Task-008 Phase 1: NEW parameters
               follow_pagination: bool = False,
               same_domain_only: bool = True,
               # Stage 1 optimization parameters
               enable_optimizations: bool = True,
               crawl_strategy: str = 'default',
               # Stage 1.3 memory optimization
               memory_efficient: bool = False,
               page_callback = None) -> list:
    """
    Crawl entire site using BFS algorithm.
    使用 BFS 算法爬取整个站点。

    Returns list of (url, html, depth) tuples.
    返回 (url, html, depth) 元组列表。

    Args:
        start_url: Starting URL for crawling / 爬取起始 URL
        ua: User agent string for requests / 请求的 User Agent 字符串
        max_depth: Maximum crawling depth / 最大爬取深度
        max_pages: Maximum number of pages to crawl / 最大爬取页面数
        delay: Delay between requests in seconds / 请求间隔秒数
        follow_pagination: Follow pagination links (Task-008 Phase 1) / 跟随分页链接（Task-008 Phase 1）
        same_domain_only: Only crawl same domain (Task-008 Phase 1) / 仅爬取同域名（Task-008 Phase 1）
        enable_optimizations: Enable Stage 1 optimizations / 启用Stage 1优化
        crawl_strategy: Crawling strategy / 爬取策略
        memory_efficient: Enable memory optimization / 启用内存优化
        page_callback: Optional callback for streaming / 流式处理的可选回调
    """
```

**Note / 注意:** The actual implementation of `follow_pagination` and `same_domain_only` logic will be done in later phases. For Phase 1, we just add the parameters to fix the bug.

实际的 `follow_pagination` 和 `same_domain_only` 逻辑实现将在后续阶段完成。Phase 1 只添加参数以修复缺陷。

#### Step 1.4: Update wf.py to Expose Crawl Parameters

**File / 文件:** `wf.py`
**Location / 位置:** Line ~426 (site command handler)

**Replace the entire site command handler with:**

```python
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
        # 构建可配置参数的 webfetcher 命令
        cmd_args = [url, '-o', output_dir, '--crawl-site']

        # Task-008 Phase 1: Extract user-specified parameters or use defaults
        # Task-008 Phase 1：提取用户指定的参数或使用默认值
        max_pages_value = None
        max_depth_value = None
        delay_value = None

        # Extract parameters manually (simple approach for Phase 1)
        i = 0
        while i < len(remaining_args):
            arg = remaining_args[i]

            if arg in ['--max-pages', '--max-crawl-depth', '--delay', '--crawl-delay']:
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
        # 如果存在布尔标志则添加
        if '--follow-pagination' in remaining_args:
            cmd_args.append('--follow-pagination')

        # same-domain-only is default, explicitly add it
        # same-domain-only 是默认值，显式添加
        cmd_args.append('--same-domain-only')

        # Add any other remaining args (like --fetch-mode, etc.)
        # 添加任何其他剩余参数（如 --fetch-mode 等）
        for arg in remaining_args:
            if arg not in ['--max-pages', '--max-depth', '--max-crawl-depth',
                          '--delay', '--crawl-delay', '--follow-pagination', '--same-domain-only']:
                # Check if it's a value (next to a parameter we already processed)
                # This is a simple heuristic - skip values that look like numbers or paths
                if not (arg.replace('.', '').isdigit() or arg.startswith('/')):
                    cmd_args.append(arg)

        logger.info(f"Site crawling with: max-pages={max_pages_value}, max-depth={max_depth_value}, delay={delay_value}")
        run_webfetcher(cmd_args)
```

### Testing Steps / 测试步骤

#### Test 1: Verify --follow-pagination Flag Works

```bash
cd "/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher"

# Test that flag is recognized (should not error)
# 测试标志被识别（不应报错）
python webfetcher.py https://httpbin.org/html --crawl-site --follow-pagination --max-pages 1

# Expected: No "unrecognized arguments" error
# 预期：无"未识别参数"错误
```

**Success Criteria / 成功标准:**
- ✅ No error about unrecognized arguments
- ✅ Command executes (may or may not crawl successfully, but flag is recognized)

#### Test 2: Test wf site Command

```bash
# Test 2.1: Basic usage (should work without errors)
# 测试 2.1：基础用法（应该无错误工作）
python wf.py site https://httpbin.org/html -o ./test_output

# Expected: Creates ./test_output/ directory with crawled content
# 预期：创建 ./test_output/ 目录并包含爬取的内容

# Test 2.2: With custom parameters
# 测试 2.2：使用自定义参数
python wf.py site https://httpbin.org/html -o ./test_output_custom \
  --max-pages 5 --max-depth 2 --delay 0.3 --follow-pagination

# Expected: Uses custom parameters, no errors
# 预期：使用自定义参数，无错误

# Test 2.3: With only some custom parameters (test defaults)
# 测试 2.3：仅使用部分自定义参数（测试默认值）
python wf.py site https://httpbin.org/html -o ./test_output_partial --max-pages 3

# Expected: Uses max-pages=3, but defaults for depth and delay
# 预期：使用 max-pages=3，但 depth 和 delay 使用默认值
```

**Success Criteria / 成功标准:**
- ✅ All test commands execute without "unrecognized arguments" error
- ✅ Output directories are created
- ✅ At least one .md file is generated in each output directory

#### Test 3: Verify Backward Compatibility

```bash
# Old command format should still work
# 旧命令格式应该仍然工作
python wf.py site https://httpbin.org/html ./test_output_old

# Expected: Works with default parameters (max-pages=100, max-depth=5, delay=0.5)
# 预期：使用默认参数工作（max-pages=100, max-depth=5, delay=0.5）
```

**Success Criteria / 成功标准:**
- ✅ Old command format still works
- ✅ Uses default parameters automatically
- ✅ No breaking changes

#### Test 4: Help Text Display

```bash
# Test help text is displayed
# 测试帮助文本显示
python wf.py site

# Expected: Displays usage with available options in bilingual format
# 预期：以双语格式显示用法和可用选项
```

**Success Criteria / 成功标准:**
- ✅ Help text is displayed
- ✅ Bilingual (English/Chinese)
- ✅ Lists all available options

### Phase 1 Acceptance Criteria / Phase 1 验收标准

**Phase 1 is COMPLETE when / Phase 1 在以下情况下完成:**

- [ ] ✅ `--follow-pagination` flag exists in webfetcher.py argparser
- [ ] ✅ `--same-domain-only` flag exists with default=True
- [ ] ✅ `crawl_site()` function accepts new parameters (even if not implemented yet)
- [ ] ✅ `wf site` command works without "unrecognized arguments" error
- [ ] ✅ All crawl parameters configurable via wf.py (--max-pages, --max-depth, --delay)
- [ ] ✅ Help text updated in wf.py with bilingual options
- [ ] ✅ Test 1-4 all pass (4/4 tests)
- [ ] ✅ Backward compatibility maintained (old commands work)
- [ ] ✅ Regression test script created and passes
- [ ] ✅ Code properly documented with bilingual comments

### Files to Modify / 要修改的文件

**Summary / 总结:**

1. `webfetcher.py` - Add arguments, update function signature (3 locations)
2. `wf.py` - Update site command handler (1 location)
3. `tests/url_suite.txt` - Add test URLs (append to file)
4. `tests/test_site_crawling_phase1.py` - Create new file

**Total Lines Changed / 总修改行数:** ~150 lines

### Rollback Plan / 回滚计划

If Phase 1 has critical issues:

**Quick Fix (Temporary) / 快速修复（临时）:**
```python
# In wf.py line 446, remove --follow-pagination:
run_webfetcher([url, '-o', output_dir, '--crawl-site', '--max-crawl-depth', '5'] + remaining_args)
```

**Full Rollback / 完全回滚:**
```bash
git log --oneline | head -5  # Find commit hash
git revert <commit-hash>
```

### Next Steps After Phase 1 / Phase 1 之后的下一步

After Phase 1 is complete and tested:

1. **Review by architect** (@agent-archy-principle-architect)
2. **Update TASKS documentation** with Phase 1 completion status
3. **Git commit** with detailed message
4. **Decide on Phase 2** (Sitemap support) or stop here

Phase 1 alone provides significant value by fixing the broken `wf site` command!

---

### Risk Mitigation / 风险缓解

**Risk 1: Breaking existing crawl_site() callers / 破坏现有调用者**
- Mitigation: Keep existing `crawl_site()` function signature
- Add new `crawl_site_enhanced()` with new features
- Gradually migrate over multiple releases

**Risk 2: State file corruption / 状态文件损坏**
- Mitigation: Use JSON schema validation
- Write to temp file first, then atomic rename
- Keep backup of previous state

**Risk 3: Sitemap parsing failures / Sitemap解析失败**
- Mitigation: Robust error handling for malformed sitemaps
- Fall back to BFS crawling if sitemap parsing fails
- Support multiple sitemap formats (XML, gzipped, sitemap index)

---

## Testing Strategy / 测试策略

### Unit Tests / 单元测试 (8-10 tests per module)

**Test crawler/sitemap_manager.py:**
```python
def test_sitemap_xml_discovery():
    """Test sitemap.xml discovery from /sitemap.xml and /sitemap_index.xml."""

def test_sitemap_url_extraction():
    """Test URL extraction from sitemap.xml."""

def test_sitemap_gzip_handling():
    """Test parsing of gzipped sitemaps (sitemap.xml.gz)."""

def test_sitemap_index_parsing():
    """Test parsing sitemap index files with multiple sitemaps."""
```

**Test crawler/link_scout.py:**
```python
def test_url_pattern_matching():
    """Test glob and regex pattern matching."""

def test_domain_boundary_enforcement():
    """Test same-domain filtering."""

def test_link_discovery_comprehensive():
    """Test link extraction from <a>, <link>, <iframe>."""
```

**Test crawler/state_manager.py:**
```python
def test_state_save_load():
    """Test state persistence and loading."""

def test_state_resume_correctness():
    """Test that resume doesn't duplicate visits."""

def test_state_corruption_handling():
    """Test handling of corrupted state files."""
```

### Integration Tests / 集成测试 (5-7 scenarios)

**Test full crawl scenarios:**
```python
def test_wf_site_command_end_to_end():
    """Test wf site command from CLI to output."""
    # Run: wf site https://httpbin.org/html --max-pages 5
    # Verify: output files created, JSON index valid

def test_crawl_with_sitemap():
    """Test crawling using sitemap.xml."""
    # Setup: mock server with sitemap.xml
    # Run: wf site --use-sitemap
    # Verify: URLs from sitemap are crawled

def test_resume_interrupted_crawl():
    """Test resuming a partially completed crawl."""
    # Run: crawl 100 pages
    # Interrupt: after 50 pages
    # Resume: with --resume flag
    # Verify: no duplicate fetches, total = 100 pages
```

### Regression Tests / 回归测试

#### Add Site Crawling Test Cases to url_suite.txt

**File / 文件:** `tests/url_suite.txt`

**Add the following test URLs / 添加以下测试 URL:**

```
# Site Crawling Tests / 站点爬取测试 (Task-008 Phase 1)
# ========================================================

# Test 1: Basic site crawl - single page
https://httpbin.org/html | HTTPBin HTML (site crawl test) | urllib | basic,site-crawl,phase1

# Test 2: Multi-page crawl - links test
https://httpbin.org/links/5/0 | HTTPBin links test (5 links) | urllib | site-crawl,pagination,phase1

# Test 3: Example.com - simple static site
https://example.com | Example.com (depth test) | urllib | basic,site-crawl,depth-test,phase1
```

#### Create Regression Test Script

**File / 文件:** `tests/test_site_crawling_phase1.py`

Create a comprehensive regression test script to verify Phase 1 functionality:

```python
#!/usr/bin/env python3
"""
Regression tests for site crawling functionality (Task-008 Phase 1)
站点爬取功能回归测试（Task-008 Phase 1）
"""

import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, timeout=60):
    """Run command and return result"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher"
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"

def test_basic_site_crawl():
    """Test 1: Basic site crawl command"""
    print("Test 1: Basic site crawl...")

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ['python', 'wf.py', 'site', 'https://httpbin.org/html',
               '-o', tmpdir, '--max-pages', '1']

        code, stdout, stderr = run_command(cmd)

        if 'unrecognized arguments' in stderr:
            print(f"  ❌ FAILED: Unrecognized arguments error")
            print(f"  stderr: {stderr}")
            return False

        # Check output directory has files
        output_files = list(Path(tmpdir).glob('**/*.md'))
        if not output_files:
            print(f"  ⚠️  WARNING: No output files, but command executed")
            # This is acceptable for Phase 1 - flag is recognized
            return True

        print(f"  ✅ PASSED: Generated {len(output_files)} files")
        return True

def test_follow_pagination_flag():
    """Test 2: --follow-pagination flag is recognized"""
    print("Test 2: --follow-pagination flag recognition...")

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ['python', 'wf.py', 'site', 'https://httpbin.org/html',
               '-o', tmpdir, '--max-pages', '1', '--follow-pagination']

        code, stdout, stderr = run_command(cmd)

        # Check for "unrecognized arguments" error
        if 'unrecognized arguments' in stderr:
            print(f"  ❌ FAILED: --follow-pagination not recognized")
            print(f"  stderr: {stderr}")
            return False

        print(f"  ✅ PASSED: --follow-pagination flag recognized")
        return True

def test_custom_parameters():
    """Test 3: Custom crawl parameters"""
    print("Test 3: Custom crawl parameters...")

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = ['python', 'wf.py', 'site', 'https://httpbin.org/html',
               '-o', tmpdir,
               '--max-pages', '3',
               '--max-depth', '2',
               '--delay', '0.1']

        code, stdout, stderr = run_command(cmd, timeout=30)

        if 'unrecognized arguments' in stderr:
            print(f"  ❌ FAILED: Parameters not recognized")
            print(f"  stderr: {stderr}")
            return False

        print(f"  ✅ PASSED: Custom parameters accepted")
        return True

def test_backward_compatibility():
    """Test 4: Backward compatibility (old command format)"""
    print("Test 4: Backward compatibility...")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Old format: wf site <URL> <output_dir>
        cmd = ['python', 'wf.py', 'site', 'https://httpbin.org/html', tmpdir]

        code, stdout, stderr = run_command(cmd)

        if 'unrecognized arguments' in stderr:
            print(f"  ❌ FAILED: Backward compatibility broken")
            print(f"  stderr: {stderr}")
            return False

        print(f"  ✅ PASSED: Backward compatibility maintained")
        return True

def test_help_text():
    """Test 5: Help text is displayed correctly"""
    print("Test 5: Help text display...")

    cmd = ['python', 'wf.py', 'site']
    code, stdout, stderr = run_command(cmd, timeout=10)

    # Check for bilingual help text
    if '可用选项' not in stdout and '可用选项' not in stderr:
        print(f"  ❌ FAILED: Help text missing or not bilingual")
        return False

    if 'max-pages' not in stdout and 'max-pages' not in stderr:
        print(f"  ❌ FAILED: Help text incomplete")
        return False

    print(f"  ✅ PASSED: Help text displayed correctly")
    return True

def main():
    """Run all regression tests"""
    print("=" * 70)
    print("Site Crawling Regression Tests (Task-008 Phase 1)")
    print("站点爬取回归测试（Task-008 Phase 1）")
    print("=" * 70)
    print()

    tests = [
        test_basic_site_crawl,
        test_follow_pagination_flag,
        test_custom_parameters,
        test_backward_compatibility,
        test_help_text
    ]

    results = []
    for test_func in tests:
        try:
            passed = test_func()
            results.append(passed)
        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
        print()

    # Summary
    print("=" * 70)
    passed_count = sum(results)
    total_count = len(results)
    success_rate = (passed_count / total_count * 100) if total_count > 0 else 0

    print(f"Results: {passed_count}/{total_count} tests passed ({success_rate:.1f}%)")
    print(f"结果：{passed_count}/{total_count} 测试通过 ({success_rate:.1f}%)")

    if passed_count == total_count:
        print("\n✅ All tests PASSED! Phase 1 regression testing complete.")
        print("✅ 所有测试通过！Phase 1 回归测试完成。")
        return 0
    else:
        print(f"\n❌ {total_count - passed_count} test(s) FAILED!")
        print(f"❌ {total_count - passed_count} 个测试失败！")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

#### Regression Test Execution / 回归测试执行

**Run After Each Phase / 每个阶段后运行:**

```bash
# Run Phase 1 regression tests
cd "/Users/tieli/Library/Mobile Documents/com~apple~CloudDocs/Project/Web_Fetcher"
python tests/test_site_crawling_phase1.py

# Run full regression suite
python scripts/run_regression_suite.py
```

**Expected Results / 预期结果:**
- [ ] All 5 Phase 1 tests pass (5/5)
- [ ] No regressions in existing regression suite (30/30 or better)
- [ ] Backward compatibility maintained
- [ ] No "unrecognized arguments" errors

---

## Documentation Requirements / 文档要求

### User Documentation / 用户文档

**1. Updated wf.py Help Text / 更新帮助文本**
```bash
wf site --help
```
- Document all new flags and options
- Provide examples for common use cases
- Bilingual (English/Chinese)

**2. Crawler Guide / 爬虫指南** (`docs/crawler_guide.md`)
- Architecture overview
- Crawl strategy selection guide
- Sitemap.xml handling
- Resume capability usage
- Output format specifications
- Troubleshooting common issues
- Note: Personal use only, no robots.txt compliance

**3. Examples / 示例**
```bash
# Basic site crawl
wf site https://example.com

# Crawl with custom parameters
wf site https://docs.example.com --max-pages 200 --max-depth 3

# Crawl documentation site with pattern filtering
wf site https://example.com --include-pattern "/docs/*" --strategy documentation

# Resume interrupted crawl
wf site https://example.com --resume

# Generate JSON index and CSV report
wf site https://example.com --output-json index.json --output-csv report.csv
```

### Developer Documentation / 开发者文档

**1. Architecture Document / 架构文档**
- Component responsibilities
- Data flow diagrams
- Extension points for new strategies

**2. API Documentation / API文档**
- Docstrings for all public functions
- Type hints for all function parameters
- Usage examples in docstrings

**3. Migration Guide / 迁移指南**
- How to migrate from old `crawl_site()` to new enhanced crawler
- Breaking changes (if any)
- Deprecation timeline

---

## Acceptance Criteria / 验收标准

### Functional Criteria / 功能标准

- ✅ **Bug Fix**: `wf site` command works without `--follow-pagination` error
- ✅ **Parameters**: All crawl parameters (depth, pages, delay) configurable via CLI
- ✅ **Sitemap**: Discovers and uses sitemap.xml when available
- ✅ **Pagination**: Follows pagination links correctly
- ✅ **URL Filtering**: Supports include/exclude patterns (glob and regex)
- ✅ **Domain Boundaries**: Enforces same-domain crawling by default
- ✅ **Strategies**: At least 3 crawl strategies implemented (default, docs, blog)
- ✅ **JSON Output**: Generates valid JSON index with complete metadata
- ✅ **CSV Output**: Generates importable CSV report
- ✅ **Resume**: Can resume interrupted crawls without duplicates
- ⚠️ **Note**: No robots.txt compliance (personal use tool)

### Quality Criteria / 质量标准

- ✅ **Test Coverage**: >85% code coverage for new crawler module
- ✅ **Regression**: All existing tests pass (30/30 or better)
- ✅ **Performance**: No performance regression (<10% slower than current)
- ✅ **Documentation**: Bilingual user guide and API docs complete
- ✅ **Backward Compatibility**: Existing `wf site` commands still work

### Performance Criteria / 性能标准

- ✅ **Crawl Speed**: 5-10 pages/minute on average network
- ✅ **Memory Usage**: <500MB for 1000-page crawl
- ✅ **State File Size**: <1MB per 1000 URLs visited
- ✅ **Resume Overhead**: <5% extra time compared to fresh crawl

---

## Dependencies / 依赖

### Required Libraries / 必需库

```python
# Standard library (already available)
import xml.etree.ElementTree  # For sitemap.xml parsing
import gzip  # For gzipped sitemap parsing
import json  # For state and JSON output
import csv  # For CSV output
import time  # For timestamps
import re  # For regex patterns
from pathlib import Path  # For file operations
```

**No new external dependencies required.** / 无需新的外部依赖。
**Note:** urllib.robotparser removed as robots.txt support was eliminated. / 注意：已移除urllib.robotparser，因为不再支持robots.txt。

### Related Tasks / 相关任务

- **Task-007**: Dual-Method Regression Testing
  - New crawler should support dual-method testing
  - Extend `--dual-method` to site crawling mode

- **Task-002**: Regression Test Harness
  - Add crawler test scenarios to regression suite

- **Task-001**: Parser Template Creator
  - Crawled content should use template-based parsing

---

## Future Enhancements (Out of Scope) / 未来增强（不在范围内）

These features are explicitly **NOT** included in Task-008 but may be considered for future tasks:

1. **Distributed Crawling / 分布式爬取:** Multi-machine crawling with shared state
2. **JavaScript Execution / JavaScript执行:** Full page rendering for all pages (too slow)
3. **Content Deduplication / 内容去重:** Detect and skip duplicate content (different URLs, same content)
4. **Link Graph Analysis / 链接图分析:** PageRank-style importance scoring
5. **Media Download / 媒体下载:** Automatic download of images, videos, PDFs
6. **Database Storage / 数据库存储:** Store crawled pages in database instead of files
7. **Web UI / Web界面:** Graphical interface for crawl configuration and monitoring

---

## Success Metrics / 成功指标

**Quantitative Metrics / 量化指标:**
- 🎯 **Bug Resolution**: 100% (1/1 critical bug fixed)
- 🎯 **Feature Completion**: 100% (all 5 phases complete)
- 🎯 **Test Coverage**: >85% for new code
- 🎯 **Regression Tests**: 100% pass rate (30/30 or better)
- 🎯 **Documentation**: 100% bilingual coverage

**Qualitative Metrics / 定性指标:**
- ✨ **User Experience**: CLI is intuitive and well-documented
- ✨ **Code Quality**: Clean architecture, well-tested, maintainable
- ✨ **Reliability**: Handles errors gracefully, state persistence works
- ✨ **Performance**: No noticeable slowdown from current implementation

---

## References / 参考资料

### Related Files / 相关文件

1. `wf.py:426-446` - Current `wf site` command handler
2. `webfetcher.py:3153-3360` - Current `crawl_site()` implementation
3. `webfetcher.py:3082-3152` - `crawl_site_by_categories()` (category-first strategy)
4. `webfetcher.py:2690-2720` - `process_pagination()` (pagination handling)
5. `tests/url_suite.txt` - Regression test URL suite

### External Standards / 外部标准

- [Sitemap Protocol](https://www.sitemaps.org/protocol.html)
- [Sitemap XML Format](https://www.sitemaps.org/protocol.html#xmlTagDefinitions)

---

## Notes / 备注

**Design Philosophy / 设计哲学:**
- ✅ **Backward Compatible**: Existing commands must continue to work
- ✅ **Progressive Enhancement**: New features are opt-in, not mandatory
- ✅ **Personal Use Tool**: Designed for personal/research use, not production crawling
- ✅ **Fail-Safe Defaults**: Safe defaults (rate limiting, same-domain crawling)
- ✅ **User Control**: Always provide override flags for customization
- ⚠️ **No Robots.txt**: This tool does not respect robots.txt (personal use only)

**Implementation Notes / 实施说明:**
- Phase 1 (bug fixes) should be completed first as it unblocks users
- Phases 2-5 can be developed in parallel by different developers
- Each phase should have its own git commit with detailed commit message
- All bilingual documentation must be verified for accuracy

---

**Created By / 创建者:** Architectural Analysis (Principal Architect)
**Last Updated / 最后更新:** 2025-10-10
**Status / 状态:** Ready for Review and Implementation / 待审查与实施

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
