"""
Integration tests for download and cache functionality
下载和缓存功能集成测试
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import shutil
from drivers.version_manager import VersionCache, VersionDownloader, DownloadError


class TestVersionCache(unittest.TestCase):
    """Test VersionCache class"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = VersionCache(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_cache_path_creation(self):
        """Test cache directory creation"""
        self.assertTrue(self.temp_dir.exists())

    def test_get_cache_path(self):
        """Test getting cache path for version"""
        path = self.cache.get_cache_path("141.0.0.0")
        self.assertEqual(path, self.temp_dir / "141.0.0.0")

    def test_is_cached_false(self):
        """Test is_cached returns False for non-existent version"""
        self.assertFalse(self.cache.is_cached("141.0.0.0"))

    def test_is_cached_true(self):
        """Test is_cached returns True for existing version"""
        version = "141.0.0.0"
        driver_path = self.cache.get_driver_path(version)
        driver_path.parent.mkdir(parents=True, exist_ok=True)
        driver_path.write_text("fake driver")

        self.assertTrue(self.cache.is_cached(version))

    def test_list_cached_versions(self):
        """Test listing cached versions"""
        # Create some fake cached versions
        for version in ["141.0.0.0", "140.0.0.0", "139.0.0.0"]:
            driver_path = self.cache.get_driver_path(version)
            driver_path.parent.mkdir(parents=True, exist_ok=True)
            driver_path.write_text("fake")

        versions = self.cache.list_cached_versions()
        self.assertEqual(versions, ["141.0.0.0", "140.0.0.0", "139.0.0.0"])

    def test_set_active(self):
        """Test setting active version via symlink"""
        version = "141.0.0.0"
        driver_path = self.cache.get_driver_path(version)
        driver_path.parent.mkdir(parents=True, exist_ok=True)
        driver_path.write_text("fake driver")

        self.cache.set_active(version)

        current_link = self.temp_dir / "current"
        self.assertTrue(current_link.is_symlink())
        # Use resolve() for both to handle /var vs /private/var on macOS
        self.assertEqual(current_link.resolve(), driver_path.resolve())

    def test_set_active_raises_for_missing_version(self):
        """Test set_active raises error for non-cached version"""
        with self.assertRaises(FileNotFoundError):
            self.cache.set_active("999.0.0.0")

    def test_get_active_version(self):
        """Test getting active version"""
        version = "141.0.0.0"
        driver_path = self.cache.get_driver_path(version)
        driver_path.parent.mkdir(parents=True, exist_ok=True)
        driver_path.write_text("fake driver")

        self.cache.set_active(version)
        active = self.cache.get_active_version()
        self.assertEqual(active, version)

    def test_get_active_version_none(self):
        """Test get_active_version returns None when no active version"""
        active = self.cache.get_active_version()
        self.assertIsNone(active)


class TestVersionDownloader(unittest.TestCase):
    """Test VersionDownloader class"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = VersionCache(self.temp_dir)
        self.downloader = VersionDownloader(self.cache)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_download_already_cached(self):
        """Test that cached version is returned without download"""
        version = "141.0.0.0"
        driver_path = self.cache.get_driver_path(version)
        driver_path.parent.mkdir(parents=True, exist_ok=True)
        driver_path.write_text("fake driver")

        result = self.downloader.download_version(version)
        self.assertEqual(result, driver_path)

    @patch('requests.get')
    def test_download_network_failure(self, mock_get):
        """Test network failure handling"""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        with self.assertRaises(DownloadError):
            self.downloader.download_version("141.0.0.0")

    @patch('requests.get')
    def test_download_retries_on_failure(self, mock_get):
        """Test retry logic on network failure"""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        with self.assertRaises(DownloadError) as cm:
            self.downloader.download_version("141.0.0.0")

        # Should attempt MAX_RETRIES times
        from drivers.constants import MAX_RETRIES
        self.assertEqual(mock_get.call_count, MAX_RETRIES)

    def test_verify_download_missing_file(self):
        """Test verify_download returns False for missing file"""
        fake_path = self.temp_dir / "nonexistent" / "chromedriver"
        self.assertFalse(self.downloader.verify_download(fake_path))

    def test_verify_download_invalid_file(self):
        """Test verify_download returns False for invalid file"""
        fake_driver = self.temp_dir / "chromedriver"
        fake_driver.write_text("not a real driver")
        self.assertFalse(self.downloader.verify_download(fake_driver))


class TestDownloadIntegration(unittest.TestCase):
    """Integration tests for download functionality"""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache = VersionCache(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_cache_directory_structure(self):
        """Test cache creates proper directory structure"""
        version = "141.0.0.0"
        cache_path = self.cache.get_cache_path(version)
        driver_path = self.cache.get_driver_path(version)

        self.assertEqual(cache_path, self.temp_dir / version)
        self.assertEqual(driver_path, cache_path / "chromedriver")

    def test_multiple_versions_coexist(self):
        """Test multiple versions can be cached simultaneously"""
        versions = ["141.0.0.0", "140.0.0.0", "139.0.0.0"]

        for version in versions:
            driver_path = self.cache.get_driver_path(version)
            driver_path.parent.mkdir(parents=True, exist_ok=True)
            driver_path.write_text(f"driver {version}")

        for version in versions:
            self.assertTrue(self.cache.is_cached(version))

        cached = self.cache.list_cached_versions()
        self.assertEqual(len(cached), 3)
        self.assertEqual(set(cached), set(versions))

    def test_symlink_switching(self):
        """Test switching active version via symlink"""
        v1 = "141.0.0.0"
        v2 = "140.0.0.0"

        # Create two versions
        for version in [v1, v2]:
            driver_path = self.cache.get_driver_path(version)
            driver_path.parent.mkdir(parents=True, exist_ok=True)
            driver_path.write_text(f"driver {version}")

        # Set v1 as active
        self.cache.set_active(v1)
        self.assertEqual(self.cache.get_active_version(), v1)

        # Switch to v2
        self.cache.set_active(v2)
        self.assertEqual(self.cache.get_active_version(), v2)

        # Verify symlink points to v2
        current_link = self.temp_dir / "current"
        # Use resolve() for both to handle /var vs /private/var on macOS
        self.assertEqual(current_link.resolve(), self.cache.get_driver_path(v2).resolve())


if __name__ == '__main__':
    unittest.main()
