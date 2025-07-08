"""
Path Utilities Module

Provides comprehensive path manipulation, validation, and utility functions
for working with Windows file system paths and special directories.
"""

import os
import sys
import platform
from pathlib import Path, PurePath
from typing import Dict, List, Optional, Tuple, Union, Set
from dataclasses import dataclass
from enum import Enum


class SpecialFolder(Enum):
    """Windows special folder identifiers"""
    DESKTOP = "Desktop"
    PUBLIC_DESKTOP = "Public\\Desktop"
    DOCUMENTS = "Documents"
    PUBLIC_DOCUMENTS = "Public\\Documents"
    DOWNLOADS = "Downloads"
    PICTURES = "Pictures"
    VIDEOS = "Videos"
    MUSIC = "Music"
    APPDATA = "AppData\\Roaming"
    LOCAL_APPDATA = "AppData\\Local"
    PROGRAM_FILES = "Program Files"
    PROGRAM_FILES_X86 = "Program Files (x86)"
    WINDOWS = "Windows"
    SYSTEM32 = "System32"
    TEMP = "Temp"


@dataclass
class PathInfo:
    """Information about a file system path"""
    path: Path
    exists: bool
    is_file: bool
    is_directory: bool
    is_readable: bool
    is_writable: bool
    size_bytes: Optional[int] = None
    parent_exists: bool = False
    is_absolute: bool = False
    is_valid: bool = True
    error_message: str = ""


