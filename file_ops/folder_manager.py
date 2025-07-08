"""
Folder Manager Module

Provides comprehensive folder copying, management, and file operations.
Supports various copy modes, progress tracking, and error handling.
"""

import os
import shutil
import platform
from pathlib import Path
from typing import List, Dict, Optional, Callable, Tuple, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import stat

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
                return False
            
            # Check system files
            if not file_filter.include_system and self._is_system_file(file_path):
                return False
            
            # Check file size
            if file_path.is_file():
                file_size = file_path.stat().st_size
                
                if file_filter.min_size is not None and file_size < file_filter.min_size:
                    return file_filter.filter_type == FilterType.EXCLUDE
                
                if file_filter.max_size is not None and file_size > file_filter.max_size:
                    return file_filter.filter_type == FilterType.EXCLUDE
            
            # Check extensions
            if file_filter.extensions:
                file_ext = file_path.suffix.lower()
                ext_match = file_ext in file_filter.extensions
                
                if file_filter.filter_type == FilterType.INCLUDE:
                    if not ext_match:
                        return False
                else:  # EXCLUDE
                    if ext_match:
                        return False
            
            # Check patterns
            if file_filter.patterns:
                import fnmatch
                pattern_match = any(fnmatch.fnmatch(file_path.name, pattern) 
                                  for pattern in file_filter.patterns)
                
                if file_filter.filter_type == FilterType.INCLUDE:
                    if not pattern_match:
                        return False
                else:  # EXCLUDE
                    if pattern_match:
                        return False
            
            return True
            
        except Exception:
            return True  # Include file if we can't determine filter criteria
    
    def _is_hidden_file(self, file_path: Path) -> bool:
        """Check if a file is hidden"""
        try:
            if platform.system() == "Windows":
                return bool(file_path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)
            else:
                return file_path.name.startswith('.')
        except:
            return False
    
    def _is_system_file(self, file_path: Path) -> bool:
        """Check if a file is a system file"""
        try:
            if platform.system() == "Windows":
                return bool(file_path.stat().st_file_attributes & stat.FILE_ATTRIBUTE_SYSTEM)
            else:
                return False  # No standard system file attribute on Unix-like systems
        except:
            return False
    
    def _resolve_conflict(self, source_path: Path, dest_path: Path, 
                         resolution: ConflictResolution) -> Tuple[bool, Optional[Path]]:
        """
        Resolve file conflict based on resolution strategy
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
            resolution: Conflict resolution strategy
            
        Returns:
            Tuple of (should_copy, final_destination_path)
        """
        if not dest_path.exists():
            return True, dest_path
        
        if resolution == ConflictResolution.SKIP:
            return False, None
        
        elif resolution == ConflictResolution.OVERWRITE:
            return True, dest_path
        
        elif resolution == ConflictResolution.RENAME:
            unique_path = self.path_utilities.get_unique_path(dest_path)
            return True, unique_path
        
        elif resolution == ConflictResolution.NEWER:
            try:
                source_mtime = source_path.stat().st_mtime
                dest_mtime = dest_path.stat().st_mtime
                return source_mtime > dest_mtime, dest_path
            except:
                return True, dest_path  # Default to copy if we can't compare times
        
        elif resolution == ConflictResolution.LARGER:
            try:
                source_size = source_path.stat().st_size
                dest_size = dest_path.stat().st_size
                return source_size > dest_size, dest_path
            except:
                return True, dest_path  # Default to copy if we can't compare sizes
        
        else:  # ASK - for now, default to skip
            return False, None
    
    def copy_folder_contents(self, operation: FolderOperation) -> CopyResult:
        """
        Copy folder contents based on operation configuration
        
        Args:
            operation: FolderOperation defining the copy parameters
            
        Returns:
            CopyResult with operation results
        """
        start_time = datetime.now()
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
            
            # Create destination directory if needed
            if operation.create_destination:
                if not self.path_utilities.ensure_directory_exists(operation.destination_path):
                    result.errors.append(f"Could not create destination directory: {operation.destination_path}")
                    return result
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
            
            # Process all items in source directory
            for item in operation.source_path.rglob('*'):
                result.files_processed += 1
                
                try:
                    # Calculate relative path
                    rel_path = item.relative_to(operation.source_path)
                    dest_item = operation.destination_path / rel_path
                    
                    if item.is_dir():
                        # Create directory structure
                        if not dest_item.exists():
                            dest_item.mkdir(parents=True, exist_ok=True)
                            result.directories_created += 1
                        continue
                    
                    if not item.is_file():
                        continue  # Skip special files
                    
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
                    if operation.copy_mode == CopyMode.COPY:
                        shutil.copy2(item, final_dest)
                    elif operation.copy_mode == CopyMode.MOVE:
                        shutil.move(item, final_dest)
                    else:
                        # For sync and merge, use copy2
                        shutil.copy2(item, final_dest)
                    
                    # Preserve permissions if requested
                    if operation.preserve_permissions:
                        try:
                            shutil.copystat(item, final_dest)
                        except:
                            result.warnings.append(f"Could not preserve permissions for: {rel_path}")
                    
                    # Verify copy if requested
                    if operation.verify_copy:
                        if not self._verify_file_copy(item, final_dest):
                            result.warnings.append(f"Copy verification failed for: {rel_path}")
                    
                    result.files_copied += 1
                    result.total_bytes_copied += item.stat().st_size
                    
                    # Progress update for large operations
                    if result.files_processed % 100 == 0:
                        self.progress_callback(f"Processed {result.files_processed} files...")
                
                except Exception as e:
                    result.files_failed += 1
                    error_msg = f"Failed to copy {rel_path}: {str(e)}"
                    result.errors.append(error_msg)
                    result.failed_files.append(str(rel_path))
                    self.progress_callback(f"ERROR: {error_msg}")
            
            # Calculate final results
            end_time = datetime.now()
            result.total_time_seconds = (end_time - start_time).total_seconds()
            result.success = result.files_failed == 0
            
            # Final status report
            self.progress_callback(f"Operation completed in {result.total_time_seconds:.2f} seconds")
            self.progress_callback(f"Files copied: {result.files_copied}")
            self.progress_callback(f"Files skipped: {result.files_skipped}")
            self.progress_callback(f"Files failed: {result.files_failed}")
            self.progress_callback(f"Total bytes copied: {self.path_utilities.format_file_size(result.total_bytes_copied)}")
            
            return result
            
        except Exception as e:
            result.errors.append(f"Operation failed: {str(e)}")
            self.progress_callback(f"CRITICAL ERROR: {str(e)}")
            return result
    
    def _verify_file_copy(self, source_path: Path, dest_path: Path) -> bool:
        """
        Verify that a file was copied correctly by comparing sizes
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
            
        Returns:
            True if files match
        """
        try:
            if not dest_path.exists():
                return False
            
            source_size = source_path.stat().st_size
            dest_size = dest_path.stat().st_size
            
            return source_size == dest_size
            
        except Exception:
            return False
    
    def copy_to_public_desktop(self, source_folder: Union[str, Path]) -> CopyResult:
        """
        Copy folder contents to the public desktop (convenience method)
        
        Args:
            source_folder: Source folder to copy from
            
        Returns:
            CopyResult with operation results
        """
        try:
            source_path = Path(source_folder)
            public_desktop = self.path_utilities.get_special_folder(SpecialFolder.PUBLIC_DESKTOP)
            
            if public_desktop is None:
                result = CopyResult(
                    success=False,
                    source_path=source_path,
                    destination_path=Path("Unknown"),
                    operation_type="copy_to_public_desktop"
                )
                result.errors.append("Could not locate public desktop folder")
                return result
            
            operation = FolderOperation(
                source_path=source_path,
                destination_path=public_desktop,
                copy_mode=CopyMode.COPY,
                conflict_resolution=ConflictResolution.OVERWRITE,
                create_destination=True
            )
            
            return self.copy_folder_contents(operation)
            
        except Exception as e:
            result = CopyResult(
                success=False,
                source_path=Path(str(source_folder)),
                destination_path=Path("Unknown"),
                operation_type="copy_to_public_desktop"
            )
            result.errors.append(f"Failed to copy to public desktop: {str(e)}")
            return result
    
    def synchronize_folders(self, source_path: Union[str, Path], 
                           dest_path: Union[str, Path],
                           bidirectional: bool = False) -> CopyResult:
        """
        Synchronize two folders (one-way or bidirectional)
        
        Args:
            source_path: Source folder path
            dest_path: Destination folder path
            bidirectional: If True, sync both ways
            
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