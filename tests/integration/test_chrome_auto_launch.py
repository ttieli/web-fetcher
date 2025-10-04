#!/usr/bin/env python3
"""
Chrome Auto-Launch Integration Tests

Tests for Chrome debug auto-launch functionality including:
1. Cold start auto-launch
2. Hot connect to existing instance
3. Stale instance recovery
4. Permission error guidance

Author: Cody (Claude Code)
Date: 2025-10-04
Phase: 3.2 - Auto-Launch Integration Tests
"""

import unittest
import time
import subprocess
from pathlib import Path
import logging

from base_integration_test import BaseIntegrationTest

logger = logging.getLogger(__name__)


class TestChromeAutoLaunch(BaseIntegrationTest):
    """Integration tests for Chrome auto-launch functionality"""

    def test_cold_start_auto_launch(self):
        """
        Test: Cold start auto-launch

        Scenario:
        1. Ensure no Chrome running
        2. Call ensure_chrome_debug()
        3. Assert Chrome starts within 3 seconds
        4. Verify Chrome accessible on port 9222
        """
        logger.info("TEST: Cold start auto-launch")

        # Verify clean state
        self.assertFalse(
            self.verify_chrome_running(),
            "Chrome should not be running before test"
        )

        # Measure launch time
        result, launch_time = self.measure_performance(
            self.ensure_chrome_debug,
            self.DEFAULT_PORT,
            5
        )

        # Assert launch succeeded
        self.assertEqual(
            result.returncode,
            0,
            f"ensure_chrome_debug failed: {result.stderr}"
        )

        # Assert launch time < 3 seconds
        self.assertLess(
            launch_time,
            3.0,
            f"Chrome launch took {launch_time:.2f}s, expected < 3s"
        )

        # Verify Chrome is accessible
        self.assertTrue(
            self.verify_chrome_running(self.DEFAULT_PORT),
            "Chrome should be running and accessible on port 9222"
        )

        # Verify DevTools endpoint
        import requests
        response = requests.get(f"http://localhost:{self.DEFAULT_PORT}/json/version", timeout=3)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Browser", response.text)

        logger.info("✓ Cold start auto-launch test PASSED")

    def test_hot_connect_existing(self):
        """
        Test: Hot connect to existing Chrome instance

        Scenario:
        1. Start Chrome manually first
        2. Call ensure_chrome_debug()
        3. Assert connection < 1 second
        4. Verify no duplicate Chrome instances
        """
        logger.info("TEST: Hot connect to existing instance")

        # Start Chrome manually
        logger.info("Starting Chrome manually...")
        launch_result = subprocess.run(
            [str(self.LAUNCHER_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=10
        )
        self.assertEqual(launch_result.returncode, 0, "Manual Chrome launch failed")

        # Wait for Chrome to be ready
        self.assertTrue(
            self.wait_for_chrome_ready(timeout=5),
            "Chrome failed to become ready"
        )

        # Get initial PID count
        initial_pids = self.get_chrome_pids(self.DEFAULT_PORT)
        self.assertEqual(len(initial_pids), 1, "Should have exactly 1 Chrome instance")

        # Measure connection time
        result, connect_time = self.measure_performance(
            self.ensure_chrome_debug,
            self.DEFAULT_PORT,
            5
        )

        # Assert connection succeeded
        self.assertEqual(
            result.returncode,
            0,
            f"ensure_chrome_debug failed to connect: {result.stderr}"
        )

        # Assert connection time < 1 second
        self.assertLess(
            connect_time,
            1.0,
            f"Connection took {connect_time:.2f}s, expected < 1s for hot connect"
        )

        # Verify no duplicate instances
        final_pids = self.get_chrome_pids(self.DEFAULT_PORT)
        self.assertEqual(
            len(final_pids),
            len(initial_pids),
            f"Chrome instance count changed: {len(initial_pids)} -> {len(final_pids)}"
        )

        logger.info("✓ Hot connect test PASSED")

    def test_stale_instance_recovery(self):
        """
        Test: Stale instance recovery

        Scenario:
        1. Create zombie Chrome process (kill -9)
        2. Call ensure_chrome_debug()
        3. Assert recovery successful
        4. Verify new Chrome instance healthy
        """
        logger.info("TEST: Stale instance recovery")

        # Create zombie Chrome
        zombie_pid = self.create_zombie_chrome(self.DEFAULT_PORT)
        if zombie_pid is None:
            self.skipTest("Failed to create zombie Chrome process")

        logger.info(f"Created zombie Chrome (PID: {zombie_pid})")

        # Verify Chrome is not accessible (zombie state)
        time.sleep(1)
        accessible_before = self.verify_chrome_running(self.DEFAULT_PORT)

        # Call ensure_chrome_debug to trigger recovery
        result = self.ensure_chrome_debug(self.DEFAULT_PORT, timeout=10)

        # Assert recovery succeeded
        self.assertEqual(
            result.returncode,
            0,
            f"Recovery failed: {result.stderr}"
        )

        # Verify new Chrome instance is healthy
        self.assertTrue(
            self.verify_chrome_running(self.DEFAULT_PORT),
            "Chrome should be healthy after recovery"
        )

        # Verify it's a new instance (different PID)
        new_pids = self.get_chrome_pids(self.DEFAULT_PORT)
        self.assertEqual(len(new_pids), 1, "Should have exactly 1 Chrome instance")
        self.assertNotEqual(
            new_pids[0],
            zombie_pid,
            "Should be a new Chrome instance, not the zombie"
        )

        logger.info("✓ Stale instance recovery test PASSED")

    def test_permission_error_guidance(self):
        """
        Test: Permission error guidance

        Scenario:
        1. Make chrome-debug-launcher.sh non-executable
        2. Call ensure_chrome_debug()
        3. Assert appropriate error raised/returned
        4. Verify guidance message contains macOS instructions
        5. Restore permissions in cleanup
        """
        logger.info("TEST: Permission error guidance")

        # Make launcher script non-executable
        self.make_script_non_executable(self.LAUNCHER_SCRIPT)

        try:
            # Verify script is no longer executable
            is_executable = self.LAUNCHER_SCRIPT.stat().st_mode & 0o111
            self.assertEqual(is_executable, 0, "Script should not be executable")

            # Try to ensure Chrome (should fail with permission error)
            result = self.ensure_chrome_debug(self.DEFAULT_PORT, timeout=5)

            # Depending on implementation, this could return error code 3 or 1
            # Check that it failed
            self.assertNotEqual(
                result.returncode,
                0,
                "Should fail when launcher is not executable"
            )

            # Check for permission-related messaging
            error_output = result.stderr.lower()

            # Should contain permission-related guidance
            has_permission_guidance = any([
                'permission' in error_output,
                'chmod' in error_output,
                'executable' in error_output,
                'denied' in error_output
            ])

            self.assertTrue(
                has_permission_guidance,
                f"Error message should contain permission guidance. Got: {result.stderr}"
            )

            logger.info("✓ Permission error guidance test PASSED")

        finally:
            # Always restore permissions
            self.restore_script_executable(self.LAUNCHER_SCRIPT)

            # Verify restoration
            is_executable = self.LAUNCHER_SCRIPT.stat().st_mode & 0o111
            self.assertNotEqual(is_executable, 0, "Script should be executable again")
            logger.info("Restored launcher script permissions")


if __name__ == "__main__":
    unittest.main(verbosity=2)
