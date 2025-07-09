"""
Folder Manager Module

Provides comprehensive folder copying, management, and file operations.
Supports various copy modes, progress tracking, and error handling.
"""

import os
import shutil
import hashlib
import platform
from pathlib import Path
from typing import List, Dict, Optional, Callable, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import time

from .path_utilities import PathUtilities, PathValidator, SpecialFolder


class CopyMode(Enum):
    """File copy operation modes"""
    COPY = "copy"           # Copy files only
    MOVE = "move"           # Move files
    SYNC = "sync"           # Synchronize directories
    MERGE = "merge"         # Merge directories


class ConflictResolution(Enum):
    """How to handle file conflicts during copy operations"""
    SKIP = "skip"           # Skip existing files
    OVERWRITE = "overwrite" # Overwrite existing files
    RENAME = "rename"       # Rename new files
    ASK = "ask"            # Ask user for each conflict
    NEWER = "newer"        # Keep newer file
    LARGER = "larger"      # Keep larger file


class FilterType(Enum):
    """File filtering types"""
    INCLUDE = "include"     # Include only matching patterns
    EXCLUDE = "exclude"     # Exclude matching patterns


@dataclass
class FileFilter:
    """Defines file filtering criteria"""
    patterns: List[str] = field(default_factory=list)  # File patterns (e.g., "*.txt")
    extensions: Set[str] = field(default_factory=set)  # File extensions (e.g., {".txt", ".doc"})
    min_size: Optional[int] = None                      # Minimum file size in bytes
    max_size: Optional[int] = None                      # Maximum file size in bytes
    filter_type: FilterType = FilterType.INCLUDE       # Include or exclude matching files
    include_hidden: bool = False                        # Whether to include hidden files
    include_system: bool = False                        # Whether to include system files


@dataclass
class FolderOperation:
    """Defines a folder operation configuration"""
    source_path: Path
    destination_path: Path
    copy_mode: CopyMode = CopyMode.COPY
    conflict_resolution: ConflictResolution = ConflictResolution.SKIP
    file_filter: Optional[FileFilter] = None
    preserve_permissions: bool = True
    preserve_timestamps: bool = True
    create_destination: bool = True
    verify_copy: bool = False
    follow_symlinks: bool = False


@dataclass
class CopyResult:
    """Results of a folder operation"""
    success: bool
    source_path: Path
    destination_path: Path
    operation_type: str
    files_processed: int = 0
    files_copied: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    directories_created: int = 0
    total_bytes_copied: int = 0
    total_time_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    failed_files: List[str] = field(default_factory=list)


