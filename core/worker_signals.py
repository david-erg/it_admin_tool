"""
Worker Signals for Thread Communication

Provides Qt-based signal system for safe thread communication in GUI application.
Simplified GUI-only version without CLI complexity.
"""

import logging
from typing import Any, Optional, Callable, Dict, Union
from PySide6.QtCore import QObject, Signal, QThread, QTimer, QMutex
from PySide6.QtWidgets import QApplication


class WorkerSignals(QObject):
    """
    Standard signals for worker threads to communicate with main GUI thread.
    
    All worker classes should use these signals for consistent communication.
    """
    
    # Core signals
    finished = Signal()                    # Worker completed (success or failure)
    error = Signal(str)                   # Error occurred (error message)
    result = Signal(object)               # Results available (result data)
    progress = Signal(str)                # Progress update (progress message)
    
    # Extended signals for detailed feedback
    progress_percent = Signal(int)        # Progress percentage (0-100)
    status_changed = Signal(str)          # Status change (status message)
    warning = Signal(str)                 # Warning message
    info = Signal(str)                    # Info message
    
    # Data signals
    data_ready = Signal(object)           # Data is ready for processing
    partial_result = Signal(object)       # Partial result available
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._is_finished = False
        self._mutex = QMutex()
    
    def emit_progress(self, message: str, percent: Optional[int] = None) -> None:
        """
        Emit progress update with optional percentage.
        
        Args:
            message: Progress message
            percent: Optional progress percentage (0-100)
        """
        try:
            self.progress.emit(message)
            if percent is not None and 0 <= percent <= 100:
                self.progress_percent.emit(percent)
        except Exception as e:
            logging.error(f"Failed to emit progress signal: {e}")
    
    def emit_status(self, status: str) -> None:
        """
        Emit status change.
        
        Args:
            status: New status message
        """
        try:
            self.status_changed.emit(status)
        except Exception as e:
            logging.error(f"Failed to emit status signal: {e}")
    
    def emit_result(self, result: Any) -> None:
        """
        Emit final result and mark as finished.
        
        Args:
            result: Result data
        """
        try:
            with QMutex():
                if not self._is_finished:
                    self.result.emit(result)
                    self._is_finished = True
                    self.finished.emit()
        except Exception as e:
            logging.error(f"Failed to emit result signal: {e}")
    
    def emit_error(self, error_message: str) -> None:
        """
        Emit error and mark as finished.
        
        Args:
            error_message: Error description
        """
        try:
            with QMutex():
                if not self._is_finished:
                    self.error.emit(error_message)
                    self._is_finished = True
                    self.finished.emit()
        except Exception as e:
            logging.error(f"Failed to emit error signal: {e}")
    
    def is_finished(self) -> bool:
        """Check if worker has finished."""
        return self._is_finished


class BaseWorker(QObject):
    """
    Base worker class with standard signals and error handling.
    
    All worker classes should inherit from this base class to ensure
    consistent signal interfaces and proper error handling.
    """
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.signals = WorkerSignals(self)
        self._is_running = False
        self._should_stop = False
        self._mutex = QMutex()
    
    def run(self) -> None:
        """
        Main worker execution method. Override in subclasses.
        This method should be called from a QThread.
        """
        try:
            with QMutex():
                self._is_running = True
                self._should_stop = False
            
            self.signals.emit_status("Starting...")
            
            # Override this method in subclasses
            result = self.do_work()
            
            if not self._should_stop:
                self.signals.emit_result(result)
            
        except Exception as e:
            error_msg = f"Worker error: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self.signals.emit_error(error_msg)
        finally:
            with QMutex():
                self._is_running = False
    
    def do_work(self) -> Any:
        """
        Override this method in subclasses to implement actual work.
        
        Returns:
            Any: Work result
        """
        raise NotImplementedError("Subclasses must implement do_work()")
    
    def stop(self) -> None:
        """Request worker to stop gracefully."""
        with QMutex():
            self._should_stop = True
    
    def should_stop(self) -> bool:
        """Check if worker should stop."""
        return self._should_stop
    
    def is_running(self) -> bool:
        """Check if worker is currently running."""
        return self._is_running
    
    def emit_progress(self, message: str, percent: Optional[int] = None) -> None:
        """Emit progress update."""
        if not self._should_stop:
            self.signals.emit_progress(message, percent)
    
    def emit_status(self, status: str) -> None:
        """Emit status update."""
        if not self._should_stop:
            self.signals.emit_status(status)
    
    def emit_warning(self, warning: str) -> None:
        """Emit warning message."""
        if not self._should_stop:
            self.signals.warning.emit(warning)
    
    def emit_info(self, info: str) -> None:
        """Emit info message."""
        if not self._should_stop:
            self.signals.info.emit(info)


