"""
Enhanced Path Utilities for File Operations

Provides comprehensive path manipulation, validation, and utility functions
for working with Windows file system paths and special directories.
GUI-optimized with robust error handling and validation.
"""

import os
import sys
import platform
import tempfile
import shutil
from pathlib import Path, PurePath
from typing import Dict, List, Optional, Tuple, Union, Set
from dataclasses import dataclass
from enum import Enum
import logging
import re
import stat

from core import (
    safe_get_env_var,
    validate_path,
    sanitize_filename,
    format_bytes,
    VALID_FILENAME_PATTERN
)


class SpecialFolder(Enum):
    """Windows special folder identifiers with user-friendly names."""
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
    STARTUP = "Startup"
    SENDTO = "SendTo"
    RECENT = "Recent"


class FileType(Enum):
    """File type classifications."""
    REGULAR = "regular"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    HIDDEN = "hidden"
    SYSTEM = "system"
    READONLY = "readonly"
    COMPRESSED = "compressed"
    ENCRYPTED = "encrypted"


@dataclass
class PathInfo:
    """Comprehensive information about a file system path."""
    path: Path
    exists: bool = False
    is_file: bool = False
    is_directory: bool = False
    is_symlink: bool = False
    is_hidden: bool = False
    is_system: bool = False
    is_readonly: bool = False
    is_readable: bool = False
    is_writable: bool = False
    is_executable: bool = False
    size_bytes: int = 0
    size_formatted: str = "0 B"
    created_time: Optional[float] = None
    modified_time: Optional[float] = None
    accessed_time: Optional[float] = None
    parent_exists: bool = False
    is_absolute: bool = False
    is_valid: bool = True
    drive: str = ""
    extension: str = ""
    stem: str = ""
    file_type: FileType = FileType.REGULAR
    permissions: str = ""
    error_message: str = ""
    
    def __post_init__(self):
        """Initialize computed fields after creation."""
        if self.size_bytes > 0:
            self.size_formatted = format_bytes(self.size_bytes)


