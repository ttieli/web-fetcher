# Task-008: Enhanced Multi-Page and Whole-Site Crawling
# Task-008：增强的多页面与整站爬取功能

**Priority / 优先级:** P2 (Important / 重要)
**Status / 状态:** PENDING / 待办
**Created / 创建日期:** 2025-10-10
**Estimated Effort / 预计工时:** 16-22 hours / 16-22小时

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
2. 🚫 **No Robots.txt Support / 不支持robots.txt:** Doesn't respect site crawling policies
3. 🚫 **No Sitemap Support / 不支持sitemap.xml:** Misses efficient site discovery
4. 🔗 **Limited URL Filtering / 有限的URL过滤:** Only supports documentation URL filter
5. 🌐 **No Domain Boundaries / 无域名边界:** Doesn't enforce same-domain crawling
6. 💾 **No Resume Capability / 无恢复能力:** Can't resume interrupted crawls
7. 📊 **Limited Output Formats / 有限的输出格式:** Only dumps files, no structured index

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
   - Add robots.txt compliance
   - Add sitemap.xml discovery and parsing
   - Enforce domain boundary controls
   - Improve link discovery algorithms

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

### Phase 2: Robots.txt and Sitemap Support (5-7 hours) / 阶段2：Robots.txt与Sitemap支持

**2.1 Robots.txt Parser / Robots.txt解析器**
- [ ] Implement robots.txt fetcher and parser
- [ ] Respect User-agent directives
- [ ] Handle Disallow/Allow rules
- [ ] Respect Crawl-delay directive
- [ ] Add `--ignore-robots` flag for override

**2.2 Sitemap.xml Parser / Sitemap.xml解析器**
- [ ] Implement sitemap.xml discovery (check /sitemap.xml, robots.txt)
- [ ] Parse sitemap.xml and sitemap index files
- [ ] Extract URLs with priorities and lastmod dates
- [ ] Add `--use-sitemap` flag to enable sitemap-first crawling

**2.3 Integration / 集成**
```python
def crawl_site_with_policies(start_url, **kwargs):
    """Enhanced crawl with robots.txt and sitemap support."""
    # 1. Check robots.txt
    if not kwargs.get('ignore_robots'):
        robots = fetch_robots_txt(start_url)
        if not robots.can_fetch(ua, start_url):
            raise PermissionError("Crawling disallowed by robots.txt")

    # 2. Try sitemap-first if enabled
    if kwargs.get('use_sitemap'):
        sitemap_urls = fetch_sitemap(start_url)
        if sitemap_urls:
            return crawl_from_sitemap(sitemap_urls, **kwargs)

    # 3. Fall back to BFS crawling
    return crawl_site(start_url, **kwargs)
```

**Acceptance Criteria / 验收标准:**
- ✅ Respects robots.txt Disallow rules
- ✅ Discovers and parses sitemap.xml
- ✅ Can crawl from sitemap when available
- ✅ `--ignore-robots` flag works for testing

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
│  │  PolicyManager    │  │  LinkScout   │  │  State  │ │
│  │  - robots.txt     │  │  - Discover  │  │  - Save │ │
│  │  - sitemap.xml    │  │  - Filter    │  │  - Load │ │
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
│   ├── policy_manager.py          # Robots.txt, sitemap handling
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
│       ├── test_policy_manager.py
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
| Phase 2 | Robots.txt + sitemap support | 5-7h | Phase 1 |
| Phase 3 | Advanced crawling features | 4-6h | Phase 1 |
| Phase 4 | Structured output | 3-4h | Phase 1 |
| Phase 5 | Resume capability | 3-4h | Phase 1, 4 |

**Total Estimated Effort:** 16-22 hours
**Recommended Order:** 1 → 2 → 3 → 4 → 5

### Risk Mitigation / 风险缓解

**Risk 1: Breaking existing crawl_site() callers / 破坏现有调用者**
- Mitigation: Keep existing `crawl_site()` function signature
- Add new `crawl_site_enhanced()` with new features
- Gradually migrate over multiple releases

**Risk 2: Robots.txt compliance too strict / Robots.txt合规性过于严格**
- Mitigation: Always provide `--ignore-robots` override
- Log when robots.txt blocks crawling
- Provide clear error messages

**Risk 3: State file corruption / 状态文件损坏**
- Mitigation: Use JSON schema validation
- Write to temp file first, then atomic rename
- Keep backup of previous state

---

## Testing Strategy / 测试策略

### Unit Tests / 单元测试 (8-10 tests per module)

**Test crawler/policy_manager.py:**
```python
def test_robots_txt_parser():
    """Test robots.txt parsing with various formats."""

def test_robots_txt_respect_disallow():
    """Test that Disallow rules are respected."""

def test_sitemap_xml_discovery():
    """Test sitemap.xml discovery from robots.txt and /sitemap.xml."""

def test_sitemap_url_extraction():
    """Test URL extraction from sitemap.xml."""
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

def test_crawl_with_robots_txt():
    """Test crawling with robots.txt restrictions."""
    # Setup: mock server with robots.txt
    # Verify: blocked paths are not crawled

def test_resume_interrupted_crawl():
    """Test resuming a partially completed crawl."""
    # Run: crawl 100 pages
    # Interrupt: after 50 pages
    # Resume: with --resume flag
    # Verify: no duplicate fetches, total = 100 pages
```

### Regression Tests / 回归测试

- [ ] Add `wf site` test URLs to `tests/url_suite.txt`
- [ ] Run full regression suite after each phase
- [ ] Ensure backward compatibility with existing commands

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
- robots.txt and sitemap.xml handling
- Resume capability usage
- Output format specifications
- Troubleshooting common issues

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
- ✅ **Robots.txt**: Respects robots.txt Disallow rules (with override option)
- ✅ **Sitemap**: Discovers and uses sitemap.xml when available
- ✅ **Pagination**: Follows pagination links correctly
- ✅ **URL Filtering**: Supports include/exclude patterns (glob and regex)
- ✅ **Domain Boundaries**: Enforces same-domain crawling by default
- ✅ **Strategies**: At least 3 crawl strategies implemented (default, docs, blog)
- ✅ **JSON Output**: Generates valid JSON index with complete metadata
- ✅ **CSV Output**: Generates importable CSV report
- ✅ **Resume**: Can resume interrupted crawls without duplicates

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
import urllib.robotparser  # For robots.txt parsing
import xml.etree.ElementTree  # For sitemap.xml parsing
import json  # For state and JSON output
import csv  # For CSV output
import time  # For timestamps
import re  # For regex patterns
from pathlib import Path  # For file operations
```

**No new external dependencies required.** / 无需新的外部依赖。

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

- [Robots.txt Specification](https://www.robotstxt.org/robotstxt.html)
- [Sitemap Protocol](https://www.sitemaps.org/protocol.html)
- [RFC 9309 - Robots Exclusion Protocol](https://datatracker.ietf.org/doc/rfc9309/)

---

## Notes / 备注

**Design Philosophy / 设计哲学:**
- ✅ **Backward Compatible**: Existing commands must continue to work
- ✅ **Progressive Enhancement**: New features are opt-in, not mandatory
- ✅ **Fail-Safe Defaults**: Safe, polite defaults (respect robots.txt, rate limiting)
- ✅ **User Control**: Always provide override flags for testing (--ignore-robots, etc.)

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
