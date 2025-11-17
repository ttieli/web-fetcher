# Template-Based Parser System

## 概述

WebFetcher 使用基于 YAML 模板的解析系统，实现了**内容提取逻辑与代码的完全分离**。所有网站特定的解析规则都存储在独立的 YAML 模板文件中，无需修改 Python 代码即可：

- ✅ 添加新网站支持
- ✅ 升级现有模板
- ✅ 调整提取规则
- ✅ 自定义字段处理

## 架构优势

### 1. 完全分离的模板系统

```
src/webfetcher/parsing/engine/
├── template_parser.py          # 通用解析引擎（无需修改）
├── template_loader.py          # 模板加载器（自动发现）
└── templates/                  # 模板存储目录
    ├── sites/                  # 站点特定模板
    │   ├── wechat/
    │   │   └── wechat.yaml    # 微信公众号模板
    │   ├── xiaohongshu/
    │   │   └── xiaohongshu.yaml  # 小红书模板
    │   ├── wikipedia/
    │   └── news_cn/
    ├── generic.yaml            # 通用回退模板
    └── schema.yaml             # 模板验证规则
```

### 2. 自动模板发现

`TemplateLoader` 会在启动时：
- 扫描 `templates/` 下所有 `.yaml` 文件
- 验证模板格式
- 按优先级和域名建立索引
- 无需注册或配置

### 3. 智能模板匹配

```python
# 自动按域名匹配模板
url = "https://mp.weixin.qq.com/s/xxxxx"
# → 自动使用 wechat.yaml

url = "https://www.xiaohongshu.com/discovery/item/xxxxx"
# → 自动使用 xiaohongshu.yaml

url = "https://example.com/article"
# → 回退到 generic.yaml
```

## 当前支持的模板

### 已实现模板

| 模板 | 域名 | 特性 | 位置 |
|------|------|------|------|
| **WeChat** | mp.weixin.qq.com | • 图片提取（data-src）<br>• 作者字段<br>• 发布日期 | `sites/wechat/wechat.yaml` |
| **XiaoHongShu** | xiaohongshu.com<br>xhslink.com | • 标题后处理（移除"- 小红书"）<br>• CDN图片验证<br>• JS代码过滤 | `sites/xiaohongshu/xiaohongshu.yaml` |
| **Wikipedia** | zh.wikipedia.org | • 多语言支持<br>• Infobox提取 | `sites/wikipedia/zh_wikipedia.yaml` |
| **News.cn** | news.cn | • 新闻文章格式 | `sites/news_cn/template.yaml` |
| **Generic** | *(fallback)* | • 通用网页<br>• OpenGraph元数据 | `generic.yaml` |

## 如何添加新网站模板

### 步骤 1: 创建模板目录

```bash
cd src/webfetcher/parsing/engine/templates/sites/
mkdir mynewsite
cd mynewsite
```

### 步骤 2: 创建模板文件

创建 `template.yaml` 或 `mynewsite.yaml`：

```yaml
# MyNewSite Template v1.0
name: "MyNewSite Articles"
version: "1.0.0"
domains:
  - "mynewsite.com"
  - "www.mynewsite.com"
priority: 100  # 100 = 精确匹配, 50 = 通配符, 10 = 通用

selectors:
  # 标题提取
  title:
    - selector: "meta[property='og:title']"
      strategy: "css"
      attribute: "content"
    - selector: "h1.article-title"
      strategy: "css"

  # 作者提取
  author:
    - selector: "meta[name='author']"
      strategy: "css"
      attribute: "content"
    - selector: ".author-name"
      strategy: "css"

  # 日期提取
  date:
    - selector: "meta[property='article:published_time']"
      strategy: "css"
      attribute: "content"
    - selector: "time"
      strategy: "css"
      attribute: "datetime"

  # 图片提取
  images:
    - selector: "img"
      strategy: "css"
      attribute: "src"
      validation:
        domain_contains:
          - "mynewsite.com/images"
          - "cdn.mynewsite.com"
        exclude_patterns:
          - "avatar"
          - "icon"

  # 内容提取
  content:
    - selector: "article.main-content"
      strategy: "css"
    - selector: "div.post-content"
      strategy: "css"
```

### 步骤 3: 测试新模板

```bash
# 安装最新版本
pipx reinstall webfetcher

# 测试提取
wf "https://mynewsite.com/article" -o ~/output

# 检查输出
cat ~/output/2025-*.md
```

