"""
Application constants and default configurations.

This module contains all static configuration data, default values,
and constants used throughout the IT Admin Tool.
"""

from typing import Dict, List

# Application Information
APP_NAME = "Admin's ToolBox - IT Administration Tool"
APP_VERSION = "2.1"
APP_ID = "AdminToolBox"

# File Names
SETTINGS_FILE = "settings.json"
PRESETS_FILE = "software_presets.json"

# UI Configuration
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 700
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
HEADER_HEIGHT = 50

# Timeout Values (seconds)
DEFAULT_COMMAND_TIMEOUT = 30
CHOCOLATEY_INSTALL_TIMEOUT = 300
PACKAGE_SEARCH_TIMEOUT = 60
SYSTEM_INFO_TIMEOUT = 30

# Default Software Presets
DEFAULT_PRESETS: Dict[str, List[str]] = {
    "Basic Office Setup": [
        "adobereader",
        "googlechrome",
        "firefox",
        "7zip",
        "notepadplusplus"
    ],
    "Developer Tools": [
        "git",
        "vscode",
        "nodejs",
        "python",
        "postman"
    ],
    "Media & Design": [
        "vlc",
        "gimp",
        "audacity",
        "blender",
        "obs-studio"
    ],
    "System Utilities": [
        "ccleaner",
        "malwarebytes",
        "teamviewer",
        "anydesk",
        "windirstat"
    ],
    "Gaming Setup": [
        "steam",
        "discord",
        "nvidia-geforce-experience",
        "origin",
        "epicgameslauncher"
    ],
    "Office 365 + Essential Tools": [
        "adobereader",
        "googlechrome",
        "7zip",
        "vlc",
        "teamviewer"
    ],
    "Web Development": [
        "vscode",
        "nodejs",
        "git",
        "googlechrome",
        "firefox",
        "postman",
        "filezilla"
    ],
    "Graphic Design Workstation": [
        "adobecreativecloud",
        "gimp",
        "inkscape",
        "blender",
        "vlc",
        "7zip"
    ],
    "Security Tools": [
        "malwarebytes",
        "ccleaner",
        "glasswire",
        "wireshark",
        "nmap",
        "procexp"
    ],
    "Remote Work Setup": [
        "teamviewer",
        "anydesk",
        "zoom",
        "skype",
        "slack",
        "discord",
        "googlechrome"
    ]
}

# Windows Bloatware Applications
BLOATWARE_APPS: Dict[str, str] = {
    "Microsoft.XboxApp": "Xbox Console Companion",
    "Microsoft.XboxGamingOverlay": "Xbox Gaming Overlay", 
    "Microsoft.XboxGameOverlay": "Xbox Game Overlay",
    "Microsoft.XboxIdentityProvider": "Xbox Identity Provider",
    "Microsoft.Xbox.TCUI": "Xbox TCUI",
    "Microsoft.ZuneMusic": "Groove Music",
    "Microsoft.ZuneVideo": "Movies & TV",
    "Microsoft.SkypeApp": "Skype",
    "Microsoft.MicrosoftSolitaireCollection": "Microsoft Solitaire",
    "Microsoft.MicrosoftOfficeHub": "Office Hub",
    "Microsoft.Office.OneNote": "OneNote",
    "Microsoft.People": "People",
    "Microsoft.WindowsCamera": "Camera",
    "Microsoft.windowscommunicationsapps": "Mail and Calendar",
    "Microsoft.BingWeather": "Weather",
    "Microsoft.BingNews": "News",
    "Microsoft.GetHelp": "Get Help",
    "Microsoft.Getstarted": "Tips",
    "Microsoft.MixedReality.Portal": "Mixed Reality Portal",
    "Microsoft.Microsoft3DViewer": "3D Viewer",
    "Microsoft.MSPaint": "Paint 3D",
    "Microsoft.WindowsFeedbackHub": "Feedback Hub",
    "Microsoft.YourPhone": "Your Phone",
    "Microsoft.MicrosoftStickyNotes": "Sticky Notes",
    "Microsoft.WindowsMaps": "Maps",
    "Microsoft.PowerAutomateDesktop": "Power Automate",
    "MicrosoftTeams": "Microsoft Teams",
    "Microsoft.Todos": "Microsoft To Do",
    "Clipchamp.Clipchamp": "Clipchamp",
    "Disney.37853FC22B2CE": "Disney+",
    "SpotifyAB.SpotifyMusic": "Spotify"
}

