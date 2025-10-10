# Quick Start Guide / 快速上手指南

Get started with Parser Template Creator Tools in 5 minutes.

5分钟内开始使用解析模板创作工具。

## 30-Second Overview / 30秒概览

Create custom parsers for any website without writing code:

无需编写代码即可为任何网站创建自定义解析器：

1. **`init`** - Generate template / 生成模板
2. **`validate`** - Check it's valid / 检查有效性
3. **`preview`** - Test extraction / 测试提取
4. **`doc`** - Create documentation / 创建文档

## Your First Template / 你的第一个模板

### Step 1: Create Template / 创建模板

```bash
python scripts/template_tool.py init --domain myblog.com --type article
```

**Output:**
```
✓ Template created successfully!

Location: parser_engine/templates/sites/myblog_com/template.yaml
Type: article
Domain: myblog.com
```

### Step 2: Validate Template / 验证模板

```bash
python scripts/template_tool.py validate parser_engine/templates/sites/myblog_com/template.yaml
```

**Output:**
```
✓ Template is valid!

Template: parser_engine/templates/sites/myblog_com/template.yaml
Version: 2.0
Domain: myblog.com
```

### Step 3: You're Done! / 完成!

Your template is ready to use. The system will automatically load and use it when parsing pages from `myblog.com`.

模板已准备就绪。系统将在解析来自 `myblog.com` 的页面时自动加载和使用它。

## Customize Your Template / 自定义模板

### Edit Selectors / 编辑选择器

Open the generated template file and customize selectors:

打开生成的模板文件并自定义选择器：

```yaml
# parser_engine/templates/sites/myblog_com/template.yaml

selectors:
  # Change these to match your site's HTML structure
  # 更改这些以匹配你网站的HTML结构
  title: "h1.post-title"           # Article title
  author: "span.author-name"       # Author name
  published_date: "time.published" # Publication date
  content: "div.post-content"      # Main content
```

### How to Find Selectors / 如何找到选择器

1. **Open the page in your browser** / 在浏览器中打开页面
2. **Right-click on the element** → **Inspect** / 右键点击元素 → 检查
3. **Copy the CSS selector** / 复制CSS选择器
4. **Paste into template** / 粘贴到模板

**Example:**
```
Browser shows: <h1 class="article-title">My Title</h1>
CSS Selector: h1.article-title
Template:     title: "h1.article-title"
```

## Test Your Template / 测试模板

### Preview Extraction / 预览提取

```bash
# Save a sample HTML file from the website
# Then preview what will be extracted
python scripts/template_tool.py preview \
  --template parser_engine/templates/sites/myblog_com/template.yaml \
  --html sample.html \
  --output text
```

**Output:**
```
Preview Extraction Results
==================================================

Extracted Fields:
--------------------------------------------------
title: "My Blog Post Title"
author: "John Doe"
published_date: "2025-10-10"
content: "This is the blog post content..."

Total fields extracted: 4
```

### Different Output Formats / 不同输出格式

```bash
# JSON format
python scripts/template_tool.py preview --template <template> --html <file> --output json

# YAML format
python scripts/template_tool.py preview --template <template> --html <file> --output yaml

# Text format (default)
python scripts/template_tool.py preview --template <template> --html <file> --output text
```

## Generate Documentation / 生成文档

```bash
python scripts/template_tool.py doc \
  --template parser_engine/templates/sites/myblog_com/template.yaml \
  --output docs/templates/ \
  --format markdown
```

**Output:**
```
✓ Documentation generated successfully!

Output: docs/templates/myblog_com.md
Size: 2.1 KB
```

## Template Types / 模板类型

### Article Template / 文章模板

For blog posts, news articles, documentation pages.

用于博客文章、新闻文章、文档页面。

```bash
python scripts/template_tool.py init --domain site.com --type article
```

**Default fields:** title, author, published_date, content, tags, images

### List Template / 列表模板

For category pages, search results, archives.

用于分类页面、搜索结果、存档页面。

```bash
python scripts/template_tool.py init --domain site.com --type list
```

**Default fields:** items (with title, url, summary, image for each)

### Generic Template / 通用模板

For any other page type.

用于任何其他页面类型。

```bash
python scripts/template_tool.py init --domain site.com --type generic
```

**Default fields:** title, content

## Common Patterns / 常见模式

### Multiple URL Patterns / 多个URL模式

```yaml
page_types:
  article:
    url_pattern:
      - "*/article/*"
      - "*/post/*"
      - "*/blog/*"
```

### Optional Fields / 可选字段

```yaml
selectors:
  title: "h1"           # Required - will always try to extract
  author: "span.author" # Will extract if present, skip if not
```

