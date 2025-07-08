"""
Theme management for the IT Admin Tool.

This module handles all theme-related functionality including dark/light mode
switching, stylesheet generation, and theme persistence.
"""

from typing import Dict, Any
from PySide6.QtWidgets import QWidget

from core import ConfigManager, THEME_COLORS


class ThemeManager:
    """
    Manages application themes and styling.
    
    This class provides centralized theme management with support for
    light and dark themes, dynamic theme switching, and consistent
    styling across all application components.
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._current_theme = "dark" if config_manager.is_dark_mode() else "light"
        self._theme_colors = THEME_COLORS
    
    def get_current_theme(self) -> str:
        """
        Get the current theme name.
        
        Returns:
            str: Current theme name ("light" or "dark")
        """
        return self._current_theme
    
    def is_dark_mode(self) -> bool:
        """
        Check if dark mode is currently active.
        
        Returns:
            bool: True if dark mode is active
        """
        return self._current_theme == "dark"
    
    def toggle_theme(self) -> str:
        """
        Toggle between light and dark themes.
        
        Returns:
            str: New theme name
        """
        self._current_theme = "light" if self._current_theme == "dark" else "dark"
        self.config_manager.set_dark_mode(self._current_theme == "dark")
        return self._current_theme
    
    def set_theme(self, theme_name: str) -> bool:
        """
        Set a specific theme.
        
        Args:
            theme_name: Theme name ("light" or "dark")
        
        Returns:
            bool: True if theme was set successfully
        """
        if theme_name in ["light", "dark"]:
            self._current_theme = theme_name
            self.config_manager.set_dark_mode(theme_name == "dark")
            return True
        return False
    
    def get_theme_colors(self, theme_name: str = None) -> Dict[str, str]:
        """
        Get color scheme for a specific theme.
        
        Args:
            theme_name: Theme name, uses current theme if None
        
        Returns:
            Dict[str, str]: Color scheme dictionary
        """
        if theme_name is None:
            theme_name = self._current_theme
        
        return self._theme_colors.get(theme_name, self._theme_colors["light"]).copy()
    
    def apply_theme(self, widget: QWidget) -> None:
        """
        Apply the current theme to a widget.
        
        Args:
            widget: Widget to apply theme to
        """
        if self._current_theme == "dark":
            self._apply_dark_theme(widget)
        else:
            self._apply_light_theme(widget)
    
    def _apply_dark_theme(self, widget: QWidget) -> None:
        """Apply dark theme stylesheet to widget."""
        dark_stylesheet = """
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #2b2b2b;
        }
        
        QTabBar::tab {
            background-color: #404040;
            color: #ffffff;
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid #555555;
        }
        
        QTabBar::tab:selected {
            background-color: #606060;
            border-bottom: 2px solid #0078d4;
        }
        
        QTabBar::tab:hover {
            background-color: #505050;
        }
        
        QPushButton {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #505050;
            border-color: #777777;
        }
        
        QPushButton:pressed {
            background-color: #353535;
        }
        
        QLineEdit {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 6px;
            border-radius: 4px;
        }
        
        QLineEdit:focus {
            border-color: #0078d4;
        }
        
        QTextEdit {
            background-color: #353535;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
        }
        
        QTableWidget {
            background-color: #353535;
            color: #ffffff;
            border: 1px solid #555555;
            gridline-color: #555555;
        }
        
        QTableWidget::item {
            padding: 4px;
            border-bottom: 1px solid #555555;
        }
        
        QTableWidget::item:selected {
            background-color: #0078d4;
        }
        
        QHeaderView::section {
            background-color: #404040;
            color: #ffffff;
            padding: 8px;
            border: 1px solid #555555;
            font-weight: bold;
        }
        
        QListWidget {
            background-color: #353535;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
        }
        
        QListWidget::item {
            padding: 4px;
            border-bottom: 1px solid #555555;
        }
        
        QListWidget::item:selected {
            background-color: #0078d4;
        }
        
        QComboBox {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 6px;
            border-radius: 4px;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #ffffff;
            margin-right: 5px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555555;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #ffffff;
        }
        
        QCheckBox {
            color: #ffffff;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #555555;
            border-radius: 3px;
            background-color: #404040;
        }
        
        QCheckBox::indicator:checked {
            background-color: #0078d4;
            border-color: #0078d4;
        }
        
        QLabel {
            color: #ffffff;
        }
        
        QProgressBar {
            border: 1px solid #555555;
            border-radius: 4px;
            text-align: center;
            background-color: #404040;
            color: #ffffff;
        }
        
        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 3px;
        }
        
        QFrame[frameShape="4"] {
            color: #555555;
        }
        
        QScrollArea {
            background-color: #2b2b2b;
            border: 1px solid #555555;
        }
        
        QScrollBar:vertical {
            background-color: #404040;
            width: 16px;
            border-radius: 8px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #606060;
            border-radius: 8px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #707070;
        }
        
        QScrollBar:horizontal {
            background-color: #404040;
            height: 16px;
            border-radius: 8px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #606060;
            border-radius: 8px;
            min-width: 20px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #707070;
        }
        """
        
        widget.setStyleSheet(dark_stylesheet)
    
    def _apply_light_theme(self, widget: QWidget) -> None:
        """Apply light theme stylesheet to widget."""
        light_stylesheet = """
        QMainWindow {
            background-color: #ffffff;
            color: #000000;
        }
        
        QWidget {
            background-color: #ffffff;
            color: #000000;
        }
        
        QTabWidget::pane {
            border: 1px solid #cccccc;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #f0f0f0;
            color: #000000;
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid #cccccc;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 2px solid #0078d4;
        }
        
        QTabBar::tab:hover {
            background-color: #e8e8e8;
        }
        
        QPushButton {
            background-color: #f0f0f0;
            color: #000000;
            border: 1px solid #cccccc;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #e8e8e8;
            border-color: #999999;
        }
        
        QPushButton:pressed {
            background-color: #d0d0d0;
        }
        
        QLineEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            padding: 6px;
            border-radius: 4px;
        }
        
        QLineEdit:focus {
            border-color: #0078d4;
        }
        
        QTextEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
        
        QTableWidget {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            gridline-color: #e0e0e0;
        }
        
        QTableWidget::item {
            padding: 4px;
            border-bottom: 1px solid #e0e0e0;
            background-color: #ffffff;
            color: #000000;
        }
        
        QTableWidget::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        
        QTableWidget::item:alternate {
            background-color: #f8f8f8;
        }
        
        QHeaderView::section {
            background-color: #f0f0f0;
            color: #000000;
            padding: 8px;
            border: 1px solid #cccccc;
            font-weight: bold;
        }
        
        QListWidget {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            border-radius: 4px;
        }
        
        QListWidget::item {
            padding: 4px;
            border-bottom: 1px solid #e0e0e0;
            background-color: #ffffff;
            color: #000000;
        }
        
        QListWidget::item:selected {
            background-color: #0078d4;
            color: #ffffff;
        }
        
        QListWidget::item:hover {
            background-color: #f0f0f0;
        }
        
        QComboBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            padding: 6px;
            border-radius: 4px;
        }
        
        QComboBox:hover {
            border-color: #999999;
        }
        
        QComboBox:focus {
            border-color: #0078d4;
        }
        
        QComboBox::drop-down {
            border: none;
            width: 20px;
            background-color: #f0f0f0;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid #000000;
            margin-right: 5px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #cccccc;
            selection-background-color: #0078d4;
            selection-color: #ffffff;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: #ffffff;
            color: #000000;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #000000;
            background-color: #ffffff;
        }
        
        QCheckBox {
            color: #000000;
            background-color: #ffffff;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #cccccc;
            border-radius: 3px;
            background-color: #ffffff;
        }
        
        QCheckBox::indicator:checked {
            background-color: #0078d4;
            border-color: #0078d4;
        }
        
        QCheckBox::indicator:hover {
            border-color: #999999;
        }
        
        QLabel {
            color: #000000;
            background-color: transparent;
        }
        
        QProgressBar {
            border: 1px solid #cccccc;
            border-radius: 4px;
            text-align: center;
            background-color: #f0f0f0;
            color: #000000;
        }
        
        QProgressBar::chunk {
            background-color: #0078d4;
            border-radius: 3px;
        }
        
        QFrame {
            background-color: #ffffff;
            color: #000000;
        }
        
        QFrame[frameShape="4"] {
            color: #cccccc;
        }
        
        QScrollArea {
            background-color: #ffffff;
            border: 1px solid #cccccc;
        }
        
        QScrollBar:vertical {
            background-color: #f0f0f0;
            width: 16px;
            border-radius: 8px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #cccccc;
            border-radius: 8px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #999999;
        }
        
        QScrollBar:horizontal {
            background-color: #f0f0f0;
            height: 16px;
            border-radius: 8px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #cccccc;
            border-radius: 8px;
            min-width: 20px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #999999;
        }
        """
        
        widget.setStyleSheet(light_stylesheet)
    
    def get_button_style(self, button_type: str = "default") -> str:
        """
        Get stylesheet for specific button types.
        
        Args:
            button_type: Type of button ("default", "primary", "success", "warning", "danger")
        
        Returns:
            str: Button stylesheet
        """
        base_style = """
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                border: 1px solid;
            }
            QPushButton:hover {
                opacity: 0.8;
            }
            QPushButton:pressed {
                opacity: 0.9;
            }
        """
        
        colors = {
            "primary": "background-color: #2196F3; color: white; border-color: #2196F3;",
            "success": "background-color: #4CAF50; color: white; border-color: #4CAF50;",
            "warning": "background-color: #FF9800; color: white; border-color: #FF9800;",
            "danger": "background-color: #e74c3c; color: white; border-color: #e74c3c;",
            "purple": "background-color: #9C27B0; color: white; border-color: #9C27B0;"
        }
        
        if button_type in colors:
            return base_style + colors[button_type]
        
        return base_style
    
    def get_theme_info(self) -> Dict[str, Any]:
        """
        Get comprehensive theme information.
        
        Returns:
            Dict[str, Any]: Theme information
        """
        return {
            "current_theme": self._current_theme,
            "is_dark_mode": self.is_dark_mode(),
            "available_themes": list(self._theme_colors.keys()),
            "colors": self.get_theme_colors()
        }
