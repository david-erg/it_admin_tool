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
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Optional custom configuration directory
        """
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
            # Validate presets structure
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
        """
        Save current configuration to file.
        
        Args:
            backup: Whether to create backup before saving
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Create backup if requested
            if backup and self.config_file.exists():
                self._create_backup()
            
            # Update timestamp
            self._config.last_updated = datetime.now().isoformat()
            
            # Save configuration
            success = save_json_config(self.config_file, self._config.to_dict())
            
            if success:
                logging.info("Configuration saved successfully")
            else:
                logging.error("Failed to save configuration")
            
            return success
            
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
            return False
    
    def save_presets(self, backup: bool = True) -> bool:
        """
        Save current presets to file.
        
        Args:
            backup: Whether to create backup before saving
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Create backup if requested
            if backup and self.presets_file.exists():
                self._create_presets_backup()
            
            # Save presets
            success = save_json_config(self.presets_file, self._presets)
            
            if success:
                logging.info("Presets saved successfully")
            else:
                logging.error("Failed to save presets")
            
            return success
            
        except Exception as e:
            logging.error(f"Error saving presets: {e}")
            return False
    
    def _create_backup(self) -> None:
        """Create backup of current configuration."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"settings_{timestamp}.json"
            
            if self.config_file.exists():
                import shutil
                shutil.copy2(self.config_file, backup_file)
                logging.info(f"Configuration backup created: {backup_file}")
                
                # Clean old backups (keep last 10)
                self._cleanup_old_backups("settings_")
                
        except Exception as e:
            logging.warning(f"Failed to create configuration backup: {e}")
    
    def _create_presets_backup(self) -> None:
        """Create backup of current presets."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"presets_{timestamp}.json"
            
            if self.presets_file.exists():
                import shutil
                shutil.copy2(self.presets_file, backup_file)
                logging.info(f"Presets backup created: {backup_file}")
                
                # Clean old backups (keep last 10)
                self._cleanup_old_backups("presets_")
                
        except Exception as e:
            logging.warning(f"Failed to create presets backup: {e}")
    
    def _cleanup_old_backups(self, prefix: str, keep_count: int = 10) -> None:
        """Clean up old backup files."""
        try:
            backup_files = sorted(
                [f for f in self.backup_dir.glob(f"{prefix}*.json")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Remove old backups
            for old_backup in backup_files[keep_count:]:
                old_backup.unlink()
                logging.debug(f"Removed old backup: {old_backup}")
                
        except Exception as e:
            logging.warning(f"Failed to cleanup old backups: {e}")
    
    def reset_to_defaults(self, save: bool = True) -> bool:
        """
        Reset configuration to default values.
        
        Args:
            save: Whether to save after reset
            
        Returns:
            bool: True if reset successfully
        """
        try:
            # Create backup first
            if self.config_file.exists():
                self._create_backup()
            
            # Reset to defaults
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
    
    def export_config(self, export_path: Path) -> bool:
        """
        Export current configuration to specified path.
        
        Args:
            export_path: Path to export configuration
            
        Returns:
            bool: True if exported successfully
        """
        try:
            export_data = {
                'config': self._config.to_dict(),
                'presets': self._presets,
                'exported_at': datetime.now().isoformat(),
                'version': self._config.version
            }
            
            success = save_json_config(export_path, export_data)
            
            if success:
                logging.info(f"Configuration exported to: {export_path}")
            
            return success
            
        except Exception as e:
            logging.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, import_path: Path, merge: bool = False) -> bool:
        """
        Import configuration from specified path.
        
        Args:
            import_path: Path to import configuration from
            merge: Whether to merge with existing config or replace
            
        Returns:
            bool: True if imported successfully
        """
        try:
            # Validate path
            is_valid, error = validate_path(import_path)
            if not is_valid:
                logging.error(f"Invalid import path: {error}")
                return False
            
            if not import_path.exists():
                logging.error(f"Import file does not exist: {import_path}")
                return False
            
            # Load import data
            import_data = load_json_config(import_path, {})
            if not import_data:
                logging.error("Failed to load import data")
                return False
            
            # Create backup before import
            self._create_backup()
            self._create_presets_backup()
            
            # Import configuration
            if merge:
                # Merge with existing config
                if 'config' in import_data:
                    config_dict = self._config.to_dict()
                    config_dict.update(import_data['config'])
                    self._config = AppConfig.from_dict(config_dict)
                
                if 'presets' in import_data:
                    self._presets.update(import_data['presets'])
            else:
                # Replace existing config
                if 'config' in import_data:
                    self._config = AppConfig.from_dict(import_data['config'])
                
                if 'presets' in import_data:
                    self._presets = import_data['presets']
            
            # Save imported configuration
            self.save_config(backup=False)
            self.save_presets(backup=False)
            
            logging.info(f"Configuration imported from: {import_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to import configuration: {e}")
            return False
    
    def get_recent_backups(self, count: int = 5) -> List[Path]:
        """
        Get list of recent backup files.
        
        Args:
            count: Number of recent backups to return
            
        Returns:
            List[Path]: List of backup file paths
        """
        try:
            backup_files = sorted(
                self.backup_dir.glob("*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            return backup_files[:count]
        except Exception as e:
            logging.error(f"Failed to get recent backups: {e}")
            return []
    
    def validate_config(self) -> List[str]:
        """
        Validate current configuration and return any issues.
        
        Returns:
            List[str]: List of validation issues (empty if valid)
        """
        issues = []
        
        try:
            # Validate window settings
            if self._config.window.width < 800:
                issues.append("Window width too small (minimum 800)")
            
            if self._config.window.height < 600:
                issues.append("Window height too small (minimum 600)")
            
            # Validate chocolatey settings
            if self._config.chocolatey.timeout_minutes < 1:
                issues.append("Chocolatey timeout too small (minimum 1 minute)")
            
            if self._config.chocolatey.parallel_downloads < 1:
                issues.append("Parallel downloads must be at least 1")
            
            # Validate file operation settings
            if self._config.file_operations.max_file_size_gb < 1:
                issues.append("Max file size too small (minimum 1 GB)")
            
            # Validate presets
            for preset_name, packages in self._presets.items():
                if not isinstance(packages, list):
                    issues.append(f"Preset '{preset_name}' is not a list")
                elif not all(isinstance(pkg, str) for pkg in packages):
                    issues.append(f"Preset '{preset_name}' contains non-string packages")
            
        except Exception as e:
            issues.append(f"Configuration validation error: {e}")
        
        return issues