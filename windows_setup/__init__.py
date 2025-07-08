"""
Windows Setup Module

This module provides utilities for configuring Windows systems including:
- Bloatware removal
- Essential Windows settings configuration  
- Local user account management
- Registry manipulation utilities

All operations require administrator privileges and are Windows-specific.
"""

from .bloatware_remover import BloatwareRemover
from .settings_manager import WindowsSettingsManager
from .user_manager import LocalUserManager
from .registry_helper import RegistryHelper

__all__ = [
    'BloatwareRemover',
    'WindowsSettingsManager', 
    'LocalUserManager',
    'RegistryHelper'
]

__version__ = "1.0.0"