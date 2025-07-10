"""
Core Module for IT Admin Tool

This module provides the foundational components for the IT Administration Tool
including configuration management, worker threading, utilities, and constants.

GUI-only version with simplified architecture and robust error handling.
"""

# Version information
__version__ = "3.0"
__author__ = "IT Admin Tool Team"
__description__ = "Core components for IT Administration Tool"

# Core imports
from .constants import (
    # Application Info
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    
    # File Configuration
    SETTINGS_FILE,
    PRESETS_FILE,
    LOG_FILE,
    
    # Timeouts
    DEFAULT_COMMAND_TIMEOUT,
    CHOCOLATEY_INSTALL_TIMEOUT,
    PACKAGE_SEARCH_TIMEOUT,
    SYSTEM_INFO_TIMEOUT,
    WMI_QUERY_TIMEOUT,
    
    # UI Configuration
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    HEADER_HEIGHT,
    TAB_HEIGHT,
    BUTTON_HEIGHT,
    SPACING_SMALL,
    SPACING_MEDIUM,
    SPACING_LARGE,
    THEME_COLORS,
    
    # Package Management
    PACKAGE_SEARCH_LIMIT,
    MAX_PACKAGE_SEARCH_RESULTS,
    MAX_CONCURRENT_INSTALLATIONS,
    CHOCOLATEY_SOURCE,
    CHOCOLATEY_INSTALL_ARGS,
    
    # File Operations
    MAX_SINGLE_FILE_SIZE,
    MAX_TOTAL_COPY_SIZE,
    BACKUP_FILE_EXTENSION,
    LOG_FILE_EXTENSION,
    TEMP_FILE_PREFIX,
    SUPPORTED_EXPORT_FORMATS,
    
    # Validation Patterns
    VALID_PACKAGE_NAME_PATTERN,
    VALID_USERNAME_PATTERN,
    VALID_FILENAME_PATTERN,
    
    # Directories
    DEFAULT_BACKUP_DIR,
    DEFAULT_LOGS_DIR,
    DEFAULT_EXPORTS_DIR,
    DEFAULT_CONFIG_DIR,
    DEFAULT_TEMP_DIR,
    
    # Data
    DEFAULT_PRESETS,
    COMMON_BLOATWARE,
    BLOATWARE_APPS,
    ESSENTIAL_SETTINGS,
    RECOMMENDED_REGISTRY_TWEAKS,
    
    # Messages
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    
    # Limits
    MAX_LOG_FILE_SIZE_MB,
    MAX_BACKUP_AGE_DAYS,
    MAX_PARALLEL_OPERATIONS,
    MAX_RETRY_ATTEMPTS,
    MIN_PYTHON_VERSION,
    MIN_WINDOWS_VERSION,
    MIN_FREE_DISK_SPACE_GB,
    
    # Feature Flags
    ENABLE_SYSTEM_INFO,
    ENABLE_SOFTWARE_MANAGEMENT,
    ENABLE_FILE_OPERATIONS,
    ENABLE_WINDOWS_SETUP,
    ENABLE_ADVANCED_LOGGING,
    ENABLE_AUTO_BACKUP
)

from .utils import (
    # System Information
    is_windows_platform,
    check_admin_privileges,
    get_application_path,
    get_system_info,
    
    # Command Execution
    run_command_with_timeout,
    query_wmic,
    safe_get_env_var,
    
    # Validation
    validate_username,
    validate_password,
    validate_filename,
    validate_path,
    
    # Utilities
    format_bytes,
    escape_command_arg,
    sanitize_filename,
    get_unique_filename,
    
    # Configuration Helpers
    load_json_config,
    save_json_config,
    
    # Logging
    setup_logging,
    get_error_message
)

from .worker_signals import (
    # Core Classes
    WorkerSignals,
    BaseWorker,
    WorkerThread,
    WorkerManager,
    
    # Enums
    # (None in this version)
    
    # Utility Functions
    create_worker_thread,
    connect_worker_signals,
    safe_emit_signal,
    is_gui_available,
    ensure_gui_thread
)

