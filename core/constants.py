"""
Core Constants for IT Admin Tool

Contains all application constants, configuration values, and shared data.
GUI-only version with simplified structure.
"""

from pathlib import Path
from typing import Dict, List, Set
import re

# =============================================================================
# APPLICATION INFO
# =============================================================================

APP_NAME = "Admin's ToolBox"
APP_VERSION = "3.0"
APP_DESCRIPTION = "IT Administration Tool for Windows"

# =============================================================================
# FILE CONFIGURATION
# =============================================================================

SETTINGS_FILE = "settings.json"
PRESETS_FILE = "presets.json"
LOG_FILE = "admin_toolbox.log"

# =============================================================================
# TIMEOUTS (seconds)
# =============================================================================

DEFAULT_COMMAND_TIMEOUT = 30
CHOCOLATEY_INSTALL_TIMEOUT = 300  # 5 minutes for package installation
PACKAGE_SEARCH_TIMEOUT = 15
SYSTEM_INFO_TIMEOUT = 45
WMI_QUERY_TIMEOUT = 20

# =============================================================================
# UI CONFIGURATION
# =============================================================================

# Window sizing
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 700
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800

# Layout
HEADER_HEIGHT = 60
TAB_HEIGHT = 40
BUTTON_HEIGHT = 35
SPACING_SMALL = 5
SPACING_MEDIUM = 10
SPACING_LARGE = 20

# Theme colors
THEME_COLORS = {
    'primary': '#2563eb',      # Blue
    'secondary': '#64748b',    # Slate
    'success': '#059669',      # Green
    'warning': '#d97706',      # Orange
    'error': '#dc2626',        # Red
    'background': '#f8fafc',   # Light gray
    'surface': '#ffffff',      # White
    'text_primary': '#1e293b', # Dark gray
    'text_secondary': '#64748b' # Medium gray
}

# =============================================================================
# PACKAGE MANAGEMENT
# =============================================================================

PACKAGE_SEARCH_LIMIT = 50
MAX_PACKAGE_SEARCH_RESULTS = 100
MAX_CONCURRENT_INSTALLATIONS = 3

# Chocolatey configuration
CHOCOLATEY_SOURCE = "https://community.chocolatey.org/api/v2"
CHOCOLATEY_INSTALL_ARGS = [
    "--yes",
    "--no-progress", 
    "--ignore-checksums"
]

# =============================================================================
# FILE OPERATIONS
# =============================================================================

# File size limits (bytes)
MAX_SINGLE_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
MAX_TOTAL_COPY_SIZE = 50 * 1024 * 1024 * 1024   # 50GB

# File patterns
BACKUP_FILE_EXTENSION = ".backup"
LOG_FILE_EXTENSION = ".log"
TEMP_FILE_PREFIX = "admin_toolbox_"

# Supported formats
SUPPORTED_EXPORT_FORMATS = [".json", ".csv", ".txt", ".xml"]

# =============================================================================
# VALIDATION PATTERNS
# =============================================================================

VALID_PACKAGE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\-\._]+$')
VALID_USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9\-\._@]+$')
VALID_FILENAME_PATTERN = re.compile(r'^[^<>:"/\\|?*\x00-\x1f]+$')

# =============================================================================
# DIRECTORY CONFIGURATION  
# =============================================================================

DEFAULT_BACKUP_DIR = "Backups"
DEFAULT_LOGS_DIR = "Logs"
DEFAULT_EXPORTS_DIR = "Exports"
DEFAULT_CONFIG_DIR = "Config"
DEFAULT_TEMP_DIR = "Temp"

# =============================================================================
# SOFTWARE PRESETS
# =============================================================================

DEFAULT_PRESETS = {
    "Essential": [
        "7zip",
        "googlechrome", 
        "notepadplusplus",
        "vlc",
        "firefox"
    ],
    "Development": [
        "git",
        "vscode",
        "python",
        "nodejs",
        "docker-desktop"
    ],
    "Media": [
        "vlc",
        "handbrake",
        "audacity",
        "gimp",
        "obs-studio"
    ],
    "Office": [
        "libreoffice",
        "adobereader",
        "zoom",
        "teamviewer",
        "skype"
    ]
}

# =============================================================================
# WINDOWS BLOATWARE
# =============================================================================

