"""
File operations tab widget.

This module contains the UI components for file and folder operations,
including copying folders to public desktop and other file management tasks.
"""

import os
import shutil
from pathlib import Path
from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QMessageBox, QGroupBox
)

from core import ConfigManager, get_application_path


class FileOpsTab(QWidget):
    """
    File operations tab widget.
    
    This widget provides an interface for various file operations including
    copying folder contents to the public desktop and other file management tasks.
    """
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        
        self._init_ui()
        self._setup_connections()
        self.refresh_folders()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Folder operations section
        folder_ops_group = self._create_folder_ops_section()
        layout.addWidget(folder_ops_group, 0)
        
        # Additional operations section (for future expansion)
        additional_ops_group = self._create_additional_ops_section()
        layout.addWidget(additional_ops_group, 0)
        
        # Output section
        output_group = self._create_output_section()
        layout.addWidget(output_group, 1)
        
        self.setLayout(layout)
    
    def _create_folder_ops_section(self) -> QGroupBox:
        """Create the folder operations section."""
        folder_ops_group = QGroupBox("Folder Operations")
        folder_ops_layout = QVBoxLayout()
        
        # Folder selection
        folder_ops_layout.addWidget(QLabel("Select Folder to Copy Contents to Public Desktop:"))
        
        self.folders_combo = QComboBox()
        folder_ops_layout.addWidget(self.folders_combo)
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        
        self.refresh_folders_btn = QPushButton("Refresh Folders")
        buttons_layout.addWidget(self.refresh_folders_btn)
        
        self.copy_folder_btn = QPushButton("Copy Folder Contents to Public Desktop")
        self.copy_folder_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; font-weight: bold; }"
        )
        buttons_layout.addWidget(self.copy_folder_btn)
        
        buttons_layout.addStretch()
        folder_ops_layout.addLayout(buttons_layout)
        
        folder_ops_group.setLayout(folder_ops_layout)
        return folder_ops_group
    
    def _create_additional_ops_section(self) -> QGroupBox:
        """Create additional operations section for future expansion."""
        additional_ops_group = QGroupBox("Additional File Operations")
        additional_ops_layout = QVBoxLayout()
        
        # Placeholder for future file operations
        info_label = QLabel("Additional file operations will be added here in future versions.")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        additional_ops_layout.addWidget(info_label)
        
        # Example buttons for future features
        future_buttons_layout = QHBoxLayout()
        
        self.backup_btn = QPushButton("Create Backup (Coming Soon)")
        self.backup_btn.setEnabled(False)
        future_buttons_layout.addWidget(self.backup_btn)
        
        self.restore_btn = QPushButton("Restore Files (Coming Soon)")
        self.restore_btn.setEnabled(False)
        future_buttons_layout.addWidget(self.restore_btn)
        
        future_buttons_layout.addStretch()
        additional_ops_layout.addLayout(future_buttons_layout)
        
        additional_ops_group.setLayout(additional_ops_layout)
        return additional_ops_group
    
    def _create_output_section(self) -> QGroupBox:
        """Create the file operations output section."""
        output_group = QGroupBox("File Operations Output")
        output_layout = QVBoxLayout()
        
        self.files_output = QTextEdit()
        self.files_output.setReadOnly(True)
        self.files_output.setMinimumHeight(200)
        output_layout.addWidget(self.files_output)
        
        # Clear output button
        clear_output_btn = QPushButton("Clear Output")
        clear_output_btn.clicked.connect(self.files_output.clear)
        output_layout.addWidget(clear_output_btn)
        
        output_group.setLayout(output_layout)
        return output_group
    
    def _setup_connections(self):
        """Setup signal connections."""
        self.refresh_folders_btn.clicked.connect(self.refresh_folders)
        self.copy_folder_btn.clicked.connect(self._copy_selected_folder)
    
    def refresh_folders(self):
        """Refresh the list of available folders."""
        self.folders_combo.clear()
        
        try:
            # Use the directory where the application is running from
            base_path = get_application_path()
            
            # Add folders from application directory
            folder_count = 0
            for path in base_path.iterdir():
                if path.is_dir() and not path.name.startswith('.'):
                    self.folders_combo.addItem(path.name)
                    folder_count += 1
            
            if folder_count == 0:
                self.folders_combo.addItem("No folders found")
                self.files_output.append("No folders found in application directory.")
            else:
                self.files_output.append(f"Found {folder_count} folder(s) in application directory.")
                
        except Exception as e:
            self.folders_combo.addItem("Error loading folders")
            self.files_output.append(f"Error refreshing folders: {str(e)}")
    
    def _copy_selected_folder(self):
        """Copy selected folder contents to public desktop."""
        selected_folder = self.folders_combo.currentText()
        
        if not selected_folder or selected_folder in ["No folders found", "Error loading folders"]:
            QMessageBox.information(self, "No Selection", "Please select a valid folder.")
            return
        
        try:
            # Source and destination paths
            source_path = get_application_path() / selected_folder
            dest_path = Path(os.environ.get('PUBLIC', 'C:\\\\Users\\\\Public')) / 'Desktop'
            
            # Validate paths
            if not source_path.exists():
                raise FileNotFoundError(f"Source folder does not exist: {source_path}")
            
            if not dest_path.exists():
                raise FileNotFoundError(f"Public Desktop does not exist: {dest_path}")
            
            # Confirm operation
            confirm = QMessageBox.question(
                self,
                "Confirm Copy Operation",
                f"Copy all contents from '{selected_folder}' to Public Desktop?\\n\\n"
                f"Source: {source_path}\\n"
                f"Destination: {dest_path}",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm != QMessageBox.Yes:
                return
            
            # Copy files
            self.files_output.append(f"Starting copy operation for '{selected_folder}'...")
            self.files_output.append(f"Source: {source_path}")
            self.files_output.append(f"Destination: {dest_path}")
            self.files_output.append("")
            
            copied_files = 0
            for item in source_path.iterdir():
                try:
                    dest_item = dest_path / item.name
                    
                    if item.is_file():
                        shutil.copy2(item, dest_item)
                        copied_files += 1
                        self.files_output.append(f"✓ Copied file: {item.name}")
                        
                    elif item.is_dir():
                        if dest_item.exists():
                            shutil.rmtree(dest_item)
                        shutil.copytree(item, dest_item)
                        copied_files += 1
                        self.files_output.append(f"✓ Copied directory: {item.name}")
                        
                except Exception as e:
                    self.files_output.append(f"✗ Failed to copy {item.name}: {str(e)}")
            
            self.files_output.append("")
            self.files_output.append(f"Copy operation completed. {copied_files} items copied successfully.")
            
            QMessageBox.information(
                self,
                "Copy Complete",
                f"Successfully copied {copied_files} items to Public Desktop."
            )
            
        except Exception as e:
            error_msg = f"Copy operation failed: {str(e)}"
            self.files_output.append(f"✗ {error_msg}")
            QMessageBox.critical(self, "Copy Error", error_msg)
    
    def cleanup(self):
        """Cleanup resources when the tab is closed."""
        # No background operations for this tab currently
        pass
    
    def get_available_folders(self) -> List[str]:
        """Get list of available folders."""
        folders = []
        for i in range(self.folders_combo.count()):
            folder_name = self.folders_combo.itemText(i)
            if folder_name not in ["No folders found", "Error loading folders"]:
                folders.append(folder_name)
        return folders
    
    def select_folder(self, folder_name: str) -> bool:
        """
        Select a specific folder in the combo box.
        
        Args:
            folder_name: Name of the folder to select
            
        Returns:
            bool: True if folder was found and selected
        """
        for i in range(self.folders_combo.count()):
            if self.folders_combo.itemText(i) == folder_name:
                self.folders_combo.setCurrentIndex(i)
                return True
        return False
    
    def add_output_message(self, message: str):
        """Add a message to the file operations output."""
        self.files_output.append(message)
    
    def get_public_desktop_path(self) -> Path:
        """Get the public desktop path."""
        return Path(os.environ.get('PUBLIC', 'C:\\\\Users\\\\Public')) / 'Desktop'
    
    def copy_folder_contents(self, source_folder: str, destination: Path = None) -> tuple:
        """
        Copy folder contents programmatically.
        
        Args:
            source_folder: Name of the source folder
            destination: Destination path (uses public desktop if None)
            
        Returns:
            tuple: (success: bool, copied_count: int, error_message: str)
        """
        try:
            source_path = get_application_path() / source_folder
            if destination is None:
                destination = self.get_public_desktop_path()
            
            if not source_path.exists():
                return False, 0, f"Source folder '{source_folder}' does not exist"
            
            if not destination.exists():
                return False, 0, f"Destination '{destination}' does not exist"
            
            copied_files = 0
            for item in source_path.iterdir():
                try:
                    dest_item = destination / item.name
                    
                    if item.is_file():
                        shutil.copy2(item, dest_item)
                        copied_files += 1
                    elif item.is_dir():
                        if dest_item.exists():
                            shutil.rmtree(dest_item)
                        shutil.copytree(item, dest_item)
                        copied_files += 1
                        
                except Exception as e:
                    # Continue with other files even if one fails
                    continue
            
            return True, copied_files, ""
            
        except Exception as e:
            return False, 0, str(e)
