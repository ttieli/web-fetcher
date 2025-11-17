"""
ChromeDriver Version Detection and Management
ChromeDriver版本检测和管理
"""
import subprocess
import re
import zipfile
import time
import tempfile
import shutil
import requests
from pathlib import Path
from typing import Optional, Tuple, List, Callable
from dataclasses import dataclass
from .constants import (
    CHROME_EXECUTABLE,
    CHROME_PLIST,
    CHROMEDRIVER_LOCATIONS,
    CACHE_BASE_PATH,
    CompatibilityStatus,
    CHROME_FOR_TESTING_URL_TEMPLATE,
    DOWNLOAD_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY
)

@dataclass
class CompatibilityResult:
    """Version compatibility check result"""
    status: CompatibilityStatus
    chrome_version: Optional[str]
    driver_version: Optional[str]
    message_en: str
    message_cn: str

    @property
    def is_compatible(self) -> bool:
        return self.status == CompatibilityStatus.COMPATIBLE

class VersionDetector:
    """Detect Chrome and ChromeDriver versions"""

    def get_chrome_version(self) -> Optional[str]:
        """
        Detect installed Chrome version on macOS
        检测macOS上已安装的Chrome版本

        Returns:
            Version string (e.g., "141.0.6496.0") or None if not found
        """
        # Try method 1: Direct executable call
        try:
            result = subprocess.run(
                [CHROME_EXECUTABLE, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Output format: "Google Chrome 141.0.6496.0"
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                if match:
                    return match.group(1)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Try method 2: Read from plist
        try:
            result = subprocess.run(
                ["defaults", "read", CHROME_PLIST, "CFBundleShortVersionString"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                if re.match(r'\d+\.\d+\.\d+\.\d+', version):
                    return version
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def get_chromedriver_version(self) -> Optional[str]:
        """
        Detect installed ChromeDriver version
        检测已安装的ChromeDriver版本

        Returns:
            Version string or None if not found
        """
        for location in CHROMEDRIVER_LOCATIONS:
            try:
                result = subprocess.run(
                    [location, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Output format: "ChromeDriver 140.0.6476.0 (hash)"
                    match = re.search(r'ChromeDriver\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if match:
                        return match.group(1)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        return None

    def check_compatibility(
        self,
        chrome_version: Optional[str],
        driver_version: Optional[str]
    ) -> CompatibilityResult:
        """
        Check version compatibility
        检查版本兼容性

        Args:
            chrome_version: Chrome version string
            driver_version: ChromeDriver version string

        Returns:
            CompatibilityResult with status and messages
        """
        # Handle missing versions
        if chrome_version is None:
            return CompatibilityResult(
                status=CompatibilityStatus.CHROME_NOT_FOUND,
                chrome_version=None,
                driver_version=driver_version,
                message_en="Chrome browser not found on this system",
                message_cn="系统中未找到Chrome浏览器"
            )

        if driver_version is None:
            return CompatibilityResult(
                status=CompatibilityStatus.DRIVER_NOT_FOUND,
                chrome_version=chrome_version,
                driver_version=None,
                message_en="ChromeDriver not found on this system",
                message_cn="系统中未找到ChromeDriver"
            )

        # Compare major versions
        chrome_major = int(chrome_version.split('.')[0])
        driver_major = int(driver_version.split('.')[0])

        if chrome_major == driver_major:
            return CompatibilityResult(
                status=CompatibilityStatus.COMPATIBLE,
                chrome_version=chrome_version,
                driver_version=driver_version,
                message_en=f"Compatible: Chrome {chrome_version} ✓ ChromeDriver {driver_version}",
                message_cn=f"兼容: Chrome {chrome_version} ✓ ChromeDriver {driver_version}"
            )
        else:
            return CompatibilityResult(
                status=CompatibilityStatus.MISMATCH,
                chrome_version=chrome_version,
                driver_version=driver_version,
                message_en=f"Version mismatch: Chrome {chrome_major} vs ChromeDriver {driver_major}",
                message_cn=f"版本不匹配: Chrome {chrome_major} vs ChromeDriver {driver_major}"
            )

def check_chrome_driver_compatibility() -> CompatibilityResult:
    """
    Convenience function to check Chrome/ChromeDriver compatibility
    便捷函数：检查Chrome/ChromeDriver兼容性
    """
    detector = VersionDetector()
    chrome_ver = detector.get_chrome_version()
    driver_ver = detector.get_chromedriver_version()
    return detector.check_compatibility(chrome_ver, driver_ver)


class VersionCache:
    """Manage cached ChromeDriver versions"""

    def __init__(self, cache_base: Path = CACHE_BASE_PATH):
        self.cache_base = cache_base
        self.cache_base.mkdir(parents=True, exist_ok=True)

    def get_cache_path(self, version: str) -> Path:
        """
        Get cache directory path for a specific version
        获取特定版本的缓存目录路径

        Args:
            version: ChromeDriver version (e.g., "141.0.6496.0")

        Returns:
            Path to version cache directory
        """
        return self.cache_base / version

    def get_driver_path(self, version: str) -> Path:
        """Get full path to chromedriver executable"""
        return self.get_cache_path(version) / "chromedriver"

    def is_cached(self, version: str) -> bool:
        """
        Check if version is already cached
        检查版本是否已缓存
        """
        driver_path = self.get_driver_path(version)
        return driver_path.exists() and driver_path.is_file()

    def list_cached_versions(self) -> List[str]:
        """
        List all cached versions
        列出所有已缓存的版本

        Returns:
            List of version strings
        """
        if not self.cache_base.exists():
            return []

        versions = []
        for item in self.cache_base.iterdir():
            if item.is_dir() and (item / "chromedriver").exists():
                versions.append(item.name)

        return sorted(versions, reverse=True)  # Latest first

    def set_active(self, version: str) -> None:
        """
        Set active ChromeDriver version via symlink
        通过符号链接设置活动的ChromeDriver版本

        Args:
            version: Version to activate
        """
        current_link = self.cache_base / "current"
        target = self.get_driver_path(version)

        if not target.exists():
            raise FileNotFoundError(f"Version {version} not cached")

        # Remove old symlink if exists
        if current_link.exists() or current_link.is_symlink():
            current_link.unlink()

        # Create new symlink
        current_link.symlink_to(target)

    def get_active_version(self) -> Optional[str]:
        """Get currently active version"""
        current_link = self.cache_base / "current"
        if current_link.is_symlink():
            target = current_link.resolve()
            return target.parent.name
        return None


class DownloadError(Exception):
    """Download operation failed"""
    pass


class VersionDownloader:
    """Download ChromeDriver from official sources"""

    def __init__(self, cache: VersionCache = None):
        self.cache = cache or VersionCache()

    def download_version(
        self,
        version: str,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Path:
        """
        Download specific ChromeDriver version
        下载特定版本的ChromeDriver

        Args:
            version: Version to download
            progress_callback: Optional callback(downloaded, total)

        Returns:
            Path to downloaded driver

        Raises:
            DownloadError: If download fails
        """
        # Check if already cached
        if self.cache.is_cached(version):
            return self.cache.get_driver_path(version)

        # Try official source first
        try:
            return self._download_from_chrome_for_testing(version, progress_callback)
        except Exception as e:
            # Try fallback methods
            try:
                return self._download_via_selenium_manager(version)
            except Exception as fallback_error:
                raise DownloadError(
                    f"Failed to download ChromeDriver {version}. "
                    f"Official source: {e}. Fallback: {fallback_error}"
                )

    def _download_from_chrome_for_testing(
        self,
        version: str,
        progress_callback: Optional[Callable] = None
    ) -> Path:
        """Download from Chrome for Testing official source"""
        url = CHROME_FOR_TESTING_URL_TEMPLATE.format(version=version)

        # Retry logic
        for attempt in range(MAX_RETRIES):
            try:
                # Download zip file
                response = requests.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT)
                response.raise_for_status()

                # Prepare temp file
                temp_zip = Path(tempfile.mktemp(suffix='.zip'))

                # Download with progress
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0

                with open(temp_zip, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_size:
                                progress_callback(downloaded, total_size)

                # Extract
                driver_path = self._extract_driver(temp_zip, version)

                # Cleanup
                temp_zip.unlink()

                return driver_path

            except requests.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                    continue
                raise DownloadError(f"Download failed after {MAX_RETRIES} attempts: {e}")

    def _extract_driver(self, zip_path: Path, version: str) -> Path:
        """Extract ChromeDriver from zip and place in cache"""
        cache_dir = self.cache.get_cache_path(version)
        cache_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find chromedriver executable in zip
            for name in zip_ref.namelist():
                # Match only the actual binary, not files like LICENSE.chromedriver
                if (name.endswith('/chromedriver') or name == 'chromedriver') and not name.endswith('/'):
                    # Extract to cache directory
                    zip_ref.extract(name, cache_dir)
                    extracted_path = cache_dir / name

                    # Move to standard location if nested
                    driver_path = cache_dir / "chromedriver"
                    if extracted_path != driver_path:
                        extracted_path.rename(driver_path)
                        # Clean up parent directory if empty
                        try:
                            extracted_path.parent.rmdir()
                        except OSError:
                            pass

                    # Set executable permission
                    driver_path.chmod(0o755)

                    return driver_path

        raise DownloadError("ChromeDriver executable not found in downloaded archive")

    def _download_via_selenium_manager(self, version: str) -> Path:
        """Fallback: Use selenium-manager to download driver"""
        try:
            # This requires selenium package
            # Try to use selenium-manager command
            result = subprocess.run(
                ["selenium-manager", "--driver", "chrome", "--browser-version", version],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                # Parse output to find driver path
                # selenium-manager outputs path to driver
                driver_path = result.stdout.strip().split()[-1]

                # Copy to our cache
                cache_dir = self.cache.get_cache_path(version)
                cache_dir.mkdir(parents=True, exist_ok=True)
                cached_path = cache_dir / "chromedriver"

                shutil.copy2(driver_path, cached_path)
                cached_path.chmod(0o755)

                return cached_path
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise DownloadError(f"Selenium Manager fallback failed: {e}")

    def verify_download(self, driver_path: Path) -> bool:
        """
        Verify downloaded driver is valid
        验证下载的驱动是否有效
        """
        if not driver_path.exists():
            return False

        # Check if executable
        if not driver_path.is_file():
            return False

        # Try to run --version
        try:
            result = subprocess.run(
                [str(driver_path), "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False


def download_compatible_driver(
    progress_callback: Optional[Callable] = None
) -> Optional[Path]:
    """
    Download ChromeDriver matching installed Chrome version
    下载与已安装Chrome版本匹配的ChromeDriver

    Returns:
        Path to downloaded driver, or None if Chrome not found
    """
    detector = VersionDetector()
    chrome_version = detector.get_chrome_version()

    if not chrome_version:
        return None

    downloader = VersionDownloader()
    return downloader.download_version(chrome_version, progress_callback)