class FolderManager:
    """Manages folder operations including copying, moving, and synchronization"""
    
    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize FolderManager
        
        Args:
            progress_callback: Optional callback function for progress updates
        """
        self.progress_callback = progress_callback or self._default_progress_callback
        self.path_utilities = PathUtilities()
        self.path_validator = PathValidator()
    
    def _default_progress_callback(self, message: str) -> None:
        """Default progress callback that prints to console"""
        print(message)
    
    def get_available_folders(self, base_path: Optional[Union[str, Path]] = None) -> List[Path]:
        """
        Get list of available folders in a directory
        
        Args:
            base_path: Base directory to scan (defaults to application directory)
            
        Returns:
            List of folder paths
        """
        if base_path is None:
            base_path = self.path_utilities.get_application_path()
        
        folders = []
        try:
            base_path = Path(base_path)
            if not base_path.exists() or not base_path.is_dir():
                return folders
            
            for item in base_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    folders.append(item)
            
            return sorted(folders, key=lambda p: p.name.lower())
            
        except Exception as e:
            self.progress_callback(f"Error scanning folders: {str(e)}")
            return folders
    
    def get_folder_info(self, folder_path: Union[str, Path]) -> Dict[str, Union[str, int]]:
        """
        Get detailed information about a folder
        
        Args:
            folder_path: Path to the folder
            
        Returns:
            Dictionary with folder information
        """
        try:
            path = Path(folder_path)
            if not path.exists():
                return {"error": "Folder does not exist"}
            
            if not path.is_dir():
                return {"error": "Path is not a directory"}
            
            # Get size and file count
            total_size, file_count = self.path_utilities.get_directory_size(path)
            
            # Count subdirectories
            dir_count = sum(1 for item in path.rglob('*') if item.is_dir())
            
            # Get modification time
            mod_time = datetime.fromtimestamp(path.stat().st_mtime)
            
            return {
                "name": path.name,
                "path": str(path),
                "size_bytes": total_size,
                "size_formatted": self.path_utilities.format_file_size(total_size),
                "file_count": file_count,
                "directory_count": dir_count,
                "modified": mod_time.strftime("%Y-%m-%d %H:%M:%S"),
                "exists": True,
                "is_readable": os.access(path, os.R_OK),
                "is_writable": os.access(path, os.W_OK)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def copy_folder_contents(self, operation: FolderOperation) -> CopyResult:
        """
        Copy folder contents with comprehensive options
        
        Args:
            operation: FolderOperation configuration
            
        Returns:
            CopyResult with operation results
        """
        start_time = time.time()
        
        result = CopyResult(
            success=False,
            source_path=operation.source_path,
            destination_path=operation.destination_path,
            operation_type=operation.copy_mode.value
        )
        
        try:
            # Validate source path
            if not operation.source_path.exists():
                result.errors.append(f"Source path does not exist: {operation.source_path}")
                return result
            
            if not operation.source_path.is_dir():
                result.errors.append(f"Source path is not a directory: {operation.source_path}")
                return result
            
            # Create destination if needed
            if operation.create_destination:
                operation.destination_path.mkdir(parents=True, exist_ok=True)
                if operation.destination_path.is_dir() and not operation.destination_path.exists():
                    result.directories_created += 1
            
            # Validate destination path
            if not operation.destination_path.exists():
                result.errors.append(f"Destination path does not exist: {operation.destination_path}")
                return result
            
            if not operation.destination_path.is_dir():
                result.errors.append(f"Destination path is not a directory: {operation.destination_path}")
                return result
            
            self.progress_callback(f"Starting {operation.copy_mode.value} operation...")
            self.progress_callback(f"Source: {operation.source_path}")
            self.progress_callback(f"Destination: {operation.destination_path}")
            
            # Process all files and directories
            for item in operation.source_path.rglob('*'):
                if item == operation.source_path:
                    continue  # Skip the source directory itself
                
                try:
                    # Calculate relative path
                    rel_path = item.relative_to(operation.source_path)
                    dest_item = operation.destination_path / rel_path
                    
                    result.files_processed += 1
                    
                    # Handle directories
                    if item.is_dir():
                        # Create directory structure
                        if not dest_item.exists():
                            dest_item.mkdir(parents=True, exist_ok=True)
                            result.directories_created += 1
                        continue
                    
                    if not item.is_file():
                        continue  # Skip special files (symlinks, etc.)
                    
                    # Apply file filter
                    if not self._should_include_file(item, operation.file_filter):
                        result.files_skipped += 1
                        result.skipped_files.append(str(rel_path))
                        continue
                    
                    # Create parent directory for destination file
                    dest_item.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Resolve conflicts
                    should_copy, final_dest = self._resolve_conflict(
                        item, dest_item, operation.conflict_resolution
                    )
                    
                    if not should_copy:
                        result.files_skipped += 1
                        result.skipped_files.append(str(rel_path))
                        continue
                    
                    # Perform the copy operation
                    success = self._copy_single_file(
                        item, final_dest, operation
                    )
                    
                    if success:
                        result.files_copied += 1
                        result.total_bytes_copied += item.stat().st_size
                        
                        # Verify copy if requested
                        if operation.verify_copy:
                            if not self._verify_file_copy(item, final_dest):
                                result.warnings.append(f"Copy verification failed for: {rel_path}")
                    else:
                        result.files_failed += 1
                        result.failed_files.append(str(rel_path))
                
                except Exception as e:
                    result.files_failed += 1
                    result.failed_files.append(str(rel_path))
                    result.errors.append(f"Error processing {rel_path}: {str(e)}")
            
            # Calculate total time
            result.total_time_seconds = time.time() - start_time
            
            # Determine overall success
            result.success = result.files_failed == 0 and len(result.errors) == 0
            
            # Log results
            self.progress_callback(f"Operation completed:")
            self.progress_callback(f"  Files processed: {result.files_processed}")
            self.progress_callback(f"  Files copied: {result.files_copied}")
            self.progress_callback(f"  Files skipped: {result.files_skipped}")
            self.progress_callback(f"  Files failed: {result.files_failed}")
            self.progress_callback(f"  Directories created: {result.directories_created}")
            self.progress_callback(f"  Total time: {result.total_time_seconds:.2f} seconds")
            
            if result.errors:
                self.progress_callback(f"  Errors: {len(result.errors)}")
                
        except Exception as e:
            result.errors.append(f"Operation failed: {str(e)}")
            result.total_time_seconds = time.time() - start_time
        
        return result
    
    def _copy_single_file(self, source: Path, dest: Path, operation: FolderOperation) -> bool:
        """
        Copy a single file with proper error handling
        
        Args:
            source: Source file path
            dest: Destination file path
            operation: Operation configuration
            
        Returns:
            bool: True if copy successful
        """
        try:
            if operation.copy_mode == CopyMode.COPY:
                shutil.copy2(source, dest)
            elif operation.copy_mode == CopyMode.MOVE:
                shutil.move(str(source), str(dest))
            else:
                # For sync and merge, use copy2
                shutil.copy2(source, dest)
            
            # Preserve permissions if requested
            if operation.preserve_permissions:
                try:
                    shutil.copystat(source, dest)
                except Exception:
                    pass  # Non-critical error
            
            return True
            
        except Exception:
            return False
    
    def _should_include_file(self, file_path: Path, file_filter: Optional[FileFilter]) -> bool:
        """
        Check if a file should be included based on filter criteria
        
        Args:
            file_path: Path to the file
            file_filter: Filter criteria
            
        Returns:
            True if file should be included
        """
        if file_filter is None:
            return True
        
        try:
            # Check hidden files
            if not file_filter.include_hidden and self._is_hidden_file(file_path):
                return file_filter.filter_type == FilterType.EXCLUDE
            
            # Check system files
            if not file_filter.include_system and self._is_system_file(file_path):
                return file_filter.filter_type == FilterType.EXCLUDE
            
            # Check file size
            if file_path.is_file():
                file_size = file_path.stat().st_size
                
                if file_filter.min_size is not None and file_size < file_filter.min_size:
                    return file_filter.filter_type == FilterType.EXCLUDE
                
                if file_filter.max_size is not None and file_size > file_filter.max_size:
                    return file_filter.filter_type == FilterType.EXCLUDE
            
            # Check file patterns and extensions
            matches_pattern = False
            
            # Check extensions
            if file_filter.extensions:
                file_ext = file_path.suffix.lower()
                matches_pattern = file_ext in file_filter.extensions
            
            # Check patterns
            if file_filter.patterns and not matches_pattern:
                import fnmatch
                for pattern in file_filter.patterns:
                    if fnmatch.fnmatch(file_path.name.lower(), pattern.lower()):
                        matches_pattern = True
                        break
            
            # If no patterns/extensions specified, include by default
            if not file_filter.patterns and not file_filter.extensions:
                matches_pattern = True
            
            # Apply filter logic
            if file_filter.filter_type == FilterType.INCLUDE:
                return matches_pattern
            else:  # EXCLUDE
                return not matches_pattern
                
        except Exception:
            # On error, include the file
            return True
    
    def _is_hidden_file(self, file_path: Path) -> bool:
        """
        Check if a file is hidden
        
        Args:
            file_path: Path to check
            
        Returns:
            bool: True if file is hidden
        """
        try:
            if platform.system() == "Windows":
                # Windows hidden files - use GetFileAttributes
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
                if attrs == -1:  # INVALID_FILE_ATTRIBUTES
                    return False
                FILE_ATTRIBUTE_HIDDEN = 0x02
                return bool(attrs & FILE_ATTRIBUTE_HIDDEN)
            else:
                # Unix-like systems - files starting with dot
                return file_path.name.startswith('.')
        except Exception:
            # Fallback: check if filename starts with dot
            return file_path.name.startswith('.')
    
    def _is_system_file(self, file_path: Path) -> bool:
        """
        Check if a file is a system file
        
        Args:
            file_path: Path to check
            
        Returns:
            bool: True if file is a system file
        """
        try:
            if platform.system() == "Windows":
                # Windows system files - use GetFileAttributes
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
                if attrs == -1:  # INVALID_FILE_ATTRIBUTES
                    return False
                FILE_ATTRIBUTE_SYSTEM = 0x04
                return bool(attrs & FILE_ATTRIBUTE_SYSTEM)
            else:
                # Unix-like systems - check common system directories
                system_dirs = {'/bin', '/sbin', '/usr/bin', '/usr/sbin', '/sys', '/proc'}
                return any(str(file_path).startswith(sys_dir) for sys_dir in system_dirs)
        except Exception:
            # Fallback: basic system file detection
            system_extensions = {'.sys', '.dll', '.exe'}
            return file_path.suffix.lower() in system_extensions
    
    def _resolve_conflict(self, source_file: Path, dest_file: Path, 
                         resolution: ConflictResolution) -> Tuple[bool, Path]:
        """
        Resolve file conflicts based on resolution strategy
        
        Args:
            source_file: Source file path
            dest_file: Destination file path
            resolution: Conflict resolution strategy
            
        Returns:
            Tuple[bool, Path]: (should_copy, final_destination)
        """
        if not dest_file.exists():
            return True, dest_file
        
        try:
            if resolution == ConflictResolution.SKIP:
                return False, dest_file
            
            elif resolution == ConflictResolution.OVERWRITE:
                return True, dest_file
            
            elif resolution == ConflictResolution.RENAME:
                # Generate unique filename
                counter = 1
                stem = dest_file.stem
                suffix = dest_file.suffix
                parent = dest_file.parent
                
                while True:
                    new_name = f"{stem}_{counter}{suffix}"
                    new_dest = parent / new_name
                    if not new_dest.exists():
                        return True, new_dest
                    counter += 1
                    if counter > 1000:  # Prevent infinite loop
                        return False, dest_file
            
            elif resolution == ConflictResolution.NEWER:
                source_mtime = source_file.stat().st_mtime
                dest_mtime = dest_file.stat().st_mtime
                return source_mtime > dest_mtime, dest_file
            
            elif resolution == ConflictResolution.LARGER:
                source_size = source_file.stat().st_size
                dest_size = dest_file.stat().st_size
                return source_size > dest_size, dest_file
            
            elif resolution == ConflictResolution.ASK:
                # For automated operations, default to skip
                # In GUI mode, this would show a dialog
                return False, dest_file
            
        except Exception:
            # On error, skip the file
            return False, dest_file
        
        return False, dest_file
    
    def _verify_file_copy(self, source_file: Path, dest_file: Path) -> bool:
        """
        Verify that a file was copied correctly by comparing checksums
        
        Args:
            source_file: Original file path
            dest_file: Copied file path
            
        Returns:
            bool: True if files match
        """
        try:
            # Quick check: file sizes
            if source_file.stat().st_size != dest_file.stat().st_size:
                return False
            
            # Checksum verification for small files only (< 100MB)
            if source_file.stat().st_size > 100 * 1024 * 1024:
                return True  # Skip checksum for large files
            
            source_hash = self._calculate_file_hash(source_file)
            dest_hash = self._calculate_file_hash(dest_file)
            
            return source_hash == dest_hash
            
        except Exception:
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of a file
        
        Args:
            file_path: Path to file
            
        Returns:
            str: SHA-256 hash hexdigest
        """
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    def sync_folders(self, source_path: Union[str, Path], 
                    dest_path: Union[str, Path]) -> CopyResult:
        """
        Synchronize two folders (one-way sync from source to destination)
        
        Args:
            source_path: Source folder path
            dest_path: Destination folder path
            
        Returns:
            CopyResult with sync results
        """
        operation = FolderOperation(
            source_path=Path(source_path),
            destination_path=Path(dest_path),
            copy_mode=CopyMode.SYNC,
            conflict_resolution=ConflictResolution.NEWER,
            create_destination=True,
            verify_copy=True
        )
        
        # TODO: Implement bidirectional sync if needed
        return self.copy_folder_contents(operation)
    
    def create_folder_backup(self, folder_path: Union[str, Path], 
                           backup_location: Optional[Union[str, Path]] = None) -> CopyResult:
        """
        Create a backup of a folder
        
        Args:
            folder_path: Folder to backup
            backup_location: Where to store backup (defaults to folder parent)
            
        Returns:
            CopyResult with backup results
        """
        source_path = Path(folder_path)
        
        if backup_location is None:
            backup_location = source_path.parent
        
        backup_name = f"{source_path.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = Path(backup_location) / backup_name
        
        operation = FolderOperation(
            source_path=source_path,
            destination_path=backup_path,
            copy_mode=CopyMode.COPY,
            conflict_resolution=ConflictResolution.OVERWRITE,
            create_destination=True,
            preserve_permissions=True,
            preserve_timestamps=True,
            verify_copy=True
        )
        
        return self.copy_folder_contents(operation)


