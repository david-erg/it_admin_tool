"""
Chocolatey Package Manager Integration

Provides comprehensive Chocolatey package management with robust error handling,
timeout protection, and proper progress tracking for GUI integration.
"""

import subprocess
import logging
import re
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import xml.etree.ElementTree as ET

from core import (
    BaseWorker,
    run_command_with_timeout,
    escape_command_arg,
    check_admin_privileges,
    get_error_message,
    CHOCOLATEY_INSTALL_TIMEOUT,
    PACKAGE_SEARCH_TIMEOUT,
    CHOCOLATEY_INSTALL_ARGS,
    VALID_PACKAGE_NAME_PATTERN
)


class PackageStatus(Enum):
    """Package installation status."""
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    OUTDATED = "outdated"
    UNKNOWN = "unknown"


class OperationType(Enum):
    """Chocolatey operation types."""
    INSTALL = "install"
    UNINSTALL = "uninstall"
    UPGRADE = "upgrade"
    SEARCH = "search"
    LIST = "list"


@dataclass
class ChocolateyPackage:
    """Represents a Chocolatey package."""
    name: str
    version: str = ""
    title: str = ""
    description: str = ""
    author: str = ""
    tags: List[str] = field(default_factory=list)
    download_count: int = 0
    status: PackageStatus = PackageStatus.NOT_INSTALLED
    installed_version: str = ""
    available_version: str = ""
    is_prerelease: bool = False
    package_size: str = ""
    dependencies: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate and clean package data."""
        self.name = self.name.strip().lower()
        self.title = self.title.strip() if self.title else self.name.title()
        self.description = self.description.strip()
        
        # Clean version strings
        self.version = self._clean_version(self.version)
        self.installed_version = self._clean_version(self.installed_version)
        self.available_version = self._clean_version(self.available_version)
    
    def _clean_version(self, version: str) -> str:
        """Clean and normalize version string."""
        if not version:
            return ""
        
        # Remove common prefixes/suffixes
        version = version.strip()
        version = re.sub(r'^v?', '', version, flags=re.IGNORECASE)
        version = re.sub(r'\s+', '', version)
        
        return version
    
    def is_installed(self) -> bool:
        """Check if package is installed."""
        return self.status in (PackageStatus.INSTALLED, PackageStatus.OUTDATED)
    
    def needs_update(self) -> bool:
        """Check if package needs update."""
        return self.status == PackageStatus.OUTDATED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'version': self.version,
            'title': self.title,
            'description': self.description,
            'author': self.author,
            'tags': self.tags,
            'download_count': self.download_count,
            'status': self.status.value,
            'installed_version': self.installed_version,
            'available_version': self.available_version,
            'is_prerelease': self.is_prerelease,
            'package_size': self.package_size,
            'dependencies': self.dependencies
        }


@dataclass
class ChocolateyResult:
    """Result of a Chocolatey operation."""
    success: bool
    operation: OperationType
    packages: List[ChocolateyPackage] = field(default_factory=list)
    output: str = ""
    error_message: str = ""
    exit_code: int = 0
    execution_time: float = 0.0
    packages_processed: int = 0
    packages_succeeded: int = 0
    packages_failed: int = 0
    warnings: List[str] = field(default_factory=list)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
        logging.warning(f"Chocolatey warning: {warning}")


class ChocolateyValidator:
    """Validates Chocolatey operations and package names."""
    
    @staticmethod
    def is_valid_package_name(package_name: str) -> Tuple[bool, str]:
        """
        Validate package name format.
        
        Args:
            package_name: Package name to validate
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not package_name:
            return False, "Package name cannot be empty"
        
        if not package_name.strip():
            return False, "Package name cannot be only whitespace"
        
        package_name = package_name.strip()
        
        if len(package_name) > 100:
            return False, "Package name too long (max 100 characters)"
        
        if not VALID_PACKAGE_NAME_PATTERN.match(package_name):
            return False, "Package name contains invalid characters (use letters, numbers, hyphens, dots, underscores only)"
        
        # Check for reserved names or patterns
        reserved_patterns = ['con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5', 'lpt1', 'lpt2']
        if package_name.lower() in reserved_patterns:
            return False, f"'{package_name}' is a reserved name"
        
        return True, ""
    
    @staticmethod
    def validate_package_list(package_names: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate a list of package names.
        
        Args:
            package_names: List of package names to validate
            
        Returns:
            Tuple[List[str], List[str]]: (valid_packages, invalid_packages)
        """
        valid_packages = []
        invalid_packages = []
        
        for package_name in package_names:
            is_valid, error = ChocolateyValidator.is_valid_package_name(package_name)
            if is_valid:
                valid_packages.append(package_name.strip().lower())
            else:
                invalid_packages.append(f"{package_name}: {error}")
        
        return valid_packages, invalid_packages


class ChocolateyManager:
    """
    High-level Chocolatey package manager interface.
    
    Provides robust package management with timeout protection,
    proper error handling, and progress tracking.
    """
    
    def __init__(self):
        """Initialize Chocolatey manager."""
        self.validator = ChocolateyValidator()
        self._chocolatey_path = None
        self._is_available = None
        self._version = None
        
        # Cache for installed packages
        self._installed_cache = {}
        self._cache_time = 0
        self._cache_ttl = 300  # 5 minutes
        
        logging.info("Chocolatey manager initialized")
    
    def is_chocolatey_available(self) -> bool:
        """
        Check if Chocolatey is installed and available.
        
        Returns:
            bool: True if Chocolatey is available
        """
        if self._is_available is not None:
            return self._is_available
        
        try:
            return_code, stdout, stderr = run_command_with_timeout("choco --version", timeout=10)
            
            if return_code == 0:
                self._is_available = True
                self._version = stdout.strip()
                self._chocolatey_path = "choco"
                logging.info(f"Chocolatey detected: version {self._version}")
            else:
                self._is_available = False
                logging.warning("Chocolatey not found or not working")
            
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            self._is_available = False
            logging.warning("Chocolatey not available")
        
        return self._is_available
    
    def is_chocolatey_installed(self) -> bool:
        """
        Check if Chocolatey is installed.
        
        Returns:
            bool: True if Chocolatey is installed
        """
        return self.is_chocolatey_available()
    
    def get_chocolatey_version(self) -> str:
        """
        Get Chocolatey version.
        
        Returns:
            str: Chocolatey version or "Unknown" if not available
        """
        if self.is_chocolatey_available():
            return self._version or "Unknown"
        return "Not installed"
    
    def get_chocolatey_info(self) -> Dict[str, Any]:
        """
        Get Chocolatey installation information.
        
        Returns:
            Dict[str, Any]: Chocolatey information
        """
        if not self.is_chocolatey_available():
            return {
                'available': False,
                'error': 'Chocolatey not installed or not accessible'
            }
        
        return {
            'available': True,
            'version': self._version,
            'path': self._chocolatey_path,
            'admin_required': not check_admin_privileges(),
            'cache_size': len(self._installed_cache),
            'cache_age_seconds': time.time() - self._cache_time if self._cache_time else 0
        }
    
    def test_chocolatey_functionality(self) -> Tuple[bool, str]:
        """
        Test Chocolatey functionality.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not self.is_chocolatey_installed():
            return False, "Chocolatey is not installed or not in PATH"
        
        try:
            # Test 1: Basic version check
            return_code, stdout, stderr = run_command_with_timeout("choco --version", timeout=15)
            
            if return_code != 0:
                return False, f"Chocolatey version check failed: {stderr}"
            
            # Test 2: List command
            return_code, stdout, stderr = run_command_with_timeout(
                "choco list chocolatey --exact", timeout=30
            )
            
            if return_code != 0:
                return False, f"Chocolatey list command failed: {stderr}"
            
            # Test 3: Search command (basic test)
            return_code, stdout, stderr = run_command_with_timeout(
                "choco search chocolatey --exact --limit-output", timeout=30
            )
            
            if return_code != 0:
                return False, f"Chocolatey search command failed: {stderr}"
            
            # All tests passed
            version = self._version or "Unknown"
            return True, f"Chocolatey is working properly (version: {version})"
            
        except Exception as e:
            return False, f"Chocolatey test failed with exception: {str(e)}"
    
    def check_internet_connectivity(self) -> Tuple[bool, str]:
        """
        Check internet connectivity for Chocolatey operations.
        
        Returns:
            Tuple[bool, str]: (has_internet, message)
        """
        test_hosts = [
            "chocolatey.org",
            "packages.chocolatey.org",
            "community.chocolatey.org"
        ]
        
        import socket
        
        for host in test_hosts:
            try:
                # Test DNS resolution and basic connectivity
                socket.setdefaulttimeout(5)
                socket.gethostbyname(host)
                return True, f"Internet connectivity verified ({host})"
            except (socket.gaierror, socket.timeout, OSError):
                continue
        
        return False, "Cannot reach Chocolatey repositories - check internet connection"
    
    def search_packages(
        self,
        query: str,
        limit: int = 50,
        include_prerelease: bool = False,
        exact_match: bool = False
    ) -> ChocolateyResult:
        """
        Search for packages in Chocolatey repository.
        
        Args:
            query: Search query
            limit: Maximum number of results
            include_prerelease: Include prerelease packages
            exact_match: Search for exact matches only
            
        Returns:
            ChocolateyResult: Search results
        """
        start_time = time.time()
        result = ChocolateyResult(success=False, operation=OperationType.SEARCH)
        
        if not self.is_chocolatey_available():
            result.error_message = "Chocolatey is not available"
            return result
        
        try:
            # Validate query
            is_valid, error_msg = self.validator.is_valid_package_name(query)
            if not is_valid and exact_match:
                result.error_message = f"Invalid package name: {error_msg}"
                return result
            
            # Build search command
            cmd_parts = ["choco", "search", query]
            
            if exact_match:
                cmd_parts.append("--exact")
            
            if include_prerelease:
                cmd_parts.append("--prerelease")
            
            if limit > 0:
                cmd_parts.extend(["--page-size", str(limit)])
            
            cmd_parts.append("--limit-output")
            
            cmd = " ".join(cmd_parts)
            
            # Execute search
            return_code, stdout, stderr = run_command_with_timeout(
                cmd, timeout=PACKAGE_SEARCH_TIMEOUT
            )
            
            result.execution_time = time.time() - start_time
            result.exit_code = return_code
            result.output = stdout
            
            if return_code == 0:
                # Parse search results
                packages = self._parse_search_output(stdout)
                result.packages = packages
                result.packages_processed = len(packages)
                result.success = True
            else:
                result.error_message = f"Search failed: {stderr}"
            
        except subprocess.TimeoutExpired:
            result.error_message = f"Search timed out after {PACKAGE_SEARCH_TIMEOUT} seconds"
        except Exception as e:
            result.error_message = f"Search error: {str(e)}"
        
        result.execution_time = time.time() - start_time
        return result
    
    def _parse_search_output(self, output: str) -> List[ChocolateyPackage]:
        """
        Parse Chocolatey search output.
        
        Args:
            output: Raw search output
            
        Returns:
            List[ChocolateyPackage]: Parsed packages
        """
        packages = []
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            
            # Parse limited output format: packagename|version
            parts = line.split('|')
            if len(parts) >= 2:
                package = ChocolateyPackage(
                    name=parts[0].strip(),
                    version=parts[1].strip()
                )
                packages.append(package)
        
        return packages
    
    def install_packages(
        self,
        package_names: List[str],
        force: bool = False,
        skip_powershell: bool = True,
        ignore_checksums: bool = False
    ) -> ChocolateyResult:
        """
        Install multiple packages.
        
        Args:
            package_names: List of package names to install
            force: Force installation
            skip_powershell: Skip PowerShell scripts
            ignore_checksums: Ignore package checksums
            
        Returns:
            ChocolateyResult: Installation results
        """
        start_time = time.time()
        result = ChocolateyResult(success=False, operation=OperationType.INSTALL)
        
        if not self.is_chocolatey_available():
            result.error_message = "Chocolatey is not available"
            return result
        
        if not package_names:
            result.error_message = "No packages specified"
            return result
        
        try:
            # Validate package names
            valid_packages, invalid_packages = self.validator.validate_package_list(package_names)
            
            if invalid_packages:
                result.add_warning(f"Invalid packages skipped: {', '.join(invalid_packages)}")
            
            if not valid_packages:
                result.error_message = "No valid packages to install"
                return result
            
            # Build install command
            cmd_parts = ["choco", "install"] + valid_packages + ["-y"]
            
            if force:
                cmd_parts.append("--force")
            
            if skip_powershell:
                cmd_parts.append("--skip-powershell")
            
            if ignore_checksums:
                cmd_parts.append("--ignore-checksums")
            
            cmd = " ".join(cmd_parts)
            
            # Execute installation
            return_code, stdout, stderr = run_command_with_timeout(
                cmd, timeout=CHOCOLATEY_INSTALL_TIMEOUT
            )
            
            result.execution_time = time.time() - start_time
            result.exit_code = return_code
            result.output = stdout
            result.packages_processed = len(valid_packages)
            
            if return_code == 0:
                result.success = True
                result.packages_succeeded = len(valid_packages)
            else:
                result.error_message = f"Installation failed: {stderr}"
                result.packages_failed = len(valid_packages)
            
        except subprocess.TimeoutExpired:
            result.error_message = f"Installation timed out after {CHOCOLATEY_INSTALL_TIMEOUT} seconds"
        except Exception as e:
            result.error_message = f"Installation error: {str(e)}"
        
        result.execution_time = time.time() - start_time
        return result


class ChocolateyInstallWorker(BaseWorker):
    """
    Worker class for installing Chocolatey package manager.
    
    This worker handles the installation of Chocolatey itself in a background thread,
    providing progress updates and handling the PowerShell installation script.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.installation_url = "https://chocolatey.org/install.ps1"
    
    def do_work(self) -> bool:
        """
        Install Chocolatey package manager.
        
        Returns:
            bool: True if installation successful, False otherwise
        """
        try:
            self.signals.emit_status("Starting Chocolatey installation...")
            
            # Check if already installed
            if self._check_existing_installation():
                self.signals.emit_status("Chocolatey is already installed")
                return True
            
            # Check admin privileges
            if not check_admin_privileges():
                self.signals.emit_status("ERROR: Administrator privileges required for Chocolatey installation")
                return False
            
            self.signals.emit_status("Downloading Chocolatey installation script...")
            
            # PowerShell command to install Chocolatey
            install_command = [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                (
                    "Set-ExecutionPolicy Bypass -Scope Process -Force; "
                    "[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
                    "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
                )
            ]
            
            self.signals.emit_status("Running Chocolatey installation...")
            
            # Execute installation command
            return_code, stdout, stderr = run_command_with_timeout(
                " ".join(f'"{arg}"' if " " in arg else arg for arg in install_command),
                timeout=CHOCOLATEY_INSTALL_TIMEOUT
            )
            
            if return_code == 0:
                self.signals.emit_status("Chocolatey installation completed successfully")
                
                # Verify installation
                if self._verify_installation():
                    self.signals.emit_status("✓ Chocolatey installation verified")
                    return True
                else:
                    self.signals.emit_status("⚠ Warning: Chocolatey installation cannot be verified")
                    return False
            else:
                error_msg = f"Chocolatey installation failed (return code: {return_code})"
                if stderr:
                    error_msg += f"\nError: {stderr}"
                self.signals.emit_status(error_msg)
                return False
                
        except subprocess.TimeoutExpired:
            self.signals.emit_status("ERROR: Chocolatey installation timed out")
            return False
        except Exception as e:
            self.signals.emit_status(f"ERROR: Chocolatey installation failed: {str(e)}")
            return False
    
    def _check_existing_installation(self) -> bool:
        """Check if Chocolatey is already installed."""
        try:
            return_code, stdout, stderr = run_command_with_timeout("choco --version", timeout=10)
            return return_code == 0
        except:
            return False
    
    def _verify_installation(self) -> bool:
        """Verify that Chocolatey was installed successfully."""
        try:
            # Wait a moment for installation to complete
            time.sleep(2)
            
            # Test basic Chocolatey command
            return_code, stdout, stderr = run_command_with_timeout("choco --version", timeout=15)
            
            if return_code == 0 and stdout.strip():
                self.signals.emit_status(f"Chocolatey version: {stdout.strip()}")
                return True
            return False
            
        except Exception as e:
            self.signals.emit_status(f"Installation verification failed: {str(e)}")
            return False