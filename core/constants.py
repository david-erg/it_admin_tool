"""
Constants for the IT Admin Tool.

This module defines all application constants including UI dimensions,
timeout values, default settings, and configuration file names.
"""

from typing import Dict, List

# Application Information
APP_NAME = "Admin's ToolBox"
APP_VERSION = "2.1"

# File Names
SETTINGS_FILE = "settings.json"
PRESETS_FILE = "presets.json"

# Timeout Constants (in seconds)
DEFAULT_COMMAND_TIMEOUT = 30
CHOCOLATEY_INSTALL_TIMEOUT = 600  # 10 minutes
PACKAGE_SEARCH_TIMEOUT = 60
SYSTEM_INFO_TIMEOUT = 45
PACKAGE_SEARCH_LIMIT = 100

# UI Constants
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
HEADER_HEIGHT = 60

# Theme Colors
THEME_COLORS = {
    "primary": "#2196F3",
    "secondary": "#FFC107",
    "success": "#4CAF50",
    "danger": "#F44336",
    "warning": "#FF9800",
    "info": "#00BCD4",
    "light": "#F8F9FA",
    "dark": "#343A40",
    "background_light": "#FFFFFF",
    "background_dark": "#2B2B2B",
    "text_light": "#000000",
    "text_dark": "#FFFFFF",
    "border": "#DEE2E6",
    "hover": "#E3F2FD"
}

# Default Software Presets
DEFAULT_PRESETS: Dict[str, List[str]] = {
    "Basic Office Setup": [
        "googlechrome",
        "firefox",
        "7zip",
        "notepadplusplus",
        "vlc",
        "adobe-acrobat-reader-dc",
        "microsoft-office-deployment"
    ],
    "Developer Essentials": [
        "git",
        "vscode",
        "python",
        "nodejs",
        "docker-desktop",
        "postman",
        "github-desktop",
        "visualstudio2022community"
    ],
    "System Administration": [
        "sysinternals",
        "putty",
        "wireshark",
        "teamviewer",
        "powershell-core",
        "openssh",
        "curl",
        "wget"
    ],
    "Media & Graphics": [
        "vlc",
        "gimp",
        "inkscape",
        "audacity",
        "obs-studio",
        "handbrake",
        "paint.net",
        "blender"
    ],
    "Gaming Essentials": [
        "steam",
        "epicgameslauncher",
        "discord",
        "spotify",
        "nvidia-geforce-experience",
        "razer-synapse-3",
        "msi-afterburner"
    ],
    "Security & Privacy": [
        "malwarebytes",
        "ccleaner",
        "bitwarden",
        "tor-browser",
        "veracrypt",
        "windirstat",
        "revo-uninstaller"
    ]
}

# Common Bloatware Applications
BLOATWARE_APPS: List[str] = [
    "Microsoft.549981C3F5F10",  # Cortana
    "Microsoft.BingWeather",
    "Microsoft.BingNews",
    "Microsoft.GetHelp",
    "Microsoft.Getstarted",
    "Microsoft.MixedReality.Portal",
    "Microsoft.Microsoft3DViewer",
    "Microsoft.MSPaint",
    "Microsoft.YourPhone",
    "Microsoft.WindowsFeedbackHub",
    "Microsoft.WindowsMaps",
    "Microsoft.WindowsSoundRecorder",
    "Microsoft.Xbox.TCUI",
    "Microsoft.XboxApp",
    "Microsoft.XboxGameOverlay",
    "Microsoft.XboxGamingOverlay",
    "Microsoft.XboxIdentityProvider",
    "Microsoft.XboxSpeechToTextOverlay",
    "Microsoft.ZuneMusic",
    "Microsoft.ZuneVideo",
    "Disney.37853FC22B2CE",
    "Clipchamp.Clipchamp",
    "Microsoft.Todos",
    "Microsoft.PowerAutomateDesktop",
    "SpotifyAB.SpotifyMusic",
    "king.com.CandyCrushSaga",
    "king.com.CandyCrushSodaSaga",
    "FACEBOOK.317180B0BB486",
    "TikTok.TikTok",
    "BytedancePte.Ltd.TikTok"
]

# Legacy alias for compatibility
COMMON_BLOATWARE = BLOATWARE_APPS

# Essential Windows Settings
ESSENTIAL_SETTINGS: Dict[str, str] = {
    "show_file_extensions": "Show file extensions in File Explorer",
    "show_hidden_files": "Show hidden files and folders",
    "disable_cortana": "Disable Cortana",
    "disable_web_search": "Disable web search in Start Menu",
    "disable_telemetry": "Disable Windows telemetry and data collection",
    "disable_consumer_features": "Disable consumer features (ads, suggestions)",
    "disable_location_tracking": "Disable location tracking",
    "disable_advertising_id": "Disable advertising ID",
    "enable_dark_mode": "Enable Windows dark mode",
    "disable_lock_screen_ads": "Disable lock screen ads and tips",
    "disable_timeline": "Disable Windows Timeline",
    "classic_right_click": "Enable classic right-click context menu (Windows 11)",
    "taskbar_cleanup": "Remove weather, news, task view from taskbar",
    "disable_notifications": "Disable non-essential notifications",
    "disable_startup_boost": "Disable Windows startup boost",
    "privacy_settings": "Configure privacy settings for better security",
    "disable_background_apps": "Disable unnecessary background apps"
}

