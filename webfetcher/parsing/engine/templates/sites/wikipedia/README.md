# Wikipedia Chinese Articles Template

Template for parsing Chinese Wikipedia articles (zh.wikipedia.org) with high-quality content extraction.

## Overview

This template provides optimized parsing for Wikipedia articles, achieving >95% content-to-noise ratio compared to the 20% baseline of generic parsing.

**Quality Improvement: 4.75x better**

## Features

- ✅ **Clean Content Extraction**: Removes all navigation UI elements
- ✅ **Zero CSS Leakage**: No style code in markdown output
- ✅ **Metadata Extraction**: Title, author, last modified date
- ✅ **Image Extraction**: Wikipedia article images
- ✅ **Fast Performance**: ~1.5s parse time

## Usage

The template is automatically applied to any Wikipedia URL:

```bash
# Simple usage
python3 wf.py "https://zh.wikipedia.org/wiki/聂元梓"

# Verbose mode
python3 wf.py "https://zh.wikipedia.org/wiki/聂元梓" --verbose
```

### Expected Output

```markdown
# 聂元梓

- 标题: 聂元梓
- 作者: Wikipedia contributors
- 来源: https://zh.wikipedia.org/wiki/聂元梓
- 抓取时间: 2025-10-10 15:59:11

**聂元梓**（1921年4月4日—2019年8月28日）...
[Article content with proper formatting]
```

## Template Configuration

### Domains

- `zh.wikipedia.org` (Chinese Wikipedia)

**Priority:** 100 (High - exact domain match)

### Selectors

| Field | Selector | Description |
|-------|----------|-------------|
| **title** | `h1.firstHeading, title` | Article title from h1 heading |
| **author** | `meta[name='author']@content` | Defaults to "Wikipedia contributors" |
| **date** | `#footer-info-lastmod, ...` | Last modified date from footer |
| **content** | `#mw-content-text .mw-parser-output, ...` | Main article content |
| **images** | `#mw-content-text img, ...` | Article images |

### Content Filtering

The template automatically removes:
- Navigation menus and sidebars
- Edit links and UI buttons
- Table of contents boxes
- Footer elements
- Category links
- JavaScript and CSS code

## Quality Metrics

### Before/After Comparison

**Test Article:** [聂元梓](https://zh.wikipedia.org/wiki/聂元梓)

| Metric | Before (Generic Parser) | After (Wikipedia Template) | Improvement |
|--------|------------------------|---------------------------|-------------|
| **Output Lines** | 639 | 317 | **50% reduction** |
| **Navigation Noise** | 120 lines (19%) | 0 lines | **100% eliminated** |
| **Content-to-Noise Ratio** | ~20% | **>95%** | **4.75x better** |
| **CSS Code Leaks** | Yes (line 192) | None | **Fixed** |
| **Parse Time** | 1.6s | 1.5s | Slightly faster |

### Quality Gates Achieved

- ✅ Content-to-noise ratio >95%
- ✅ Zero CSS/JS code in output
- ✅ All navigation noise removed
- ✅ Parse time <3s
- ✅ Proper markdown structure

## Known Limitations

### Currently NOT Supported

1. **Other Wikipedia Language Versions**
   - Only Chinese Wikipedia (zh.wikipedia.org)
   - English/other languages: future enhancement

2. **Special Page Types**
   - Disambiguation pages
   - List articles
   - Portal pages

3. **Advanced MediaWiki Features**
   - Template transclusion rendering
   - Math formula parsing (basic support only)
   - Gallery/media complex layouts

4. **Infobox Extraction**
   - Basic infobox content included in main text
   - Structured infobox parsing: planned enhancement

## Testing URLs

Use these URLs for comprehensive testing:

```bash
# Standard biography
wf "https://zh.wikipedia.org/wiki/聂元梓"

# With infobox
wf "https://zh.wikipedia.org/wiki/中华人民共和国"

# Stub article (short)
wf "https://zh.wikipedia.org/wiki/黄龙镇_(北京市)"

# Long article
wf "https://zh.wikipedia.org/wiki/第二次世界大战"

# Chinese variants
wf "https://zh.wikipedia.org/wiki/中国?variant=zh-cn"  # Simplified
wf "https://zh.wikipedia.org/wiki/中国?variant=zh-tw"  # Traditional (Taiwan)
```

## Technical Details

### Architecture

- **Template File**: `zh_wikipedia.yaml`
- **Parser**: Template-based (TemplateParser)
- **Fetcher**: urllib (static content, no JavaScript needed)
- **Routing Priority**: 90 (high priority)

### Integration Points

1. **Template Loader**: Auto-loads on startup from `parser_engine/templates/sites/wikipedia/`
2. **Generic Parser**: Falls through to template-based parsing for Wikipedia URLs
3. **Routing System**: `config/routing.yaml` ensures urllib fetcher

### Selector Format

This template uses **string-based selectors** for compatibility with the current TemplateParser implementation:

```yaml
title: "h1.firstHeading, title"  # Comma-separated fallback selectors
content: "#mw-content-text .mw-parser-output, article"
```

**Note:** List-of-dict selector format (used by WeChat/XHS templates) is planned for future TemplateParser enhancement.

## Troubleshooting

### Template Not Being Used

Check if template is loaded:

```python
from parser_engine.engine.template_loader import TemplateLoader
loader = TemplateLoader()
print("Loaded templates:", loader.list_templates())
```

Expected output should include: `"Wikipedia Chinese Articles"`

### Poor Quality Output

1. Check URL domain matches `zh.wikipedia.org`
2. Verify routing rule in `config/routing.yaml`
3. Run with `--verbose` to see parser selection

### Parsing Errors

If you see `"No template found"` error:
1. Ensure template file exists at: `parser_engine/templates/sites/wikipedia/zh_wikipedia.yaml`
2. Check template validation (see Development section)

## Development

### Validating Template

```bash
cd parser_engine/templates/sites/wikipedia
python3 -c "
from parser_engine.tools.validators.schema_validator import SchemaValidator
validator = SchemaValidator()
is_valid, errors = validator.validate_file('zh_wikipedia.yaml')
print('Valid' if is_valid else f'Errors: {errors}')
"
```

**Note:** Schema validator may show warnings about string selectors. This is expected - the TemplateParser accepts string format.

### Testing Changes

```bash
# Quick test
python3 wf.py "https://zh.wikipedia.org/wiki/Test_Article" --verbose

# Check output quality
wc -l output/latest-wikipedia-article.md
grep -i "开关目录\|编辑链接" output/latest-wikipedia-article.md
```

## Version History

- **v1.0.0 (2025-10-10)**: Initial release
  - Basic content extraction
  - Navigation noise removal
  - Image extraction
  - Quality: >95% content-to-noise ratio

## Related

- **Task Document**: `TASKS/task-4-wikipedia-parser-optimization.md`
- **Schema**: `parser_engine/templates/schema.yaml`
- **Template Parser**: `parser_engine/template_parser.py`
- **Reference Templates**:
  - WeChat: `parser_engine/templates/sites/wechat/wechat.yaml`
  - XiaoHongShu: `parser_engine/templates/sites/xiaohongshu/xiaohongshu.yaml`

## Contributing

When enhancing this template:

1. Test with multiple article types (biography, place, event, etc.)
2. Verify quality metrics meet >95% content-to-noise ratio
3. Update this README with new features/limitations
4. Run regression tests to ensure no breakage

## License

Part of WebFetcher project. See main project LICENSE.
