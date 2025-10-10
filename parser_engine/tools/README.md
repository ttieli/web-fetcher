# Parser Template Creator Tools / 解析模板创作工具

A complete CLI toolchain for creating, validating, and managing parser templates without modifying core code.

一套完整的CLI工具链，用于创建、验证和管理解析器模板，无需修改核心代码。

## Features / 功能特性

- **Template Generation** - Create template scaffolding for article, list, or generic pages
- **Schema Validation** - Validate templates against schema with clear error messages
- **Preview Extraction** - Preview what content will be extracted from HTML
- **Auto Documentation** - Generate comprehensive Markdown documentation

- **模板生成** - 为文章、列表或通用页面创建模板脚手架
- **Schema验证** - 根据schema验证模板并提供清晰的错误消息
- **提取预览** - 预览将从HTML中提取的内容
- **自动文档** - 生成全面的Markdown文档

## Quick Start / 快速开始

### Installation / 安装

The tools are already integrated into the Web_Fetcher project. No additional installation required.

工具已集成到Web_Fetcher项目中，无需额外安装。

### Usage / 使用方法

#### 1. Create a New Template / 创建新模板

```bash
# Create an article template
python scripts/template_tool.py init --domain example.com --type article

# Create a list template
python scripts/template_tool.py init --domain site.com --type list

# Create a generic template
python scripts/template_tool.py init --domain generic.org --type generic

# Custom output path
python scripts/template_tool.py init --domain site.com --output /path/to/template.yaml
```

#### 2. Validate a Template / 验证模板

```bash
python scripts/template_tool.py validate path/to/template.yaml
```

#### 3. Preview Extraction / 预览提取

```bash
# Text format (default)
python scripts/template_tool.py preview --template <template> --html <file> --output text

# JSON format
python scripts/template_tool.py preview --template <template> --html <file> --output json

# YAML format
python scripts/template_tool.py preview --template <template> --html <file> --output yaml
```

#### 4. Generate Documentation / 生成文档

```bash
# Output to stdout
python scripts/template_tool.py doc --template <template> --format markdown

# Save to file
python scripts/template_tool.py doc --template <template> --output docs/ --format markdown
```

## Complete Workflow Example / 完整工作流程示例

```bash
# 1. Create a new template
python scripts/template_tool.py init --domain news.example.com --type article

# 2. Edit the template (customize selectors)
# Edit: parser_engine/templates/sites/news_example_com/template.yaml

# 3. Validate the template
python scripts/template_tool.py validate parser_engine/templates/sites/news_example_com/template.yaml

# 4. Test with sample HTML
python scripts/template_tool.py preview \
  --template parser_engine/templates/sites/news_example_com/template.yaml \
  --html sample.html \
  --output text

# 5. Generate documentation
python scripts/template_tool.py doc \
  --template parser_engine/templates/sites/news_example_com/template.yaml \
  --output docs/templates/ \
  --format markdown
```

## Command Reference / 命令参考

### init - Initialize Template / 初始化模板

Create a new template with default selectors based on type.

```bash
python scripts/template_tool.py init --domain <domain> --type <type> [--output <path>]
```

**Arguments:**
- `--domain`: Target domain (e.g., example.com)
- `--type`: Template type (article, list, generic)
- `--output`: Optional output path (default: parser_engine/templates/sites/{domain}/)

**Example Output:**
```
✓ Template created successfully!

Location: parser_engine/templates/sites/example_com/template.yaml
Type: article
Domain: example.com

Next steps:
1. Customize selectors in the template file
2. Validate: python scripts/template_tool.py validate <template>
3. Preview: python scripts/template_tool.py preview --template <template> --html <file>
```

### validate - Validate Template / 验证模板

Validate a template file against the schema.

```bash
python scripts/template_tool.py validate <template_file>
```

**Arguments:**
- `template_file`: Path to template YAML file

**Example Output:**
```
✓ Template is valid!

Template: parser_engine/templates/sites/example_com/template.yaml
Version: 2.0
Domain: example.com
Page Types: article
```

