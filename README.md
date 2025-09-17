# Web Fetcher - 单文件网页提取工具

一个简单、强大的Python脚本，用于抓取网页内容并转换为Markdown格式。

## 特点
- **单文件设计** - 只需要webfetcher.py一个文件
- **零依赖** - 仅使用Python标准库
- **多平台支持** - 微信公众号、小红书、大众点评等
- **全站爬取** - 支持递归爬取整个网站
- **智能重试** - 自动重试和错误处理

## 快速开始

```bash
# 基本使用
python3 webfetcher.py https://example.com

# 爬取整个网站
python3 webfetcher.py https://docs.example.com --crawl-site

# 查看所有选项
python3 webfetcher.py --help
```

## 常用功能

### 单页抓取
```bash
python3 webfetcher.py https://mp.weixin.qq.com/s/xxxxx
```

### 全站爬取
```bash
python3 webfetcher.py https://docs.python.org --crawl-site --max-pages 100
```

### 保存到指定目录
```bash
python3 webfetcher.py https://example.com -o ./output
```

### 导出JSON格式
```bash
python3 webfetcher.py https://example.com --json
```

## 支持的网站
- 微信公众号文章
- 小红书笔记
- 大众点评
- Docusaurus文档
- MkDocs文档
- 通用网页

## 系统要求
- Python 3.8+
- 无需安装任何依赖包

## 许可证
MIT License

---
*简单就是美 - 1个文件，1703行代码，无限可能*