"""
Core module for IT Admin Tool.

This module provides core functionality shared across the application including
configuration management, worker signals, utilities, and constants.
"""

from .config import ConfigManager
from .worker_signals import WorkerSignals, BaseWorker
from .utils import (
    check_admin_privileges,
    get_application_path,
    is_windows_platform,
    query_wmic,
    run_command_with_timeout,
    safe_get_env_var,
    format_bytes,
    validate_username,
    validate_password,
    escape_command_arg
)
from .constants import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_PRESETS,
    COMMON_BLOATWARE,
    RECOMMENDED_SETTINGS,
    ESSENTIAL_SETTINGS_COMMANDS,
    DEFAULT_COMMAND_TIMEOUT,
    CHOCOLATEY_INSTALL_TIMEOUT,
    PACKAGE_SEARCH_TIMEOUT,
    SYSTEM_INFO_TIMEOUT,
    PACKAGE_SEARCH_LIMIT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    THEME_COLORS,
    BLOATWARE_APPS,
    ESSENTIAL_SETTINGS,
    SETTINGS_FILE,
    PRESETS_FILE,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    HEADER_HEIGHT
)

__all__ = [
    'ConfigManager',
    'WorkerSignals',
    'BaseWorker',
    'check_admin_privileges',
    'get_application_path',
    'is_windows_platform',
    'query_wmic',
    'run_command_with_timeout',
    'safe_get_env_var',
    'format_bytes',
    'validate_username',
    'validate_password',
    'escape_command_arg',
    'APP_NAME',
    'APP_VERSION',
    'DEFAULT_PRESETS',
    'COMMON_BLOATWARE',
    'RECOMMENDED_SETTINGS',
    'ESSENTIAL_SETTINGS_COMMANDS',
    'DEFAULT_COMMAND_TIMEOUT',
    'CHOCOLATEY_INSTALL_TIMEOUT',
    'PACKAGE_SEARCH_TIMEOUT',
    'SYSTEM_INFO_TIMEOUT',
    'PACKAGE_SEARCH_LIMIT',
    'MIN_WINDOW_WIDTH',
    'MIN_WINDOW_HEIGHT',
    'THEME_COLORS',
    'BLOATWARE_APPS',
    'ESSENTIAL_SETTINGS',
    'SETTINGS_FILE',
    'PRESETS_FILE',
    'DEFAULT_WINDOW_WIDTH',
    'DEFAULT_WINDOW_HEIGHT',
    'HEADER_HEIGHT'
]