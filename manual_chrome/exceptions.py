"""
Custom exceptions for Manual Chrome module

These exceptions provide clear error handling and diagnostic information
for various failure scenarios in the manual Chrome workflow.
"""


class ManualChromeError(Exception):
    """Base exception for all manual Chrome errors"""
    pass


class ChromeNotFoundError(ManualChromeError):
    """Raised when Chrome browser is not found at expected location"""

    def __init__(self, message="Chrome browser not found"):
        self.message = message
        super().__init__(self.message)


class PortInUseError(ManualChromeError):
    """Raised when the debug port is already in use"""

    def __init__(self, port, message=None):
        self.port = port
        if message is None:
            message = (
                f"Port {port} is already in use.\n\n"
                f"Solutions:\n"
                f"1. Close existing Chrome debug session\n"
                f"2. Configure a different port in manual_chrome_config.yaml\n"
                f"3. Kill process using: lsof -ti:{port} | xargs kill -9"
            )
        self.message = message
        super().__init__(self.message)


class AttachmentError(ManualChromeError):
    """Raised when unable to attach to Chrome via CDP"""

    def __init__(self, message="Failed to attach to Chrome debug session"):
        self.message = message
        super().__init__(self.message)


class TimeoutError(ManualChromeError):
    """Raised when user doesn't complete navigation within timeout period"""

    def __init__(self, timeout_seconds, message=None):
        self.timeout_seconds = timeout_seconds
        if message is None:
            message = (
                f"Timeout after {timeout_seconds} seconds.\n"
                f"User did not complete navigation in time."
            )
        self.message = message
        super().__init__(self.message)


class NavigationError(ManualChromeError):
    """Raised when page navigation fails or results in error state"""

    def __init__(self, url, message=None):
        self.url = url
        if message is None:
            message = f"Navigation to {url} failed or resulted in error state"
        self.message = message
        super().__init__(self.message)
