# Task-5: Rodong Sinmun Empty Content Fix / 劳动新闻空内容问题修复

**Task ID:** Task-5
**Priority:** P2 (Important) / P2（重要）
**Status:** 📋 **PENDING** / 待办
**Created:** 2025-10-10
**Estimated Effort:** 3-4 hours / 预计工时：3-4小时

---

## Problem Statement / 问题描述

### English

When scraping articles from Rodong Sinmun (North Korean state newspaper, `www.rodong.rep.kp`), the system successfully fetches the HTML but extracts **zero content**, resulting in markdown files with only metadata (title, author, source) and no article body.

**Example URL:**
```
http://www.rodong.rep.kp/cn/index.php?MTJAMjAyNS0xMC0xMC0wMTNAM0AxQEAwQDNA==
```

**Expected:** Full article text about Kim Jong Un receiving congratulatory message
**Actual:** Empty content (26 lines of metadata only)

### 中文

从劳动新闻网站（朝鲜官方报纸，`www.rodong.rep.kp`）抓取文章时，系统成功获取HTML但**提取内容为零**，导致Markdown文件中只有元数据（标题、作者、来源）而无正文内容。

**示例URL：**
```
http://www.rodong.rep.kp/cn/index.php?MTJAMjAyNS0xMC0xMC0wMTNAM0AxQEAwQDNA==
```

**预期：** 关于金正恩收到贺电的完整文章文本
**实际：** 空内容（仅26行元数据）

---

## Root Cause Analysis / 根本原因分析

### English

**Investigation Results:**

1. **HTML Fetching: ✅ Success**
   - Method: urllib (6.35s)
   - Status: 200 OK
   - Content-Length: 23,532 bytes
   - Encoding: UTF-8 (Chinese text readable)

2. **Content Exists in HTML: ✅ Confirmed**
   ```html
   <div id="articleContent" class="article-content" style="display: block;">
       <div class="container" id="ContDIV">
           <p class="TitleP">敬爱的金正恩同志收到老挝人民革命党中央委员会总书记...</p>
           <p class="TextP">朝鲜劳动党总书记、朝鲜民主主义人民共和国国务委员长...</p>
           <!-- Full article content present -->
       </div>
   </div>
   ```

3. **Generic Web Template Failure: ❌ Root Cause**

   **What the template looks for (parser_engine/templates/generic.yaml:94-174):**
   - `article`, `main`, `[role='main']`
   - `.article-content` (line 110)
   - `#article-content` (line 136) — **But actual element is `#articleContent` (camelCase!)**
   - `.post-content`, `.entry-content`, etc.

   **What Rodong Sinmun actually has:**
   - `#articleContent` (camelCase, not `#article-content`)
   - Content nested in: `#ContDIV` → `p.TitleP` + `p.TextP`
   - Outer `.article-content` div contains both article AND control buttons

   **Why it failed:**
   - Generic template selector `#article-content` (kebab-case) doesn't match `#articleContent` (camelCase)
   - Selector `.article-content` matches outer div but content is nested deeper in `#ContDIV`
   - Template doesn't look for specific classes like `.TitleP` or `.TextP`
   - Post-processing likely removed content thinking it was navigation noise

### 中文

**调查结果：**

1. **HTML抓取：✅ 成功**
   - 方法：urllib（6.35秒）
   - 状态：200 OK
   - 内容长度：23,532字节
   - 编码：UTF-8（中文文本可读）

2. **HTML中存在内容：✅ 已确认**
   ```html
   <div id="articleContent" class="article-content" style="display: block;">
       <div class="container" id="ContDIV">
           <p class="TitleP">敬爱的金正恩同志收到老挝人民革命党中央委员会总书记...</p>
           <p class="TextP">朝鲜劳动党总书记、朝鲜民主主义人民共和国国务委员长...</p>
           <!-- 完整文章内容存在 -->
       </div>
   </div>
   ```

