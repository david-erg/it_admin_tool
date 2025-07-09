"""
Enhanced Chocolatey package manager integration with comprehensive error reporting.

This module handles Chocolatey installation, verification, and basic operations
with detailed logging and error capture.
"""

import subprocess
import platform
from typing import Tuple, Optional

from core import (
    BaseWorker, run_command_with_timeout, check_admin_privileges,
    CHOCOLATEY_INSTALL_TIMEOUT
)


class EnhancedChocolateyManager:
    """
    Enhanced Chocolatey package manager operations with detailed error reporting.
    
    This class provides methods for checking Chocolatey installation status,
    installing Chocolatey, and performing basic Chocolatey operations with
    comprehensive error logging.
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
        
        # Test 2: Simple list command
        try:
            return_code, stdout, stderr = run_command_with_timeout(
                "choco list chocolatey --exact --local-only --limit-output",
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
                # Execution policy check is optional
                pass
        
        # Test 4: Test search functionality
        try:
            return_code, stdout, stderr = run_command_with_timeout(
                "choco search chocolatey --exact --limit-output",
                timeout=45
            )
            
            if return_code != 0:
                error_details = stderr.strip() if stderr.strip() else "No error message"
                return False, f"Search command failed (code {return_code}): {error_details}"
                
        except subprocess.TimeoutExpired:
            return False, "Search command timed out after 45 seconds - check internet connection"
        except Exception as e:
            return False, f"Search command exception: {str(e)}"
        
        # All tests passed
        version = self._chocolatey_version or "Unknown"
        return True, f"Chocolatey is working properly (version: {version})"
    
    def check_internet_connectivity(self) -> Tuple[bool, str]:
        """
        Check internet connectivity for Chocolatey operations with enhanced reporting.
        
        Returns:
            Tuple[bool, str]: (has_connectivity, detailed_status_message)
        """
        test_urls = [
            ("chocolatey.org", "Primary Chocolatey repository"),
            ("packages.chocolatey.org", "Chocolatey package repository"),
            ("google.com", "General internet connectivity")
        ]
        
        for url, description in test_urls:
            try:
                return_code, stdout, stderr = run_command_with_timeout(
                    f"ping {url} -n 1",
                    timeout=10
                )
                
                if return_code == 0:
                    return True, f"Internet connection available ({description} reachable)"
                    
            except Exception:
                continue
        
        return False, "Internet connection may be limited - could not reach Chocolatey servers"
    
    def get_installed_packages(self, limit: int = 100) -> Tuple[bool, list, str]:
        """
        Get list of installed Chocolatey packages with enhanced error reporting.
        
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
            return_code, stdout, stderr = run_command_with_timeout(
                f"choco list {package_name} --local-only --exact --limit-output",
                timeout=20
            )
            
            if return_code == 0:
                # Check if the package name appears in the output
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
            dict: Detailed system requirements status
        """
        status = {
            'chocolatey_installed': self.is_chocolatey_installed(),
            'admin_privileges': check_admin_privileges(),
            'internet_connectivity': False,
            'chocolatey_working': False,
            'platform': platform.system(),
            'platform_supported': platform.system() == "Windows",
            'powershell_available': False,
            'execution_policy': "Unknown"
        }
        
        # Test internet connectivity
        status['internet_connectivity'] = self.check_internet_connectivity()[0]
        
        # Test Chocolatey functionality if installed
        if status['chocolatey_installed']:
            status['chocolatey_working'] = self.test_chocolatey_functionality()[0]
        
        # Check PowerShell availability (Windows only)
        if platform.system() == "Windows":
            try:
                return_code, stdout, stderr = run_command_with_timeout(
                    "powershell -Command \"$PSVersionTable.PSVersion.Major\"",
                    timeout=10
                )
                
                if return_code == 0:
                    status['powershell_available'] = True
                    ps_version = stdout.strip()
                    status['powershell_version'] = ps_version
                    
                    # Check execution policy
                    return_code, stdout, stderr = run_command_with_timeout(
                        "powershell -Command \"Get-ExecutionPolicy\"",
                        timeout=10
                    )
                    
                    if return_code == 0:
                        status['execution_policy'] = stdout.strip()
                        
            except Exception:
                pass
        
        return status
    
    def get_detailed_diagnostics(self) -> dict:
        """
        Get detailed diagnostic information for troubleshooting.
        
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
                ("choco list --local-only --limit-output", "Local package list"),
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
        import os
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
            has_internet, internet_msg = self.chocolatey_manager.check_internet_connectivity()
            if not has_internet:
                self.emit_progress(f"⚠ Internet connectivity warning: {internet_msg}")
                self.emit_progress("Installation may fail without internet access")
            else:
                self.emit_progress(f"✓ Internet connectivity confirmed: {internet_msg}")
            
            # PowerShell command to install Chocolatey with enhanced error handling
            ps_cmd = (
                'powershell -ExecutionPolicy Bypass -NoProfile -Command "'
                'try { '
                '    Set-ExecutionPolicy Bypass -Scope Process -Force; '
                '    [System.Net.ServicePointManager]::SecurityProtocol = '
                '    [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; '
                '    iex ((New-Object System.Net.WebClient).DownloadString('
                '    \'https://community.chocolatey.org/install.ps1\')); '
                '    Write-Host \'Chocolatey installation completed successfully\' '
                '} catch { '
                '    Write-Error $_.Exception.Message; '
                '    exit 1 '
                '}"'
            )
            
            self.emit_progress("Downloading and installing Chocolatey...")
            self.emit_progress("This may take several minutes depending on your internet connection...")
            
            return_code, stdout, stderr = run_command_with_timeout(
                ps_cmd,
                timeout=CHOCOLATEY_INSTALL_TIMEOUT
            )
            
            # Log detailed output for debugging
            self.emit_progress(f"Installation command return code: {return_code}")
            if stdout.strip():
                self.emit_progress(f"Installation output: {stdout.strip()}")
            if stderr.strip():
                self.emit_progress(f"Installation errors: {stderr.strip()}")
            
            if return_code == 0:
                # Verify installation
                self.emit_progress("Verifying Chocolatey installation...")
                
                # Force refresh the installation check
                if self.chocolatey_manager.is_chocolatey_installed(force_check=True):
                    version = self.chocolatey_manager.get_chocolatey_version()
                    self.emit_progress(f"✓ Chocolatey installed successfully! (Version: {version})")
                    
                    # Test functionality
                    self.emit_progress("Testing Chocolatey functionality...")
                    is_working, test_msg = self.chocolatey_manager.test_chocolatey_functionality()
                    
                    if is_working:
                        self.emit_progress(f"✓ Chocolatey functionality test passed: {test_msg}")
                        self.emit_result(True)
                    else:
                        self.emit_progress(f"⚠ Chocolatey installed but functionality test failed: {test_msg}")
                        self.emit_progress("You may need to restart your command prompt or computer")
                        self.emit_result(True)  # Still consider successful since it's installed
                else:
                    self.emit_error("Chocolatey installation completed but verification failed")
                    self.emit_progress("Try running 'refreshenv' in a new command prompt")
                    self.emit_result(False)
            else:
                error_msg = stderr.strip() if stderr.strip() else "Unknown installation error"
                self.emit_error(f"Chocolatey installation failed (code {return_code}): {error_msg}")
                
                # Provide troubleshooting suggestions
                self.emit_progress("\nTroubleshooting suggestions:")
                self.emit_progress("1. Ensure you're running as Administrator")
                self.emit_progress("2. Check your internet connection")
                self.emit_progress("3. Try running: Set-ExecutionPolicy Bypass -Scope Process -Force")
                self.emit_progress("4. Temporarily disable antivirus software")
                
                self.emit_result(False)
                
        except subprocess.TimeoutExpired:
            self.emit_error(f"Chocolatey installation timed out after {CHOCOLATEY_INSTALL_TIMEOUT} seconds")
            self.emit_progress("This usually indicates a slow internet connection or system")
            self.emit_progress("Try increasing the timeout or install manually")
            self.emit_result(False)
        except Exception as e:
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
        status = self.chocolatey_manager.get_system_requirements_status()
        
        return {
            'admin_required': True,
            'admin_available': status['admin_privileges'],
            'internet_required': True,
            'internet_available': status['internet_connectivity'],
            'platform_supported': status['platform_supported'],
            'powershell_available': status['powershell_available'],
            'estimated_time': "2-5 minutes",
            'disk_space_required': "~100 MB",
            'execution_policy': status.get('execution_policy', 'Unknown')
        }


class ChocolateyOperations:
    """
    Higher-level Chocolatey operations and utilities with enhanced error reporting.
    
    This class provides convenient methods for common Chocolatey operations
    that combine multiple lower-level functions.
    """
    
    def __init__(self):
        self.manager = EnhancedChocolateyManager()
    
    def ensure_chocolatey_available(self) -> Tuple[bool, str]:
        """
        Ensure Chocolatey is available and working with detailed status.
        
        Returns:
            Tuple[bool, str]: (is_available, detailed_status_message)
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
                status['package_list_error'] = error
        
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
    
    def get_troubleshooting_info(self) -> dict:
        """
        Get comprehensive troubleshooting information.
        
        Returns:
            dict: Detailed troubleshooting information
        """
        return self.manager.get_detailed_diagnostics()