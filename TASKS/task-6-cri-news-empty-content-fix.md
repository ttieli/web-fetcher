# Task-6: CRI News Empty Content Fix / 国际在线新闻空内容问题修复

**Task ID:** Task-6
**Priority:** P2 (Important) / P2（重要）
**Status:** 📋 **PENDING** / 待办
**Created:** 2025-10-10
**Estimated Effort:** 2-3 hours / 预计工时：2-3小时

---

## Problem Statement / 问题描述

### English

When scraping articles from China Radio International (CRI) News (`news.cri.cn`), the system successfully fetches the HTML but extracts **zero content**, resulting in markdown files with only metadata (title, author, source) and no article body.

**Example URL:**
```
https://news.cri.cn/20251010/fa71e5ca-4e5b-eb61-fd34-e3ff1a7955d8.html
```

**Expected:** Full article text about "携手为人类命运共同体撑起辽远发展天空——写在全球妇女峰会即将在北京举行之际"
**Actual:** Empty content (26 lines of metadata only)

### 中文

从国际在线新闻网站（China Radio International，`news.cri.cn`）抓取文章时，系统成功获取HTML但**提取内容为零**，导致Markdown文件中只有元数据（标题、作者、来源）而无正文内容。

**示例URL：**
```
https://news.cri.cn/20251010/fa71e5ca-4e5b-eb61-fd34-e3ff1a7955d8.html
```

**预期：** 关于"携手为人类命运共同体撑起辽远发展天空——写在全球妇女峰会即将在北京举行之际"的完整文章文本
**实际：** 空内容（仅26行元数据）

---

## Root Cause Analysis / 根本原因分析

### English

**Investigation Results:**

1. **HTML Fetching: ✅ Success**
   - Method: urllib (0.362s)
   - Status: 200 OK
   - Encoding: GB2312 (Chinese text readable)
   - Content exists in HTML

2. **Content Exists in HTML: ✅ Confirmed**
   ```html
   <div class="list-title" id="atitle">
       新华社政论｜携手为人类命运共同体撑起辽远发展天空——写在全球妇女峰会即将在北京举行之际
   </div>

   <div class="list-brief">
       <span id="apublishtime" class="apublishtime span-first">2025-10-10 08:36:25</span>
       <span id="asource" class="asource">来源：<a href="...">新华网</a></span>
       <span id="aeditor" class="aeditor">编辑：韩基韬</span>
   </div>

   <div class="list-abody abody" id="abody" pageData=''>
       <p>　　新华社北京10月9日电 <strong>题：携手为人类命运共同体撑起辽远发展天空...</strong></p>
       <p>　　新华社政论</p>
       <p>　　<strong>（一）</strong></p>
       <p>　　这是一双创造历史的手，也是一双托举文明的手。</p>
       <!-- Full article content present with 10+ paragraphs -->
   </div>
   ```

3. **Generic Web Template Failure: ❌ Root Cause**

   **What the template looks for (parser_engine/templates/generic.yaml:14-88):**
   - Title: `og:title`, `twitter:title`, `h1`, `.headline`, `.post-title` (but NOT `#atitle`)
   - Content: `article`, `main`, `.article-content`, `#article-content` (but NOT `#abody`)

   **What CRI News actually has:**
   - Title: `#atitle` (unique ID selector)
   - Content: `#abody` (unique ID selector)
   - Additional metadata: `#apublishtime`, `#asource`, `#aeditor`

   **Why it failed:**
   - Generic template doesn't include `#atitle` or `#abody` ID selectors
   - CRI News uses unique naming convention not covered by common patterns
   - Same TemplateParser format issue as Task-5 (list-of-dict vs string format)

### 中文

**调查结果：**

1. **HTML抓取：✅ 成功**
   - 方法：urllib（0.362秒）
   - 状态：200 OK
   - 编码：GB2312（中文文本可读）
   - HTML中存在内容