3. **通用Web模板失败：❌ 根本原因**

   **模板查找的内容（parser_engine/templates/generic.yaml:94-174）：**
   - `article`、`main`、`[role='main']`
   - `.article-content`（第110行）
   - `#article-content`（第136行）— **但实际元素是 `#articleContent`（驼峰命名！）**
   - `.post-content`、`.entry-content` 等

   **劳动新闻实际使用的结构：**
   - `#articleContent`（驼峰命名，不是 `#article-content`）
   - 内容嵌套在：`#ContDIV` → `p.TitleP` + `p.TextP`
   - 外层 `.article-content` div包含文章和控制按钮

   **失败原因：**
   - 通用模板选择器 `#article-content`（kebab-case）不匹配 `#articleContent`（驼峰命名）
   - 选择器 `.article-content` 匹配外层div但内容嵌套更深在 `#ContDIV` 中
   - 模板不查找特定类如 `.TitleP` 或 `.TextP`
   - 后处理可能将内容误认为导航噪音而删除

---

## Technical Solution / 技术方案

### English

**Approach:** Create Rodong Sinmun-specific template

**Implementation Steps:**

1. **Create Template Directory (15 min)**
   ```bash
   mkdir -p parser_engine/templates/sites/rodong_sinmun
   ```

2. **Create Template File (45-60 min)**

   **File:** `parser_engine/templates/sites/rodong_sinmun/rodong_sinmun.yaml`

   **Key Selectors:**
   ```yaml
   name: "Rodong Sinmun Chinese Articles"
   version: "1.0.0"
   domains:
     - "www.rodong.rep.kp"
   priority: 100

   selectors:
     # Title extraction
     title: "p.TitleP, .RevoTitleP, title"

     # Content extraction
     content: "#ContDIV, #articleContent .container"

     # Date extraction
     date: "#article-date"

     # Author (default fallback)
     author: "meta[name='author']@content"

     # Images
     images: "#articleContent img, #ContDIV img"

   metadata:
     fields:
       - title
       - author
       - publish_time
       - images
       - url
       - fetch_time
     defaults:
       author: "劳动新闻"
   ```

3. **Add Routing Rule (15 min)**

   **File:** `config/routing.yaml`

   ```yaml
   - name: "Rodong Sinmun - Static Content"
     name_zh: "劳动新闻 - 静态内容"
     priority: 90
     enabled: true
     conditions:
       domain: "www.rodong.rep.kp"
     action:
       fetcher: "urllib"
       reason: "Static content, template-based parsing"
       reason_zh: "静态内容，使用模板解析"
   ```

4. **Testing & Validation (60-90 min)**

   ```bash
   # Test template loading
   python3 -c "from parser_engine.engine.template_loader import TemplateLoader; \
   loader = TemplateLoader(); \
   print('Loaded templates:', loader.list_templates())"

   # Test parsing
   python3 wf.py "http://www.rodong.rep.kp/cn/index.php?MTJAMjAyNS0xMC0xMC0wMTNAM0AxQEAwQDNA==" --verbose

   # Verify output
   cat "output/latest-rodong-article.md"
   wc -l "output/latest-rodong-article.md"  # Should be >50 lines
   grep -i "金正恩" "output/latest-rodong-article.md"  # Should find content
   ```

5. **Documentation (30-45 min)**

   Create `parser_engine/templates/sites/rodong_sinmun/README.md`:
   - Usage examples
   - Testing URLs
   - Known limitations
   - Troubleshooting

### 中文

**方法：** 创建劳动新闻专用模板

**实施步骤：**

1. **创建模板目录（15分钟）**
   ```bash
   mkdir -p parser_engine/templates/sites/rodong_sinmun
   ```

