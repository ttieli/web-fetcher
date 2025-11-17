# Web Fetcher 项目重组方案

**日期**: 2025-11-17
**目标**: 在清晰性和简洁性之间达到平衡，避免过度工程化

## 📊 当前状态评估

### 项目特征
- **规模**: 中等（12个核心Python文件，6个模块目录）
- **类型**: CLI工具 + 库功能
- **用户**: 直接执行 `wf` 命令
- **维护**: 个人/小团队项目
- **打包**: 无（脚本式使用）

### 现有问题
1. ✗ 根目录12个Python文件略显混乱
2. ✗ 错误处理模块（4个文件）分散
3. ✗ 解析器模块（3个文件 + parser_engine/）结构不够清晰
4. ✗ 配置文件混合（config/ + selenium_config.py）
5. ✗ 待删除文件夹占据根目录
6. ✓ 核心模块目录结构良好（routing/, manual_chrome/, drivers/）

## 🎯 重组原则

1. **适度模块化** - 不采用过重的 src-layout，保持CLI简单性
2. **按功能聚合** - 相关文件归类到子包
3. **减少根目录** - 根目录仅保留入口、配置、文档
4. **向后兼容** - 保持 `wf` 命令用法不变
5. **渐进迁移** - 分阶段执行，每阶段可独立验证

## 📁 目标结构

```
Web_Fetcher/
├── wf.py                           # CLI入口（保持根目录便于执行）
├── pyproject.toml                  # 新增：项目元数据和依赖管理
├── README.md                       # 新增：项目说明
├── .gitignore                      # 新增：统一忽略规则
│
├── webfetcher/                     # 核心包（不用src/，直接作为顶层包）
│   ├── __init__.py                 # 包初始化，导出主要接口
│   ├── cli.py                      # 从wf.py提取的CLI逻辑
│   ├── core.py                     # 从webfetcher.py重命名
│   │
│   ├── fetchers/                   # 获取器模块
│   │   ├── __init__.py
│   │   ├── selenium.py             # selenium_fetcher.py
│   │   └── config.py               # selenium_config.py
│   │
│   ├── parsing/                    # 解析器模块（整合3个文件）
│   │   ├── __init__.py             # 统一导出接口
│   │   ├── parser.py               # parsers.py
│   │   ├── templates.py            # parsers_migrated.py
│   │   ├── legacy.py               # parsers_legacy.py
│   │   └── engine/                 # parser_engine/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── loader.py
│   │       ├── strategies/
│   │       └── utils/
│   │
│   ├── errors/                     # 错误处理模块（整合4个文件）
│   │   ├── __init__.py             # 统一导出异常类
│   │   ├── handler.py              # error_handler.py
│   │   ├── classifier.py           # error_classifier.py
│   │   ├── types.py                # error_types.py
│   │   └── cache.py                # error_cache.py
│   │
│   ├── routing/                    # 路由模块（保持现有结构）
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── matchers.py
│   │   └── config_loader.py
│   │
│   ├── manual/                     # 手动Chrome模块（从manual_chrome/重命名）
│   │   ├── __init__.py
│   │   ├── helper.py
│   │   └── exceptions.py
│   │
│   ├── drivers/                    # ChromeDriver管理（保持）
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   └── version_manager.py
│   │
│   └── utils/                      # 工具模块
│       ├── __init__.py
│       └── url_formatter.py        # url_formatter.py
│
├── configs/                        # 配置文件目录
│   ├── README.md                   # 配置说明
│   ├── routing.yaml                # 从config/
│   ├── selenium_defaults.yaml      # 从config/
│   ├── ssl_problematic_domains.py  # 从config/
│   └── scripts/                    # Shell脚本
│       ├── chrome-debug.sh
│       ├── ensure-chrome-debug.sh
│       └── chrome-debug-launcher.sh
│
├── scripts/                        # Python脚本工具
│   ├── README.md                   # 脚本说明
│   └── manage_chromedriver.py      # 保持
│
├── tests/                          # 测试目录（新建）
│   ├── __init__.py
│   ├── conftest.py                 # pytest配置
│   ├── unit/                       # 单元测试
│   │   ├── test_errors.py
│   │   ├── test_parsing.py
│   │   └── test_routing.py
│   ├── integration/                # 集成测试
│   │   ├── test_selenium.py
│   │   └── test_end_to_end.py
│   └── fixtures/                   # 测试数据
│       └── regression/             # 回归测试基准
│
├── docs/                           # 文档目录
│   ├── README.md                   # 文档索引
│   ├── architecture/               # 架构文档
│   │   ├── dependencies.md         # WF_DEPENDENCIES.md
│   │   └── root_files.md           # ROOT_FILES_DEPENDENCY_ANALYSIS.md
│   ├── how-to/                     # 使用指南
│   │   ├── manual_chrome.md
│   │   └── selenium_setup.md
│   └── archive/                    # 历史文档（从待删除/整理）
│       └── ...
│
├── var/                            # 运行时数据（新增到.gitignore）
│   ├── output/                     # 从output/迁移
│   ├── logs/                       # 日志文件
│   └── cache/                      # 缓存文件
│
├── requirements/                   # 依赖文件目录
│   ├── base.txt                    # 基础依赖
│   ├── selenium.txt                # Selenium依赖（从requirements-selenium.txt）
│   └── dev.txt                     # 开发依赖（pytest等）
│
└── archive/                        # 归档目录（从待删除/重命名）
    ├── README.md                   # 说明这是历史文件
    ├── tests/                      # 旧测试代码
    ├── docs/                       # 旧文档
    └── tasks/                      # 任务记录
```

