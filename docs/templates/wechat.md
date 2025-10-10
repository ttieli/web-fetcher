# WeChat Articles

**Version:** 1.0.0
**Generated:** 2025-10-10 11:47:14
**Template File:** `wechat.yaml`

## Supported Domains / 支持的域名

- `mp.weixin.qq.com`

## Template Type / 模板类型

**Type:** `unknown`

## Selectors / 选择器

This template defines the following extraction selectors:

### Title

| Priority | Selector | Strategy | Attribute | Transform |
|----------|----------|----------|-----------|-----------|
| 1 | `meta[property='og:title']` | css | content | - |
| 2 | `h1.rich_media_title` | css | text | - |
| 3 | `#activity-name` | css | text | - |
| 4 | `h1` | css | text | - |

### Author

| Priority | Selector | Strategy | Attribute | Transform |
|----------|----------|----------|-----------|-----------|
| 1 | `meta[property='og:article:author']` | css | content | - |
| 2 | `span.rich_media_meta.rich_media_meta_text` | css | text | - |
| 3 | `#js_name` | css | text | - |
| 4 | `a.profile_nickname` | css | text | - |

### Date

| Priority | Selector | Strategy | Attribute | Transform |
|----------|----------|----------|-----------|-----------|
| 1 | `meta[property='article:published_time']` | css | content | - |
| 2 | `#publish_time` | css | text | - |
| 3 | `em#publish_time` | css | text | - |
| 4 | `.rich_media_meta_list em` | css | text | - |

### Content

| Priority | Selector | Strategy | Attribute | Transform |
|----------|----------|----------|-----------|-----------|
| 1 | `#js_content` | css | text | - |
| 2 | `.rich_media_content` | css | text | - |
| 3 | `article` | css | text | - |
| 4 | `.rich_media_wrp` | css | text | - |

### Images

| Priority | Selector | Strategy | Attribute | Transform |
|----------|----------|----------|-----------|-----------|
| 1 | `#js_content img` | css | data-src | - |
| 2 | `#js_content img` | css | src | - |
| 3 | `.rich_media_content img` | css | data-src | - |

## Metadata / 元数据

- **fields:** ['author', 'publish_time', 'images', 'title', 'url', 'fetch_time']
- **defaults:** {'author': '', 'title': '未命名', 'publish_time': ''}

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

*Documentation auto-generated from `parser_engine/templates/sites/wechat/wechat.yaml`*
