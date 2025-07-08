"""
Worker signals for thread communication.

This module provides signal classes for worker threads to communicate
with the main UI thread safely.
"""

from typing import Any
from PySide6.QtCore import QObject, Signal


class WorkerSignals(QObject):
    """
    Signals for worker threads to communicate with main thread.
    
    This class provides a standard set of signals that worker threads
    can use to communicate progress, results, and errors back to the
    main UI thread in a thread-safe manner.
    """
    
    # Signal emitted when worker finishes (success or failure)
    finished = Signal()
    
    # Signal emitted when an error occurs (str: error message)
    error = Signal(str)
    
    # Signal emitted with results (object: result data)
    result = Signal(object)
    
    # Signal emitted with progress updates (str: progress message)
    progress = Signal(str)


class BaseWorker(QObject):
    """
    Base worker class with standard signals.
    
    This provides a common base for all worker classes, ensuring
    they have consistent signal interfaces and error handling.
    """
    
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self._is_cancelled = False
    
    def cancel(self):
        """Cancel the worker operation."""
        self._is_cancelled = True
    
    def is_cancelled(self) -> bool:
        """Check if the worker has been cancelled."""
        return self._is_cancelled
    
    def emit_progress(self, message: str):
        """Emit a progress message."""
        if not self._is_cancelled:
            self.signals.progress.emit(message)
    
    def emit_error(self, error_message: str):
        """Emit an error message."""
        self.signals.error.emit(error_message)
    
    def emit_result(self, result: Any):
        """Emit a result."""
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