# Registry Commands for Essential Settings
ESSENTIAL_SETTINGS_COMMANDS: Dict[str, Dict[str, str]] = {
    "show_file_extensions": {
        "command": r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v HideFileExt /t REG_DWORD /d 0 /f',
        "description": "Show file extensions"
    },
    "show_hidden_files": {
        "command": r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v Hidden /t REG_DWORD /d 1 /f',
        "description": "Show hidden files"
    },
    "disable_cortana": {
        "command": r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v SearchboxTaskbarMode /t REG_DWORD /d 0 /f',
        "description": "Disable Cortana search box"
    },
    "disable_web_search": {
        "command": r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v BingSearchEnabled /t REG_DWORD /d 0 /f',
        "description": "Disable web search in Start Menu"
    },
    "disable_telemetry": {
        "command": r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
        "description": "Disable Windows telemetry"
    },
    "disable_consumer_features": {
        "command": r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\CloudContent" /v DisableWindowsConsumerFeatures /t REG_DWORD /d 1 /f',
        "description": "Disable consumer features"
    },
    "disable_location_tracking": {
        "command": r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors" /v DisableLocation /t REG_DWORD /d 1 /f',
        "description": "Disable location tracking"
    },
    "disable_advertising_id": {
        "command": r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\AdvertisingInfo" /v DisabledByGroupPolicy /t REG_DWORD /d 1 /f',
        "description": "Disable advertising ID"
    },
    "enable_dark_mode": {
        "command": r'reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v AppsUseLightTheme /t REG_DWORD /d 0 /f',
        "description": "Enable dark mode for apps"
    },
    "disable_lock_screen_ads": {
        "command": r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" /v RotatingLockScreenOverlayEnabled /t REG_DWORD /d 0 /f',
        "description": "Disable lock screen ads"
    },
    "disable_timeline": {
        "command": r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" /v EnableActivityFeed /t REG_DWORD /d 0 /f',
        "description": "Disable Windows Timeline"
    },
    "classic_right_click": {
        "command": r'reg add "HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" /f',
        "description": "Enable classic right-click menu (Windows 11)"
    },
    "taskbar_cleanup": {
        "command": r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Search" /v SearchboxTaskbarMode /t REG_DWORD /d 0 /f',
        "description": "Clean up taskbar elements"
    },
    "disable_notifications": {
        "command": r'reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\PushNotifications" /v ToastEnabled /t REG_DWORD /d 0 /f',
        "description": "Disable non-essential notifications"
    },
    "disable_startup_boost": {
        "command": r'reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" /v EnableSuperfetch /t REG_DWORD /d 0 /f',
        "description": "Disable startup boost"
    },
    "privacy_settings": {
        "command": r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\AppPrivacy" /v LetAppsAccessAccountInfo /t REG_DWORD /d 2 /f',
        "description": "Configure privacy settings"
    },
    "disable_background_apps": {
        "command": r'reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" /v GlobalUserDisabled /t REG_DWORD /d 1 /f',
        "description": "Disable background apps"
    }
}

# Recommended Settings (subset of essential settings)
RECOMMENDED_SETTINGS: List[str] = [
    "show_file_extensions",
    "show_hidden_files",
    "disable_cortana",
    "disable_telemetry",
    "disable_consumer_features",
    "disable_advertising_id",
    "disable_lock_screen_ads",
    "privacy_settings"
]

# PowerShell Commands for complex operations
POWERSHELL_COMMANDS: Dict[str, str] = {
    "get_installed_programs": "Get-WmiObject -Class Win32_Product | Select-Object Name, Version, Vendor | Sort-Object Name",
    "get_startup_programs": "Get-WmiObject Win32_StartupCommand | Select-Object Name, Command, Location | Sort-Object Name",
    "get_services": "Get-Service | Select-Object Name, Status, StartType | Sort-Object Name",
    "get_network_adapters": "Get-NetAdapter | Select-Object Name, Status, LinkSpeed | Sort-Object Name",
    "get_disk_info": "Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, Size, FreeSpace, FileSystem",
    "get_system_info": "Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, TotalPhysicalMemory"
}

# Error Messages
ERROR_MESSAGES: Dict[str, str] = {
    "admin_required": "Administrator privileges are required for this operation.",
    "chocolatey_not_found": "Chocolatey package manager is not installed.",
    "internet_required": "Internet connection is required for this operation.",
    "file_not_found": "The specified file could not be found.",
    "invalid_path": "The specified path is invalid or inaccessible.",
    "operation_cancelled": "Operation was cancelled by the user.",
    "unexpected_error": "An unexpected error occurred. Please check the logs for details."
}

# Success Messages  
SUCCESS_MESSAGES: Dict[str, str] = {
    "operation_complete": "Operation completed successfully.",
    "packages_installed": "All packages were installed successfully.",
    "settings_applied": "Settings have been applied successfully.",
    "backup_created": "Backup created successfully.",
    "export_complete": "Export completed successfully."
}

# File Extensions
SUPPORTED_EXPORT_FORMATS = ['.csv', '.json', '.html', '.txt']
BACKUP_FILE_EXTENSION = '.backup'
LOG_FILE_EXTENSION = '.log'

# Validation Patterns
VALID_PACKAGE_NAME_PATTERN = r'^[a-zA-Z0-9\-\._]+$'
VALID_USERNAME_PATTERN = r'^[a-zA-Z0-9\-\._]+$'

# Default Directories
DEFAULT_BACKUP_DIR = "backups"
DEFAULT_LOGS_DIR = "logs"
DEFAULT_EXPORTS_DIR = "exports"
DEFAULT_CONFIG_DIR = "config"

# Application Limits
MAX_PACKAGE_SEARCH_RESULTS = 500
MAX_CONCURRENT_INSTALLATIONS = 3
MAX_LOG_FILE_SIZE_MB = 10
MAX_BACKUP_AGE_DAYS = 30