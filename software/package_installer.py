"""
Package installation management.

This module handles the installation of software packages through Chocolatey,
including batch installations, progress tracking, and verification.
"""

import subprocess
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from core import BaseWorker, run_command_with_timeout, check_admin_privileges
from .chocolatey_manager import ChocolateyManager


class InstallationStatus(Enum):
    """Package installation status enumeration."""
    PENDING = "pending"
    INSTALLING = "installing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PackageInstallResult:
    """Result of a package installation attempt."""
    package_name: str
    status: InstallationStatus
    message: str
    return_code: Optional[int] = None
    install_time: Optional[float] = None
    output: str = ""
    error_output: str = ""


class PackageInstaller:
    """
    Handles package installation operations.
    
    This class provides methods for installing individual packages and
    managing batch installations with proper error handling and verification.
    """
    
    def __init__(self):
        self.chocolatey_manager = ChocolateyManager()
    
    def install_package(
        self, 
        package_name: str, 
        force: bool = True,
        allow_empty_checksums: bool = False,
        timeout: int = 300
    ) -> PackageInstallResult:
        """
        Install a single package.
        
        Args:
            package_name: Name of the package to install
            force: Whether to force installation
            allow_empty_checksums: Whether to allow empty checksums
            timeout: Installation timeout in seconds
        
        Returns:
            PackageInstallResult: Installation result
        """
        import time
        start_time = time.time()
        
        # Build command
        cmd_parts = ["choco", "install", package_name, "-y"]
        
        if force:
            cmd_parts.append("--force")
        
        if allow_empty_checksums:
            cmd_parts.append("--allow-empty-checksums")
        
        cmd_parts.append("--verbose")
        
        cmd = " ".join(cmd_parts)
        
        try:
            return_code, stdout, stderr = run_command_with_timeout(
                cmd, timeout=timeout
            )
            
            install_time = time.time() - start_time
            
            # Analyze installation result
            success = self._analyze_installation_result(
                return_code, stdout, stderr, package_name
            )
            
            if success:
                # Verify installation
                if self.chocolatey_manager.verify_package_installation(package_name):
                    return PackageInstallResult(
                        package_name=package_name,
                        status=InstallationStatus.SUCCESS,
                        message=f"Successfully installed {package_name}",
                        return_code=return_code,
                        install_time=install_time,
                        output=stdout,
                        error_output=stderr
                    )
                else:
                    return PackageInstallResult(
                        package_name=package_name,
                        status=InstallationStatus.FAILED,
                        message=f"Installation completed but verification failed for {package_name}",
                        return_code=return_code,
                        install_time=install_time,
                        output=stdout,
                        error_output=stderr
                    )
            else:
                return PackageInstallResult(
                    package_name=package_name,
                    status=InstallationStatus.FAILED,
                    message=f"Installation failed for {package_name}",
                    return_code=return_code,
                    install_time=install_time,
                    output=stdout,
                    error_output=stderr
                )
                
        except Exception as e:
            install_time = time.time() - start_time
            return PackageInstallResult(
                package_name=package_name,
                status=InstallationStatus.FAILED,
                message=f"Installation error for {package_name}: {str(e)}",
                install_time=install_time,
                error_output=str(e)
            )
    
    def _analyze_installation_result(
        self, 
        return_code: int, 
        stdout: str, 
        stderr: str, 
        package_name: str
    ) -> bool:
        """
        Analyze installation output to determine success/failure.
        
        Args:
            return_code: Process return code
            stdout: Standard output
            stderr: Standard error
            package_name: Package name being installed
        
        Returns:
            bool: True if installation was successful
        """
        # Check return code first
        if return_code != 0:
            return False
        
        stdout_lower = stdout.lower()
        stderr_lower = stderr.lower()
        
        # Success indicators
        success_indicators = [
            'successfully installed',
            'installation was successful',
            f'the install of {package_name.lower()}',
            'chocolatey installed'
        ]
        
        # Failure indicators
        failure_indicators = [
            'failed',
            'error occurred',
            'access denied',
            'not found',
            'unable to',
            'installation failed',
            'could not',
            'permission denied'
        ]
        
        # Check for explicit success
        has_success_indicator = any(
            indicator in stdout_lower for indicator in success_indicators
        )
        
        # Check for explicit failure
        has_failure_indicator = any(
            indicator in stdout_lower or indicator in stderr_lower 
            for indicator in failure_indicators
        )
        
        # If no explicit failure and return code is 0, assume success
        if not has_failure_indicator and return_code == 0:
            return True
        
        # If explicit success indicator, return true
        if has_success_indicator and not has_failure_indicator:
            return True
        
        # Otherwise, consider it failed
        return False
    
    def get_installation_requirements(self, packages: List[str]) -> Dict[str, any]:
        """
        Get installation requirements for a list of packages.
        
        Args:
            packages: List of package names
        
        Returns:
            Dict: Installation requirements and estimates
        """
        return {
            'package_count': len(packages),
            'estimated_time_minutes': len(packages) * 2,  # 2 minutes per package estimate
            'admin_required': True,
            'admin_available': check_admin_privileges(),
            'internet_required': True,
            'chocolatey_available': self.chocolatey_manager.is_chocolatey_installed(),
            'disk_space_estimate_mb': len(packages) * 50  # 50MB per package estimate
        }


