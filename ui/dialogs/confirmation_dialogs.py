"""
Confirmation dialogs and reusable dialog components.

This module provides standardized dialog components for confirmations,
information display, and user input throughout the application.
"""

from typing import List, Optional, Tuple
from PySide6.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QCheckBox, QLineEdit, QWidget
)
from PySide6.QtCore import Qt

from core import check_admin_privileges


class ConfirmationDialogs:
    """
    Collection of standardized confirmation and information dialogs.
    
    This class provides static methods for creating consistent dialogs
    throughout the application with proper styling and behavior.
    """
    
    @staticmethod
    def confirm_package_installation(packages: List[str], parent: QWidget = None) -> bool:
        """
        Show confirmation dialog for package installation.
        
        Args:
            packages: List of package names to install
            parent: Parent widget for the dialog
            
        Returns:
            bool: True if user confirmed installation
        """
        if not packages:
            return False
        
        package_list = '\n'.join(f"• {pkg}" for pkg in sorted(packages))
        is_admin = check_admin_privileges()
        
        message = (
            f"Install the following {len(packages)} package(s)?\n\n"
            f"{package_list}\n\n"
            f"Admin privileges: {'✓ Yes' if is_admin else '✗ No'}\n\n"
            "Note: Installation may take several minutes depending on "
            "package size and internet speed."
        )
        
        reply = QMessageBox.question(
            parent,
            "Confirm Installation",
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        
        return reply == QMessageBox.Yes
    
    @staticmethod
    def confirm_bloatware_removal(apps: List[str], parent: QWidget = None) -> bool:
        """
        Show confirmation dialog for bloatware removal.
        
        Args:
            apps: List of application display names to remove
            parent: Parent widget for the dialog
            
        Returns:
            bool: True if user confirmed removal
        """
        if not apps:
            return False
        
        app_list = '\n'.join(f"• {app}" for app in apps)
        
        message = (
            f"Remove the following {len(apps)} application(s)?\n\n"
            f"{app_list}\n\n"
            "Note: This action cannot be easily undone. "
            "Removed apps can be reinstalled from Microsoft Store if needed."
        )
        
        reply = QMessageBox.question(
            parent,
            "Confirm Bloatware Removal",
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        
        return reply == QMessageBox.Yes
    
    @staticmethod
    def confirm_settings_application(settings: List[str], parent: QWidget = None) -> bool:
        """
        Show confirmation dialog for applying Windows settings.
        
        Args:
            settings: List of setting descriptions to apply
            parent: Parent widget for the dialog
            
        Returns:
            bool: True if user confirmed application
        """
        if not settings:
            return False
        
        settings_list = '\n'.join(f"• {setting}" for setting in settings)
        
        message = (
            f"Apply the following {len(settings)} setting(s)?\n\n"
            f"{settings_list}\n\n"
            "Note: Some changes may require a system restart to take effect."
        )
        
        reply = QMessageBox.question(
            parent,
            "Confirm Settings Application",
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        
        return reply == QMessageBox.Yes
    
    @staticmethod
    def confirm_user_creation(username: str, fullname: str, options: dict, parent: QWidget = None) -> bool:
        """
        Show confirmation dialog for user account creation.
        
        Args:
            username: Username for the new account
            fullname: Full name for the account
            options: Dictionary of account options
            parent: Parent widget for the dialog
            
        Returns:
            bool: True if user confirmed creation
        """
        message = (
            f"Create local administrator account?\n\n"
            f"Username: {username}\n"
            f"Full Name: {fullname if fullname else 'Not specified'}\n"
            f"Administrator: Yes\n"
        )
        
        for option, value in options.items():
            message += f"{option}: {'Yes' if value else 'No'}\n"
        
        reply = QMessageBox.question(
            parent,
            "Confirm Account Creation",
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        
        return reply == QMessageBox.Yes
    
    @staticmethod
    def confirm_file_operation(operation: str, source: str, destination: str, parent: QWidget = None) -> bool:
        """
        Show confirmation dialog for file operations.
        
        Args:
            operation: Type of operation (e.g., "Copy", "Move", "Delete")
            source: Source path or description
            destination: Destination path or description
            parent: Parent widget for the dialog
            
        Returns:
            bool: True if user confirmed operation
        """
        message = (
            f"{operation} operation confirmation\n\n"
            f"Source: {source}\n"
            f"Destination: {destination}\n\n"
            f"Do you want to proceed with this {operation.lower()} operation?"
        )
        
        reply = QMessageBox.question(
            parent,
            f"Confirm {operation} Operation",
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        
        return reply == QMessageBox.Yes
    
    @staticmethod
    def show_admin_warning(parent: QWidget = None):
        """
        Show administrator privileges warning.
        
        Args:
            parent: Parent widget for the dialog
        """
        QMessageBox.information(
            parent,
            "Administrator Privileges",
            "This application works best with administrator privileges.\n\n"
            "Some features (like package installation) may not work without admin rights.\n\n"
            "To run as administrator:\n"
            "• Right-click the application\n"
            "• Select 'Run as administrator'"
        )
    
    @staticmethod
    def show_admin_required(feature: str, parent: QWidget = None):
        """
        Show administrator required dialog for specific features.
        
        Args:
            feature: Name of the feature requiring admin privileges
            parent: Parent widget for the dialog
        """
        QMessageBox.warning(
            parent,
            "Administrator Required",
            f"{feature} requires administrator privileges.\n\n"
            "Please restart this application as administrator."
        )
    
    @staticmethod
    def show_operation_complete(operation: str, success_count: int, total_count: int, parent: QWidget = None):
        """
        Show operation completion dialog.
        
        Args:
            operation: Name of the operation
            success_count: Number of successful operations
            total_count: Total number of operations attempted
            parent: Parent widget for the dialog
        """
        if success_count == total_count:
            QMessageBox.information(
                parent,
                f"{operation} Complete",
                f"Successfully completed {operation.lower()} for all {success_count} item(s)!"
            )
        elif success_count > 0:
            QMessageBox.warning(
                parent,
                f"{operation} Partial Success",
                f"Completed {operation.lower()} for {success_count} out of {total_count} item(s).\n\n"
                "Check the output for details on any failures."
            )
        else:
            QMessageBox.critical(
                parent,
                f"{operation} Failed",
                f"No items were successfully processed.\n\n"
                "Please check the output for error details."
            )
    
    @staticmethod
    def show_chocolatey_install_prompt(parent: QWidget = None) -> bool:
        """
        Show Chocolatey installation prompt.
        
        Args:
            parent: Parent widget for the dialog
            
        Returns:
            bool: True if user wants to install Chocolatey
        """
        reply = QMessageBox.question(
            parent,
            "Chocolatey Not Found",
            "Chocolatey package manager is required but not installed.\n\n"
            "Would you like to install Chocolatey automatically?\n\n"
            "Note: This requires administrator privileges and internet connection.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        return reply == QMessageBox.Yes
    
    @staticmethod
    def show_platform_warning(platform: str, parent: QWidget = None):
        """
        Show platform compatibility warning.
        
        Args:
            platform: Current platform name
            parent: Parent widget for the dialog
        """
        QMessageBox.warning(
            parent,
            "Platform Warning",
            f"This tool is designed for Windows systems. "
            f"Some features may not work correctly on {platform}."
        )


class DetailedConfirmationDialog(QDialog):
    """
    Custom dialog for detailed confirmations with scrollable content.
    
    This dialog provides a more detailed confirmation interface
    with scrollable content and custom buttons.
    """
    
    def __init__(self, title: str, message: str, details: List[str], parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(500, 400)
        self.result_value = False
        
        self._init_ui(message, details)
    
    def _init_ui(self, message: str, details: List[str]):
        """Initialize the dialog UI."""
        layout = QVBoxLayout()
        
        # Main message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Details in scrollable text area
        details_text = QTextEdit()
        details_text.setReadOnly(True)
        details_text.setMaximumHeight(200)
        
        for detail in details:
            details_text.append(f"• {detail}")
        
        layout.addWidget(details_text)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("Proceed")
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.ok_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }"
        )
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.ok_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def _on_ok_clicked(self):
        """Handle OK button click."""
        self.result_value = True
        self.accept()
    
    def _on_cancel_clicked(self):
        """Handle Cancel button click."""
        self.result_value = False
        self.reject()
    
    def get_result(self) -> bool:
        """Get the dialog result."""
        return self.result_value


class InputDialog(QDialog):
    """
    Custom input dialog for collecting user input.
    
    This dialog provides a flexible interface for collecting
    various types of user input with validation.
    """
    
    def __init__(self, title: str, fields: dict, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        
        self.fields = fields
        self.field_widgets = {}
        self.result_values = {}
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout()
        
        # Create input fields
        for field_name, field_config in self.fields.items():
            field_layout = QVBoxLayout()
            
            # Label
            label = QLabel(field_config.get('label', field_name))
            field_layout.addWidget(label)
            
            # Input widget
            if field_config.get('type') == 'password':
                widget = QLineEdit()
                widget.setEchoMode(QLineEdit.Password)
            elif field_config.get('type') == 'checkbox':
                widget = QCheckBox(field_config.get('text', ''))
            else:
                widget = QLineEdit()
            
            # Set placeholder if provided
            if hasattr(widget, 'setPlaceholderText') and 'placeholder' in field_config:
                widget.setPlaceholderText(field_config['placeholder'])
            
            # Set default value if provided
            if 'default' in field_config:
                if isinstance(widget, QCheckBox):
                    widget.setChecked(field_config['default'])
                else:
                    widget.setText(str(field_config['default']))
            
            self.field_widgets[field_name] = widget
            field_layout.addWidget(widget)
            layout.addLayout(field_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self._on_ok_clicked)
        self.ok_button.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; font-weight: bold; }"
        )
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.ok_button)
        
        layout.addLayout(buttons_layout)
        self.setLayout(layout)
    
    def _on_ok_clicked(self):
        """Handle OK button click with validation."""
        # Collect values
        for field_name, widget in self.field_widgets.items():
            if isinstance(widget, QCheckBox):
                self.result_values[field_name] = widget.isChecked()
            else:
                self.result_values[field_name] = widget.text()
        
        # Validate required fields
        for field_name, field_config in self.fields.items():
            if field_config.get('required', False):
                value = self.result_values[field_name]
                if not value or (isinstance(value, str) and not value.strip()):
                    QMessageBox.warning(
                        self,
                        "Validation Error",
                        f"Field '{field_config.get('label', field_name)}' is required."
                    )
                    return
        
        self.accept()
    
    def get_values(self) -> dict:
        """Get the collected input values."""
        return self.result_values.copy()
    
    @staticmethod
    def get_user_input(title: str, fields: dict, parent: QWidget = None) -> Tuple[bool, dict]:
        """
        Static method to get user input.
        
        Args:
            title: Dialog title
            fields: Dictionary defining input fields
            parent: Parent widget
            
        Returns:
            Tuple[bool, dict]: (accepted, values)
        """
        dialog = InputDialog(title, fields, parent)
        accepted = dialog.exec() == QDialog.Accepted
        values = dialog.get_values() if accepted else {}
        return accepted, values
