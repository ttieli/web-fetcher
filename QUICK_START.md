# Web_Fetcher 快速开始

## 30秒设置

```bash
# 运行设置脚本
./setup.sh

# 选择安装方式：
# 1) 添加别名（推荐）
# 2) 创建软链接
# 3) 两种都安装
# 4) 配置默认输出目录（推荐）

# 然后重新加载配置
source ~/.zshrc  # 或 source ~/.bashrc
```

## 立即使用

```bash
# 最简单的用法 - 直接输入域名（保存到./output/）
wf example.com

# 指定输出目录 - 位置参数方式
wf example.com ~/Desktop/

# 快速模式 - 不渲染JS
wf fast news.site.com/article

# 完整模式 - 包含所有资源
wf full important-page.com ~/Documents/

# 整站爬虫 - 抓取整个站点
wf site docs.python.org ./python-docs/

# 批量抓取 - 从文件读取URL
wf batch sample_urls.txt ~/Downloads/
```

## 输出路径配置

三种方式配置输出路径（优先级从高到低）：

```bash
# 1. 命令行指定（最高优先级）
wf example.com ~/Desktop/          # 位置参数
wf example.com -o ~/Desktop/       # 或使用-o参数

# 2. 环境变量（中等优先级）
export WF_OUTPUT_DIR=~/Documents/web-content
wf example.com                     # 自动保存到环境变量指定的目录

# 3. 默认值（最低优先级）
wf example.com                     # 保存到./output/
```

## 高级用法

```bash
# 混合使用：指定输出目录并添加额外参数
wf fast example.com ~/Desktop/ --json --timeout 10

# 使用环境变量后的便捷操作
export WF_OUTPUT_DIR=~/Documents/fetched
wf mp.weixin.qq.com/s/xxx          # 微信文章
wf xiaohongshu.com/explore/xxx     # 小红书内容
wf site docs.python.org            # Python文档

# 使用原始webfetcher参数
wf https://example.com --crawl-site --max-pages 100 -o ~/sites/
```

## 核心优势

- **极简命令**：`wf` 只有2个字符
- **灵活输出**：支持位置参数、环境变量、默认路径
- **自动创建目录**：输出目录不存在时自动创建
- **保持兼容**：webfetcher.py保持不变
- **预设模式**：fast/full/site/batch覆盖80%场景