class PackageInstallWorker(BaseWorker):
    """
    Worker class for installing packages in the background.
    
    This worker handles batch package installation without blocking the UI,
    providing real-time progress updates and detailed results.
    """
    
    def __init__(self, packages: List[str], install_options: Dict[str, any] = None):
        super().__init__()
        self.packages = packages
        self.install_options = install_options or {}
        self.installer = PackageInstaller()
        self.results: List[PackageInstallResult] = []
        
        # Installation options
        self.force_install = self.install_options.get('force', True)
        self.allow_empty_checksums = self.install_options.get('allow_empty_checksums', False)
        self.package_timeout = self.install_options.get('package_timeout', 300)
        self.continue_on_failure = self.install_options.get('continue_on_failure', True)
    
    def run(self):
        """Install packages without blocking UI."""
        try:
            self.emit_progress("=== CHOCOLATEY PACKAGE INSTALLATION ===")
            self.emit_progress(f"Installing {len(self.packages)} package(s)...")
            self.emit_progress("")
            
            # Pre-installation checks
            if not self._run_pre_installation_checks():
                self.emit_finished()
                return
            
            # Install each package
            for i, package in enumerate(self.packages, 1):
                if self.is_cancelled():
                    self.emit_progress("Installation cancelled by user")
                    break
                
                self.emit_progress(f"[{i}/{len(self.packages)}] Installing {package}...")
                
                # Install the package
                result = self.installer.install_package(
                    package_name=package,
                    force=self.force_install,
                    allow_empty_checksums=self.allow_empty_checksums,
                    timeout=self.package_timeout
                )
                
                self.results.append(result)
                
                # Report result
                if result.status == InstallationStatus.SUCCESS:
                    self.emit_progress(f"✓ {package} installed successfully")
                    if result.install_time:
                        self.emit_progress(f"  Installation time: {result.install_time:.1f} seconds")
                else:
                    self.emit_progress(f"✗ {package} installation failed")
                    self.emit_progress(f"  Error: {result.message}")
                    
                    # Show relevant error details
                    if result.error_output:
                        error_lines = result.error_output.strip().split('\n')
                        for line in error_lines[-3:]:  # Show last 3 lines of error
                            if line.strip():
                                self.emit_progress(f"  {line.strip()}")
                    
                    # Stop on failure if configured
                    if not self.continue_on_failure:
                        self.emit_progress("Stopping installation due to failure")
                        break
                
                self.emit_progress("")  # Add spacing between packages
            
            # Generate installation summary
            self._generate_installation_summary()
            
        except Exception as e:
            self.emit_error(f"Installation process error: {str(e)}")
        finally:
            self.emit_result(self.results)
            self.emit_finished()
    
    def _run_pre_installation_checks(self) -> bool:
        """
        Run pre-installation checks and report status.
        
        Returns:
            bool: True if checks passed and installation can proceed
        """
        self.emit_progress("=== PRE-INSTALLATION CHECKS ===")
        
        # Check Chocolatey
        if not self.installer.chocolatey_manager.is_chocolatey_installed():
            self.emit_error("Chocolatey is not installed")
            return False
        
        # Test Chocolatey functionality
        is_working, message = self.installer.chocolatey_manager.test_chocolatey_functionality()
        if is_working:
            self.emit_progress("✓ Chocolatey is working properly")
        else:
            self.emit_error(f"Chocolatey check failed: {message}")
            return False
        
        # Check admin privileges
        if check_admin_privileges():
            self.emit_progress("✓ Administrator privileges available")
        else:
            self.emit_progress("⚠ Warning: Running without administrator privileges")
            self.emit_progress("  Some installations may fail")
        
        # Check internet connectivity
        has_internet, message = self.installer.chocolatey_manager.check_internet_connectivity()
        if has_internet:
            self.emit_progress("✓ Internet connection available")
        else:
            self.emit_progress(f"⚠ Warning: {message}")
        
        # Check disk space (basic check)
        try:
            import shutil
            free_bytes = shutil.disk_usage('.').free
            free_gb = free_bytes / (1024**3)
            if free_gb > 1:
                self.emit_progress(f"✓ Sufficient disk space ({free_gb:.1f} GB available)")
            else:
                self.emit_progress(f"⚠ Warning: Low disk space ({free_gb:.1f} GB available)")
        except Exception:
            self.emit_progress("⚠ Warning: Could not check disk space")
        
        self.emit_progress("")
        return True
    
    def _generate_installation_summary(self):
        """Generate and emit installation summary."""
        self.emit_progress("=== INSTALLATION SUMMARY ===")
        
        successful = [r for r in self.results if r.status == InstallationStatus.SUCCESS]
        failed = [r for r in self.results if r.status == InstallationStatus.FAILED]
        
        self.emit_progress(f"Total packages: {len(self.packages)}")
        self.emit_progress(f"Successfully installed: {len(successful)}")
        self.emit_progress(f"Failed: {len(failed)}")
        
        if successful:
            self.emit_progress("")
            self.emit_progress("✓ Successfully installed:")
            for result in successful:
                time_str = f" ({result.install_time:.1f}s)" if result.install_time else ""
                self.emit_progress(f"  • {result.package_name}{time_str}")
        
        if failed:
            self.emit_progress("")
            self.emit_progress("✗ Failed to install:")
            for result in failed:
                self.emit_progress(f"  • {result.package_name}: {result.message}")
        
        self.emit_progress("")
        self.emit_progress("=== INSTALLATION PROCESS COMPLETED ===")
        
        # Add helpful notes
        if failed:
            self.emit_progress("")
            self.emit_progress("Troubleshooting tips for failed installations:")
            self.emit_progress("• Ensure you're running as Administrator")
            self.emit_progress("• Check your internet connection")
            self.emit_progress("• Try installing failed packages individually")
            self.emit_progress("• Some packages may require manual confirmation")
        
        if len(successful) > 0:
            self.emit_progress("")
            self.emit_progress("Note: Some installations may require a system restart to take effect.")
    
    def get_results(self) -> List[PackageInstallResult]:
        """Get installation results."""
        return self.results.copy()
    
    def get_success_count(self) -> int:
        """Get number of successful installations."""
        return len([r for r in self.results if r.status == InstallationStatus.SUCCESS])
    
    def get_failure_count(self) -> int:
        """Get number of failed installations."""
        return len([r for r in self.results if r.status == InstallationStatus.FAILED])
    
    def get_total_install_time(self) -> float:
        """Get total installation time in seconds."""
        return sum(r.install_time or 0 for r in self.results)