## 🔄 迁移计划

### Phase 1: 准备工作（低风险）
**目标**: 建立新结构，不改动现有代码

```bash
# 1. 创建新目录结构
mkdir -p webfetcher/{fetchers,parsing,errors,routing,manual,drivers,utils}
mkdir -p configs/scripts
mkdir -p scripts tests/{unit,integration,fixtures/regression}
mkdir -p docs/{architecture,how-to,archive}
mkdir -p var/{output,logs,cache}
mkdir -p requirements

# 2. 创建 __init__.py
touch webfetcher/__init__.py
touch webfetcher/{fetchers,parsing,errors,routing,manual,drivers,utils}/__init__.py
touch tests/__init__.py

# 3. 创建配置文件
cat > pyproject.toml << 'EOF'
[project]
name = "webfetcher"
version = "1.0.0"
description = "Web content fetcher with intelligent routing"
requires-python = ">=3.7"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
EOF

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Runtime
var/
*.log

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Archive
archive/
EOF
```

### Phase 2: 迁移文件（中等风险）
**目标**: 移动文件到新位置，更新导入路径

#### 2.1 错误处理模块
```bash
# 移动文件
mv error_handler.py webfetcher/errors/handler.py
mv error_classifier.py webfetcher/errors/classifier.py
mv error_types.py webfetcher/errors/types.py
mv error_cache.py webfetcher/errors/cache.py

# 创建 __init__.py
cat > webfetcher/errors/__init__.py << 'EOF'
"""Unified error handling framework."""
from .handler import (
    ChromeDebugError, ChromePortConflictError,
    ChromePermissionError, ChromeTimeoutError,
    ChromeLaunchError, ChromeErrorMessages
)
from .classifier import UnifiedErrorClassifier
from .types import ErrorType, ErrorClassification
from .cache import ErrorCache

__all__ = [
    'ChromeDebugError', 'ChromePortConflictError',
    'ChromePermissionError', 'ChromeTimeoutError',
    'ChromeLaunchError', 'ChromeErrorMessages',
    'UnifiedErrorClassifier',
    'ErrorType', 'ErrorClassification',
    'ErrorCache'
]
EOF
```

