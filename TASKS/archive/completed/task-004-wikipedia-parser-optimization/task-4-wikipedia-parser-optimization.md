# Task 4: Wikipedia Parser Optimization / 维基百科解析器优化

## Status / 状态
- 🔄 **PENDING** / 待执行

## Priority / 优先级
- P2 – Important / 重要优先级

## Estimated Effort / 预计工时
- 6-8 hours / 6-8小时
  - Template creation: 2-3h / 模板创建：2-3小时
  - Testing & validation: 2-3h / 测试与验证：2-3小时
  - Documentation: 1-2h / 文档编写：1-2小时

---

## 📝 Task Name / 任务名称

Wikipedia Parser Optimization / 维基百科解析器优化

---

## Overview / 概述

Currently, Wikipedia articles (zh.wikipedia.org) are parsed using the legacy generic parser, which produces poor-quality output with excessive navigation noise, missing infobox data, and leaked CSS code. This task migrates Wikipedia to the template-based parser system (Task-001 deliverable) to achieve clean, structured content extraction.

当前维基百科文章（zh.wikipedia.org）使用旧版通用解析器，产生大量导航噪音、缺失信息框数据和CSS代码泄漏的低质量输出。本任务将维基百科迁移到基于模板的解析器系统（Task-001交付物），实现干净、结构化的内容提取。

### Current Problems / 当前问题

