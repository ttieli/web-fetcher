# News.cn Template / 新华网模板

## Overview / 概览

This template provides dedicated parsing rules for news.cn (新华网) articles. It was created to fix the empty content extraction issue (Task-009) where the generic template failed to extract article content due to missing selectors.

本模板为新华网（news.cn）文章提供专用解析规则。它是为了修复内容提取为空的问题（Task-009）而创建的，因为通用模板由于缺少选择器而无法提取文章内容。

## Problem Solved / 解决的问题

**Issue / 问题**: The generic template did not include `#detail` in its content selectors, which is the primary content container used by news.cn. This resulted in completely empty article bodies in the output files, with only metadata being extracted.

**问题详情**: 通用模板的内容选择器中不包含`#detail`，而这是新华网使用的主要内容容器。这导致输出文件中的文章正文完全为空，只提取了元数据。

**Solution / 解决方案**: This dedicated template prioritizes `#detail` as the PRIMARY content selector, ensuring successful extraction of news.cn article content.

**解决方案**: 这个专用模板将`#detail`作为主要内容选择器优先使用，确保成功提取新华网文章内容。

## Key Selectors / 关键选择器

### Content Extraction / 内容提取

The most critical selector for news.cn content extraction is:

新华网内容提取最关键的选择器是：

```yaml
content:
  - selector: "#detail"        # PRIMARY - news.cn main content container
    strategy: "css"
  - selector: "#detailContent" # Alternative detail container
    strategy: "css"
```

**Why #detail is critical / 为什么#detail至关重要**:
- News.cn wraps ALL article content in `<div id="detail">` / 新华网将所有文章内容包装在`<div id="detail">`中
- This container holds all paragraphs, images, and formatting / 这个容器包含所有段落、图片和格式
- Without this selector, content extraction returns empty / 没有这个选择器，内容提取返回空值

### Title Extraction / 标题提取

```yaml
title:
  - selector: "meta[property='og:title']"  # Open Graph meta tag
    attribute: "content"
  - selector: "h1"                          # Standard h1 heading
  - selector: "title"                       # Page title fallback
```

### Author Extraction / 作者提取

```yaml
author:
  - selector: "meta[property='og:article:author']"  # OG meta tag
    attribute: "content"
  - selector: ".info .source"                       # News.cn info section
  - selector: ".author"                             # Generic author class
```

### Date Extraction / 日期提取

```yaml
date:
  - selector: "meta[property='article:published_time']"  # OG published time
    attribute: "content"
  - selector: ".info .time"                              # News.cn time field
  - selector: ".time"                                    # Generic time class
```

### Image Extraction / 图片提取

```yaml
images:
  - selector: "#detail img"      # Images in detail container
    attribute: "src"
  - selector: "#detail img"      # Lazy-loaded images
    attribute: "data-src"
```

## Template Features / 模板特性

### Selector Priority / 选择器优先级

The template uses a cascading priority system:

模板使用级联优先级系统：

1. **Highest Priority / 最高优先级**: Site-specific selectors (e.g., `#detail` for content)
2. **Medium Priority / 中等优先级**: Open Graph meta tags
3. **Low Priority / 低优先级**: Generic HTML5 semantic elements
4. **Fallback / 后备**: Common class names

### Content Processing / 内容处理

- **Tag Removal / 标签移除**: Removes `<script>`, `<style>`, `<noscript>`, `<iframe>`
- **Whitespace Normalization / 空格规范化**: Cleans up excessive whitespace
- **Max Newlines / 最大换行数**: Limits consecutive newlines to 2
- **Encoding / 编码**: UTF-8 with HTML entity decoding
- **Link Preservation / 链接保留**: Extracts and preserves article links

### Output Format / 输出格式

The template generates markdown output with a comprehensive header:

模板生成带有完整标题的markdown输出：

```markdown
# {title}

- 标题: {title}
- 作者: {author}
- 发布时间: {publish_time}
- 来源: [{url}]({url})
- 抓取时间: {fetch_time}

[Article content follows...]
```

## Supported Domains / 支持的域名

This template matches the following domains:

此模板匹配以下域名：

- `news.cn`
- `www.news.cn`
- `*.news.cn` (all subdomains / 所有子域名)

**Priority / 优先级**: 95 (High priority for exact domain matching)

**优先级**: 95（精确域名匹配的高优先级）

## Validation Rules / 验证规则

The template includes quality checks to ensure successful extraction:

模板包含质量检查以确保成功提取：

