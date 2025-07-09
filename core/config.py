"""
Configuration management for the IT Admin Tool.

This module handles loading, saving, and managing application configuration
including user settings, software presets, and application defaults.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .constants import (
    SETTINGS_FILE,
    PRESETS_FILE, 
    DEFAULT_PRESETS,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT
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
            "window_width": DEFAULT_WINDOW_WIDTH,
            "window_height": DEFAULT_WINDOW_HEIGHT,
            "window_maximized": False,
            "last_preset_used": "",
            "auto_refresh_system_info": True,
            "confirm_package_installation": True,
            "confirm_bloatware_removal": True,
            "search_limit": 100,
            "command_timeout": 30,
            "auto_save_settings": True,
            "log_level": "INFO",
            "export_format": "csv",
            "backup_before_operations": True,
            "theme": "light"
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
            # Add metadata
            settings_with_metadata = {
                "metadata": {
                    "last_saved": datetime.now().isoformat(),
                    "version": "2.1"
                },
                "settings": self._settings
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_with_metadata, f, indent=2)
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
        
        # Auto-save if enabled
        if self.get_setting("auto_save_settings", True):
            self.save_settings()
    
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
        self.save_settings()
    
    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """
        Update multiple settings at once.
        
        Args:
            new_settings: Dictionary of settings to update
        
        Returns:
            bool: True if updated successfully
        """
        try:
            self._settings.update(new_settings)
            return self.save_settings()
        except Exception:
            return False
    
    # Presets Management
    def load_presets(self) -> Dict[str, List[str]]:
        """
        Load software presets from file.
        
        If the presets file doesn't exist, creates it with default presets.
        
        Returns:
            Dict[str, List[str]]: Loaded presets
        """
        try:
            if not self.presets_file.exists():
                self.create_default_presets_file()
            
            with open(self.presets_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                # Handle both old and new format
                if "presets" in config:
                    raw_presets = config["presets"]
                else:
                    # Old format: entire file is presets
                    raw_presets = config
                
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
            config = {
                "metadata": {
                    "last_saved": datetime.now().isoformat(),
                    "version": "2.1",
                    "total_presets": len(self._presets)
                },
                "presets": self._presets
            }
            
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
        return self._presets.get(name)
    
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
    
    def update_preset(self, name: str, packages: List[str]) -> bool:
        """
        Update an existing preset.
        
        Args:
            name: Preset name
            packages: New list of packages
        
        Returns:
            bool: True if updated successfully
        """
        if name in self._presets:
            return self.add_preset(name, packages)
        return False
    
    def preset_exists(self, name: str) -> bool:
        """
        Check if a preset exists.
        
        Args:
            name: Preset name
        
        Returns:
            bool: True if preset exists
        """
        return name in self._presets
    
    def get_preset_names(self) -> List[str]:
        """
        Get list of all preset names.
        
        Returns:
            List[str]: List of preset names sorted alphabetically
        """
        return sorted(list(self._presets.keys()))
    
    def get_preset_count(self) -> int:
        """
        Get the number of presets.
        
        Returns:
            int: Number of presets
        """
        return len(self._presets)
    
    def create_default_presets_file(self) -> bool:
        """
        Create the default presets configuration file.
        
        Returns:
            bool: True if created successfully, False otherwise
        """
        try:
            self._presets = DEFAULT_PRESETS.copy()
            return self.save_presets()
            
        except Exception as e:
            print(f"Warning: Could not create default presets config: {e}")
            return False
    
    def import_presets_from_dict(self, presets_dict: Dict[str, List[str]], 
                                overwrite: bool = False) -> Tuple[int, int]:
        """
        Import presets from a dictionary.
        
        Args:
            presets_dict: Dictionary of presets to import
            overwrite: Whether to overwrite existing presets
        
        Returns:
            Tuple[int, int]: (imported_count, skipped_count)
        """
        imported = 0
        skipped = 0
        
        for name, packages in presets_dict.items():
            if name in self._presets and not overwrite:
                skipped += 1
            else:
                self._presets[name] = packages.copy()
                imported += 1
        
        if imported > 0:
            self.save_presets()
        
        return imported, skipped
    
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
    
    def get_theme(self) -> str:
        """
        Get current theme name.
        
        Returns:
            str: Current theme name
        """
        return self.get_setting("theme", "light")
    
    def set_theme(self, theme_name: str) -> None:
        """
        Set the current theme.
        
        Args:
            theme_name: Name of the theme to set
        """
        self.set_setting("theme", theme_name)
        # Update dark mode setting based on theme
        self.set_setting("dark_mode", theme_name.lower() == "dark")
    
    # Window State Management
    def get_window_geometry(self) -> Dict[str, int]:
        """
        Get saved window geometry.
        
        Returns:
            Dict[str, int]: Window geometry (width, height, maximized)
        """
        return {
            "width": self.get_setting("window_width", DEFAULT_WINDOW_WIDTH),
            "height": self.get_setting("window_height", DEFAULT_WINDOW_HEIGHT),
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
    
    # Utility Methods
    def reset_to_defaults(self) -> bool:
        """
        Reset both settings and presets to defaults.
        
        Returns:
            bool: True if reset successfully
        """
        try:
            self.reset_settings()
            self._presets = DEFAULT_PRESETS.copy()
            return self.save_presets()
        except Exception:
            return False
    
    def get_config_info(self) -> Dict[str, Any]:
        """
        Get information about the current configuration.
        
        Returns:
            Dict[str, Any]: Configuration information
        """
        return {
            "settings_file": str(self.settings_file),
            "presets_file": str(self.presets_file),
            "settings_count": len(self._settings),
            "presets_count": len(self._presets),
            "settings_file_exists": self.settings_file.exists(),
            "presets_file_exists": self.presets_file.exists(),
            "app_path": str(self.app_path)
        }
    
    def validate_config_files(self) -> Dict[str, bool]:
        """
        Validate configuration files.
        
        Returns:
            Dict[str, bool]: Validation results
        """
        results = {
            "settings_valid": False,
            "presets_valid": False,
            "settings_readable": False,
            "presets_readable": False
        }
        
        # Check settings file
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                results["settings_valid"] = True
                results["settings_readable"] = True
        except Exception:
            pass
        
        # Check presets file
        try:
            if self.presets_file.exists():
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                results["presets_valid"] = True
                results["presets_readable"] = True
        except Exception:
            pass
        
        return results