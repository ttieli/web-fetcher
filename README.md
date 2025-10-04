# Web_Fetcher (urllib 稳定版)

支持小红书和微信内容抓取的网页内容提取工具

## 项目特色 / Key Features

- **🔄 基于 urllib 的稳定 HTTP 抓取** - 使用 Python 标准库，无需复杂依赖
- **🌐 Chrome 自动集成** - 自动管理 Chrome 调试实例，支持复杂页面抓取
- **📱 微信公众号文章提取** - 专门优化的微信公众号内容解析器
- **📍 小红书内容解析** - 支持小红书笔记和用户内容提取
- **📄 双格式输出** - 支持 Markdown 和 HTML 两种输出格式
- **🏗️ 简洁的 3 文件架构** - 核心功能集中在三个文件中，易于维护

## 项目架构 / Project Structure

```
Web_Fetcher/
├── webfetcher.py    # 核心抓取引擎和CLI接口
├── parsers.py       # 网站特定的内容解析器
├── wf.py           # 便捷命令行工具
├── output/         # 默认输出目录
└── tests/          # 测试文件
```

## 支持的网站 / Supported Sites

### 🔥 专门优化支持
- **微信公众号** (`mp.weixin.qq.com`) - 文章内容、标题、发布时间
- **小红书** (`xiaohongshu.com`) - 笔记内容、图片、用户信息

### 🌐 通用支持
- 其他网站使用通用解析器，自动提取主要内容

## 安装和使用 / Installation & Usage

### 基本使用

```bash
# 使用便捷工具 wf.py (自动选择最佳抓取模式)
./wf.py <URL>

# 或直接使用主程序
python3 webfetcher.py <URL>

# 强制使用 Chrome/Selenium 模式（适用于动态页面）
./wf.py <URL> --fetch-mode selenium

# 强制使用 urllib 模式（快速、轻量）
./wf.py <URL> --force-urllib
```

### Chrome 集成功能

Web_Fetcher 现已支持自动 Chrome 管理：

```bash
# 首次使用时，系统会自动启动 Chrome 调试实例
./wf.py https://example.com

# 检查 Chrome 状态
./config/ensure-chrome-debug.sh --check-only

# 使用自定义端口
./wf.py https://example.com --debug-port 9333

# 强制重启 Chrome
./wf.py https://example.com --force-restart
```

**macOS 权限设置：**
如果遇到权限问题，请参阅 [Chrome 集成指南](docs/chrome_integration.md#prerequisites--前置条件)

### 输出格式选项

```bash
# Markdown 输出 (默认)
./wf.py https://mp.weixin.qq.com/s/example

# HTML 输出
./wf.py https://mp.weixin.qq.com/s/example --format html

# 指定输出目录
./wf.py https://xiaohongshu.com/explore/example -o ./my_output/
```

### 环境变量配置

```bash
# 设置默认输出目录
export WF_OUTPUT_DIR="./my_default_output/"

# Chrome 相关配置
export CHROME_DEBUG_PORT=9222  # Chrome 调试端口
export CHROME_STARTUP_TIMEOUT=15  # 启动超时（秒）
export WF_DISABLE_AUTO_CHROME=1  # 禁用自动 Chrome（如需要）
```

## 输出文件命名 / Output File Naming

文件按以下格式自动命名：
```
YYYY-MM-DD-HHMMSS - 文章标题.{md|html}
```

示例：
```
2025-09-29-143346 - 北京·首钢园 永定河集：京西的快闪乌托邦.md
2025-09-29-150357 - 小红书笔记标题.html
```

## 技术特点 / Technical Features

### 🛡️ 稳定性优先
- 基于 Python 标准库 `urllib`，避免第三方依赖冲突
- 移除了不稳定的 Safari 集成和插件系统
- 专注于核心功能，提供可靠的内容抓取

### 🎯 智能解析
- **WeChat 解析器**: 专门处理微信公众号文章格式
- **Xiaohongshu 解析器**: 优化小红书内容结构提取
- **通用解析器**: 自动识别和提取其他网站的主要内容

### 📁 输出管理
- 智能输出路径优先级：命令行参数 > 环境变量 > 默认目录
- 自动创建输出目录
- 避免文件名冲突的时间戳命名

### ⚠️ 统一错误处理
- **智能错误分类**: 自动将错误分为7大类别（网络连接、浏览器初始化、页面加载、权限、依赖、超时、未知）
- **详细故障排除指南**: 每个错误类别提供针对性的解决步骤和常见原因分析
- **自动报告生成**: 失败时自动生成包含根因分析和技术详情的Markdown报告
- **零配置集成**: 错误处理已自动集成到webfetcher，无需手动配置
- **性能优化**: 错误分类速度<1ms，对正常流程影响可忽略

详细使用方法请参阅：[错误处理指南](docs/error_handling_guide.md) | [故障排除手册](docs/troubleshooting_manual.md)

## 依赖要求 / Requirements

### 核心依赖（必需）
- Python 3.7+
- 标准库模块：`urllib`, `html.parser`, `argparse`

### 可选依赖（增强功能）
- `beautifulsoup4` - 提供更好的 HTML 解析能力
- `lxml` - 加快 BeautifulSoup 解析速度

```bash
# 安装可选依赖以获得最佳体验
pip install beautifulsoup4 lxml
```

## 版本历史 / Version History

### v1.1.0 - Chrome 集成版 (2025-10-04)
- ✅ 新增 Chrome 自动启动和管理功能
- ✅ 实现 Chrome 健康检查和自动恢复
- ✅ 添加 5 个 Chrome 专用异常类和双语错误消息
- ✅ 完成 18 个集成测试场景和性能基准测试
- ✅ 支持 Selenium 和 urllib 智能切换

### v1.0.0 - urllib 稳定版
- ✅ 完成项目重构，移除不稳定的 Safari 集成
- ✅ 移除复杂的插件系统
- ✅ 简化为 3 文件架构
- ✅ 专注于微信和小红书内容抓取
- ✅ 添加 HTML 输出格式支持

### 近期更新
- **2025-10-04**: Chrome 调试守护进程集成完成
- **Phase 4.1**: 清理非核心解析器，专注主要功能
- **Phase 3.x**: 移除 extractors 目录和未使用的解析器
- **Phase 2.x**: 完全移除插件系统和 Safari 集成

## 开发说明 / Development Notes

这个项目经过多轮重构，现在专注于：
1. **稳定性** - 使用标准库，减少外部依赖
2. **专业性** - 专门针对中文内容平台优化
3. **简洁性** - 3 文件架构，易于理解和维护

## 许可证 / License

本项目遵循 MIT 许可证。

---

**Web_Fetcher Team** | 专注于中文内容平台的网页抓取解决方案