**Error Example:**
```
✗ Template validation failed!

Errors:
  - selectors.title: Missing required field
  - page_types.article.url_pattern: Must be a list

Fix these issues and run validation again.
```

### preview - Preview Extraction / 预览提取

Preview what content would be extracted from HTML.

```bash
python scripts/template_tool.py preview --template <template> --html <file> [--output <format>]
```

**Arguments:**
- `--template`: Path to template file
- `--html`: Path to HTML file
- `--output`: Output format (text, json, yaml)

**Example Output (text format):**
```
Preview Extraction Results
==================================================

Domain: example.com
Page Type: article

Extracted Fields:
--------------------------------------------------
title: "Example Article Title"
author: "John Doe"
published_date: "2025-10-10"
content: "This is the article content..."

--------------------------------------------------
Total fields extracted: 4
```

**Example Output (json format):**
```json
{
  "domain": "example.com",
  "page_type": "article",
  "extracted_data": {
    "title": "Example Article Title",
    "author": "John Doe",
    "published_date": "2025-10-10",
    "content": "This is the article content..."
  }
}
```

### doc - Generate Documentation / 生成文档

Generate documentation from a template.

```bash
python scripts/template_tool.py doc --template <template> [--output <dir>] [--format <format>]
```

**Arguments:**
- `--template`: Path to template file
- `--output`: Output directory (if not specified, prints to stdout)
- `--format`: Documentation format (markdown)

**Example Output:**
```
✓ Documentation generated successfully!

Template: parser_engine/templates/sites/example_com/template.yaml
Output: docs/templates/example_com.md
Format: markdown
Size: 2.3 KB
```

## Architecture / 架构

```
parser_engine/tools/
├── cli/
│   ├── __init__.py          # Schema loading and shared constants
│   └── template_cli.py      # Main CLI implementation
├── generators/
│   ├── template_generator.py # Template scaffolding generation
│   └── doc_generator.py     # Documentation generation
├── validators/
│   ├── schema_validator.py  # Template schema validation
│   └── output_validator.py  # Output consistency checking
└── preview/
    └── html_preview.py      # HTML extraction preview
```

### Component Details / 组件详情

#### CLI Layer / CLI层

**template_cli.py** - Main command-line interface
- Parses arguments and routes to appropriate handlers
- Provides user-friendly output and error messages
- Handles file I/O and path resolution

#### Generators / 生成器

**template_generator.py** - Template scaffolding creation
- Generates YAML templates with default selectors
- Supports article, list, and generic page types
- Creates proper directory structure

**doc_generator.py** - Documentation generation
- Converts templates to Markdown documentation
- Includes selector examples and usage notes
- Supports bilingual output (EN/CN)

#### Validators / 验证器

**schema_validator.py** - Schema validation
- Validates templates against template.schema.yaml
- Provides detailed error messages with field paths
- Checks required fields, types, and formats

**output_validator.py** - Output consistency checking
- Ensures extracted data matches expected schema
- Validates field presence and data types
- Reports missing or malformed data

#### Preview / 预览

**html_preview.py** - Extraction preview
- Applies template selectors to HTML
- Extracts content without saving
- Supports multiple output formats (text, json, yaml)

## Template Structure / 模板结构

### Minimal Template / 最小模板

```yaml
version: "2.0"
domain: "example.com"

page_types:
  article:
    url_pattern: ["*/article/*"]
    selectors:
      title: "h1.title"
      content: "div.content"
```

### Full Template / 完整模板

```yaml
version: "2.0"
domain: "news.example.com"
site_name: "Example News"
description: "News site template"

page_types:
  article:
    url_pattern:
      - "*/article/*"
      - "*/news/*"

    selectors:
      title: "h1.article-title"
      author: "span.author-name"
      published_date: "time[datetime]"
      content: "div.article-body"
      tags: "a.tag"
      images: "img.article-image"

    metadata:
      source_indicator: "span.source"
      update_time: "time.updated"
```