#### 2.2 解析器模块
```bash
# 移动文件
mv parsers.py webfetcher/parsing/parser.py
mv parsers_migrated.py webfetcher/parsing/templates.py
mv parsers_legacy.py webfetcher/parsing/legacy.py
mv parser_engine webfetcher/parsing/engine

# 创建 __init__.py
cat > webfetcher/parsing/__init__.py << 'EOF'
"""Web content parsing with template support."""
from .parser import (
    xhs_to_markdown,
    wechat_to_markdown,
    generic_to_markdown
)

__all__ = [
    'xhs_to_markdown',
    'wechat_to_markdown',
    'generic_to_markdown'
]
EOF
```

#### 2.3 获取器模块
```bash
mv selenium_fetcher.py webfetcher/fetchers/selenium.py
mv selenium_config.py webfetcher/fetchers/config.py
```

#### 2.4 其他模块
```bash
# URL格式化
mv url_formatter.py webfetcher/utils/url_formatter.py

# 路由（已在正确位置，只需移动）
mv routing webfetcher/

# 手动Chrome
mv manual_chrome webfetcher/manual

# Drivers
mv drivers webfetcher/
```

#### 2.5 配置文件
```bash
# 移动配置
mv config/* configs/
mv config/*.sh configs/scripts/
rmdir config

# 拆分requirements
cat > requirements/base.txt << 'EOF'
# Base dependencies
pyyaml>=6.0.0,<7.0.0
lxml>=4.9.0,<5.0.0
jsonschema>=4.0.0,<5.0.0
html2text>=2020.1.16
requests>=2.28.0,<3.0.0
EOF

mv requirements-selenium.txt requirements/selenium.txt
```

#### 2.6 文档和输出
```bash
# 文档
mv WF_DEPENDENCIES.md docs/architecture/dependencies.md
mv ROOT_FILES_DEPENDENCY_ANALYSIS.md docs/architecture/root_files.md

# 输出
mv output/* var/output/ 2>/dev/null || true
rmdir output

# 归档
mv 待删除 archive
```

### Phase 3: 更新导入路径（高风险）
**目标**: 修改所有Python文件的导入语句

**自动化脚本**:
```python
# scripts/update_imports.py
import re
from pathlib import Path

IMPORT_MAPPINGS = {
    'from error_handler import': 'from webfetcher.errors import',
    'from error_classifier import': 'from webfetcher.errors.classifier import',
    'from error_types import': 'from webfetcher.errors.types import',
    'from error_cache import': 'from webfetcher.errors.cache import',

    'from parsers import': 'from webfetcher.parsing import',
    'from parsers_migrated import': 'from webfetcher.parsing.templates import',
    'from parsers_legacy import': 'from webfetcher.parsing.legacy import',

    'from selenium_fetcher import': 'from webfetcher.fetchers.selenium import',
    'from selenium_config import': 'from webfetcher.fetchers.config import',

    'from url_formatter import': 'from webfetcher.utils.url_formatter import',

    'from routing import': 'from webfetcher.routing import',
    'from manual_chrome import': 'from webfetcher.manual import',
    'from drivers import': 'from webfetcher.drivers import',
}

def update_imports(file_path):
    content = file_path.read_text()
    modified = False

    for old, new in IMPORT_MAPPINGS.items():
        if old in content:
            content = content.replace(old, new)
            modified = True

    if modified:
        file_path.write_text(content)
        print(f"Updated: {file_path}")

# 更新所有Python文件
for py_file in Path('webfetcher').rglob('*.py'):
    update_imports(py_file)

update_imports(Path('wf.py'))
```

### Phase 4: 更新wf.py入口（中等风险）
```python
# wf.py 简化版本
#!/usr/bin/env python3
"""Web Fetcher CLI - Simplified entry point."""
import sys
from pathlib import Path

# 确保webfetcher包可导入
sys.path.insert(0, str(Path(__file__).parent))

from webfetcher.cli import main

if __name__ == '__main__':
    main()
```

提取CLI逻辑到 `webfetcher/cli.py`:
```python
# webfetcher/cli.py
"""CLI implementation for wf command."""
# ... 原wf.py的所有逻辑 ...
```

