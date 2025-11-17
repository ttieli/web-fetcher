# Web Fetcher

智能网页内容抓取工具，支持微信公众号、小红书等多种网站的内容提取和Markdown转换。

## 快速开始

### 安装方式

#### 方式1：pipx 安装（推荐）

```bash
# 安装 pipx（如果还没有）
brew install pipx
pipx ensurepath

# 安装 webfetcher（自动安装/升级到最新版本）
pipx install --force 'git+https://github.com/ttieli/web-fetcher.git#egg=webfetcher[selenium]'

# 验证安装
wf --help
```

#### 方式2：克隆仓库 + 一键部署

```bash
# 克隆仓库
git clone https://github.com/ttieli/web-fetcher.git
cd web-fetcher

# 一键部署（macOS/Linux）
./bootstrap.sh

# 激活环境并使用
source .venv/bin/activate
wf https://mp.weixin.qq.com/s/xxxxx
```

#### 方式3：pip 安装（虚拟环境）

```bash
# 创建虚拟环境
python3 -m venv ~/webfetcher-env
source ~/webfetcher-env/bin/activate

# 从 GitHub 安装
pip install 'git+https://github.com/ttieli/web-fetcher.git#egg=webfetcher[selenium]'
```

### 更新到最新版本

```bash
# pipx 方式
pipx upgrade webfetcher

# 或强制重新安装最新版
pipx install --force 'git+https://github.com/ttieli/web-fetcher.git#egg=webfetcher[selenium]'

# pip 方式
pip install -U 'git+https://github.com/ttieli/web-fetcher.git#egg=webfetcher[selenium]'
```

### 基本用法

```bash
# 最简单的用法
wf https://mp.weixin.qq.com/s/xxxxx

# 指定输出目录
wf https://example.com -o ~/Desktop/

# 快速模式（仅静态抓取）
wf fast https://example.com

# 完整模式（包含资源）
wf full https://example.com

# 系统诊断
wf diagnose
```

## 功能特性

- ✅ **智能路由** - 自动识别网站类型，选择最佳抓取方式
- ✅ **模板解析** - 基于YAML模板的内容提取
- ✅ **Selenium支持** - 处理JavaScript动态加载的页面
- ✅ **Markdown输出** - 清晰格式化的Markdown文件
- ✅ **URL跟踪** - 保留原始URL和访问URL双记录
- ✅ **错误处理** - 统一的错误分类和重试机制

## 项目结构

```
Web_Fetcher/
├── src/
│   └── webfetcher/          # 核心包
│       ├── cli.py           # CLI 入口
│       ├── core.py          # 核心引擎
│       ├── errors/          # 错误处理
│       ├── parsing/         # 解析器（含模板引擎）
│       ├── fetchers/        # 获取器（Selenium等）
│       ├── routing/         # 智能路由
│       ├── utils/           # 工具函数
│       ├── manual/          # 手动Chrome集成
│       └── drivers/         # ChromeDriver管理
├── config/                  # 配置文件
├── tests/                   # 测试文件
├── bootstrap.sh             # 一键部署脚本（macOS/Linux）
├── bootstrap.ps1            # 一键部署脚本（Windows）
├── pyproject.toml           # 项目配置
└── output/                  # 默认输出目录
```

## 支持的网站

- 微信公众号（mp.weixin.qq.com）
- 小红书（xiaohongshu.com）
- 维基百科（wikipedia.org）
- 新闻网站（news.cn等）
- 通用网站（自动适配）

## 高级用法

### 环境变量

```bash
# 设置默认输出目录
export WF_OUTPUT_DIR=~/Documents/articles
```

### 命令行选项

```bash
# Selenium相关
wf --fetch-mode selenium <url>        # 强制使用Selenium
wf --selenium-timeout 60 <url>        # 设置超时时间

# 站点爬虫
wf site <url> --max-pages 100         # 限制页面数
wf site <url> --max-depth 5           # 限制深度
wf site <url> --use-sitemap           # 使用sitemap.xml
```

## 开发

### 运行测试

```bash
pytest tests/ -v
```

### 更新ChromeDriver

```bash
python scripts/manage_chromedriver.py sync
```

## 文档

- 架构文档：`archive/PROJECT_RESTRUCTURE_PLAN.md`
- 依赖分析：`archive/ROOT_FILES_DEPENDENCY_ANALYSIS.md`
- 重组报告：`archive/RESTRUCTURE_COMPLETION_REPORT.md`

## 许可证

MIT License

## 版本

v1.0.0 - 模块化重组版本（2025-11-17）
