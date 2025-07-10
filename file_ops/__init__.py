"""
File Operations Module for IT Admin Tool

Provides comprehensive file and folder operations including copying, moving,
synchronization, and path management. GUI-optimized with progress tracking
and robust error handling.
"""

# Version information
__version__ = "3.0"
__author__ = "IT Admin Tool Team"
__description__ = "File operations module with folder management and path utilities"

# Core folder management
from .folder_manager import (
    FolderManager,
    FolderOperation,
    FolderOperationWorker,
    OperationResult,
    CopyMode,
    ConflictResolution,
    FileFilter,
    FilterType
)

# Path utilities and validation
from .path_utilities import (
    PathUtilities,
    PathValidator,
    PathInfo,
    SpecialFolder,
    FileType
)

# High-level operations interface
from .file_operations import (
    FileOperationsManager,
    QuickCopyOptions,
    copy_folder,
    validate_operation_paths
)

# Module-level convenience functions
def create_file_operations_manager() -> FileOperationsManager:
    """
    Create a new file operations manager instance.
    
    Returns:
        FileOperationsManager: New manager instance
    """
    return FileOperationsManager()

def get_special_folder_path(folder: SpecialFolder) -> str:
    """
    Get path to Windows special folder as string.
    
    Args:
        folder: Special folder identifier
        
    Returns:
        str: Path to special folder or empty string if not found
    """
    utilities = PathUtilities()
    path = utilities.get_special_folder(folder)
    return str(path) if path else ""

def copy_to_public_desktop(source_path: str) -> tuple:
    """
    Copy a file or folder to the public desktop.
    
    Args:
        source_path: Source file or folder path
        
    Returns:
        tuple: (success: bool, message: str)
    """
    manager = FileOperationsManager()
    return manager.copy_to_public_desktop(source_path)

def validate_filename(filename: str) -> tuple:
    """
    Validate a filename for Windows compatibility.
    
    Args:
        filename: Filename to validate
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    validator = PathValidator()
    return validator.validate_filename(filename)

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    validator = PathValidator()
    return validator.sanitize_filename(filename)

def get_folder_size(folder_path: str) -> dict:
    """
    Get folder size information.
    
    Args:
        folder_path: Path to folder
        
    Returns:
        dict: Size information including bytes and formatted size
    """
    from core import format_bytes
    utilities = PathUtilities()
    total_bytes, file_count = utilities.get_directory_size(folder_path)
    
    return {
        'total_bytes': total_bytes,
        'total_formatted': format_bytes(total_bytes),
        'file_count': file_count
    }

def get_disk_space(path: str) -> dict:
    """
    Get disk space information for a path.
    
    Args:
        path: Path to check
        
    Returns:
        dict: Disk space information
    """
    manager = FileOperationsManager()
    return manager.get_disk_usage(path)

def create_simple_file_filter(
    extensions: list = None,
    include_hidden: bool = False
) -> FileFilter:
    """
    Create a simple file filter based on extensions.
    
    Args:
        extensions: List of file extensions to include (e.g., ['.txt', '.doc'])
        include_hidden: Whether to include hidden files
        
    Returns:
        FileFilter: Configured file filter
    """
    return FileFilter(
        extensions=set(ext.lower() for ext in (extensions or [])),
        include_hidden=include_hidden,
        filter_type=FilterType.INCLUDE if extensions else FilterType.INCLUDE
    )

# Export all public components
__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__description__',
    
    # Core Classes - Folder Management
    'FolderManager',
    'FolderOperation',
    'FolderOperationWorker',
    'OperationResult',
    
    # Enums
    'CopyMode',
    'ConflictResolution',
    'FilterType',
    'SpecialFolder',
    'FileType',
    
    # Data Classes
    'FileFilter',
    'PathInfo',
    'QuickCopyOptions',
    
    # Utility Classes
    'PathUtilities',
    'PathValidator',
    
    # High-Level Interface
    'FileOperationsManager',
    
    # Module Functions
    'create_file_operations_manager',
    'get_special_folder_path',
    'copy_to_public_desktop',
    'validate_filename',
    'sanitize_filename',
    'get_folder_size',
    'get_disk_space',
    'create_simple_file_filter',
    
    # Convenience Functions
    'copy_folder',
    'validate_operation_paths'
]

# Module metadata
__module_info__ = {
    'name': 'file_ops',
    'version': __version__,
    'description': __description__,
    'author': __author__,
    'components': len(__all__),
    'gui_optimized': True,
    'thread_safe': True,
    'platform': 'Windows'
}

# Module initialization logging
import logging
logging.info(f"File operations module loaded - version {__version__}")

# Validate module dependencies
def validate_module_dependencies() -> list:
    """
    Validate that all required dependencies are available.
    
    Returns:
        list: List of missing dependencies (empty if all available)
    """
    missing = []
    
    try:
        from core import BaseWorker, WorkerManager
    except ImportError:
        missing.append('core.BaseWorker')
    
    try:
        from pathlib import Path
    except ImportError:
        missing.append('pathlib')
    
    try:
        import shutil
    except ImportError:
        missing.append('shutil')
    
    try:
        import hashlib
    except ImportError:
        missing.append('hashlib')
    
    return missing

# Check dependencies on import
_missing_deps = validate_module_dependencies()
if _missing_deps:
    logging.error(f"File operations module missing dependencies: {_missing_deps}")
else:
    logging.debug("File operations module dependencies satisfied")

# Default manager instance (lazy-loaded)
_default_manager = None

def get_default_manager() -> FileOperationsManager:
    """
    Get the default file operations manager instance.
    Creates one if it doesn't exist.
    
    Returns:
        FileOperationsManager: Default manager instance
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = FileOperationsManager()
    return _default_manager

def cleanup_default_manager() -> None:
    """Clean up the default manager instance."""
    global _default_manager
    if _default_manager is not None:
        _default_manager.cleanup()
        _default_manager = None

# Add cleanup to module exports
__all__.extend(['get_default_manager', 'cleanup_default_manager', 'validate_module_dependencies'])