### Phase 5: 验证和测试
```bash
# 1. 验证导入
python -c "import webfetcher; print('✓ Package import OK')"
python -c "from webfetcher.errors import ChromeDebugError; print('✓ Errors OK')"
python -c "from webfetcher.parsing import wechat_to_markdown; print('✓ Parsing OK')"

# 2. 测试CLI
./wf.py diagnose
./wf.py "https://mp.weixin.qq.com/s/test"

# 3. 运行测试套件
pytest tests/ -v

# 4. 检查依赖
pip install -r requirements/base.txt
pip install -r requirements/selenium.txt
```

## ⚖️ 方案对比

### 本方案 vs. Full Src-Layout

| 特性 | 本方案 | Full Src-Layout | 优势 |
|------|--------|-----------------|------|
| 复杂度 | 中等 | 高 | ✓ 本方案更简洁 |
| CLI便捷性 | 高（wf.py在根目录） | 低（需要安装） | ✓ 本方案更便捷 |
| 模块化程度 | 良好 | 优秀 | Src-Layout更规范 |
| 迁移成本 | 中等 | 高 | ✓ 本方案成本更低 |
| 可维护性 | 良好 | 优秀 | Src-Layout更专业 |
| 适合场景 | 小团队/个人项目 | 大型/企业项目 | ✓ 本方案更适合 |

### 关键决策

1. **不使用 src/ 目录** - 直接使用 webfetcher/ 作为顶层包
   - ✓ 更简单，减少嵌套
   - ✓ CLI可以直接运行 `./wf.py`
   - ✗ 不符合最新Python打包最佳实践（但项目不需要发布）

2. **保留 wf.py 在根目录** - 不移入 webfetcher/cli/
   - ✓ 用户习惯的入口点不变
   - ✓ 可以直接 `./wf.py` 运行
   - ✗ 根目录多一个文件（可接受）

3. **模块化关键部分** - errors/, parsing/, fetchers/
   - ✓ 清理根目录
   - ✓ 逻辑分组清晰
   - ✓ 易于单元测试

4. **configs/ 而非 config/** - 语义更清晰
   - ✓ 表明这是配置文件集合
   - ✓ 与 webfetcher/config/（代码）区分

## 📋 执行检查清单

### 迁移前
- [ ] 备份整个项目
- [ ] 确认git状态干净
- [ ] 记录当前功能测试结果
- [ ] 准备回滚方案

### Phase 1完成后
- [ ] 新目录结构创建完成
- [ ] pyproject.toml配置正确
- [ ] .gitignore覆盖所有需要忽略的文件

### Phase 2完成后
- [ ] 所有文件已移动到新位置
- [ ] __init__.py文件创建完成
- [ ] 原位置文件已删除

### Phase 3完成后
- [ ] 所有导入路径已更新
- [ ] 运行import测试通过
- [ ] 无明显语法错误

### Phase 4完成后
- [ ] wf.py简化完成
- [ ] webfetcher/cli.py创建
- [ ] CLI功能正常

### Phase 5完成后
- [ ] 所有测试通过
- [ ] wf diagnose正常
- [ ] 实际抓取测试正常
- [ ] 文档已更新

## 🎯 预期收益

1. **代码组织** - 根目录从12个Python文件减少到1个（wf.py）
2. **可维护性** - 模块职责清晰，易于定位和修改
3. **可测试性** - 模块化后更容易编写单元测试
4. **可扩展性** - 新功能可以按模块组织，不会污染根目录
5. **专业性** - 项目结构更符合Python最佳实践
6. **文档化** - 配置、文档、归档分类清晰

## ⚠️ 风险控制

1. **导入路径错误** - 使用自动化脚本，逐个验证
2. **功能退化** - 每个Phase后运行完整测试
3. **用户影响** - wf命令用法保持不变
4. **回滚方案** - 保持git历史，可随时回退

## 📚 后续工作

1. **编写测试** - 补充单元测试和集成测试
2. **完善文档** - 更新架构文档和使用指南
3. **持续优化** - 根据使用情况调整结构
4. **考虑打包** - 如需分发，可进一步迁移到src-layout