- **Minimum Content Length / 最小内容长度**: 50 characters / 50个字符
- **Required Fields / 必需字段**: Title must be extracted / 必须提取标题
- **Text-to-HTML Ratio / 文本与HTML比率**: At least 0.1 (10% text content) / 至少0.1（10%文本内容）

## Testing / 测试

### Test URL / 测试URL

The template was tested and validated with:

模板已通过以下URL测试和验证：

```
https://www.news.cn/politics/leaders/20251010/2822d6ac4c4e424abde9fdd8fb94e2d3/c.html
```

**Before Template / 使用模板前**: Empty content, only metadata extracted / 内容为空，仅提取元数据

**After Template / 使用模板后**: Full article content successfully extracted / 成功提取完整文章内容

### Expected Behavior / 预期行为

When this template is active:

当此模板激活时：

1. **Domain Matching / 域名匹配**: Automatically selected for news.cn URLs / 自动选择用于新华网URL
2. **Content Extraction / 内容提取**: Extracts full article text from `#detail` container / 从`#detail`容器提取完整文章文本
3. **Metadata Extraction / 元数据提取**: Successfully extracts title, author, date / 成功提取标题、作者、日期
4. **Output Generation / 输出生成**: Creates well-formatted markdown files / 创建格式良好的markdown文件
5. **File Size / 文件大小**: Output files should be >1KB for typical articles / 对于典型文章，输出文件应>1KB

### Regression Testing / 回归测试

Verify that this template does not affect other sites:

验证此模板不影响其他网站：

- [ ] Wikipedia articles still extract correctly / 维基百科文章仍正确提取
- [ ] WeChat articles still extract correctly / 微信文章仍正确提取
- [ ] Generic sites using generic template still work / 使用通用模板的通用网站仍正常工作

## Performance / 性能

- **Target Parse Time / 目标解析时间**: <3 seconds per article / 每篇文章<3秒
- **Selector Caching / 选择器缓存**: Enabled for faster repeated extractions / 启用以加快重复提取
- **Max Attempts / 最大尝试次数**: 3 attempts per field / 每个字段3次尝试

## Maintenance / 维护

### When to Update This Template / 何时更新此模板

Update this template if:

如果出现以下情况，请更新此模板：

1. News.cn changes their HTML structure / 新华网更改其HTML结构
2. New article types appear with different selectors / 出现具有不同选择器的新文章类型
3. Content extraction starts failing / 内容提取开始失败
4. Performance degradation occurs / 性能下降

### How to Test Changes / 如何测试更改

1. Make changes to template.yaml / 对template.yaml进行更改
2. Test with multiple news.cn URLs / 使用多个新华网URL测试
3. Verify no regression on other sites / 验证其他网站无回归
4. Check output file quality / 检查输出文件质量
5. Update this README with changes / 使用更改更新此README

### Known Limitations / 已知限制

- **JavaScript Content / JavaScript内容**: This template parses static HTML. If news.cn uses heavy JavaScript rendering, content may be incomplete. / 此模板解析静态HTML。如果新华网使用大量JavaScript渲染，内容可能不完整。
- **Dynamic Elements / 动态元素**: Comments, related articles, and dynamic content may not be extracted. / 评论、相关文章和动态内容可能无法提取。
- **Multimedia / 多媒体**: Videos and audio embeds may not be fully captured in markdown format. / 视频和音频嵌入可能无法以markdown格式完全捕获。

## Related Documentation / 相关文档

- **Task Documentation / 任务文档**: `/TASKS/task-009-news-cn-empty-content-extraction.md`
- **Generic Template / 通用模板**: `/parser_engine/templates/generic.yaml`
- **Template System / 模板系统**: `/parser_engine/README.md`

## Version History / 版本历史

### v1.0.0 (2025-10-11)

- **Initial Release / 初始版本**
- Created dedicated news.cn template / 创建专用新华网模板
- Fixed empty content extraction issue / 修复内容提取为空问题
- Added comprehensive selector set / 添加全面的选择器集
- Implemented validation and quality checks / 实施验证和质量检查
- **Task Reference / 任务参考**: task-009

## Support / 支持

For issues or questions about this template:

如有关于此模板的问题或疑问：

1. Check the task documentation: `task-009-news-cn-empty-content-extraction.md`
2. Review the parser engine logs / 查看解析引擎日志
3. Test with the provided test URL / 使用提供的测试URL进行测试
4. Verify the template is being selected (check priority and domain matching) / 验证模板是否被选中（检查优先级和域名匹配）

---

**Template Version / 模板版本**: 1.0.0
**Created / 创建日期**: 2025-10-11
**Task / 任务**: task-009
**Author / 作者**: Cody (Full-Stack Engineer)
**Status / 状态**: Active / 激活
