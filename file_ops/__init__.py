"""
File Operations Module

This module provides utilities for file and folder operations including:
- Folder copying and management
- Path manipulation and validation
- Directory operations and utilities

Supports both basic file operations and advanced folder management tasks.
"""

from .folder_manager import FolderManager, FolderOperation, CopyResult
from .path_utilities import PathUtilities, PathValidator, get_special_folders

__all__ = [
    'FolderManager',
    'FolderOperation', 
    'CopyResult',
    'PathUtilities',
    'PathValidator',
    'get_special_folders'
]

__version__ = "1.0.0"