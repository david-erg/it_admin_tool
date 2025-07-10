"""
High-Level File Operations API

Provides a clean, GUI-friendly interface for all file operations.
Integrates folder management, path utilities, and worker threading.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Callable, Tuple, Any
from datetime import datetime
from dataclasses import dataclass

from core import (
    BaseWorker,
    WorkerManager,
    connect_worker_signals,
    get_application_path,
    format_bytes
)
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
from .path_utilities import (
    PathUtilities,
    PathValidator,
    SpecialFolder,
    PathInfo
)


@dataclass
class QuickCopyOptions:
    """Simple options for quick copy operations."""
    overwrite_existing: bool = False
    preserve_timestamps: bool = True
    show_progress: bool = True
    verify_copy: bool = False


class FileOperationsManager:
    """
    High-level file operations manager.
    
    Provides a simplified interface for common file operations
    with built-in progress tracking and error handling.
    """
    
    def __init__(self, worker_manager: Optional[WorkerManager] = None):
        """
        Initialize file operations manager.
        
        Args:
            worker_manager: Optional worker manager for threading
        """
        self.folder_manager = FolderManager()
        self.path_utilities = PathUtilities()
        self.validator = PathValidator()
        self.worker_manager = worker_manager or WorkerManager()
        
        # Operation tracking
        self._active_operations: Dict[str, FolderOperationWorker] = {}
        self._operation_counter = 0
        
        logging.info("File operations manager initialized")
    
    # =================================================================
    # Quick Operations (Simple Interface)
    # =================================================================
    
    def quick_copy_folder(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        options: Optional[QuickCopyOptions] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
        result_callback: Optional[Callable[[OperationResult], None]] = None
    ) -> str:
        """
        Quick folder copy with simple options.
        
        Args:
            source: Source folder path
            destination: Destination folder path
            options: Copy options
            progress_callback: Progress update callback
            result_callback: Result callback
            
        Returns:
            str: Operation ID for tracking
        """
        if options is None:
            options = QuickCopyOptions()
        
        # Create operation
        operation = FolderOperation(
            source_path=Path(source),
            destination_path=Path(destination),
            copy_mode=CopyMode.COPY,
            conflict_resolution=ConflictResolution.OVERWRITE if options.overwrite_existing else ConflictResolution.SKIP,
            preserve_timestamps=options.preserve_timestamps,
            calculate_progress=options.show_progress,
            verify_copy=options.verify_copy
        )
        
        return self.start_operation(operation, progress_callback, result_callback)
    
    def quick_move_folder(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        options: Optional[QuickCopyOptions] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
        result_callback: Optional[Callable[[OperationResult], None]] = None
    ) -> str:
        """
        Quick folder move with simple options.
        
        Args:
            source: Source folder path
            destination: Destination folder path
            options: Move options
            progress_callback: Progress update callback
            result_callback: Result callback
            
        Returns:
            str: Operation ID for tracking
        """
        if options is None:
            options = QuickCopyOptions()
        
        # Create operation
        operation = FolderOperation(
            source_path=Path(source),
            destination_path=Path(destination),
            copy_mode=CopyMode.MOVE,
            conflict_resolution=ConflictResolution.OVERWRITE if options.overwrite_existing else ConflictResolution.SKIP,
            preserve_timestamps=options.preserve_timestamps,
            calculate_progress=options.show_progress
        )
        
        return self.start_operation(operation, progress_callback, result_callback)
    
    def quick_sync_folders(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        progress_callback: Optional[Callable[[str], None]] = None,
        result_callback: Optional[Callable[[OperationResult], None]] = None
    ) -> str:
        """
        Quick folder synchronization (copy newer files).
        
        Args:
            source: Source folder path
            destination: Destination folder path
            progress_callback: Progress update callback
            result_callback: Result callback
            
        Returns:
            str: Operation ID for tracking
        """
        operation = FolderOperation(
            source_path=Path(source),
            destination_path=Path(destination),
            copy_mode=CopyMode.SYNC,
            conflict_resolution=ConflictResolution.NEWER,
            preserve_timestamps=True,
            calculate_progress=True
        )
        
        return self.start_operation(operation, progress_callback, result_callback)
    
    # =================================================================
    # Advanced Operations (Full Control)
    # =================================================================
    
    def start_operation(
        self,
        operation: FolderOperation,
        progress_callback: Optional[Callable[[str], None]] = None,
        result_callback: Optional[Callable[[OperationResult], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Start a folder operation with full control.
        
        Args:
            operation: Operation configuration
            progress_callback: Progress update callback
            result_callback: Result callback
            error_callback: Error callback
            
        Returns:
            str: Operation ID for tracking
        """
        try:
            # Generate operation ID
            self._operation_counter += 1
            operation_id = f"file_op_{self._operation_counter}"
            
            # Create worker
            worker = self.folder_manager.create_operation_worker(operation)
            
            # Connect signals
            connect_worker_signals(
                worker,
                progress_callback=progress_callback,
                result_callback=result_callback,
                error_callback=error_callback,
                finished_callback=lambda: self._operation_finished(operation_id)
            )
            
            # Start worker
            self.worker_manager.start_worker(worker, operation_id)
            self._active_operations[operation_id] = worker
            
            logging.info(f"Started file operation: {operation_id}")
            return operation_id
            
        except Exception as e:
            error_msg = f"Failed to start file operation: {str(e)}"
            logging.error(error_msg)
            if error_callback:
                error_callback(error_msg)
            return ""
    
    def stop_operation(self, operation_id: str) -> bool:
        """
        Stop a running operation.
        
        Args:
            operation_id: Operation to stop
            
        Returns:
            bool: True if operation was stopped
        """
        if operation_id in self._active_operations:
            worker = self._active_operations[operation_id]
            worker.stop()
            self.worker_manager.stop_worker(operation_id)
            return True
        return False
    
    def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """
        Get status of a running operation.
        
        Args:
            operation_id: Operation ID
            
        Returns:
            Dict[str, Any]: Operation status
        """
        if operation_id in self._active_operations:
            worker = self._active_operations[operation_id]
            return {
                'id': operation_id,
                'running': worker.is_running(),
                'current_file': getattr(worker, '_current_file', ''),
                'bytes_copied': getattr(worker, '_bytes_copied', 0),
                'total_bytes': getattr(worker, '_total_bytes', 0)
            }
        return {'id': operation_id, 'running': False}
    
    def _operation_finished(self, operation_id: str) -> None:
        """Handle operation completion."""
        if operation_id in self._active_operations:
            del self._active_operations[operation_id]
            logging.info(f"File operation completed: {operation_id}")
    
    # =================================================================
    # Folder Information and Management
    # =================================================================
    
    def get_folder_info(self, folder_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get detailed folder information.
        
        Args:
            folder_path: Path to folder
            
        Returns:
            Dict[str, Any]: Folder information
        """
        return self.folder_manager.get_folder_info(folder_path)
    
    def list_folders(self, base_path: Optional[Union[str, Path]] = None) -> List[Dict[str, Any]]:
        """
        List folders with basic information.
        
        Args:
            base_path: Base directory to scan
            
        Returns:
            List[Dict[str, Any]]: List of folder information
        """
        folders = self.folder_manager.get_available_folders(base_path)
        folder_info = []
        
        for folder in folders:
            try:
                info = self.get_folder_info(folder)
                if 'error' not in info:
                    folder_info.append(info)
            except Exception as e:
                logging.warning(f"Failed to get info for folder {folder}: {e}")
        
        return sorted(folder_info, key=lambda x: x['name'].lower())
    
    def estimate_operation(self, operation: FolderOperation) -> Dict[str, Any]:
        """
        Estimate operation requirements and time.
        
        Args:
            operation: Operation to estimate
            
        Returns:
            Dict[str, Any]: Estimation results
        """
        file_count, total_bytes, estimated_seconds = self.folder_manager.estimate_operation_time(operation)
        
        return {
            'file_count': file_count,
            'total_bytes': total_bytes,
            'total_bytes_formatted': format_bytes(total_bytes),
            'estimated_seconds': estimated_seconds,
            'estimated_minutes': estimated_seconds / 60,
            'estimated_formatted': self._format_duration(estimated_seconds)
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
    
    # =================================================================
    # Path Utilities
    # =================================================================
    
    def validate_path(self, path: Union[str, Path], must_exist: bool = False) -> Tuple[bool, str]:
        """
        Validate a file system path.
        
        Args:
            path: Path to validate
            must_exist: Whether path must exist
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        return self.validator.validate_path(path, must_exist)
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename for safe use.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        return self.validator.sanitize_filename(filename)
    
    def get_path_info(self, path: Union[str, Path]) -> PathInfo:
        """
        Get comprehensive path information.
        
        Args:
            path: Path to analyze
            
        Returns:
            PathInfo: Path information
        """
        return self.path_utilities.get_path_info(path)
    
    def get_special_folder(self, folder: SpecialFolder) -> Optional[Path]:
        """
        Get path to Windows special folder.
        
        Args:
            folder: Special folder identifier
            
        Returns:
            Optional[Path]: Path to special folder
        """
        return self.path_utilities.get_special_folder(folder)
    
    def ensure_directory_exists(self, directory: Union[str, Path]) -> Tuple[bool, str]:
        """
        Ensure a directory exists.
        
        Args:
            directory: Directory path
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        return self.path_utilities.ensure_directory_exists(directory)
    
    def get_disk_usage(self, path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get disk usage information for a path.
        
        Args:
            path: Path to check
            
        Returns:
            Dict[str, Any]: Disk usage information
        """
        total, used, free = self.path_utilities.get_available_space(path)
        
        return {
            'total_bytes': total,
            'used_bytes': used,
            'free_bytes': free,
            'total_formatted': format_bytes(total),
            'used_formatted': format_bytes(used),
            'free_formatted': format_bytes(free),
            'used_percent': (used / total * 100) if total > 0 else 0,
            'free_percent': (free / total * 100) if total > 0 else 0
        }
    
    # =================================================================
    # Convenience Functions
    # =================================================================
    
    def copy_to_public_desktop(self, source_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        Copy a file or folder to the public desktop.
        
        Args:
            source_path: Source path
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        return self.folder_manager.copy_to_public_desktop(source_path)
    
    def create_file_filter(
        self,
        patterns: Optional[List[str]] = None,
        extensions: Optional[List[str]] = None,
        min_size: Optional[int] = None,
        max_size: Optional[int] = None,
        include_hidden: bool = False,
        filter_type: FilterType = FilterType.INCLUDE
    ) -> FileFilter:
        """
        Create a file filter with common options.
        
        Args:
            patterns: File patterns (e.g., ["*.txt", "*.doc"])
            extensions: File extensions (e.g., [".txt", ".doc"])
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes
            include_hidden: Include hidden files
            filter_type: Filter type (include/exclude)
            
        Returns:
            FileFilter: Configured file filter
        """
        return FileFilter(
            patterns=patterns or [],
            extensions=set(ext.lower() for ext in (extensions or [])),
            min_size=min_size,
            max_size=max_size,
            include_hidden=include_hidden,
            filter_type=filter_type
        )
    
    def get_active_operations(self) -> List[Dict[str, Any]]:
        """
        Get list of active operations.
        
        Returns:
            List[Dict[str, Any]]: Active operations
        """
        operations = []
        for operation_id in list(self._active_operations.keys()):
            status = self.get_operation_status(operation_id)
            if status['running']:
                operations.append(status)
        return operations
    
    def stop_all_operations(self) -> int:
        """
        Stop all active operations.
        
        Returns:
            int: Number of operations stopped
        """
        operation_ids = list(self._active_operations.keys())
        stopped_count = 0
        
        for operation_id in operation_ids:
            if self.stop_operation(operation_id):
                stopped_count += 1
        
        return stopped_count
    
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.stop_all_operations()
            logging.info("File operations manager cleaned up")
        except Exception as e:
            logging.error(f"Error during file operations cleanup: {e}")


# =================================================================
# Module-Level Convenience Functions
# =================================================================

def copy_folder(
    source: Union[str, Path],
    destination: Union[str, Path],
    overwrite: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None
) -> OperationResult:
    """
    Simple synchronous folder copy function.
    
    Args:
        source: Source folder
        destination: Destination folder
        overwrite: Whether to overwrite existing files
        progress_callback: Progress callback
        
    Returns:
        OperationResult: Operation result
    """
    # Create temporary manager
    manager = FileOperationsManager()
    
    # Create operation
    operation = FolderOperation(
        source_path=Path(source),
        destination_path=Path(destination),
        copy_mode=CopyMode.COPY,
        conflict_resolution=ConflictResolution.OVERWRITE if overwrite else ConflictResolution.SKIP,
        calculate_progress=progress_callback is not None
    )
    
    # Execute synchronously
    worker = manager.folder_manager.create_operation_worker(operation)
    if progress_callback:
        connect_worker_signals(worker, progress_callback=progress_callback)
    
    return worker.do_work()


def validate_operation_paths(source: Union[str, Path], destination: Union[str, Path]) -> Tuple[bool, str]:
    """
    Validate source and destination paths for an operation.
    
    Args:
        source: Source path
        destination: Destination path
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    validator = PathValidator()
    
    # Validate source
    is_valid, error = validator.validate_path(source, must_exist=True)
    if not is_valid:
        return False, f"Invalid source path: {error}"
    
    source_path = Path(source)
    if not source_path.is_dir():
        return False, f"Source is not a directory: {source}"
    
    # Validate destination
    is_valid, error = validator.validate_path(destination)
    if not is_valid:
        return False, f"Invalid destination path: {error}"
    
    # Check for nested copy (copying into subdirectory of itself)
    try:
        dest_path = Path(destination).resolve()
        source_resolved = source_path.resolve()
        
        if str(dest_path).startswith(str(source_resolved)):
            return False, "Cannot copy directory into itself"
    except Exception:
        pass
    
    return True, ""