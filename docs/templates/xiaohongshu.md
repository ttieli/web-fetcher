# XiaoHongShu Posts

**Version:** 1.0.0
**Generated:** 2025-10-10 11:48:10
**Template File:** `xiaohongshu.yaml`

## Supported Domains / 支持的域名

- `xiaohongshu.com`
- `xhslink.com`
- `www.xiaohongshu.com`

## Template Type / 模板类型

**Type:** `unknown`

## Selectors / 选择器

This template defines the following extraction selectors:

### Title

| Priority | Selector | Strategy | Attribute | Transform |
|----------|----------|----------|-----------|-----------|
| 1 | `meta[property='og:title']` | css | content | - |
| 2 | `meta[name='twitter:title']` | css | content | - |
| 3 | `title` | css | text | - |
| 4 | `.note-title` | css | text | - |
| 5 | `h1.title` | css | text | - |
| 6 | `h1` | css | text | - |

### Author

| Priority | Selector | Strategy | Attribute | Transform |
|----------|----------|----------|-----------|-----------|
| 1 | `script[type='application/ld+json']` | text_pattern | text | - |
| 2 | `script[type='application/ld+json']` | text_pattern | text | - |
| 3 | `meta[name='author']` | css | content | - |
| 4 | `.author-name` | css | text | - |
| 5 | `.user-nickname` | css | text | - |
| 6 | `.profile-name` | css | text | - |

### Date

| Priority | Selector | Strategy | Attribute | Transform |
|----------|----------|----------|-----------|-----------|
| 1 | `script[type='application/ld+json']` | text_pattern | text | - |
| 2 | `script[type='application/ld+json']` | text_pattern | text | - |
| 3 | `meta[property='article:published_time']` | css | content | - |
| 4 | `.publish-time` | css | text | - |
| 5 | `time` | css | datetime | - |
| 6 | `time` | css | text | - |

### Content

| Priority | Selector | Strategy | Attribute | Transform |
|----------|----------|----------|-----------|-----------|
| 1 | `meta[name='description']` | css | content | - |
| 2 | `meta[property='og:description']` | css | content | - |
| 3 | `.note-content` | css | text | - |
| 4 | `article` | css | text | - |
| 5 | `main` | css | text | - |
| 6 | `.post-content` | css | text | - |
| 7 | `.content-wrapper` | css | text | - |

### Cover

| Priority | Selector | Strategy | Attribute | Transform |
|----------|----------|----------|-----------|-----------|
| 1 | `meta[property='og:image']` | css | content | - |
| 2 | `meta[name='twitter:image']` | css | content | - |

### Images

| Priority | Selector | Strategy | Attribute | Transform |
|----------|----------|----------|-----------|-----------|
| 1 | `img` | css | src | - |
| 2 | `img` | css | data-src | - |
| 3 | `img` | css | srcset | - |
| 4 | `script` | text_pattern | text | - |

## Metadata / 元数据

- **fields:** ['author', 'publish_time', 'images', 'cover', 'description', 'title', 'url', 'fetch_time']
- **defaults:** {'author': '', 'title': '未命名', 'publish_time': '', 'description': '(未能从页面提取正文摘要)', 'cover': ''}

## Usage Example / 使用示例

```python
from parser_engine.template_parser import TemplateParser

# Initialize parser
parser = TemplateParser()

# Parse HTML content
result = parser.parse(html_content, url)

# Access extracted data
print(result.title)
print(result.content)
print(result.author)
```

---

*Documentation auto-generated from `parser_engine/templates/sites/xiaohongshu/xiaohongshu.yaml`*
