"""
ChromeDriver Version Detection and Management
ChromeDriver版本检测和管理
"""
import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from .constants import (
    CHROME_EXECUTABLE,
    CHROME_PLIST,
    CHROMEDRIVER_LOCATIONS,
    CompatibilityStatus
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