from .config import (
    # Configuration Classes
    ConfigManager,
    AppConfig,
    WindowSettings,
    ApplicationSettings,
    ChocolateySettings,
    FileOperationSettings,
    SystemInfoSettings,
    
    # Enums
    ThemeMode,
    LogLevel
)

# Module-level convenience functions
def get_version() -> str:
    """Get core module version."""
    return __version__

def get_app_info() -> dict:
    """Get application information."""
    return {
        'name': APP_NAME,
        'version': APP_VERSION,
        'description': APP_DESCRIPTION,
        'core_version': __version__
    }

def initialize_core(config_dir=None, log_file=None, log_level=None) -> tuple:
    """
    Initialize core components.
    
    Args:
        config_dir: Optional custom configuration directory
        log_file: Optional log file path
        log_level: Optional logging level
        
    Returns:
        tuple: (config_manager, worker_manager, success)
    """
    try:
        # Setup logging
        if log_file is None:
            app_path = get_application_path()
            log_file = app_path / "logs" / LOG_FILE
        
        if log_level is None:
            import logging
            log_level = logging.INFO
        
        setup_logging(log_file, log_level)
        
        # Initialize configuration manager
        config_manager = ConfigManager(config_dir)
        
        # Initialize worker manager
        worker_manager = WorkerManager()
        
        # Log initialization
        import logging
        logging.info(f"Core module initialized successfully")
        logging.info(f"Application: {APP_NAME} v{APP_VERSION}")
        logging.info(f"Core version: {__version__}")
        logging.info(f"Platform: {get_system_info()['platform']}")
        logging.info(f"Admin privileges: {check_admin_privileges()}")
        
        return config_manager, worker_manager, True
        
    except Exception as e:
        # Basic error logging if logging setup failed
        print(f"ERROR: Failed to initialize core module: {e}")
        return None, None, False

def cleanup_core(worker_manager=None) -> None:
    """
    Cleanup core components.
    
    Args:
        worker_manager: Optional worker manager to cleanup
    """
    try:
        import logging
        logging.info("Cleaning up core module...")
        
        # Stop all workers
        if worker_manager:
            worker_manager.stop_all_workers()
        
        logging.info("Core module cleanup completed")
        
    except Exception as e:
        print(f"ERROR: Failed to cleanup core module: {e}")

# Module validation
def validate_core_environment() -> list:
    """
    Validate that the core environment is properly set up.
    
    Returns:
        list: List of validation issues (empty if valid)
    """
    issues = []
    
    try:
        # Check platform
        if not is_windows_platform():
            issues.append("Not running on Windows platform")
        
        # Check Python version
        import sys
        if sys.version_info < MIN_PYTHON_VERSION:
            issues.append(f"Python version too old (requires {MIN_PYTHON_VERSION})")
        
        # Check required modules
        required_modules = ['PySide6', 'pathlib', 'json', 'logging']
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                issues.append(f"Required module not available: {module}")
        
        # Check application path
        try:
            app_path = get_application_path()
            if not app_path.exists():
                issues.append(f"Application path does not exist: {app_path}")
        except Exception as e:
            issues.append(f"Cannot determine application path: {e}")
        
        # Check disk space
        try:
            import shutil
            app_path = get_application_path()
            free_space = shutil.disk_usage(app_path).free
            free_gb = free_space / (1024**3)
            if free_gb < MIN_FREE_DISK_SPACE_GB:
                issues.append(f"Insufficient disk space: {free_gb:.1f}GB (requires {MIN_FREE_DISK_SPACE_GB}GB)")
        except Exception as e:
            issues.append(f"Cannot check disk space: {e}")
        
    except Exception as e:
        issues.append(f"Environment validation error: {e}")
    
    return issues

