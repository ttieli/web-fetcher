#!/usr/bin/env python3
"""
Base Integration Test Class for Chrome Debug Auto-Launch Testing

This module provides a base test class with utilities for:
- Chrome process management (cleanup, verification)
- Lock file management
- Performance measurement
- Common test setup/teardown

Author: Cody (Claude Code)
Date: 2025-10-04
Phase: 3.1 - Integration Test Framework
"""

import unittest
import subprocess
import time
import os
import signal
import psutil
import requests
from pathlib import Path
from typing import Optional, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BaseIntegrationTest(unittest.TestCase):
    """
    Base class for Chrome debug integration tests.

    Provides:
    - setUp(): Clean environment before each test
    - tearDown(): Cleanup after each test
    - Helper methods for Chrome management and verification
    """

    # Configuration
    DEFAULT_PORT = 9222
    PROFILE_DIR = Path.home() / ".chrome-wf"
    PID_FILE = PROFILE_DIR / ".chrome-debug.pid"
    LOCK_FILE = PROFILE_DIR / ".chrome-debug.lock"
    ENSURE_SCRIPT = Path(__file__).parent.parent.parent / "config" / "ensure-chrome-debug.sh"
    LAUNCHER_SCRIPT = Path(__file__).parent.parent.parent / "config" / "chrome-debug-launcher.sh"

    def setUp(self):
        """
        Setup method called before each test.

        Actions:
        1. Kill all Chrome debug instances
        2. Clear lock files
        3. Reset test environment
        """
        logger.info(f"Setting up test: {self._testMethodName}")

        # Kill all Chrome debug instances
        self.kill_all_chrome_debug_instances()

        # Clear locks
        self.cleanup_locks()

        # Small delay to ensure clean state
        time.sleep(0.5)

        logger.info("Test setup complete")

    def tearDown(self):
        """
        Teardown method called after each test.

        Actions:
        1. Kill Chrome processes
        2. Remove test artifacts
        3. Clean up locks
        """
        logger.info(f"Tearing down test: {self._testMethodName}")

        # Kill Chrome processes
        self.kill_all_chrome_debug_instances()

        # Clean up locks
        self.cleanup_locks()

        logger.info("Test teardown complete")

    def kill_all_chrome_debug_instances(self) -> None:
        """
        Kill all Chrome debug instances (port 9222).

        Uses multiple methods to ensure all instances are terminated:
        1. Find by port using lsof
        2. Find by process name and debug flag
        3. Force kill using SIGKILL
        """
        killed_count = 0

        # Method 1: Find by port using lsof
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{self.DEFAULT_PORT}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        pid_int = int(pid.strip())
                        os.kill(pid_int, signal.SIGKILL)
                        killed_count += 1
                        logger.debug(f"Killed Chrome process on port (PID: {pid_int})")
                    except (ValueError, ProcessLookupError):
                        pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Method 2: Find by process pattern
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'Chrome' in proc.info['name'] and 'remote-debugging-port=9222' in cmdline:
                        proc.kill()
                        proc.wait(timeout=3)
                        killed_count += 1
                        logger.debug(f"Killed Chrome debug process (PID: {proc.info['pid']})")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    pass
        except Exception as e:
            logger.warning(f"Error during process cleanup: {e}")

        # Wait for processes to terminate
        time.sleep(1)

        if killed_count > 0:
            logger.info(f"Killed {killed_count} Chrome debug instance(s)")

    def verify_chrome_running(self, port: int = None) -> bool:
        """
        Verify Chrome is running and accessible on debug port.

        Args:
            port: Debug port to check (default: DEFAULT_PORT)

        Returns:
            True if Chrome is running and accessible, False otherwise
        """
        if port is None:
            port = self.DEFAULT_PORT

        # Check 1: Port is listening
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if not result.stdout.strip():
                logger.debug(f"Port {port} is not listening")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.debug("lsof check failed")
            return False

        # Check 2: DevTools endpoint is accessible
        try:
            response = requests.get(
                f"http://localhost:{port}/json/version",
                timeout=3
            )
            if response.status_code == 200 and 'Browser' in response.text:
                logger.debug(f"Chrome verified running on port {port}")
                return True
        except requests.RequestException as e:
            logger.debug(f"DevTools endpoint check failed: {e}")

        return False

    def measure_performance(self, func, *args, **kwargs) -> tuple:
        """
        Measure execution time of a function.

        Args:
            func: Function to measure
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Tuple of (result, execution_time_seconds)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time

        logger.debug(f"Function {func.__name__} executed in {execution_time:.3f}s")
        return result, execution_time

    def cleanup_locks(self) -> None:
        """
        Clean up lock files and Chrome profile locks.

        Removes:
        - .chrome-debug.lock
        - .chrome-debug.pid
        - Chrome SingletonLock and SingletonCookie
        """
        files_to_remove = [
            self.LOCK_FILE,
            self.PID_FILE,
            self.PROFILE_DIR / "SingletonLock",
            self.PROFILE_DIR / "SingletonCookie",
        ]

        removed_count = 0
        for file_path in files_to_remove:
            if file_path.exists():
                try:
                    file_path.unlink()
                    removed_count += 1
                    logger.debug(f"Removed lock file: {file_path}")
                except OSError as e:
                    logger.warning(f"Failed to remove {file_path}: {e}")

        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} lock file(s)")

    def ensure_chrome_debug(self, port: int = None, timeout: int = 5) -> subprocess.CompletedProcess:
        """
        Call ensure-chrome-debug.sh script.

        Args:
            port: Debug port (default: DEFAULT_PORT)
            timeout: Timeout in seconds

        Returns:
            CompletedProcess object with returncode, stdout, stderr
        """
        if port is None:
            port = self.DEFAULT_PORT

        cmd = [
            str(self.ENSURE_SCRIPT),
            "--port", str(port),
            "--timeout", str(timeout)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        return result

    def get_chrome_pids(self, port: int = None) -> List[int]:
        """
        Get PIDs of Chrome processes on debug port.

        Args:
            port: Debug port to check (default: DEFAULT_PORT)

        Returns:
            List of PIDs
        """
        if port is None:
            port = self.DEFAULT_PORT

        pids = []

        # Try lsof first
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip():
                pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n')]
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass

        return pids

    def wait_for_chrome_ready(self, timeout: int = 10, port: int = None) -> bool:
        """
        Wait for Chrome to be ready and accessible.

        Args:
            timeout: Maximum wait time in seconds
            port: Debug port to check (default: DEFAULT_PORT)

        Returns:
            True if Chrome becomes ready, False if timeout
        """
        if port is None:
            port = self.DEFAULT_PORT

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.verify_chrome_running(port):
                return True
            time.sleep(0.5)

        return False

    def create_zombie_chrome(self, port: int = None) -> Optional[int]:
        """
        Create a zombie Chrome process for testing recovery.

        Args:
            port: Debug port (default: DEFAULT_PORT)

        Returns:
            PID of zombie process, or None if failed
        """
        if port is None:
            port = self.DEFAULT_PORT

        # First start Chrome normally
        try:
            result = subprocess.run(
                [str(self.LAUNCHER_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.error("Failed to start Chrome for zombie creation")
                return None

            # Wait for Chrome to start
            time.sleep(2)

            # Get PID
            pids = self.get_chrome_pids(port)
            if not pids:
                logger.error("No Chrome PID found after launch")
                return None

            pid = pids[0]

            # Kill with SIGKILL to create zombie-like state
            os.kill(pid, signal.SIGKILL)

            logger.info(f"Created zombie Chrome process (PID: {pid})")
            return pid

        except Exception as e:
            logger.error(f"Failed to create zombie Chrome: {e}")
            return None

    def make_script_non_executable(self, script_path: Path) -> None:
        """
        Remove execute permissions from a script.

        Args:
            script_path: Path to script
        """
        try:
            current_mode = script_path.stat().st_mode
            script_path.chmod(current_mode & ~0o111)
            logger.debug(f"Removed execute permission from {script_path}")
        except OSError as e:
            logger.error(f"Failed to modify permissions: {e}")

    def restore_script_executable(self, script_path: Path) -> None:
        """
        Restore execute permissions to a script.

        Args:
            script_path: Path to script
        """
        try:
            current_mode = script_path.stat().st_mode
            script_path.chmod(current_mode | 0o755)
            logger.debug(f"Restored execute permission to {script_path}")
        except OSError as e:
            logger.error(f"Failed to restore permissions: {e}")


if __name__ == "__main__":
    # Run a simple test to verify the base class
    class SimpleTest(BaseIntegrationTest):
        def test_chrome_not_running(self):
            """Test that Chrome is not running after setup"""
            self.assertFalse(self.verify_chrome_running())

        def test_locks_cleaned(self):
            """Test that locks are cleaned"""
            self.assertFalse(self.LOCK_FILE.exists())
            self.assertFalse(self.PID_FILE.exists())

    unittest.main()