## Development / 开发

### Adding New Template Types / 添加新模板类型

Edit `parser_engine/tools/generators/template_generator.py` and add a new selector set:

```python
def get_default_selectors(template_type):
    if template_type == 'my_new_type':
        return {
            'field1': 'selector1',
            'field2': 'selector2',
        }
```

### Extending Validation Rules / 扩展验证规则

Edit `parser_engine/tools/validators/schema_validator.py` and add new validation logic:

```python
def validate_custom_field(self, template_data):
    # Add custom validation logic
    if 'custom_field' in template_data:
        # Validate custom field
        pass
```

### Adding Output Formats / 添加输出格式

Edit `parser_engine/tools/preview/html_preview.py` and add format handler:

```python
def format_custom(self, data):
    # Implement custom format
    return formatted_output
```

## Best Practices / 最佳实践

### Template Design / 模板设计

1. **Use Specific Selectors** - Prefer class-based selectors over tag-only
   ```yaml
   # Good
   title: "h1.article-title"

   # Less reliable
   title: "h1"
   ```

2. **Test with Real HTML** - Always preview with actual page HTML
   ```bash
   python scripts/template_tool.py preview --template <template> --html real_page.html
   ```

3. **Document Selector Logic** - Add comments for complex selectors
   ```yaml
   selectors:
     # Extracts first paragraph after header
     summary: "header + p:first-of-type"
   ```

### Validation Workflow / 验证工作流程

1. Create template → 2. Validate → 3. Preview → 4. Refine → 5. Document

```bash
# 1. Create
python scripts/template_tool.py init --domain site.com --type article

# 2. Validate
python scripts/template_tool.py validate <template>

# 3. Preview
python scripts/template_tool.py preview --template <template> --html sample.html

# 4. Refine (edit template.yaml)

# 5. Document
python scripts/template_tool.py doc --template <template> --output docs/
```

### Maintenance / 维护

- **Regular Validation** - Run validation after any template changes
- **Version Control** - Track template changes with git
- **Documentation Updates** - Regenerate docs when templates change
- **Testing** - Preview with various HTML samples

## Troubleshooting / 故障排除

### Template Validation Fails / 模板验证失败

**Problem:** Validation reports missing fields

**Solution:** Check the error messages for specific field paths
```bash
python scripts/template_tool.py validate <template>
# Error: selectors.title: Missing required field
# Fix: Add 'title' to selectors in template.yaml
```

### Preview Shows Empty Results / 预览显示空结果

**Problem:** Preview extracts no content

**Solutions:**
1. Verify selectors match the HTML structure
   - Use browser developer tools (F12) to inspect elements
   - Copy the exact selector from browser

2. Check if content requires JavaScript
   - If content is dynamically loaded, use selenium fetcher
   - Update template to use selenium mode

3. Test selectors incrementally
   ```bash
   # Test each selector individually
   # Comment out all but one selector in template
   python scripts/template_tool.py preview --template <template> --html <file>
   ```

### Documentation Generation Fails / 文档生成失败

**Problem:** Doc command produces errors

**Solutions:**
1. Ensure template is valid first
   ```bash
   python scripts/template_tool.py validate <template>
   ```

2. Check output directory permissions
   ```bash
   # Make sure directory exists and is writable
   mkdir -p docs/templates/
   chmod 755 docs/templates/
   ```

### CLI Command Not Found / CLI命令未找到

**Problem:** `template_tool.py` not found

**Solution:** Ensure you're in the project root
```bash
# Check current directory
pwd
# Should be: /path/to/Web_Fetcher

# Or use absolute path
python /path/to/Web_Fetcher/scripts/template_tool.py <command>
```

## Testing / 测试

### Run Integration Tests / 运行集成测试

