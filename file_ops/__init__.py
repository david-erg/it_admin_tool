"""
File Operations Module

This module provides utilities for file and folder operations including:
- Folder copying and management with various modes (copy, move, sync, merge)
- Path manipulation and validation for Windows file systems
- Directory operations and utilities with comprehensive error handling
- Special folder access and file filtering capabilities

Supports both basic file operations and advanced folder management tasks
with progress tracking, conflict resolution, and verification features.
"""

from .folder_manager import (
    FolderManager, 
    FolderOperation, 
    CopyResult,
    CopyMode,
    ConflictResolution,
    FilterType,
    FileFilter,
    get_folder_manager,
    quick_copy_folder,
    copy_to_public_desktop
)
from .path_utilities import (
    PathUtilities, 
    PathValidator, 
    PathInfo,
    SpecialFolder,
    get_special_folders,
    validate_and_sanitize_path,
    ensure_safe_path
)

__all__ = [
    # Core Classes
    'FolderManager',
    'PathUtilities',
    'PathValidator',
    
    # Data Classes and Enums
    'FolderOperation', 
    'CopyResult',
    'PathInfo',
    'CopyMode',
    'ConflictResolution',
    'FilterType',
    'FileFilter',
    'SpecialFolder',
    
    # Convenience Functions
    'get_folder_manager',
    'quick_copy_folder',
    'copy_to_public_desktop',
    'get_special_folders',
    'validate_and_sanitize_path',
    'ensure_safe_path'
]

__version__ = "2.0.0"