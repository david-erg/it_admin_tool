"""
UI module for IT Admin Tool.

This module provides all user interface components including the main window,
theme management, tab widgets, and dialogs.
"""

from .main_window import MainWindow
from .themes import ThemeManager
from .widgets import (
    SoftwareTab,
    SystemInfoTab, 
    WindowsSetupTab,
    FileOpsTab
)
from .dialogs import ConfirmationDialogs

__all__ = [
    'MainWindow',
    'ThemeManager',
    'SoftwareTab',
    'SystemInfoTab',
    'WindowsSetupTab', 
    'FileOpsTab',
    'ConfirmationDialogs'
]
