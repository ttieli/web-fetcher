"""
Headless Chrome Manager for CDP fetcher.

Manages the lifecycle of a headless Chrome instance:
- Detect existing Chrome debug session (front-end or headless)
- Launch headless Chrome if none available
- Wait for readiness via /json/version endpoint
- Clean up on process exit (atexit + signal handlers)
- PID file for cross-invocation reuse
"""
import atexit
import json
import logging
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

# Default Chrome paths by platform
_CHROME_PATHS_MACOS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]
_CHROME_PATHS_LINUX = [
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
]

DEFAULT_PORT = 9222
FALLBACK_PORT = 9333
DATA_DIR = os.path.expanduser("~/.chrome-wf-headless")
PID_FILE = os.path.join(DATA_DIR, ".headless.pid")
READY_TIMEOUT = 15  # seconds
READY_POLL_INTERVAL = 0.3  # seconds


def _find_chrome_binary() -> str:
    """Find Chrome binary path. Checks CHROME_BINARY env var first."""
    env_path = os.environ.get('CHROME_BINARY')
    if env_path and os.path.exists(env_path):
        return env_path

    paths = _CHROME_PATHS_MACOS if sys.platform == 'darwin' else _CHROME_PATHS_LINUX
    for path in paths:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(
        "Chrome binary not found. Install Google Chrome or set CHROME_BINARY env var."
    )