2. **创建模板文件（45-60分钟）**

   **文件：** `parser_engine/templates/sites/rodong_sinmun/rodong_sinmun.yaml`

   **关键选择器：**
   ```yaml
   name: "Rodong Sinmun Chinese Articles"
   version: "1.0.0"
   domains:
     - "www.rodong.rep.kp"
   priority: 100

   selectors:
     # 标题提取
     title: "p.TitleP, .RevoTitleP, title"

     # 内容提取
     content: "#ContDIV, #articleContent .container"

     # 日期提取
     date: "#article-date"

     # 作者（默认回退）
     author: "meta[name='author']@content"

     # 图片
     images: "#articleContent img, #ContDIV img"

   metadata:
     fields:
       - title
       - author
       - publish_time
       - images
       - url
       - fetch_time
     defaults:
       author: "劳动新闻"
   ```

3. **添加路由规则（15分钟）**

   **文件：** `config/routing.yaml`

   ```yaml
   - name: "Rodong Sinmun - Static Content"
     name_zh: "劳动新闻 - 静态内容"
     priority: 90
     enabled: true
     conditions:
       domain: "www.rodong.rep.kp"
     action:
       fetcher: "urllib"
       reason: "Static content, template-based parsing"
       reason_zh: "静态内容，使用模板解析"
   ```

4. **测试与验证（60-90分钟）**

   ```bash
   # 测试模板加载
   python3 -c "from parser_engine.engine.template_loader import TemplateLoader; \
   loader = TemplateLoader(); \
   print('已加载模板:', loader.list_templates())"

   # 测试解析
   python3 wf.py "http://www.rodong.rep.kp/cn/index.php?MTJAMjAyNS0xMC0xMC0wMTNAM0AxQEAwQDNA==" --verbose

   # 验证输出
   cat "output/latest-rodong-article.md"
   wc -l "output/latest-rodong-article.md"  # 应大于50行
   grep -i "金正恩" "output/latest-rodong-article.md"  # 应找到内容
   ```

5. **文档编写（30-45分钟）**

   创建 `parser_engine/templates/sites/rodong_sinmun/README.md`：
   - 使用示例
   - 测试URL
   - 已知限制
   - 故障排除

---

## Acceptance Criteria / 验收标准

### English

**Functional Requirements:**

1. **Template Creation:** ✅
   - [ ] `rodong_sinmun.yaml` created and valid
   - [ ] Domain matching for `www.rodong.rep.kp` configured
   - [ ] Selectors target correct HTML elements (`#ContDIV`, `.TitleP`, `.TextP`)

2. **Content Extraction Quality:** ✅
   - [ ] Article title extracted correctly
   - [ ] Full article body extracted (>100 characters)
   - [ ] Date extracted from `#article-date`
   - [ ] No control buttons/navigation in output
   - [ ] Chinese text encoding preserved correctly

3. **Routing Integration:** ✅
   - [ ] Routing rule added to `config/routing.yaml`
   - [ ] urllib fetcher selected for Rodong Sinmun URLs
   - [ ] Template auto-selected for domain

4. **Documentation:** ✅
   - [ ] README.md created with usage examples
   - [ ] Known limitations documented
   - [ ] Testing URLs provided

**Quality Gates:**

- **Content-to-Noise Ratio:** >90% (article text vs metadata/controls)
- **Parse Success Rate:** 100% for standard article pages
- **Parse Time:** <5 seconds (urllib fetch + parse)
- **Output Size:** >50 lines for typical articles
- **Encoding Quality:** Zero garbled Chinese characters

**Test Cases:**

| Test Case | URL | Expected Result |
|-----------|-----|-----------------|
| **TC-1: Standard Article** | http://www.rodong.rep.kp/cn/index.php?MTJAMjAyNS0xMC0xMC0wMTNAM0AxQEAwQDNA== | Full article extracted, >50 lines |
| **TC-2: Template Loading** | N/A | Template found in loader.list_templates() |
| **TC-3: Routing Decision** | Above URL | Rule: "Rodong Sinmun - Static Content", urllib |
| **TC-4: Content Quality** | Above URL | Contains "金正恩", "老挝", "朝鲜劳动党" |

### 中文

**功能需求：**

