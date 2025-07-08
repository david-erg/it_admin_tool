"""
Software presets management.

This module provides advanced preset management functionality specific to
software packages, including preset validation, package verification, and
preset recommendations.
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from core import ConfigManager
from .chocolatey_manager import ChocolateyManager
from .package_search import PackageSearcher, PackageInfo


class PresetCategory(Enum):
    """Preset category enumeration."""
    OFFICE = "office"
    DEVELOPMENT = "development"
    MEDIA = "media"
    GAMING = "gaming"
    SECURITY = "security"
    UTILITIES = "utilities"
    CUSTOM = "custom"


@dataclass
class PresetValidationResult:
    """Result of preset validation."""
    preset_name: str
    valid_packages: List[str]
    invalid_packages: List[str]
    missing_packages: List[str]
    warnings: List[str]
    is_valid: bool


@dataclass
class PresetInfo:
    """Extended preset information."""
    name: str
    packages: List[str]
    category: PresetCategory
    description: str = ""
    author: str = ""
    created_date: str = ""
    last_modified: str = ""
    tags: List[str] = None
    estimated_install_time: int = 0  # in minutes
    estimated_size_mb: int = 0
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class PresetsManager:
    """
    Advanced software presets management.
    
    This class extends the basic preset functionality in ConfigManager
    with software-specific features like package validation and recommendations.
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.chocolatey_manager = ChocolateyManager()
        self.package_searcher = PackageSearcher()
    
    def validate_preset(self, preset_name: str) -> PresetValidationResult:
        """
        Validate a preset by checking if all packages are available.
        
        Args:
            preset_name: Name of the preset to validate
        
        Returns:
            PresetValidationResult: Validation results
        """
        packages = self.config_manager.get_preset(preset_name)
        if not packages:
            return PresetValidationResult(
                preset_name=preset_name,
                valid_packages=[],
                invalid_packages=[],
                missing_packages=[],
                warnings=[f"Preset '{preset_name}' not found"],
                is_valid=False
            )
        
        valid_packages = []
        invalid_packages = []
        missing_packages = []
        warnings = []
        
        # Check if Chocolatey is available for validation
        if not self.chocolatey_manager.is_chocolatey_installed():
            warnings.append("Chocolatey not installed - cannot validate package availability")
            return PresetValidationResult(
                preset_name=preset_name,
                valid_packages=packages,  # Assume valid if can't check
                invalid_packages=[],
                missing_packages=[],
                warnings=warnings,
                is_valid=True
            )
        
        # Validate each package
        for package in packages:
            try:
                success, package_info, error = self.package_searcher.get_package_details(package)
                
                if success and package_info:
                    valid_packages.append(package)
                else:
                    # Try a search to see if package exists with different name
                    search_success, search_results, search_error = self.package_searcher.search_packages(
                        package, exact_match=True, limit=1
                    )
                    
                    if search_success and search_results:
                        valid_packages.append(package)
                    else:
                        missing_packages.append(package)
                        
            except Exception as e:
                warnings.append(f"Error validating package '{package}': {str(e)}")
                invalid_packages.append(package)
        
        is_valid = len(invalid_packages) == 0 and len(missing_packages) == 0
        
        return PresetValidationResult(
            preset_name=preset_name,
            valid_packages=valid_packages,
            invalid_packages=invalid_packages,
            missing_packages=missing_packages,
            warnings=warnings,
            is_valid=is_valid
        )
    
    def validate_all_presets(self) -> Dict[str, PresetValidationResult]:
        """
        Validate all presets.
        
        Returns:
            Dict[str, PresetValidationResult]: Validation results for all presets
        """
        results = {}
        preset_names = self.config_manager.get_preset_names()
        
        for preset_name in preset_names:
            results[preset_name] = self.validate_preset(preset_name)
        
        return results
    
    def suggest_similar_packages(self, package_name: str, max_suggestions: int = 5) -> List[str]:
        """
        Suggest similar packages for a missing or invalid package.
        
        Args:
            package_name: Name of the package to find alternatives for
            max_suggestions: Maximum number of suggestions to return
        
        Returns:
            List[str]: List of suggested package names
        """
        if not self.chocolatey_manager.is_chocolatey_installed():
            return []
        
        suggestions = []
        
        try:
            # Search for packages with similar names
            success, packages, error = self.package_searcher.search_packages(
                package_name, exact_match=False, limit=max_suggestions * 2
            )
            
            if success:
                # Filter and sort suggestions by relevance
                for package_info in packages:
                    if package_info.name.lower() != package_name.lower():
                        suggestions.append(package_info.name)
                        
                        if len(suggestions) >= max_suggestions:
                            break
            
        except Exception:
            pass  # Return empty list on error
        
        return suggestions
    
    def create_preset_from_installed(self, preset_name: str) -> Tuple[bool, str]:
        """
        Create a preset from currently installed packages.
        
        Args:
            preset_name: Name for the new preset
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not self.chocolatey_manager.is_chocolatey_installed():
            return False, "Chocolatey is not installed"
        
        try:
            success, packages, error = self.chocolatey_manager.get_installed_packages()
            
            if success:
                package_names = [pkg['name'] for pkg in packages]
                
                if self.config_manager.add_preset(preset_name, package_names):
                    return True, f"Created preset '{preset_name}' with {len(package_names)} packages"
                else:
                    return False, "Failed to save preset"
            else:
                return False, f"Failed to get installed packages: {error}"
                
        except Exception as e:
            return False, f"Error creating preset: {str(e)}"
    
    def merge_presets(self, preset_names: List[str], new_preset_name: str) -> Tuple[bool, str]:
        """
        Merge multiple presets into a new preset.
        
        Args:
            preset_names: List of preset names to merge
            new_preset_name: Name for the merged preset
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        all_packages = set()
        
        for preset_name in preset_names:
            packages = self.config_manager.get_preset(preset_name)
            if packages:
                all_packages.update(packages)
            else:
                return False, f"Preset '{preset_name}' not found"
        
        merged_packages = list(all_packages)
        
        if self.config_manager.add_preset(new_preset_name, merged_packages):
            return True, f"Created merged preset '{new_preset_name}' with {len(merged_packages)} packages"
        else:
            return False, "Failed to save merged preset"
    
    def get_preset_statistics(self) -> Dict[str, any]:
        """
        Get statistics about all presets.
        
        Returns:
            Dict: Preset statistics
        """
        presets = self.config_manager.get_presets()
        
        if not presets:
            return {
                'total_presets': 0,
                'total_packages': 0,
                'average_packages_per_preset': 0,
                'largest_preset': None,
                'smallest_preset': None,
                'common_packages': []
            }
        
        total_presets = len(presets)
        total_packages = sum(len(packages) for packages in presets.values())
        average_packages = total_packages / total_presets if total_presets > 0 else 0
        
        # Find largest and smallest presets
        largest_preset = max(presets.items(), key=lambda x: len(x[1]))
        smallest_preset = min(presets.items(), key=lambda x: len(x[1]))
        
        # Find common packages across presets
        all_packages = []
        for packages in presets.values():
            all_packages.extend(packages)
        
        package_counts = {}
        for package in all_packages:
            package_counts[package] = package_counts.get(package, 0) + 1
        
        # Get packages that appear in multiple presets
        common_packages = [
            package for package, count in package_counts.items() 
            if count > 1
        ]
        common_packages.sort(key=lambda x: package_counts[x], reverse=True)
        
        return {
            'total_presets': total_presets,
            'total_packages': total_packages,
            'average_packages_per_preset': round(average_packages, 1),
            'largest_preset': {
                'name': largest_preset[0],
                'package_count': len(largest_preset[1])
            },
            'smallest_preset': {
                'name': smallest_preset[0],
                'package_count': len(smallest_preset[1])
            },
            'common_packages': common_packages[:10]  # Top 10 most common
        }
    
    def export_presets(self, file_path: Path, include_validation: bool = False) -> Tuple[bool, str]:
        """
        Export presets to a JSON file with optional validation data.
        
        Args:
            file_path: Path to export file
            include_validation: Whether to include validation results
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            presets = self.config_manager.get_presets()
            
            export_data = {
                'presets': presets,
                'export_metadata': {
                    'exported_at': self._get_current_timestamp(),
                    'total_presets': len(presets),
                    'chocolatey_available': self.chocolatey_manager.is_chocolatey_installed()
                }
            }
            
            if include_validation:
                validation_results = self.validate_all_presets()
                export_data['validation_results'] = {
                    name: {
                        'is_valid': result.is_valid,
                        'valid_packages': result.valid_packages,
                        'invalid_packages': result.invalid_packages,
                        'missing_packages': result.missing_packages,
                        'warnings': result.warnings
                    }
                    for name, result in validation_results.items()
                }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Presets exported to {file_path}"
            
        except Exception as e:
            return False, f"Export failed: {str(e)}"
    
    def import_presets(self, file_path: Path, overwrite_existing: bool = False) -> Tuple[bool, str, Dict]:
        """
        Import presets from a JSON file.
        
        Args:
            file_path: Path to import file
            overwrite_existing: Whether to overwrite existing presets
        
        Returns:
            Tuple[bool, str, Dict]: (success, message, import_summary)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if 'presets' not in import_data:
                return False, "Invalid preset file format", {}
            
            imported_presets = import_data['presets']
            existing_presets = self.config_manager.get_preset_names()
            
            imported_count = 0
            skipped_count = 0
            updated_count = 0
            
            for preset_name, packages in imported_presets.items():
                if preset_name in existing_presets and not overwrite_existing:
                    skipped_count += 1
                    continue
                
                if preset_name in existing_presets:
                    updated_count += 1
                else:
                    imported_count += 1
                
                self.config_manager.add_preset(preset_name, packages)
            
            summary = {
                'imported': imported_count,
                'updated': updated_count,
                'skipped': skipped_count,
                'total_in_file': len(imported_presets)
            }
            
            message = f"Import completed: {imported_count} new, {updated_count} updated, {skipped_count} skipped"
            
            return True, message, summary
            
        except Exception as e:
            return False, f"Import failed: {str(e)}", {}
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_package_recommendations(self, installed_packages: List[str]) -> List[str]:
        """
        Get package recommendations based on installed packages.
        
        Args:
            installed_packages: List of currently installed packages
        
        Returns:
            List[str]: Recommended packages
        """
        # This is a simple implementation - could be enhanced with ML or more sophisticated logic
        recommendations = []
        
        # Define package relationships and recommendations
        recommendation_rules = {
            'googlechrome': ['firefox', 'chromium'],
            'firefox': ['googlechrome', 'thunderbird'],
            'vscode': ['git', 'nodejs', 'python'],
            'git': ['vscode', 'github-desktop', 'gitextensions'],
            'nodejs': ['vscode', 'yarn', 'npm'],
            'python': ['vscode', 'pip', 'anaconda3'],
            'vlc': ['k-litecodecpackfull', 'obs-studio'],
            '7zip': ['winrar', 'peazip'],
            'steam': ['discord', 'nvidia-geforce-experience'],
            'discord': ['steam', 'obs-studio'],
        }
        
        installed_lower = [pkg.lower() for pkg in installed_packages]
        
        for installed_pkg in installed_lower:
            if installed_pkg in recommendation_rules:
                for recommended_pkg in recommendation_rules[installed_pkg]:
                    if recommended_pkg not in installed_lower and recommended_pkg not in recommendations:
                        recommendations.append(recommended_pkg)
        
        return recommendations[:10]  # Return top 10 recommendations