# Convenience functions
def get_folder_manager(progress_callback: Optional[Callable[[str], None]] = None) -> FolderManager:
    """Get a configured FolderManager instance"""
    return FolderManager(progress_callback)


def quick_copy_folder(source_path: Union[str, Path], dest_path: Union[str, Path],
                     progress_callback: Optional[Callable[[str], None]] = None) -> CopyResult:
    """
    Quick function to copy a folder with default settings
    
    Args:
        source_path: Source folder path
        dest_path: Destination folder path
        progress_callback: Optional progress callback
        
    Returns:
        CopyResult with operation results
    """
    manager = FolderManager(progress_callback)
    operation = FolderOperation(
        source_path=Path(source_path),
        destination_path=Path(dest_path),
        copy_mode=CopyMode.COPY,
        conflict_resolution=ConflictResolution.SKIP,
        create_destination=True
    )
    return manager.copy_folder_contents(operation)


def copy_to_public_desktop(source_folder: Union[str, Path], 
                          progress_callback: Optional[Callable[[str], None]] = None) -> CopyResult:
    """
    Copy folder contents to the public desktop
    
    Args:
        source_folder: Source folder to copy from
        progress_callback: Optional progress callback
        
    Returns:
        CopyResult with operation results
    """
    try:
        # Get public desktop path
        if platform.system() == "Windows":
            public_desktop = Path("C:/Users/Public/Desktop")
        else:
            # Fallback for non-Windows systems
            public_desktop = Path.home() / "Desktop"
        
        manager = FolderManager(progress_callback)
        operation = FolderOperation(
            source_path=Path(source_folder),
            destination_path=public_desktop,
            copy_mode=CopyMode.COPY,
            conflict_resolution=ConflictResolution.SKIP,
            create_destination=True,
            preserve_permissions=False  # Don't preserve permissions for desktop
        )
        
        return manager.copy_folder_contents(operation)
        
    except Exception as e:
        # Return error result
        return CopyResult(
            success=False,
            source_path=Path(source_folder),
            destination_path=Path(""),
            operation_type="copy_to_public_desktop",
            errors=[f"Failed to copy to public desktop: {str(e)}"]
        )