# Generic Web Template

**Version:** 2.0.0
**Generated:** 2025-10-10 11:46:54
**Template File:** `generic.yaml`

## Supported Domains / 支持的域名

- `*`

## Template Type / 模板类型

**Type:** `unknown`

## Selectors / 选择器

This template defines the following extraction selectors:

### Title

| Priority | Selector | Strategy | Attribute | Transform |
|----------|----------|----------|-----------|-----------|
| 1 | `meta[property='og:title']` | css | content | - |
| 2 | `meta[name='twitter:title']` | css | content | - |
| 3 | `meta[itemprop='headline']` | css | content | - |
| 4 | `meta[itemprop='name']` | css | content | - |
| 5 | `title` | css | text | - |
| 6 | `h1` | css | text | - |
| 7 | `article h1` | css | text | - |
| 8 | `main h1` | css | text | - |
| 9 | `.headline` | css | text | - |
| 10 | `.post-title` | css | text | - |
| 11 | `.article-title` | css | text | - |
| 12 | `.entry-title` | css | text | - |
| 13 | `.page-title` | css | text | - |
| 14 | `.title` | css | text | - |
| 15 | `#post-title` | css | text | - |
| 16 | `#article-title` | css | text | - |
| 17 | `.story-headline` | css | text | - |
| 18 | `.news-title` | css | text | - |
| 19 | `[itemprop='headline']` | css | text | - |
| 20 | `.blog-title` | css | text | - |
| 21 | `.post-heading` | css | text | - |
| 22 | `header h1` | css | text | - |
| 23 | `.content-title` | css | text | - |
| 24 | `.article-heading` | css | text | - |

### Content

| Priority | Selector | Strategy | Attribute | Transform |
|----------|----------|----------|-----------|-----------|
| 1 | `article` | css | text | - |
| 2 | `main` | css | text | - |
| 3 | `[role='main']` | css | text | - |
| 4 | `[role='article']` | css | text | - |
| 5 | `.post-content` | css | text | - |
| 6 | `.entry-content` | css | text | - |
| 7 | `.article-content` | css | text | - |
| 8 | `.article-body` | css | text | - |
| 9 | `.news-article` | css | text | - |
| 10 | `.story-body` | css | text | - |
| 11 | `.content-body` | css | text | - |
| 12 | `.post-body` | css | text | - |
| 13 | `.docs-content` | css | text | - |
| 14 | `.documentation` | css | text | - |
| 15 | `.markdown-body` | css | text | - |
| 16 | `#content` | css | text | - |
| 17 | `#main-content` | css | text | - |
| 18 | `#article-content` | css | text | - |
| 19 | `#post-content` | css | text | - |
| 20 | `.content` | css | text | - |
| 21 | `div.text` | css | text | - |
| 22 | `.story-content` | css | text | - |
| 23 | `.news-content` | css | text | - |
| 24 | `[itemprop='articleBody']` | css | text | - |
| 25 | `.blog-content` | css | text | - |
| 26 | `.post-text` | css | text | - |
| 27 | `.message-body` | css | text | - |
| 28 | `.post-message` | css | text | - |
| 29 | `.doc-content` | css | text | - |
| 30 | `.documentation-content` | css | text | - |
| 31 | `.readme` | css | text | - |

### Metadata

*No selectors defined / 未定义选择器*

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

*Documentation auto-generated from `parser_engine/templates/generic.yaml`*
