"""
Chocolatey package manager integration.

This module handles Chocolatey installation, verification, and basic operations
for the IT Admin Tool.
"""

import subprocess
from typing import Tuple, Optional

from core import (
    BaseWorker, run_command_with_timeout, check_admin_privileges,
    CHOCOLATEY_INSTALL_TIMEOUT
)


class ChocolateyManager:
    """
    Manages Chocolatey package manager operations.
    
    This class provides methods for checking Chocolatey installation status,
    installing Chocolatey, and performing basic Chocolatey operations.
    """
    
    def __init__(self):
        self._chocolatey_available = None
        self._chocolatey_version = None
    
    def is_chocolatey_installed(self, force_check: bool = False) -> bool:
        """
        Check if Chocolatey is installed and available.
        
        Args:
            force_check: Force a fresh check instead of using cached result
        
        Returns:
            bool: True if Chocolatey is available
        """
        if self._chocolatey_available is None or force_check:
            try:
                return_code, stdout, stderr = run_command_with_timeout(
                    "choco --version", 
                    timeout=10
                )
                
                if return_code == 0 and stdout.strip():
                    self._chocolatey_available = True
                    self._chocolatey_version = stdout.strip()
                else:
                    self._chocolatey_available = False
                    self._chocolatey_version = None
                    
            except Exception:
                self._chocolatey_available = False
                self._chocolatey_version = None
        
        return self._chocolatey_available or False
    
    def get_chocolatey_version(self) -> Optional[str]:
        """
        Get the installed Chocolatey version.
        
        Returns:
            Optional[str]: Chocolatey version string or None if not installed
        """
        if not self.is_chocolatey_installed():
            return None
        
        return self._chocolatey_version
    
    def test_chocolatey_functionality(self) -> Tuple[bool, str]:
        """
        Test basic Chocolatey functionality.
        
        Returns:
            Tuple[bool, str]: (is_working, status_message)
        """
        if not self.is_chocolatey_installed():
            return False, "Chocolatey is not installed"
        
        try:
            # Test with a simple command
            return_code, stdout, stderr = run_command_with_timeout(
                "choco list chocolatey --exact --local-only",
                timeout=15
            )
            
            if return_code == 0:
                return True, f"Chocolatey is working (version: {self._chocolatey_version})"
            else:
                return False, f"Chocolatey command failed: {stderr}"
                
        except Exception as e:
            return False, f"Chocolatey test failed: {str(e)}"
    
    def check_internet_connectivity(self) -> Tuple[bool, str]:
        """
        Check internet connectivity for Chocolatey operations.
        
        Returns:
            Tuple[bool, str]: (has_connectivity, status_message)
        """
        try:
            return_code, stdout, stderr = run_command_with_timeout(
                "ping chocolatey.org -n 1",
                timeout=10
            )
            
            if return_code == 0:
                return True, "Internet connection available"
            else:
                return False, "Internet connection may be limited"
                
        except Exception:
            return False, "Could not verify internet connection"
    
    def get_installed_packages(self, limit: int = 100) -> Tuple[bool, list, str]:
        """
        Get list of installed Chocolatey packages.
        
        Args:
            limit: Maximum number of packages to return
        
        Returns:
            Tuple[bool, list, str]: (success, package_list, error_message)
        """
        if not self.is_chocolatey_installed():
            return False, [], "Chocolatey is not installed"
        
        try:
            return_code, stdout, stderr = run_command_with_timeout(
                f"choco list --local-only --limit-output",
                timeout=30
            )
            
            if return_code == 0:
                packages = []
                lines = stdout.splitlines()
                
                for line in lines[:limit]:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        packages.append({
                            'name': parts[0].strip(),
                            'version': parts[1].strip()
                        })
                
                return True, packages, ""
            else:
                return False, [], f"Failed to get package list: {stderr}"
                
        except Exception as e:
            return False, [], f"Error getting package list: {str(e)}"
    
    def verify_package_installation(self, package_name: str) -> bool:
        """
        Verify that a specific package is installed.
        
        Args:
            package_name: Name of the package to verify
        
        Returns:
            bool: True if package is installed
        """
        if not self.is_chocolatey_installed():
            return False
        
        try:
            return_code, stdout, stderr = run_command_with_timeout(
                f"choco list {package_name} --local-only --exact",
                timeout=15
            )
            
            return return_code == 0 and package_name.lower() in stdout.lower()
            
        except Exception:
            return False
    
    def get_system_requirements_status(self) -> dict:
        """
        Get system requirements status for Chocolatey operations.
        
        Returns:
            dict: System requirements status
        """
        status = {
            'chocolatey_installed': self.is_chocolatey_installed(),
            'admin_privileges': check_admin_privileges(),
            'internet_connectivity': self.check_internet_connectivity()[0],
            'chocolatey_working': False,
            'disk_space_available': True  # Will be implemented if needed
        }
        
        if status['chocolatey_installed']:
            status['chocolatey_working'] = self.test_chocolatey_functionality()[0]
        
        return status


