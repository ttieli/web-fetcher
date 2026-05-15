"""
WebFetcher - 智能网页内容抓取工具
支持微信公众号、小红书等多种网站的内容提取和Markdown转换
"""

__version__ = "1.3.6"

# 导出 CLI 的 main 函数，用于 [project.scripts] 注册
from .cli import main

# 回归测试套件依赖：从 core 重新导出
from .core import fetch_html_with_retry, FetchMetrics

__all__ = ['main', '__version__', 'fetch_html_with_retry', 'FetchMetrics']
