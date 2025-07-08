"""
Windows setup and configuration tab widget.

This module contains the UI components for Windows system configuration,
including bloatware removal, essential settings, and user management.
"""

from typing import Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QCheckBox, QGroupBox, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt

from core import (
    ConfigManager, BLOATWARE_APPS, ESSENTIAL_SETTINGS, 
    COMMON_BLOATWARE, RECOMMENDED_SETTINGS
)


class WindowsSetupTab(QWidget):
    """
    Windows setup and configuration tab widget.
    
    This widget provides interfaces for removing Windows bloatware,
    applying essential Windows settings, and managing user accounts.
    """
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        
        # Checkbox storage
        self.bloatware_checkboxes: Dict[str, QCheckBox] = {}
        self.settings_checkboxes: Dict[str, QCheckBox] = {}
        
        self._init_ui()
        self._setup_connections()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create main tab widget with scroll area
        main_layout = QVBoxLayout()
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create content widget
        content_widget = QWidget()
        layout = QVBoxLayout()
        
        # Add sections
        bloatware_group = self._create_bloatware_section()
        layout.addWidget(bloatware_group)
        
        settings_group = self._create_settings_section()
        layout.addWidget(settings_group)
        
        admin_group = self._create_admin_section()
        layout.addWidget(admin_group)
        
        output_group = self._create_output_section()
        layout.addWidget(output_group)
        
        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
    
    def _create_bloatware_section(self) -> QGroupBox:
        """Create the bloatware removal section."""
        bloatware_group = QGroupBox("Windows Bloatware Remover")
        bloatware_layout = QVBoxLayout()
        
        # Selection buttons
        buttons_layout = QHBoxLayout()
        
        self.select_all_bloat_btn = QPushButton("Select All")
        self.deselect_all_bloat_btn = QPushButton("Deselect All")
        self.select_common_bloat_btn = QPushButton("Select Common Bloatware")
        
        buttons_layout.addWidget(self.select_all_bloat_btn)
        buttons_layout.addWidget(self.deselect_all_bloat_btn)
        buttons_layout.addWidget(self.select_common_bloat_btn)
        buttons_layout.addStretch()
        
        bloatware_layout.addLayout(buttons_layout)
        
        # Bloatware checkboxes in a grid
        checkboxes_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)
        
        row, col, max_cols = 0, 0, 2
        
        for package_name, display_name in BLOATWARE_APPS.items():
            checkbox = QCheckBox(display_name)
            checkbox.setToolTip(f"Package: {package_name}")
            self.bloatware_checkboxes[package_name] = checkbox
            
            grid_layout.addWidget(checkbox, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        checkboxes_widget.setLayout(grid_layout)
        bloatware_layout.addWidget(checkboxes_widget)
        
        # Remove button
        self.remove_bloatware_btn = QPushButton("Remove Selected Bloatware")
        self.remove_bloatware_btn.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; font-weight: bold; }"
        )
        bloatware_layout.addWidget(self.remove_bloatware_btn)
        
        bloatware_group.setLayout(bloatware_layout)
        return bloatware_group
    
    def _create_settings_section(self) -> QGroupBox:
        """Create the essential settings section."""
        settings_group = QGroupBox("Essential Windows Settings")
        settings_layout = QVBoxLayout()
        
        # Selection buttons
        settings_buttons_layout = QHBoxLayout()
        
        self.select_all_settings_btn = QPushButton("Select All Settings")
        self.deselect_all_settings_btn = QPushButton("Deselect All Settings")
        self.select_recommended_btn = QPushButton("Select Recommended")
        
        settings_buttons_layout.addWidget(self.select_all_settings_btn)
        settings_buttons_layout.addWidget(self.deselect_all_settings_btn)
        settings_buttons_layout.addWidget(self.select_recommended_btn)
        settings_buttons_layout.addStretch()
        
        settings_layout.addLayout(settings_buttons_layout)
        
        # Settings checkboxes in a grid
        settings_checkboxes_widget = QWidget()
        settings_grid_layout = QGridLayout()
        settings_grid_layout.setSpacing(5)
        
        settings_row, settings_col, max_settings_cols = 0, 0, 2
        
        for setting_key, setting_name in ESSENTIAL_SETTINGS.items():
            checkbox = QCheckBox(setting_name)
            self.settings_checkboxes[setting_key] = checkbox
            
            settings_grid_layout.addWidget(checkbox, settings_row, settings_col)
            
            settings_col += 1
            if settings_col >= max_settings_cols:
                settings_col = 0
                settings_row += 1
        
        settings_checkboxes_widget.setLayout(settings_grid_layout)
        settings_layout.addWidget(settings_checkboxes_widget)
        
        # Apply settings button
        self.apply_settings_btn = QPushButton("Apply Selected Settings")
        self.apply_settings_btn.setStyleSheet(
            "QPushButton { background-color: #3498db; color: white; font-weight: bold; }"
        )
        settings_layout.addWidget(self.apply_settings_btn)
        
        settings_group.setLayout(settings_layout)
        return settings_group
    
    def _create_admin_section(self) -> QGroupBox:
        """Create the local administrator creation section."""
        admin_group = QGroupBox("Create Local Administrator Account")
        admin_layout = QVBoxLayout()
        
        # User creation form
        form_layout = QHBoxLayout()
        
        # Username field
        username_layout = QVBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self.admin_username_input = QLineEdit()
        self.admin_username_input.setPlaceholderText("Enter administrator username")
        username_layout.addWidget(self.admin_username_input)
        form_layout.addLayout(username_layout)
        
        # Password field
        password_layout = QVBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.admin_password_input = QLineEdit()
        self.admin_password_input.setEchoMode(QLineEdit.Password)
        self.admin_password_input.setPlaceholderText("Enter secure password")
        password_layout.addWidget(self.admin_password_input)
        form_layout.addLayout(password_layout)
        
        # Full name field
        fullname_layout = QVBoxLayout()
        fullname_layout.addWidget(QLabel("Full Name (Optional):"))
        self.admin_fullname_input = QLineEdit()
        self.admin_fullname_input.setPlaceholderText("Enter full name")
        fullname_layout.addWidget(self.admin_fullname_input)
        form_layout.addLayout(fullname_layout)
        
        admin_layout.addLayout(form_layout)
        
        # Options
        options_layout = QHBoxLayout()
        self.admin_password_never_expires = QCheckBox("Password never expires")
        self.admin_cannot_change_password = QCheckBox("User cannot change password")
        options_layout.addWidget(self.admin_password_never_expires)
        options_layout.addWidget(self.admin_cannot_change_password)
        options_layout.addStretch()
        admin_layout.addLayout(options_layout)
        
        # Create user button
        self.create_admin_btn = QPushButton("Create Local Administrator")
        self.create_admin_btn.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; font-weight: bold; }"
        )
        admin_layout.addWidget(self.create_admin_btn)
        
        admin_group.setLayout(admin_layout)
        return admin_group
    
    def _create_output_section(self) -> QGroupBox:
        """Create the setup operations output section."""
        output_group = QGroupBox("Setup Operations Output")
        output_layout = QVBoxLayout()
        
        self.setup_output = QTextEdit()
        self.setup_output.setReadOnly(True)
        self.setup_output.setMaximumHeight(200)
        output_layout.addWidget(self.setup_output)
        
        output_group.setLayout(output_layout)
        return output_group
    
    def _setup_connections(self):
        """Setup signal connections."""
        # Bloatware connections
        self.select_all_bloat_btn.clicked.connect(lambda: self._toggle_all_bloatware(True))
        self.deselect_all_bloat_btn.clicked.connect(lambda: self._toggle_all_bloatware(False))
        self.select_common_bloat_btn.clicked.connect(self._select_common_bloatware)
        self.remove_bloatware_btn.clicked.connect(self._remove_bloatware)
        
        # Settings connections
        self.select_all_settings_btn.clicked.connect(lambda: self._toggle_all_settings(True))
        self.deselect_all_settings_btn.clicked.connect(lambda: self._toggle_all_settings(False))
        self.select_recommended_btn.clicked.connect(self._select_recommended_settings)
        self.apply_settings_btn.clicked.connect(self._apply_essential_settings)
        
        # Admin creation connections
        self.create_admin_btn.clicked.connect(self._create_local_admin)
    
    def _toggle_all_bloatware(self, checked: bool):
        """Toggle all bloatware checkboxes."""
        for checkbox in self.bloatware_checkboxes.values():
            checkbox.setChecked(checked)
    
    def _select_common_bloatware(self):
        """Select commonly removed bloatware."""
        # First deselect all
        self._toggle_all_bloatware(False)
        
        # Then select common ones
        for package_name in COMMON_BLOATWARE:
            if package_name in self.bloatware_checkboxes:
                self.bloatware_checkboxes[package_name].setChecked(True)
    
    def _remove_bloatware(self):
        """Remove selected bloatware applications."""
        selected_apps = []
        for package_name, checkbox in self.bloatware_checkboxes.items():
            if checkbox.isChecked():
                selected_apps.append(package_name)
        
        if not selected_apps:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "No Selection", "Please select at least one application to remove.")
            return
        
        # TODO: Implement bloatware removal using windows_setup module
        # This will be implemented when we create the windows_setup module
        app_list = '\\n'.join(f"• {self.bloatware_checkboxes[app].text()}" for app in selected_apps)
        self.setup_output.append("=== BLOATWARE REMOVAL ===")
        self.setup_output.append(f"Would remove {len(selected_apps)} application(s):")
        self.setup_output.append(app_list)
        self.setup_output.append("Note: Bloatware removal will be implemented in the windows_setup module.")
    
    def _toggle_all_settings(self, checked: bool):
        """Toggle all settings checkboxes."""
        for checkbox in self.settings_checkboxes.values():
            checkbox.setChecked(checked)
    
    def _select_recommended_settings(self):
        """Select recommended essential settings."""
        # First deselect all
        self._toggle_all_settings(False)
        
        # Then select recommended ones
        for setting_key in RECOMMENDED_SETTINGS:
            if setting_key in self.settings_checkboxes:
                self.settings_checkboxes[setting_key].setChecked(True)
    
    def _apply_essential_settings(self):
        """Apply selected essential Windows settings."""
        selected_settings = []
        for setting_key, checkbox in self.settings_checkboxes.items():
            if checkbox.isChecked():
                selected_settings.append(setting_key)
        
        if not selected_settings:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "No Selection", "Please select at least one setting to apply.")
            return
        
        # TODO: Implement settings application using windows_setup module
        # This will be implemented when we create the windows_setup module
        settings_list = '\\n'.join(f"• {ESSENTIAL_SETTINGS[key]}" for key in selected_settings)
        self.setup_output.append("=== APPLYING ESSENTIAL SETTINGS ===")
        self.setup_output.append(f"Would apply {len(selected_settings)} setting(s):")
        self.setup_output.append(settings_list)
        self.setup_output.append("Note: Settings application will be implemented in the windows_setup module.")
    
    def _create_local_admin(self):
        """Create a new local administrator account."""
        username = self.admin_username_input.text().strip()
        password = self.admin_password_input.text()
        fullname = self.admin_fullname_input.text().strip()
        
        # Basic validation
        if not username:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Input Error", "Please enter a username.")
            return
        
        if not password:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Input Error", "Please enter a password.")
            return
        
        if len(password) < 8:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Password Error", "Password must be at least 8 characters long.")
            return
        
        # TODO: Implement user creation using windows_setup module
        # This will be implemented when we create the windows_setup module
        self.setup_output.append("=== CREATING LOCAL ADMINISTRATOR ===")
        self.setup_output.append(f"Would create user account: {username}")
        if fullname:
            self.setup_output.append(f"Full name: {fullname}")
        self.setup_output.append(f"Administrator: Yes")
        self.setup_output.append(f"Password never expires: {'Yes' if self.admin_password_never_expires.isChecked() else 'No'}")
        self.setup_output.append("Note: User creation will be implemented in the windows_setup module.")
        
        # Clear the form for demo purposes
        self.admin_username_input.clear()
        self.admin_password_input.clear()
        self.admin_fullname_input.clear()
        self.admin_password_never_expires.setChecked(False)
        self.admin_cannot_change_password.setChecked(False)
    
    def cleanup(self):
        """Cleanup resources when the tab is closed."""
        # No background operations for this tab currently
        pass
    
    def get_selected_bloatware(self) -> list:
        """Get list of selected bloatware packages."""
        selected = []
        for package_name, checkbox in self.bloatware_checkboxes.items():
            if checkbox.isChecked():
                selected.append(package_name)
        return selected
    
    def get_selected_settings(self) -> list:
        """Get list of selected settings."""
        selected = []
        for setting_key, checkbox in self.settings_checkboxes.items():
            if checkbox.isChecked():
                selected.append(setting_key)
        return selected
    
    def clear_output(self):
        """Clear the setup output text."""
        self.setup_output.clear()
    
    def add_output_message(self, message: str):
        """Add a message to the setup output."""
        self.setup_output.append(message)
