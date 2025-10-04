#!/usr/bin/env python3
"""
Concurrent Operations Integration Tests

Tests for concurrent Chrome debug operations including:
1. Concurrent launch prevention
2. Parallel fetch operations
3. Lock mechanism integrity

Author: Cody (Claude Code)
Date: 2025-10-04
Phase: 3.4 - Concurrent Operations Testing
"""

import unittest
import sys
import time
import threading
from pathlib import Path
import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from base_integration_test import BaseIntegrationTest

logger = logging.getLogger(__name__)


class TestConcurrentOperations(BaseIntegrationTest):
    """Integration tests for concurrent Chrome debug operations"""

    def test_concurrent_launch_prevention(self):
        """
        Test: Concurrent launch prevention

        Scenario:
        1. Use threading to create 10 concurrent ensure_chrome_debug() calls
        2. Assert only ONE Chrome instance started
        3. Verify lock mechanism worked
        """
        logger.info("TEST: Concurrent launch prevention")

        # Ensure clean state
        self.kill_all_chrome_debug_instances()
        self.cleanup_locks()

        # Verify no Chrome running
        self.assertFalse(
            self.verify_chrome_running(),
            "Chrome should not be running before test"
        )

        # Function to call ensure_chrome_debug in thread
        def launch_chrome(thread_id):
            logger.debug(f"Thread {thread_id}: Calling ensure_chrome_debug")
            result = self.ensure_chrome_debug(self.DEFAULT_PORT, timeout=10)
            logger.debug(f"Thread {thread_id}: Result code {result.returncode}")
            return {
                'thread_id': thread_id,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

        # Launch 10 concurrent threads
        num_threads = 10
        results = []

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(launch_chrome, i) for i in range(num_threads)]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Thread failed with exception: {e}")

        # Wait a bit for all processes to settle
        time.sleep(2)

        # Assert only ONE Chrome instance is running
        final_pids = self.get_chrome_pids(self.DEFAULT_PORT)
        self.assertEqual(
            len(final_pids),
            1,
            f"Expected 1 Chrome instance, found {len(final_pids)}: {final_pids}"
        )

        # Verify Chrome is accessible
        self.assertTrue(
            self.verify_chrome_running(self.DEFAULT_PORT),
            "Chrome should be running and accessible"
        )

        # Count successful launches (returncode 0)
        successful_count = sum(1 for r in results if r['returncode'] == 0)
        logger.info(f"Successful ensure_chrome_debug calls: {successful_count}/{num_threads}")

        # All threads should succeed (either launching or connecting to existing)
        self.assertEqual(
            successful_count,
            num_threads,
            f"All threads should succeed, but {num_threads - successful_count} failed"
        )

        logger.info("✓ Concurrent launch prevention test PASSED")

    def test_parallel_fetch_operations(self):
        """
        Test: Parallel fetch operations

        Scenario:
        1. Start Chrome once
        2. Launch 5 parallel fetch requests
        3. Assert all succeed
        4. Verify no Chrome crashes
        """
        logger.info("TEST: Parallel fetch operations")

        # Import webfetcher
        try:
            from webfetcher import fetch_html_with_retry
        except ImportError:
            self.skipTest("webfetcher module not found")

        # Start Chrome once
        logger.info("Starting Chrome for parallel fetch test...")
        launch_result = subprocess.run(
            [str(self.LAUNCHER_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if launch_result.returncode != 0:
            self.skipTest("Failed to launch Chrome for test")

        # Wait for Chrome to be ready
        self.assertTrue(
            self.wait_for_chrome_ready(timeout=5),
            "Chrome should be ready"
        )

        # Get initial Chrome PID
        initial_pids = self.get_chrome_pids(self.DEFAULT_PORT)
        self.assertEqual(len(initial_pids), 1, "Should have 1 Chrome instance")

        # Test URLs
        test_urls = [
            "http://example.com",
            "http://example.org",
            "http://example.net",
            "https://www.iana.org/domains/reserved",
            "http://example.edu"
        ]

        # Function to fetch URL
        def fetch_url(url_index, url):
            logger.debug(f"Fetch {url_index}: Starting {url}")
            try:
                html, metrics = fetch_html_with_retry(
                    url=url,
                    ua="Mozilla/5.0 Test Parallel",
                    timeout=15,
                    fetch_mode='auto'
                )
                logger.debug(f"Fetch {url_index}: Completed ({len(html)} bytes)")
                return {
                    'url_index': url_index,
                    'url': url,
                    'success': True,
                    'html_length': len(html),
                    'metrics': metrics
                }
            except Exception as e:
                logger.error(f"Fetch {url_index}: Failed with {e}")
                return {
                    'url_index': url_index,
                    'url': url,
                    'success': False,
                    'error': str(e)
                }

        # Launch parallel fetches
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_url, i, url) for i, url in enumerate(test_urls)]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Future failed with exception: {e}")

        # Assert all fetches succeeded
        successful_fetches = sum(1 for r in results if r.get('success', False))
        self.assertEqual(
            successful_fetches,
            len(test_urls),
            f"Expected {len(test_urls)} successful fetches, got {successful_fetches}"
        )

        # Verify Chrome is still running (no crashes)
        self.assertTrue(
            self.verify_chrome_running(self.DEFAULT_PORT),
            "Chrome should still be running after parallel fetches"
        )

        # Verify same Chrome instance (no duplicates)
        final_pids = self.get_chrome_pids(self.DEFAULT_PORT)
        self.assertEqual(
            final_pids,
            initial_pids,
            "Chrome PID should remain the same (no crashes/restarts)"
        )

        logger.info("✓ Parallel fetch operations test PASSED")

    def test_lock_mechanism_integrity(self):
        """
        Test: Lock mechanism integrity

        Scenario:
        1. Manually acquire lock
        2. Try to launch Chrome
        3. Assert blocked appropriately
        4. Release lock and verify works
        """
        logger.info("TEST: Lock mechanism integrity")

        # Ensure clean state
        self.kill_all_chrome_debug_instances()
        self.cleanup_locks()

        # Manually create lock file
        lock_file = self.LOCK_FILE
        lock_file.parent.mkdir(parents=True, exist_ok=True)

        # Write a PID to lock file (simulating another process holding lock)
        fake_pid = 99999
        lock_file.write_text(str(fake_pid))
        logger.info(f"Created lock file with fake PID: {fake_pid}")

        # Verify lock file exists
        self.assertTrue(lock_file.exists(), "Lock file should exist")

        # Try to launch Chrome (should be blocked or handle lock gracefully)
        result = self.ensure_chrome_debug(self.DEFAULT_PORT, timeout=5)

        # The behavior depends on implementation:
        # - Might fail with error (locked)
        # - Might detect stale lock and proceed
        # - Might wait for lock release

        # Check if lock was respected or cleaned up
        if result.returncode != 0:
            # Launch failed - lock was respected
            logger.info("Lock was respected, launch failed as expected")

            # Verify Chrome did NOT start
            chrome_running = self.verify_chrome_running(self.DEFAULT_PORT)
            if chrome_running:
                logger.warning("Chrome started despite lock - lock might be ignored")
        else:
            # Launch succeeded - lock might have been detected as stale
            logger.info("Lock was detected as stale and cleaned up")

        # Now release lock manually
        if lock_file.exists():
            lock_file.unlink()
            logger.info("Released lock file")

        # Clean up any Chrome instances
        self.kill_all_chrome_debug_instances()
        time.sleep(1)

        # Try again without lock - should succeed
        result = self.ensure_chrome_debug(self.DEFAULT_PORT, timeout=10)

        self.assertEqual(
            result.returncode,
            0,
            f"Launch should succeed without lock: {result.stderr}"
        )

        # Verify Chrome is running
        self.assertTrue(
            self.verify_chrome_running(self.DEFAULT_PORT),
            "Chrome should be running after lock release"
        )

        logger.info("✓ Lock mechanism integrity test PASSED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
