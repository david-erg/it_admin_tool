"""
Bloatware Remover Module

Provides functionality to remove unwanted Windows applications (bloatware)
using PowerShell commands. Requires administrator privileges.
"""

import subprocess
import platform
from typing import List, Dict, Tuple, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class BloatwareCategory(Enum):
    """Categories of bloatware applications"""
    GAMING = "gaming"
    MEDIA = "media"
    OFFICE = "office"
    SOCIAL = "social"
    UTILITIES = "utilities"
    MICROSOFT_APPS = "microsoft_apps"
    THIRD_PARTY = "third_party"


@dataclass
class BloatwareApp:
    """Represents a bloatware application"""
    package_name: str
    display_name: str
    category: BloatwareCategory
    description: str = ""
    is_safe_to_remove: bool = True


class BloatwareRemover:
    """Handles removal of Windows bloatware applications"""
    
    # Predefined bloatware applications
    BLOATWARE_APPS = {
        # Gaming apps
        "Microsoft.XboxApp": BloatwareApp(
            "Microsoft.XboxApp", "Xbox Console Companion", 
            BloatwareCategory.GAMING, "Xbox gaming companion app"
        ),
        "Microsoft.XboxGamingOverlay": BloatwareApp(
            "Microsoft.XboxGamingOverlay", "Xbox Gaming Overlay",
            BloatwareCategory.GAMING, "Xbox gaming overlay for screenshots/recording"
        ),
        "Microsoft.XboxGameOverlay": BloatwareApp(
            "Microsoft.XboxGameOverlay", "Xbox Game Overlay",
            BloatwareCategory.GAMING, "Xbox game overlay interface"
        ),
        "Microsoft.XboxIdentityProvider": BloatwareApp(
            "Microsoft.XboxIdentityProvider", "Xbox Identity Provider",
            BloatwareCategory.GAMING, "Xbox identity and authentication service"
        ),
        "Microsoft.Xbox.TCUI": BloatwareApp(
            "Microsoft.Xbox.TCUI", "Xbox TCUI",
            BloatwareCategory.GAMING, "Xbox UI components"
        ),
        
        # Media apps
        "Microsoft.ZuneMusic": BloatwareApp(
            "Microsoft.ZuneMusic", "Groove Music",
            BloatwareCategory.MEDIA, "Microsoft's music player"
        ),
        "Microsoft.ZuneVideo": BloatwareApp(
            "Microsoft.ZuneVideo", "Movies & TV",
            BloatwareCategory.MEDIA, "Microsoft's video player"
        ),
        "Microsoft.WindowsCamera": BloatwareApp(
            "Microsoft.WindowsCamera", "Camera",
            BloatwareCategory.MEDIA, "Windows Camera app"
        ),
        
        # Office/Productivity apps
        "Microsoft.MicrosoftOfficeHub": BloatwareApp(
            "Microsoft.MicrosoftOfficeHub", "Office Hub",
            BloatwareCategory.OFFICE, "Microsoft Office launcher"
        ),
        "Microsoft.Office.OneNote": BloatwareApp(
            "Microsoft.Office.OneNote", "OneNote",
            BloatwareCategory.OFFICE, "Microsoft OneNote note-taking app"
        ),
        "Microsoft.MicrosoftStickyNotes": BloatwareApp(
            "Microsoft.MicrosoftStickyNotes", "Sticky Notes",
            BloatwareCategory.OFFICE, "Digital sticky notes app"
        ),
        "Microsoft.Todos": BloatwareApp(
            "Microsoft.Todos", "Microsoft To Do",
            BloatwareCategory.OFFICE, "Task management app"
        ),
        
        # Social/Communication apps
        "Microsoft.SkypeApp": BloatwareApp(
            "Microsoft.SkypeApp", "Skype",
            BloatwareCategory.SOCIAL, "Video calling and messaging"
        ),
        "Microsoft.People": BloatwareApp(
            "Microsoft.People", "People",
            BloatwareCategory.SOCIAL, "Contact management app"
        ),
        "Microsoft.YourPhone": BloatwareApp(
            "Microsoft.YourPhone", "Your Phone",
            BloatwareCategory.SOCIAL, "Phone integration app"
        ),
        "MicrosoftTeams": BloatwareApp(
            "MicrosoftTeams", "Microsoft Teams",
            BloatwareCategory.SOCIAL, "Business communication platform"
        ),
        
        # Utility/System apps
        "Microsoft.WindowsMaps": BloatwareApp(
            "Microsoft.WindowsMaps", "Maps",
            BloatwareCategory.UTILITIES, "Windows Maps application"
        ),
        "Microsoft.BingWeather": BloatwareApp(
            "Microsoft.BingWeather", "Weather",
            BloatwareCategory.UTILITIES, "Weather information app"
        ),
        "Microsoft.BingNews": BloatwareApp(
            "Microsoft.BingNews", "News",
            BloatwareCategory.UTILITIES, "News aggregation app"
        ),
        "Microsoft.GetHelp": BloatwareApp(
            "Microsoft.GetHelp", "Get Help",
            BloatwareCategory.UTILITIES, "Windows help and support"
        ),
        "Microsoft.Getstarted": BloatwareApp(
            "Microsoft.Getstarted", "Tips",
            BloatwareCategory.UTILITIES, "Windows tips and getting started"
        ),
        "Microsoft.WindowsFeedbackHub": BloatwareApp(
            "Microsoft.WindowsFeedbackHub", "Feedback Hub",
            BloatwareCategory.UTILITIES, "Windows feedback collection"
        ),
        "Microsoft.PowerAutomateDesktop": BloatwareApp(
            "Microsoft.PowerAutomateDesktop", "Power Automate",
            BloatwareCategory.UTILITIES, "Process automation tool"
        ),
        
        # Microsoft Apps
        "Microsoft.MicrosoftSolitaireCollection": BloatwareApp(
            "Microsoft.MicrosoftSolitaireCollection", "Microsoft Solitaire",
            BloatwareCategory.MICROSOFT_APPS, "Card game collection"
        ),
        "Microsoft.windowscommunicationsapps": BloatwareApp(
            "Microsoft.windowscommunicationsapps", "Mail and Calendar",
            BloatwareCategory.MICROSOFT_APPS, "Email and calendar apps"
        ),
        "Microsoft.MixedReality.Portal": BloatwareApp(
            "Microsoft.MixedReality.Portal", "Mixed Reality Portal",
            BloatwareCategory.MICROSOFT_APPS, "VR/AR portal application"
        ),
        "Microsoft.Microsoft3DViewer": BloatwareApp(
            "Microsoft.Microsoft3DViewer", "3D Viewer",
            BloatwareCategory.MICROSOFT_APPS, "3D model viewer"
        ),
        "Microsoft.MSPaint": BloatwareApp(
            "Microsoft.MSPaint", "Paint 3D",
            BloatwareCategory.MICROSOFT_APPS, "3D painting application"
        ),
        
        # Third-party apps
        "Disney.37853FC22B2CE": BloatwareApp(
            "Disney.37853FC22B2CE", "Disney+",
            BloatwareCategory.THIRD_PARTY, "Disney streaming service"
        ),
        "SpotifyAB.SpotifyMusic": BloatwareApp(
            "SpotifyAB.SpotifyMusic", "Spotify",
            BloatwareCategory.THIRD_PARTY, "Music streaming service"
        ),
        "Clipchamp.Clipchamp": BloatwareApp(
            "Clipchamp.Clipchamp", "Clipchamp",
            BloatwareCategory.THIRD_PARTY, "Video editing application"
        ),
    }
    
    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize BloatwareRemover
        
        Args:
            progress_callback: Optional callback function for progress updates
        """
        self._validate_platform()
        self.progress_callback = progress_callback or self._default_progress_callback
    
    def _validate_platform(self) -> None:
        """Ensure we're running on Windows"""
        if platform.system() != "Windows":
            raise OSError("Bloatware removal is only supported on Windows")
    
    def _default_progress_callback(self, message: str) -> None:
        """Default progress callback that prints to console"""
        print(message)
    
    def get_available_apps(self) -> Dict[str, BloatwareApp]:
        """
        Get dictionary of all available bloatware apps
        
        Returns:
            Dict mapping package names to BloatwareApp objects
        """
        return self.BLOATWARE_APPS.copy()
    
    def get_apps_by_category(self, category: BloatwareCategory) -> Dict[str, BloatwareApp]:
        """
        Get bloatware apps filtered by category
        
        Args:
            category: BloatwareCategory to filter by
            
        Returns:
            Dict of filtered apps
        """
        return {
            pkg_name: app for pkg_name, app in self.BLOATWARE_APPS.items()
            if app.category == category
        }
    
    def get_common_bloatware(self) -> List[str]:
        """
        Get list of commonly removed bloatware package names
        
        Returns:
            List of package names that are commonly safe to remove
        """
        common_packages = [
            "Microsoft.XboxApp", "Microsoft.XboxGamingOverlay", "Microsoft.XboxGameOverlay",
            "Microsoft.ZuneMusic", "Microsoft.ZuneVideo", "Microsoft.MicrosoftSolitaireCollection",
            "Microsoft.BingWeather", "Microsoft.BingNews", "Microsoft.GetHelp", "Microsoft.Getstarted",
            "Microsoft.MixedReality.Portal", "Microsoft.Microsoft3DViewer", "Microsoft.MSPaint",
            "Microsoft.YourPhone", "Disney.37853FC22B2CE", "Clipchamp.Clipchamp"
        ]
        return common_packages
    
    def check_app_installed(self, package_name: str, timeout: int = 30) -> bool:
        """
        Check if a specific app is installed
        
        Args:
            package_name: Package name to check
            timeout: Command timeout in seconds
            
        Returns:
            bool: True if app is installed, False otherwise
        """
        try:
            ps_cmd = f'powershell -Command "Get-AppxPackage *{package_name}* | Select-Object Name"'
            result = subprocess.run(
                ps_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.returncode == 0 and package_name.lower() in result.stdout.lower()
            
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
    
    def remove_app(self, package_name: str, timeout: int = 30) -> bool:
        """
        Remove a single bloatware app
        
        Args:
            package_name: Package name to remove
            timeout: Command timeout in seconds
            
        Returns:
            bool: True if removal was successful, False otherwise
        """
        try:
            # Get display name for progress reporting
            display_name = self.BLOATWARE_APPS.get(package_name, 
                                                  BloatwareApp(package_name, package_name, 
                                                             BloatwareCategory.UTILITIES)).display_name
            
            self.progress_callback(f"Removing {display_name}...")
            
            # PowerShell command to remove the app
            ps_cmd = f'powershell -Command "Get-AppxPackage *{package_name}* | Remove-AppxPackage"'
            result = subprocess.run(
                ps_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                self.progress_callback(f"✓ Successfully removed {display_name}")
                return True
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self.progress_callback(f"✗ Failed to remove {display_name}: {error_msg}")
                return False
                
        except subprocess.TimeoutExpired:
            self.progress_callback(f"✗ Timeout removing {display_name}")
            return False
        except Exception as e:
            self.progress_callback(f"✗ Error removing {display_name}: {str(e)}")
            return False
    
    def remove_multiple_apps(self, package_names: List[str], 
                           timeout_per_app: int = 30) -> Tuple[List[str], List[str]]:
        """
        Remove multiple bloatware apps
        
        Args:
            package_names: List of package names to remove
            timeout_per_app: Timeout per app removal in seconds
            
        Returns:
            Tuple of (successful_removals, failed_removals)
        """
        successful = []
        failed = []
        
        self.progress_callback(f"=== BLOATWARE REMOVAL ===")
        self.progress_callback(f"Removing {len(package_names)} applications...")
        self.progress_callback("")
        
        for package_name in package_names:
            if self.remove_app(package_name, timeout_per_app):
                successful.append(package_name)
            else:
                failed.append(package_name)
        
        self.progress_callback("")
        self.progress_callback(f"=== REMOVAL COMPLETE ===")
        self.progress_callback(f"Successfully removed {len(successful)} out of {len(package_names)} applications.")
        
        if successful:
            self.progress_callback("Note: A system restart may be required for all changes to take effect.")
        
        return successful, failed
    
    def get_installed_bloatware(self, timeout: int = 60) -> List[str]:
        """
        Get list of bloatware apps that are currently installed
        
        Args:
            timeout: Command timeout in seconds
            
        Returns:
            List of installed package names from our bloatware list
        """
        installed = []
        
        try:
            # Get all installed packages
            ps_cmd = 'powershell -Command "Get-AppxPackage | Select-Object Name"'
            result = subprocess.run(
                ps_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                installed_packages = result.stdout.lower()
                
                # Check which of our bloatware apps are installed
                for package_name in self.BLOATWARE_APPS.keys():
                    if package_name.lower() in installed_packages:
                        installed.append(package_name)
            
        except Exception:
            pass
        
        return installed
    
    def create_removal_report(self, successful: List[str], 
                            failed: List[str]) -> Dict[str, any]:
        """
        Create a detailed removal report
        
        Args:
            successful: List of successfully removed package names
            failed: List of failed package names
            
        Returns:
            Dict containing detailed removal report
        """
        report = {
            "total_attempted": len(successful) + len(failed),
            "successful_count": len(successful),
            "failed_count": len(failed),
            "success_rate": len(successful) / (len(successful) + len(failed)) if (successful or failed) else 0,
            "successful_removals": [],
            "failed_removals": [],
            "recommendations": []
        }
        
        # Add details for successful removals
        for package_name in successful:
            app = self.BLOATWARE_APPS.get(package_name)
            if app:
                report["successful_removals"].append({
                    "package_name": package_name,
                    "display_name": app.display_name,
                    "category": app.category.value
                })
        
        # Add details for failed removals
        for package_name in failed:
            app = self.BLOATWARE_APPS.get(package_name)
            if app:
                report["failed_removals"].append({
                    "package_name": package_name,
                    "display_name": app.display_name,
                    "category": app.category.value
                })
        
        # Add recommendations
        if failed:
            report["recommendations"].extend([
                "Ensure the application is running with administrator privileges",
                "Some apps may be in use - close all applications and try again",
                "Consider removing apps individually for better error diagnosis",
                "Check Windows Update status - some apps may be protected during updates"
            ])
        
        if successful:
            report["recommendations"].append("Consider restarting the system to complete the removal process")
        
        return report


# Convenience functions
def get_bloatware_remover(progress_callback: Optional[Callable[[str], None]] = None) -> BloatwareRemover:
    """Get a configured BloatwareRemover instance"""
    return BloatwareRemover(progress_callback)


def remove_common_bloatware(progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[List[str], List[str]]:
    """
    Quick function to remove commonly unwanted bloatware
    
    Args:
        progress_callback: Optional progress callback function
        
    Returns:
        Tuple of (successful_removals, failed_removals)
    """
    remover = BloatwareRemover(progress_callback)
    common_apps = remover.get_common_bloatware()
    return remover.remove_multiple_apps(common_apps)