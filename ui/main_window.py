"""
Main window for the IT Admin Tool.

This module contains the main application window and handles the overall
UI layout, tab management, and window-level operations.
"""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTabWidget, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor

from core import (
    ConfigManager, check_admin_privileges, is_windows_platform,
    APP_NAME, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT
)
from .themes import ThemeManager
from .widgets import SoftwareTab, SystemInfoTab, WindowsSetupTab, FileOpsTab


class MainWindow(QMainWindow):
    """
    Main application window for the IT Administration Tool.
    
    This class manages the overall application layout, window properties,
    and coordinates between different tabs and the theme system.
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.theme_manager = ThemeManager(self.config_manager)
        
        # Initialize UI
        self._setup_window()
        self._setup_icon()
        self._check_platform_compatibility()
        self._init_ui()
        
        # Apply saved theme and geometry
        self._apply_saved_settings()
        
        # Initialize tabs with delayed loading for better startup performance
        QTimer.singleShot(100, self._initialize_tabs)
    
    def _setup_window(self):
        """Setup basic window properties."""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        
        # Load saved geometry or use defaults
        geometry = self.config_manager.get_window_geometry()
        self.resize(geometry["width"], geometry["height"])
        
        if geometry["maximized"]:
            self.showMaximized()
    
    def _setup_icon(self):
        """Set up the application icon."""
        icon_paths = [
            Path(__file__).parent.parent / "assets" / "toolbox_icon.png",
            Path(__file__).parent.parent / "assets" / "toolbox_icon.ico",
            Path(__file__).parent.parent / "toolbox_icon.png",
            Path(__file__).parent.parent / "toolbox_icon.ico"
        ]
        
        icon_set = False
        for icon_path in icon_paths:
            if icon_path.exists():
                try:
                    icon = QIcon(str(icon_path))
                    if not icon.isNull():
                        self.setWindowIcon(icon)
                        QApplication.instance().setWindowIcon(icon)
                        icon_set = True
                        break
                except Exception:
                    continue
        
        if not icon_set:
            self._create_default_icon()
    
    def _create_default_icon(self):
        """Create a simple default icon programmatically."""
        try:
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor(70, 130, 180))  # Steel blue background
            
            painter = QPainter(pixmap)
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawRect(10, 10, 44, 44)
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(20, 35, "IT")
            painter.end()
            
            icon = QIcon(pixmap)
            self.setWindowIcon(icon)
            QApplication.instance().setWindowIcon(icon)
        except Exception:
            pass  # Use default system icon if all fails
    
    def _check_platform_compatibility(self):
        """Check platform compatibility and show warnings if needed."""
        if not is_windows_platform():
            QMessageBox.warning(
                self, 
                "Platform Warning", 
                "This tool is designed for Windows systems. "
                "Some features may not work correctly on other platforms."
            )
    
    def _init_ui(self):
        """Initialize the main user interface."""
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 2, 10, 10)
        main_layout.setSpacing(3)
        
        # Add header
        header_widget = self._create_header()
        main_layout.addWidget(header_widget, 0)
        
        # Add separator
        separator = self._create_separator()
        main_layout.addWidget(separator, 0)
        
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, 1)
        
        # Set main widget
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def _create_header(self) -> QWidget:
        """Create the header layout with logo and controls."""
        header_widget = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(10)
        
        # Left side - Logo
        self.logo_label = QLabel("IT TOOLBOX")
        self.logo_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_layout.addWidget(self.logo_label)
        
        # Spacer
        header_layout.addStretch()
        
        # Right side - Admin info and controls
        right_widget = self._create_header_controls()
        header_layout.addWidget(right_widget)
        
        header_widget.setLayout(header_layout)
        header_widget.setFixedHeight(50)
        
        return header_widget
    
    def _create_header_controls(self) -> QWidget:
        """Create header control widgets (admin status, theme button)."""
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(2)
        
        # Admin status indicator
        admin_container = self._create_admin_status()
        right_layout.addWidget(admin_container)
        
        # Theme toggle button
        self.theme_button = QPushButton()
        self.theme_button.clicked.connect(self._toggle_theme)
        self.theme_button.setFixedHeight(30)
        self._update_theme_button()
        right_layout.addWidget(self.theme_button)
        
        right_widget.setLayout(right_layout)
        return right_widget
    
    def _create_admin_status(self) -> QWidget:
        """Create the admin status indicator."""
        admin_container = QWidget()
        admin_layout = QHBoxLayout()
        admin_layout.setContentsMargins(0, 0, 0, 0)
        admin_layout.setSpacing(5)
        
        is_admin = check_admin_privileges()
        
        # Status components
        privilege_label = QLabel("Privilege Level:")
        privilege_label.setStyleSheet("font-size: 11px;")
        
        indicator = QLabel("●")
        indicator.setStyleSheet(
            f"color: {'#4CAF50' if is_admin else '#F44336'}; font-size: 14px; font-weight: bold;"
        )
        
        status_text = QLabel(f"{'Administrator' if is_admin else 'Standard User'}")
        status_text.setStyleSheet(
            f"color: {'#4CAF50' if is_admin else '#F44336'}; font-weight: bold; font-size: 11px;"
        )
        
        admin_layout.addWidget(privilege_label)
        admin_layout.addWidget(indicator)
        admin_layout.addWidget(status_text)
        admin_container.setLayout(admin_layout)
        
        return admin_container
    
    def _create_separator(self) -> QFrame:
        """Create a thin separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setFixedHeight(1)
        return separator
    
    def _initialize_tabs(self):
        """Initialize all tab widgets with delayed loading."""
        try:
            # Create tab instances
            self.software_tab = SoftwareTab(self.config_manager)
            self.system_info_tab = SystemInfoTab(self.config_manager)
            self.windows_setup_tab = WindowsSetupTab(self.config_manager)
            self.file_ops_tab = FileOpsTab(self.config_manager)
            
            # Add tabs to the tab widget
            self.tabs.addTab(self.software_tab, "Software Management")
            self.tabs.addTab(self.system_info_tab, "System Information")
            self.tabs.addTab(self.windows_setup_tab, "Windows Setup")
            self.tabs.addTab(self.file_ops_tab, "File Operations")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Initialization Error",
                f"Failed to initialize application tabs:\n{str(e)}\n\n"
                "Please restart the application."
            )
    
    def _apply_saved_settings(self):
        """Apply saved theme and other settings."""
        # Apply theme
        self.theme_manager.apply_theme(self)
        self._update_logo_style()
        
        # Update theme button
        self._update_theme_button()
    
    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        self.config_manager.toggle_dark_mode()
        self.theme_manager.apply_theme(self)
        self._update_logo_style()
        self._update_theme_button()
    
    def _update_theme_button(self):
        """Update the theme button text and style."""
        is_dark = self.config_manager.is_dark_mode()
        self.theme_button.setText("☀️ Light Mode" if is_dark else "🌙 Dark Mode")
        
        self.theme_button.setStyleSheet("""
            QPushButton {
                background-color: #6c5ce7;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #5a4fcf;
            }
        """)
    
    def _update_logo_style(self):
        """Update logo style based on current theme."""
        is_dark = self.config_manager.is_dark_mode()
        
        logo_style = f"""
            QLabel {{
                font-size: 36px;
                font-weight: bold;
                color: {'#ffffff' if is_dark else '#2c3e50'};
                margin: 0px;
                padding: 0px;
            }}
        """
        
        self.logo_label.setStyleSheet(logo_style)
    
    def closeEvent(self, event):
        """Handle application close event to save settings."""
        try:
            # Save window geometry
            if not self.isMaximized():
                self.config_manager.save_window_geometry(
                    self.width(),
                    self.height(),
                    False
                )
            else:
                self.config_manager.save_window_geometry(
                    self.config_manager.get_setting("window_width", 1200),
                    self.config_manager.get_setting("window_height", 800),
                    True
                )
            
            # Cleanup any running operations in tabs
            if hasattr(self, 'software_tab'):
                self.software_tab.cleanup()
            if hasattr(self, 'system_info_tab'):
                self.system_info_tab.cleanup()
            if hasattr(self, 'windows_setup_tab'):
                self.windows_setup_tab.cleanup()
            if hasattr(self, 'file_ops_tab'):
                self.file_ops_tab.cleanup()
                
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")
        
        event.accept()
    
    def show_admin_warning(self):
        """Show administrator privileges warning if needed."""
        if not check_admin_privileges():
            QMessageBox.information(
                self,
                "Administrator Privileges", 
                "This application works best with administrator privileges.\n\n"
                "Some features (like package installation) may not work without admin rights.\n\n"
                "To run as administrator:\n"
                "• Right-click the application\n"
                "• Select 'Run as administrator'"
            )
    
    def get_config_manager(self) -> ConfigManager:
        """Get the configuration manager instance."""
        return self.config_manager
    
    def get_theme_manager(self) -> ThemeManager:
        """Get the theme manager instance."""
        return self.theme_manager
    
    def refresh_all_tabs(self):
        """Refresh content in all tabs."""
        try:
            if hasattr(self, 'system_info_tab'):
                self.system_info_tab.refresh_system_info()
            if hasattr(self, 'file_ops_tab'):
                self.file_ops_tab.refresh_folders()
        except Exception as e:
            print(f"Warning: Error refreshing tabs: {e}")
    
    def switch_to_tab(self, tab_name: str):
        """
        Switch to a specific tab by name.
        
        Args:
            tab_name: Name of the tab to switch to
        """
        tab_map = {
            "software": 0,
            "system_info": 1,
            "windows_setup": 2,
            "file_ops": 3
        }
        
        if tab_name.lower() in tab_map:
            self.tabs.setCurrentIndex(tab_map[tab_name.lower()])