2. **HTML中存在内容：✅ 已确认**
   ```html
   <div class="list-title" id="atitle">
       新华社政论｜携手为人类命运共同体撑起辽远发展天空——写在全球妇女峰会即将在北京举行之际
   </div>

   <div class="list-brief">
       <span id="apublishtime" class="apublishtime span-first">2025-10-10 08:36:25</span>
       <span id="asource" class="asource">来源：<a href="...">新华网</a></span>
       <span id="aeditor" class="aeditor">编辑：韩基韬</span>
   </div>

   <div class="list-abody abody" id="abody" pageData=''>
       <p>　　新华社北京10月9日电 <strong>题：携手为人类命运共同体撑起辽远发展天空...</strong></p>
       <p>　　新华社政论</p>
       <!-- 完整文章内容存在，包含10+个段落 -->
   </div>
   ```

3. **通用Web模板失败：❌ 根本原因**

   **模板查找的内容 (parser_engine/templates/generic.yaml:14-88)：**
   - 标题：`og:title`、`twitter:title`、`h1`、`.headline`、`.post-title`（但不包括`#atitle`）
   - 内容：`article`、`main`、`.article-content`、`#article-content`（但不包括`#abody`）

   **国际在线实际使用的：**
   - 标题：`#atitle`（独特的ID选择器）
   - 内容：`#abody`（独特的ID选择器）
   - 额外元数据：`#apublishtime`、`#asource`、`#aeditor`

   **失败原因：**
   - 通用模板不包含`#atitle`或`#abody` ID选择器
   - 国际在线使用的独特命名约定未被常见模式覆盖
   - 与Task-5相同的TemplateParser格式问题（列表字典 vs 字符串格式）

---

## Comparison with Task-5 (Rodong Sinmun) / 与Task-5对比（劳动新闻）

### English

| Aspect | Task-5 (Rodong Sinmun) | Task-6 (CRI News) | Similarity |
|--------|------------------------|-------------------|------------|
| **Site** | www.rodong.rep.kp | news.cri.cn | Different |
| **Root Cause** | Selector mismatch + TemplateParser format | Selector mismatch + TemplateParser format | ✅ Same |
| **Content Selector** | `#ContDIV` | `#abody` | ✅ Both use unique IDs |
| **Title Selector** | `p.TitleP` | `#atitle` | ✅ Both use unique selectors |
| **Encoding** | UTF-8 | GB2312 | Different |
| **Solution Applied** | Site-specific template (string format) | TBD | Similar approach needed |
| **Parser Format Issue** | List-of-dict doesn't work | List-of-dict doesn't work | ✅ Same underlying issue |

**Key Similarity:**
Both sites use **unique ID/class selectors** not covered by generic template's common patterns. Both are affected by TemplateParser's inability to parse list-of-dict format selectors.

### 中文

| 方面 | Task-5（劳动新闻） | Task-6（国际在线） | 相似性 |
|------|-------------------|-------------------|--------|
| **站点** | www.rodong.rep.kp | news.cri.cn | 不同 |
| **根本原因** | 选择器不匹配 + TemplateParser格式 | 选择器不匹配 + TemplateParser格式 | ✅ 相同 |
| **内容选择器** | `#ContDIV` | `#abody` | ✅ 都使用独特ID |
| **标题选择器** | `p.TitleP` | `#atitle` | ✅ 都使用独特选择器 |
| **编码** | UTF-8 | GB2312 | 不同 |
| **应用方案** | 站点专用模板（字符串格式） | 待定 | 需要类似方案 |
| **解析器格式问题** | 列表字典不工作 | 列表字典不工作 | ✅ 相同底层问题 |

**关键相似性：**
两个站点都使用通用模板常见模式未覆盖的**独特ID/类选择器**。都受到TemplateParser无法解析列表字典格式选择器的影响。

---

## Specific Requirements / 具体要求

### English

1. **Content Extraction Success**
   - Extract full article body from `#abody` container
   - Include all `<p>` tags with proper formatting
   - Preserve HTML entities (e.g., `&mdash;`, `&nbsp;`, `&ldquo;`, `&rdquo;`)

2. **Metadata Extraction**
   - Title from `#atitle`
   - Publish time from `#apublishtime`
   - Source from `#asource` (extract link text, e.g., "新华网")
   - Editor from `#aeditor`

3. **Encoding Handling**
   - Properly handle GB2312 encoding
   - Ensure no garbled Chinese characters in output
   - Convert to UTF-8 for markdown output