### Multiple Elements / 多个元素

```yaml
selectors:
  tags: "a.tag"        # Will extract all matching elements as a list
  images: "img.photo"  # All images will be extracted
```

### Nested Content / 嵌套内容

```yaml
selectors:
  # Direct child
  main_image: "article > img:first-child"

  # Descendant
  paragraphs: "div.content p"

  # Adjacent sibling
  subtitle: "h1 + h2"
```

## Troubleshooting / 故障排除

### Problem: Preview returns empty / 预览返回空结果

**Solution 1:** Check your selectors in browser dev tools

**Solution 2:** Verify HTML file contains the expected content

**Solution 3:** Try simpler selectors first
```yaml
# Instead of: "article > div.content > p.text"
# Try: "p.text"
```

### Problem: Validation fails / 验证失败

**Solution:** Read the error message carefully
```
✗ Template validation failed!
Errors:
  - selectors.title: Missing required field

# Fix: Add 'title' field to selectors
```

### Problem: Some fields not extracted / 某些字段未提取

**Solution:** Test each selector individually
1. Comment out all selectors except one
2. Run preview
3. If it works, uncomment next selector
4. Repeat until you find the problematic selector

## Next Steps / 下一步

### For More Details / 获取更多详细信息

Read the full documentation:
- [README.md](README.md) - Complete documentation
- [Template Schema](../templates/template.schema.yaml) - Schema reference

### Advanced Usage / 高级使用

```bash
# Validate all templates
find parser_engine/templates -name "template.yaml" -exec python scripts/template_tool.py validate {} \;

# Generate docs for all templates
for template in parser_engine/templates/sites/*/template.yaml; do
  python scripts/template_tool.py doc --template "$template" --output docs/templates/
done
```

### Integration with Fetcher / 与Fetcher集成

The templates work automatically with the fetcher:

模板自动与fetcher配合工作：

```python
from fetcher import fetch_content

# The system will automatically:
# 1. Detect the domain
# 2. Load the matching template
# 3. Extract content using template selectors
result = fetch_content("https://myblog.com/article/123")

print(result['title'])  # Extracted using your template
```

## Cheat Sheet / 速查表

```bash
# Create template
python scripts/template_tool.py init --domain <domain> --type <type>

# Validate template
python scripts/template_tool.py validate <template.yaml>

# Preview extraction
python scripts/template_tool.py preview --template <template> --html <file>

# Generate docs
python scripts/template_tool.py doc --template <template> --output <dir>
```

## Examples / 示例

### Example 1: News Site / 新闻网站

```bash
# 1. Create template
python scripts/template_tool.py init --domain news.example.com --type article

# 2. Edit selectors (use browser dev tools to find them)
# title: "h1.headline"
# author: "div.byline span.name"
# published_date: "time[datetime]"
# content: "div.article-body"

# 3. Test with sample HTML
python scripts/template_tool.py preview \
  --template parser_engine/templates/sites/news_example_com/template.yaml \
  --html news_sample.html
```

### Example 2: Blog Platform / 博客平台

```bash
# 1. Create template
python scripts/template_tool.py init --domain blog.example.com --type article

# 2. Customize for blog structure
# title: "h1.entry-title"
# author: "a.author-link"
# published_date: "time.entry-date"
# content: "div.entry-content"
# tags: "a.tag-link"

# 3. Validate
python scripts/template_tool.py validate \
  parser_engine/templates/sites/blog_example_com/template.yaml
```

### Example 3: Documentation Site / 文档网站

```bash
# 1. Create generic template
python scripts/template_tool.py init --domain docs.example.com --type generic

# 2. Set up documentation-specific selectors
# title: "h1#page-title"
# content: "article.doc-content"
# toc: "nav.table-of-contents a"

# 3. Generate documentation
python scripts/template_tool.py doc \
  --template parser_engine/templates/sites/docs_example_com/template.yaml \
  --output docs/templates/
```

## Tips / 提示

1. **Start Simple** - Begin with basic selectors, refine later
   从简单开始 - 从基本选择器开始，稍后优化

2. **Test Often** - Use preview after each change
   经常测试 - 每次更改后使用预览

3. **Use Browser Tools** - Dev tools are your best friend
   使用浏览器工具 - 开发工具是你最好的朋友

4. **Document Selectors** - Add comments for complex selectors
   记录选择器 - 为复杂选择器添加注释

5. **Version Control** - Track template changes with git
   版本控制 - 用git跟踪模板更改

---

**Ready to create your first template? Let's go!**

**准备好创建你的第一个模板了吗？开始吧！**

```bash
python scripts/template_tool.py init --domain your-site.com --type article
```