class PathValidator:
    """Validates and analyzes file system paths"""
    
    # Windows invalid filename characters
    INVALID_FILENAME_CHARS = set('<>:"|?*')
    INVALID_PATH_CHARS = set('<>"|?*')
    
    # Reserved Windows names
    RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    @classmethod
    def validate_filename(cls, filename: str) -> Tuple[bool, str]:
        """
        Validate a filename according to Windows rules
        
        Args:
            filename: Filename to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return False, "Filename cannot be empty"
        
        if not filename.strip():
            return False, "Filename cannot be only whitespace"
        
        if len(filename) > 255:
            return False, "Filename too long (max 255 characters)"
        
        # Check for invalid characters
        invalid_chars = cls.INVALID_FILENAME_CHARS.intersection(set(filename))
        if invalid_chars:
            return False, f"Filename contains invalid characters: {', '.join(sorted(invalid_chars))}"
        
        # Check for trailing periods and spaces
        if filename.endswith('.') or filename.endswith(' '):
            return False, "Filename cannot end with period or space"
        
        # Check for reserved names
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in cls.RESERVED_NAMES:
            return False, f"'{name_without_ext}' is a reserved filename"
        
        return True, ""
    
    @classmethod
    def validate_path(cls, path_str: str) -> Tuple[bool, str]:
        """
        Validate a file path according to Windows rules
        
        Args:
            path_str: Path string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not path_str:
            return False, "Path cannot be empty"
        
        if not path_str.strip():
            return False, "Path cannot be only whitespace"
        
        # Check total path length
        if len(path_str) > 260:  # Windows MAX_PATH limitation
            return False, "Path too long (max 260 characters on Windows)"
        
        try:
            path = Path(path_str)
            
            # Validate each part of the path
            for part in path.parts:
                if part in ('', '.', '..'):
                    continue  # These are valid path components
                
                # Check if it's a drive letter (like 'C:')
                if len(part) == 2 and part[1] == ':' and part[0].isalpha():
                    continue
                
                # Validate as filename
                valid, error = cls.validate_filename(part)
                if not valid:
                    return False, f"Invalid path component '{part}': {error}"
            
            return True, ""
            
        except (ValueError, OSError) as e:
            return False, f"Invalid path format: {str(e)}"
    
    @classmethod
    def sanitize_filename(cls, filename: str, replacement: str = "_") -> str:
        """
        Sanitize a filename by replacing invalid characters
        
        Args:
            filename: Filename to sanitize
            replacement: Character to replace invalid characters with
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed"
        
        # Replace invalid characters
        sanitized = filename
        for char in cls.INVALID_FILENAME_CHARS:
            sanitized = sanitized.replace(char, replacement)
        
        # Remove trailing periods and spaces
        sanitized = sanitized.rstrip('. ')
        
        # Handle reserved names
        name_without_ext = sanitized.split('.')[0].upper()
        if name_without_ext in cls.RESERVED_NAMES:
            sanitized = f"{replacement}{sanitized}"
        
        # Ensure not empty
        if not sanitized:
            sanitized = "unnamed"
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = os.path.splitext(sanitized)
            max_name_length = 255 - len(ext)
            sanitized = name[:max_name_length] + ext
        
        return sanitized
    
    @classmethod
    def get_path_info(cls, path: Union[str, Path]) -> PathInfo:
        """
        Get comprehensive information about a path
        
        Args:
            path: Path to analyze
            
        Returns:
            PathInfo object with path details
        """
        try:
            path_obj = Path(path)
            
            info = PathInfo(
                path=path_obj,
                exists=path_obj.exists(),
                is_file=path_obj.is_file() if path_obj.exists() else False,
                is_directory=path_obj.is_dir() if path_obj.exists() else False,
                is_readable=os.access(path_obj, os.R_OK) if path_obj.exists() else False,
                is_writable=os.access(path_obj, os.W_OK) if path_obj.exists() else False,
                parent_exists=path_obj.parent.exists(),
                is_absolute=path_obj.is_absolute(),
                is_valid=True
            )
            
            # Get file size if it's a file
            if info.is_file:
                try:
                    info.size_bytes = path_obj.stat().st_size
                except OSError:
                    pass
            
            # Validate the path string
            valid, error = cls.validate_path(str(path))
            if not valid:
                info.is_valid = False
                info.error_message = error
            
            return info
            
        except Exception as e:
            return PathInfo(
                path=Path(str(path)),
                exists=False,
                is_file=False,
                is_directory=False,
                is_readable=False,
                is_writable=False,
                is_valid=False,
                error_message=str(e)
            )


class PathUtilities:
    """Utility functions for path manipulation and operations"""
    
    @staticmethod
    def get_application_path() -> Path:
        """
        Get the directory where the application is running from
        
        Returns:
            Path to application directory
        """
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return Path(sys.executable).parent
        else:
            # Running as Python script
            return Path(__file__).parent
    
    @staticmethod
    def get_special_folder(folder: SpecialFolder) -> Optional[Path]:
        """
        Get path to a Windows special folder
        
        Args:
            folder: SpecialFolder enum value
            
        Returns:
            Path to the special folder or None if not found
        """
        try:
            if folder == SpecialFolder.PUBLIC_DESKTOP:
                public_path = os.environ.get('PUBLIC', 'C:\\Users\\Public')
                return Path(public_path) / 'Desktop'
            
            elif folder == SpecialFolder.PUBLIC_DOCUMENTS:
                public_path = os.environ.get('PUBLIC', 'C:\\Users\\Public')
                return Path(public_path) / 'Documents'
            
            elif folder == SpecialFolder.DESKTOP:
                return Path.home() / 'Desktop'
            
            elif folder == SpecialFolder.DOCUMENTS:
                return Path.home() / 'Documents'
            
            elif folder == SpecialFolder.DOWNLOADS:
                return Path.home() / 'Downloads'
            
            elif folder == SpecialFolder.PICTURES:
                return Path.home() / 'Pictures'
            
            elif folder == SpecialFolder.VIDEOS:
                return Path.home() / 'Videos'
            
            elif folder == SpecialFolder.MUSIC:
                return Path.home() / 'Music'
            
            elif folder == SpecialFolder.APPDATA:
                appdata = os.environ.get('APPDATA')
                return Path(appdata) if appdata else None
            
            elif folder == SpecialFolder.LOCAL_APPDATA:
                localappdata = os.environ.get('LOCALAPPDATA')
                return Path(localappdata) if localappdata else None
            
            elif folder == SpecialFolder.PROGRAM_FILES:
                pf = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
                return Path(pf)
            
            elif folder == SpecialFolder.PROGRAM_FILES_X86:
                pf_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
                return Path(pf_x86)
            
            elif folder == SpecialFolder.WINDOWS:
                windows = os.environ.get('WINDIR', 'C:\\Windows')
                return Path(windows)
            
            elif folder == SpecialFolder.SYSTEM32:
                windows = os.environ.get('WINDIR', 'C:\\Windows')
                return Path(windows) / 'System32'
            
            elif folder == SpecialFolder.TEMP:
                temp = os.environ.get('TEMP') or os.environ.get('TMP')
                return Path(temp) if temp else None
            
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def ensure_directory_exists(directory: Union[str, Path], create_parents: bool = True) -> bool:
        """
        Ensure a directory exists, creating it if necessary
        
        Args:
            directory: Directory path to ensure exists
            create_parents: Whether to create parent directories
            
        Returns:
            True if directory exists or was created successfully
        """
        try:
            path = Path(directory)
            if not path.exists():
                path.mkdir(parents=create_parents, exist_ok=True)
            return path.is_dir()
        except Exception:
            return False
    
    @staticmethod
    def get_safe_filename(filename: str, max_length: int = 255) -> str:
        """
        Generate a safe filename from any string
        
        Args:
            filename: Original filename
            max_length: Maximum length for filename
            
        Returns:
            Safe filename string
        """
        safe_name = PathValidator.sanitize_filename(filename)
        
        if len(safe_name) > max_length:
            name, ext = os.path.splitext(safe_name)
            max_name_length = max_length - len(ext)
            safe_name = name[:max_name_length] + ext
        
        return safe_name
    
    @staticmethod
    def get_unique_path(base_path: Union[str, Path]) -> Path:
        """
        Get a unique path by adding numbers if the path already exists
        
        Args:
            base_path: Base path to make unique
            
        Returns:
            Unique path that doesn't exist
        """
        path = Path(base_path)
        
        if not path.exists():
            return path
        
        # Split the path into name and extension
        parent = path.parent
        stem = path.stem
        suffix = path.suffix
        
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
            
            # Prevent infinite loop
            if counter > 9999:
                break
        
        return path
    
    @staticmethod
    def get_relative_path(target_path: Union[str, Path], 
                         base_path: Union[str, Path]) -> Optional[Path]:
        """
        Get relative path from base to target
        
        Args:
            target_path: Target path
            base_path: Base path to calculate relative to
            
        Returns:
            Relative path or None if not possible
        """
        try:
            target = Path(target_path).resolve()
            base = Path(base_path).resolve()
            return target.relative_to(base)
        except (ValueError, OSError):
            return None
    
    @staticmethod
    def is_subdirectory(child_path: Union[str, Path], 
                       parent_path: Union[str, Path]) -> bool:
        """
        Check if one path is a subdirectory of another
        
        Args:
            child_path: Potential child path
            parent_path: Potential parent path
            
        Returns:
            True if child_path is under parent_path
        """
        try:
            child = Path(child_path).resolve()
            parent = Path(parent_path).resolve()
            
            # Check if child is under parent
            child.relative_to(parent)
            return True
        except (ValueError, OSError):
            return False
    
    @staticmethod
    def get_directory_size(directory: Union[str, Path]) -> Tuple[int, int]:
        """
        Calculate total size and file count of a directory
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Tuple of (total_bytes, file_count)
        """
        total_size = 0
        file_count = 0
        
        try:
            path = Path(directory)
            if not path.is_dir():
                return 0, 0
            
            for item in path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                        file_count += 1
                    except OSError:
                        continue  # Skip files we can't access
            
            return total_size, file_count
            
        except Exception:
            return 0, 0
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string (e.g., "1.5 MB")
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        size_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and size_index < len(size_names) - 1:
            size /= 1024
            size_index += 1
        
        return f"{size:.1f} {size_names[size_index]}"


# Convenience functions
def get_special_folders() -> Dict[str, Optional[Path]]:
    """
    Get dictionary of all special folder paths
    
    Returns:
        Dictionary mapping folder names to paths
    """
    folders = {}
    for folder in SpecialFolder:
        folders[folder.value] = PathUtilities.get_special_folder(folder)
    return folders


def validate_and_sanitize_path(path_str: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validate a path and provide sanitized version if invalid
    
    Args:
        path_str: Path string to validate
        
    Returns:
        Tuple of (is_valid, error_message, sanitized_path)
    """
    valid, error = PathValidator.validate_path(path_str)
    
    if valid:
        return True, "", path_str
    
    # Try to sanitize
    try:
        path = Path(path_str)
        sanitized_parts = []
        
        for part in path.parts:
            if part in ('', '.', '..') or (len(part) == 2 and part[1] == ':'):
                sanitized_parts.append(part)
            else:
                sanitized_parts.append(PathValidator.sanitize_filename(part))
        
        sanitized_path = str(Path(*sanitized_parts))
        return False, error, sanitized_path
        
    except Exception:
        return False, error, None