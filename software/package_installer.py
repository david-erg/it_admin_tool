"""
Enhanced Package installation management with comprehensive error reporting and logging.

This module handles the installation of software packages through Chocolatey,
including batch installations, progress tracking, verification, and detailed
error reporting.
"""

import subprocess
import time
import logging
import shutil
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import core utilities - handle missing imports gracefully
try:
    from core import BaseWorker, run_command_with_timeout, check_admin_privileges
except ImportError:
    # Fallback implementations if core module isn't available
    class BaseWorker:
        def __init__(self):
            self.should_stop_flag = False
            
        def should_stop(self):
            return self.should_stop_flag
    
    def run_command_with_timeout(cmd: str, timeout: int = 300) -> Tuple[int, str, str]:
        """Fallback command runner with timeout."""
        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            raise
        except Exception as e:
            return 1, "", str(e)
    
    def check_admin_privileges() -> bool:
        """Check if running with admin privileges."""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False


class InstallationStatus(Enum):
    """Package installation status enumeration."""
    PENDING = "pending"
    INSTALLING = "installing"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PackageInstallResult:
    """Enhanced result of a package installation attempt."""
    package_name: str
    status: InstallationStatus
    message: str
    return_code: Optional[int] = None
    install_time: Optional[float] = None
    output: str = ""
    error_output: str = ""
    command_used: str = ""
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'package_name': self.package_name,
            'status': self.status.value,
            'message': self.message,
            'return_code': self.return_code,
            'install_time': self.install_time,
            'success': self.status == InstallationStatus.SUCCESS,
            'warnings_count': len(self.warnings)
        }


class PackageInstaller:
    """
    Basic package installer for Chocolatey packages.
    
    This class provides basic methods for installing individual packages and
    managing installations with standard error handling.
    """
    
    def __init__(self):
        # Import here to avoid circular imports
        self.chocolatey_manager = None
        try:
            from software.chocolatey_manager import ChocolateyManager
            self.chocolatey_manager = ChocolateyManager()
        except ImportError:
            # Chocolatey manager not available - we'll check manually
            pass
    
    def is_chocolatey_available(self) -> bool:
        """Check if Chocolatey is available on the system."""
        if self.chocolatey_manager:
            return self.chocolatey_manager.is_chocolatey_installed()
        
        # Manual check if manager not available
        return shutil.which("choco") is not None
    
    def install_package(
        self, 
        package_name: str, 
        force: bool = True,
        timeout: int = 300
    ) -> PackageInstallResult:
        """
        Install a single package.
        
        Args:
            package_name: Name of the package to install
            force: Whether to force installation
            timeout: Installation timeout in seconds
        
        Returns:
            PackageInstallResult: Installation result
        """
        if not package_name or not package_name.strip():
            return PackageInstallResult(
                package_name=package_name,
                status=InstallationStatus.FAILED,
                message="Package name cannot be empty"
            )
        
        package_name = package_name.strip()
        start_time = time.time()
        
        # Check if Chocolatey is available
        if not self.is_chocolatey_available():
            return PackageInstallResult(
                package_name=package_name,
                status=InstallationStatus.FAILED,
                message="Chocolatey is not installed or not available in PATH"
            )
        
        # Build command
        cmd_parts = ["choco", "install", package_name, "-y"]
        
        if force:
            cmd_parts.append("--force")
        
        cmd = " ".join(cmd_parts)
        
        try:
            return_code, stdout, stderr = run_command_with_timeout(
                cmd, timeout=timeout
            )
            
            install_time = time.time() - start_time
            
            # Simple success check
            success = return_code == 0 and "successfully installed" in stdout.lower()
            
            if success:
                return PackageInstallResult(
                    package_name=package_name,
                    status=InstallationStatus.SUCCESS,
                    message=f"Successfully installed {package_name}",
                    return_code=return_code,
                    install_time=install_time,
                    output=stdout,
                    error_output=stderr,
                    command_used=cmd
                )
            else:
                error_msg = stderr.strip() if stderr.strip() else "Installation failed"
                return PackageInstallResult(
                    package_name=package_name,
                    status=InstallationStatus.FAILED,
                    message=f"Installation failed: {error_msg}",
                    return_code=return_code,
                    install_time=install_time,
                    output=stdout,
                    error_output=stderr,
                    command_used=cmd
                )
                
        except subprocess.TimeoutExpired:
            install_time = time.time() - start_time
            return PackageInstallResult(
                package_name=package_name,
                status=InstallationStatus.FAILED,
                message=f"Installation timed out after {timeout} seconds",
                install_time=install_time,
                error_output="Installation timeout",
                command_used=cmd
            )
        except Exception as e:
            install_time = time.time() - start_time
            return PackageInstallResult(
                package_name=package_name,
                status=InstallationStatus.FAILED,
                message=f"Installation error: {str(e)}",
                install_time=install_time,
                error_output=str(e),
                command_used=cmd
            )
    
    def get_installation_requirements(self, packages: List[str]) -> Dict[str, Any]:
        """
        Get installation requirements for a list of packages.
        
        Args:
            packages: List of package names
        
        Returns:
            Dict: Installation requirements and estimates
        """
        return {
            'package_count': len(packages),
            'estimated_time_minutes': len(packages) * 3,
            'admin_required': True,
            'admin_available': check_admin_privileges(),
            'internet_required': True,
            'chocolatey_available': self.is_chocolatey_available(),
            'disk_space_estimate_mb': len(packages) * 75
        }


