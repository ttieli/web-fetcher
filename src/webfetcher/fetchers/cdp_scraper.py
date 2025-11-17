"""
CDP (Chrome DevTools Protocol) Scraper for WebFetcher

完整的CDP浏览器会话复用抓取器,支持:
- 复用真实浏览器会话保持登录状态
- 提取渲染后的DOM内容
- 监听网络请求和API调用
- 执行JavaScript代码
- 截图功能
- Cookie/LocalStorage导出

Architecture:
- 连接到已启动的Chrome调试实例 (localhost:9222)
- 避免自动化检测,保持真实用户会话
- 适用于反爬强、需要登录、JS渲染的网站

Author: WebFetcher Team
Date: 2025-11-17
Version: 1.0.0
"""

import time
import json
import base64
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

# Conditional import - graceful degradation when pychrome not available
try:
    import pychrome
    PYCHROME_AVAILABLE = True
except ImportError:
    PYCHROME_AVAILABLE = False
    logging.debug("pychrome not available - CDP功能将不可用")


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class CDPMetrics:
    """CDP抓取性能指标"""
    connection_time: float = 0.0  # 连接时间
    navigation_time: float = 0.0  # 页面导航时间
    render_time: float = 0.0      # 渲染等待时间
    total_time: float = 0.0       # 总耗时
    api_calls_count: int = 0      # 监听到的API调用数量
    success: bool = False         # 是否成功
    error_message: str = ""       # 错误信息


# ============================================================================
# Custom Exceptions
# ============================================================================

class CDPNotAvailableError(Exception):
    """CDP功能不可用 (pychrome未安装)"""
    pass


class CDPConnectionError(Exception):
    """CDP连接失败"""
    pass


class CDPFetchError(Exception):
    """CDP抓取失败"""
    pass


class CDPTimeoutError(Exception):
    """CDP操作超时"""
    pass


# ============================================================================
# CDP Scraper Core
# ============================================================================

