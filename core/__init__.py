"""
Core module for IT Admin Tool.

This module provides core functionality shared across the application including
configuration management, worker signals, utilities, and constants.
"""

from .config import ConfigManager
from .worker_signals import WorkerSignals
from .utils import (
    check_admin_privileges,
    get_application_path,
    is_windows_platform,
    query_wmic,
    run_command_with_timeout
)
from .constants import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_PRESETS,
    COMMON_BLOATWARE,
    RECOMMENDED_SETTINGS,
    ESSENTIAL_SETTINGS_COMMANDS
)

__all__ = [
    'ConfigManager',
    'WorkerSignals', 
    'check_admin_privileges',
    'get_application_path',
    'is_windows_platform',
    'query_wmic',
    'run_command_with_timeout',
    'APP_NAME',
    'APP_VERSION',
    'DEFAULT_PRESETS',
    'COMMON_BLOATWARE',
    'RECOMMENDED_SETTINGS',
    'ESSENTIAL_SETTINGS_COMMANDS'
]