# Export all public components
__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__description__',
    
    # Constants
    'APP_NAME',
    'APP_VERSION', 
    'APP_DESCRIPTION',
    'SETTINGS_FILE',
    'PRESETS_FILE',
    'LOG_FILE',
    'DEFAULT_COMMAND_TIMEOUT',
    'CHOCOLATEY_INSTALL_TIMEOUT',
    'PACKAGE_SEARCH_TIMEOUT',
    'SYSTEM_INFO_TIMEOUT',
    'WMI_QUERY_TIMEOUT',
    'MIN_WINDOW_WIDTH',
    'MIN_WINDOW_HEIGHT',
    'DEFAULT_WINDOW_WIDTH',
    'DEFAULT_WINDOW_HEIGHT',
    'HEADER_HEIGHT',
    'TAB_HEIGHT',
    'BUTTON_HEIGHT',
    'SPACING_SMALL',
    'SPACING_MEDIUM',
    'SPACING_LARGE',
    'THEME_COLORS',
    'PACKAGE_SEARCH_LIMIT',
    'MAX_PACKAGE_SEARCH_RESULTS',
    'MAX_CONCURRENT_INSTALLATIONS',
    'CHOCOLATEY_SOURCE',
    'CHOCOLATEY_INSTALL_ARGS',
    'MAX_SINGLE_FILE_SIZE',
    'MAX_TOTAL_COPY_SIZE',
    'BACKUP_FILE_EXTENSION',
    'LOG_FILE_EXTENSION',
    'TEMP_FILE_PREFIX',
    'SUPPORTED_EXPORT_FORMATS',
    'VALID_PACKAGE_NAME_PATTERN',
    'VALID_USERNAME_PATTERN',
    'VALID_FILENAME_PATTERN',
    'DEFAULT_BACKUP_DIR',
    'DEFAULT_LOGS_DIR',
    'DEFAULT_EXPORTS_DIR',
    'DEFAULT_CONFIG_DIR',
    'DEFAULT_TEMP_DIR',
    'DEFAULT_PRESETS',
    'COMMON_BLOATWARE',
    'BLOATWARE_APPS',
    'ESSENTIAL_SETTINGS',
    'RECOMMENDED_REGISTRY_TWEAKS',
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',
    'MAX_LOG_FILE_SIZE_MB',
    'MAX_BACKUP_AGE_DAYS',
    'MAX_PARALLEL_OPERATIONS',
    'MAX_RETRY_ATTEMPTS',
    'MIN_PYTHON_VERSION',
    'MIN_WINDOWS_VERSION',
    'MIN_FREE_DISK_SPACE_GB',
    'ENABLE_SYSTEM_INFO',
    'ENABLE_SOFTWARE_MANAGEMENT',
    'ENABLE_FILE_OPERATIONS',
    'ENABLE_WINDOWS_SETUP',
    'ENABLE_ADVANCED_LOGGING',
    'ENABLE_AUTO_BACKUP',
    
    # Utilities
    'is_windows_platform',
    'check_admin_privileges',
    'get_application_path',
    'get_system_info',
    'run_command_with_timeout',
    'query_wmic',
    'safe_get_env_var',
    'validate_username',
    'validate_password',
    'validate_filename',
    'validate_path',
    'format_bytes',
    'escape_command_arg',
    'sanitize_filename',
    'get_unique_filename',
    'load_json_config',
    'save_json_config',
    'setup_logging',
    'get_error_message',
    
    # Worker System
    'WorkerSignals',
    'BaseWorker',
    'WorkerThread',
    'WorkerManager',
    'create_worker_thread',
    'connect_worker_signals',
    'safe_emit_signal',
    'is_gui_available',
    'ensure_gui_thread',
    
    # Configuration
    'ConfigManager',
    'AppConfig',
    'WindowSettings',
    'ApplicationSettings',
    'ChocolateySettings',
    'FileOperationSettings',
    'SystemInfoSettings',
    'ThemeMode',
    'LogLevel',
    
    # Module Functions
    'get_version',
    'get_app_info',
    'initialize_core',
    'cleanup_core',
    'validate_core_environment'
]

# Module metadata
__module_info__ = {
    'name': 'core',
    'version': __version__,
    'description': __description__,
    'author': __author__,
    'components': len(__all__),
    'gui_only': True,
    'platform': 'Windows'
}