# Common Bloatware (most frequently removed)
COMMON_BLOATWARE: List[str] = [
    "Microsoft.XboxApp",
    "Microsoft.XboxGamingOverlay", 
    "Microsoft.XboxGameOverlay",
    "Microsoft.ZuneMusic",
    "Microsoft.ZuneVideo",
    "Microsoft.MicrosoftSolitaireCollection",
    "Microsoft.BingWeather",
    "Microsoft.BingNews",
    "Microsoft.GetHelp",
    "Microsoft.Getstarted",
    "Microsoft.MixedReality.Portal",
    "Microsoft.Microsoft3DViewer",
    "Microsoft.MSPaint",
    "Microsoft.YourPhone",
    "Disney.37853FC22B2CE",
    "Clipchamp.Clipchamp"
]

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
    "disable_notifications": "Disable non-essential notifications"
}

# Registry Commands for Essential Settings
ESSENTIAL_SETTINGS_COMMANDS: Dict[str, Dict[str, str]] = {
    "show_file_extensions": {
        "command": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v HideFileExt /t REG_DWORD /d 0 /f',
        "description": "Show file extensions"
    },
    "show_hidden_files": {
        "command": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced" /v Hidden /t REG_DWORD /d 1 /f',
        "description": "Show hidden files"
    },
    "disable_cortana": {
        "command": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Search" /v SearchboxTaskbarMode /t REG_DWORD /d 0 /f',
        "description": "Disable Cortana"
    },
    "disable_web_search": {
        "command": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Search" /v BingSearchEnabled /t REG_DWORD /d 0 /f',
        "description": "Disable web search"
    },
    "disable_telemetry": {
        "command": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection" /v AllowTelemetry /t REG_DWORD /d 0 /f',
        "description": "Disable telemetry"
    },
    "disable_consumer_features": {
        "command": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\CloudContent" /v DisableWindowsConsumerFeatures /t REG_DWORD /d 1 /f',
        "description": "Disable consumer features"
    },
    "disable_location_tracking": {
        "command": 'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\CapabilityAccessManager\\ConsentStore\\location" /v Value /t REG_SZ /d Deny /f',
        "description": "Disable location tracking"
    },
    "disable_advertising_id": {
        "command": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo" /v Enabled /t REG_DWORD /d 0 /f',
        "description": "Disable advertising ID"
    },
    "enable_dark_mode": {
        "command": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v AppsUseLightTheme /t REG_DWORD /d 0 /f',
        "description": "Enable dark mode"
    },
    "disable_lock_screen_ads": {
        "command": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager" /v RotatingLockScreenOverlayEnabled /t REG_DWORD /d 0 /f',
        "description": "Disable lock screen ads"
    },
    "disable_timeline": {
        "command": 'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System" /v EnableActivityFeed /t REG_DWORD /d 0 /f',
        "description": "Disable timeline"
    },
    "classic_right_click": {
        "command": 'reg add "HKCU\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32" /f',
        "description": "Enable classic right-click menu"
    },
    "taskbar_cleanup": {
        "command": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Search" /v SearchboxTaskbarMode /t REG_DWORD /d 0 /f & reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Feeds" /v ShellFeedsTaskbarViewMode /t REG_DWORD /d 2 /f',
        "description": "Clean up taskbar"
    },
    "disable_notifications": {
        "command": 'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\PushNotifications" /v ToastEnabled /t REG_DWORD /d 0 /f',
        "description": "Disable notifications"
    }
}

# Recommended Settings (subset of essential settings)
RECOMMENDED_SETTINGS: List[str] = [
    "show_file_extensions",
    "show_hidden_files", 
    "disable_cortana",
    "disable_web_search",
    "disable_telemetry",
    "disable_consumer_features",
    "disable_advertising_id",
    "disable_lock_screen_ads",
    "taskbar_cleanup"
]

# System Information Fields
SYSTEM_INFO_FIELDS = [
    "Device Name",
    "Serial Number",
    "Logged User Name",
    "Manufacturer",
    "Model",
    "CPU",
    "GPU",
    "RAM (GB)",
    "Storage",
    "OS Edition",
    "Anti-Virus",
    "Office Installed",
    "IP Address",
    "MAC Address",
    "Updated Time"
]

# Package Search Configuration
PACKAGE_SEARCH_LIMIT = 100
PACKAGE_TABLE_COLUMNS = ["Package", "Version", "Description"]
PACKAGE_TABLE_INITIAL_WIDTHS = [200, 100]  # Package and Version columns

# Theme Configuration
THEME_COLORS = {
    "dark": {
        "primary": "#2b2b2b",
        "secondary": "#404040",
        "accent": "#0078d4",
        "text": "#ffffff",
        "border": "#555555"
    },
    "light": {
        "primary": "#ffffff",
        "secondary": "#f0f0f0",
        "accent": "#0078d4",
        "text": "#000000",
        "border": "#cccccc"
    }
}