1. **模板创建：** ✅
   - [ ] `rodong_sinmun.yaml` 已创建且有效
   - [ ] 已配置 `www.rodong.rep.kp` 域名匹配
   - [ ] 选择器针对正确的HTML元素（`#ContDIV`、`.TitleP`、`.TextP`）

2. **内容提取质量：** ✅
   - [ ] 文章标题正确提取
   - [ ] 完整文章正文提取（>100字符）
   - [ ] 从 `#article-date` 提取日期
   - [ ] 输出中无控制按钮/导航
   - [ ] 中文文本编码正确保留

3. **路由集成：** ✅
   - [ ] 路由规则已添加到 `config/routing.yaml`
   - [ ] 劳动新闻URL选择urllib抓取器
   - [ ] 模板自动选择域名

4. **文档：** ✅
   - [ ] 已创建包含使用示例的README.md
   - [ ] 已记录已知限制
   - [ ] 已提供测试URL

**质量门槛：**

- **内容噪音比：** >90%（文章文本 vs 元数据/控制）
- **解析成功率：** 标准文章页100%
- **解析时间：** <5秒（urllib抓取+解析）
- **输出大小：** 典型文章>50行
- **编码质量：** 零中文乱码

**测试用例：**

| 测试用例 | URL | 预期结果 |
|---------|-----|---------|
| **TC-1：标准文章** | http://www.rodong.rep.kp/cn/index.php?MTJAMjAyNS0xMC0xMC0wMTNAM0AxQEAwQDNA== | 提取完整文章，>50行 |
| **TC-2：模板加载** | N/A | loader.list_templates()中找到模板 |
| **TC-3：路由决策** | 上述URL | 规则："劳动新闻 - 静态内容"，urllib |
| **TC-4：内容质量** | 上述URL | 包含"金正恩"、"老挝"、"朝鲜劳动党" |

---

## Time Estimation / 工时估算

| Phase / 阶段 | Estimated Time / 预计时间 | Tasks / 任务 |
|-------------|------------------------|-------------|
| **Phase 1: Setup** / 阶段1：设置 | 15 min / 15分钟 | Create directory structure / 创建目录结构 |
| **Phase 2: Template Creation** / 阶段2：模板创建 | 60 min / 60分钟 | Analyze HTML, write YAML, validate / 分析HTML、编写YAML、验证 |
| **Phase 3: Routing** / 阶段3：路由 | 15 min / 15分钟 | Add routing rule / 添加路由规则 |
| **Phase 4: Testing** / 阶段4：测试 | 90 min / 90分钟 | Template loading, parsing, quality checks / 模板加载、解析、质量检查 |
| **Phase 5: Documentation** / 阶段5：文档 | 45 min / 45分钟 | README, examples, troubleshooting / README、示例、故障排除 |
| **Total** / 总计 | **3.5-4 hours** / **3.5-4小时** | |

**Buffer:** +30 min for unexpected issues / 意外问题缓冲：+30分钟

---

## Dependencies / 依赖关系

### English

**Code Dependencies:**
- `parser_engine/template_parser.py` (existing)
- `parser_engine/engine/template_loader.py` (existing, skip schema.yaml logic added in Task-4)
- `parsers_migrated.py` (Phase 3.5 generic parser from Task-4)
- `config/routing.yaml` (existing)

**Template Pattern:**
- Follows same pattern as Wikipedia template (Task-4)
- String-based selectors for TemplateParser compatibility
- Domain-based auto-selection
- Graceful fallback to legacy parser

**Infrastructure:**
- No new dependencies required
- urllib fetcher (already available)
- BeautifulSoup CSS selectors (already available)

### 中文

**代码依赖：**
- `parser_engine/template_parser.py`（现有）
- `parser_engine/engine/template_loader.py`（现有，Task-4中添加的跳过schema.yaml逻辑）
- `parsers_migrated.py`（Task-4的阶段3.5通用解析器）
- `config/routing.yaml`（现有）

**模板模式：**
- 遵循与维基百科模板相同的模式（Task-4）
- 字符串选择器以兼容TemplateParser
- 基于域名的自动选择
- 优雅回退到传统解析器