**就这样！** 无需修改任何 Python 代码，模板会被自动发现和使用。

## 模板高级特性

### 1. 后处理管道（Post-Processing）

用于清理和转换提取的字段：

```yaml
title:
  - selector: "meta[property='og:title']"
    strategy: "css"
    attribute: "content"
    post_process:
      # 正则替换
      - type: "regex_replace"
        pattern: '\s*-\s*网站名\s*$'
        replacement: ''
        flags: "i"  # i=忽略大小写, m=多行, s=.匹配换行

      # 简单替换
      - type: "replace"
        old: "©2024"
        new: ""

      # 其他转换
      - type: "strip"    # 去除首尾空格
      - type: "lower"    # 转小写
      - type: "upper"    # 转大写
```

**实际应用**: 小红书模板使用 `post_process` 移除标题中的 "- 小红书" 后缀。

### 2. 图片URL验证

防止提取无效图片和JavaScript代码：

```yaml
images:
  - selector: "img"
    strategy: "css"
    attribute: "src"
    validation:
      # 域名白名单
      domain_contains:
        - "cdn.example.com"
        - "images.example.com"

      # URL黑名单模式
      exclude_patterns:
        - "avatar"
        - "favicon"
        - "icon"
        - "logo"
```

**自动过滤**:
- ❌ JavaScript 代码（检测关键字：function, window, etc.）
- ❌ 大型 base64 图片（>500字节）
- ❌ 不匹配域名的URL

### 3. 懒加载图片处理

自动转换 `data-src` 为 `src`：

```yaml
images:
  - selector: "img"
    strategy: "css"
    attribute: "src"  # 会自动检查 data-src
```

模板解析器在提取前会自动：
1. 移除 `<script>`, `<style>`, `<noscript>` 标签
2. 将 `data-src` 复制到 `src` 属性
3. 然后再执行选择器

### 4. 多选择器优先级

按顺序尝试，返回第一个成功的结果：

```yaml
title:
  - selector: "meta[property='og:title']@content"  # 最高优先级
  - selector: "h1.article-title"                    # 备选1
  - selector: "h1"                                   # 备选2
```

### 5. 选择器策略

```yaml
selectors:
  title:
    - selector: "h1.title"
      strategy: "css"      # CSS选择器（默认）

    - selector: "//h1[@class='title']"
      strategy: "xpath"    # XPath选择器

    - selector: "Title: (.*?)\\n"
      strategy: "text"     # 正则模式
```

## 升级现有模板

### 微信模板升级示例

假设需要添加新的作者字段选择器：

```bash
# 1. 编辑模板文件
vim src/webfetcher/parsing/engine/templates/sites/wechat/wechat.yaml

# 2. 在 author 部分添加新选择器
author:
  - selector: "meta[property='og:article:author']"
    strategy: "css"
    attribute: "content"

  # ✨ 新增：备选作者字段
  - selector: ".author-signature"
    strategy: "css"

# 3. 保存并重新安装
pipx reinstall webfetcher

# 4. 测试
wf "https://mp.weixin.qq.com/s/xxxxx" -o ~/output
```

### 小红书模板升级示例

添加新的图片域名白名单：

```yaml
images:
  - selector: "img"
    strategy: "css"
    attribute: "src"
    validation:
      domain_contains:
        - "ci.xiaohongshu.com"
        - "sns-img"
        - "xhscdn.com"
        - "new-cdn.xiaohongshu.com"  # ✨ 新增CDN域名
```

**无需任何代码修改** - 重新安装即可生效！

## 模板验证

### 自动验证

`TemplateLoader` 在加载时会自动验证：
- ✅ 必需字段存在（name, domains, selectors）
- ✅ 选择器格式正确
- ✅ 策略类型有效（css/xpath/text）
- ✅ Post-process规则语法

### 手动验证

```python
from webfetcher.parsing.engine.utils.validators import TemplateValidator

validator = TemplateValidator()
with open('mynewsite.yaml') as f:
    template = yaml.safe_load(f)

is_valid, errors = validator.validate_template(template)
if not is_valid:
    print("验证失败:", errors)
```

## 模板调试技巧

### 1. 启用调试日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 2. 测试单个选择器

```python
from webfetcher.parsing.engine.template_parser import TemplateParser

parser = TemplateParser()
result = parser.parse(html_content, url)

print(f"标题: {result.title}")
print(f"作者: {result.metadata.get('author')}")
print(f"图片数量: {len(result.metadata.get('images', []))}")
```

