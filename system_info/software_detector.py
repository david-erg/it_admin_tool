"""
Software detection and identification.

This module provides comprehensive software detection capabilities including
operating system information, installed applications, antivirus software,
and Microsoft Office products.
"""

import subprocess
from typing import List, Dict, Optional
from dataclasses import dataclass

from core import query_wmic, run_command_with_timeout, safe_get_env_var


@dataclass
class OperatingSystemInfo:
    """Operating system information structure."""
    name: str
    version: str = ""
    build: str = ""
    architecture: str = ""
    install_date: str = ""
    last_boot_time: str = ""
    registered_user: str = ""


@dataclass
class OfficeInfo:
    """Microsoft Office information structure."""
    product_name: str
    version: str = ""
    installation_path: str = ""
    license_type: str = ""
    is_click_to_run: bool = False


@dataclass
class AntivirusInfo:
    """Antivirus software information structure."""
    display_name: str
    product_state: str = ""
    publisher: str = ""
    is_enabled: bool = False
    is_up_to_date: bool = False


class SoftwareDetector:
    """
    Detects and identifies installed software.
    
    This class provides methods for detecting operating system information,
    Microsoft Office installations, antivirus software, and other applications.
    """
    
    def __init__(self):
        self.timeout = 30
    
    def detect_operating_system(self) -> OperatingSystemInfo:
        """
        Detect operating system information.
        
        Returns:
            OperatingSystemInfo: Operating system details
        """
        try:
            # Get OS caption (name)
            os_caption = query_wmic("wmic os get caption")
            name = os_caption[0] if os_caption else "Unknown OS"
            
            # Get additional OS details
            os_details = self._get_os_details()
            
            return OperatingSystemInfo(
                name=name,
                version=os_details.get('version', ''),
                build=os_details.get('build', ''),
                architecture=os_details.get('architecture', ''),
                install_date=os_details.get('install_date', ''),
                last_boot_time=os_details.get('last_boot_time', ''),
                registered_user=os_details.get('registered_user', '')
            )
            
        except Exception as e:
            return OperatingSystemInfo(name=f"Detection Error: {str(e)}")
    
    def _get_os_details(self) -> Dict[str, str]:
        """Get detailed operating system information."""
        details = {}
        
        try:
            # Version
            version = query_wmic("wmic os get version")
            if version:
                details['version'] = version[0]
            
            # Build number
            build = query_wmic("wmic os get buildnumber")
            if build:
                details['build'] = build[0]
            
            # Architecture
            architecture = query_wmic("wmic os get osarchitecture")
            if architecture:
                details['architecture'] = architecture[0]
            
            # Install date
            install_date = query_wmic("wmic os get installdate")
            if install_date:
                details['install_date'] = self._format_wmi_date(install_date[0])
            
            # Last boot time
            boot_time = query_wmic("wmic os get lastbootuptime")
            if boot_time:
                details['last_boot_time'] = self._format_wmi_date(boot_time[0])
            
            # Registered user
            user = query_wmic("wmic os get registereduser")
            if user:
                details['registered_user'] = user[0]
            
        except Exception:
            pass
        
        return details
    
    def _format_wmi_date(self, wmi_date: str) -> str:
        """Format WMI date string to readable format."""
        try:
            if len(wmi_date) >= 14:
                # WMI date format: YYYYMMDDHHMMSS.000000+000
                year = wmi_date[0:4]
                month = wmi_date[4:6]
                day = wmi_date[6:8]
                hour = wmi_date[8:10]
                minute = wmi_date[10:12]
                second = wmi_date[12:14]
                
                return f"{year}-{month}-{day} {hour}:{minute}:{second}"
        except Exception:
            pass
        
        return wmi_date
    
    def detect_office_products(self) -> List[OfficeInfo]:
        """
        Detect Microsoft Office installations.
        
        Returns:
            List[OfficeInfo]: List of detected Office products
        """
        office_products = []
        
        # Try multiple detection methods
        office_products.extend(self._detect_office_click_to_run())
        
        if not office_products:
            office_products.extend(self._detect_office_msi())
        
        if not office_products:
            office_products.extend(self._detect_office_registry())
        
        return office_products if office_products else [OfficeInfo(product_name="None detected")]
    
    def _detect_office_click_to_run(self) -> List[OfficeInfo]:
        """Detect Office Click-to-Run installations."""
        office_products = []
        
        try:
            # Check ClickToRun configuration for exact product name
            reg_paths = [
                r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Office\ClickToRun\Configuration',
                r'HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Office\ClickToRun\Configuration'
            ]
            
            for reg_path in reg_paths:
                # Get ProductReleaseIds
                cmd = f'reg query "{reg_path}" /v ProductReleaseIds'
                return_code, stdout, stderr = run_command_with_timeout(cmd, timeout=10)
                
                if return_code == 0:
                    product_ids = self._extract_reg_value(stdout, "ProductReleaseIds")
                    
                    if product_ids:
                        # Try to get exact product name
                        name_cmd = f'reg query "{reg_path}" /v ProductName'
                        name_result = run_command_with_timeout(name_cmd, timeout=10)
                        
                        if name_result[0] == 0:
                            product_name = self._extract_reg_value(name_result[1], "ProductName")
                            if product_name:
                                version = self._get_office_version(reg_path)
                                office_products.append(OfficeInfo(
                                    product_name=product_name,
                                    version=version,
                                    is_click_to_run=True,
                                    license_type="Click-to-Run"
                                ))
                                return office_products
                        
                        # Fallback: interpret product IDs
                        interpreted_name = self._interpret_office_product_ids(product_ids)
                        if interpreted_name:
                            version = self._get_office_version(reg_path)
                            office_products.append(OfficeInfo(
                                product_name=interpreted_name,
                                version=version,
                                is_click_to_run=True,
                                license_type="Click-to-Run"
                            ))
                            return office_products
        
        except Exception:
            pass
        
        return office_products
    
    def _detect_office_msi(self) -> List[OfficeInfo]:
        """Detect traditional MSI Office installations."""
        office_products = []
        
        try:
            # Check traditional Office registry paths
            msi_paths = [
                r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Office\16.0\Registration',
                r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Office\15.0\Registration',
                r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Office\14.0\Registration',
                r'HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Office\16.0\Registration',
                r'HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Office\15.0\Registration'
            ]
            
            for reg_path in msi_paths:
                cmd = f'reg query "{reg_path}" /s'
                return_code, stdout, stderr = run_command_with_timeout(cmd, timeout=15)
                
                if return_code == 0:
                    for line in stdout.splitlines():
                        if "ProductName" in line and "REG_SZ" in line:
                            product_name = self._extract_reg_value(line, "ProductName")
                            
                            if product_name and "Microsoft Office" in product_name:
                                # Filter out components and keep main products
                                main_products = ["Professional", "Standard", "Home", "Personal", "Enterprise"]
                                excluded = ["component", "mui", "language", "proofing", "shared"]
                                
                                if (any(prod in product_name for prod in main_products) and
                                    not any(skip in product_name.lower() for skip in excluded)):
                                    
                                    version = self._extract_office_version_from_path(reg_path)
                                    office_products.append(OfficeInfo(
                                        product_name=product_name,
                                        version=version,
                                        is_click_to_run=False,
                                        license_type="MSI"
                                    ))
                                    return office_products
        
        except Exception:
            pass
        
        return office_products
    
    def _detect_office_registry(self) -> List[OfficeInfo]:
        """Detect Office through uninstall registry entries."""
        office_products = []
        
        try:
            # Check uninstall registry
            uninstall_paths = [
                r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                r'HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
            ]
            
            for reg_path in uninstall_paths:
                cmd = f'reg query "{reg_path}" /s /f "Microsoft Office"'
                return_code, stdout, stderr = run_command_with_timeout(cmd, timeout=20)
                
                if return_code == 0:
                    for line in stdout.splitlines():
                        if "DisplayName" in line and "Microsoft Office" in line:
                            product_name = self._extract_reg_value(line, "DisplayName")
                            
                            if product_name:
                                # Filter for main Office products
                                if any(term in product_name for term in ["365", "2019", "2021", "2016", "Professional", "Standard"]):
                                    office_products.append(OfficeInfo(
                                        product_name=product_name,
                                        license_type="Unknown"
                                    ))
                                    return office_products
        
        except Exception:
            pass
        
        return office_products
    
    def _extract_reg_value(self, line: str, value_name: str) -> Optional[str]:
        """Extract value from registry query output line."""
        try:
            if value_name in line and "REG_SZ" in line:
                parts = line.split("REG_SZ")
                if len(parts) > 1:
                    return parts[-1].strip()
        except Exception:
            pass
        return None
    
    def _interpret_office_product_ids(self, product_ids: str) -> Optional[str]:
        """Interpret Office product IDs to product names."""
        product_map = {
            "O365ProPlusRetail": "Microsoft 365 Apps for business",
            "O365BusinessRetail": "Microsoft 365 Apps for business",
            "O365HomePremRetail": "Microsoft 365 Family",
            "O365HomeRetail": "Microsoft 365 Personal",
            "ProPlus2019Retail": "Office Professional Plus 2019",
            "Professional2019Retail": "Office Professional 2019",
            "Standard2019Retail": "Office Standard 2019",
            "ProPlus2021Retail": "Office Professional Plus 2021",
            "Professional2021Retail": "Office Professional 2021",
            "HomeBusiness2019Retail": "Office Home & Business 2019",
            "HomeBusiness2021Retail": "Office Home & Business 2021"
        }
        
        for product_id, product_name in product_map.items():
            if product_id in product_ids:
                return product_name
        
        # Generic fallback
        if "365" in product_ids:
            return "Microsoft 365"
        elif "2021" in product_ids:
            return "Microsoft Office 2021"
        elif "2019" in product_ids:
            return "Microsoft Office 2019"
        elif "2016" in product_ids:
            return "Microsoft Office 2016"
        
        return None
    
    def _get_office_version(self, reg_path: str) -> str:
        """Get Office version from registry path."""
        try:
            version_cmd = f'reg query "{reg_path}" /v VersionToReport'
            return_code, stdout, stderr = run_command_with_timeout(version_cmd, timeout=10)
            
            if return_code == 0:
                version = self._extract_reg_value(stdout, "VersionToReport")
                if version:
                    return version
        except Exception:
            pass
        
        return ""
    
    def _extract_office_version_from_path(self, reg_path: str) -> str:
        """Extract Office version from registry path."""
        version_map = {
            "16.0": "2016/2019/2021/365",
            "15.0": "2013",
            "14.0": "2010",
            "12.0": "2007"
        }
        
        for version_key, version_name in version_map.items():
            if version_key in reg_path:
                return version_name
        
        return ""
    
    def detect_antivirus_software(self) -> List[AntivirusInfo]:
        """
        Detect antivirus software using Windows Security Center.
        
        Returns:
            List[AntivirusInfo]: List of detected antivirus products
        """
        antivirus_products = []
        
        # Try multiple detection methods
        antivirus_products.extend(self._detect_antivirus_powershell())
        
        if not antivirus_products:
            antivirus_products.extend(self._detect_antivirus_wmic())
        
        if not antivirus_products:
            antivirus_products.extend(self._detect_windows_defender())
        
        return antivirus_products if antivirus_products else [AntivirusInfo(display_name="Not Detected")]
    
    def _detect_antivirus_powershell(self) -> List[AntivirusInfo]:
        """Detect antivirus using PowerShell SecurityCenter2."""
        antivirus_products = []
        
        try:
            cmd = (
                'powershell -Command "Get-CimInstance -Namespace root/SecurityCenter2 '
                '-ClassName AntivirusProduct | Select-Object displayName, productState '
                '| Format-Table -HideTableHeaders"'
            )
            
            return_code, stdout, stderr = run_command_with_timeout(cmd, timeout=20)
            
            if return_code == 0:
                for line in stdout.splitlines():
                    line = line.strip()
                    if line and not line.isdigit():
                        # Parse display name and product state
                        parts = line.split()
                        if parts:
                            # Remove product state number if present
                            if len(parts) > 1 and parts[-1].isdigit():
                                av_name = " ".join(parts[:-1])
                                product_state = parts[-1]
                            else:
                                av_name = line
                                product_state = ""
                            
                            if av_name:
                                is_enabled = self._parse_product_state(product_state)
                                antivirus_products.append(AntivirusInfo(
                                    display_name=av_name,
                                    product_state=product_state,
                                    is_enabled=is_enabled
                                ))
        
        except Exception:
            pass
        
        return antivirus_products
    
    def _detect_antivirus_wmic(self) -> List[AntivirusInfo]:
        """Detect antivirus using WMIC SecurityCenter2."""
        antivirus_products = []
        
        try:
            # Try SecurityCenter2 first (Windows Vista+)
            cmd = r'wmic /namespace:\\root\\SecurityCenter2 path AntiVirusProduct get displayName'
            return_code, stdout, stderr = run_command_with_timeout(cmd, timeout=15)
            
            if return_code == 0:
                for line in stdout.splitlines():
                    line = line.strip()
                    if line and "displayName" not in line:
                        antivirus_products.append(AntivirusInfo(display_name=line))
            
            # Fallback to SecurityCenter (older Windows)
            if not antivirus_products:
                cmd = r'wmic /namespace:\\root\\SecurityCenter path AntiVirusProduct get displayName'
                return_code, stdout, stderr = run_command_with_timeout(cmd, timeout=15)
                
                if return_code == 0:
                    for line in stdout.splitlines():
                        line = line.strip()
                        if line and "displayName" not in line:
                            antivirus_products.append(AntivirusInfo(display_name=line))
        
        except Exception:
            pass
        
        return antivirus_products
    
    def _detect_windows_defender(self) -> List[AntivirusInfo]:
        """Detect Windows Defender specifically."""
        try:
            cmd = '''powershell -Command "Get-MpPreference | Select-Object -ExpandProperty DisableRealtimeMonitoring"'''
            return_code, stdout, stderr = run_command_with_timeout(cmd, timeout=10)
            
            if return_code == 0:
                disabled = stdout.strip().lower()
                is_enabled = disabled == "false"
                
                return [AntivirusInfo(
                    display_name="Windows Defender",
                    is_enabled=is_enabled
                )]
        
        except Exception:
            pass
        
        return []
    
    def _parse_product_state(self, product_state: str) -> bool:
        """Parse antivirus product state to determine if enabled."""
        try:
            if product_state.isdigit():
                state = int(product_state)
                # Product state is a bitmask - enabled if certain bits are set
                # This is a simplified check
                return (state & 0x1000) != 0
        except Exception:
            pass
        
        return False
    
    def detect_installed_applications(self, limit: int = 50) -> List[Dict[str, str]]:
        """
        Detect installed applications from registry.
        
        Args:
            limit: Maximum number of applications to return
        
        Returns:
            List[Dict]: List of installed applications
        """
        applications = []
        
        try:
            uninstall_paths = [
                r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                r'HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
            ]
            
            for reg_path in uninstall_paths:
                cmd = f'reg query "{reg_path}" /s'
                return_code, stdout, stderr = run_command_with_timeout(cmd, timeout=30)
                
                if return_code == 0:
                    current_app = {}
                    
                    for line in stdout.splitlines():
                        line = line.strip()
                        
                        # New application entry
                        if line.startswith(reg_path) and len(line.split('\\')) > len(reg_path.split('\\')):
                            if current_app.get('DisplayName'):
                                applications.append(current_app.copy())
                                if len(applications) >= limit:
                                    return applications
                            current_app = {}
                        
                        # Extract application properties
                        elif "DisplayName" in line and "REG_SZ" in line:
                            display_name = self._extract_reg_value(line, "DisplayName")
                            if display_name:
                                current_app['DisplayName'] = display_name
                        
                        elif "DisplayVersion" in line and "REG_SZ" in line:
                            version = self._extract_reg_value(line, "DisplayVersion")
                            if version:
                                current_app['Version'] = version
                        
                        elif "Publisher" in line and "REG_SZ" in line:
                            publisher = self._extract_reg_value(line, "Publisher")
                            if publisher:
                                current_app['Publisher'] = publisher
                    
                    # Add final application
                    if current_app.get('DisplayName'):
                        applications.append(current_app)
        
        except Exception:
            pass
        
        return applications[:limit]
    
    def get_comprehensive_software_info(self) -> Dict[str, any]:
        """
        Get comprehensive software information.
        
        Returns:
            Dict: Complete software information
        """
        return {
            'operating_system': self.detect_operating_system(),
            'office_products': self.detect_office_products(),
            'antivirus_software': self.detect_antivirus_software(),
            'installed_applications': self.detect_installed_applications(limit=20)
        }