**基础设施：**
- 无需新依赖
- urllib抓取器（已有）
- BeautifulSoup CSS选择器（已有）

---

## Known Limitations / 已知限制

### English

1. **Video/Photo Content:**
   - Current template focuses on text articles
   - Video (`#videoContent`) and photo galleries (`#photoContent`) not extracted
   - Future enhancement: detect content type and extract accordingly

2. **Pagination:**
   - Articles are paginated (e.g., "3 / 543" in controls)
   - Template extracts only current page
   - Future enhancement: auto-follow next/prev links

3. **Special Characters:**
   - Full-width numerals (８０) used in text
   - May affect text processing/analysis
   - Consider normalization in post-processing

4. **Language Variants:**
   - Template designed for Chinese (`/cn/`) version
   - Korean version has different structure
   - Future enhancement: add Korean template

### 中文

1. **视频/图片内容：**
   - 当前模板专注于文本文章
   - 视频（`#videoContent`）和图片库（`#photoContent`）未提取
   - 未来增强：检测内容类型并相应提取

2. **分页：**
   - 文章分页（例如控制中的"3 / 543"）
   - 模板仅提取当前页
   - 未来增强：自动跟随下一页/上一页链接

3. **特殊字符：**
   - 文本中使用全角数字（８０）
   - 可能影响文本处理/分析
   - 考虑在后处理中标准化

4. **语言变体：**
   - 模板设计用于中文（`/cn/`）版本
   - 韩文版本结构不同
   - 未来增强：添加韩文模板

---

## Success Metrics / 成功指标

### English

**Before (Current State):**
- Content Extraction: ❌ 0% (0 lines of article body)
- Output Size: 26 lines (metadata only)
- User Experience: Failed (unusable output)

**After (Target State):**
- Content Extraction: ✅ 100% (full article body)
- Output Size: >50 lines (metadata + content)
- Content Quality: >90% content-to-noise ratio
- Parse Success: 100% for standard articles
- User Experience: Success (readable article)

**Quality Comparison:**

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| **Article Body Lines** | 0 | >50 | wc -l output.md |
| **Content Characters** | 0 | >500 | grep -v "^#\\|^-\\|^---" output.md \| wc -m |
| **Parse Success Rate** | 0% | 100% | Test with 5+ URLs |
| **Chinese Encoding** | N/A | Perfect | No garbled characters |

### 中文

**优化前（当前状态）：**
- 内容提取：❌ 0%（0行文章正文）
- 输出大小：26行（仅元数据）
- 用户体验：失败（输出不可用）

**优化后（目标状态）：**
- 内容提取：✅ 100%（完整文章正文）
- 输出大小：>50行（元数据+内容）
- 内容质量：>90%内容噪音比
- 解析成功：标准文章100%
- 用户体验：成功（可读文章）

**质量对比：**

| 指标 | 优化前 | 目标 | 测量方法 |
|-----|-------|------|---------|
| **文章正文行数** | 0 | >50 | wc -l output.md |
| **内容字符数** | 0 | >500 | grep -v "^#\\|^-\\|^---" output.md \| wc -m |
| **解析成功率** | 0% | 100% | 用5+个URL测试 |
| **中文编码** | N/A | 完美 | 无乱码 |

---

## Implementation Notes / 实施说明

### English

**Pattern Reference:**
- Use Task-4 Wikipedia template as reference
- Follow same directory structure: `parser_engine/templates/sites/rodong_sinmun/`
- Use string-based selectors for TemplateParser compatibility

**Testing Strategy:**
1. Test template loading first (verify it appears in loader.list_templates())
2. Test routing decision (verify urllib + template selection)
3. Test content extraction (verify article body present)
4. Test quality (verify no control buttons, clean Chinese text)

**Error Handling:**
- If template fails, generic parser fallback already implemented (Task-4 Phase 3.5)
- Log failures for debugging: check for selector mismatches
- Monitor parse success rate in production