4. **Template Requirements**
   - Use STRING format selectors (TemplateParser compatible)
   - Domain-specific template: `parser_engine/templates/sites/cri_news/`
   - Priority: 100 (exact domain match)
   - Fallback to generic if template fails

### 中文

1. **内容提取成功**
   - 从`#abody`容器提取完整文章正文
   - 包含所有`<p>`标签及适当格式
   - 保留HTML实体（如`&mdash;`、`&nbsp;`、`&ldquo;`、`&rdquo;`）

2. **元数据提取**
   - 标题从`#atitle`
   - 发布时间从`#apublishtime`
   - 来源从`#asource`（提取链接文本，如"新华网"）
   - 编辑从`#aeditor`

3. **编码处理**
   - 正确处理GB2312编码
   - 确保输出无中文乱码
   - 转换为UTF-8用于markdown输出

4. **模板要求**
   - 使用STRING格式选择器（兼容TemplateParser）
   - 域专用模板：`parser_engine/templates/sites/cri_news/`
   - 优先级：100（精确域匹配）
   - 如模板失败则回退到通用

---

## Technical Solution / 技术方案

### English

**Option 1: Site-Specific Template (Recommended) ⭐**

**Pros:**
- ✅ Proven approach (Task-5 success with Rodong Sinmun)
- ✅ Immediate fix with 100% reliability
- ✅ No TemplateParser refactoring needed
- ✅ Isolated change, minimal risk

**Cons:**
- ❌ Creates 5th production template (scalability concern)
- ❌ Doesn't solve underlying TemplateParser issue
- ❌ Template proliferation technical debt

**Implementation:**
```yaml
# parser_engine/templates/sites/cri_news/cri_news.yaml
name: "CRI News Articles"
version: "1.0.0"
domains:
  - "news.cri.cn"
  - "gb.cri.cn"
priority: 100

selectors:
  title: "#atitle, meta[property='og:title']@content, title"
  content: "#abody, .list-abody"

metadata:
  publish_time:
    - "#apublishtime"
  source:
    - "#asource a"
  editor:
    - "#aeditor"
```

**Option 2: TemplateParser Refactoring (Long-term)**

Refactor TemplateParser to support list-of-dict format, then enhance generic.yaml with:
```yaml
content:
  - selector: "#abody"
    strategy: "css"
```

**Effort:** 4-6 hours
**Risk:** Higher (affects all templates)
**Benefit:** Solves root cause for all future sites

### 中文

**方案1：站点专用模板（推荐）⭐**

**优点：**
- ✅ 已验证方法（Task-5劳动新闻成功）
- ✅ 立即修复，100%可靠
- ✅ 无需TemplateParser重构
- ✅ 隔离变更，风险最小

**缺点：**
- ❌ 创建第5个生产模板（可扩展性担忧）
- ❌ 未解决底层TemplateParser问题
- ❌ 模板泛滥技术债务

**实施：**
```yaml
# parser_engine/templates/sites/cri_news/cri_news.yaml
name: "CRI News Articles"
version: "1.0.0"
domains:
  - "news.cri.cn"
  - "gb.cri.cn"
priority: 100

selectors:
  title: "#atitle, meta[property='og:title']@content, title"
  content: "#abody, .list-abody"

metadata:
  publish_time:
    - "#apublishtime"
  source:
    - "#asource a"
  editor:
    - "#aeditor"
```

**方案2：TemplateParser重构（长期）**

重构TemplateParser以支持列表字典格式，然后增强generic.yaml：
```yaml
content:
  - selector: "#abody"
    strategy: "css"
```

**工时：** 4-6小时
**风险：** 较高（影响所有模板）
**收益：** 解决所有未来站点的根本原因

---

## Estimated Effort / 预计工时

### English

**Option 1: Site-Specific Template (Recommended)**
- Template creation: 0.5 hours
- Testing and validation: 0.5 hours
- Documentation: 0.5 hours
- Routing configuration: 0.25 hours
- Git commit: 0.25 hours
- **Total: 2 hours**

**Option 2: TemplateParser Refactoring**
- TemplateParser code analysis: 1 hour
- Format parser refactoring: 2-3 hours
- Testing all existing templates: 1 hour
- Regression testing: 1 hour
- Documentation: 0.5 hours
- **Total: 5.5-6.5 hours**

### 中文

