# WF 命令核心依赖关系

本文档记录 `wf` 命令依赖的所有 Python 代码，用于区分核心代码和临时测试代码。

## 依赖关系树

```
wf.py (入口)
├── webfetcher.py (核心抓取逻辑)
│   ├── selenium_config.py
│   ├── selenium_fetcher.py
│   ├── error_handler.py
│   │   ├── error_types.py
│   │   ├── error_cache.py
│   │   └── error_classifier.py
│   ├── config/ssl_problematic_domains.py
│   ├── routing/ (配置驱动路由系统)
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── config_loader.py
│   │   └── matchers.py
│   ├── manual_chrome/ (手动 Chrome 集成)
│   │   ├── __init__.py
│   │   ├── helper.py
│   │   └── exceptions.py
│   ├── parsers.py (解析器)
│   ├── parsers_legacy.py
│   ├── parsers_migrated.py
│   ├── url_formatter.py
│   └── parser_engine/ (模板解析引擎)
│       ├── __init__.py
│       ├── base_parser.py
│       ├── template_parser.py
│       ├── engine/
│       │   ├── __init__.py
│       │   └── template_loader.py
│       ├── strategies/
│       │   ├── __init__.py
│       │   ├── base_strategy.py
│       │   ├── css_strategy.py
│       │   ├── xpath_strategy.py
│       │   └── text_pattern_strategy.py
│       └── utils/
│           ├── __init__.py
│           └── validators.py
└── drivers/ (ChromeDriver 版本管理)
    ├── __init__.py
    ├── constants.py
    └── version_manager.py
```

## 核心模块说明

### 1. 主入口
- `wf.py` - CLI 便捷工具，提供简化的命令行接口

### 2. 核心抓取
- `webfetcher.py` - 主抓取逻辑，协调各个组件

### 3. Selenium 集成
- `selenium_config.py` - Selenium 配置管理
- `selenium_fetcher.py` - Selenium 网页获取器

### 4. 错误处理系统
- `error_handler.py` - 统一错误处理
- `error_types.py` - 错误类型定义
- `error_cache.py` - 错误缓存机制
- `error_classifier.py` - 错误分类器

### 5. 路由系统
- `routing/` - 配置驱动的路由引擎（Task-1）

### 6. Chrome 集成
- `manual_chrome/` - 手动 Chrome 调试集成（Task-000）
- `config/ssl_problematic_domains.py` - SSL 问题域名配置

### 7. 解析器
- `parsers.py` - 主解析器
- `parsers_legacy.py` - 遗留解析器（兼容性）
- `parsers_migrated.py` - 迁移的解析器
- `parser_engine/` - 模板驱动解析引擎（Task-001）

### 8. 工具模块
- `url_formatter.py` - URL 格式化和双 URL 跟踪（Task-003）
- `drivers/` - ChromeDriver 版本管理（Task-003）

### 9. 保留的脚本
- `scripts/manage_chromedriver.py` - ChromeDriver 管理工具

## 非核心代码（可移动到待删除文件夹）

### 测试代码（已在待删除文件夹）
- `待删除/tests/` - 所有测试文件
- `待删除/tests/diagnostics/` - 诊断工具
- `待删除/tests/integration/` - 集成测试
- `待删除/tests/migration/` - 迁移测试
- `待删除/tests/regression/` - 回归测试

### 临时工具（已在待删除文件夹）
- `待删除/tools/` - 模板工具（已废弃）
- `待删除/template_tool.py` - 模板工具 CLI（已废弃）
- `待删除/routing_ctl.py` - 路由控制工具（已废弃）

### 其他临时文件（待移动）
无，所有临时代码已清理完毕

## 验证方法

运行以下命令验证 wf 核心功能：

```bash
# 基本功能测试
wf "https://mp.weixin.qq.com/s/V3is7AMjJV1QzE-9Dh8I_w"

# 系统诊断
wf diagnose

# 不同模式测试
wf fast <url>
wf full <url>
wf site <url>
```

## 更新历史

- 2025-11-17: 初始版本，完成核心依赖关系分析