class PathValidator:
    """Advanced path and filename validation for Windows."""
    
    # Windows forbidden characters
    FORBIDDEN_FILENAME_CHARS = set('<>:"|?*/')
    FORBIDDEN_PATH_CHARS = set('<>"|?*')
    
    # Reserved Windows names (case-insensitive)
    RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    # File size limits
    MAX_FILENAME_LENGTH = 255
    MAX_PATH_LENGTH = 260
    MAX_COMPONENT_LENGTH = 255
    
    @classmethod
    def validate_filename(cls, filename: str, strict: bool = True) -> Tuple[bool, str]:
        """
        Comprehensive filename validation.
        
        Args:
            filename: Filename to validate
            strict: Whether to apply strict validation rules
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not filename:
            return False, "Filename cannot be empty"
        
        if not filename.strip():
            return False, "Filename cannot be only whitespace"
        
        # Length check
        if len(filename) > cls.MAX_FILENAME_LENGTH:
            return False, f"Filename too long (max {cls.MAX_FILENAME_LENGTH} characters)"
        
        # Check for forbidden characters
        forbidden_chars = cls.FORBIDDEN_FILENAME_CHARS.intersection(set(filename))
        if forbidden_chars:
            return False, f"Filename contains forbidden characters: {', '.join(sorted(forbidden_chars))}"
        
        # Check for control characters
        if any(ord(c) < 32 for c in filename):
            return False, "Filename contains control characters"
        
        # Check for trailing periods and spaces
        if filename.endswith('.') or filename.endswith(' '):
            return False, "Filename cannot end with period or space"
        
        # Check for leading/trailing dots
        if strict and (filename.startswith('.') and len(filename) > 1):
            # Allow single dot (current directory) but not hidden files in strict mode
            if not filename.startswith('..'):
                return False, "Hidden files not allowed in strict mode"
        
        # Check for reserved names
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in cls.RESERVED_NAMES:
            return False, f"'{name_without_ext}' is a reserved system name"
        
        # Additional Windows-specific checks
        if strict:
            # No multiple consecutive dots
            if '..' in filename and filename != '..':
                return False, "Multiple consecutive dots not allowed"
            
            # No space before extension
            if '.' in filename and ' .' in filename:
                return False, "Space before file extension not allowed"
        
        return True, ""
    
    @classmethod
    def validate_path(cls, path: Union[str, Path], must_exist: bool = False) -> Tuple[bool, str]:
        """
        Comprehensive path validation.
        
        Args:
            path: Path to validate
            must_exist: Whether path must exist
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            path_obj = Path(path)
            path_str = str(path_obj)
            
            # Length check
            if len(path_str) > cls.MAX_PATH_LENGTH:
                return False, f"Path too long (max {cls.MAX_PATH_LENGTH} characters)"
            
            # Check each path component
            for part in path_obj.parts:
                if len(part) > cls.MAX_COMPONENT_LENGTH:
                    return False, f"Path component too long: '{part}'"
                
                # Skip drive letters (C:, D:, etc.)
                if len(part) == 2 and part[1] == ':':
                    continue
                
                # Skip UNC prefixes
                if part in ('\\\\', '//'):
                    continue
                
                # Validate each component as filename
                is_valid, error = cls.validate_filename(part, strict=False)
                if not is_valid:
                    return False, f"Invalid path component '{part}': {error}"
            
            # Check for forbidden path characters
            forbidden_chars = cls.FORBIDDEN_PATH_CHARS.intersection(set(path_str))
            if forbidden_chars:
                return False, f"Path contains forbidden characters: {', '.join(sorted(forbidden_chars))}"
            
            # Try to resolve path
            try:
                resolved = path_obj.resolve()
            except (OSError, ValueError) as e:
                return False, f"Invalid path format: {str(e)}"
            
            # Existence check
            if must_exist and not path_obj.exists():
                return False, f"Path does not exist: {path_obj}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Path validation error: {str(e)}"
    
    @classmethod
    def sanitize_filename(cls, filename: str, replacement: str = "_") -> str:
        """
        Sanitize filename by replacing forbidden characters.
        
        Args:
            filename: Original filename
            replacement: Character to replace forbidden chars with
            
        Returns:
            str: Sanitized filename
        """
        if not filename:
            return "unnamed_file"
        
        # Replace forbidden characters
        sanitized = filename
        for char in cls.FORBIDDEN_FILENAME_CHARS:
            sanitized = sanitized.replace(char, replacement)
        
        # Replace control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', replacement, sanitized)
        
        # Remove trailing periods and spaces
        sanitized = sanitized.rstrip('. ')
        
        # Handle reserved names
        name_part = sanitized.split('.')[0].upper()
        if name_part in cls.RESERVED_NAMES:
            sanitized = f"{replacement}{sanitized}"
        
        # Ensure not empty
        if not sanitized:
            sanitized = "unnamed_file"
        
        # Truncate if too long
        if len(sanitized) > cls.MAX_FILENAME_LENGTH:
            name, ext = os.path.splitext(sanitized)
            max_name_len = cls.MAX_FILENAME_LENGTH - len(ext)
            sanitized = name[:max_name_len] + ext
        
        return sanitized
    
    @classmethod
    def sanitize_path(cls, path: Union[str, Path], replacement: str = "_") -> Path:
        """
        Sanitize entire path by sanitizing each component.
        
        Args:
            path: Original path
            replacement: Character to replace forbidden chars with
            
        Returns:
            Path: Sanitized path
        """
        path_obj = Path(path)
        
        # Handle drive letter separately
        parts = list(path_obj.parts)
        if len(parts) > 0 and len(parts[0]) == 2 and parts[0][1] == ':':
            # Keep drive letter as-is
            sanitized_parts = [parts[0]]
            start_index = 1
        else:
            sanitized_parts = []
            start_index = 0
        
        # Sanitize each component
        for part in parts[start_index:]:
            sanitized_part = cls.sanitize_filename(part, replacement)
            sanitized_parts.append(sanitized_part)
        
        return Path(*sanitized_parts) if sanitized_parts else Path(".")


