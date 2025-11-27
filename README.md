# Web Fetcher 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![GitHub Stars](https://img.shields.io/github/stars/ttieli/web-fetcher.svg)](https://github.com/ttieli/web-fetcher/stargazers)

智能网页内容抓取工具，支持微信公众号、小红书、Google搜索等多种网站的内容提取和Markdown转换。

## ✨ 核心特性

- 🎯 **智能路由** - 自动识别网站类型，选择最佳抓取策略
- 📝 **模板解析** - 基于YAML的灵活内容提取系统
- 🔄 **多级回退** - urllib → CDP → Selenium三级智能回退
- 🌐 **广泛兼容** - 支持静态网站和JavaScript动态渲染页面
- 📊 **结构化输出** - 格式化的Markdown文件，保留完整元数据
- 🔍 **Google搜索** - 专业的搜索结果提取（含图片、描述、相关搜索）
- 📋 **智能列表识别** - 自动修正列表层级，优化新闻专题页阅读体验
- 🎨 **模板系统** - 轻松添加新网站支持

## 🚀 快速开始

### 安装

**方式1：pipx 安装（推荐）**

```bash
# 安装 pipx（如果还没有）
brew install pipx
pipx ensurepath

# 安装 webfetcher
pipx install 'git+https://github.com/ttieli/web-fetcher.git'

# 验证安装
wf --help
```

**方式2：一键部署脚本**

```bash
git clone https://github.com/ttieli/web-fetcher.git
cd web-fetcher
./bootstrap.sh  # macOS/Linux
# 或
./bootstrap.ps1 # Windows
```

### 基本用法

```bash
# 抓取微信文章
wf https://mp.weixin.qq.com/s/xxxxx

# Google搜索结果
wf "https://www.google.com/search?q=人工智能"

# 小红书内容
wf https://www.xiaohongshu.com/discovery/item/xxxxx

# 指定输出目录
wf https://example.com -o ~/Desktop/

# 快速模式（仅静态抓取）
wf fast https://example.com

# 强制使用Selenium
wf --fetch-mode selenium https://example.com
```

## 📸 示例输出

### Google搜索结果

提取结构化的搜索结果，包括：
- ✅ 搜索结果标题和链接
- ✅ 描述性文字摘要
- ✅ 图片缩略图（📸 图片部分）
- ✅ 相关搜索建议
- ✅ 新闻结果（含时间戳）

```markdown
## 🔍 搜索结果

### 1. 大熊猫- 维基百科，自由的百科全书

**来源:** [https://zh.wikipedia.org›...](url)
**链接:** <https://zh.wikipedia.org/...>

大熊猫（学名：Ailuropoda melanoleuca），属于食肉目熊科的一种哺乳动物，
体色为黑白两色。是中国特有物种，现存的主要栖息地是中国中西部四川盆地...

## 📸 图片
[缩略图显示...]
```

### 微信公众号

- 标题、作者、发布时间
- 完整正文内容
- 图片链接保留
- 原始URL和访问URL双记录

## 🎯 支持的网站

| 网站类型 | 支持状态 | 特殊功能 |
|---------|---------|---------|
| 微信公众号 | ✅ | 完整内容提取 |
| 小红书 | ✅ | 图文视频内容 |
| Google搜索 | ✅ | 结构化搜索结果 |
| Wikipedia | ✅ | 多语言支持 |
| 新闻网站 | ✅ | 正文提取 |
| 新华网专题 | ✅ | 专题列表优化 |
| 通用网站 | ✅ | 自动适配 |

## 🔧 高级功能

### 环境变量

```bash
# 设置默认输出目录
export WF_OUTPUT_DIR=~/Documents/articles

# 设置Selenium超时
export WF_SELENIUM_TIMEOUT=60
```

### 命令行选项

```bash
# 获取模式选择
wf --fetch-mode [urllib|cdp|selenium] <url>

# 站点爬虫
wf site <url> --max-pages 100 --max-depth 5

# 使用sitemap
wf site <url> --use-sitemap

# 系统诊断
wf diagnose
```

### Chrome调试模式

```bash
# 启动Chrome调试服务器
./config/start_chrome_debug.sh

# 使用CDP模式
wf --fetch-mode cdp https://example.com
```

## 📁 项目结构

```
Web_Fetcher/
├── src/webfetcher/       # 核心包
│   ├── cli.py            # CLI 入口
│   ├── core.py           # 核心引擎
│   ├── fetchers/         # 获取器（urllib, CDP, Selenium）
│   ├── parsing/          # 解析器和模板引擎
│   ├── routing/          # 智能路由系统
│   └── errors/           # 错误处理
├── config/               # 配置文件
│   ├── templates/        # 网站模板（YAML）
│   └── routing_config.yaml
├── docs/                 # 文档
├── tests/                # 测试套件
├── bootstrap.sh          # 一键部署脚本
└── pyproject.toml        # 项目配置
```

## 🤝 贡献指南

### 添加新网站支持

1. **创建模板文件** `config/templates/your_site.yaml`:

```yaml
name: "Your Site Template"
domains:
  - yoursite.com
content_extraction:
  selectors:
    title: "h1.title"
    content: "div.content"
```

2. **测试模板**:

```bash
wf https://yoursite.com/article
```

3. **提交PR**

### 运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 测试urllib vs CDP性能
python tests/compare_urllib_cdp.py
```

## 📚 文档

- [CDP集成说明](docs/CDP_INTEGRATION_SUMMARY.md)
- [安全检查](docs/SECURITY_CHECK.md)
- [更新日志](CHANGELOG.md)

## ❓ 常见问题 (FAQ)

<details>
<summary><b>Q: 如何更新到最新版本？</b></summary>

```bash
# pipx方式
pipx upgrade webfetcher
# 或强制重装
pipx install --force 'git+https://github.com/ttieli/web-fetcher.git'
```
</details>

<details>
<summary><b>Q: 为什么有些网站抓取失败？</b></summary>

尝试不同的fetch模式：
```bash
# 尝试CDP模式
wf --fetch-mode cdp <url>

# 尝试Selenium模式（最可靠但较慢）
wf --fetch-mode selenium <url>
```
</details>

<details>
<summary><b>Q: 如何添加自定义网站模板？</b></summary>

参考 `config/templates/` 目录下的现有模板，创建YAML配置文件。
</details>

<details>
<summary><b>Q: Google搜索结果为什么没有描述文字？</b></summary>

新版本已优化snippet提取逻辑，确保安装最新版本：
```bash
pipx install --force 'git+https://github.com/ttieli/web-fetcher.git'
```
</details>

<details>
<summary><b>Q: 输出文件保存在哪里？</b></summary>

默认保存在 `output/` 目录，可通过 `-o` 参数或 `WF_OUTPUT_DIR` 环境变量自定义。
</details>

## 🐛 问题反馈

遇到问题？请[提交Issue](https://github.com/ttieli/web-fetcher/issues)并提供：
- 运行命令
- 错误信息
- 目标URL（如果可以公开）
- `wf diagnose` 输出

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🌟 致谢

感谢所有贡献者和使用者的支持！

---

**最新版本:** v1.1.1 (2025-11-27)
**作者:** ttieli
**项目主页:** https://github.com/ttieli/web-fetcher
