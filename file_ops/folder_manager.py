"""
Folder Manager for File Operations

Provides comprehensive folder copying, management, and file operations
with robust error handling, progress tracking, and resource management.
GUI-optimized with proper threading support.
"""

import os
import shutil
import hashlib
import time
import threading
from pathlib import Path
from typing import List, Dict, Optional, Callable, Tuple, Union, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

from core import (
    BaseWorker,
    WorkerSignals,
    format_bytes,
    get_unique_filename,
    MAX_SINGLE_FILE_SIZE,
    MAX_TOTAL_COPY_SIZE
)
from .path_utilities import PathUtilities, PathValidator, PathInfo, SpecialFolder


class CopyMode(Enum):
    """File copy operation modes."""
    COPY = "copy"           # Copy files only
    MOVE = "move"           # Move files
    SYNC = "sync"           # Synchronize directories
    MIRROR = "mirror"       # Mirror directories (delete extra files in dest)


class ConflictResolution(Enum):
    """How to handle file conflicts during operations."""
    SKIP = "skip"           # Skip existing files
    OVERWRITE = "overwrite" # Overwrite existing files
    RENAME = "rename"       # Rename new files
    NEWER = "newer"         # Keep newer file
    LARGER = "larger"       # Keep larger file
    ASK = "ask"             # Ask user for each conflict (GUI callback)


class FilterType(Enum):
    """File filtering types."""
    INCLUDE = "include"     # Include only matching patterns
    EXCLUDE = "exclude"     # Exclude matching patterns


@dataclass
class FileFilter:
    """Defines file filtering criteria."""
    patterns: List[str] = field(default_factory=list)  # File patterns (e.g., "*.txt")
    extensions: Set[str] = field(default_factory=set)  # File extensions (e.g., {".txt", ".doc"})
    min_size: Optional[int] = None                       # Minimum file size in bytes
    max_size: Optional[int] = None                       # Maximum file size in bytes
    filter_type: FilterType = FilterType.INCLUDE        # Include or exclude matching files
    include_hidden: bool = False                         # Whether to include hidden files
    include_system: bool = False                         # Whether to include system files
    include_readonly: bool = True                        # Whether to include readonly files
    
    def matches(self, path_info: PathInfo) -> bool:
        """
        Check if a file matches this filter.
        
        Args:
            path_info: File information to check
            
        Returns:
            bool: True if file matches filter
        """
        # Hidden files check
        if not self.include_hidden and path_info.is_hidden:
            return False
        
        # System files check
        if not self.include_system and path_info.is_system:
            return False
        
        # Readonly files check
        if not self.include_readonly and path_info.is_readonly:
            return False
        
        # Size checks
        if self.min_size is not None and path_info.size_bytes < self.min_size:
            return False
        
        if self.max_size is not None and path_info.size_bytes > self.max_size:
            return False
        
        # Pattern and extension checks
        matches_pattern = False
        filename = path_info.path.name
        
        # Check patterns
        if self.patterns:
            import fnmatch
            for pattern in self.patterns:
                if fnmatch.fnmatch(filename, pattern):
                    matches_pattern = True
                    break
        else:
            matches_pattern = True  # No patterns means match all
        
        # Check extensions
        if self.extensions:
            extension = path_info.extension.lower()
            if extension in self.extensions:
                matches_pattern = True
        
        # Apply filter type
        if self.filter_type == FilterType.INCLUDE:
            return matches_pattern
        else:  # EXCLUDE
            return not matches_pattern


@dataclass
class FolderOperation:
    """Defines a folder operation configuration."""
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
    calculate_progress: bool = True
    dry_run: bool = False
    
    def __post_init__(self):
        """Validate operation configuration."""
        # Ensure paths are Path objects
        self.source_path = Path(self.source_path)
        self.destination_path = Path(self.destination_path)
        
        # Create default filter if none provided
        if self.file_filter is None:
            self.file_filter = FileFilter()