class EnhancedPackageInstaller(PackageInstaller):
    """
    Enhanced package installer with comprehensive error reporting and logging.
    
    This class provides methods for installing individual packages and
    managing batch installations with detailed error handling and verification.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)
        
        # Try to use enhanced Chocolatey manager if available
        try:
            from software.chocolatey_manager import EnhancedChocolateyManager
            self.chocolatey_manager = EnhancedChocolateyManager()
        except ImportError:
            # Keep the basic manager or None
            pass
    
    def _log(self, level: str, message: str) -> None:
        """Log message if logger is available."""
        if self.logger and hasattr(self.logger, level):
            getattr(self.logger, level)(message)
    
    def install_package(
        self, 
        package_name: str, 
        force: bool = True,
        allow_empty_checksums: bool = False,
        timeout: int = 300,
        additional_args: Optional[List[str]] = None
    ) -> PackageInstallResult:
        """
        Install a single package with enhanced error reporting.
        
        Args:
            package_name: Name of the package to install
            force: Whether to force installation
            allow_empty_checksums: Whether to allow empty checksums
            timeout: Installation timeout in seconds
            additional_args: Additional command line arguments
        
        Returns:
            PackageInstallResult: Detailed installation result
        """
        if not package_name or not package_name.strip():
            return PackageInstallResult(
                package_name=package_name,
                status=InstallationStatus.FAILED,
                message="Package name cannot be empty"
            )
        
        package_name = package_name.strip()
        start_time = time.time()
        self._log("info", f"Starting installation of {package_name}")
        
        # Check prerequisites
        if not self.is_chocolatey_available():
            self._log("error", "Chocolatey is not available")
            return PackageInstallResult(
                package_name=package_name,
                status=InstallationStatus.FAILED,
                message="Chocolatey is not installed or not available in PATH"
            )
        
        # Build enhanced command
        cmd_parts = ["choco", "install", package_name, "-y"]
        
        if force:
            cmd_parts.append("--force")
        
        if allow_empty_checksums:
            cmd_parts.append("--allow-empty-checksums")
        
        if additional_args:
            cmd_parts.extend(additional_args)
        
        cmd = " ".join(cmd_parts)
        self._log("debug", f"Installation command: {cmd}")
        
        try:
            return_code, stdout, stderr = run_command_with_timeout(
                cmd, timeout=timeout
            )
            
            install_time = time.time() - start_time
            self._log("debug", f"Installation completed in {install_time:.1f} seconds")
            
            # Enhanced result analysis
            success, analysis_msg, warnings = self._analyze_installation_result(
                return_code, stdout, stderr, package_name
            )
            
            if success:
                self._log("info", f"Successfully installed {package_name}")
                return PackageInstallResult(
                    package_name=package_name,
                    status=InstallationStatus.SUCCESS,
                    message=analysis_msg,
                    return_code=return_code,
                    install_time=install_time,
                    output=stdout,
                    error_output=stderr,
                    command_used=cmd,
                    warnings=warnings
                )
            else:
                self._log("error", f"Failed to install {package_name}: {analysis_msg}")
                return PackageInstallResult(
                    package_name=package_name,
                    status=InstallationStatus.FAILED,
                    message=f"Installation failed: {analysis_msg}",
                    return_code=return_code,
                    install_time=install_time,
                    output=stdout,
                    error_output=stderr,
                    command_used=cmd,
                    warnings=warnings
                )
                
        except subprocess.TimeoutExpired:
            install_time = time.time() - start_time
            self._log("error", f"Installation timed out for {package_name} after {timeout} seconds")
            return PackageInstallResult(
                package_name=package_name,
                status=InstallationStatus.FAILED,
                message=f"Installation timed out after {timeout} seconds",
                install_time=install_time,
                error_output="Installation timeout",
                command_used=cmd,
                warnings=["Consider increasing timeout for large packages"]
            )
        except Exception as e:
            install_time = time.time() - start_time
            self._log("error", f"Installation exception for {package_name}: {str(e)}")
            return PackageInstallResult(
                package_name=package_name,
                status=InstallationStatus.FAILED,
                message=f"Installation error: {str(e)}",
                install_time=install_time,
                error_output=str(e),
                command_used=cmd
            )
    
    def _analyze_installation_result(
        self, 
        return_code: int, 
        stdout: str, 
        stderr: str, 
        package_name: str
    ) -> Tuple[bool, str, List[str]]:
        """
        Enhanced analysis of installation output to determine success/failure.
        
        Args:
            return_code: Process return code
            stdout: Standard output
            stderr: Standard error
            package_name: Package name being installed
        
        Returns:
            Tuple[bool, str, List[str]]: (is_successful, message, warnings)
        """
        warnings = []
        stdout_lower = stdout.lower()
        stderr_lower = stderr.lower()
        
        # Check return code first
        if return_code != 0:
            error_analysis = self._analyze_error_code(return_code, stderr)
            return False, error_analysis, warnings
        
        # Enhanced success indicators
        success_indicators = [
            'successfully installed',
            'installation was successful',
            f'the install of {package_name.lower()}',
            'chocolatey installed',
            f'{package_name.lower()} has been installed',
            'package files install completed'
        ]
        
        # Enhanced failure indicators
        failure_indicators = [
            'failed',
            'error occurred',
            'access denied',
            'not found',
            'unable to',
            'installation failed',
            'package was not found',
            'chocolatey failed',
            'execution failed'
        ]
        
        # Warning indicators
        warning_indicators = [
            'warning',
            'deprecated',
            'outdated',
            'checksum validation',
            'unable to verify'
        ]
        
        # Check for success
        has_success = any(indicator in stdout_lower for indicator in success_indicators)
        has_failure = any(indicator in stdout_lower or indicator in stderr_lower 
                         for indicator in failure_indicators)
        
        # Check for warnings
        for indicator in warning_indicators:
            if indicator in stdout_lower or indicator in stderr_lower:
                warnings.append(f"Installation warning: {indicator} detected")
        
        # Determine result
        if has_success and not has_failure:
            return True, f"Successfully installed {package_name}", warnings
        elif has_failure:
            # Extract specific error from stderr
            if stderr.strip():
                error_lines = [line.strip() for line in stderr.split('\n') if line.strip()]
                if error_lines:
                    return False, error_lines[-1], warnings
            return False, "Installation failed (see output for details)", warnings
        else:
            # Ambiguous result - check return code
            if return_code == 0:
                return True, f"Package {package_name} processed (check output for details)", warnings
            else:
                return False, f"Installation failed with return code {return_code}", warnings
    
    def _analyze_error_code(self, return_code: int, stderr: str) -> str:
        """
        Analyze Chocolatey return codes and provide human-readable error messages.
        
        Args:
            return_code: The return code from chocolatey
            stderr: Standard error output
            
        Returns:
            str: Human-readable error message
        """
        error_codes = {
            1: "General error or unspecified failure",
            2: "File not found or package not found",
            3: "Invalid arguments or configuration error",
            4: "Access denied or permission error",
            5: "Network error or download failure",
            48: "Package installation cancelled by user",
            1641: "Installation successful but restart required",
            3010: "Installation successful but restart required"
        }
        
        base_message = error_codes.get(return_code, f"Unknown error (code {return_code})")
        
        if stderr.strip():
            error_lines = [line.strip() for line in stderr.split('\n') if line.strip()]
            if error_lines:
                relevant_error = error_lines[-1]
                return f"{base_message}: {relevant_error}"
        
        return base_message


class PackageInstallWorker(BaseWorker):
    """
    Enhanced worker class for installing packages in the background.
    
    This worker handles batch package installation without blocking the UI,
    providing real-time progress updates and detailed results.
    """
    
    def __init__(self, packages: List[str], install_options: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.packages = packages
        self.install_options = install_options or {}
        self.installer = EnhancedPackageInstaller()
        self.results: List[PackageInstallResult] = []
        
        # Installation options
        self.force_install = self.install_options.get('force', True)
        self.allow_empty_checksums = self.install_options.get('allow_empty_checksums', False)
        self.package_timeout = self.install_options.get('package_timeout', 300)
        self.continue_on_failure = self.install_options.get('continue_on_failure', True)
        self.max_retries = self.install_options.get('max_retries', 1)
        
        # Signals for progress reporting
        self.signals = getattr(self, 'signals', None)
    
    def emit_progress(self, message: str, progress: Optional[int] = None) -> None:
        """Emit progress signal if available."""
        if self.signals and hasattr(self.signals, 'emit_progress'):
            if progress is not None:
                self.signals.emit_progress(message, progress)
            else:
                self.signals.emit_progress(message)
        else:
            # Fallback to print for standalone usage
            print(message)
    
    def run(self) -> None:
        """Install packages without blocking UI with enhanced error reporting."""
        try:
            self.emit_progress("Starting package installation...")
            
            # Pre-installation checks
            if not self._run_pre_installation_checks():
                self.emit_progress("Pre-installation checks failed. Aborting.")
                return
            
            total_packages = len(self.packages)
            successful_installs = 0
            failed_installs = 0
            
            for i, package in enumerate(self.packages):
                if self.should_stop():
                    self.emit_progress("Installation stopped by user.")
                    break
                
                self.emit_progress(f"Installing package {i+1}/{total_packages}: {package}")
                
                # Install package with retries
                result = self._install_with_retries(package)
                self.results.append(result)
                
                # Report result
                self._report_package_result(result)
                
                # Update counters
                if result.status == InstallationStatus.SUCCESS:
                    successful_installs += 1
                else:
                    failed_installs += 1
                    if not self.continue_on_failure:
                        self.emit_progress(f"Installation failed for {package}. Stopping due to continue_on_failure=False")
                        break
                
                # Update progress
                progress = int(((i + 1) / total_packages) * 100)
                self.emit_progress(f"Progress: {progress}%", progress)
            
            # Generate summary
            self._generate_installation_summary()
            
        except Exception as e:
            self.emit_progress(f"Critical error during installation: {str(e)}")
    
    def _install_with_retries(self, package: str) -> PackageInstallResult:
        """Install package with retry logic."""
        last_result = None
        
        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                self.emit_progress(f"  Retry {attempt}/{self.max_retries} for {package}")
            
            result = self.installer.install_package(
                package,
                force=self.force_install,
                allow_empty_checksums=self.allow_empty_checksums,
                timeout=self.package_timeout
            )
            
            if result.status == InstallationStatus.SUCCESS:
                return result
            
            last_result = result
            
            if attempt < self.max_retries:
                time.sleep(2)  # Brief delay between retries
        
        return last_result or PackageInstallResult(
            package_name=package,
            status=InstallationStatus.FAILED,
            message="All retry attempts failed"
        )
    
    def _run_pre_installation_checks(self) -> bool:
        """Run pre-installation checks."""
        self.emit_progress("Running pre-installation checks...")
        
        # Check admin privileges
        if not check_admin_privileges():
            self.emit_progress("⚠ Warning: Not running with administrator privileges")
            self.emit_progress("  Some packages may fail to install properly")
        else:
            self.emit_progress("✓ Running with administrator privileges")
        
        # Check Chocolatey availability
        if not self.installer.is_chocolatey_available():
            self.emit_progress("✗ Chocolatey is not installed or not available")
            return False
        else:
            self.emit_progress("✓ Chocolatey is available")
        
        # Check disk space (rough estimate)
        try:
            import shutil
            total, used, free = shutil.disk_usage('.')
            free_gb = free / (1024**3)
            required_gb = len(self.packages) * 0.075
            
            if free_gb > required_gb:
                self.emit_progress(f"✓ Sufficient disk space ({free_gb:.1f} GB available, ~{required_gb:.1f} GB estimated needed)")
            else:
                self.emit_progress(f"⚠ Warning: Low disk space ({free_gb:.1f} GB available, ~{required_gb:.1f} GB estimated needed)")
        except Exception as e:
            self.emit_progress(f"⚠ Warning: Could not check disk space: {str(e)}")
        
        # Test a simple choco command
        self.emit_progress("Testing basic Chocolatey command...")
        try:
            return_code, stdout, stderr = run_command_with_timeout("choco --version", timeout=10)
            if return_code == 0:
                version = stdout.strip()
                self.emit_progress(f"✓ Chocolatey version: {version}")
            else:
                self.emit_progress(f"⚠ Chocolatey version command failed: {stderr}")
                return False
        except Exception as e:
            self.emit_progress(f"⚠ Chocolatey version command error: {str(e)}")
            return False
        
        self.emit_progress("")
        return True
    
    def _report_package_result(self, result: PackageInstallResult) -> None:
        """Report detailed package installation result."""
        if result.status == InstallationStatus.SUCCESS:
            self.emit_progress(f"✓ {result.package_name} installed successfully")
            if result.install_time:
                self.emit_progress(f"  Installation time: {result.install_time:.1f} seconds")
            if result.warnings:
                for warning in result.warnings:
                    self.emit_progress(f"  ⚠ Warning: {warning}")
        else:
            self.emit_progress(f"✗ {result.package_name} installation failed")
            self.emit_progress(f"  Error: {result.message}")
            
            # Show relevant error details from stderr
            if result.error_output:
                error_lines = result.error_output.strip().split('\n')
                relevant_errors = [line for line in error_lines if line.strip() and 
                                 any(keyword in line.lower() for keyword in ['error', 'failed', 'exception'])]
                
                for line in relevant_errors[-2:]:  # Show last 2 relevant error lines
                    if line.strip():
                        self.emit_progress(f"  {line.strip()}")
            
            # Show return code if available
            if result.return_code is not None:
                self.emit_progress(f"  Return code: {result.return_code}")
    
    def _generate_installation_summary(self) -> None:
        """Generate enhanced installation summary."""
        successful = sum(1 for r in self.results if r.status == InstallationStatus.SUCCESS)
        failed = sum(1 for r in self.results if r.status == InstallationStatus.FAILED)
        total = len(self.results)
        
        self.emit_progress("")
        self.emit_progress("=" * 50)
        self.emit_progress("INSTALLATION SUMMARY")
        self.emit_progress("=" * 50)
        self.emit_progress(f"Total packages: {total}")
        self.emit_progress(f"Successful: {successful}")
        self.emit_progress(f"Failed: {failed}")
        
        if successful > 0:
            self.emit_progress("\nSuccessfully installed:")
            for result in self.results:
                if result.status == InstallationStatus.SUCCESS:
                    time_str = f" ({result.install_time:.1f}s)" if result.install_time else ""
                    self.emit_progress(f"  ✓ {result.package_name}{time_str}")
        
        if failed > 0:
            self.emit_progress("\nFailed installations:")
            for result in self.results:
                if result.status == InstallationStatus.FAILED:
                    self.emit_progress(f"  ✗ {result.package_name}: {result.message}")
        
        # Calculate total installation time
        total_time = sum(r.install_time for r in self.results if r.install_time)
        if total_time > 0:
            self.emit_progress(f"\nTotal installation time: {total_time:.1f} seconds")
        
        self.emit_progress("=" * 50)
    
    def get_results(self) -> List[PackageInstallResult]:
        """Get installation results."""
        return self.results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get installation summary as dictionary."""
        successful = sum(1 for r in self.results if r.status == InstallationStatus.SUCCESS)
        failed = sum(1 for r in self.results if r.status == InstallationStatus.FAILED)
        total_time = sum(r.install_time for r in self.results if r.install_time)
        
        return {
            'total_packages': len(self.results),
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / len(self.results)) * 100 if self.results else 0,
            'total_time_seconds': total_time,
            'average_time_per_package': total_time / len(self.results) if self.results else 0,
            'results': [r.to_dict() for r in self.results]
        }


# Utility functions for testing
def test_single_package_installation(package_name: str) -> PackageInstallResult:
    """Test installation of a single package."""
    installer = EnhancedPackageInstaller()
    return installer.install_package(package_name)


def test_batch_installation(packages: List[str]) -> Dict[str, Any]:
    """Test batch installation of packages."""
    worker = PackageInstallWorker(packages)
    worker.run()
    return worker.get_summary()


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        package_name = sys.argv[1]
        print(f"Testing installation of {package_name}...")
        
        result = test_single_package_installation(package_name)
        print(f"Result: {result.status.value}")
        print(f"Message: {result.message}")
        
        if result.install_time:
            print(f"Time: {result.install_time:.1f} seconds")
    else:
        print("Usage: python package_installer.py <package_name>")