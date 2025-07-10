"""
Configuration Manager for IT Admin Tool

Handles application settings, user preferences, and configuration persistence.
Provides a clean interface for managing all configuration data.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum

from .utils import (
    get_application_path, 
    load_json_config, 
    save_json_config,
    validate_path
)
from .constants import (
    SETTINGS_FILE,
    PRESETS_FILE,
    DEFAULT_PRESETS,
    THEME_COLORS,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT
)


class ThemeMode(Enum):
    """Application theme modes."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class LogLevel(Enum):
    """Logging levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class WindowSettings:
    """Window configuration settings."""
    width: int = DEFAULT_WINDOW_WIDTH
    height: int = DEFAULT_WINDOW_HEIGHT
    x: Optional[int] = None
    y: Optional[int] = None
    maximized: bool = False
    theme: str = ThemeMode.LIGHT.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WindowSettings':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class ApplicationSettings:
    """General application settings."""
    auto_check_updates: bool = True
    minimize_to_tray: bool = False
    start_minimized: bool = False
    remember_window_state: bool = True
    log_level: str = LogLevel.INFO.value
    max_log_files: int = 10
    enable_animations: bool = True
    confirm_dangerous_operations: bool = True
    auto_backup_settings: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationSettings':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class ChocolateySettings:
    """Chocolatey package manager settings."""
    auto_confirm: bool = True
    use_local_only: bool = False
    ignore_checksums: bool = True
    timeout_minutes: int = 10
    parallel_downloads: int = 3
    custom_source: Optional[str] = None
    proxy_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChocolateySettings':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class FileOperationSettings:
    """File operation settings."""
    default_copy_mode: str = "copy"
    verify_copies: bool = False
    preserve_timestamps: bool = True
    preserve_permissions: bool = True
    show_progress: bool = True
    conflict_resolution: str = "ask"
    max_file_size_gb: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileOperationSettings':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class SystemInfoSettings:
    """System information gathering settings."""
    include_hardware: bool = True
    include_software: bool = True
    include_network: bool = True
    include_performance: bool = False
    detailed_scan: bool = False
    timeout_seconds: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemInfoSettings':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class AppConfig:
    """Complete application configuration."""
    window: WindowSettings = field(default_factory=WindowSettings)
    application: ApplicationSettings = field(default_factory=ApplicationSettings)
    chocolatey: ChocolateySettings = field(default_factory=ChocolateySettings)
    file_operations: FileOperationSettings = field(default_factory=FileOperationSettings)
    system_info: SystemInfoSettings = field(default_factory=SystemInfoSettings)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "3.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire config to dictionary."""
        return {
            'window': self.window.to_dict(),
            'application': self.application.to_dict(),
            'chocolatey': self.chocolatey.to_dict(),
            'file_operations': self.file_operations.to_dict(),
            'system_info': self.system_info.to_dict(),
            'last_updated': self.last_updated,
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """Create config from dictionary."""
        return cls(
            window=WindowSettings.from_dict(data.get('window', {})),
            application=ApplicationSettings.from_dict(data.get('application', {})),
            chocolatey=ChocolateySettings.from_dict(data.get('chocolatey', {})),
            file_operations=FileOperationSettings.from_dict(data.get('file_operations', {})),
            system_info=SystemInfoSettings.from_dict(data.get('system_info', {})),
            last_updated=data.get('last_updated', datetime.now().isoformat()),
            version=data.get('version', '3.0')
        )


class ConfigManager:
    """
    Manages application configuration and settings persistence.
    
    Provides a centralized interface for loading, saving, and managing
    all application configuration data with automatic backup and validation.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager."""
        self.config_dir = config_dir or (get_application_path() / "config")
        self.config_file = self.config_dir / SETTINGS_FILE
        self.presets_file = self.config_dir / PRESETS_FILE
        self.backup_dir = self.config_dir / "backups"
        
        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self._config = self._load_config()
        self._presets = self._load_presets()
        
        logging.info(f"Configuration manager initialized: {self.config_dir}")
    
    @property
    def config(self) -> AppConfig:
        """Get current application configuration."""
        return self._config
    
    @property
    def presets(self) -> Dict[str, List[str]]:
        """Get current software presets."""
        return self._presets
    
    def _load_config(self) -> AppConfig:
        """Load configuration from file."""
        try:
            config_data = load_json_config(self.config_file, {})
            if config_data:
                return AppConfig.from_dict(config_data)
            else:
                logging.info("No existing configuration found, using defaults")
                return AppConfig()
        except Exception as e:
            logging.error(f"Failed to load configuration: {e}")
            return AppConfig()
    
    def _load_presets(self) -> Dict[str, List[str]]:
        """Load software presets from file."""
        try:
            presets_data = load_json_config(self.presets_file, DEFAULT_PRESETS)
            if isinstance(presets_data, dict) and all(
                isinstance(k, str) and isinstance(v, list) 
                for k, v in presets_data.items()
            ):
                return presets_data
            else:
                logging.warning("Invalid presets format, using defaults")
                return DEFAULT_PRESETS.copy()
        except Exception as e:
            logging.error(f"Failed to load presets: {e}")
            return DEFAULT_PRESETS.copy()
    
    def save_config(self, backup: bool = True) -> bool:
        """Save current configuration to file."""
        try:
            if backup and self.config_file.exists():
                self._create_backup()
            
            self._config.last_updated = datetime.now().isoformat()
            success = save_json_config(self.config_file, self._config.to_dict())
            
            if success:
                logging.info("Configuration saved successfully")
            return success
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
            return False
    
    def save_presets(self, backup: bool = True) -> bool:
        """Save current presets to file."""
        try:
            if backup and self.presets_file.exists():
                self._create_backup()
            
            success = save_json_config(self.presets_file, self._presets)
            if success:
                logging.info("Presets saved successfully")
            return success
        except Exception as e:
            logging.error(f"Error saving presets: {e}")
            return False
    
    def _create_backup(self) -> None:
        """Create backup of configuration files."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if self.config_file.exists():
                backup_config = self.backup_dir / f"settings_{timestamp}.json"
                import shutil
                shutil.copy2(self.config_file, backup_config)
            
            if self.presets_file.exists():
                backup_presets = self.backup_dir / f"presets_{timestamp}.json"
                import shutil
                shutil.copy2(self.presets_file, backup_presets)
        except Exception as e:
            logging.warning(f"Failed to create backup: {e}")
    
    # Theme Management Methods
    def is_dark_mode(self) -> bool:
        """Check if dark mode is enabled."""
        return self._config.window.theme == ThemeMode.DARK.value
    
    def toggle_dark_mode(self) -> bool:
        """Toggle dark mode on/off."""
        current_theme = self._config.window.theme
        new_theme = ThemeMode.LIGHT.value if current_theme == ThemeMode.DARK.value else ThemeMode.DARK.value
        self._config.window.theme = new_theme
        self.save_config(backup=False)
        return new_theme == ThemeMode.DARK.value
    
    def set_dark_mode(self, enabled: bool) -> None:
        """Set dark mode state."""
        self._config.window.theme = ThemeMode.DARK.value if enabled else ThemeMode.LIGHT.value
        self.save_config(backup=False)
    
    # Window Management Methods
    def get_window_geometry(self) -> Dict[str, Any]:
        """Get window geometry settings."""
        return {
            "width": self._config.window.width,
            "height": self._config.window.height,
            "maximized": self._config.window.maximized,
            "x": self._config.window.x,
            "y": self._config.window.y
        }
    
    def save_window_geometry(self, width: int, height: int, maximized: bool, x: int = None, y: int = None) -> None:
        """Save window geometry settings."""
        self._config.window.width = width
        self._config.window.height = height
        self._config.window.maximized = maximized
        if x is not None:
            self._config.window.x = x
        if y is not None:
            self._config.window.y = y
        self.save_config(backup=False)
    
    # General Settings Methods
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key."""
        # Map legacy setting keys to new structure
        legacy_mapping = {
            "dark_mode": lambda: self.is_dark_mode(),
            "window_width": lambda: self._config.window.width,
            "window_height": lambda: self._config.window.height,
            "window_maximized": lambda: self._config.window.maximized,
            "theme": lambda: self._config.window.theme,
            "log_level": lambda: self._config.application.log_level,
            "auto_check_updates": lambda: self._config.application.auto_check_updates,
            "confirm_dangerous_operations": lambda: self._config.application.confirm_dangerous_operations,
            "chocolatey_timeout": lambda: self._config.chocolatey.timeout_minutes,
            "chocolatey_parallel": lambda: self._config.chocolatey.parallel_downloads,
        }
        
        if key in legacy_mapping:
            return legacy_mapping[key]()
        
        return default
    
    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value by key."""
        # Map legacy setting keys to new structure
        if key == "dark_mode":
            self.set_dark_mode(value)
        elif key == "window_width":
            self._config.window.width = value
        elif key == "window_height":
            self._config.window.height = value
        elif key == "window_maximized":
            self._config.window.maximized = value
        elif key == "theme":
            self._config.window.theme = value
        elif key == "log_level":
            self._config.application.log_level = value
        elif key == "auto_check_updates":
            self._config.application.auto_check_updates = value
        elif key == "confirm_dangerous_operations":
            self._config.application.confirm_dangerous_operations = value
        elif key == "chocolatey_timeout":
            self._config.chocolatey.timeout_minutes = value
        elif key == "chocolatey_parallel":
            self._config.chocolatey.parallel_downloads = value
        
        self.save_config(backup=False)
    
    # Preset Management Methods
    def get_preset_names(self) -> List[str]:
        """Get list of available preset names."""
        return list(self._presets.keys())
    
    def get_preset(self, name: str) -> List[str]:
        """Get packages for a specific preset."""
        return self._presets.get(name, [])
    
    def add_preset(self, name: str, packages: List[str]) -> bool:
        """Add a new preset."""
        if not name or not packages:
            return False
        
        self._presets[name] = packages[:]
        return self.save_presets()
    
    def update_preset(self, name: str, packages: List[str]) -> bool:
        """Update an existing preset."""
        if name not in self._presets:
            return False
        
        self._presets[name] = packages[:]
        return self.save_presets()
    
    def delete_preset(self, name: str) -> bool:
        """Delete a preset."""
        if name not in self._presets:
            return False
        
        del self._presets[name]
        return self.save_presets()
    
    def reset_to_defaults(self, save: bool = True) -> bool:
        """Reset configuration to defaults."""
        try:
            if self.config_file.exists():
                self._create_backup()
            
            self._config = AppConfig()
            self._presets = DEFAULT_PRESETS.copy()
            
            if save:
                self.save_config(backup=False)
                self.save_presets(backup=False)
            
            logging.info("Configuration reset to defaults")
            return True
        except Exception as e:
            logging.error(f"Failed to reset configuration: {e}")
            return False
    
    def validate_config(self) -> List[str]:
        """Validate current configuration."""
        issues = []
        
        try:
            if self._config.window.width < 800:
                issues.append("Window width too small (minimum 800)")
            
            if self._config.window.height < 600:
                issues.append("Window height too small (minimum 600)")
            
            if self._config.chocolatey.timeout_minutes < 1:
                issues.append("Chocolatey timeout too small (minimum 1 minute)")
            
            if self._config.chocolatey.parallel_downloads < 1:
                issues.append("Parallel downloads must be at least 1")
            
            if self._config.file_operations.max_file_size_gb < 1:
                issues.append("Max file size too small (minimum 1 GB)")
            
            for preset_name, packages in self._presets.items():
                if not isinstance(packages, list):
                    issues.append(f"Preset '{preset_name}' is not a list")
                elif not all(isinstance(pkg, str) for pkg in packages):
                    issues.append(f"Preset '{preset_name}' contains non-string packages")
        except Exception as e:
            issues.append(f"Configuration validation error: {e}")
        
        return issues