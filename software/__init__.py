"""
Software management module for IT Admin Tool.

This module provides comprehensive software package management functionality
including Chocolatey integration, package searching, installation, and preset management.
"""

from .chocolatey_manager import ChocolateyManager, ChocolateyInstallWorker
from .package_installer import PackageInstaller, PackageInstallWorker
from .package_search import PackageSearcher, PackageSearchWorker
from .presets_manager import PresetsManager

__all__ = [
    'ChocolateyManager',
    'ChocolateyInstallWorker',
    'PackageInstaller', 
    'PackageInstallWorker',
    'PackageSearcher',
    'PackageSearchWorker',
    'PresetsManager'
]