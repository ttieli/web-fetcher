#!/usr/bin/env python3
"""
CDP (Chrome DevTools Protocol) Fetcher
使用Chrome远程调试协议进行网页采集
"""
import time
import json
import logging
import requests
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 检查pychrome是否可用
try:
    import pychrome
    CDP_AVAILABLE = True
except ImportError:
    CDP_AVAILABLE = False
    logger.warning("pychrome not installed. CDP fetcher unavailable. Install with: pip install pychrome")


@dataclass
class CDPFetchResult:
    """CDP采集结果"""
    html: str
    final_url: str
    status_code: int = 200
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = None


class CDPFetcher:
    """
    CDP浏览器会话复用抓取器

    特点：
    - 复用真实浏览器会话（保留登录状态）
    - 自动渲染JavaScript
    - 支持网络监听
    - 可执行自定义JS
    """

    def __init__(self, host="127.0.0.1", port=9222):
        """
        初始化CDP客户端

        Args:
            host: Chrome调试服务器地址
            port: Chrome调试端口（默认9222）
        """
        if not CDP_AVAILABLE:
            raise ImportError("pychrome is required for CDP fetcher. Install with: pip install pychrome")

        self.host = host
        self.port = port
        self.url = f"http://{host}:{port}"
        self.browser = None
        self.current_tab = None

        logger.info(f"CDP Fetcher initialized: {self.url}")

    def connect(self):
        """连接到Chrome浏览器"""
        try:
            self.browser = pychrome.Browser(url=self.url)
            logger.info(f"✓ Connected to Chrome at {self.url}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to connect to Chrome: {e}")
            logger.error(f"  请确保Chrome已启动: ./config/start_chrome_debug.sh")
            return False

    def list_tabs(self):
        """列出所有标签页"""
        if not self.browser:
            self.connect()

        tabs = self.browser.list_tab()
        logger.info(f"Found {len(tabs)} tabs:")
        for i, t in enumerate(tabs):
            logger.info(f"  {i}. {t.url}")
        return tabs

    def attach_tab(self, tab_index=0):
        """
        连接到已存在的标签页

        Args:
            tab_index: 标签页索引（默认第一个）
        """
        tabs = self.browser.list_tab()
        if not tabs:
            logger.warning("No tabs available, creating new tab")
            return self.new_tab()

        tab = tabs[tab_index]
        tab.start()
        tab.Network.enable()
        tab.Page.enable()
        tab.Runtime.enable()

        self.current_tab = tab
        logger.info(f"✓ Attached to tab: {tab.url}")
        return tab

    def new_tab(self, url=None):
        """
        创建新标签页（使用PUT方法兼容新版Chrome）

        Args:
            url: 可选，创建后立即导航到该URL
        """
        # 使用PUT方法创建标签页（修复pychrome与新版Chrome的兼容性问题）
        # 新版Chrome要求使用PUT而不是GET来创建标签页
        try:
            response = requests.put(f"{self.url}/json/new")
            tab_info = response.json()

            # 使用返回的标签页ID来获取Tab对象
            tabs = self.browser.list_tab()
            tab = None
            for t in tabs:
                if hasattr(t, 'id') and str(t.id) == tab_info.get('id'):
                    tab = t
                    break

            if not tab:
                # 如果找不到，使用最后一个标签页（最新创建的）
                tab = tabs[-1] if tabs else None

            if not tab:
                raise Exception("Failed to find newly created tab")

        except Exception as e:
            logger.warning(f"PUT method failed: {e}, falling back to existing tab")
            # 如果创建失败，使用现有标签页
            tabs = self.browser.list_tab()
            if not tabs:
                raise Exception("No tabs available and cannot create new tab")
            tab = tabs[0]

        tab.start()
        tab.Network.enable()
        tab.Page.enable()
        tab.Runtime.enable()

        if url:
            tab.Page.navigate(url=url)
            time.sleep(2)  # 等待页面加载

        self.current_tab = tab
        logger.info(f"✓ Created/attached to tab{': ' + url if url else ''}")
        return tab

    def fetch(self, url: str, wait_time: float = 3.0, use_existing_tab: bool = True) -> CDPFetchResult:
        """
        使用CDP采集网页

        Args:
            url: 目标URL
            wait_time: 等待页面加载时间（秒）
            use_existing_tab: 是否复用现有标签页

        Returns:
            CDPFetchResult: 采集结果
        """
        start_time = time.time()

        try:
            # 连接到浏览器
            if not self.browser:
                if not self.connect():
                    return CDPFetchResult(
                        html="",
                        final_url=url,
                        status_code=0,
                        error="Failed to connect to Chrome",
                        duration=time.time() - start_time
                    )

            # 选择或创建标签页
            if use_existing_tab and self.current_tab:
                tab = self.current_tab
                tab.Page.navigate(url=url)
            else:
                tab = self.new_tab(url)

            # 等待页面加载
            logger.info(f"Waiting {wait_time}s for page to load...")
            time.sleep(wait_time)

            # 获取渲染后的HTML
            html = self._get_html(tab)

            # 获取当前URL（可能发生了重定向）
            final_url = self._eval_js(tab, "window.location.href")

            duration = time.time() - start_time

            logger.info(f"✓ CDP fetch completed in {duration:.2f}s")
            logger.info(f"  HTML length: {len(html)} chars")
            logger.info(f"  Final URL: {final_url}")

            return CDPFetchResult(
                html=html,
                final_url=final_url,
                status_code=200,
                error=None,
                duration=duration,
                metadata={
                    'method': 'cdp',
                    'wait_time': wait_time,
                    'tab_reused': use_existing_tab
                }
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"CDP fetch failed: {str(e)}"
            logger.error(error_msg)

            return CDPFetchResult(
                html="",
                final_url=url,
                status_code=0,
                error=error_msg,
                duration=duration
            )

    def _get_html(self, tab) -> str:
        """获取渲染后的完整HTML"""
        try:
            result = tab.Runtime.evaluate(
                expression="document.documentElement.outerHTML"
            )
            return result["result"]["value"]
        except Exception as e:
            logger.error(f"Failed to get HTML: {e}")
            return ""

    def _eval_js(self, tab, js_code: str) -> Any:
        """执行JavaScript并返回结果"""
        try:
            result = tab.Runtime.evaluate(expression=js_code)
            return result["result"]["value"]
        except Exception as e:
            logger.error(f"Failed to execute JS: {e}")
            return None

    def query_text(self, tab, selector: str) -> list:
        """使用CSS选择器提取文本"""
        js = f"""
        Array.from(document.querySelectorAll('{selector}'))
             .map(el => el.innerText || el.textContent);
        """
        return self._eval_js(tab, js) or []

    def screenshot(self, tab, filename: str = "screenshot.png"):
        """截图"""
        import base64
        try:
            shot = tab.Page.captureScreenshot()
            with open(filename, "wb") as f:
                f.write(base64.b64decode(shot["data"]))
            logger.info(f"✓ Screenshot saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return False

    def close_tab(self, tab=None):
        """关闭标签页"""
        tab = tab or self.current_tab
        if tab:
            try:
                # 抑制pychrome后台线程的JSON错误输出
                import sys
                import os
                # 临时重定向stderr来隐藏pychrome的线程错误
                old_stderr = sys.stderr
                sys.stderr = open(os.devnull, 'w')
                try:
                    tab.stop()
                    # 给后台线程一点时间来完成清理
                    time.sleep(0.1)
                finally:
                    sys.stderr.close()
                    sys.stderr = old_stderr
                logger.info("✓ Tab closed")
            except Exception as e:
                # 静默处理关闭错误，因为标签页通常已经成功关闭
                logger.debug(f"Tab close exception (ignored): {e}")

    def close(self):
        """关闭连接"""
        if self.current_tab:
            self.close_tab()
        self.browser = None
        logger.info("✓ CDP connection closed")


# ============================================================================
# 简化的函数接口（兼容现有fetcher模式）
# ============================================================================

def fetch_with_cdp(url: str, wait_time: float = 3.0, **kwargs) -> Tuple[str, str, dict]:
    """
    使用CDP采集网页（简化接口）

    Args:
        url: 目标URL
        wait_time: 等待时间
        **kwargs: 其他参数

    Returns:
        Tuple[html, final_url, metadata]
    """
    fetcher = CDPFetcher()
    result = fetcher.fetch(url, wait_time=wait_time)

    metadata = {
        'method': 'cdp',
        'status_code': result.status_code,
        'duration': result.duration,
        'error': result.error,
        **(result.metadata or {})
    }

    fetcher.close()

    if result.error:
        raise Exception(result.error)

    return result.html, result.final_url, metadata


__all__ = [
    'CDPFetcher',
    'CDPFetchResult',
    'fetch_with_cdp',
    'CDP_AVAILABLE'
]
