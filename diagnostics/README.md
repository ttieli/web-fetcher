# SPA页面诊断工具 - Phase 0

## 概述

这个诊断工具用于分析SPA（单页应用）页面的内容提取问题，特别是React.dev等现代Web应用。

## 文件结构

```
diagnostics/
├── README.md                    # 本文件
├── spa_diagnosis.py            # 主诊断工具类
├── run_diagnosis.py            # 执行入口脚本
└── test_results/               # 诊断结果输出目录
    ├── reactdev_raw.html       # 原始HTML文件
    └── diagnosis_report.md     # 诊断报告
```

## 功能

### SPADiagnostics 类

主要功能模块：

1. **save_raw_html()** - 使用SeleniumFetcher获取并保存原始HTML
2. **analyze_dom_structure()** - 分析DOM结构，识别主要内容容器
3. **test_wait_strategies()** - 测试不同等待时间策略的效果
4. **test_parser_selectors()** - 测试Generic Parser的选择器匹配情况
5. **generate_report()** - 生成Markdown格式的诊断报告

## 使用方法

### 运行诊断

```bash
cd diagnostics
python3 run_diagnosis.py
```

或直接运行主脚本：

```bash
python3 spa_diagnosis.py
```

### 自定义诊断

```python
from diagnostics.spa_diagnosis import SPADiagnostics

# 初始化诊断工具
diagnostics = SPADiagnostics()

# 对特定URL执行诊断
url = "https://react.dev/"

# 获取原始HTML
html, size, path = diagnostics.save_raw_html(url, "output.html")

# 分析DOM结构
dom_info = diagnostics.analyze_dom_structure(html)

# 测试等待策略
wait_results = diagnostics.test_wait_strategies(url)

# 测试选择器
selector_results = diagnostics.test_parser_selectors(html)

# 生成报告
report = diagnostics.generate_report(url, {
    'html_stats': {...},
    'dom_analysis': dom_info,
    'wait_strategies': wait_results,
    'selector_tests': selector_results
})
```

## 诊断报告内容

生成的报告包含以下部分：

1. **原始HTML统计**
   - HTML大小
   - 标签总数
   - div和script标签数量

2. **DOM结构分析**
   - 主要内容容器识别
   - 每个容器的文本长度和子元素数
   - 内容预览

3. **等待策略对比**
   - 不同等待时间的效果
   - 内容提取成功率
   - 提取内容的长度

4. **选择器匹配情况**
   - Generic Parser选择器测试结果
   - 匹配和未匹配的选择器列表
   - 匹配元素的内容预览

5. **根因分析和建议**
   - 自动识别的问题
   - 针对性的解决方案建议
   - 特定网站的优化建议

## React.dev诊断结果摘要

### 主要发现

从2025-09-30的诊断报告中发现：

1. **HTML成功获取** - 272KB，3541个标签
2. **内容存在** - main和article标签都有7000+字符
3. **选择器匹配** - 3/14个选择器匹配成功
4. **等待时间不是问题** - 1-10秒都成功

### 根因判断

1. 匹配的选择器（main, article）确实包含内容
2. div.lead选择器匹配但内容很短（25字符）
3. 问题可能在于：
   - 选择器优先级
   - 内容提取逻辑
   - HTML结构与预期不符

### 建议的解决方案

1. 优先使用`main`和`article`标签选择器
2. 对于React.dev，确保等待React hydration完成
3. 可能需要等待特定的data-ready属性
4. 考虑使用网络空闲等待策略

## 依赖项

- selenium_fetcher.py - Selenium网页抓取
- selenium_config.py - Selenium配置管理
- parsers.py - 内容解析器
- BeautifulSoup4 - HTML解析和DOM分析

## 注意事项

1. 需要Chrome浏览器运行在debug端口（9222）
2. 执行时间可能较长（特别是wait策略测试）
3. 建议在诊断前启动Chrome debug会话：
   ```bash
   ./config/chrome-debug.sh
   ```

## 下一步

基于诊断结果，Phase 1应该：

1. 优化Generic Parser的选择器优先级
2. 增强`main`和`article`标签的提取逻辑
3. 添加React特定的等待条件
4. 改进内容清理和格式化逻辑

---

**Author**: Cody (Full-Stack Engineer)
**Date**: 2025-09-30
**Version**: 1.0 (Phase 0 Complete)