```bash
# Run all integration tests
python tests/tools/test_template_tool_integration.py

# Expected output:
# ✓ PASS: Template Initialization (init)
# ✓ PASS: Template Validation (validate)
# ✓ PASS: Template Preview (preview)
# ✓ PASS: Documentation Generation (doc)
# ✓ PASS: Full Workflow Integration
# ✓ PASS: CLI Command Execution
#
# Passed: 6/6
# Success Rate: 100.0%
```

### Manual Testing / 手动测试

```bash
# Create test template
python scripts/template_tool.py init --domain test.com --type article --output /tmp/test_template

# Validate it
python scripts/template_tool.py validate /tmp/test_template/template.yaml

# Create sample HTML
cat > /tmp/sample.html << 'EOF'
<!DOCTYPE html>
<html>
<body>
  <article>
    <h1>Test Title</h1>
    <p>Test content</p>
  </article>
</body>
</html>
EOF

# Preview extraction
python scripts/template_tool.py preview --template /tmp/test_template/template.yaml --html /tmp/sample.html

# Generate docs
python scripts/template_tool.py doc --template /tmp/test_template/template.yaml
```

## FAQ / 常见问题

### Q: Can I use templates for JavaScript-heavy sites? / 可以为JavaScript重度网站使用模板吗？

A: Yes, but you need to fetch with selenium mode. Templates work with the final rendered HTML.

是的，但需要使用selenium模式获取。模板适用于最终渲染的HTML。

### Q: How do I handle dynamic URLs? / 如何处理动态URL？

A: Use regex patterns in `url_pattern`:
```yaml
url_pattern:
  - "*/article/[0-9]+/*"
  - "*/post/*"
```

### Q: Can I have multiple page types in one template? / 一个模板可以有多个页面类型吗？

A: Yes! Define multiple page types:
```yaml
page_types:
  article:
    url_pattern: ["*/article/*"]
    selectors: {...}

  list:
    url_pattern: ["*/category/*"]
    selectors: {...}
```

### Q: How do I extract nested content? / 如何提取嵌套内容？

A: Use CSS combinators:
```yaml
selectors:
  # Child combinator
  main_image: "article > img"

  # Descendant combinator
  paragraphs: "div.content p"

  # Adjacent sibling
  subtitle: "h1 + h2"
```

### Q: What if a selector returns multiple elements? / 如果选择器返回多个元素怎么办？

A: The parser will extract all matching elements as a list. For single values, ensure your selector is specific enough.

解析器会将所有匹配元素提取为列表。对于单一值，确保选择器足够具体。

## Migration Guide / 迁移指南

### From Legacy Code-Based Parsers / 从旧代码解析器迁移

If you have existing parsers in `/parser_engine/parsers/`, migrate them to templates:

1. **Analyze existing parser** - Identify selectors used
2. **Create template** - Use `init` command
3. **Transfer selectors** - Copy selectors to template
4. **Test** - Preview with real HTML
5. **Validate** - Ensure template is valid
6. **Document** - Generate documentation
7. **Archive old parser** - Move to `/legacy/` directory

Example migration:
```python
# Old parser (wechat_article.py)
def extract_title(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.select_one('h1#activity-name').text

# New template (wechat_article.yaml)
selectors:
  title: "h1#activity-name"
```

## Roadmap / 路线图

Future enhancements planned:

- [ ] Interactive template editor
- [ ] Template marketplace/sharing
- [ ] Visual selector picker (browser extension)
- [ ] Advanced validation rules
- [ ] Performance profiling for selectors
- [ ] Template versioning and migration tools

## License / 许可证

Part of the Web_Fetcher project.

## Support / 支持

For issues and questions:
- Check this README
- Review [QUICKSTART.md](QUICKSTART.md)
- Run integration tests
- Check existing templates in `/parser_engine/templates/sites/`

## Contributing / 贡献

When contributing templates or tool improvements:
1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Validate all templates
5. Test with real-world HTML

---

**Version:** 1.0.0
**Last Updated:** 2025-10-10
**Author:** Cody (Full-Stack Engineer)