class PathUtilities:
    """Comprehensive path utilities for file operations."""
    
    def __init__(self):
        """Initialize path utilities."""
        self.validator = PathValidator()
        self._special_folders_cache = {}
    
    def get_path_info(self, path: Union[str, Path]) -> PathInfo:
        """
        Get comprehensive information about a path.
        
        Args:
            path: Path to analyze
            
        Returns:
            PathInfo: Detailed path information
        """
        try:
            path_obj = Path(path)
            info = PathInfo(path=path_obj)
            
            # Basic path properties
            info.is_absolute = path_obj.is_absolute()
            info.drive = str(path_obj.drive) if path_obj.drive else ""
            info.extension = path_obj.suffix
            info.stem = path_obj.stem
            
            # Validate path
            is_valid, error = self.validator.validate_path(path_obj)
            info.is_valid = is_valid
            if not is_valid:
                info.error_message = error
                return info
            
            # Check if path exists
            info.exists = path_obj.exists()
            if not info.exists:
                info.parent_exists = path_obj.parent.exists()
                return info
            
            # Get file system information
            try:
                stat_result = path_obj.stat()
                info.size_bytes = stat_result.st_size
                info.size_formatted = format_bytes(stat_result.st_size)
                info.created_time = stat_result.st_ctime
                info.modified_time = stat_result.st_mtime
                info.accessed_time = stat_result.st_atime
                
                # File type detection
                info.is_file = path_obj.is_file()
                info.is_directory = path_obj.is_dir()
                info.is_symlink = path_obj.is_symlink()
                
                # Determine file type
                if info.is_directory:
                    info.file_type = FileType.DIRECTORY
                elif info.is_symlink:
                    info.file_type = FileType.SYMLINK
                else:
                    info.file_type = FileType.REGULAR
                
                # Windows-specific attributes
                if platform.system() == 'Windows':
                    self._get_windows_attributes(path_obj, info, stat_result)
                
                # Permissions
                info.is_readable = os.access(path_obj, os.R_OK)
                info.is_writable = os.access(path_obj, os.W_OK)
                info.is_executable = os.access(path_obj, os.X_OK)
                info.permissions = self._format_permissions(stat_result.st_mode)
                
            except (OSError, PermissionError) as e:
                info.error_message = f"Cannot access file information: {str(e)}"
            
            return info
            
        except Exception as e:
            return PathInfo(
                path=Path(path),
                is_valid=False,
                error_message=f"Path analysis error: {str(e)}"
            )
    
    def _get_windows_attributes(self, path: Path, info: PathInfo, stat_result) -> None:
        """Get Windows-specific file attributes."""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Get file attributes
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            if attrs != -1:  # INVALID_FILE_ATTRIBUTES
                # FILE_ATTRIBUTE constants
                FILE_ATTRIBUTE_HIDDEN = 0x2
                FILE_ATTRIBUTE_SYSTEM = 0x4
                FILE_ATTRIBUTE_READONLY = 0x1
                FILE_ATTRIBUTE_COMPRESSED = 0x800
                FILE_ATTRIBUTE_ENCRYPTED = 0x4000
                
                info.is_hidden = bool(attrs & FILE_ATTRIBUTE_HIDDEN)
                info.is_system = bool(attrs & FILE_ATTRIBUTE_SYSTEM)
                info.is_readonly = bool(attrs & FILE_ATTRIBUTE_READONLY)
                
                # Update file type based on attributes
                if info.is_hidden:
                    info.file_type = FileType.HIDDEN
                elif info.is_system:
                    info.file_type = FileType.SYSTEM
                elif bool(attrs & FILE_ATTRIBUTE_COMPRESSED):
                    info.file_type = FileType.COMPRESSED
                elif bool(attrs & FILE_ATTRIBUTE_ENCRYPTED):
                    info.file_type = FileType.ENCRYPTED
                elif info.is_readonly:
                    info.file_type = FileType.READONLY
                    
        except Exception:
            # Fallback to basic detection
            info.is_hidden = path.name.startswith('.')
            info.is_readonly = not (stat_result.st_mode & stat.S_IWRITE)
    
    def _format_permissions(self, mode: int) -> str:
        """Format file permissions as readable string."""
        permissions = []
        
        # Owner permissions
        if mode & stat.S_IRUSR:
            permissions.append('r')
        else:
            permissions.append('-')
        
        if mode & stat.S_IWUSR:
            permissions.append('w')
        else:
            permissions.append('-')
        
        if mode & stat.S_IXUSR:
            permissions.append('x')
        else:
            permissions.append('-')
        
        return ''.join(permissions)
    
    def get_special_folder(self, folder: SpecialFolder) -> Optional[Path]:
        """
        Get path to Windows special folder.
        
        Args:
            folder: Special folder identifier
            
        Returns:
            Optional[Path]: Path to special folder, None if not found
        """
        # Check cache first
        if folder in self._special_folders_cache:
            return self._special_folders_cache[folder]
        
        try:
            folder_path = None
            
            if folder == SpecialFolder.DESKTOP:
                folder_path = Path(safe_get_env_var('USERPROFILE')) / 'Desktop'
            
            elif folder == SpecialFolder.DOCUMENTS:
                folder_path = Path(safe_get_env_var('USERPROFILE')) / 'Documents'
            
            elif folder == SpecialFolder.DOWNLOADS:
                folder_path = Path(safe_get_env_var('USERPROFILE')) / 'Downloads'
            
            elif folder == SpecialFolder.PICTURES:
                folder_path = Path(safe_get_env_var('USERPROFILE')) / 'Pictures'
            
            elif folder == SpecialFolder.VIDEOS:
                folder_path = Path(safe_get_env_var('USERPROFILE')) / 'Videos'
            
            elif folder == SpecialFolder.MUSIC:
                folder_path = Path(safe_get_env_var('USERPROFILE')) / 'Music'
            
            elif folder == SpecialFolder.APPDATA:
                appdata = safe_get_env_var('APPDATA')
                folder_path = Path(appdata) if appdata else None
            
            elif folder == SpecialFolder.LOCAL_APPDATA:
                localappdata = safe_get_env_var('LOCALAPPDATA')
                folder_path = Path(localappdata) if localappdata else None
            
            elif folder == SpecialFolder.PROGRAM_FILES:
                pf = safe_get_env_var('PROGRAMFILES', 'C:\\Program Files')
                folder_path = Path(pf)
            
            elif folder == SpecialFolder.PROGRAM_FILES_X86:
                pf_x86 = safe_get_env_var('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
                folder_path = Path(pf_x86)
            
            elif folder == SpecialFolder.WINDOWS:
                windows = safe_get_env_var('WINDIR', 'C:\\Windows')
                folder_path = Path(windows)
            
            elif folder == SpecialFolder.SYSTEM32:
                windows = safe_get_env_var('WINDIR', 'C:\\Windows')
                folder_path = Path(windows) / 'System32'
            
            elif folder == SpecialFolder.TEMP:
                folder_path = Path(tempfile.gettempdir())
            
            elif folder == SpecialFolder.PUBLIC_DESKTOP:
                public = safe_get_env_var('PUBLIC')
                folder_path = Path(public) / 'Desktop' if public else None
            
            elif folder == SpecialFolder.PUBLIC_DOCUMENTS:
                public = safe_get_env_var('PUBLIC')
                folder_path = Path(public) / 'Documents' if public else None
            
            # Cache the result
            if folder_path and folder_path.exists():
                self._special_folders_cache[folder] = folder_path
                return folder_path
            
            return None
            
        except Exception as e:
            logging.error(f"Failed to get special folder {folder}: {e}")
            return None
    
    def ensure_directory_exists(
        self, 
        directory: Union[str, Path], 
        create_parents: bool = True,
        permissions: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory: Directory path to ensure exists
            create_parents: Whether to create parent directories
            permissions: Optional permissions for created directories
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        try:
            path = Path(directory)
            
            # Validate path
            is_valid, error = self.validator.validate_path(path)
            if not is_valid:
                return False, error
            
            if path.exists():
                if path.is_dir():
                    return True, ""
                else:
                    return False, f"Path exists but is not a directory: {path}"
            
            # Create directory
            path.mkdir(parents=create_parents, exist_ok=True)
            
            # Set permissions if specified
            if permissions is not None and platform.system() != 'Windows':
                path.chmod(permissions)
            
            return True, ""
            
        except PermissionError:
            return False, f"Permission denied creating directory: {directory}"
        except FileExistsError:
            return False, f"File exists at directory path: {directory}"
        except OSError as e:
            return False, f"OS error creating directory: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error creating directory: {str(e)}"
    
    def get_unique_filename(self, filepath: Path, max_attempts: int = 1000) -> Path:
        """
        Generate a unique filename if the file already exists.
        
        Args:
            filepath: Original file path
            max_attempts: Maximum number of attempts to find unique name
            
        Returns:
            Path: Unique file path
        """
        if not filepath.exists():
            return filepath
        
        stem = filepath.stem
        suffix = filepath.suffix
        parent = filepath.parent
        
        for counter in range(1, max_attempts + 1):
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
        
        # If we can't find a unique name, use timestamp
        import time
        timestamp = int(time.time())
        new_name = f"{stem}_{timestamp}{suffix}"
        return parent / new_name
    
    def get_available_space(self, path: Union[str, Path]) -> Tuple[int, int, int]:
        """
        Get available disk space for a path.
        
        Args:
            path: Path to check
            
        Returns:
            Tuple[int, int, int]: (total_bytes, used_bytes, free_bytes)
        """
        try:
            usage = shutil.disk_usage(path)
            return usage.total, usage.used, usage.free
        except Exception as e:
            logging.error(f"Failed to get disk usage for {path}: {e}")
            return 0, 0, 0
    
    def is_safe_path(self, path: Union[str, Path], base_path: Union[str, Path]) -> bool:
        """
        Check if path is safe (doesn't escape base directory).
        
        Args:
            path: Path to check
            base_path: Base directory path
            
        Returns:
            bool: True if path is safe
        """
        try:
            path_obj = Path(path).resolve()
            base_obj = Path(base_path).resolve()
            
            # Check if path is within base directory
            try:
                path_obj.relative_to(base_obj)
                return True
            except ValueError:
                return False
                
        except Exception:
            return False
    
    def get_directory_size(self, directory: Union[str, Path]) -> Tuple[int, int]:
        """
        Calculate total size of directory and file count.
        
        Args:
            directory: Directory to analyze
            
        Returns:
            Tuple[int, int]: (total_bytes, file_count)
        """
        try:
            total_size = 0
            file_count = 0
            
            dir_path = Path(directory)
            if not dir_path.is_dir():
                return 0, 0
            
            for item in dir_path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                        file_count += 1
                    except (OSError, PermissionError):
                        # Skip files we can't access
                        continue
            
            return total_size, file_count
            
        except Exception as e:
            logging.error(f"Failed to calculate directory size for {directory}: {e}")
            return 0, 0
    
    def copy_to_public_desktop(self, source_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        Copy a file or directory to the public desktop.
        
        Args:
            source_path: Source file or directory
            
        Returns:
            Tuple[bool, str]: (success, error_message_or_destination)
        """
        try:
            source = Path(source_path)
            if not source.exists():
                return False, f"Source does not exist: {source}"
            
            # Get public desktop
            public_desktop = self.get_special_folder(SpecialFolder.PUBLIC_DESKTOP)
            if not public_desktop:
                return False, "Could not locate public desktop"
            
            # Create unique destination name
            dest_name = self.validator.sanitize_filename(source.name)
            destination = self.get_unique_filename(public_desktop / dest_name)
            
            # Copy file or directory
            if source.is_file():
                shutil.copy2(source, destination)
            elif source.is_dir():
                shutil.copytree(source, destination)
            else:
                return False, f"Source is neither file nor directory: {source}"
            
            return True, str(destination)
            
        except PermissionError:
            return False, "Permission denied copying to public desktop"
        except Exception as e:
            return False, f"Error copying to public desktop: {str(e)}"