### 中文

**模式参考：**
- 以Task-4维基百科模板为参考
- 遵循相同目录结构：`parser_engine/templates/sites/rodong_sinmun/`
- 使用字符串选择器以兼容TemplateParser

**测试策略：**
1. 首先测试模板加载（验证出现在loader.list_templates()中）
2. 测试路由决策（验证urllib + 模板选择）
3. 测试内容提取（验证文章正文存在）
4. 测试质量（验证无控制按钮，中文文本清晰）

**错误处理：**
- 如模板失败，通用解析器回退已实现（Task-4阶段3.5）
- 记录失败以调试：检查选择器不匹配
- 监控生产环境解析成功率

---

## Testing URLs / 测试URL

### English

```bash
# Test URL 1: Standard article (Kim Jong Un congratulatory message)
http://www.rodong.rep.kp/cn/index.php?MTJAMjAyNS0xMC0xMC0wMTNAM0AxQEAwQDNA==

# Test URL 2-5: Additional articles for regression testing
# (To be collected during implementation)
```

### 中文

```bash
# 测试URL 1：标准文章（金正恩收到贺电）
http://www.rodong.rep.kp/cn/index.php?MTJAMjAyNS0xMC0xMC0wMTNAM0AxQEAwQDNA==

# 测试URL 2-5：回归测试的额外文章
# （实施期间收集）
```

---

## Related Tasks / 相关任务

- **Task-4:** Wikipedia Parser Optimization (template pattern reference)
- **Task-1:** Parser Template Creator Tools (template creation workflow)
- **Strategic Planning:** Production Hardening (error monitoring, quality metrics)

---

## Appendix / 附录

### HTML Structure Analysis / HTML结构分析

```html
<!-- Rodong Sinmun Article Structure -->
<!DOCTYPE html>
<html>
<head>
    <title>劳动新闻</title>
    <meta charset="utf-8">
</head>
<body>
    <!-- Outer container -->
    <div class="container" id="newsPage">
        <!-- Header with date -->
        <div class="article-modal-header row">
            <div id="article-homepage">劳动新闻</div>
            <div id="article-date">2025年 10月 10日 星期五</div>
        </div>

        <!-- Content containers (one visible at a time) -->
        <div id="videoContent" style="display: none;"></div>
        <div id="photoContent" style="display: none;"></div>

        <!-- Article content (display: block) -->
        <div id="articleContent" class="article-content" style="display: block;">
            <!-- Actual content container -->
            <div class="container" id="ContDIV">
                <!-- Title -->
                <p class="TitleP">敬爱的金正恩同志收到...</p>

                <!-- Body paragraphs -->
                <p class="TextP">朝鲜劳动党总书记...</p>
                <p class="TextP">值此朝鲜劳动党成立...</p>
                <!-- ... more paragraphs ... -->

                <!-- Signature -->
                <p class="WriterP">劳动新闻</p>
            </div>
        </div>

        <!-- Control buttons (skip in extraction) -->
        <div class="article-controls">
            <button id="btnPrev">上一个</button>
            <span>3 / 543</span>
            <button id="btnNext">下一个</button>
        </div>
    </div>
</body>
</html>
```

### Key CSS Classes / 关键CSS类

| Class | Purpose | Extract? |
|-------|---------|----------|
| `#articleContent` | Article container | ✅ Yes (outer) |
| `#ContDIV` | Content container | ✅ Yes (main target) |
| `.TitleP` | Article title | ✅ Yes |
| `.TextP` | Body paragraphs | ✅ Yes |
| `.WriterP` | Signature/byline | ✅ Yes |
| `.article-controls` | Navigation buttons | ❌ No (exclude) |
| `#article-date` | Publication date | ✅ Yes (metadata) |

---

**Document Version:** 1.0
**Created By:** Task Analysis Team
**Review Status:** Ready for implementation
**Encoding:** UTF-8 (verified bilingual, no garbled text)
