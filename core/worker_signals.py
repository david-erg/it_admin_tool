"""
Worker signals for thread communication.

This module provides signal classes for worker threads to communicate
with the main UI thread safely. It handles both GUI and CLI modes with
conditional imports.
"""

import sys
from typing import Any, Callable, Optional

# Conditional import for PySide6 - only needed for GUI mode
try:
    from PySide6.QtCore import QObject, Signal
    HAS_QT = True
except ImportError:
    # Fallback for CLI mode or when PySide6 is not available
    HAS_QT = False
    
    # Mock QObject and Signal for compatibility
    class QObject:
        """Mock QObject for CLI mode."""
        def __init__(self):
            super().__init__()
    
    class Signal:
        """Mock Signal for CLI mode."""
        def __init__(self, *args):
            self._callbacks = []
        
        def connect(self, callback: Callable):
            """Connect a callback to this signal."""
            self._callbacks.append(callback)
        
        def disconnect(self, callback: Callable = None):
            """Disconnect a callback from this signal."""
            if callback and callback in self._callbacks:
                self._callbacks.remove(callback)
            elif callback is None:
                self._callbacks.clear()
        
        def emit(self, *args, **kwargs):
            """Emit the signal to all connected callbacks."""
            for callback in self._callbacks:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    print(f"Warning: Signal callback failed: {e}")


class WorkerSignals(QObject):
    """
    Signals for worker threads to communicate with main thread.
    
    This class provides a standard set of signals that worker threads
    can use to communicate progress, results, and errors back to the
    main UI thread in a thread-safe manner.
    
    Works in both GUI mode (with real Qt signals) and CLI mode (with mock signals).
    """
    
    def __init__(self):
        super().__init__()
        
        # Signal emitted when worker finishes (success or failure)
        self.finished = Signal()
        
        # Signal emitted when an error occurs (str: error message)
        self.error = Signal(str)
        
        # Signal emitted with results (object: result data)
        self.result = Signal(object)
        
        # Signal emitted with progress updates (str: progress message)
        self.progress = Signal(str)


class BaseWorker(QObject):
    """
    Base worker class with standard signals.
    
    This provides a common base for all worker classes, ensuring
    they have consistent signal interfaces and error handling.
    Works in both GUI and CLI modes.
    """
    
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self._is_cancelled = False
        self._progress_callback: Optional[Callable[[str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[str], None]):
        """
        Set a progress callback for CLI mode.
        
        Args:
            callback: Function to call with progress messages
        """
        self._progress_callback = callback
        if not HAS_QT:
            # In CLI mode, connect the callback to the progress signal
            self.signals.progress.connect(callback)
    
    def cancel(self):
        """Cancel the worker operation."""
        self._is_cancelled = True
    
    def is_cancelled(self) -> bool:
        """Check if the worker has been cancelled."""
        return self._is_cancelled
    
    def emit_progress(self, message: str):
        """
        Emit a progress message.
        
        Args:
            message: Progress message to emit
        """
        if not self._is_cancelled:
            self.signals.progress.emit(message)
            
            # In CLI mode, also call the callback directly if set
            if not HAS_QT and self._progress_callback:
                try:
                    self._progress_callback(message)
                except Exception as e:
                    print(f"Warning: Progress callback failed: {e}")
    
    def emit_error(self, error_message: str):
        """
        Emit an error message.
        
        Args:
            error_message: Error message to emit
        """
        self.signals.error.emit(error_message)
    
    def emit_result(self, result: Any):
        """
        Emit a result.
        
        Args:
            result: Result data to emit
        """
        if not self._is_cancelled:
            self.signals.result.emit(result)
    
    def emit_finished(self):
        """Emit the finished signal."""
        self.signals.finished.emit()
    
    def run(self):
        """
        Main worker method to be implemented by subclasses.
        
        This method should contain the main work to be performed
        in the worker thread.
        """
        raise NotImplementedError("Subclasses must implement the run method")


class CLIWorker(BaseWorker):
    """
    Specialized worker for CLI mode operations.
    
    This worker is designed to work well in CLI mode with
    direct progress output and simplified error handling.
    """
    
    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        super().__init__()
        
        # Set default progress callback for CLI
        if progress_callback is None:
            progress_callback = self._default_progress_callback
        
        self.set_progress_callback(progress_callback)
        
        # Connect error and result signals to CLI-friendly handlers
        self.signals.error.connect(self._handle_error)
        self.signals.result.connect(self._handle_result)
    
    def _default_progress_callback(self, message: str):
        """Default progress callback that prints to console."""
        print(f"Progress: {message}")
    
    def _handle_error(self, error_message: str):
        """Handle error messages in CLI mode."""
        print(f"Error: {error_message}", file=sys.stderr)
    
    def _handle_result(self, result: Any):
        """Handle results in CLI mode."""
        if result is not None:
            print(f"Result: {result}")


def create_worker(worker_class, *args, cli_mode: bool = False, 
                 progress_callback: Optional[Callable[[str], None]] = None, **kwargs):
    """
    Factory function to create worker instances.
    
    Args:
        worker_class: The worker class to instantiate
        *args: Positional arguments for the worker
        cli_mode: Whether to optimize for CLI mode
        progress_callback: Progress callback function
        **kwargs: Keyword arguments for the worker
    
    Returns:
        Worker instance
    """
    worker = worker_class(*args, **kwargs)
    
    if cli_mode or not HAS_QT:
        if hasattr(worker, 'set_progress_callback') and progress_callback:
            worker.set_progress_callback(progress_callback)
    
    return worker


def is_gui_mode() -> bool:
    """
    Check if GUI mode is available.
    
    Returns:
        bool: True if PySide6 is available and GUI mode is possible
    """
    return HAS_QT


def get_signal_info() -> dict:
    """
    Get information about the signal system.
    
    Returns:
        dict: Information about the current signal implementation
    """
    return {
        "has_qt": HAS_QT,
        "signal_type": "Qt Signals" if HAS_QT else "Mock Signals",
        "gui_mode_available": HAS_QT,
        "thread_safe": HAS_QT
    }