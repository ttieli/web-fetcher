#!/usr/bin/env python3
"""
Fallback Mechanism Integration Tests

Tests for webfetcher fallback behavior including:
1. Selenium to urllib fallback
2. Force urllib mode
3. Retry with recovery

Author: Cody (Claude Code)
Date: 2025-10-04
Phase: 3.3 - Fallback Mechanism Tests
"""

import unittest
import sys
import time
from pathlib import Path
import logging
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from base_integration_test import BaseIntegrationTest

logger = logging.getLogger(__name__)


class TestFallbackMechanisms(BaseIntegrationTest):
    """Integration tests for webfetcher fallback mechanisms"""

    def test_selenium_to_urllib_fallback(self):
        """
        Test: Selenium to urllib fallback

        Scenario:
        1. Kill Chrome
        2. Make ensure-chrome-debug.sh return error
        3. Call webfetcher in auto mode
        4. Assert falls back to urllib
        5. Verify fetch still succeeds
        """
        logger.info("TEST: Selenium to urllib fallback")

        # Import webfetcher
        try:
            from webfetcher import fetch_html_with_retry
        except ImportError:
            self.skipTest("webfetcher module not found")

        # Kill Chrome to ensure it's not available
        self.kill_all_chrome_debug_instances()

        # Make ensure-chrome-debug.sh non-executable to simulate failure
        ensure_script_backup = self.ENSURE_SCRIPT.with_suffix('.sh.backup')

        try:
            # Backup original script
            if self.ENSURE_SCRIPT.exists():
                import shutil
                shutil.copy(self.ENSURE_SCRIPT, ensure_script_backup)
                self.make_script_non_executable(self.ENSURE_SCRIPT)

            # Call webfetcher in auto mode with a simple URL
            test_url = "http://example.com"

            html, metrics = fetch_html_with_retry(
                url=test_url,
                ua="Mozilla/5.0 Test",
                timeout=10,
                fetch_mode='auto'  # Should try selenium, fail, fallback to urllib
            )

            # Assert fetch succeeded
            self.assertIsNotNone(html, "Fetch should succeed via fallback")
            self.assertGreater(len(html), 0, "HTML should not be empty")

            # Verify metrics show fallback was used
            self.assertEqual(
                metrics.primary_method,
                "urllib",
                "Primary method should be urllib when selenium unavailable"
            )

            # Verify final status is success
            self.assertEqual(
                metrics.final_status,
                "success",
                "Final status should be success via urllib fallback"
            )

            logger.info("✓ Selenium to urllib fallback test PASSED")

        finally:
            # Restore ensure script
            if ensure_script_backup.exists():
                import shutil
                shutil.copy(ensure_script_backup, self.ENSURE_SCRIPT)
                ensure_script_backup.unlink()
                self.restore_script_executable(self.ENSURE_SCRIPT)

    def test_force_urllib_mode(self):
        """
        Test: Force urllib mode

        Scenario:
        1. Set fetch_mode='urllib'
        2. Verify Chrome NOT launched
        3. Verify urllib used directly
        """
        logger.info("TEST: Force urllib mode")

        # Import webfetcher
        try:
            from webfetcher import fetch_html_with_retry
        except ImportError:
            self.skipTest("webfetcher module not found")

        # Ensure no Chrome running
        self.kill_all_chrome_debug_instances()

        # Verify Chrome not running
        self.assertFalse(
            self.verify_chrome_running(),
            "Chrome should not be running before test"
        )

        # Call webfetcher in urllib-only mode
        test_url = "http://example.com"

        html, metrics = fetch_html_with_retry(
            url=test_url,
            ua="Mozilla/5.0 Test",
            timeout=10,
            fetch_mode='urllib'  # Force urllib only
        )

        # Verify Chrome was NOT launched
        self.assertFalse(
            self.verify_chrome_running(),
            "Chrome should NOT be launched in urllib-only mode"
        )

        # Verify fetch succeeded with urllib
        self.assertIsNotNone(html, "Fetch should succeed with urllib")
        self.assertGreater(len(html), 0, "HTML should not be empty")

        # Verify metrics show urllib was used
        self.assertEqual(
            metrics.primary_method,
            "urllib",
            "Primary method should be urllib in force mode"
        )

        # Verify no fallback was used
        self.assertIsNone(
            metrics.fallback_method,
            "No fallback should be used in urllib-only mode"
        )

        logger.info("✓ Force urllib mode test PASSED")

    def test_retry_with_recovery(self):
        """
        Test: Retry with recovery

        Scenario:
        1. Simulate Chrome crash mid-fetch
        2. Verify recovery triggered
        3. Assert retry succeeds
        """
        logger.info("TEST: Retry with recovery")

        # Import webfetcher and selenium_fetcher
        try:
            from webfetcher import fetch_html_with_retry
            from selenium_fetcher import SeleniumFetcher
        except ImportError:
            self.skipTest("webfetcher or selenium_fetcher module not found")

        # Start Chrome first
        logger.info("Starting Chrome for test...")
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

        try:
            # Test URL that should work
            test_url = "http://example.com"

            # First successful fetch to establish Chrome is working
            html1, metrics1 = fetch_html_with_retry(
                url=test_url,
                ua="Mozilla/5.0 Test",
                timeout=10,
                fetch_mode='auto'
            )

            self.assertIsNotNone(html1, "First fetch should succeed")

            # Now simulate Chrome crash by killing it
            logger.info("Simulating Chrome crash...")
            self.kill_all_chrome_debug_instances()
            time.sleep(1)

            # Verify Chrome is down
            self.assertFalse(
                self.verify_chrome_running(),
                "Chrome should be down after kill"
            )

            # Try to fetch again - should trigger recovery
            # Note: With current implementation, this will fallback to urllib
            # because Chrome auto-restart is not automatic in fetch_html_with_retry
            html2, metrics2 = fetch_html_with_retry(
                url=test_url,
                ua="Mozilla/5.0 Test",
                timeout=10,
                fetch_mode='auto'
            )

            # Should succeed via fallback
            self.assertIsNotNone(html2, "Fetch should succeed after Chrome crash")
            self.assertGreater(len(html2), 0, "HTML should not be empty")

            # Verify recovery/fallback occurred
            # In auto mode, it should fallback to urllib when Chrome is unavailable
            self.assertEqual(
                metrics2.final_status,
                "success",
                "Should succeed via fallback mechanism"
            )

            logger.info("✓ Retry with recovery test PASSED")

        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            raise


if __name__ == "__main__":
    unittest.main(verbosity=2)
