"""Web content fetchers (Selenium, CDP, etc)."""
# Conditional imports to handle optional dependencies

# Selenium support
try:
    from .selenium import SeleniumFetcher, SeleniumMetrics
    from .selenium import ChromeConnectionError, SeleniumFetchError
    from .selenium import SeleniumTimeoutError, SeleniumNotAvailableError
    from .config import SeleniumConfig
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# CDP support
try:
    from .cdp_scraper import CDPScraper, CDPMetrics
    from .cdp_scraper import CDPNotAvailableError, CDPConnectionError
    from .cdp_scraper import CDPFetchError, CDPTimeoutError
    from .cdp_scraper import is_cdp_available, check_chrome_debug_running
    CDP_AVAILABLE = True
except ImportError:
    CDP_AVAILABLE = False

__all__ = []
if SELENIUM_AVAILABLE:
    __all__.extend([
        'SeleniumFetcher', 'SeleniumMetrics', 'SeleniumConfig',
        'ChromeConnectionError', 'SeleniumFetchError',
        'SeleniumTimeoutError', 'SeleniumNotAvailableError'
    ])
if CDP_AVAILABLE:
    __all__.extend([
        'CDPScraper', 'CDPMetrics',
        'CDPNotAvailableError', 'CDPConnectionError',
        'CDPFetchError', 'CDPTimeoutError',
        'is_cdp_available', 'check_chrome_debug_running'
    ])
