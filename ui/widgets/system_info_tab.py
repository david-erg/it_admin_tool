"""
System information tab widget.

This module contains the UI components for displaying system information,
including hardware details, software information, and export functionality.
"""

import csv
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QProgressBar, QMessageBox, QFileDialog, QGroupBox
)
from PySide6.QtCore import QThread, QTimer
from PySide6.QtGui import QTextCursor

from core import ConfigManager


class SystemInfoTab(QWidget):
    """
    System information tab widget.
    
    This widget provides an interface for gathering, displaying, and exporting
    comprehensive system information including hardware and software details.
    """
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.system_info_data: Dict[str, str] = {}
        
        # Thread management
        self.sys_info_thread: Optional[QThread] = None
        
        self._init_ui()
        self._setup_connections()
        
        # Auto-load system info if enabled
        if self.config_manager.get_setting("auto_refresh_system_info", True):
            QTimer.singleShot(100, self.refresh_system_info)
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Control buttons section
        controls_group = self._create_controls_section()
        layout.addWidget(controls_group, 0)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar, 0)
        
        # System info display section
        display_group = self._create_display_section()
        layout.addWidget(display_group, 1)
        
        self.setLayout(layout)
    
    def _create_controls_section(self) -> QGroupBox:
        """Create the control buttons section."""
        controls_group = QGroupBox("System Information Controls")
        controls_layout = QHBoxLayout()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh System Info")
        self.refresh_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; font-weight: bold; }"
        )
        controls_layout.addWidget(self.refresh_btn)
        
        # Export button
        self.export_btn = QPushButton("Export to CSV")
        controls_layout.addWidget(self.export_btn)
        
        # Auto-refresh checkbox
        from PySide6.QtWidgets import QCheckBox
        self.auto_refresh_cb = QCheckBox("Auto-refresh on startup")
        self.auto_refresh_cb.setChecked(
            self.config_manager.get_setting("auto_refresh_system_info", True)
        )
        controls_layout.addWidget(self.auto_refresh_cb)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        
        return controls_group
    
    def _create_display_section(self) -> QGroupBox:
        """Create the system info display section."""
        display_group = QGroupBox("System Information")
        display_layout = QVBoxLayout()
        
        # System info text display
        self.sys_info_output = QTextEdit()
        self.sys_info_output.setReadOnly(True)
        self.sys_info_output.setMinimumHeight(400)
        
        # Set monospace font for better alignment
        font = self.sys_info_output.font()
        font.setFamily("Consolas, Monaco, monospace")
        self.sys_info_output.setFont(font)
        
        display_layout.addWidget(self.sys_info_output)
        display_group.setLayout(display_layout)
        
        return display_group
    
    def _setup_connections(self):
        """Setup signal connections."""
        self.refresh_btn.clicked.connect(self.refresh_system_info)
        self.export_btn.clicked.connect(self._export_system_info)
        self.auto_refresh_cb.toggled.connect(self._on_auto_refresh_changed)
    
    def refresh_system_info(self):
        """Refresh system information using a worker thread."""
        self.sys_info_output.clear()
        self.sys_info_output.append("Gathering system information...")
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Disable refresh button during operation
        self.refresh_btn.setEnabled(False)
        
        # TODO: Create and start system info worker thread
        # This will be implemented when we create the system_info module
        QTimer.singleShot(1000, self._mock_system_info_complete)
    
    def _mock_system_info_complete(self):
        """Mock system info completion for now."""
        # This is a placeholder until we implement the system_info module
        mock_data = {
            "Device Name": "DESKTOP-EXAMPLE",
            "Serial Number": "ABC123456789",
            "Logged User Name": "Administrator",
            "Manufacturer": "Dell Inc.",
            "Model": "OptiPlex 7090",
            "CPU": "Intel(R) Core(TM) i7-10700 CPU @ 2.90GHz",
            "GPU": "Intel(R) UHD Graphics 630",
            "RAM (GB)": "16.0",
            "Storage": "C: 500.0GB (Free: 250.0GB)",
            "OS Edition": "Microsoft Windows 11 Pro",
            "Anti-Virus": "Windows Defender",
            "Office Installed": "Microsoft 365 Apps for business",
            "IP Address": "192.168.1.100",
            "MAC Address": "AA-BB-CC-DD-EE-FF",
            "Updated Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self._display_system_info(mock_data)
        
        # Hide progress bar and re-enable button
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
    
    def _display_system_info(self, system_info: Dict[str, str]):
        """Display the gathered system information."""
        self.system_info_data = system_info
        self.sys_info_output.clear()
        
        # Create a nicely formatted display
        self.sys_info_output.append("=" * 60)
        self.sys_info_output.append("SYSTEM INFORMATION REPORT")
        self.sys_info_output.append("=" * 60)
        self.sys_info_output.append("")
        
        # Display each piece of information
        for key, value in system_info.items():
            # Format for better readability
            formatted_line = f"{key:20}: {value}"
            self.sys_info_output.append(formatted_line)
        
        self.sys_info_output.append("")
        self.sys_info_output.append("=" * 60)
        self.sys_info_output.append("Report generated successfully")
        self.sys_info_output.append("=" * 60)
        
        # Scroll to top - Fixed PySide6 syntax
        cursor = self.sys_info_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.sys_info_output.setTextCursor(cursor)
    
    def _export_system_info(self):
        """Export system information to a CSV file."""
        if not self.system_info_data:
            QMessageBox.information(
                self, 
                "No Data", 
                "Please refresh system information first before exporting."
            )
            return
        
        # Get save path from user
        default_filename = f"system_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save System Information",
            default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(["Property", "Value"])
                
                # Write data
                for key, value in self.system_info_data.items():
                    writer.writerow([key, value])
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"System information exported successfully to:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export system information:\n{str(e)}"
            )
    
    def _on_auto_refresh_changed(self, checked: bool):
        """Handle auto-refresh setting change."""
        self.config_manager.set_setting("auto_refresh_system_info", checked)
        self.config_manager.save_settings()
    
    def cleanup(self):
        """Cleanup resources when the tab is closed."""
        # Stop any running system info gathering
        if self.sys_info_thread and self.sys_info_thread.isRunning():
            self.sys_info_thread.quit()
            self.sys_info_thread.wait()
    
    def get_system_info_data(self) -> Dict[str, str]:
        """Get the current system information data."""
        return self.system_info_data.copy()
    
    def set_system_info_data(self, data: Dict[str, str]):
        """Set system information data (for testing or external updates)."""
        self.system_info_data = data.copy()
        self._display_system_info(data)
    
    def export_to_file(self, file_path: str) -> bool:
        """
        Export system information to a specific file path.
        
        Args:
            file_path: Path to save the file
            
        Returns:
            bool: True if export was successful
        """
        if not self.system_info_data:
            return False
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Property", "Value"])
                
                for key, value in self.system_info_data.items():
                    writer.writerow([key, value])
            
            return True
            
        except Exception:
            return False
    
    def get_formatted_info(self) -> str:
        """
        Get formatted system information as a string.
        
        Returns:
            str: Formatted system information
        """
        if not self.system_info_data:
            return "No system information available"
        
        lines = ["SYSTEM INFORMATION REPORT", "=" * 40, ""]
        
        for key, value in self.system_info_data.items():
            lines.append(f"{key}: {value}")
        
        lines.extend(["", "=" * 40])
        
        return "\n".join(lines)