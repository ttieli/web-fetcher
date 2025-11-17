"""
WebFetcher - 智能网页内容抓取工具
支持微信公众号、小红书等多种网站的内容提取和Markdown转换
"""

__version__ = "1.0.0"

# 导出 CLI 的 main 函数，用于 [project.scripts] 注册
from .cli import main

__all__ = ['main', '__version__']