@dataclass
class OperationResult:
    """Results of a folder operation."""
    success: bool
    source_path: Path
    destination_path: Path
    operation_type: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    files_processed: int = 0
    files_copied: int = 0
    files_moved: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    directories_created: int = 0
    total_bytes_copied: int = 0
    total_time_seconds: float = 0.0
    average_speed_mbps: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    failed_files: List[str] = field(default_factory=list)
    
    def finalize(self) -> None:
        """Finalize the operation result with computed values."""
        self.end_time = datetime.now()
        if self.start_time:
            self.total_time_seconds = (self.end_time - self.start_time).total_seconds()
        
        # Calculate average speed
        if self.total_time_seconds > 0 and self.total_bytes_copied > 0:
            bytes_per_second = self.total_bytes_copied / self.total_time_seconds
            self.average_speed_mbps = bytes_per_second / (1024 * 1024)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get operation summary as dictionary."""
        return {
            'success': self.success,
            'operation_type': self.operation_type,
            'files_processed': self.files_processed,
            'files_copied': self.files_copied,
            'files_moved': self.files_moved,
            'files_skipped': self.files_skipped,
            'files_failed': self.files_failed,
            'directories_created': self.directories_created,
            'total_bytes_copied': self.total_bytes_copied,
            'total_bytes_formatted': format_bytes(self.total_bytes_copied),
            'total_time_seconds': self.total_time_seconds,
            'average_speed_mbps': self.average_speed_mbps,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }


class FolderOperationWorker(BaseWorker):
    """Worker class for folder operations with progress reporting."""
    
    def __init__(self, operation: FolderOperation, parent=None):
        super().__init__(parent)
        self.operation = operation
        self.path_utilities = PathUtilities()
        self.validator = PathValidator()
        self._current_file = ""
        self._bytes_copied = 0
        self._total_bytes = 0
        self._files_to_process = []
        self._lock = threading.Lock()
    
    def do_work(self) -> OperationResult:
        """Execute the folder operation."""
        result = OperationResult(
            success=False,
            source_path=self.operation.source_path,
            destination_path=self.operation.destination_path,
            operation_type=self.operation.copy_mode.value
        )
        
        try:
            # Validate operation
            if not self._validate_operation(result):
                return result
            
            # Calculate total work if progress tracking enabled
            if self.operation.calculate_progress:
                self.emit_status("Calculating operation size...")
                self._calculate_total_work()
            
            # Execute operation
            if self.operation.copy_mode == CopyMode.COPY:
                self._execute_copy(result)
            elif self.operation.copy_mode == CopyMode.MOVE:
                self._execute_move(result)
            elif self.operation.copy_mode == CopyMode.SYNC:
                self._execute_sync(result)
            elif self.operation.copy_mode == CopyMode.MIRROR:
                self._execute_mirror(result)
            
            # Finalize result
            result.finalize()
            result.success = len(result.errors) == 0
            
            return result
            
        except Exception as e:
            result.errors.append(f"Operation failed: {str(e)}")
            result.finalize()
            logging.error(f"Folder operation failed: {e}", exc_info=True)
            return result
    
    def _validate_operation(self, result: OperationResult) -> bool:
        """Validate operation parameters."""
        # Check source exists
        if not self.operation.source_path.exists():
            result.errors.append(f"Source path does not exist: {self.operation.source_path}")
            return False
        
        # Check source is directory
        if not self.operation.source_path.is_dir():
            result.errors.append(f"Source path is not a directory: {self.operation.source_path}")
            return False
        
        # Check destination path validity
        is_valid, error = self.validator.validate_path(self.operation.destination_path)
        if not is_valid:
            result.errors.append(f"Invalid destination path: {error}")
            return False
        
        # Create destination if needed
        if self.operation.create_destination:
            success, error = self.path_utilities.ensure_directory_exists(
                self.operation.destination_path.parent
            )
            if not success:
                result.errors.append(f"Cannot create destination directory: {error}")
                return False
        
        # Check available space
        if not self.operation.dry_run:
            total, used, free = self.path_utilities.get_available_space(
                self.operation.destination_path.parent
            )
            
            if self._total_bytes > 0 and free < self._total_bytes:
                result.warnings.append(
                    f"Insufficient disk space. Need: {format_bytes(self._total_bytes)}, "
                    f"Available: {format_bytes(free)}"
                )
        
        return True
    
    def _calculate_total_work(self) -> None:
        """Calculate total bytes and files to process."""
        try:
            self._files_to_process = []
            self._total_bytes = 0
            
            for item in self.operation.source_path.rglob('*'):
                if self.should_stop():
                    break
                
                if item.is_file():
                    path_info = self.path_utilities.get_path_info(item)
                    
                    # Apply filter
                    if self.operation.file_filter.matches(path_info):
                        self._files_to_process.append(item)
                        self._total_bytes += path_info.size_bytes
            
            self.emit_progress(
                f"Found {len(self._files_to_process)} files "
                f"({format_bytes(self._total_bytes)} total)",
                0
            )
            
        except Exception as e:
            logging.warning(f"Failed to calculate total work: {e}")
    
    def _execute_copy(self, result: OperationResult) -> None:
        """Execute copy operation."""
        self.emit_status("Starting copy operation...")
        
        for item in self.operation.source_path.rglob('*'):
            if self.should_stop():
                break
            
            try:
                self._process_item(item, result, move=False)
            except Exception as e:
                result.errors.append(f"Error processing {item}: {str(e)}")
                result.files_failed += 1
    
    def _execute_move(self, result: OperationResult) -> None:
        """Execute move operation."""
        self.emit_status("Starting move operation...")
        
        for item in self.operation.source_path.rglob('*'):
            if self.should_stop():
                break
            
            try:
                self._process_item(item, result, move=True)
            except Exception as e:
                result.errors.append(f"Error processing {item}: {str(e)}")
                result.files_failed += 1
    
    def _execute_sync(self, result: OperationResult) -> None:
        """Execute sync operation (copy newer files)."""
        self.emit_status("Starting sync operation...")
        
        # First pass: copy/update files from source
        for item in self.operation.source_path.rglob('*'):
            if self.should_stop():
                break
            
            try:
                self._process_item(item, result, move=False, sync_mode=True)
            except Exception as e:
                result.errors.append(f"Error processing {item}: {str(e)}")
                result.files_failed += 1
    
    def _execute_mirror(self, result: OperationResult) -> None:
        """Execute mirror operation (sync + delete extra files)."""
        self.emit_status("Starting mirror operation...")
        
        # First: sync files
        self._execute_sync(result)
        
        if self.should_stop():
            return
        
        # Second: remove files that don't exist in source
        self.emit_status("Removing extra files...")
        self._remove_extra_files(result)
    
    def _process_item(self, item: Path, result: OperationResult, move: bool = False, sync_mode: bool = False) -> None:
        """Process a single file or directory."""
        try:
            # Calculate relative path
            rel_path = item.relative_to(self.operation.source_path)
            dest_item = self.operation.destination_path / rel_path
            
            result.files_processed += 1
            
            # Handle directories
            if item.is_dir():
                if not dest_item.exists():
                    if not self.operation.dry_run:
                        dest_item.mkdir(parents=True, exist_ok=True)
                    result.directories_created += 1
                return
            
            # Skip non-files
            if not item.is_file():
                return
            
            # Get file info and apply filter
            path_info = self.path_utilities.get_path_info(item)
            if not self.operation.file_filter.matches(path_info):
                result.files_skipped += 1
                result.skipped_files.append(str(rel_path))
                return
            
            # Update progress
            self._current_file = str(rel_path)
            if self._total_bytes > 0:
                progress = int((self._bytes_copied / self._total_bytes) * 100)
                self.emit_progress(f"Processing: {self._current_file}", progress)
            else:
                self.emit_progress(f"Processing: {self._current_file}")
            
            # Handle file conflicts
            if dest_item.exists():
                action = self._resolve_conflict(item, dest_item, sync_mode)
                if action == "skip":
                    result.files_skipped += 1
                    result.skipped_files.append(str(rel_path))
                    return
                elif action == "rename":
                    dest_item = get_unique_filename(dest_item)
            
            # Check file size limits
            if path_info.size_bytes > MAX_SINGLE_FILE_SIZE:
                result.warnings.append(f"File too large, skipping: {rel_path}")
                result.files_skipped += 1
                return
            
            # Perform the operation
            if not self.operation.dry_run:
                success = self._copy_file(item, dest_item, move)
                if success:
                    if move:
                        result.files_moved += 1
                    else:
                        result.files_copied += 1
                    result.total_bytes_copied += path_info.size_bytes
                else:
                    result.files_failed += 1
                    result.failed_files.append(str(rel_path))
            else:
                # Dry run
                result.files_copied += 1
                result.total_bytes_copied += path_info.size_bytes
            
            # Update bytes copied for progress
            with self._lock:
                self._bytes_copied += path_info.size_bytes
            
        except Exception as e:
            result.errors.append(f"Failed to process {item}: {str(e)}")
            result.files_failed += 1
    
    def _resolve_conflict(self, source: Path, dest: Path, sync_mode: bool = False) -> str:
        """
        Resolve file conflict based on conflict resolution strategy.
        
        Returns:
            str: Action to take ("copy", "skip", "rename")
        """
        resolution = self.operation.conflict_resolution
        
        if resolution == ConflictResolution.SKIP:
            return "skip"
        elif resolution == ConflictResolution.OVERWRITE:
            return "copy"
        elif resolution == ConflictResolution.RENAME:
            return "rename"
        elif resolution == ConflictResolution.NEWER:
            source_time = source.stat().st_mtime
            dest_time = dest.stat().st_mtime
            return "copy" if source_time > dest_time else "skip"
        elif resolution == ConflictResolution.LARGER:
            source_size = source.stat().st_size
            dest_size = dest.stat().st_size
            return "copy" if source_size > dest_size else "skip"
        elif resolution == ConflictResolution.ASK:
            # In sync mode, default to newer
            if sync_mode:
                source_time = source.stat().st_mtime
                dest_time = dest.stat().st_mtime
                return "copy" if source_time > dest_time else "skip"
            else:
                # For GUI, emit signal and wait for response
                # This would need to be implemented in the UI layer
                return "skip"  # Default fallback
        
        return "skip"
    
    def _copy_file(self, source: Path, dest: Path, move: bool = False) -> bool:
        """
        Copy or move a single file with error handling.
        
        Args:
            source: Source file path
            dest: Destination file path
            move: Whether to move instead of copy
            
        Returns:
            bool: True if operation successful
        """
        try:
            # Ensure destination directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Perform operation
            if move:
                shutil.move(str(source), str(dest))
            else:
                if self.operation.preserve_timestamps:
                    shutil.copy2(source, dest)
                else:
                    shutil.copy(source, dest)
            
            # Verify copy if requested
            if self.operation.verify_copy and not move:
                if not self._verify_file_copy(source, dest):
                    return False
            
            return True
            
        except (IOError, OSError, shutil.Error) as e:
            logging.error(f"Failed to {'move' if move else 'copy'} {source} to {dest}: {e}")
            return False
    
    def _verify_file_copy(self, source: Path, dest: Path) -> bool:
        """Verify file was copied correctly by comparing checksums."""
        try:
            def get_file_hash(filepath: Path) -> str:
                hasher = hashlib.md5()
                with open(filepath, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                return hasher.hexdigest()
            
            source_hash = get_file_hash(source)
            dest_hash = get_file_hash(dest)
            
            return source_hash == dest_hash
            
        except Exception as e:
            logging.error(f"Failed to verify copy of {source}: {e}")
            return False
    
    def _remove_extra_files(self, result: OperationResult) -> None:
        """Remove files in destination that don't exist in source (mirror mode)."""
        try:
            if not self.operation.destination_path.exists():
                return
            
            # Get all files in destination
            dest_files = set()
            for item in self.operation.destination_path.rglob('*'):
                if item.is_file():
                    rel_path = item.relative_to(self.operation.destination_path)
                    dest_files.add(rel_path)
            
            # Get all files in source
            source_files = set()
            for item in self.operation.source_path.rglob('*'):
                if item.is_file():
                    rel_path = item.relative_to(self.operation.source_path)
                    
                    # Apply filter
                    path_info = self.path_utilities.get_path_info(item)
                    if self.operation.file_filter.matches(path_info):
                        source_files.add(rel_path)
            
            # Remove extra files
            extra_files = dest_files - source_files
            for rel_path in extra_files:
                if self.should_stop():
                    break
                
                try:
                    extra_file = self.operation.destination_path / rel_path
                    if not self.operation.dry_run:
                        extra_file.unlink()
                    
                    self.emit_progress(f"Removed extra file: {rel_path}")
                    
                except Exception as e:
                    result.warnings.append(f"Failed to remove extra file {rel_path}: {str(e)}")
            
        except Exception as e:
            result.errors.append(f"Failed to remove extra files: {str(e)}")


