"""
Enhanced Chocolatey package manager integration with comprehensive error reporting.

This module handles Chocolatey installation, verification, and basic operations
with detailed logging and error capture.

CRITICAL: This version is compatible with Chocolatey 2.4.3+ where --local-only was removed
"""

import subprocess
import platform
import os
from typing import Tuple, Optional, List, Dict

from core import (
    BaseWorker, run_command_with_timeout, check_admin_privileges,
    CHOCOLATEY_INSTALL_TIMEOUT
)


class ChocolateyManager:
    """
    Basic Chocolatey package manager operations.
    
    This class provides basic methods for checking Chocolatey installation status,
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
            # Test basic version check
            return_code, stdout, stderr = run_command_with_timeout(
                "choco --version",
                timeout=15
            )
            
            if return_code != 0:
                return False, f"Version check failed: {stderr.strip()}"
            
            if not stdout.strip():
                return False, "Version check returned empty output"
            
            # Test simple list command - FIXED: removed --local-only completely
            # In Chocolatey 2.4.3+, choco list defaults to local packages
            return_code, stdout, stderr = run_command_with_timeout(
                "choco list chocolatey --exact --limit-output",
                timeout=30
            )
            
            if return_code != 0:
                return False, f"List command failed: {stderr.strip()}"
            
            # All tests passed
            version = self._chocolatey_version or "Unknown"
            return True, f"Chocolatey is working properly (version: {version})"
            
        except subprocess.TimeoutExpired:
            return False, "Chocolatey commands timed out"
        except Exception as e:
            return False, f"Chocolatey test failed: {str(e)}"
    
    def check_internet_connectivity(self) -> Tuple[bool, str]:
        """
        Check internet connectivity for Chocolatey operations.
        
        Returns:
            Tuple[bool, str]: (has_connectivity, status_message)
        """
        test_hosts = ["chocolatey.org", "packages.chocolatey.org", "google.com"]
        
        for host in test_hosts:
            try:
                return_code, stdout, stderr = run_command_with_timeout(
                    f"ping {host} -n 1",
                    timeout=10
                )
                
                if return_code == 0:
                    return True, f"Internet connection available ({host} reachable)"
                    
            except Exception:
                continue
        
        return False, "Internet connection may be limited - could not reach Chocolatey servers"
    
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
            # FIXED: In Chocolatey 2.4.3+, choco list defaults to local packages
            return_code, stdout, stderr = run_command_with_timeout(
                f"choco list --limit-output",
                timeout=45
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
                error_details = stderr.strip() if stderr.strip() else "No error details"
                return False, [], f"Failed to get package list (code {return_code}): {error_details}"
                
        except subprocess.TimeoutExpired:
            return False, [], "Package list command timed out after 45 seconds"
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
            # FIXED: removed --local-only, choco list <package> defaults to local
            return_code, stdout, stderr = run_command_with_timeout(
                f"choco list {package_name} --exact --limit-output",
                timeout=20
            )
            
            if return_code == 0:
                lines = stdout.splitlines()
                for line in lines:
                    if line.strip().lower().startswith(package_name.lower() + "|"):
                        return True
            
            return False
            
        except Exception:
            return False
    
    def get_system_requirements_status(self) -> dict:
        """
        Get comprehensive system requirements status for Chocolatey operations.
        
        Returns:
            dict: System requirements status
        """
        status = {
            "platform": platform.system(),
            "platform_supported": platform.system() == "Windows",
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "chocolatey_installed": self.is_chocolatey_installed(),
            "chocolatey_version": self.get_chocolatey_version(),
            "admin_privileges": self._check_admin_privileges(),
            "powershell_available": self._check_powershell_available(),
            "execution_policy": self._get_execution_policy()
        }
        
        return status
    
    def _check_admin_privileges(self) -> bool:
        """Check if running with admin privileges"""
        try:
            if platform.system() == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception:
            return False
    
    def _check_powershell_available(self) -> bool:
        """Check if PowerShell is available"""
        try:
            return_code, _, _ = run_command_with_timeout(
                "powershell -Command \"$PSVersionTable.PSVersion.Major\"",
                timeout=10
            )
            return return_code == 0
        except Exception:
            return False
    
    def _get_execution_policy(self) -> str:
        """Get PowerShell execution policy"""
        try:
            return_code, stdout, _ = run_command_with_timeout(
                "powershell -Command \"Get-ExecutionPolicy\"",
                timeout=10
            )
            if return_code == 0:
                return stdout.strip()
            return "Unknown"
        except Exception:
            return "Unknown"
    
    def get_diagnostics(self) -> dict:
        """
        Get comprehensive diagnostic information.
        
        Returns:
            dict: Comprehensive diagnostic information
        """
        diagnostics = {
            'timestamp': subprocess.run(
                "echo %date% %time%" if platform.system() == "Windows" else "date",
                shell=True, capture_output=True, text=True
            ).stdout.strip(),
            'system_requirements': self.get_system_requirements_status(),
            'chocolatey_tests': {},
            'environment_variables': {},
            'path_analysis': {}
        }
        
        # Test individual Chocolatey commands
        if self.is_chocolatey_installed():
            test_commands = [
                ("choco --version", "Version check"),
                ("choco list --limit-output", "Local package list"),  # FIXED
                ("choco search chocolatey --exact --limit-output", "Search functionality"),
                ("choco config list", "Configuration check")
            ]
            
            for cmd, description in test_commands:
                try:
                    return_code, stdout, stderr = run_command_with_timeout(cmd, timeout=30)
                    diagnostics['chocolatey_tests'][description] = {
                        'command': cmd,
                        'return_code': return_code,
                        'stdout_length': len(stdout),
                        'stderr_length': len(stderr),
                        'success': return_code == 0,
                        'error': stderr.strip() if stderr.strip() else None
                    }
                except Exception as e:
                    diagnostics['chocolatey_tests'][description] = {
                        'command': cmd,
                        'exception': str(e),
                        'success': False
                    }
        
        # Check relevant environment variables
        env_vars_to_check = ['PATH', 'PATHEXT', 'ChocolateyInstall', 'PSExecutionPolicyPreference']
        for var in env_vars_to_check:
            diagnostics['environment_variables'][var] = os.environ.get(var, "Not set")
        
        # Analyze PATH for Chocolatey
        path = os.environ.get('PATH', '')
        path_entries = path.split(os.pathsep)
        chocolatey_paths = [entry for entry in path_entries if 'chocolatey' in entry.lower()]
        diagnostics['path_analysis'] = {
            'total_path_entries': len(path_entries),
            'chocolatey_paths': chocolatey_paths,
            'chocolatey_in_path': len(chocolatey_paths) > 0
        }
        
        return diagnostics


class EnhancedChocolateyManager(ChocolateyManager):
    """
    Enhanced Chocolatey package manager operations with detailed error reporting.
    
    This class provides methods for checking Chocolatey installation status,
    installing Chocolatey, and performing basic Chocolatey operations with
    comprehensive error logging.
    """
    
    def __init__(self):
        super().__init__()
    
    def test_chocolatey_functionality(self) -> Tuple[bool, str]:
        """
        Test basic Chocolatey functionality with enhanced error reporting.
        
        Returns:
            Tuple[bool, str]: (is_working, detailed_status_message)
        """
        if not self.is_chocolatey_installed():
            return False, "Chocolatey is not installed"
        
        # Test 1: Basic version check
        try:
            return_code, stdout, stderr = run_command_with_timeout(
                "choco --version", 
                timeout=15
            )
            
            if return_code != 0:
                return False, f"Version check failed (code {return_code}): {stderr.strip()}"
            
            if not stdout.strip():
                return False, "Version check returned empty output"
                
        except subprocess.TimeoutExpired:
            return False, "Version check timed out after 15 seconds"
        except Exception as e:
            return False, f"Version check exception: {str(e)}"
        
        # Test 2: Simple list command - FIXED: removed --local-only completely
        try:
            return_code, stdout, stderr = run_command_with_timeout(
                "choco list chocolatey --exact --limit-output",
                timeout=30
            )
            
            if return_code != 0:
                error_details = stderr.strip() if stderr.strip() else "No error message"
                return False, f"List command failed (code {return_code}): {error_details}"
                
        except subprocess.TimeoutExpired:
            return False, "List command timed out after 30 seconds"
        except Exception as e:
            return False, f"List command exception: {str(e)}"
        
        # Test 3: Check execution policy (Windows specific)
        if platform.system() == "Windows":
            try:
                return_code, stdout, stderr = run_command_with_timeout(
                    "powershell -Command \"Get-ExecutionPolicy\"",
                    timeout=10
                )
                
                if return_code == 0:
                    policy = stdout.strip()
                    if policy in ["Restricted", "Undefined"]:
                        return False, f"PowerShell execution policy is '{policy}' - this may prevent Chocolatey from working properly"
                        
            except Exception:
                pass  # Execution policy check is optional
        
        # All tests passed
        version = self._chocolatey_version or "Unknown"
        return True, f"Chocolatey is working properly (version: {version})"
    
    def install_chocolatey(self, force: bool = False) -> Tuple[bool, str]:
        """
        Install Chocolatey package manager.
        
        Args:
            force: Force installation even if already installed
        
        Returns:
            Tuple[bool, str]: (success, status_message)
        """
        if self.is_chocolatey_installed() and not force:
            return True, "Chocolatey is already installed"
        
        if not check_admin_privileges():
            return False, "Administrator privileges required for Chocolatey installation"
        
        try:
            # PowerShell command to install Chocolatey
            install_command = (
                "powershell -NoProfile -InputFormat None -ExecutionPolicy Bypass "
                "-Command \"[System.Net.ServicePointManager]::SecurityProtocol = 3072; "
                "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))\""
            )
            
            return_code, stdout, stderr = run_command_with_timeout(
                install_command,
                timeout=CHOCOLATEY_INSTALL_TIMEOUT
            )
            
            if return_code == 0:
                # Verify installation
                if self.is_chocolatey_installed(force_check=True):
                    version = self.get_chocolatey_version()
                    return True, f"Chocolatey successfully installed (version: {version})"
                else:
                    return False, "Installation completed but Chocolatey verification failed"
            else:
                error_output = stderr.strip() if stderr.strip() else "No error details available"
                return False, f"Installation failed (code {return_code}): {error_output}"
                
        except subprocess.TimeoutExpired:
            return False, f"Installation timed out after {CHOCOLATEY_INSTALL_TIMEOUT} seconds"
        except Exception as e:
            return False, f"Installation error: {str(e)}"
    
    def update_chocolatey(self) -> Tuple[bool, str]:
        """
        Update Chocolatey to the latest version.
        
        Returns:
            Tuple[bool, str]: (success, status_message)
        """
        if not self.is_chocolatey_installed():
            return False, "Chocolatey is not installed"
        
        try:
            return_code, stdout, stderr = run_command_with_timeout(
                "choco upgrade chocolatey -y",
                timeout=300
            )
            
            if return_code == 0:
                # Update version info
                self.is_chocolatey_installed(force_check=True)
                version = self.get_chocolatey_version()
                return True, f"Chocolatey updated successfully (version: {version})"
            else:
                error_output = stderr.strip() if stderr.strip() else "No error details available"
                return False, f"Update failed (code {return_code}): {error_output}"
                
        except subprocess.TimeoutExpired:
            return False, "Update timed out after 300 seconds"
        except Exception as e:
            return False, f"Update error: {str(e)}"


class ChocolateyInstallWorker(BaseWorker):
    """
    Enhanced worker class for installing Chocolatey in the background.
    
    This worker handles the Chocolatey installation process without blocking
    the main UI thread, with comprehensive error reporting.
    """
    
    def __init__(self):
        super().__init__()
        self.chocolatey_manager = EnhancedChocolateyManager()
    
    def run(self):
        """Install Chocolatey automatically with enhanced error reporting."""
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
            
            # Check system requirements
            self.emit_progress("Checking system requirements...")
            status = self.chocolatey_manager.get_system_requirements_status()
            
            if not status['platform_supported']:
                self.emit_error(f"Platform '{status['platform']}' is not supported for Chocolatey")
                self.emit_result(False)
                return
            
            if not status['powershell_available']:
                self.emit_error("PowerShell is required but not available")
                self.emit_result(False)
                return
            
            # Check execution policy
            if status.get('execution_policy') in ['Restricted', 'Undefined']:
                self.emit_progress(f"⚠ PowerShell execution policy is '{status['execution_policy']}' - attempting to bypass...")
            
            # Check internet connectivity
            self.emit_progress("Checking internet connectivity...")
            has_internet, internet_msg = self.chocolatey_manager.check_internet_connectivity()
            if not has_internet:
                self.emit_error(f"Internet connection required: {internet_msg}")
                self.emit_result(False)
                return
            
            self.emit_progress("✓ All requirements met, starting installation...")
            
            # Install Chocolatey
            success, message = self.chocolatey_manager.install_chocolatey()
            
            if success:
                self.emit_progress(f"✓ {message}")
                
                # Test functionality after installation
                self.emit_progress("Testing Chocolatey functionality...")
                is_working, test_msg = self.chocolatey_manager.test_chocolatey_functionality()
                
                if is_working:
                    self.emit_progress(f"✓ {test_msg}")
                    self.emit_result(True)
                else:
                    self.emit_error(f"Installation completed but functionality test failed: {test_msg}")
                    self.emit_result(False)
            else:
                self.emit_error(f"Installation failed: {message}")
                self.emit_result(False)
                
        except Exception as e:
            self.emit_error(f"Unexpected error during installation: {str(e)}")
            self.emit_result(False)
    
    def emit_progress(self, message: str):
        """Emit progress signal with message"""
        self.signals.progress.emit(message)
    
    def emit_result(self, success: bool):
        """Emit result signal"""
        self.signals.result.emit(success)
    
    def emit_error(self, message: str):
        """Emit error signal with message"""
        self.signals.error.emit(message)