**方案1：站点专用模板（推荐）**
- 模板创建：0.5小时
- 测试和验证：0.5小时
- 文档编写：0.5小时
- 路由配置：0.25小时
- Git提交：0.25小时
- **总计：2小时**

**方案2：TemplateParser重构**
- TemplateParser代码分析：1小时
- 格式解析器重构：2-3小时
- 测试所有现有模板：1小时
- 回归测试：1小时
- 文档编写：0.5小时
- **总计：5.5-6.5小时**

---

## Acceptance Criteria / 验收标准

### English

**Content Quality:**
- ✅ Article body: >10 paragraphs extracted from `#abody`
- ✅ Title: Exact match from `#atitle`
- ✅ Metadata: publish_time, source, editor all present
- ✅ Chinese encoding: No garbled characters
- ✅ Output size: >100 lines (vs 26 empty lines before)

**Functional Requirements:**
- ✅ Template loads successfully (appears in loader.list_templates())
- ✅ Routing selects correct template (priority 100 match)
- ✅ Parser returns complete content
- ✅ Markdown formatting: proper headings, paragraphs, emphasis

**Quality Metrics:**
| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| **Article Lines** | 0 | >100 | wc -l output.md |
| **Content Characters** | 0 | >2000 | Content extraction count |
| **Parse Success** | 0% | 100% | Test with 3+ URLs |
| **Chinese Encoding** | N/A | Perfect | Visual inspection |

### 中文

**内容质量：**
- ✅ 文章正文：从`#abody`提取>10个段落
- ✅ 标题：从`#atitle`精确匹配
- ✅ 元数据：发布时间、来源、编辑全部存在
- ✅ 中文编码：无乱码字符
- ✅ 输出大小：>100行（vs 之前26行空内容）

**功能要求：**
- ✅ 模板成功加载（出现在loader.list_templates()中）
- ✅ 路由选择正确模板（优先级100匹配）
- ✅ 解析器返回完整内容
- ✅ Markdown格式：适当的标题、段落、强调

**质量指标：**
| 指标 | 优化前 | 目标 | 测量方法 |
|-----|-------|------|---------|
| **文章行数** | 0 | >100 | wc -l output.md |
| **内容字符数** | 0 | >2000 | 内容提取计数 |
| **解析成功率** | 0% | 100% | 用3+个URL测试 |
| **中文编码** | N/A | 完美 | 视觉检查 |

---

## HTML Structure Analysis / HTML结构分析

### English

```html
<!-- CRI News Article Structure -->
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=gb2312" />
    <title>新华社政论｜携手为人类命运共同体撑起辽远发展天空...</title>
    <meta name="keywords" content="" />
    <meta name="description" content="新华社北京10月9日电题：携手为人类命运共同体..." />
</head>
<body>
    <!-- Navigation omitted -->

    <!-- Article Container -->
    <div class="list-title" id="atitle">
        新华社政论｜携手为人类命运共同体撑起辽远发展天空——写在全球妇女峰会即将在北京举行之际
    </div>

    <!-- Metadata -->
    <div class="list-brief">
        <span id="apublishtime" class="apublishtime span-first">2025-10-10 08:36:25</span>
        <span id="asource" class="asource">来源：<a href="..." target="_blank">新华网</a></span>
        <span id="aeditor" class="aeditor">编辑：韩基韬</span>
    </div>

    <!-- Article Body -->
    <div class="list-abody abody" id="abody" pageData=''>
        <p>　　新华社北京10月9日电 <strong>题：携手为人类命运共同体撑起辽远发展天空...</strong></p>
        <p>　　新华社政论</p>
        <p>　　<strong>（一）</strong></p>
        <p>　　这是一双创造历史的手，也是一双托举文明的手。</p>
        <p>　　苏美尔文明晨曦里，她们摸索出通过发酵谷物酿制美酒的复杂技艺...</p>
        <!-- 10+ more paragraphs -->
    </div>
</body>
</html>
```

### 中文