COMMON_BLOATWARE = [
    # Microsoft Apps
    "Microsoft.3DBuilder",
    "Microsoft.Appconnector",
    "Microsoft.BingFinance", 
    "Microsoft.BingNews",
    "Microsoft.BingSports",
    "Microsoft.BingWeather",
    "Microsoft.GetHelp",
    "Microsoft.Getstarted",
    "Microsoft.Messaging",
    "Microsoft.Microsoft3DViewer",
    "Microsoft.MicrosoftOfficeHub",
    "Microsoft.MicrosoftSolitaireCollection",
    "Microsoft.MixedReality.Portal",
    "Microsoft.Office.OneNote",
    "Microsoft.People",
    "Microsoft.Print3D",
    "Microsoft.SkypeApp",
    "Microsoft.Wallet",
    "Microsoft.WindowsAlarms",
    "Microsoft.WindowsCamera",
    "microsoft.windowscommunicationsapps",
    "Microsoft.WindowsMaps",
    "Microsoft.WindowsPhone",
    "Microsoft.WindowsSoundRecorder",
    "Microsoft.Xbox.TCUI",
    "Microsoft.XboxApp",
    "Microsoft.XboxGameOverlay",
    "Microsoft.XboxSpeechToTextOverlay",
    "Microsoft.YourPhone",
    "Microsoft.ZuneMusic",
    "Microsoft.ZuneVideo",
    
    # Third-party bloatware
    "CandyCrush",
    "Facebook",
    "Instagram", 
    "TikTok",
    "Twitter",
    "Netflix",
    "Spotify",
    "Disney",
    "Xbox",
    "LinkedInforWindows"
]

# Legacy alias for backwards compatibility
BLOATWARE_APPS = {app: app.replace("Microsoft.", "").replace(".", " ") for app in COMMON_BLOATWARE}

# =============================================================================
# WINDOWS SETTINGS
# =============================================================================

ESSENTIAL_SETTINGS = {
    "disable_telemetry": "Disable Windows telemetry and data collection",
    "disable_cortana": "Disable Cortana virtual assistant",
    "show_file_extensions": "Show file extensions in File Explorer",
    "show_hidden_files": "Show hidden files and folders",
    "disable_auto_updates": "Disable automatic Windows updates",
    "disable_defender_cloud": "Disable Windows Defender cloud protection",
    "disable_location_tracking": "Disable location tracking",
    "disable_advertising_id": "Disable advertising ID",
    "disable_suggested_apps": "Disable suggested apps in Start Menu",
    "optimize_visual_effects": "Optimize visual effects for performance",
    "disable_search_web": "Disable web search in Start Menu",
    "disable_timeline": "Disable Windows Timeline feature",
    "set_privacy_defaults": "Configure privacy settings to recommended defaults",
    "disable_activity_history": "Disable activity history collection"
}

RECOMMENDED_SETTINGS = [
    "disable_telemetry",
    "show_file_extensions", 
    "show_hidden_files",
    "disable_advertising_id",
    "disable_suggested_apps",
    "set_privacy_defaults"
]

RECOMMENDED_REGISTRY_TWEAKS = {
    # Disable telemetry
    r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection": {
        "AllowTelemetry": 0
    },
    # Disable Cortana
    r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search": {
        "AllowCortana": 0
    },
    # Disable automatic updates restart
    r"HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU": {
        "NoAutoRebootWithLoggedOnUsers": 1
    },
    # Show file extensions
    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced": {
        "HideFileExt": 0
    },
    # Show hidden files
    r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced": {
        "Hidden": 1
    }
}

# =============================================================================
# ERROR MESSAGES
# =============================================================================

ERROR_MESSAGES = {
    'admin_required': "Administrator privileges required for this operation.",
    'chocolatey_not_found': "Chocolatey package manager not found. Please install Chocolatey first.",
    'package_not_found': "Package not found in repository.",
    'installation_failed': "Package installation failed. Check logs for details.",
    'file_not_found': "File or directory not found.",
    'permission_denied': "Permission denied. Check file permissions.",
    'invalid_path': "Invalid file path specified.",
    'network_error': "Network connection error. Check internet connectivity.",
    'wmi_query_failed': "WMI query failed. System information may be incomplete.",
    'registry_access_denied': "Registry access denied. Administrator privileges required."
}

SUCCESS_MESSAGES = {
    'package_installed': "Package installed successfully.",
    'package_removed': "Package removed successfully.",
    'settings_applied': "Settings applied successfully.",
    'bloatware_removed': "Bloatware removal completed.",
    'files_copied': "Files copied successfully.",
    'backup_created': "Backup created successfully.",
    'system_info_gathered': "System information gathered successfully."
}

# =============================================================================
# LIMITS AND CONSTRAINTS
# =============================================================================

MAX_LOG_FILE_SIZE_MB = 10
MAX_BACKUP_AGE_DAYS = 30
MAX_PARALLEL_OPERATIONS = 5
MAX_RETRY_ATTEMPTS = 3

# System requirements
MIN_PYTHON_VERSION = (3, 10)
MIN_WINDOWS_VERSION = "10"
MIN_FREE_DISK_SPACE_GB = 1

# =============================================================================
# FEATURE FLAGS
# =============================================================================

ENABLE_SYSTEM_INFO = True
ENABLE_SOFTWARE_MANAGEMENT = True
ENABLE_FILE_OPERATIONS = True
ENABLE_WINDOWS_SETUP = True
ENABLE_ADVANCED_LOGGING = True
ENABLE_AUTO_BACKUP = True