class FolderManager:
    """High-level folder management interface."""
    
    def __init__(self):
        """Initialize folder manager."""
        self.path_utilities = PathUtilities()
        self.validator = PathValidator()
    
    def create_operation_worker(self, operation: FolderOperation) -> FolderOperationWorker:
        """
        Create a worker for folder operation.
        
        Args:
            operation: Operation configuration
            
        Returns:
            FolderOperationWorker: Worker instance
        """
        return FolderOperationWorker(operation)
    
    def get_available_folders(self, base_path: Optional[Union[str, Path]] = None) -> List[Path]:
        """
        Get list of available folders in a directory.
        
        Args:
            base_path: Base directory to scan
            
        Returns:
            List[Path]: List of folder paths
        """
        if base_path is None:
            from core import get_application_path
            base_path = get_application_path()
        
        folders = []
        try:
            base_path = Path(base_path)
            if not base_path.exists() or not base_path.is_dir():
                return folders
            
            for item in base_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    folders.append(item)
            
            return sorted(folders, key=lambda x: x.name.lower())
            
        except (PermissionError, OSError) as e:
            logging.error(f"Failed to list folders in {base_path}: {e}")
            return []
    
    def get_folder_info(self, folder_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get comprehensive information about a folder.
        
        Args:
            folder_path: Path to folder
            
        Returns:
            Dict[str, Any]: Folder information
        """
        try:
            path = Path(folder_path)
            path_info = self.path_utilities.get_path_info(path)
            
            if not path_info.exists:
                return {'error': f"Folder does not exist: {path}"}
            
            if not path_info.is_directory:
                return {'error': f"Path is not a directory: {path}"}
            
            # Calculate directory size and file count
            total_size, file_count = self.path_utilities.get_directory_size(path)
            
            # Count subdirectories
            dir_count = 0
            try:
                for item in path.iterdir():
                    if item.is_dir():
                        dir_count += 1
            except (PermissionError, OSError):
                dir_count = -1  # Indicate access denied
            
            return {
                'name': path.name,
                'path': str(path),
                'size_bytes': total_size,
                'size_formatted': format_bytes(total_size),
                'file_count': file_count,
                'directory_count': dir_count,
                'is_readable': path_info.is_readable,
                'is_writable': path_info.is_writable,
                'is_hidden': path_info.is_hidden,
                'created': datetime.fromtimestamp(path_info.created_time) if path_info.created_time else None,
                'modified': datetime.fromtimestamp(path_info.modified_time) if path_info.modified_time else None,
                'permissions': path_info.permissions
            }
            
        except Exception as e:
            return {'error': f"Failed to get folder info: {str(e)}"}
    
    def copy_to_public_desktop(self, source_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        Copy a folder to the public desktop.
        
        Args:
            source_path: Source folder path
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        return self.path_utilities.copy_to_public_desktop(source_path)
    
    def estimate_operation_time(self, operation: FolderOperation) -> Tuple[int, int, float]:
        """
        Estimate operation time and requirements.
        
        Args:
            operation: Operation to estimate
            
        Returns:
            Tuple[int, int, float]: (file_count, total_bytes, estimated_seconds)
        """
        try:
            file_count = 0
            total_bytes = 0
            
            for item in operation.source_path.rglob('*'):
                if item.is_file():
                    path_info = self.path_utilities.get_path_info(item)
                    if operation.file_filter.matches(path_info):
                        file_count += 1
                        total_bytes += path_info.size_bytes
            
            # Estimate time based on file count and size
            # Rough estimates: 50 MB/s for large files, 100 files/s for small files
            time_for_size = total_bytes / (50 * 1024 * 1024)  # 50 MB/s
            time_for_count = file_count / 100  # 100 files/s
            estimated_seconds = max(time_for_size, time_for_count)
            
            return file_count, total_bytes, estimated_seconds
            
        except Exception as e:
            logging.error(f"Failed to estimate operation: {e}")
            return 0, 0, 0.0