**Test Article:** 聂元梓 (https://zh.wikipedia.org/w/index.php?title=聂元梓)
**Output File:** 639 lines total

**Issue Analysis / 问题分析:**

1. **Massive Navigation Noise (Lines 1-124, ~19% of file) / 大量导航噪音:**
   ```
   开关目录
   聂元梓
   7种语言
   编辑链接
   工具
   移至侧栏
   隐藏
   [... 100+ lines of UI elements ...]
   ```

2. **Missing Infobox Data / 缺失信息框数据:**
   - No structured birth/death dates
   - No nationality, occupation metadata
   - Wikipedia infoboxes not extracted

3. **CSS Code Leakage (Line 192) / CSS代码泄漏:**
   ```
   .mw-parser-output .refbegin{font-size:90%;margin-bottom:0.5em}...
   ```

4. **Poor Section Structure / 章节结构不佳:**
   - No proper markdown headers for "生平", "参考文献"
   - Sections not clearly delimited

**Quality Metrics / 质量指标:**
- **Content-to-Noise Ratio:** ~20% (120 noise lines / 639 total)
- **Missing Metadata:** Infobox fields, categories, interwiki links
- **Structural Issues:** No proper heading hierarchy

---

## 📋 Requirements / 具体要求

### Must-Have Features / 必备功能

1. **Create Wikipedia-Specific Template / 创建维基百科专用模板**
   - Location: `parser_engine/templates/sites/wikipedia/zh_wikipedia.yaml`
   - Follow schema: `parser_engine/templates/schema.yaml`
   - Support Chinese variants: zh-cn, zh-tw, zh-hk, zh-sg

2. **Clean Content Extraction / 干净内容提取**
   - Remove navigation elements (sidebar, language links, edit tools)
   - Remove footer links (privacy, disclaimers, categories UI)
   - Filter out CSS/JavaScript code
   - Preserve actual article content only

3. **Infobox Extraction / 信息框提取**
   - Extract `.infobox` table data
   - Parse birth/death dates, nationality, occupation
   - Format as structured metadata in markdown frontmatter

4. **Proper Section Structure / 正确章节结构**
   - Extract Wikipedia headings (h2.mw-headline, h3.mw-headline)
   - Convert to markdown headers (##, ###)
   - Preserve heading hierarchy

5. **Reference Handling / 参考文献处理**
   - Extract reference section (.references)
   - Clean reference formatting
   - Preserve citation links

6. **Chinese Variant Support / 中文变体支持**
   - Handle variant parameter: `?variant=zh-cn`
   - Preserve selected variant in output

### Nice-to-Have Features / 可选功能

7. **Category Extraction / 分类提取**
   - Extract article categories (footer categories)
   - Include in metadata

8. **Interwiki Links / 跨语言链接**
   - Extract language links to other Wikipedia versions
   - Include in metadata

---

## 🔧 Technical Approach / 技术方案

### Implementation Strategy / 实现策略

#### 1. Template Creation / 模板创建

**File:** `parser_engine/templates/sites/wikipedia/zh_wikipedia.yaml`

**Structure (based on wechat.yaml template):**

```yaml
name: "Wikipedia Chinese Articles"
version: "1.0.0"
domains:
  - "zh.wikipedia.org"
priority: 100  # High priority for exact domain match

selectors:
  # Title extraction
  title:
    - selector: "h1.firstHeading"
      strategy: "css"
    - selector: "title"
      strategy: "css"

  # Author (Wikipedia doesn't have single author, use "Wikipedia contributors")
  author:
    - selector: "meta[name='author']"
      strategy: "css"
      attribute: "content"
      default: "Wikipedia contributors"

  # Publish date (last modified)
  date:
    - selector: "#footer-info-lastmod"
      strategy: "css"
      transform: "extract_date"  # Extract date from "本页面最后修订于..."

  # Main content (critical - must filter navigation)
  content:
    - selector: "#mw-content-text .mw-parser-output"
      strategy: "css"
      exclude:
        - ".mw-editsection"        # Edit links
        - "#toc"                    # Table of contents
        - ".navbox"                 # Navigation boxes
        - ".ambox"                  # Article messages
        - ".sistersitebox"          # Sister project links
        - "script"                  # JavaScript
        - "style"                   # CSS
        - ".mw-jump-link"           # Accessibility links
        - "#catlinks"               # Category links
        - ".printfooter"            # Print footer
        - ".mw-indicators"          # Page indicators

  # Infobox extraction
  metadata:
    infobox:
      - selector: ".infobox"
        strategy: "css"
        extract_table: true

    categories:
      - selector: "#mw-normal-catlinks ul li a"
        strategy: "css"
        extract_all: true

# Content filtering rules
filters:
  remove_patterns:
    - "^\\[编辑\\]$"              # [编辑] links
    - "^\\[来源请求\\]$"          # Citation needed
    - "^目录$"                   # Table of contents header

  css_classes_to_remove:
    - "mw-editsection"
    - "mw-jump"
    - "noprint"
    - "metadata"
```

#### 2. Routing Configuration / 路由配置

**File:** `config/routing.yaml`

Add Wikipedia-specific rule:

```yaml
- name: "Wikipedia Chinese Articles"
  priority: 90
  pattern:
    domain: "zh.wikipedia.org"
  fetch:
    method: "urllib"  # Static content, no JS needed
  parse:
    parser: "template"
    template: "sites/wikipedia/zh_wikipedia.yaml"
```

#### 3. Parser Integration / 解析器集成

**File:** `parsers_migrated.py`

No code changes needed - template system handles routing automatically.

#### 4. Testing Strategy / 测试策略

**Create:** `tests/test_wikipedia_parser.py`

```python
def test_wikipedia_article_parsing():
    """Test Wikipedia article parsing with noise filtering"""
    url = "https://zh.wikipedia.org/w/index.php?title=聂元梓"
    result = fetch_and_parse(url)

    # Assert content quality
    assert "聂元梓" in result.title
    assert len(result.content) > 1000
    assert "开关目录" not in result.content  # No nav noise
    assert ".mw-parser-output" not in result.content  # No CSS

    # Assert infobox data
    assert result.metadata.get("infobox") is not None

def test_wikipedia_chinese_variants():
    """Test Chinese variant parameter handling"""
    url_cn = "...?variant=zh-cn"
    url_tw = "...?variant=zh-tw"
    # Test variant preservation
```

---

## In Scope / 工作范围

### Deliverables / 交付物

1. ✅ **Wikipedia Template**
   - Location: `parser_engine/templates/sites/wikipedia/zh_wikipedia.yaml`
   - Validated against schema
   - Documented with inline comments

2. ✅ **Routing Rule**
   - Updated: `config/routing.yaml`
   - Wikipedia domain routing configured

3. ✅ **Test Suite**
   - File: `tests/test_wikipedia_parser.py`
   - Test cases:
     - Content extraction (no nav noise)
     - Infobox parsing
     - Chinese variant support
     - Reference section handling
     - Edge cases (stub articles, disambiguation pages)

4. ✅ **Documentation**
   - README: `parser_engine/templates/sites/wikipedia/README.md`
   - Usage examples
   - Known limitations

5. ✅ **Quality Validation**
   - Before/after comparison report
   - Content completeness metrics
   - Parsing speed benchmarks

---

## Out of Scope / 非范围事项

The following items are explicitly excluded from this task:

1. ❌ **Other Wikipedia Language Versions**
   - Only Chinese Wikipedia (zh.wikipedia.org)
   - English/other languages: future task

2. ❌ **Wikipedia-Specific Content Types**
   - Disambiguation pages (special handling needed)
   - List articles (different structure)
   - Portal pages

3. ❌ **Advanced MediaWiki Features**
   - Template transclusion rendering
   - Math formula parsing
   - Gallery/media handling

4. ❌ **Historical Revisions**
   - Only current version parsing
   - No diff/revision comparison

5. ❌ **Wikidata Integration**
   - No Wikidata API calls
   - No structured data from Wikidata

---

## Dependencies / 依赖

### Required / 必需

1. ✅ **parser_engine/ Infrastructure**
   - Confirmed active (Task-3 analysis)
   - Template loader working
   - Validation tools available

2. ✅ **Template System**
   - Task-001 deliverable
   - Schema validation tools
   - Template generator CLI

3. ✅ **Routing System**
   - Config-driven routing (config/routing.yaml)
   - Template-based parser integration

### Optional / 可选

4. ⚠️ **Existing Templates as Reference**
   - wechat.yaml - WeChat article structure
   - xiaohongshu.yaml - XiaoHongShu content pattern
   - Use as architectural examples

---

## Risks & Mitigations / 风险与缓解

### Risk 1: Wikipedia HTML Structure Changes / 风险1：维基百科HTML结构变更

**Impact:** Template selectors may break if Wikipedia updates their HTML
**Probability:** Low (Wikipedia has stable structure)
**Mitigation:**
- Use multiple fallback selectors for critical fields
- Monitor Wikipedia technical changes
- Include version notes in template

### Risk 2: Chinese Variant Handling Complexity / 风险2：中文变体处理复杂性

**Impact:** Different variants may render different content
**Probability:** Medium
**Mitigation:**
- Test all major variants (zh-cn, zh-tw, zh-hk)
- Document variant-specific quirks
- Use variant-agnostic selectors where possible

### Risk 3: Infobox Parsing Variability / 风险3：信息框解析变化性

**Impact:** Different article types have different infobox structures
**Probability:** High (infoboxes vary greatly)
**Mitigation:**
- Use flexible table extraction
- Handle missing infobox gracefully
- Test multiple article types (person, place, event)

### Risk 4: Performance with Large Articles / 风险4：大型文章性能问题

**Impact:** Very long articles may slow parsing
**Probability:** Low
**Mitigation:**
- Benchmark with large articles (>50KB)
- Optimize selector specificity
- Set reasonable timeout limits

---

## ✅ Acceptance Criteria / 验收标准

### Functional Criteria / 功能标准

- [ ] **Template Created and Valid**
  - zh_wikipedia.yaml exists at correct location
  - Passes schema validation
  - All required selectors defined

- [ ] **Content Quality Improved**
  - Navigation noise removed (<5% of output)
  - No CSS/JavaScript code in output
  - Main article content extracted cleanly

- [ ] **Infobox Extraction Working**
  - Infobox data captured in metadata
  - At least 3 fields extracted (for articles with infoboxes)
  - Graceful handling when infobox absent

- [ ] **Section Structure Preserved**
  - Wikipedia headings converted to markdown (##, ###)
  - Heading hierarchy maintained
  - Section content properly associated

- [ ] **Chinese Variant Support**
  - Variant parameter preserved in requests
  - Content rendered in selected variant
  - Tested: zh-cn, zh-tw, zh-hk

- [ ] **References Section Clean**
  - Reference links extracted
  - Citation formatting preserved
  - No duplicate footnote markers

### Testing Criteria / 测试标准

- [ ] **All Tests Passing**
  - test_wikipedia_parser.py: 100% pass rate
  - At least 5 test cases covering:
    - Content extraction
    - Infobox parsing
    - Variant handling
    - Reference section
    - Edge cases

- [ ] **Regression Testing**
  - Existing tests still pass (no breaking changes)
  - Generic parser unaffected
  - Other templates unaffected

### Quality Criteria / 质量标准

- [ ] **Content-to-Noise Ratio: >95%**
  - Measured: actual content / total output
  - Baseline: ~20% → Target: >95%

- [ ] **Parsing Speed: <3s**
  - Typical article (20-50KB) parses in <3 seconds
  - No significant slowdown vs generic parser

- [ ] **Documentation Complete**
  - Template inline comments explain selectors
  - README with usage examples
  - Known limitations documented

---

## Success Metrics / 成功指标

### Before/After Comparison / 前后对比

**Test Article:** 聂元梓 (https://zh.wikipedia.org/w/index.php?title=聂元梓)

| Metric / 指标 | Before / 优化前 | Target / 目标 |
|--------------|----------------|--------------|
| Output Lines | 639 | <250 |
| Nav Noise Lines | 120 (19%) | <10 (<4%) |
| Content-to-Noise Ratio | ~20% | >95% |
| Infobox Fields Extracted | 0 | ≥3 |
| CSS Code Leaks | Yes (line 192) | None |
| Parse Time | 1.6s | <3s |
| Section Headers | Mixed | Clean ## hierarchy |

### Quality Gates / 质量关卡

**Must achieve all:**
1. ✅ Content-to-noise ratio >95%
2. ✅ Zero CSS/JS code in output
3. ✅ Infobox extraction working (when present)
4. ✅ All tests passing
5. ✅ Documentation complete

**Nice-to-have:**
6. ⭐ Parse time <2s
7. ⭐ Category extraction working
8. ⭐ Interwiki links captured

---

## Milestones / 里程碑

### Phase 1: Template Creation (2-3 hours) / 阶段1：模板创建

**Duration:** 2-3h

**Tasks:**
1. Create directory: `parser_engine/templates/sites/wikipedia/`
2. Analyze Wikipedia HTML structure (inspect article page)
3. Identify CSS selectors for:
   - Main content (.mw-parser-output)
   - Title (h1.firstHeading)
   - Infobox (.infobox)
   - Headings (.mw-headline)
   - References (.references)
4. Create zh_wikipedia.yaml template
5. Validate against schema: `python -m parser_engine.tools.validators.schema_validator`

**Deliverable:** Validated Wikipedia template

---

### Phase 2: Routing & Integration (1-2 hours) / 阶段2：路由与集成

**Duration:** 1-2h

**Tasks:**
1. Update `config/routing.yaml` with Wikipedia rule
2. Test routing decision: `wf https://zh.wikipedia.org/... --debug`
3. Verify template loading in parsers_migrated.py
4. Test basic parsing with new template
5. Compare output quality with baseline

**Deliverable:** Integrated and routing properly

---

### Phase 3: Testing & Validation (2-3 hours) / 阶段3：测试与验证

**Duration:** 2-3h

**Tasks:**
1. Create `tests/test_wikipedia_parser.py`
2. Write test cases:
   - `test_content_extraction_no_noise()`
   - `test_infobox_parsing()`
   - `test_chinese_variant_support()`
   - `test_reference_section_clean()`
   - `test_edge_case_stub_article()`
3. Run full test suite: `pytest tests/ -v`
4. Measure quality metrics (before/after)
5. Create comparison report

**Deliverable:** Passing test suite + quality report

---

### Phase 4: Documentation & Finalization (1-2 hours) / 阶段4：文档与完善

**Duration:** 1-2h

**Tasks:**
1. Create `parser_engine/templates/sites/wikipedia/README.md`
2. Add usage examples:
   ```bash
   wf "https://zh.wikipedia.org/wiki/聂元梓"
   wf "https://zh.wikipedia.org/wiki/中国?variant=zh-cn"
   ```
3. Document known limitations
4. Add inline comments to template
5. Update TASKS/README.md with completion status
6. Create completion report

**Deliverable:** Complete documentation

---

## Notes / 备注

### Reference Templates / 参考模板

Study existing templates for architectural patterns:
- `parser_engine/templates/sites/wechat/wechat.yaml` - Rich selector examples
- `parser_engine/templates/sites/xiaohongshu/xiaohongshu.yaml` - Content filtering
- `parser_engine/templates/schema.yaml` - Template structure

### Wikipedia Markup Specifics / 维基百科标记特性

**Key CSS Classes to Handle:**
- `.mw-parser-output` - Main content wrapper
- `.infobox` - Infobox table
- `.mw-headline` - Section headings
- `.references` - Reference list
- `.mw-editsection` - Edit links (remove)
- `.navbox` - Navigation boxes (remove)
- `.catlinks` - Category links

**MediaWiki Structure:**
```html
<div id="mw-content-text" class="mw-body-content">
  <div class="mw-parser-output">
    <table class="infobox">...</table>
    <p>Article content...</p>
    <h2><span class="mw-headline">Section</span></h2>
    <div class="reflist references">...</div>
  </div>
</div>
```

### Testing URLs / 测试URL

Use these URLs for comprehensive testing:

1. **Standard Biography:** https://zh.wikipedia.org/wiki/聂元梓
2. **With Infobox:** https://zh.wikipedia.org/wiki/中华人民共和国
3. **Stub Article (short):** https://zh.wikipedia.org/wiki/黄龙镇_(北京市)
4. **Long Article:** https://zh.wikipedia.org/wiki/第二次世界大战
5. **Chinese Variants:**
   - Simplified: `?variant=zh-cn`
   - Traditional: `?variant=zh-tw`
   - Hong Kong: `?variant=zh-hk`

---

## Version History / 版本历史

- **v1.0 (2025-10-10):** Initial task creation
  - Analysis of current Wikipedia parsing issues
  - Requirements and technical approach defined
  - Estimated 6-8 hours for complete implementation

---

**Created By / 创建者:** Archy Principle Architect
**Date / 日期:** 2025-10-10
**Status / 状态:** Ready for execution / 准备执行
**Prerequisite / 前置条件:** Task-001 (Parser Template Creator) completed ✅
