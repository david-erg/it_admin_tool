"""
Windows Settings Manager Module

Provides functionality to configure essential Windows settings through registry
modifications. Requires administrator privileges for system-wide changes.
"""

import subprocess
import platform
from typing import Dict, List, Tuple, Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum
from .registry_helper import RegistryHelper, RegistryHive, RegistryValueType


class SettingCategory(Enum):
    """Categories of Windows settings"""
    PRIVACY = "privacy"
    EXPLORER = "explorer"
    SEARCH = "search"
    INTERFACE = "interface"
    NOTIFICATIONS = "notifications"
    SECURITY = "security"
    PERFORMANCE = "performance"


class SettingScope(Enum):
    """Scope of setting application"""
    USER = "user"          # Current user only (HKCU)
    SYSTEM = "system"      # System-wide (HKLM)
    BOTH = "both"          # Both user and system


@dataclass
class WindowsSetting:
    """Represents a Windows setting that can be configured"""
    key: str
    name: str
    description: str
    category: SettingCategory
    scope: SettingScope
    registry_changes: List[Dict[str, Any]]
    is_recommended: bool = True
    requires_restart: bool = False
    requires_explorer_restart: bool = False


class WindowsSettingsManager:
    """Manages Windows system settings configuration"""
    
    # Predefined Windows settings
    SETTINGS_CATALOG = {
        "show_file_extensions": WindowsSetting(
            key="show_file_extensions",
            name="Show file extensions in File Explorer",
            description="Display file extensions for known file types",
            category=SettingCategory.EXPLORER,
            scope=SettingScope.USER,
            registry_changes=[{
                "hive": RegistryHive.HKCU,
                "path": "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced",
                "name": "HideFileExt",
                "value": 0,
                "type": RegistryValueType.REG_DWORD
            }],
            requires_explorer_restart=True
        ),
        
        "show_hidden_files": WindowsSetting(
            key="show_hidden_files",
            name="Show hidden files and folders",
            description="Display hidden files and folders in File Explorer",
            category=SettingCategory.EXPLORER,
            scope=SettingScope.USER,
            registry_changes=[{
                "hive": RegistryHive.HKCU,
                "path": "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced",
                "name": "Hidden",
                "value": 1,
                "type": RegistryValueType.REG_DWORD
            }],
            requires_explorer_restart=True
        ),
        
        "disable_cortana": WindowsSetting(
            key="disable_cortana",
            name="Disable Cortana",
            description="Turn off Cortana search assistant",
            category=SettingCategory.SEARCH,
            scope=SettingScope.USER,
            registry_changes=[{
                "hive": RegistryHive.HKCU,
                "path": "Software\\Microsoft\\Windows\\CurrentVersion\\Search",
                "name": "SearchboxTaskbarMode",
                "value": 0,
                "type": RegistryValueType.REG_DWORD
            }],
            requires_explorer_restart=True
        ),
        
        "disable_web_search": WindowsSetting(
            key="disable_web_search",
            name="Disable web search in Start Menu",
            description="Prevent Start Menu from searching the web",
            category=SettingCategory.SEARCH,
            scope=SettingScope.USER,
            registry_changes=[{
                "hive": RegistryHive.HKCU,
                "path": "Software\\Microsoft\\Windows\\CurrentVersion\\Search",
                "name": "BingSearchEnabled",
                "value": 0,
                "type": RegistryValueType.REG_DWORD
            }]
        ),
        
        "disable_telemetry": WindowsSetting(
            key="disable_telemetry",
            name="Disable Windows telemetry and data collection",
            description="Minimize data collection by Windows",
            category=SettingCategory.PRIVACY,
            scope=SettingScope.SYSTEM,
            registry_changes=[{
                "hive": RegistryHive.HKLM,
                "path": "SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection",
                "name": "AllowTelemetry",
                "value": 0,
                "type": RegistryValueType.REG_DWORD
            }],
            requires_restart=True
        ),
        
        "disable_consumer_features": WindowsSetting(
            key="disable_consumer_features",
            name="Disable consumer features (ads, suggestions)",
            description="Turn off Windows ads and app suggestions",
            category=SettingCategory.PRIVACY,
            scope=SettingScope.SYSTEM,
            registry_changes=[{
                "hive": RegistryHive.HKLM,
                "path": "SOFTWARE\\Policies\\Microsoft\\Windows\\CloudContent",
                "name": "DisableWindowsConsumerFeatures",
                "value": 1,
                "type": RegistryValueType.REG_DWORD
            }]
        ),
        
        "disable_location_tracking": WindowsSetting(
            key="disable_location_tracking",
            name="Disable location tracking",
            description="Turn off location services for privacy",
            category=SettingCategory.PRIVACY,
            scope=SettingScope.SYSTEM,
            registry_changes=[{
                "hive": RegistryHive.HKLM,
                "path": "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location",
                "name": "Value",
                "value": "Deny",
                "type": RegistryValueType.REG_SZ
            }]
        ),
        
        "disable_advertising_id": WindowsSetting(
            key="disable_advertising_id",
            name="Disable advertising ID",
            description="Turn off advertising ID for privacy",
            category=SettingCategory.PRIVACY,
            scope=SettingScope.USER,
            registry_changes=[{
                "hive": RegistryHive.HKCU,
                "path": "Software\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo",
                "name": "Enabled",
                "value": 0,
                "type": RegistryValueType.REG_DWORD
            }]
        ),
        
        "enable_dark_mode": WindowsSetting(
            key="enable_dark_mode",
            name="Enable Windows dark mode",
            description="Switch to dark theme for better eye comfort",
            category=SettingCategory.INTERFACE,
            scope=SettingScope.USER,
            registry_changes=[
                {
                    "hive": RegistryHive.HKCU,
                    "path": "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                    "name": "AppsUseLightTheme",
                    "value": 0,
                    "type": RegistryValueType.REG_DWORD
                },
                {
                    "hive": RegistryHive.HKCU,
                    "path": "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize",
                    "name": "SystemUsesLightTheme",
                    "value": 0,
                    "type": RegistryValueType.REG_DWORD
                }
            ],
            requires_explorer_restart=True
        ),
        
        "disable_lock_screen_ads": WindowsSetting(
            key="disable_lock_screen_ads",
            name="Disable lock screen ads and tips",
            description="Remove advertisements from Windows lock screen",
            category=SettingCategory.PRIVACY,
            scope=SettingScope.USER,
            registry_changes=[
                {
                    "hive": RegistryHive.HKCU,
                    "path": "Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager",
                    "name": "RotatingLockScreenOverlayEnabled",
                    "value": 0,
                    "type": RegistryValueType.REG_DWORD
                },
                {
                    "hive": RegistryHive.HKCU,
                    "path": "Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager",
                    "name": "SubscribedContent-338387Enabled",
                    "value": 0,
                    "type": RegistryValueType.REG_DWORD
                }
            ]
        ),
        
        "disable_timeline": WindowsSetting(
            key="disable_timeline",
            name="Disable Windows Timeline",
            description="Turn off activity history and timeline feature",
            category=SettingCategory.PRIVACY,
            scope=SettingScope.SYSTEM,
            registry_changes=[{
                "hive": RegistryHive.HKLM,
                "path": "SOFTWARE\\Policies\\Microsoft\\Windows\\System",
                "name": "EnableActivityFeed",
                "value": 0,
                "type": RegistryValueType.REG_DWORD
            }]
        ),
        
        "classic_right_click": WindowsSetting(
            key="classic_right_click",
            name="Enable classic right-click context menu (Windows 11)",
            description="Restore the classic context menu in Windows 11",
            category=SettingCategory.INTERFACE,
            scope=SettingScope.USER,
            registry_changes=[{
                "hive": RegistryHive.HKCU,
                "path": "Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32",
                "name": "",
                "value": "",
                "type": RegistryValueType.REG_SZ
            }],
            requires_explorer_restart=True
        ),
        
        "taskbar_cleanup": WindowsSetting(
            key="taskbar_cleanup",
            name="Remove weather, news, task view from taskbar",
            description="Clean up taskbar by removing unnecessary widgets",
            category=SettingCategory.INTERFACE,
            scope=SettingScope.USER,
            registry_changes=[
                {
                    "hive": RegistryHive.HKCU,
                    "path": "Software\\Microsoft\\Windows\\CurrentVersion\\Feeds",
                    "name": "ShellFeedsTaskbarViewMode",
                    "value": 2,
                    "type": RegistryValueType.REG_DWORD
                },
                {
                    "hive": RegistryHive.HKCU,
                    "path": "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced",
                    "name": "ShowTaskViewButton",
                    "value": 0,
                    "type": RegistryValueType.REG_DWORD
                }
            ],
            requires_explorer_restart=True
        ),
        
        "disable_notifications": WindowsSetting(
            key="disable_notifications",
            name="Disable non-essential notifications",
            description="Reduce interruptions from Windows notifications",
            category=SettingCategory.NOTIFICATIONS,
            scope=SettingScope.USER,
            registry_changes=[
                {
                    "hive": RegistryHive.HKCU,
                    "path": "Software\\Microsoft\\Windows\\CurrentVersion\\PushNotifications",
                    "name": "ToastEnabled",
                    "value": 0,
                    "type": RegistryValueType.REG_DWORD
                },
                {
                    "hive": RegistryHive.HKCU,
                    "path": "Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings",
                    "name": "NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION_SOUND",
                    "value": 0,
                    "type": RegistryValueType.REG_DWORD
                }
            ]
        ),
        
        "disable_startup_boost": WindowsSetting(
            key="disable_startup_boost",
            name="Disable Windows startup boost",
            description="Improve system performance by disabling startup boost",
            category=SettingCategory.PERFORMANCE,
            scope=SettingScope.SYSTEM,
            registry_changes=[{
                "hive": RegistryHive.HKLM,
                "path": "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Serialize",
                "name": "StartupDelayInMSec",
                "value": 0,
                "type": RegistryValueType.REG_DWORD
            }]
        ),
        
        "disable_windows_defender_cloud": WindowsSetting(
            key="disable_windows_defender_cloud",
            name="Disable Windows Defender cloud protection",
            description="Turn off cloud-based protection for privacy",
            category=SettingCategory.PRIVACY,
            scope=SettingScope.SYSTEM,
            registry_changes=[
                {
                    "hive": RegistryHive.HKLM,
                    "path": "SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Spynet",
                    "name": "SpynetReporting",
                    "value": 0,
                    "type": RegistryValueType.REG_DWORD
                },
                {
                    "hive": RegistryHive.HKLM,
                    "path": "SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Spynet",
                    "name": "SubmitSamplesConsent",
                    "value": 2,
                    "type": RegistryValueType.REG_DWORD
                }
            ],
            is_recommended=False,  # May reduce security
            requires_restart=True
        )
    }
    
    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize WindowsSettingsManager
        
        Args:
            progress_callback: Optional callback function for progress updates
        """
        self._validate_platform()
        self.progress_callback = progress_callback or self._default_progress_callback
        self.registry_helper = RegistryHelper()
    
    def _validate_platform(self) -> None:
        """Ensure we're running on Windows"""
        if platform.system() != "Windows":
            raise OSError("Windows settings management is only supported on Windows")
    
    def _default_progress_callback(self, message: str) -> None:
        """Default progress callback that prints to console"""
        print(message)
    
    def get_available_settings(self) -> Dict[str, WindowsSetting]:
        """
        Get dictionary of all available settings
        
        Returns:
            Dict mapping setting keys to WindowsSetting objects
        """
        return self.SETTINGS_CATALOG.copy()
    
    def get_settings_by_category(self, category: SettingCategory) -> Dict[str, WindowsSetting]:
        """
        Get settings filtered by category
        
        Args:
            category: SettingCategory to filter by
            
        Returns:
            Dict of filtered settings
        """
        return {
            key: setting for key, setting in self.SETTINGS_CATALOG.items()
            if setting.category == category
        }
    
    def get_recommended_settings(self) -> List[str]:
        """
        Get list of recommended setting keys
        
        Returns:
            List of setting keys that are recommended for most users
        """
        return [
            key for key, setting in self.SETTINGS_CATALOG.items()
            if setting.is_recommended
        ]
    
    def apply_setting(self, setting_key: str, timeout: int = 15) -> bool:
        """
        Apply a single Windows setting
        
        Args:
            setting_key: Key of the setting to apply
            timeout: Timeout per registry operation
            
        Returns:
            bool: True if all registry changes were successful
        """
        if setting_key not in self.SETTINGS_CATALOG:
            self.progress_callback(f"✗ Unknown setting: {setting_key}")
            return False
        
        setting = self.SETTINGS_CATALOG[setting_key]
        self.progress_callback(f"Applying: {setting.name}...")
        
        success_count = 0
        total_changes = len(setting.registry_changes)
        
        for change in setting.registry_changes:
            try:
                success = self.registry_helper.add_value(
                    hive=change["hive"],
                    path=change["path"],
                    name=change["name"],
                    value=change["value"],
                    value_type=change["type"],
                    timeout=timeout
                )
                
                if success:
                    success_count += 1
                else:
                    self.progress_callback(f"  ⚠ Failed registry change: {change['path']}\\{change['name']}")
                    
            except Exception as e:
                self.progress_callback(f"  ⚠ Registry error: {str(e)}")
        
        if success_count == total_changes:
            self.progress_callback(f"✓ {setting.name} applied successfully")
            return True
        else:
            self.progress_callback(f"✗ {setting.name} partially applied ({success_count}/{total_changes})")
            return False
    
    def apply_multiple_settings(self, setting_keys: List[str], 
                              timeout_per_setting: int = 15) -> Tuple[List[str], List[str]]:
        """
        Apply multiple Windows settings
        
        Args:
            setting_keys: List of setting keys to apply
            timeout_per_setting: Timeout per setting application
            
        Returns:
            Tuple of (successful_settings, failed_settings)
        """
        successful = []
        failed = []
        
        self.progress_callback("=== APPLYING ESSENTIAL SETTINGS ===")
        self.progress_callback(f"Applying {len(setting_keys)} settings...")
        self.progress_callback("")
        
        for setting_key in setting_keys:
            if self.apply_setting(setting_key, timeout_per_setting):
                successful.append(setting_key)
            else:
                failed.append(setting_key)
        
        self.progress_callback("")
        self.progress_callback("=== SETTINGS APPLICATION COMPLETE ===")
        self.progress_callback(f"Successfully applied {len(successful)} out of {len(setting_keys)} settings.")
        
        # Check if any settings require restarts
        explorer_restart_needed = False
        system_restart_needed = False
        
        for setting_key in successful:
            setting = self.SETTINGS_CATALOG[setting_key]
            if setting.requires_explorer_restart:
                explorer_restart_needed = True
            if setting.requires_restart:
                system_restart_needed = True
        
        if explorer_restart_needed or system_restart_needed:
            self.progress_callback("")
            if system_restart_needed:
                self.progress_callback("Note: Some changes require a system restart to take effect.")
            elif explorer_restart_needed:
                self.progress_callback("Note: Some changes require an Explorer restart to take effect.")
                self.progress_callback("To restart Explorer: Ctrl+Shift+Esc → Details → explorer.exe → End task → File → Run new task → explorer.exe")
        
        return successful, failed
    
    def restart_explorer(self) -> bool:
        """
        Restart Windows Explorer to apply changes
        
        Returns:
            bool: True if restart was successful
        """
        try:
            self.progress_callback("Restarting Windows Explorer to apply changes...")
            
            # Kill explorer
            subprocess.run("taskkill /f /im explorer.exe", 
                         shell=True, capture_output=True, timeout=10)
            
            # Start explorer
            subprocess.run("start explorer.exe", 
                         shell=True, capture_output=True, timeout=10)
            
            self.progress_callback("✓ Explorer restarted successfully")
            return True
            
        except Exception as e:
            self.progress_callback(f"⚠ Could not restart explorer automatically: {str(e)}")
            return False
    
    def create_settings_report(self, successful: List[str], 
                             failed: List[str]) -> Dict[str, Any]:
        """
        Create a detailed settings application report
        
        Args:
            successful: List of successfully applied setting keys
            failed: List of failed setting keys
            
        Returns:
            Dict containing detailed report
        """
        report = {
            "total_attempted": len(successful) + len(failed),
            "successful_count": len(successful),
            "failed_count": len(failed),
            "success_rate": len(successful) / (len(successful) + len(failed)) if (successful or failed) else 0,
            "applied_settings": [],
            "failed_settings": [],
            "restart_requirements": {
                "explorer_restart": False,
                "system_restart": False
            },
            "categories_modified": set(),
            "recommendations": []
        }
        
        # Analyze successful settings
        for setting_key in successful:
            setting = self.SETTINGS_CATALOG[setting_key]
            report["applied_settings"].append({
                "key": setting_key,
                "name": setting.name,
                "category": setting.category.value,
                "scope": setting.scope.value
            })
            report["categories_modified"].add(setting.category.value)
            
            if setting.requires_explorer_restart:
                report["restart_requirements"]["explorer_restart"] = True
            if setting.requires_restart:
                report["restart_requirements"]["system_restart"] = True
        
        # Analyze failed settings
        for setting_key in failed:
            if setting_key in self.SETTINGS_CATALOG:
                setting = self.SETTINGS_CATALOG[setting_key]
                report["failed_settings"].append({
                    "key": setting_key,
                    "name": setting.name,
                    "category": setting.category.value
                })
        
        # Convert set to list for JSON serialization
        report["categories_modified"] = list(report["categories_modified"])
        
        # Add recommendations
        if report["restart_requirements"]["system_restart"]:
            report["recommendations"].append("Restart your computer to ensure all changes take effect")
        elif report["restart_requirements"]["explorer_restart"]:
            report["recommendations"].append("Restart Windows Explorer to see interface changes")
        
        if failed:
            report["recommendations"].extend([
                "Ensure the application is running with administrator privileges",
                "Some settings may require manual configuration through Windows Settings",
                "Check that your Windows version supports the failed settings"
            ])
        
        return report


# Convenience functions
def get_settings_manager(progress_callback: Optional[Callable[[str], None]] = None) -> WindowsSettingsManager:
    """Get a configured WindowsSettingsManager instance"""
    return WindowsSettingsManager(progress_callback)


def apply_recommended_settings(progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[List[str], List[str]]:
    """
    Quick function to apply recommended Windows settings
    
    Args:
        progress_callback: Optional progress callback function
        
    Returns:
        Tuple of (successful_settings, failed_settings)
    """
    manager = WindowsSettingsManager(progress_callback)
    recommended = manager.get_recommended_settings()
    return manager.apply_multiple_settings(recommended)