### 3. 比较新旧输出

```bash
# 保存升级前的输出
wf "https://example.com/article" -o ~/before/

# 升级模板后
pipx reinstall webfetcher

# 保存升级后的输出
wf "https://example.com/article" -o ~/after/

# 对比
diff ~/before/*.md ~/after/*.md
```

## 最佳实践

### 1. 模板组织

```
sites/
└── mysite/
    ├── mysite.yaml          # 主模板
    ├── README.md            # 说明文档
    └── examples/            # 测试用例（可选）
        └── sample.html
```

### 2. 命名约定

- **模板名称**: 使用网站英文名（如 `wechat.yaml`, `xiaohongshu.yaml`）
- **显示名称**: 使用友好名称（如 "WeChat Articles", "XiaoHongShu Posts"）
- **版本号**: 语义化版本（1.0.0, 1.1.0, 2.0.0）

### 3. 选择器优先级

```yaml
title:
  # 1. 标准元数据（最可靠）
  - selector: "meta[property='og:title']"
    attribute: "content"

  # 2. 网站特定类名（次优先）
  - selector: "h1.article-title"

  # 3. 通用标签（回退）
  - selector: "h1"
```

### 4. 注释规范

```yaml
# ============================================================================
# TITLE EXTRACTION
# Priority: OG meta tag -> site-specific selector -> generic h1
# Post-processing: Remove site name suffix
# ============================================================================
title:
  # Open Graph meta tag (highest priority)
  - selector: "meta[property='og:title']"
    # ... config ...
```

### 5. 版本管理

每次重大更新时增加版本号：

```yaml
name: "MyNewSite Articles"
version: "2.0.0"  # 从 1.0.0 升级

# Changelog:
# v2.0.0 (2025-11-17): 添加图片验证，后处理清理
# v1.0.0 (2025-10-01): 初始版本
```

## 常见问题

### Q: 添加新模板后需要重启什么吗？

**A**: 需要重新安装 webfetcher：
```bash
pipx reinstall webfetcher
```

模板在首次导入时被加载到内存，重新安装会刷新模板缓存。

### Q: 多个模板匹配同一域名怎么办？

**A**: 使用 `priority` 字段控制优先级：
```yaml
priority: 100  # 数值越高优先级越高
```

### Q: 如何测试模板是否被正确加载？

**A**: 查看解析日志：
```bash
wf "https://example.com" -o ~/output 2>&1 | grep "Selected parser"
# 输出: Selected parser: MyNewSite
```

### Q: 可以在不修改代码的情况下添加新字段吗？

**A**: 可以！在 `selectors` 中添加任意字段：
```yaml
selectors:
  custom_field:
    - selector: ".my-custom-class"
      strategy: "css"
```

字段会自动出现在 `result.metadata['custom_field']` 中。

### Q: 如何处理动态加载的内容？

**A**: 当前模板系统处理静态HTML。对于需要JavaScript渲染的网站，系统会尝试使用 Playwright 预渲染，然后再应用模板。

## 贡献模板

欢迎为新网站贡献模板！

1. 在 `sites/` 下创建新目录
2. 添加 YAML 模板和 README
3. 测试并确保输出质量
4. 提交 Pull Request

**模板质量标准**:
- ✅ 至少3个测试URL验证
- ✅ 完整的字段注释
- ✅ 图片和内容提取准确率 >95%
- ✅ 无JavaScript代码泄漏
- ✅ 正确处理边缘情况

## 技术参考

### 模板解析流程

```
URL请求
  ↓
TemplateLoader.get_template_for_url(url)
  ↓ (域名匹配)
加载对应YAML模板
  ↓
TemplateParser.parse(html, url)
  ├── 预处理HTML（移除script, 转换data-src）
  ├── 提取title (应用post_process)
  ├── 提取content
  ├── 提取metadata (author, date, images)
  └── 验证URLs (过滤JS, base64)
  ↓
返回 ParseResult
  ↓
格式化为Markdown
```

### 相关代码文件

- `template_loader.py` - 模板加载和匹配
- `template_parser.py` - 模板解析引擎
- `strategies.py` - 选择器策略（CSS/XPath/Text）
- `utils/validators.py` - 模板验证器

---

**最后更新**: 2025-11-17
**维护者**: Web_Fetcher Team
**许可证**: MIT