```html
<!-- 国际在线文章结构 -->
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=gb2312" />
    <title>新华社政论｜携手为人类命运共同体撑起辽远发展天空...</title>
    <meta name="keywords" content="" />
    <meta name="description" content="新华社北京10月9日电题：携手为人类命运共同体..." />
</head>
<body>
    <!-- 导航略 -->

    <!-- 文章容器 -->
    <div class="list-title" id="atitle">
        新华社政论｜携手为人类命运共同体撑起辽远发展天空——写在全球妇女峰会即将在北京举行之际
    </div>

    <!-- 元数据 -->
    <div class="list-brief">
        <span id="apublishtime" class="apublishtime span-first">2025-10-10 08:36:25</span>
        <span id="asource" class="asource">来源：<a href="..." target="_blank">新华网</a></span>
        <span id="aeditor" class="aeditor">编辑：韩基韬</span>
    </div>

    <!-- 文章正文 -->
    <div class="list-abody abody" id="abody" pageData=''>
        <p>　　新华社北京10月9日电 <strong>题：携手为人类命运共同体撑起辽远发展天空...</strong></p>
        <p>　　新华社政论</p>
        <p>　　<strong>（一）</strong></p>
        <p>　　这是一双创造历史的手，也是一双托举文明的手。</p>
        <p>　　苏美尔文明晨曦里，她们摸索出通过发酵谷物酿制美酒的复杂技艺...</p>
        <!-- 10+个段落 -->
    </div>
</body>
</html>
```

---

## Key CSS Selectors / 关键CSS选择器

| Selector | Purpose | Extract? | Notes |
|----------|---------|----------|-------|
| `#atitle` | Article title | ✅ Yes | Main title container |
| `#abody` | Article body | ✅ Yes | Main content target |
| `.list-abody` | Article body (class) | ✅ Yes | Fallback selector |
| `#apublishtime` | Publish time | ✅ Yes | Metadata |
| `#asource` | Source/origin | ✅ Yes | Metadata (extract link text) |
| `#aeditor` | Editor name | ✅ Yes | Metadata |
| `.list-brief` | Metadata container | ❌ No | Parent container only |

---

## Testing URLs / 测试URL

### English

```bash
# Test URL 1: Xinhua editorial (current issue)
https://news.cri.cn/20251010/fa71e5ca-4e5b-eb61-fd34-e3ff1a7955d8.html

# Test URL 2-3: Additional articles for regression testing
# (To be collected during implementation)
```

### 中文

```bash
# 测试URL 1：新华社政论（当前问题）
https://news.cri.cn/20251010/fa71e5ca-4e5b-eb61-fd34-e3ff1a7955d8.html

# 测试URL 2-3：回归测试的额外文章
# （实施期间收集）
```

---

## Related Tasks / 相关任务

- **Task-5:** Rodong Sinmun Empty Content Fix (similar issue, same TemplateParser limitation)
- **Task-4:** Wikipedia Parser Optimization (template pattern reference)
- **Task-1:** Parser Template Creator Tools (template creation workflow)

---

## Implementation Notes / 实施说明

### English

**Encoding Considerations:**
- CRI News uses GB2312 encoding (not UTF-8)
- BeautifulSoup should auto-detect encoding
- Ensure proper conversion to UTF-8 for markdown output

**TemplateParser Format:**
- MUST use string format: `"#abody, .list-abody"`
- NOT list-of-dict format: `- selector: "#abody"`
- This limitation discovered in Task-5

**Testing Strategy:**
1. Verify template loads (check loader.list_templates())
2. Test routing decision (verify priority 100 match)
3. Test content extraction (verify >100 lines output)
4. Test Chinese encoding (verify no garbled text)

### 中文

**编码考虑：**
- 国际在线使用GB2312编码（非UTF-8）
- BeautifulSoup应自动检测编码
- 确保正确转换为UTF-8用于markdown输出

**TemplateParser格式：**
- 必须使用字符串格式：`"#abody, .list-abody"`
- 不要使用列表字典格式：`- selector: "#abody"`
- 此限制在Task-5中发现

**测试策略：**
1. 验证模板加载（检查loader.list_templates()）
2. 测试路由决策（验证优先级100匹配）
3. 测试内容提取（验证>100行输出）
4. 测试中文编码（验证无乱码）

---

**Document Version:** 1.0
**Created By:** Architectural Analysis
**Analyst:** Claude Code (Sonnet 4.5)
**Review Status:** Ready for implementation
**Encoding:** UTF-8 (verified bilingual, no garbled text)