def _is_port_in_use(port: int) -> bool:
    """Check if a TCP port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0


def _is_chrome_on_port(port: int) -> bool:
    """Check if Chrome debug endpoint is responding on given port."""
    try:
        url = f"http://127.0.0.1:{port}/json/version"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return 'Browser' in data and 'Chrome' in data.get('Browser', '')
    except Exception:
        pass
    return False


def _is_process_alive(pid: int) -> bool:
    """Check if a process with given PID exists."""
    try:
        os.kill(pid, 0)  # signal 0 = existence check only
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists but no permission


class HeadlessChromeManager:
    """
    Manages a headless Chrome instance for CDP fetching.

    Singleton — one headless Chrome per process.

    Usage:
        manager = HeadlessChromeManager()
        port = manager.ensure(mode='auto')  # returns port number
        # ... use CDPFetcher with this port ...
        # cleanup happens automatically via atexit
    """

    _instance: Optional['HeadlessChromeManager'] = None
    _process: Optional[subprocess.Popen] = None
    _managed_port: Optional[int] = None
    _cleanup_registered: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def ensure(self, mode: str = 'auto') -> int:
        """
        Ensure a Chrome debug session is available.

        Args:
            mode: 'auto' (detect existing, launch if needed),
                  'always' (force headless, ignore existing front-end Chrome),
                  'never' (don't auto-launch, fail if no Chrome)

        Returns:
            int: Port number of the available Chrome debug session.

        Raises:
            RuntimeError: If Chrome cannot be started or detected.
        """
        if mode == 'never':
            if _is_chrome_on_port(DEFAULT_PORT):
                logger.info(f"Using existing Chrome debug session on port {DEFAULT_PORT}")
                return DEFAULT_PORT
            raise RuntimeError(
                "No Chrome debug session found on port 9222. "
                "Start one with: ./config/chrome-debug.sh"
            )

        if mode == 'auto':
            if _is_chrome_on_port(DEFAULT_PORT):
                logger.info(f"Using existing Chrome debug session on port {DEFAULT_PORT}")
                return DEFAULT_PORT

        # Check for reusable headless instance via PID file
        reuse_port = self._try_reuse_existing()
        if reuse_port is not None:
            logger.info(f"Reusing existing headless Chrome on port {reuse_port}")
            return reuse_port

        return self._launch_headless(mode)

    def _try_reuse_existing(self) -> Optional[int]:
        """Try to reuse a previously launched headless Chrome via PID file."""
        if not os.path.exists(PID_FILE):
            return None

        try:
            with open(PID_FILE, 'r') as f:
                data = json.loads(f.read().strip())
                pid = data.get('pid')
                port = data.get('port', DEFAULT_PORT)
        except (json.JSONDecodeError, ValueError, KeyError):
            logger.debug("Invalid PID file, removing")
            self._remove_pid_file()
            return None

        if pid and _is_process_alive(pid) and _is_chrome_on_port(port):
            self._managed_port = port
            return port

        logger.debug(f"Stale PID file (pid={pid}, port={port}), cleaning up")
        if pid and _is_process_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        self._remove_pid_file()
        return None

    def _launch_headless(self, mode: str) -> int:
        """Launch a new headless Chrome instance."""
        chrome_binary = _find_chrome_binary()

        if mode == 'always' and _is_port_in_use(DEFAULT_PORT):
            port = FALLBACK_PORT
        elif _is_port_in_use(DEFAULT_PORT):
            if _is_chrome_on_port(DEFAULT_PORT):
                return DEFAULT_PORT
            port = FALLBACK_PORT
        else:
            port = DEFAULT_PORT

        os.makedirs(DATA_DIR, mode=0o700, exist_ok=True)

        logger.info(f"Starting headless Chrome on port {port}...")
        print(f"🚀 Starting headless Chrome (port {port})...", file=sys.stderr)

        args = [
            chrome_binary,
            "--headless=new",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={DATA_DIR}",
            "--remote-allow-origins=*",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-dev-shm-usage",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
        ]

        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except FileNotFoundError:
            raise RuntimeError(
                f"Chrome binary not found at: {chrome_binary}\n"
                "Install Google Chrome or set CHROME_BINARY env var."
            )
        except PermissionError:
            raise RuntimeError(
                f"Permission denied running: {chrome_binary}\n"
                "Check file permissions."
            )

        if not self._wait_for_ready(port):
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            raise RuntimeError(
                f"Headless Chrome failed to start within {READY_TIMEOUT}s on port {port}. "
                "Check Chrome installation."
            )

        HeadlessChromeManager._process = proc
        HeadlessChromeManager._managed_port = port

        self._write_pid_file(proc.pid, port)
        self._register_cleanup()

        logger.info(f"Headless Chrome started (PID: {proc.pid}, port: {port})")
        return port

    def _wait_for_ready(self, port: int) -> bool:
        """Poll /json/version until Chrome is ready or timeout."""
        deadline = time.time() + READY_TIMEOUT
        while time.time() < deadline:
            if _is_chrome_on_port(port):
                return True
            time.sleep(READY_POLL_INTERVAL)
        return False

    def _write_pid_file(self, pid: int, port: int):
        """Write PID file atomically (tmp + os.replace)."""
        os.makedirs(DATA_DIR, mode=0o700, exist_ok=True)
        tmp_path = PID_FILE + ".tmp"
        data = json.dumps({"pid": pid, "port": port, "started": time.time()})
        with open(tmp_path, 'w') as f:
            f.write(data)
        os.replace(tmp_path, PID_FILE)

    @staticmethod
    def _remove_pid_file():
        try:
            os.unlink(PID_FILE)
        except FileNotFoundError:
            pass

    def _register_cleanup(self):
        """Register atexit and signal handlers for cleanup. Chain-safe."""
        if HeadlessChromeManager._cleanup_registered:
            return

        atexit.register(HeadlessChromeManager._do_cleanup)

        for sig in (signal.SIGTERM, signal.SIGINT):
            old_handler = signal.getsignal(sig)
            def make_handler(old_h, s):
                def handler(signum, frame):
                    HeadlessChromeManager._do_cleanup()
                    signal.signal(signum, old_h if callable(old_h) else signal.SIG_DFL)
                    if callable(old_h) and old_h not in (signal.SIG_DFL, signal.SIG_IGN):
                        old_h(signum, frame)
                    else:
                        os.kill(os.getpid(), signum)
                return handler
            signal.signal(sig, make_handler(old_handler, sig))

        HeadlessChromeManager._cleanup_registered = True

    @staticmethod
    def _do_cleanup():
        """Terminate the managed headless Chrome process."""
        proc = HeadlessChromeManager._process
        if proc is None:
            return

        if proc.poll() is not None:
            HeadlessChromeManager._process = None
            HeadlessChromeManager._remove_pid_file()
            return

        logger.debug(f"Cleaning up headless Chrome (PID: {proc.pid})")
        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
        except Exception as e:
            logger.debug(f"Cleanup error (non-fatal): {e}")
        finally:
            HeadlessChromeManager._process = None
            HeadlessChromeManager._remove_pid_file()


def ensure_headless_chrome(mode: str = 'auto') -> int:
    """
    Ensure a Chrome debug session is available.

    Convenience wrapper around HeadlessChromeManager.ensure().

    Args:
        mode: 'auto', 'always', or 'never'

    Returns:
        int: Port number of the Chrome debug session.
    """
    return HeadlessChromeManager().ensure(mode=mode)
