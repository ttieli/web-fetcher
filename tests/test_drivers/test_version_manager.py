"""
Unit tests for ChromeDriver version management
ChromeDriver版本管理单元测试
"""
import unittest
from unittest.mock import patch, MagicMock
import subprocess
from drivers.version_manager import VersionDetector, CompatibilityResult
from drivers.constants import CompatibilityStatus

class TestVersionDetector(unittest.TestCase):
    """Test VersionDetector class"""

    def setUp(self):
        self.detector = VersionDetector()

    @patch('subprocess.run')
    def test_chrome_version_detection_success(self, mock_run):
        """Test successful Chrome version detection"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Google Chrome 141.0.6496.0"
        )

        version = self.detector.get_chrome_version()
        self.assertEqual(version, "141.0.6496.0")

    @patch('subprocess.run')
    def test_chrome_version_not_installed(self, mock_run):
        """Test Chrome not installed scenario"""
        mock_run.side_effect = FileNotFoundError()

        version = self.detector.get_chrome_version()
        self.assertIsNone(version)

    @patch('subprocess.run')
    def test_chromedriver_version_detection(self, mock_run):
        """Test ChromeDriver version detection"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="ChromeDriver 140.0.6476.0 (abc123)"
        )

        version = self.detector.get_chromedriver_version()
        self.assertEqual(version, "140.0.6476.0")

    def test_compatibility_check_compatible(self):
        """Test compatible versions"""
        result = self.detector.check_compatibility("141.0.6496.0", "141.0.6476.0")

        self.assertEqual(result.status, CompatibilityStatus.COMPATIBLE)
        self.assertTrue(result.is_compatible)

    def test_compatibility_check_mismatch(self):
        """Test version mismatch"""
        result = self.detector.check_compatibility("141.0.6496.0", "140.0.6476.0")

        self.assertEqual(result.status, CompatibilityStatus.MISMATCH)
        self.assertFalse(result.is_compatible)
        self.assertIn("mismatch", result.message_en.lower())

    def test_compatibility_chrome_not_found(self):
        """Test Chrome not found"""
        result = self.detector.check_compatibility(None, "140.0.6476.0")

        self.assertEqual(result.status, CompatibilityStatus.CHROME_NOT_FOUND)

    def test_compatibility_driver_not_found(self):
        """Test ChromeDriver not found"""
        result = self.detector.check_compatibility("141.0.6496.0", None)

        self.assertEqual(result.status, CompatibilityStatus.DRIVER_NOT_FOUND)

if __name__ == '__main__':
    unittest.main()