class ChocolateyInstallWorker(BaseWorker):
    """
    Worker class for installing Chocolatey in the background.
    
    This worker handles the Chocolatey installation process without blocking
    the main UI thread.
    """
    
    def __init__(self):
        super().__init__()
        self.chocolatey_manager = ChocolateyManager()
    
    def run(self):
        """Install Chocolatey automatically."""
        try:
            self.emit_progress("Installing Chocolatey package manager...")
            
            # Check if already installed
            if self.chocolatey_manager.is_chocolatey_installed(force_check=True):
                self.emit_progress("✓ Chocolatey is already installed!")
                self.emit_result(True)
                return
            
            # Check admin privileges
            if not check_admin_privileges():
                self.emit_error("Administrator privileges required for Chocolatey installation")
                self.emit_result(False)
                return
            
            # PowerShell command to install Chocolatey
            ps_cmd = (
                'powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; '
                '[System.Net.ServicePointManager]::SecurityProtocol = '
                '[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; '
                'iex ((New-Object System.Net.WebClient).DownloadString('
                '\'https://community.chocolatey.org/install.ps1\'))"'
            )
            
            self.emit_progress("Downloading and installing Chocolatey...")
            self.emit_progress("This may take several minutes...")
            
            return_code, stdout, stderr = run_command_with_timeout(
                ps_cmd,
                timeout=CHOCOLATEY_INSTALL_TIMEOUT
            )
            
            if return_code == 0:
                # Verify installation
                self.emit_progress("Verifying Chocolatey installation...")
                
                if self.chocolatey_manager.is_chocolatey_installed(force_check=True):
                    version = self.chocolatey_manager.get_chocolatey_version()
                    self.emit_progress(f"✓ Chocolatey installed successfully! (Version: {version})")
                    self.emit_result(True)
                else:
                    self.emit_error("Chocolatey installation completed but verification failed")
                    self.emit_result(False)
            else:
                error_msg = stderr if stderr else "Unknown installation error"
                self.emit_error(f"Chocolatey installation failed: {error_msg}")
                self.emit_result(False)
                
        except Exception as e:
            if "timeout" in str(e).lower():
                self.emit_error(f"Chocolatey installation timed out after {CHOCOLATEY_INSTALL_TIMEOUT} seconds")
            else:
                self.emit_error(f"Chocolatey installation error: {str(e)}")
            self.emit_result(False)
        finally:
            self.emit_finished()
    
    def get_installation_requirements(self) -> dict:
        """
        Get installation requirements and status.
        
        Returns:
            dict: Installation requirements status
        """
        return {
            'admin_required': True,
            'admin_available': check_admin_privileges(),
            'internet_required': True,
            'internet_available': self.chocolatey_manager.check_internet_connectivity()[0],
            'estimated_time': "2-5 minutes",
            'disk_space_required': "~100 MB"
        }


class ChocolateyOperations:
    """
    Higher-level Chocolatey operations and utilities.
    
    This class provides convenient methods for common Chocolatey operations
    that combine multiple lower-level functions.
    """
    
    def __init__(self):
        self.manager = ChocolateyManager()
    
    def ensure_chocolatey_available(self) -> Tuple[bool, str]:
        """
        Ensure Chocolatey is available and working.
        
        Returns:
            Tuple[bool, str]: (is_available, status_message)
        """
        if not self.manager.is_chocolatey_installed():
            return False, "Chocolatey is not installed"
        
        is_working, message = self.manager.test_chocolatey_functionality()
        if not is_working:
            return False, f"Chocolatey is installed but not working: {message}"
        
        return True, "Chocolatey is available and working"
    
    def get_comprehensive_status(self) -> dict:
        """
        Get comprehensive Chocolatey and system status.
        
        Returns:
            dict: Comprehensive status information
        """
        status = self.manager.get_system_requirements_status()
        
        # Add additional status information
        if status['chocolatey_installed']:
            status['chocolatey_version'] = self.manager.get_chocolatey_version()
            
            # Get installed package count
            success, packages, error = self.manager.get_installed_packages(limit=1000)
            if success:
                status['installed_packages_count'] = len(packages)
            else:
                status['installed_packages_count'] = 0
        
        return status
    
    def prepare_for_operations(self) -> Tuple[bool, list]:
        """
        Prepare system for Chocolatey operations and return any warnings.
        
        Returns:
            Tuple[bool, list]: (ready, warning_messages)
        """
        warnings = []
        ready = True
        
        # Check Chocolatey installation
        if not self.manager.is_chocolatey_installed():
            ready = False
            warnings.append("Chocolatey is not installed")
        else:
            # Test functionality
            is_working, message = self.manager.test_chocolatey_functionality()
            if not is_working:
                ready = False
                warnings.append(f"Chocolatey is not working: {message}")
        
        # Check admin privileges
        if not check_admin_privileges():
            warnings.append("Running without administrator privileges - some operations may fail")
        
        # Check internet connectivity
        has_internet, message = self.manager.check_internet_connectivity()
        if not has_internet:
            warnings.append(f"Internet connectivity issue: {message}")
        
        return ready, warnings