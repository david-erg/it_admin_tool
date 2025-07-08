"""
UI widgets module for IT Admin Tool.

This module contains all the tab widgets and custom UI components
used throughout the application.
"""

from .software_tab import SoftwareTab
from .system_info_tab import SystemInfoTab
from .windows_setup_tab import WindowsSetupTab
from .file_ops_tab import FileOpsTab

__all__ = [
    'SoftwareTab',
    'SystemInfoTab', 
    'WindowsSetupTab',
    'FileOpsTab'
]
