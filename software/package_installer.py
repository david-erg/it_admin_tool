"""
Enhanced Package installation management with comprehensive error reporting and logging.

This module handles the installation of software packages through Chocolatey,
including batch installations, progress tracking, verification, and detailed
error reporting.
"""

import subprocess
import time
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from core import BaseWorker, run_command_with_timeout, check_admin_privileges


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
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class EnhancedPackageInstaller:
    """
    Enhanced package installer with comprehensive error reporting and logging.
    
    This class provides methods for installing individual packages and
    managing batch installations with detailed error handling and verification.
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        # Import here to avoid circular imports
        try:
            from software.chocolatey_manager import EnhancedChocolateyManager
            self.chocolatey_manager = EnhancedChocolateyManager()
        except ImportError:
            # Fallback to original manager if enhanced is not available
            from software.chocolatey_manager import ChocolateyManager
            self.chocolatey_manager = ChocolateyManager()
    
    def _log(self, level: str, message: str):
        """Log message if logger is available"""
        if self.logger:
            getattr(self.logger, level)(message)
    
    def install_package(
        self, 
        package_name: str, 
        force: bool = True,
        allow_empty_checksums: bool = False,
        timeout: int = 300,
        additional_args: List[str] = None
    ) -> PackageInstallResult:
        """
        Install a single package with enhanced error reporting.
        
        Args:
            package_name: Name of the package to install
            force: Whether to force installation
            allow_empty_checksums: Whether to allow empty checksums
            timeout: Installation timeout in seconds
            additional_args: Additional arguments for choco install
        
        Returns:
            PackageInstallResult: Detailed installation result
        """
        start_time = time.time()
        self._log("info", f"Starting installation of package: {package_name}")
        
        # Build command with enhanced options
        cmd_parts = ["choco", "install", package_name, "-y"]
        
        if force:
            cmd_parts.append("--force")
        
        if allow_empty_checksums:
            cmd_parts.append("--allow-empty-checksums")
        
        # Add verbose output for better debugging
        cmd_parts.extend(["--verbose", "--debug"])
        
        # Add additional arguments if provided
        if additional_args:
            cmd_parts.extend(additional_args)
        
        # Add timeout argument to chocolatey if supported
        cmd_parts.extend(["--timeout", str(timeout)])
        
        cmd = " ".join(cmd_parts)
        self._log("debug", f"Installation command: {cmd}")
        
        try:
            return_code, stdout, stderr = run_command_with_timeout(
                cmd, timeout=timeout + 30  # Add buffer to our timeout
            )
            
            install_time = time.time() - start_time
            self._log("debug", f"Installation completed in {install_time:.2f} seconds")
            self._log("debug", f"Return code: {return_code}")
            self._log("debug", f"STDOUT length: {len(stdout)} chars")
            self._log("debug", f"STDERR length: {len(stderr)} chars")
            
            # Analyze installation result with enhanced logic
            success, analysis_msg, warnings = self._analyze_installation_result(
                return_code, stdout, stderr, package_name
            )
            
            if success:
                # Verify installation
                self._log("info", f"Verifying installation of {package_name}")
                if self.chocolatey_manager.verify_package_installation(package_name):
                    self._log("info", f"Successfully installed and verified {package_name}")
                    return PackageInstallResult(
                        package_name=package_name,
                        status=InstallationStatus.SUCCESS,
                        message=f"Successfully installed {package_name}",
                        return_code=return_code,
                        install_time=install_time,
                        output=stdout,
                        error_output=stderr,
                        command_used=cmd,
                        warnings=warnings
                    )
                else:
                    self._log("warning", f"Installation completed but verification failed for {package_name}")
                    return PackageInstallResult(
                        package_name=package_name,
                        status=InstallationStatus.FAILED,
                        message=f"Installation completed but verification failed for {package_name}",
                        return_code=return_code,
                        install_time=install_time,
                        output=stdout,
                        error_output=stderr,
                        command_used=cmd,
                        warnings=warnings + ["Package verification failed after installation"]
                    )
            else:
                self._log("error", f"Installation failed for {package_name}: {analysis_msg}")
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
            # Analyze specific error codes
            error_analysis = self._analyze_error_code(return_code, stderr)
            return False, error_analysis, warnings
        
        # Enhanced success indicators
        success_indicators = [
            'successfully installed',
            'installation was successful',
            f'the install of {package_name.lower()}',
            'chocolatey installed',
            f'{package_name.lower()} has been installed',
            'package files install completed',
            'chocolatey v'  # Sometimes success is indicated by version info
        ]
        
        # Enhanced failure indicators
        failure_indicators = [
            'failed',
            'error occurred',
            'access denied',
            'not found',
            'unable to',
            'installation failed',
            'could not',
            'permission denied',
            'package not found',
            'download failed',
            'checksum failed',
            'hash mismatch',
            'network error',
            'timeout',
            'cancelled',
            'aborted'
        ]
        
        # Warning indicators (don't fail but worth noting)
        warning_indicators = [
            'warning',
            'deprecated',
            'outdated',
            'unable to verify',
            'skipping',
            'already exists',
            'conflict'
        ]
        
        # Check for warnings
        for indicator in warning_indicators:
            if indicator in stdout_lower or indicator in stderr_lower:
                warnings.append(f"Warning detected: {indicator}")
        
        # Check for explicit success
        has_success_indicator = any(
            indicator in stdout_lower for indicator in success_indicators
        )
        
        # Check for explicit failure
        has_failure_indicator = any(
            indicator in stdout_lower or indicator in stderr_lower 
            for indicator in failure_indicators
        )
        
        # Enhanced analysis logic
        if has_failure_indicator:
            # Extract specific error message
            error_lines = []
            for line in stdout.split('\n') + stderr.split('\n'):
                line_lower = line.lower()
                if any(fail_ind in line_lower for fail_ind in failure_indicators):
                    error_lines.append(line.strip())
            
            error_summary = "; ".join(error_lines[:3])  # First 3 error lines
            return False, error_summary or "Installation failed", warnings
        
        if has_success_indicator:
            return True, "Installation completed successfully", warnings
        
        # If no explicit indicators, check for common success patterns
        if return_code == 0:
            # Look for package-specific success patterns
            if package_name.lower() in stdout_lower:
                # If package name appears and no failures, assume success
                return True, "Installation appears successful", warnings
            
            # If we have substantial output without errors, assume success
            if len(stdout) > 100 and not has_failure_indicator:
                return True, "Installation completed", warnings
        
        # Default to failure if uncertain
        return False, "Installation status unclear", warnings + ["Could not determine installation status"]
    
    def _analyze_error_code(self, return_code: int, stderr: str) -> str:
        """
        Analyze Chocolatey return codes for specific error messages.
        
        Args:
            return_code: The return code from chocolatey
            stderr: Standard error output
            
        Returns:
            str: Human-readable error message
        """
        # Common Chocolatey return codes
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
        
        # Add stderr details if available
        if stderr.strip():
            # Extract the most relevant error line
            error_lines = [line.strip() for line in stderr.split('\n') if line.strip()]
            if error_lines:
                relevant_error = error_lines[-1]  # Usually the last line is most relevant
                return f"{base_message}: {relevant_error}"
        
        return base_message
    
    def get_installation_requirements(self, packages: List[str]) -> Dict[str, any]:
        """
        Get enhanced installation requirements for a list of packages.
        
        Args:
            packages: List of package names
        
        Returns:
            Dict: Installation requirements and estimates
        """
        return {
            'package_count': len(packages),
            'estimated_time_minutes': len(packages) * 3,  # 3 minutes per package estimate
            'admin_required': True,
            'admin_available': check_admin_privileges(),
            'internet_required': True,
            'chocolatey_available': self.chocolatey_manager.is_chocolatey_installed(),
            'disk_space_estimate_mb': len(packages) * 75,  # 75MB per package estimate
            'chocolatey_working': False,
            'warnings': []
        }


class PackageInstallWorker(BaseWorker):
    """
    Enhanced worker class for installing packages in the background.
    
    This worker handles batch package installation without blocking the UI,
    providing real-time progress updates and detailed results.
    """
    
    def __init__(self, packages: List[str], install_options: Dict[str, any] = None):
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
    
    def run(self):
        """Install packages without blocking UI with enhanced error reporting."""
        try:
            self.emit_progress("=== CHOCOLATEY PACKAGE INSTALLATION ===")
            self.emit_progress(f"Installing {len(self.packages)} package(s)...")
            self.emit_progress("")
            
            # Enhanced pre-installation checks
            if not self._run_pre_installation_checks():
                self.emit_finished()
                return
            
            # Install each package with retry logic
            for i, package in enumerate(self.packages, 1):
                if self.is_cancelled():
                    self.emit_progress("Installation cancelled by user")
                    break
                
                self.emit_progress(f"[{i}/{len(self.packages)}] Installing {package}...")
                
                # Try installation with retries
                result = self._install_with_retries(package)
                self.results.append(result)
                
                # Report result with enhanced details
                self._report_package_result(result)
                
                # Stop on failure if configured
                if result.status == InstallationStatus.FAILED and not self.continue_on_failure:
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
    
    def _install_with_retries(self, package_name: str) -> PackageInstallResult:
        """Install a package with retry logic."""
        last_result = None
        
        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                self.emit_progress(f"  Retry attempt {attempt} for {package_name}...")
            
            result = self.installer.install_package(
                package_name=package_name,
                force=self.force_install,
                allow_empty_checksums=self.allow_empty_checksums,
                timeout=self.package_timeout
            )
            
            if result.status == InstallationStatus.SUCCESS:
                if attempt > 0:
                    self.emit_progress(f"  ✓ {package_name} succeeded on attempt {attempt + 1}")
                return result
            
            last_result = result
            
            # Don't retry certain types of failures
            if self._should_not_retry(result):
                break
        
        return last_result
    
    def _should_not_retry(self, result: PackageInstallResult) -> bool:
        """Determine if a failed installation should not be retried."""
        # Don't retry for certain types of errors
        no_retry_indicators = [
            "package not found",
            "access denied",
            "permission denied",
            "not found",
            "invalid package"
        ]
        
        error_text = (result.message + " " + result.error_output).lower()
        return any(indicator in error_text for indicator in no_retry_indicators)
    
    def _run_pre_installation_checks(self) -> bool:
        """
        Enhanced pre-installation checks with detailed reporting.
        
        Returns:
            bool: True if checks passed and installation can proceed
        """
        self.emit_progress("=== PRE-INSTALLATION CHECKS ===")
        
        # Check Chocolatey installation
        if not self.installer.chocolatey_manager.is_chocolatey_installed():
            self.emit_error("Chocolatey is not installed")
            return False
        
        self.emit_progress("✓ Chocolatey is installed")
        
        # Enhanced Chocolatey functionality test
        is_working, test_message = self.installer.chocolatey_manager.test_chocolatey_functionality()
        if is_working:
            self.emit_progress(f"✓ Chocolatey functionality test passed: {test_message}")
        else:
            self.emit_error(f"Chocolatey functionality test failed: {test_message}")
            return False
        
        # Check admin privileges
        if check_admin_privileges():
            self.emit_progress("✓ Administrator privileges available")
        else:
            self.emit_progress("⚠ Warning: Running without administrator privileges")
            self.emit_progress("  Some installations may fail")
        
        # Enhanced internet connectivity check
        has_internet, internet_message = self.installer.chocolatey_manager.check_internet_connectivity()
        if has_internet:
            self.emit_progress(f"✓ Internet connectivity verified: {internet_message}")
        else:
            self.emit_progress(f"⚠ Warning: {internet_message}")
            self.emit_progress("  Package installations may fail without internet access")
        
        # Check disk space (enhanced)
        try:
            import shutil
            free_bytes = shutil.disk_usage('.').free
            free_gb = free_bytes / (1024**3)
            required_gb = len(self.packages) * 0.075  # 75MB per package estimate
            
            if free_gb > required_gb:
                self.emit_progress(f"✓ Sufficient disk space ({free_gb:.1f} GB available, ~{required_gb:.1f} GB estimated needed)")
            else:
                self.emit_progress(f"⚠ Warning: Low disk space ({free_gb:.1f} GB available, ~{required_gb:.1f} GB estimated needed)")
        except Exception as e:
            self.emit_progress(f"⚠ Warning: Could not check disk space: {str(e)}")
        
        # Test a simple choco command
        self.emit_progress("Testing basic Chocolatey command...")
        try:
            from core import run_command_with_timeout
            return_code, stdout, stderr = run_command_with_timeout("choco --version", timeout=10)
            if return_code == 0:
                self.emit_progress(f"✓ Chocolatey version command successful: {stdout.strip()}")
            else:
                self.emit_progress(f"⚠ Chocolatey version command failed: {stderr}")
                return False
        except Exception as e:
            self.emit_progress(f"⚠ Chocolatey version command error: {str(e)}")
            return False
        
        self.emit_progress("")
        return True
    
    def _report_package_result(self, result: PackageInstallResult):
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
    
    def _generate_installation_summary(self):
        """Generate enhanced installation summary."""
        self.emit_progress("=== INSTALLATION SUMMARY ===")
        
        successful = [r for r in self.results if r.status == InstallationStatus.SUCCESS]
        failed = [r for r in self.results if r.status == InstallationStatus.FAILED]
        
        self.emit_progress(f"Total packages: {len(self.packages)}")
        self.emit_progress(f"Successfully installed: {len(successful)}")
        self.emit_progress(f"Failed: {len(failed)}")
        
        if successful and failed:
            success_rate = len(successful) / len(self.results) * 100
            self.emit_progress(f"Success rate: {success_rate:.1f}%")
        
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
        
        # Enhanced troubleshooting tips
        if failed:
            self.emit_progress("")
            self.emit_progress("Troubleshooting tips for failed installations:")
            self.emit_progress("• Ensure you're running as Administrator")
            self.emit_progress("• Check your internet connection")
            self.emit_progress("• Verify package names are correct")
            self.emit_progress("• Try installing failed packages individually")
            self.emit_progress("• Some packages may require manual confirmation")
            self.emit_progress("• Check if antivirus software is blocking the installation")
            
            # Specific tips based on error patterns
            common_errors = {}
            for result in failed:
                error_text = result.message.lower()
                if "not found" in error_text:
                    common_errors["Package not found"] = "Verify package names on chocolatey.org"
                elif "access denied" in error_text or "permission" in error_text:
                    common_errors["Permission denied"] = "Run as Administrator and check antivirus settings"
                elif "network" in error_text or "download" in error_text:
                    common_errors["Network error"] = "Check internet connection and firewall settings"
                elif "timeout" in error_text:
                    common_errors["Timeout"] = "Increase timeout value or check connection speed"
            
            if common_errors:
                self.emit_progress("")
                self.emit_progress("Specific recommendations:")
                for error_type, recommendation in common_errors.items():
                    self.emit_progress(f"• {error_type}: {recommendation}")
        
        if len(successful) > 0:
            self.emit_progress("")
            self.emit_progress("Note: Some installations may require a system restart to take effect.")
            self.emit_progress("You can verify installations by running: choco list --local-only")
        
        self.emit_progress("")
        self.emit_progress("=== INSTALLATION PROCESS COMPLETED ===")
    
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
    
    def get_detailed_summary(self) -> Dict[str, any]:
        """Get detailed installation summary."""
        return {
            'total_packages': len(self.packages),
            'successful_count': self.get_success_count(),
            'failed_count': self.get_failure_count(),
            'total_time': self.get_total_install_time(),
            'success_rate': self.get_success_count() / len(self.packages) * 100 if self.packages else 0,
            'results': [
                {
                    'package': result.package_name,
                    'status': result.status.value,
                    'message': result.message,
                    'time': result.install_time,
                    'warnings': result.warnings
                }
                for result in self.results
            ]
        }