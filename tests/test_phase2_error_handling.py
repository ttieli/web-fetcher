#!/usr/bin/env python3
"""
Unit tests for Phase 2: Chrome Error Handling Enhancement

Tests the Chrome exception class hierarchy, error message templates,
and error categorization patterns.

Author: Cody (Claude Code)
Date: 2025-10-04
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from error_handler import (
    ErrorCategory,
    ChromeDebugError,
    ChromePortConflictError,
    ChromePermissionError,
    ChromeTimeoutError,
    ChromeLaunchError,
    ChromeErrorMessages,
    ErrorClassifier
)


class TestChromeExceptionClasses(unittest.TestCase):
    """Test Chrome exception class hierarchy"""

    def test_chrome_debug_error_base(self):
        """Test ChromeDebugError base exception"""
        error = ChromeDebugError(
            "Test error",
            error_code=1,
            guidance="Test guidance"
        )
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.error_code, 1)
        self.assertEqual(error.guidance, "Test guidance")

    def test_chrome_port_conflict_error(self):
        """Test ChromePortConflictError exception"""
        error = ChromePortConflictError(
            "Port 9222 conflict",
            error_code=1,
            guidance="Port guidance"
        )
        self.assertIsInstance(error, ChromeDebugError)
        self.assertEqual(error.message, "Port 9222 conflict")

    def test_chrome_permission_error(self):
        """Test ChromePermissionError exception"""
        error = ChromePermissionError(
            "Permission denied",
            error_code=3,
            guidance="Permission guidance"
        )
        self.assertIsInstance(error, ChromeDebugError)
        self.assertEqual(error.error_code, 3)

    def test_chrome_timeout_error(self):
        """Test ChromeTimeoutError exception"""
        error = ChromeTimeoutError(
            "Chrome timeout",
            error_code=4,
            guidance="Timeout guidance"
        )
        self.assertIsInstance(error, ChromeDebugError)
        self.assertEqual(error.message, "Chrome timeout")

    def test_chrome_launch_error(self):
        """Test ChromeLaunchError exception"""
        error = ChromeLaunchError(
            "Launch failed",
            error_code=2,
            guidance="Launch guidance"
        )
        self.assertIsInstance(error, ChromeDebugError)
        self.assertEqual(error.message, "Launch failed")


class TestChromeErrorMessages(unittest.TestCase):
    """Test ChromeErrorMessages template class"""

    def test_permission_message_template(self):
        """Test permission denied message template"""
        msg = ChromeErrorMessages.get_message('permission')
        self.assertIn("Permission Error", msg)
        self.assertIn("macOS", msg)
        self.assertIn("chmod", msg)
        self.assertIn("~/.chrome-wf/", msg)

    def test_port_conflict_message_template(self):
        """Test port conflict message template with parameters"""
        msg = ChromeErrorMessages.get_message(
            'port_conflict',
            port=9222,
            diagnostic_info="Port already in use by another process"
        )
        self.assertIn("Port Conflict", msg)
        self.assertIn("9222", msg)
        self.assertIn("Port already in use", msg)
        self.assertIn("lsof", msg)

    def test_timeout_message_template(self):
        """Test timeout error message template"""
        msg = ChromeErrorMessages.get_message('timeout', timeout=15)
        self.assertIn("Timeout Error", msg)
        self.assertIn("15", msg)
        self.assertIn("system resources", msg)

    def test_launch_failed_message_template(self):
        """Test launch failed message template"""
        msg = ChromeErrorMessages.get_message(
            'launch_failed',
            error_details="Chrome executable not found"
        )
        self.assertIn("Launch Failed", msg)
        self.assertIn("Chrome executable not found", msg)
        self.assertIn("Chrome installation", msg)

    def test_unknown_error_type_defaults_to_launch_failed(self):
        """Test that unknown error types default to launch_failed template"""
        msg = ChromeErrorMessages.get_message('unknown_error_type')
        self.assertIn("Launch Failed", msg)

    def test_missing_format_parameters_handled_gracefully(self):
        """Test that missing format parameters don't crash"""
        # Should not raise exception even with missing parameters
        msg = ChromeErrorMessages.get_message('port_conflict')
        self.assertIsInstance(msg, str)
        self.assertGreater(len(msg), 0)