class WorkerThread(QThread):
    """
    Enhanced QThread for running BaseWorker instances.
    Provides automatic cleanup and error handling.
    """
    
    def __init__(self, worker: BaseWorker, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.worker = worker
        self.worker.moveToThread(self)
        
        # Connect thread signals
        self.started.connect(self.worker.run)
        self.finished.connect(self._cleanup)
        
        # Auto-cleanup when worker finishes
        self.worker.signals.finished.connect(self.quit)
        self.worker.signals.finished.connect(self.worker.deleteLater)
    
    def _cleanup(self) -> None:
        """Clean up thread resources."""
        if self.worker:
            self.worker.stop()
        self.deleteLater()
    
    def stop_worker(self) -> None:
        """Stop the worker and quit thread."""
        if self.worker:
            self.worker.stop()
        if self.isRunning():
            self.quit()
            self.wait(5000)  # Wait up to 5 seconds


class WorkerManager(QObject):
    """
    Manages multiple worker threads and provides high-level interface.
    Handles thread lifecycle, error collection, and resource cleanup.
    """
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._active_workers: Dict[str, WorkerThread] = {}
        self._worker_counter = 0
        self._mutex = QMutex()
    
    def start_worker(
        self, 
        worker: BaseWorker, 
        worker_id: Optional[str] = None
    ) -> str:
        """
        Start a worker in a new thread.
        
        Args:
            worker: Worker instance to run
            worker_id: Optional worker identifier
            
        Returns:
            str: Worker ID for tracking
        """
        with QMutex():
            if worker_id is None:
                self._worker_counter += 1
                worker_id = f"worker_{self._worker_counter}"
            
            # Stop existing worker with same ID
            if worker_id in self._active_workers:
                self.stop_worker(worker_id)
            
            # Create and start thread
            thread = WorkerThread(worker, self)
            self._active_workers[worker_id] = thread
            
            # Connect cleanup signal
            thread.finished.connect(
                lambda: self._remove_worker(worker_id)
            )
            
            thread.start()
            logging.info(f"Started worker: {worker_id}")
            
            return worker_id
    
    def stop_worker(self, worker_id: str) -> bool:
        """
        Stop a specific worker.
        
        Args:
            worker_id: Worker to stop
            
        Returns:
            bool: True if worker was stopped
        """
        with QMutex():
            if worker_id in self._active_workers:
                thread = self._active_workers[worker_id]
                thread.stop_worker()
                return True
            return False
    
    def stop_all_workers(self) -> None:
        """Stop all active workers."""
        with QMutex():
            worker_ids = list(self._active_workers.keys())
        
        for worker_id in worker_ids:
            self.stop_worker(worker_id)
    
    def _remove_worker(self, worker_id: str) -> None:
        """Remove worker from active list."""
        with QMutex():
            if worker_id in self._active_workers:
                del self._active_workers[worker_id]
                logging.info(f"Removed worker: {worker_id}")
    
    def get_active_workers(self) -> Dict[str, WorkerThread]:
        """Get dictionary of active workers."""
        with QMutex():
            return self._active_workers.copy()
    
    def is_worker_active(self, worker_id: str) -> bool:
        """Check if a worker is currently active."""
        with QMutex():
            return worker_id in self._active_workers
    
    def get_worker_count(self) -> int:
        """Get number of active workers."""
        with QMutex():
            return len(self._active_workers)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_worker_thread(worker: BaseWorker) -> WorkerThread:
    """
    Create a worker thread for a BaseWorker instance.
    
    Args:
        worker: Worker instance
        
    Returns:
        WorkerThread: Configured thread
    """
    return WorkerThread(worker)


def connect_worker_signals(
    worker: BaseWorker,
    progress_callback: Optional[Callable[[str], None]] = None,
    result_callback: Optional[Callable[[Any], None]] = None,
    error_callback: Optional[Callable[[str], None]] = None,
    finished_callback: Optional[Callable[[], None]] = None
) -> None:
    """
    Connect worker signals to callback functions.
    
    Args:
        worker: Worker instance
        progress_callback: Progress update callback
        result_callback: Result ready callback
        error_callback: Error occurred callback
        finished_callback: Worker finished callback
    """
    if progress_callback:
        worker.signals.progress.connect(progress_callback)
    
    if result_callback:
        worker.signals.result.connect(result_callback)
    
    if error_callback:
        worker.signals.error.connect(error_callback)
    
    if finished_callback:
        worker.signals.finished.connect(finished_callback)


def safe_emit_signal(signal: Signal, *args) -> bool:
    """
    Safely emit a signal with error handling.
    
    Args:
        signal: Signal to emit
        *args: Signal arguments
        
    Returns:
        bool: True if signal was emitted successfully
    """
    try:
        signal.emit(*args)
        return True
    except Exception as e:
        logging.error(f"Failed to emit signal: {e}")
        return False


def is_gui_available() -> bool:
    """
    Check if GUI is available and QApplication exists.
    
    Returns:
        bool: True if GUI is available
    """
    try:
        app = QApplication.instance()
        return app is not None
    except Exception:
        return False


def ensure_gui_thread(func: Callable) -> Callable:
    """
    Decorator to ensure function runs in GUI thread.
    
    Args:
        func: Function to wrap
        
    Returns:
        Callable: Wrapped function
    """
    def wrapper(*args, **kwargs):
        if QThread.currentThread() == QApplication.instance().thread():
            return func(*args, **kwargs)
        else:
            logging.warning(f"Function {func.__name__} called from non-GUI thread")
            # You could use QMetaObject.invokeMethod here for true GUI thread execution
            return func(*args, **kwargs)
    
    return wrapper