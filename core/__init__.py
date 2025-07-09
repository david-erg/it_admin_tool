"""
Core module for IT Admin Tool.

This module provides core functionality shared across the application including
configuration management, worker signals, utilities, and constants.
"""

from .config import ConfigManager
from .worker_signals import (
    WorkerSignals, 
    BaseWorker, 
    CLIWorker,
    create_worker,
    is_gui_mode,
    get_signal_info
)
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
    # Application Info
    APP_NAME,
    APP_VERSION,
    
    # File Names
    SETTINGS_FILE,
    PRESETS_FILE,
    
    # Timeouts
    DEFAULT_COMMAND_TIMEOUT,
    CHOCOLATEY_INSTALL_TIMEOUT,
    PACKAGE_SEARCH_TIMEOUT,
    SYSTEM_INFO_TIMEOUT,
    PACKAGE_SEARCH_LIMIT,
    
    # UI Constants
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    HEADER_HEIGHT,
    THEME_COLORS,
    
    # Application Data
    DEFAULT_PRESETS,
    BLOATWARE_APPS,
    COMMON_BLOATWARE,  # Legacy alias
    ESSENTIAL_SETTINGS,
    ESSENTIAL_SETTINGS_COMMANDS,
    RECOMMENDED_SETTINGS,
    POWERSHELL_COMMANDS,
    
    # Messages
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    
    # File Formats and Extensions
    SUPPORTED_EXPORT_FORMATS,
    BACKUP_FILE_EXTENSION,
    LOG_FILE_EXTENSION,
    
    # Validation
    VALID_PACKAGE_NAME_PATTERN,
    VALID_USERNAME_PATTERN,
    
    # Directories
    DEFAULT_BACKUP_DIR,
    DEFAULT_LOGS_DIR,
    DEFAULT_EXPORTS_DIR,
    DEFAULT_CONFIG_DIR,
    
    # Limits
    MAX_PACKAGE_SEARCH_RESULTS,
    MAX_CONCURRENT_INSTALLATIONS,
    MAX_LOG_FILE_SIZE_MB,
    MAX_BACKUP_AGE_DAYS
)

__all__ = [
    # Configuration
    'ConfigManager',
    
    # Worker System
    'WorkerSignals',
    'BaseWorker',
    'CLIWorker',
    'create_worker',
    'is_gui_mode',
    'get_signal_info',
    
    # Utilities
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
    
    # Application Info
    'APP_NAME',
    'APP_VERSION',
    
    # File Names
    'SETTINGS_FILE',
    'PRESETS_FILE',
    
    # Timeouts
    'DEFAULT_COMMAND_TIMEOUT',
    'CHOCOLATEY_INSTALL_TIMEOUT',
    'PACKAGE_SEARCH_TIMEOUT',
    'SYSTEM_INFO_TIMEOUT',
    'PACKAGE_SEARCH_LIMIT',
    
    # UI Constants
    'MIN_WINDOW_WIDTH',
    'MIN_WINDOW_HEIGHT',
    'DEFAULT_WINDOW_WIDTH',
    'DEFAULT_WINDOW_HEIGHT',
    'HEADER_HEIGHT',
    'THEME_COLORS',
    
    # Application Data
    'DEFAULT_PRESETS',
    'BLOATWARE_APPS',
    'COMMON_BLOATWARE',
    'ESSENTIAL_SETTINGS',
    'ESSENTIAL_SETTINGS_COMMANDS',
    'RECOMMENDED_SETTINGS',
    'POWERSHELL_COMMANDS',
    
    # Messages
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',
    
    # File Formats
    'SUPPORTED_EXPORT_FORMATS',
    'BACKUP_FILE_EXTENSION',
    'LOG_FILE_EXTENSION',
    
    # Validation
    'VALID_PACKAGE_NAME_PATTERN',
    'VALID_USERNAME_PATTERN',
    
    # Directories
    'DEFAULT_BACKUP_DIR',
    'DEFAULT_LOGS_DIR',
    'DEFAULT_EXPORTS_DIR',
    'DEFAULT_CONFIG_DIR',
    
    # Limits
    'MAX_PACKAGE_SEARCH_RESULTS',
    'MAX_CONCURRENT_INSTALLATIONS',
    'MAX_LOG_FILE_SIZE_MB',
    'MAX_BACKUP_AGE_DAYS'
]

__version__ = APP_VERSION