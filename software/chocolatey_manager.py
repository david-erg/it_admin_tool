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
            result = run_command_with_timeout(
                ["choco", "--version"],
                timeout=10,
                capture_output=True
            )
            
            if result.returncode == 0:
                self._is_available = True
                self._version = result.stdout.strip()
                self._chocolatey_path = "choco"
                logging.info(f"Chocolatey detected: version {self._version}")
            else:
                self._is_available = False
                logging.warning("Chocolatey not found or not working")
            
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            self._is_available = False
            logging.warning("Chocolatey not available")
        
        return self._is_available
    
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
            exact_match: Exact package name match only
            
        Returns:
            ChocolateyResult: Search results
        """
        result = ChocolateyResult(
            success=False,
            operation=OperationType.SEARCH
        )
        
        if not self.is_chocolatey_available():
            result.error_message = get_error_message('chocolatey_not_found')
            return result
        
        if not query or not query.strip():
            result.error_message = "Search query cannot be empty"
            return result
        
        try:
            start_time = time.time()
            
            # Build command
            cmd = ["choco", "search", query.strip()]
            
            if exact_match:
                cmd.append("--exact")
            
            if include_prerelease:
                cmd.append("--prerelease")
            
            cmd.extend(["--limit-output", f"--page-size={limit}"])
            
            # Execute search with timeout
            logging.info(f"Searching packages: {query}")
            process_result = run_command_with_timeout(
                cmd,
                timeout=PACKAGE_SEARCH_TIMEOUT,
                capture_output=True
            )
            
            result.exit_code = process_result.returncode
            result.output = process_result.stdout
            result.execution_time = time.time() - start_time
            
            if process_result.returncode != 0:
                result.error_message = f"Chocolatey search failed: {process_result.stderr}"
                return result
            
            # Parse results
            packages = self._parse_search_output(process_result.stdout)
            result.packages = packages[:limit]  # Ensure limit
            result.packages_processed = len(result.packages)
            result.success = True
            
            logging.info(f"Found {len(result.packages)} packages for query: {query}")
            
        except subprocess.TimeoutExpired:
            result.error_message = f"Search timed out after {PACKAGE_SEARCH_TIMEOUT} seconds"
            logging.error(f"Package search timed out: {query}")
        except Exception as e:
            result.error_message = f"Search failed: {str(e)}"
            logging.error(f"Package search error: {e}")
        
        return result
    
    def get_installed_packages(self, refresh_cache: bool = False) -> ChocolateyResult:
        """
        Get list of installed packages.
        
        Args:
            refresh_cache: Force refresh of package cache
            
        Returns:
            ChocolateyResult: Installed packages
        """
        result = ChocolateyResult(
            success=False,
            operation=OperationType.LIST
        )
        
        if not self.is_chocolatey_available():
            result.error_message = get_error_message('chocolatey_not_found')
            return result
        
        # Check cache
        current_time = time.time()
        if not refresh_cache and self._installed_cache and (current_time - self._cache_time) < self._cache_ttl:
            result.packages = list(self._installed_cache.values())
            result.packages_processed = len(result.packages)
            result.success = True
            return result
        
        try:
            start_time = time.time()
            
            # Get installed packages
            cmd = ["choco", "list", "--local-only", "--limit-output"]
            
            logging.info("Getting installed packages list")
            process_result = run_command_with_timeout(
                cmd,
                timeout=30,
                capture_output=True
            )
            
            result.exit_code = process_result.returncode
            result.output = process_result.stdout
            result.execution_time = time.time() - start_time
            
            if process_result.returncode != 0:
                result.error_message = f"Failed to get installed packages: {process_result.stderr}"
                return result
            
            # Parse results
            packages = self._parse_installed_output(process_result.stdout)
            result.packages = packages
            result.packages_processed = len(packages)
            result.success = True
            
            # Update cache
            self._installed_cache = {pkg.name: pkg for pkg in packages}
            self._cache_time = current_time
            
            logging.info(f"Found {len(packages)} installed packages")
            
        except subprocess.TimeoutExpired:
            result.error_message = "Getting installed packages timed out"
            logging.error("Get installed packages timed out")
        except Exception as e:
            result.error_message = f"Failed to get installed packages: {str(e)}"
            logging.error(f"Get installed packages error: {e}")
        
        return result
    
    def get_package_info(self, package_name: str) -> Optional[ChocolateyPackage]:
        """
        Get detailed information about a specific package.
        
        Args:
            package_name: Package name
            
        Returns:
            Optional[ChocolateyPackage]: Package information or None
        """
        # Validate package name
        is_valid, error = self.validator.is_valid_package_name(package_name)
        if not is_valid:
            logging.error(f"Invalid package name: {error}")
            return None
        
        # Try exact search first
        search_result = self.search_packages(package_name, limit=1, exact_match=True)
        if search_result.success and search_result.packages:
            package = search_result.packages[0]
            
            # Check if installed
            if package_name in self._installed_cache:
                installed_pkg = self._installed_cache[package_name]
                package.status = PackageStatus.INSTALLED
                package.installed_version = installed_pkg.installed_version
                
                # Check if outdated
                if package.version and installed_pkg.installed_version:
                    if self._compare_versions(package.version, installed_pkg.installed_version) > 0:
                        package.status = PackageStatus.OUTDATED
                        package.available_version = package.version
            
            return package
        
        return None
    
    def install_packages(self, package_names: List[str]) -> ChocolateyResult:
        """
        Install multiple packages.
        
        Args:
            package_names: List of package names to install
            
        Returns:
            ChocolateyResult: Installation result
        """
        result = ChocolateyResult(
            success=False,
            operation=OperationType.INSTALL
        )
        
        if not self.is_chocolatey_available():
            result.error_message = get_error_message('chocolatey_not_found')
            return result
        
        if not check_admin_privileges():
            result.error_message = get_error_message('admin_required')
            return result
        
        # Validate package names
        valid_packages, invalid_packages = self.validator.validate_package_list(package_names)
        
        if invalid_packages:
            result.add_warning(f"Invalid packages skipped: {', '.join(invalid_packages)}")
        
        if not valid_packages:
            result.error_message = "No valid packages to install"
            return result
        
        try:
            start_time = time.time()
            
            # Build command
            cmd = ["choco", "install"] + valid_packages + CHOCOLATEY_INSTALL_ARGS
            
            logging.info(f"Installing packages: {', '.join(valid_packages)}")
            
            # Execute installation
            process_result = run_command_with_timeout(
                cmd,
                timeout=CHOCOLATEY_INSTALL_TIMEOUT,
                capture_output=True
            )
            
            result.exit_code = process_result.returncode
            result.output = process_result.stdout
            result.execution_time = time.time() - start_time
            result.packages_processed = len(valid_packages)
            
            # Parse installation results
            if process_result.returncode == 0:
                result.success = True
                result.packages_succeeded = len(valid_packages)
                
                # Clear cache to force refresh
                self._installed_cache.clear()
                self._cache_time = 0
                
                logging.info(f"Successfully installed {len(valid_packages)} packages")
            else:
                # Try to determine which packages failed
                failed_packages = self._parse_installation_failures(process_result.stdout, valid_packages)
                result.packages_failed = len(failed_packages)
                result.packages_succeeded = len(valid_packages) - result.packages_failed
                
                if result.packages_succeeded > 0:
                    result.success = True
                    result.add_warning(f"Some packages failed to install: {', '.join(failed_packages)}")
                else:
                    result.error_message = f"All packages failed to install: {process_result.stderr}"
            
        except subprocess.TimeoutExpired:
            result.error_message = f"Installation timed out after {CHOCOLATEY_INSTALL_TIMEOUT} seconds"
            logging.error(f"Package installation timed out: {valid_packages}")
        except Exception as e:
            result.error_message = f"Installation failed: {str(e)}"
            logging.error(f"Package installation error: {e}")
        
        return result
    
    def uninstall_packages(self, package_names: List[str]) -> ChocolateyResult:
        """
        Uninstall multiple packages.
        
        Args:
            package_names: List of package names to uninstall
            
        Returns:
            ChocolateyResult: Uninstallation result
        """
        result = ChocolateyResult(
            success=False,
            operation=OperationType.UNINSTALL
        )
        
        if not self.is_chocolatey_available():
            result.error_message = get_error_message('chocolatey_not_found')
            return result
        
        if not check_admin_privileges():
            result.error_message = get_error_message('admin_required')
            return result
        
        # Validate package names
        valid_packages, invalid_packages = self.validator.validate_package_list(package_names)
        
        if invalid_packages:
            result.add_warning(f"Invalid packages skipped: {', '.join(invalid_packages)}")
        
        if not valid_packages:
            result.error_message = "No valid packages to uninstall"
            return result
        
        try:
            start_time = time.time()
            
            # Build command
            cmd = ["choco", "uninstall"] + valid_packages + ["--yes", "--remove-dependencies"]
            
            logging.info(f"Uninstalling packages: {', '.join(valid_packages)}")
            
            # Execute uninstallation
            process_result = run_command_with_timeout(
                cmd,
                timeout=CHOCOLATEY_INSTALL_TIMEOUT,
                capture_output=True
            )
            
            result.exit_code = process_result.returncode
            result.output = process_result.stdout
            result.execution_time = time.time() - start_time
            result.packages_processed = len(valid_packages)
            
            if process_result.returncode == 0:
                result.success = True
                result.packages_succeeded = len(valid_packages)
                
                # Clear cache to force refresh
                self._installed_cache.clear()
                self._cache_time = 0
                
                logging.info(f"Successfully uninstalled {len(valid_packages)} packages")
            else:
                result.error_message = f"Uninstallation failed: {process_result.stderr}"
                result.packages_failed = len(valid_packages)
            
        except subprocess.TimeoutExpired:
            result.error_message = f"Uninstallation timed out after {CHOCOLATEY_INSTALL_TIMEOUT} seconds"
            logging.error(f"Package uninstallation timed out: {valid_packages}")
        except Exception as e:
            result.error_message = f"Uninstallation failed: {str(e)}"
            logging.error(f"Package uninstallation error: {e}")
        
        return result
    
    def _parse_search_output(self, output: str) -> List[ChocolateyPackage]:
        """Parse Chocolatey search output."""
        packages = []
        
        try:
            for line in output.strip().split('\n'):
                line = line.strip()
                if not line or '|' not in line:
                    continue
                
                # Expected format: packagename|version
                parts = line.split('|', 1)
                if len(parts) >= 2:
                    name = parts[0].strip().lower()
                    version = parts[1].strip()
                    
                    if name and version:
                        package = ChocolateyPackage(
                            name=name,
                            version=version,
                            title=name.title(),
                            status=PackageStatus.NOT_INSTALLED
                        )
                        packages.append(package)
        
        except Exception as e:
            logging.error(f"Failed to parse search output: {e}")
        
        return packages
    
    def _parse_installed_output(self, output: str) -> List[ChocolateyPackage]:
        """Parse Chocolatey installed packages output."""
        packages = []
        
        try:
            for line in output.strip().split('\n'):
                line = line.strip()
                if not line or '|' not in line:
                    continue
                
                # Expected format: packagename|version
                parts = line.split('|', 1)
                if len(parts) >= 2:
                    name = parts[0].strip().lower()
                    version = parts[1].strip()
                    
                    if name and version:
                        package = ChocolateyPackage(
                            name=name,
                            version=version,
                            installed_version=version,
                            title=name.title(),
                            status=PackageStatus.INSTALLED
                        )
                        packages.append(package)
        
        except Exception as e:
            logging.error(f"Failed to parse installed output: {e}")
        
        return packages
    
    def _parse_installation_failures(self, output: str, package_names: List[str]) -> List[str]:
        """Parse installation output to identify failed packages."""
        failed = []
        
        try:
            output_lower = output.lower()
            for package_name in package_names:
                # Look for failure indicators
                if any(indicator in output_lower for indicator in [
                    f"{package_name.lower()} not installed",
                    f"{package_name.lower()} failed",
                    f"error installing {package_name.lower()}"
                ]):
                    failed.append(package_name)
        
        except Exception as e:
            logging.error(f"Failed to parse installation failures: {e}")
            # If parsing fails, assume all failed for safety
            return package_names
        
        return failed
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Returns:
            int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
        """
        try:
            # Simple version comparison - split by dots and compare numerically
            def normalize_version(v: str) -> List[int]:
                # Remove non-numeric suffixes
                v = re.sub(r'[^0-9.].*$', '', v)
                parts = v.split('.')
                return [int(p) if p.isdigit() else 0 for p in parts]
            
            v1_parts = normalize_version(version1)
            v2_parts = normalize_version(version2)
            
            # Pad to same length
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            # Compare
            for p1, p2 in zip(v1_parts, v2_parts):
                if p1 < p2:
                    return -1
                elif p1 > p2:
                    return 1
            
            return 0
            
        except Exception:
            # Fallback to string comparison
            if version1 < version2:
                return -1
            elif version1 > version2:
                return 1
            else:
                return 0
    
    def clear_cache(self) -> None:
        """Clear the installed packages cache."""
        self._installed_cache.clear()
        self._cache_time = 0
        logging.info("Chocolatey package cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        current_time = time.time()
        cache_age = current_time - self._cache_time if self._cache_time else 0
        
        return {
            'size': len(self._installed_cache),
            'age_seconds': cache_age,
            'age_minutes': cache_age / 60,
            'is_fresh': cache_age < self._cache_ttl,
            'ttl_seconds': self._cache_ttl
        }