class TestErrorCategoryEnum(unittest.TestCase):
    """Test ErrorCategory enum extensions"""

    def test_chrome_categories_exist(self):
        """Test that Chrome-specific categories are defined"""
        self.assertEqual(ErrorCategory.CHROME_LAUNCH.value, "chrome_launch")
        self.assertEqual(ErrorCategory.CHROME_PERMISSION.value, "chrome_permission")
        self.assertEqual(ErrorCategory.CHROME_PORT_CONFLICT.value, "chrome_port")
        self.assertEqual(ErrorCategory.CHROME_TIMEOUT.value, "chrome_timeout")

    def test_chrome_categories_are_distinct(self):
        """Test that Chrome categories are distinct from generic categories"""
        chrome_categories = {
            ErrorCategory.CHROME_LAUNCH,
            ErrorCategory.CHROME_PERMISSION,
            ErrorCategory.CHROME_PORT_CONFLICT,
            ErrorCategory.CHROME_TIMEOUT
        }

        generic_categories = {
            ErrorCategory.BROWSER_INIT,
            ErrorCategory.PERMISSION,
            ErrorCategory.TIMEOUT
        }

        # Ensure no overlap
        self.assertEqual(len(chrome_categories & generic_categories), 0)


class TestErrorClassifierChromePatterns(unittest.TestCase):
    """Test ErrorClassifier with Chrome error patterns"""

    def setUp(self):
        self.classifier = ErrorClassifier()

    def test_chrome_launch_pattern_matching(self):
        """Test Chrome launch error pattern detection"""
        test_error = Exception("Chrome launch failed")
        category = self.classifier.classify(test_error)
        self.assertEqual(category, ErrorCategory.CHROME_LAUNCH)

    def test_chrome_permission_pattern_matching(self):
        """Test Chrome permission error pattern detection"""
        test_error = Exception("Chrome permission denied")
        category = self.classifier.classify(test_error)
        self.assertEqual(category, ErrorCategory.CHROME_PERMISSION)

    def test_chrome_port_conflict_pattern_matching(self):
        """Test Chrome port conflict error pattern detection"""
        test_error = Exception("port 9222 already in use")
        category = self.classifier.classify(test_error)
        self.assertEqual(category, ErrorCategory.CHROME_PORT_CONFLICT)

    def test_chrome_timeout_pattern_matching(self):
        """Test Chrome timeout error pattern detection"""
        test_error = Exception("Chrome debug session timeout")
        category = self.classifier.classify(test_error)
        self.assertEqual(category, ErrorCategory.CHROME_TIMEOUT)

    def test_generic_chrome_error_classified_correctly(self):
        """Test that generic Chrome errors fall under BROWSER_INIT"""
        test_error = Exception("Chrome not found")
        category = self.classifier.classify(test_error)
        # Should match BROWSER_INIT pattern (has 'chrome' in it)
        self.assertEqual(category, ErrorCategory.BROWSER_INIT)

    def test_port_conflict_without_chrome_context(self):
        """Test port conflict without Chrome-specific context"""
        test_error = Exception("address already in use")
        category = self.classifier.classify(test_error)
        self.assertEqual(category, ErrorCategory.CHROME_PORT_CONFLICT)


class TestErrorCodeMapping(unittest.TestCase):
    """Test error code to exception mapping logic"""

    def test_returncode_mapping_logic(self):
        """Test that error codes map to correct exception types"""
        # This tests the conceptual mapping used in ensure_chrome_debug()
        error_code_mappings = {
            0: None,  # Success
            1: ChromePortConflictError,  # Port conflict or recovery failed
            2: ChromeLaunchError,  # Parameter error
            3: ChromePermissionError,  # Permission error
            4: ChromeTimeoutError,  # Timeout error
        }

        # Verify each exception type can be instantiated with expected parameters
        for code, exc_class in error_code_mappings.items():
            if exc_class is None:
                continue

            exception = exc_class(
                f"Test error for code {code}",
                error_code=code,
                guidance="Test guidance"
            )
            self.assertEqual(exception.error_code, code)
            self.assertIsInstance(exception, ChromeDebugError)


class TestMessageBilingualSupport(unittest.TestCase):
    """Test that error messages include both English and Chinese"""

    def test_permission_message_is_bilingual(self):
        """Test permission message has both languages"""
        msg = ChromeErrorMessages.PERMISSION_DENIED_MACOS
        self.assertIn("Permission Error", msg)
        self.assertIn("权限错误", msg)

    def test_port_conflict_message_is_bilingual(self):
        """Test port conflict message has both languages"""
        msg = ChromeErrorMessages.PORT_CONFLICT
        self.assertIn("Port Conflict", msg)
        self.assertIn("端口冲突", msg)

    def test_timeout_message_is_bilingual(self):
        """Test timeout message has both languages"""
        msg = ChromeErrorMessages.TIMEOUT_ERROR
        self.assertIn("Timeout Error", msg)
        self.assertIn("超时错误", msg)

    def test_launch_failed_message_is_bilingual(self):
        """Test launch failed message has both languages"""
        msg = ChromeErrorMessages.LAUNCH_FAILED
        self.assertIn("Launch Failed", msg)
        self.assertIn("启动失败", msg)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
