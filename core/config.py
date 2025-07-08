"""
Configuration management for the IT Admin Tool.

This module handles loading, saving, and managing application configuration
including user settings, software presets, and application defaults.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from .constants import (
    SETTINGS_FILE,
    PRESETS_FILE, 
    DEFAULT_PRESETS
)
from .utils import get_application_path


class ConfigManager:
    """
    Manages application configuration including settings and presets.
    
    This class provides a centralized way to handle all configuration
    data for the application, including user settings, software presets,
    and theme preferences.
    """
    
    def __init__(self):
        self.app_path = get_application_path()
        self.settings_file = self.app_path / SETTINGS_FILE
        self.presets_file = self.app_path / PRESETS_FILE
        
        # Default settings
        self._default_settings = {
            "dark_mode": False,
            "window_width": 1200,
            "window_height": 800,
            "window_maximized": False,
            "last_preset_used": "",
            "auto_refresh_system_info": True,
            "confirm_package_installation": True,
            "confirm_bloatware_removal": True,
            "search_limit": 100,
            "command_timeout": 30
        }
        
        self._settings: Dict[str, Any] = {}
        self._presets: Dict[str, List[str]] = {}
        
        # Load configuration on initialization
        self.load_settings()
        self.load_presets()
    
    # Settings Management
    def load_settings(self) -> Dict[str, Any]:
        """
        Load application settings from file.
        
        Returns:
            Dict[str, Any]: Loaded settings with defaults for missing values
        """
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    
                # Merge with defaults to ensure all keys exist
                self._settings = {**self._default_settings, **loaded_settings}
            else:
                self._settings = self._default_settings.copy()
                
        except Exception as e:
            print(f"Warning: Failed to load settings: {e}")
            self._settings = self._default_settings.copy()
        
        return self._settings
    
    def save_settings(self) -> bool:
        """
        Save current settings to file.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
            return True
            
        except Exception as e:
            print(f"Warning: Failed to save settings: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a specific setting value.
        
        Args:
            key: Setting key
            default: Default value if key not found
        
        Returns:
            Any: Setting value or default
        """
        return self._settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a specific setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self._settings[key] = value
    
    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all current settings.
        
        Returns:
            Dict[str, Any]: All settings
        """
        return self._settings.copy()
    
    def reset_settings(self) -> None:
        """Reset all settings to defaults."""
        self._settings = self._default_settings.copy()
    
    # Presets Management
    def load_presets(self) -> Dict[str, List[str]]:
        """
        Load software presets from file.
        
        If the presets file doesn't exist, creates it with default presets.
        
        Returns:
            Dict[str, List[str]]: Loaded presets (returns package lists, not full objects)
        """
        try:
            if not self.presets_file.exists():
                self.create_default_presets_file()
            
            with open(self.presets_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                raw_presets = config.get("presets", {})
                
                # Convert presets to simple format (name -> package list)
                self._presets = {}
                for preset_name, preset_data in raw_presets.items():
                    if isinstance(preset_data, list):
                        # Old format: preset is directly a list of packages
                        self._presets[preset_name] = preset_data
                    elif isinstance(preset_data, dict):
                        # New format: preset is an object with packages array
                        packages = preset_data.get("packages", [])
                        self._presets[preset_name] = packages
                    else:
                        # Skip invalid preset format
                        continue
                        
        except Exception as e:
            print(f"Warning: Failed to load presets: {e}")
            self._presets = DEFAULT_PRESETS.copy()
            self.create_default_presets_file()
        
        return self._presets
    
    def save_presets(self) -> bool:
        """
        Save current presets to file.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            config = {"presets": self._presets}
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            return True
            
        except Exception as e:
            print(f"Warning: Failed to save presets: {e}")
            return False
    
    def get_presets(self) -> Dict[str, List[str]]:
        """
        Get all available presets.
        
        Returns:
            Dict[str, List[str]]: All presets
        """
        return self._presets.copy()
    
    def get_preset(self, name: str) -> Optional[List[str]]:
        """
        Get a specific preset by name.
        
        Args:
            name: Preset name
        
        Returns:
            Optional[List[str]]: Preset packages or None if not found
        """
        preset_data = self._presets.get(name)
        if preset_data is None:
            return None
        
        # Handle both old format (simple list) and new format (object with packages array)
        if isinstance(preset_data, list):
            # Old format: preset is directly a list of packages
            return preset_data
        elif isinstance(preset_data, dict):
            # New format: preset is an object with packages array
            return preset_data.get("packages", [])
        else:
            return None
    
    def add_preset(self, name: str, packages: List[str]) -> bool:
        """
        Add a new preset.
        
        Args:
            name: Preset name
            packages: List of package names
        
        Returns:
            bool: True if added successfully
        """
        try:
            self._presets[name] = packages.copy()
            return self.save_presets()
        except Exception:
            return False
    
    def remove_preset(self, name: str) -> bool:
        """
        Remove a preset.
        
        Args:
            name: Preset name to remove
        
        Returns:
            bool: True if removed successfully
        """
        try:
            if name in self._presets:
                del self._presets[name]
                return self.save_presets()
            return False
        except Exception:
            return False
    
    def get_preset_names(self) -> List[str]:
        """
        Get list of all preset names.
        
        Returns:
            List[str]: List of preset names
        """
        return list(self._presets.keys())
    
    def create_default_presets_file(self) -> bool:
        """
        Create the default presets configuration file.
        
        Returns:
            bool: True if created successfully, False otherwise
        """
        try:
            default_config = {"presets": DEFAULT_PRESETS}
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            return True
            
        except Exception as e:
            print(f"Warning: Could not create default presets config: {e}")
            return False
    
    # Theme Management
    def is_dark_mode(self) -> bool:
        """
        Check if dark mode is enabled.
        
        Returns:
            bool: True if dark mode is enabled
        """
        return self.get_setting("dark_mode", False)
    
    def set_dark_mode(self, enabled: bool) -> None:
        """
        Set dark mode preference.
        
        Args:
            enabled: Whether to enable dark mode
        """
        self.set_setting("dark_mode", enabled)
        self.save_settings()
    
    def toggle_dark_mode(self) -> bool:
        """
        Toggle dark mode setting.
        
        Returns:
            bool: New dark mode state
        """
        new_state = not self.is_dark_mode()
        self.set_dark_mode(new_state)
        return new_state
    
    # Window State Management
    def get_window_geometry(self) -> Dict[str, int]:
        """
        Get saved window geometry.
        
        Returns:
            Dict[str, int]: Window geometry (width, height, maximized)
        """
        return {
            "width": self.get_setting("window_width", 1200),
            "height": self.get_setting("window_height", 800),
            "maximized": self.get_setting("window_maximized", False)
        }
    
    def save_window_geometry(self, width: int, height: int, maximized: bool) -> None:
        """
        Save window geometry.
        
        Args:
            width: Window width
            height: Window height 
            maximized: Whether window is maximized
        """
        self.set_setting("window_width", width)
        self.set_setting("window_height", height)
        self.set_setting("window_maximized", maximized)
        self.save_settings()
    
    # Validation
    def validate_preset(self, packages: List[str]) -> bool:
        """
        Validate a preset's package list.
        
        Args:
            packages: List of package names to validate
        
        Returns:
            bool: True if preset is valid
        """
        if not isinstance(packages, list):
            return False
        
        if len(packages) == 0:
            return False
        
        # Check that all items are strings
        for package in packages:
            if not isinstance(package, str) or not package.strip():
                return False
        
        return True
    
    def cleanup_settings(self) -> None:
        """Remove any invalid or outdated settings."""
        # Remove settings that are no longer valid
        valid_keys = set(self._default_settings.keys())
        current_keys = set(self._settings.keys())
        
        for key in current_keys - valid_keys:
            del self._settings[key]
        
        self.save_settings()