class CDPScraper:
    """
    完整的CDP浏览器会话复用抓取器

    使用方法:
    1. 启动Chrome调试模式: ./scripts/start_chrome.sh
    2. 创建scraper: scraper = CDPScraper()
    3. 创建或连接标签页: tab = scraper.new_tab(url)
    4. 抓取内容: html = scraper.get_html(tab)
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9222, timeout: int = 10):
        """
        初始化CDP抓取器

        Args:
            host: Chrome调试服务器地址
            port: Chrome调试端口 (默认9222)
            timeout: 连接超时时间(秒)
        """
        if not PYCHROME_AVAILABLE:
            raise CDPNotAvailableError(
                "pychrome未安装。请运行: pip install pychrome\n"
                "或安装完整依赖: pip install webfetcher[cdp]"
            )

        self.host = host
        self.port = port
        self.timeout = timeout
        self.url = f"http://{host}:{port}"
        self.browser = None
        self.logger = logging.getLogger(__name__)

        self.logger.info(f"CDP Scraper初始化: {self.url}")

    # ========================================================================
    # 连接与标签页管理
    # ========================================================================

    def connect(self) -> bool:
        """
        连接到Chrome调试实例

        Returns:
            bool: 连接是否成功

        Raises:
            CDPConnectionError: 连接失败
        """
        try:
            start_time = time.time()
            self.browser = pychrome.Browser(url=self.url)

            # 测试连接 - 尝试列出标签页
            self.browser.list_tab()

            connection_time = time.time() - start_time
            self.logger.info(f"CDP连接成功 (耗时: {connection_time:.2f}s)")
            return True

        except Exception as e:
            error_msg = f"CDP连接失败: {str(e)}\n"
            error_msg += "请确保Chrome已在调试模式下运行:\n"
            error_msg += "  ./scripts/start_chrome.sh\n"
            error_msg += f"  或手动启动: chrome --remote-debugging-port={self.port}"

            self.logger.error(error_msg)
            raise CDPConnectionError(error_msg)

    def list_tabs(self) -> List[Any]:
        """
        列出所有打开的标签页

        Returns:
            标签页列表
        """
        if not self.browser:
            self.connect()

        tabs = self.browser.list_tab()
        self.logger.info(f"当前标签页数量: {len(tabs)}")
        for i, t in enumerate(tabs):
            self.logger.debug(f"  [{i}] {t.url}")

        return tabs

    def attach(self, tab_index: int = 0) -> Any:
        """
        连接到已存在的标签页

        Args:
            tab_index: 标签页索引 (默认0,即第一个)

        Returns:
            标签页对象
        """
        tabs = self.list_tabs()
        if tab_index >= len(tabs):
            raise CDPFetchError(f"标签页索引{tab_index}不存在,总共{len(tabs)}个标签页")

        tab = tabs[tab_index]
        self._enable_tab(tab)

        self.logger.info(f"已连接到标签页 [{tab_index}]: {tab.url}")
        return tab

    def new_tab(self, url: Optional[str] = None, wait_load: float = 2.0) -> Any:
        """
        创建新标签页

        Args:
            url: 要访问的URL (可选)
            wait_load: 页面加载等待时间(秒)

        Returns:
            新标签页对象
        """
        if not self.browser:
            self.connect()

        tab = self.browser.new_tab()
        self._enable_tab(tab)

        if url:
            self.logger.info(f"新标签页导航到: {url}")
            tab.Page.navigate(url=url)
            time.sleep(wait_load)  # 等待页面加载

        return tab

    def _enable_tab(self, tab: Any):
        """启用标签页的必要功能"""
        tab.start()
        tab.Network.enable()
        tab.Page.enable()
        tab.Runtime.enable()

    def close_tab(self, tab: Any):
        """关闭标签页"""
        try:
            tab.stop()
            self.logger.debug("标签页已关闭")
        except Exception as e:
            self.logger.warning(f"关闭标签页失败: {e}")

    # ========================================================================
    # DOM 操作
    # ========================================================================

    def get_html(self, tab: Any) -> str:
        """
        获取渲染后的完整HTML

        Args:
            tab: 标签页对象

        Returns:
            完整的HTML源码
        """
        try:
            result = tab.Runtime.evaluate(
                expression="document.documentElement.outerHTML"
            )
            html = result.get("result", {}).get("value", "")

            self.logger.debug(f"获取HTML成功,长度: {len(html)}")
            return html

        except Exception as e:
            self.logger.error(f"获取HTML失败: {e}")
            raise CDPFetchError(f"获取HTML失败: {e}")

    def get_text(self, tab: Any) -> str:
        """
        获取页面纯文本内容

        Args:
            tab: 标签页对象

        Returns:
            页面文本
        """
        try:
            result = tab.Runtime.evaluate(
                expression="document.body.innerText || document.body.textContent"
            )
            return result.get("result", {}).get("value", "")
        except Exception as e:
            self.logger.error(f"获取文本失败: {e}")
            return ""

    def query_selector(self, tab: Any, selector: str) -> Optional[str]:
        """
        使用CSS选择器提取文本

        Args:
            tab: 标签页对象
            selector: CSS选择器

        Returns:
            提取的文本内容
        """
        try:
            js = f"""
            (function() {{
                const el = document.querySelector('{selector}');
                return el ? (el.innerText || el.textContent) : null;
            }})();
            """
            result = tab.Runtime.evaluate(expression=js)
            return result.get("result", {}).get("value")
        except Exception as e:
            self.logger.warning(f"查询选择器'{selector}'失败: {e}")
            return None

    def query_selector_all(self, tab: Any, selector: str) -> List[str]:
        """
        使用CSS选择器提取所有匹配元素的文本

        Args:
            tab: 标签页对象
            selector: CSS选择器

        Returns:
            文本列表
        """
        try:
            js = f"""
            Array.from(document.querySelectorAll('{selector}'))
                 .map(el => el.innerText || el.textContent);
            """
            result = tab.Runtime.evaluate(expression=js)
            value = result.get("result", {}).get("value", [])
            return value if isinstance(value, list) else []
        except Exception as e:
            self.logger.warning(f"查询选择器all'{selector}'失败: {e}")
            return []

    # ========================================================================
    # 页面导航
    # ========================================================================

    def navigate(self, tab: Any, url: str, wait_load: float = 2.0) -> bool:
        """
        导航到指定URL

        Args:
            tab: 标签页对象
            url: 目标URL
            wait_load: 等待加载时间(秒)

        Returns:
            是否成功
        """
        try:
            self.logger.info(f"导航到: {url}")
            tab.Page.navigate(url=url)
            time.sleep(wait_load)
            return True
        except Exception as e:
            self.logger.error(f"导航失败: {e}")
            return False

    def wait_for_selector(self, tab: Any, selector: str,
                          timeout: float = 10.0,
                          interval: float = 0.5) -> bool:
        """
        等待元素出现

        Args:
            tab: 标签页对象
            selector: CSS选择器
            timeout: 超时时间(秒)
            interval: 检查间隔(秒)

        Returns:
            元素是否出现
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            js = f"document.querySelector('{selector}') !== null"
            result = tab.Runtime.evaluate(expression=js)
            if result.get("result", {}).get("value"):
                self.logger.debug(f"元素'{selector}'已出现")
                return True
            time.sleep(interval)

        self.logger.warning(f"等待元素'{selector}'超时")
        return False

    # ========================================================================
    # 截图
    # ========================================================================

    def screenshot(self, tab: Any, filename: str = "screenshot.png") -> bool:
        """
        截取当前页面

        Args:
            tab: 标签页对象
            filename: 保存文件名

        Returns:
            是否成功
        """
        try:
            shot = tab.Page.captureScreenshot()
            with open(filename, "wb") as f:
                f.write(base64.b64decode(shot["data"]))

            self.logger.info(f"截图已保存: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            return False

    # ========================================================================
    # 网络监听
    # ========================================================================

    def watch_network(self, tab: Any):
        """
        开始监听网络请求

        监听后,可通过 tab._requests 和 tab._responses 访问记录

        Args:
            tab: 标签页对象
        """
        tab._requests = []
        tab._responses = []

        def on_request(**kwargs):
            req = kwargs.get("request", {})
            tab._requests.append({
                "url": req.get("url"),
                "method": req.get("method"),
                "headers": req.get("headers"),
                "timestamp": time.time()
            })

        def on_response(**kwargs):
            rsp = kwargs.get("response", {})
            tab._responses.append({
                "url": rsp.get("url"),
                "status": rsp.get("status"),
                "mimeType": rsp.get("mimeType"),
                "timestamp": time.time()
            })

        tab.Network.requestWillBeSent = on_request
        tab.Network.responseReceived = on_response

        self.logger.debug("网络监听已启动")

    def get_api_calls(self, tab: Any,
                      keywords: Optional[List[str]] = None) -> List[Dict]:
        """
        过滤API请求

        Args:
            tab: 标签页对象
            keywords: API关键词列表 (默认: ['api', 'graphql'])

        Returns:
            API请求列表
        """
        if not hasattr(tab, '_requests'):
            self.logger.warning("未启动网络监听,无法获取API调用")
            return []

        if keywords is None:
            keywords = ['api', 'graphql', 'ajax']

        apis = []
        for r in tab._requests:
            url = r.get("url", "").lower()
            if any(kw in url for kw in keywords):
                apis.append(r)

        self.logger.debug(f"发现{len(apis)}个API调用")
        return apis

    # ========================================================================
    # JavaScript执行
    # ========================================================================

    def eval_js(self, tab: Any, js_code: str) -> Any:
        """
        执行JavaScript代码

        Args:
            tab: 标签页对象
            js_code: JavaScript代码

        Returns:
            执行结果
        """
        try:
            result = tab.Runtime.evaluate(expression=js_code)
            return result.get("result", {}).get("value")
        except Exception as e:
            self.logger.error(f"执行JS失败: {e}")
            return None

    def scroll_to_bottom(self, tab: Any, wait: float = 1.0):
        """
        滚动到页面底部 (用于触发懒加载)

        Args:
            tab: 标签页对象
            wait: 滚动后等待时间(秒)
        """
        js = "window.scrollTo(0, document.body.scrollHeight);"
        self.eval_js(tab, js)
        time.sleep(wait)
        self.logger.debug("已滚动到页面底部")

    # ========================================================================
    # 会话状态导出
    # ========================================================================

    def export_session(self, tab: Any, filename: str = "session_state.json") -> Dict:
        """
        导出当前会话状态 (Cookies, localStorage, sessionStorage)

        Args:
            tab: 标签页对象
            filename: 保存文件名

        Returns:
            会话状态字典
        """
        try:
            state = {
                "cookies": tab.Network.getCookies().get("cookies", []),
                "localStorage": self.eval_js(tab, "JSON.stringify(localStorage)"),
                "sessionStorage": self.eval_js(tab, "JSON.stringify(sessionStorage)"),
                "url": self.eval_js(tab, "window.location.href"),
                "timestamp": time.time()
            }

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            self.logger.info(f"会话状态已导出: {filename}")
            return state

        except Exception as e:
            self.logger.error(f"导出会话失败: {e}")
            return {}

    # ========================================================================
    # 高级抓取方法
    # ========================================================================

    def fetch_page(self, url: str,
                   wait_load: float = 2.0,
                   wait_selector: Optional[str] = None,
                   scroll_bottom: bool = False,
                   enable_network_watch: bool = False) -> Tuple[str, CDPMetrics]:
        """
        完整的页面抓取流程

        Args:
            url: 目标URL
            wait_load: 页面加载等待时间(秒)
            wait_selector: 等待特定元素出现
            scroll_bottom: 是否滚动到底部
            enable_network_watch: 是否启用网络监听

        Returns:
            (html内容, 性能指标)
        """
        metrics = CDPMetrics()
        tab = None

        try:
            start_time = time.time()

            # 连接并创建标签页
            if not self.browser:
                self.connect()
            metrics.connection_time = time.time() - start_time

            # 创建新标签页并导航
            nav_start = time.time()
            tab = self.new_tab(url, wait_load=wait_load)
            metrics.navigation_time = time.time() - nav_start

            # 可选: 启用网络监听
            if enable_network_watch:
                self.watch_network(tab)

            # 可选: 等待特定元素
            if wait_selector:
                render_start = time.time()
                if self.wait_for_selector(tab, wait_selector):
                    metrics.render_time = time.time() - render_start
                else:
                    self.logger.warning(f"等待元素'{wait_selector}'超时")

            # 可选: 滚动到底部
            if scroll_bottom:
                self.scroll_to_bottom(tab)

            # 获取HTML
            html = self.get_html(tab)

            # 收集API调用数量
            if enable_network_watch:
                apis = self.get_api_calls(tab)
                metrics.api_calls_count = len(apis)

            metrics.total_time = time.time() - start_time
            metrics.success = True

            self.logger.info(f"抓取成功: {url} (耗时: {metrics.total_time:.2f}s)")
            return html, metrics

        except Exception as e:
            metrics.success = False
            metrics.error_message = str(e)
            metrics.total_time = time.time() - start_time

            self.logger.error(f"抓取失败: {e}")
            raise CDPFetchError(f"抓取失败: {e}")

        finally:
            # 清理: 关闭标签页
            if tab:
                self.close_tab(tab)


# ============================================================================
# Convenience Functions
# ============================================================================

def is_cdp_available() -> bool:
    """检查CDP功能是否可用"""
    return PYCHROME_AVAILABLE


def check_chrome_debug_running(host: str = "127.0.0.1", port: int = 9222) -> bool:
    """
    检查Chrome调试实例是否在运行

    Returns:
        bool: Chrome是否在运行
    """
    if not PYCHROME_AVAILABLE:
        return False

    try:
        import urllib.request
        url = f"http://{host}:{port}/json/version"
        with urllib.request.urlopen(url, timeout=2) as response:
            data = json.loads(response.read())
            return "Browser" in data
    except:
        return False
