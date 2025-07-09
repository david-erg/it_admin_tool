"""
Admin's ToolBox - IT Administration Tool
Main Application Entry Point

This is the main entry point for the IT Administration Tool application.
It initializes all modules and provides both GUI and CLI interfaces.

Usage:
    python main.py              # Start GUI application
    python main.py --cli        # Start CLI interface
    python main.py --help       # Show help information
"""

import sys
import os
import platform
import argparse
from pathlib import Path
from typing import Optional

# Ensure we're on Windows
if platform.system() != "Windows":
    print("ERROR: This application is designed for Windows systems only.")
    print(f"Current system: {platform.system()}")
    sys.exit(1)

# Add the current directory to Python path for module imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    # Import core modules
    from core.utils import check_admin_privileges, get_application_path
    from core.config import ConfigManager
    
    # Import all functional modules
    from software import ChocolateyManager, PackageInstaller, PackageSearcher, PresetsManager
    from file_ops import FolderManager, PathUtilities, copy_to_public_desktop
    
    # Try to import system_info and windows_setup modules (may not exist)
    system_info_available = False
    windows_setup_available = False
    ui_available = False
    
    try:
        from system_info import SystemInfoWorker, HardwareDetector, SoftwareDetector, NetworkDetector
        system_info_available = True
    except ImportError as e:
        print(f"Warning: System info module not available: {e}")
    
    try:
        from windows_setup import BloatwareRemover, WindowsSettingsManager, LocalUserManager, RegistryHelper
        windows_setup_available = True
    except ImportError as e:
        print(f"Warning: Windows setup module not available: {e}")
    
    try:
        from ui.main_window import MainWindow
        ui_available = True
    except ImportError as e:
        print(f"Note: GUI components not available: {e}")
    
except ImportError as e:
    print(f"ERROR: Failed to import required core modules: {e}")
    print("Please ensure all module directories are present and properly configured.")
    sys.exit(1)


class ITAdminApp:
    """Main application class that coordinates all modules"""
    
    def __init__(self):
        """Initialize the main application"""
        self.app_name = "Admin's ToolBox"
        self.version = "2.1"
        self.is_admin = check_admin_privileges()
        self.app_path = get_application_path()
        
        # Load application configuration
        self.config_manager = ConfigManager()
        
        print(f"{self.app_name} v{self.version}")
        print(f"Running from: {self.app_path}")
        print(f"Administrator privileges: {'✓ Yes' if self.is_admin else '✗ No'}")
        
        if not self.is_admin:
            print("\nWARNING: Some features require administrator privileges.")
            print("For full functionality, run as Administrator.")
    
    def start_gui(self) -> int:
        """
        Start the GUI application
        
        Returns:
            Exit code (0 for success)
        """
        if not ui_available:
            print("ERROR: GUI components are not available.")
            print("Install PySide6 with: pip install PySide6")
            print("Or run in CLI mode with: python main.py --cli")
            return 1
        
        try:
            # Import PySide6 for GUI
            from PySide6.QtWidgets import QApplication, QMessageBox
            from PySide6.QtCore import Qt
            
            # Create QApplication
            app = QApplication(sys.argv)
            app.setApplicationName(self.app_name)
            app.setApplicationVersion(self.version)
            
            # Show admin privilege warning if needed
            if not self.is_admin:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setWindowTitle("Administrator Privileges")
                msg_box.setText(
                    "This application works best with administrator privileges.\n\n"
                    "Some features (like package installation) may not work without admin rights.\n\n"
                    "To run as administrator:\n"
                    "• Right-click the application\n"
                    "• Select 'Run as administrator'"
                )
                msg_box.exec()
            
            # Create and show main window
            main_window = MainWindow()
            main_window.show()
            
            # Run the application
            return app.exec()
            
        except ImportError:
            print("ERROR: PySide6 is required for GUI mode.")
            print("Install with: pip install PySide6")
            print("Or run in CLI mode with: python main.py --cli")
            return 1
        except Exception as e:
            print(f"ERROR: Failed to start GUI application: {e}")
            return 1
    
    def start_cli(self) -> int:
        """
        Start the CLI interface
        
        Returns:
            Exit code (0 for success)
        """
        try:
            print(f"\n{self.app_name} - Command Line Interface")
            print("=" * 50)
            
            while True:
                print("\nAvailable Operations:")
                print("1. Software Management")
                if system_info_available:
                    print("2. System Information")
                if windows_setup_available:
                    print("3. Windows Setup")
                print("4. File Operations")
                if windows_setup_available:
                    print("5. Quick Setup")
                print("0. Exit")
                
                choice = input("\nSelect an option (0-5): ").strip()
                
                if choice == "0":
                    print("Goodbye!")
                    return 0
                elif choice == "1":
                    self._cli_software_management()
                elif choice == "2" and system_info_available:
                    self._cli_system_information()
                elif choice == "3" and windows_setup_available:
                    self._cli_windows_setup()
                elif choice == "4":
                    self._cli_file_operations()
                elif choice == "5" and windows_setup_available:
                    self._cli_quick_setup()
                else:
                    print("Invalid choice or feature not available. Please try again.")
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            return 0
        except Exception as e:
            print(f"ERROR: CLI interface failed: {e}")
            return 1
    
    def _cli_software_management(self):
        """CLI software management operations"""
        print("\n--- Software Management ---")
        print("1. Search packages")
        print("2. Install packages")
        print("3. Load preset")
        print("4. Check Chocolatey status")
        print("5. Install Chocolatey")
        
        choice = input("Select option (1-5): ").strip()
        
        if choice == "1":
            self._cli_search_packages()
        elif choice == "2":
            self._cli_install_packages()
        elif choice == "3":
            self._cli_load_preset()
        elif choice == "4":
            self._cli_check_chocolatey()
        elif choice == "5":
            self._cli_install_chocolatey()
        else:
            print("Invalid choice.")
    
    def _cli_search_packages(self):
        """Search for packages"""
        query = input("Enter search term: ").strip()
        if not query:
            print("Search term cannot be empty.")
            return
        
        try:
            searcher = PackageSearcher()
            
            print(f"Searching for '{query}'...")
            success, packages, error = searcher.search_packages(query, limit=20)
            
            if success and packages:
                print(f"\nFound {len(packages)} packages:")
                for i, pkg in enumerate(packages, 1):
                    description = pkg.description[:60] + "..." if len(pkg.description) > 60 else pkg.description
                    print(f"{i:2}. {pkg.name} ({pkg.version})")
                    print(f"    {description}")
                    if hasattr(pkg, 'download_count') and pkg.download_count:
                        print(f"    Downloads: {pkg.download_count}")
                    print()
            elif success and not packages:
                print("No packages found.")
            else:
                print(f"Search failed: {error}")
                
        except Exception as e:
            print(f"Error during search: {e}")
    
    def _cli_install_packages(self):
        """Install packages manually"""
        packages_input = input("Enter package names (comma-separated): ").strip()
        if not packages_input:
            print("Package names cannot be empty.")
            return
        
        package_list = [pkg.strip() for pkg in packages_input.split(',') if pkg.strip()]
        
        if not package_list:
            print("No valid package names provided.")
            return
        
        # Check admin privileges
        if not self.is_admin:
            print("WARNING: Package installation requires administrator privileges.")
            confirm = input("Continue anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                return
        
        try:
            installer = PackageInstaller()
            
            print(f"\nInstalling {len(package_list)} packages...")
            for package in package_list:
                print(f"\nInstalling {package}...")
                result = installer.install_package(package, timeout=300)
                
                if result.status.value == "success":
                    print(f"✅ {package} installed successfully!")
                else:
                    print(f"❌ {package} failed to install: {result.message}")
                    if result.error_output:
                        print(f"   Error: {result.error_output}")
                        
        except Exception as e:
            print(f"Error during installation: {e}")
    
    def _cli_load_preset(self):
        """Load and install a preset"""
        available_presets = self.config_manager.get_preset_names()
        
        if not available_presets:
            print("No presets available.")
            return
        
        print("\nAvailable presets:")
        for i, preset_name in enumerate(available_presets, 1):
            packages = self.config_manager.get_preset(preset_name)
            print(f"{i:2}. {preset_name} ({len(packages)} packages)")
        
        try:
            selection = int(input("\nSelect preset number: ")) - 1
            if 0 <= selection < len(available_presets):
                preset_name = available_presets[selection]
                packages = self.config_manager.get_preset(preset_name)
                
                print(f"\nPreset '{preset_name}' contains {len(packages)} packages:")
                for pkg in packages:
                    print(f"  - {pkg}")
                
                confirm = input(f"\nInstall {len(packages)} packages? (y/n): ").strip().lower()
                if confirm == 'y':
                    # Install packages one by one
                    installer = PackageInstaller()
                    successful = 0
                    failed = 0
                    
                    for package in packages:
                        print(f"\nInstalling {package}...")
                        result = installer.install_package(package, timeout=300)
                        
                        if result.status.value == "success":
                            print(f"✅ {package} installed successfully!")
                            successful += 1
                        else:
                            print(f"❌ {package} failed to install: {result.message}")
                            failed += 1
                    
                    print(f"\nInstallation complete: {successful} successful, {failed} failed")
                        
            else:
                print("Invalid selection.")
                
        except (ValueError, IndexError):
            print("Invalid selection.")
        except Exception as e:
            print(f"Error loading preset: {e}")
    
    def _cli_check_chocolatey(self):
        """Check Chocolatey status"""
        try:
            chocolatey = ChocolateyManager()
            
            if chocolatey.is_chocolatey_installed():
                version = chocolatey.get_chocolatey_version()
                print(f"✅ Chocolatey is installed (version: {version})")
                
                # Test functionality
                success, message = chocolatey.test_chocolatey_functionality()
                if success:
                    print(f"✅ Chocolatey functionality test: {message}")
                else:
                    print(f"⚠️  Chocolatey functionality test: {message}")
            else:
                print("❌ Chocolatey is not installed")
                
        except Exception as e:
            print(f"Error checking Chocolatey: {e}")
    
    def _cli_install_chocolatey(self):
        """Install Chocolatey"""
        try:
            chocolatey = ChocolateyManager()
            
            if chocolatey.is_chocolatey_installed():
                print("Chocolatey is already installed.")
                return
            
            if not self.is_admin:
                print("ERROR: Administrator privileges are required to install Chocolatey.")
                return
            
            print("Installing Chocolatey package manager...")
            print("This may take several minutes...")
            
            # Note: Actual installation would require implementing the installation method
            print("Chocolatey installation would start here...")
            print("Please visit: https://chocolatey.org/install for manual installation instructions.")
            
        except Exception as e:
            print(f"Error installing Chocolatey: {e}")
    
    def _cli_system_information(self):
        """CLI system information operations"""
        if not system_info_available:
            print("System information module is not available.")
            return
        
        print("\n--- System Information ---")
        print("1. Gather system information")
        print("2. Hardware information")
        print("3. Network information")
        print("4. Export system information")
        
        choice = input("Select option (1-4): ").strip()
        
        if choice == "1":
            self._cli_gather_system_info()
        elif choice == "2":
            self._cli_hardware_info()
        elif choice == "3":
            self._cli_network_info()
        elif choice == "4":
            self._cli_export_system_info()
        else:
            print("Invalid choice.")
    
    def _cli_gather_system_info(self):
        """Gather complete system information"""
        print("Gathering system information...")
        
        try:
            # Create progress callback
            def progress_callback(message):
                print(f"  {message}")
            
            # Use HardwareDetector directly since SystemInfoManager might not exist
            detector = HardwareDetector()
            
            print("\nCPU Information:")
            cpu_info = detector.detect_cpu_info()
            print(f"  Name: {cpu_info.name}")
            print(f"  Cores: {cpu_info.cores}")
            print(f"  Threads: {cpu_info.threads}")
            
            print("\nMemory Information:")
            memory_info = detector.detect_memory_info()
            print(f"  Total: {memory_info.total_gb:.1f} GB")
            print(f"  Available: {memory_info.available_gb:.1f} GB")
            print(f"  Usage: {memory_info.usage_percent:.1f}%")
            
            print("\nStorage Information:")
            storage_info = detector.detect_storage_info()
            print(f"  Total Capacity: {storage_info.total_capacity_gb:.1f} GB")
            print(f"  Free Space: {storage_info.total_free_gb:.1f} GB")
            
        except Exception as e:
            print(f"Error gathering system information: {e}")
    
    def _cli_hardware_info(self):
        """Display hardware information"""
        try:
            detector = HardwareDetector()
            
            print("\n--- Hardware Information ---")
            
            # CPU Info
            cpu_info = detector.detect_cpu_info()
            print(f"\nCPU: {cpu_info.name}")
            if cpu_info.cores:
                print(f"  Cores: {cpu_info.cores}")
            if cpu_info.threads:
                print(f"  Threads: {cpu_info.threads}")
            if cpu_info.max_clock_speed:
                print(f"  Max Clock Speed: {cpu_info.max_clock_speed}")
            
            # Memory Info
            memory_info = detector.detect_memory_info()
            print(f"\nMemory:")
            print(f"  Total: {memory_info.total_gb:.1f} GB")
            print(f"  Available: {memory_info.available_gb:.1f} GB")
            print(f"  Used: {memory_info.used_gb:.1f} GB")
            print(f"  Usage: {memory_info.usage_percent:.1f}%")
            
        except Exception as e:
            print(f"Error getting hardware information: {e}")
    
    def _cli_network_info(self):
        """Display network information"""
        try:
            detector = NetworkDetector()
            
            print("\n--- Network Information ---")
            
            # Primary network info
            primary_ip, primary_mac = detector.detect_primary_network_info()
            print(f"Primary IP: {primary_ip}")
            print(f"Primary MAC: {primary_mac}")
            
            # Network adapters
            network_info = detector.detect_network_info()
            print(f"Computer Name: {network_info.computer_name}")
            print(f"Domain/Workgroup: {network_info.domain_workgroup}")
            print(f"Internet Connectivity: {'Yes' if network_info.internet_connectivity else 'No'}")
            
            if network_info.adapters:
                print(f"\nNetwork Adapters ({len(network_info.adapters)}):")
                for adapter in network_info.adapters:
                    print(f"  {adapter.name}")
                    if adapter.ip_addresses:
                        print(f"    IP: {', '.join(adapter.ip_addresses)}")
                    if adapter.mac_address:
                        print(f"    MAC: {adapter.mac_address}")
                    print(f"    Status: {adapter.status}")
            
        except Exception as e:
            print(f"Error getting network information: {e}")
    
    def _cli_export_system_info(self):
        """Export system information to file"""
        try:
            filename = input("Enter filename (without extension): ").strip()
            if not filename:
                filename = f"system_info_{self._get_timestamp()}"
            
            format_choice = input("Export format (csv/json/txt) [csv]: ").strip().lower()
            if format_choice not in ['csv', 'json', 'txt']:
                format_choice = 'csv'
            
            full_filename = f"{filename}.{format_choice}"
            
            print(f"Exporting system information to {full_filename}...")
            
            # Note: Actual export would require implementing the export functionality
            print("Export functionality would be implemented here...")
            print(f"Would export to: {full_filename}")
            
        except Exception as e:
            print(f"Error exporting system information: {e}")
    
    def _cli_windows_setup(self):
        """CLI Windows setup operations"""
        if not windows_setup_available:
            print("Windows setup module is not available.")
            return
        
        print("\n--- Windows Setup ---")
        print("1. Remove bloatware")
        print("2. Apply settings")
        print("3. Create admin user")
        print("4. Registry operations")
        
        choice = input("Select option (1-4): ").strip()
        
        if choice == "1":
            self._cli_remove_bloatware()
        elif choice == "2":
            self._cli_apply_settings()
        elif choice == "3":
            self._cli_create_user()
        elif choice == "4":
            self._cli_registry_operations()
        else:
            print("Invalid choice.")
    
    def _cli_remove_bloatware(self):
        """Remove bloatware applications"""
        try:
            bloatware_remover = BloatwareRemover(lambda msg: print(f"[BLOATWARE] {msg}"))
            common_apps = bloatware_remover.get_common_bloatware()
            
            print(f"\nCommon bloatware apps ({len(common_apps)}):")
            for i, app in enumerate(common_apps[:10], 1):  # Show first 10
                print(f"  {i}. {app}")
            
            if len(common_apps) > 10:
                print(f"  ... and {len(common_apps) - 10} more")
            
            confirm = input(f"\nRemove {len(common_apps)} bloatware apps? (y/n): ").strip().lower()
            if confirm == 'y':
                if not self.is_admin:
                    print("WARNING: Administrator privileges recommended for app removal.")
                    confirm2 = input("Continue anyway? (y/n): ").strip().lower()
                    if confirm2 != 'y':
                        return
                
                print("Removing bloatware...")
                successful, failed = bloatware_remover.remove_multiple_apps(common_apps)
                print(f"\nResults: {len(successful)} removed, {len(failed)} failed")
                
                if failed:
                    print("Failed to remove:")
                    for app in failed[:5]:  # Show first 5 failures
                        print(f"  - {app}")
                        
        except Exception as e:
            print(f"Error removing bloatware: {e}")
    
    def _cli_apply_settings(self):
        """Apply Windows settings"""
        try:
            settings_manager = WindowsSettingsManager(lambda msg: print(f"[SETTINGS] {msg}"))
            recommended = settings_manager.get_recommended_settings()
            
            print(f"\nRecommended settings ({len(recommended)}):")
            for i, setting_key in enumerate(recommended, 1):
                # Try to get setting description
                setting_name = setting_key.replace('_', ' ').title()
                print(f"  {i}. {setting_name}")
            
            confirm = input(f"\nApply {len(recommended)} recommended settings? (y/n): ").strip().lower()
            if confirm == 'y':
                if not self.is_admin:
                    print("WARNING: Administrator privileges required for registry changes.")
                    confirm2 = input("Continue anyway? (y/n): ").strip().lower()
                    if confirm2 != 'y':
                        return
                
                print("Applying settings...")
                successful, failed = settings_manager.apply_multiple_settings(recommended)
                print(f"\nResults: {len(successful)} applied, {len(failed)} failed")
                
                if failed:
                    print("Failed to apply:")
                    for setting in failed[:5]:  # Show first 5 failures
                        print(f"  - {setting}")
                        
        except Exception as e:
            print(f"Error applying settings: {e}")
    
    def _cli_create_user(self):
        """Create a new user account"""
        try:
            username = input("Enter username: ").strip()
            if not username:
                print("Username cannot be empty.")
                return
            
            password = input("Enter password: ").strip()
            if not password:
                print("Password cannot be empty.")
                return
            
            admin_user = input("Make admin user? (y/n): ").strip().lower() == 'y'
            
            if not self.is_admin:
                print("ERROR: Administrator privileges are required to create user accounts.")
                return
            
            print(f"Creating {'admin' if admin_user else 'standard'} user '{username}'...")
            
            # Note: Actual user creation would require implementing the user creation method
            print("User creation functionality would be implemented here...")
            
        except Exception as e:
            print(f"Error creating user: {e}")
    
    def _cli_registry_operations(self):
        """Registry operations"""
        try:
            print("\n--- Registry Operations ---")
            print("1. Backup registry")
            print("2. View registry key")
            print("3. Export registry section")
            
            choice = input("Select option (1-3): ").strip()
            
            if choice == "1":
                print("Registry backup functionality would be implemented here...")
            elif choice == "2":
                key_path = input("Enter registry key path: ").strip()
                if key_path:
                    print(f"Would view registry key: {key_path}")
            elif choice == "3":
                section = input("Enter registry section to export: ").strip()
                if section:
                    print(f"Would export registry section: {section}")
            else:
                print("Invalid choice.")
                
        except Exception as e:
            print(f"Error with registry operations: {e}")
    
    def _cli_file_operations(self):
        """CLI file operations"""
        print("\n--- File Operations ---")
        print("1. Copy folder to public desktop")
        print("2. List available folders")
        print("3. Get folder information")
        print("4. Copy folder to custom location")
        
        choice = input("Select option (1-4): ").strip()
        
        folder_manager = FolderManager(lambda msg: print(f"[FILES] {msg}"))
        
        if choice == "1":
            self._cli_copy_to_public_desktop(folder_manager)
        elif choice == "2":
            self._cli_list_folders(folder_manager)
        elif choice == "3":
            self._cli_folder_info(folder_manager)
        elif choice == "4":
            self._cli_copy_folder_custom(folder_manager)
        else:
            print("Invalid choice.")
    
    def _cli_copy_to_public_desktop(self, folder_manager):
        """Copy folder to public desktop"""
        try:
            folders = folder_manager.get_available_folders()
            if not folders:
                print("No folders found in application directory.")
                return
            
            print("\nAvailable folders:")
            for i, folder in enumerate(folders, 1):
                print(f"  {i}. {folder.name}")
            
            try:
                selection = int(input("\nSelect folder number: ")) - 1
                if 0 <= selection < len(folders):
                    selected_folder = folders[selection]
                    
                    print(f"Copying contents of '{selected_folder.name}' to public desktop...")
                    result = copy_to_public_desktop(selected_folder)
                    
                    if result.success:
                        print(f"✅ Successfully copied {result.files_copied} files!")
                        print(f"   Processed: {result.files_processed}")
                        print(f"   Skipped: {result.files_skipped}")
                        print(f"   Time: {result.total_time_seconds:.2f} seconds")
                    else:
                        print(f"❌ Copy operation failed:")
                        for error in result.errors:
                            print(f"   {error}")
                else:
                    print("Invalid selection.")
                    
            except (ValueError, IndexError):
                print("Invalid selection.")
                
        except Exception as e:
            print(f"Error copying to public desktop: {e}")
    
    def _cli_list_folders(self, folder_manager):
        """List available folders"""
        try:
            folders = folder_manager.get_available_folders()
            print(f"\nFound {len(folders)} folders in application directory:")
            
            for i, folder in enumerate(folders, 1):
                info = folder_manager.get_folder_info(folder)
                if "error" not in info:
                    print(f"  {i:2}. {info['name']} - {info['file_count']} files, {info['size_formatted']}")
                else:
                    print(f"  {i:2}. {folder.name} - Error: {info['error']}")
                    
        except Exception as e:
            print(f"Error listing folders: {e}")
    
    def _cli_folder_info(self, folder_manager):
        """Get detailed folder information"""
        try:
            folder_name = input("Enter folder name: ").strip()
            if not folder_name:
                print("Folder name cannot be empty.")
                return
            
            folder_path = self.app_path / folder_name
            info = folder_manager.get_folder_info(folder_path)
            
            if "error" not in info:
                print(f"\nFolder Information for '{info['name']}':")
                print(f"  Path: {info['path']}")
                print(f"  Size: {info['size_formatted']} ({info['size_bytes']} bytes)")
                print(f"  Files: {info['file_count']}")
                print(f"  Directories: {info['directory_count']}")
                print(f"  Modified: {info['modified']}")
                print(f"  Readable: {'Yes' if info['is_readable'] else 'No'}")
                print(f"  Writable: {'Yes' if info['is_writable'] else 'No'}")
            else:
                print(f"Error: {info['error']}")
                
        except Exception as e:
            print(f"Error getting folder information: {e}")
    
    def _cli_copy_folder_custom(self, folder_manager):
        """Copy folder to custom location"""
        try:
            # Get source folder
            folders = folder_manager.get_available_folders()
            if not folders:
                print("No folders found in application directory.")
                return
            
            print("\nSource folders:")
            for i, folder in enumerate(folders, 1):
                print(f"  {i}. {folder.name}")
            
            try:
                selection = int(input("\nSelect source folder: ")) - 1
                if 0 <= selection < len(folders):
                    source_folder = folders[selection]
                else:
                    print("Invalid selection.")
                    return
            except (ValueError, IndexError):
                print("Invalid selection.")
                return
            
            # Get destination
            dest_path = input("Enter destination path: ").strip()
            if not dest_path:
                print("Destination path cannot be empty.")
                return
            
            dest_folder = Path(dest_path)
            
            print(f"Copying '{source_folder.name}' to '{dest_folder}'...")
            
            from file_ops import FolderOperation, CopyMode, ConflictResolution
            
            operation = FolderOperation(
                source_path=source_folder,
                destination_path=dest_folder,
                copy_mode=CopyMode.COPY,
                conflict_resolution=ConflictResolution.SKIP,
                create_destination=True
            )
            
            result = folder_manager.copy_folder_contents(operation)
            
            if result.success:
                print(f"✅ Successfully copied {result.files_copied} files!")
                print(f"   Total files processed: {result.files_processed}")
                print(f"   Files skipped: {result.files_skipped}")
                print(f"   Directories created: {result.directories_created}")
                print(f"   Time: {result.total_time_seconds:.2f} seconds")
            else:
                print(f"❌ Copy operation failed:")
                for error in result.errors:
                    print(f"   {error}")
                    
        except Exception as e:
            print(f"Error copying folder: {e}")
    
    def _cli_quick_setup(self):
        """CLI quick setup - combines multiple operations"""
        if not windows_setup_available:
            print("Quick setup requires Windows setup module.")
            return
        
        print("\n--- Quick Setup ---")
        print("This will perform a complete Windows setup:")
        print("1. Remove common bloatware")
        print("2. Apply recommended settings")
        print("3. Display essential software list")
        
        confirm = input("\nProceed with quick setup? (y/n): ").strip().lower()
        if confirm != 'y':
            return
        
        if not self.is_admin:
            print("\nWARNING: Quick setup works best with administrator privileges.")
            confirm2 = input("Continue anyway? (y/n): ").strip().lower()
            if confirm2 != 'y':
                return
        
        print("\n" + "="*50)
        print("STARTING QUICK SETUP")
        print("="*50)
        
        try:
            # 1. Remove bloatware
            print("\n1. REMOVING BLOATWARE...")
            bloatware_remover = BloatwareRemover(lambda msg: print(f"  [BLOAT] {msg}"))
            common_apps = bloatware_remover.get_common_bloatware()
            successful_removals, failed_removals = bloatware_remover.remove_multiple_apps(common_apps)
            print(f"   Result: {len(successful_removals)} removed, {len(failed_removals)} failed")
            
            # 2. Apply settings
            print("\n2. APPLYING WINDOWS SETTINGS...")
            settings_manager = WindowsSettingsManager(lambda msg: print(f"  [SETTINGS] {msg}"))
            recommended = settings_manager.get_recommended_settings()
            successful_settings, failed_settings = settings_manager.apply_multiple_settings(recommended)
            print(f"   Result: {len(successful_settings)} applied, {len(failed_settings)} failed")
            
            # 3. Display software recommendations
            print("\n3. ESSENTIAL SOFTWARE RECOMMENDATIONS...")
            essential_packages = self.config_manager.get_preset("Basic Office Setup")
            if essential_packages:
                print(f"   Recommended packages ({len(essential_packages)}):")
                for pkg in essential_packages:
                    print(f"     - {pkg}")
                print(f"\n   To install: python {sys.argv[0]} --cli")
                print(f"   Then select: Software Management -> Load preset -> Basic Office Setup")
            else:
                print("   No essential packages preset found")
            
            print("\n" + "="*50)
            print("QUICK SETUP COMPLETE")
            print("="*50)
            print(f"Bloatware removed: {len(successful_removals)}")
            print(f"Settings applied: {len(successful_settings)}")
            print(f"Software packages listed: {len(essential_packages) if essential_packages else 0}")
            print("\nRecommendation: Restart your computer to complete all changes.")
            
        except Exception as e:
            print(f"\n❌ Quick setup failed: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for filenames"""
        from datetime import datetime
        return datetime.now().strftime('%Y%m%d_%H%M%S')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description=f"Admin's ToolBox - IT Administration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              Start GUI application
  python main.py --cli        Start CLI interface
  python main.py --version    Show version information
        """
    )
    
    parser.add_argument(
        '--cli', 
        action='store_true',
        help='Start in command-line interface mode'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Admin\'s ToolBox 2.1'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    
    args = parser.parse_args()
    
    # Enable debug output if requested
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        print("Debug mode enabled")
    
    # Initialize application
    try:
        app = ITAdminApp()
    except Exception as e:
        print(f"ERROR: Failed to initialize application: {e}")
        return 1
    
    try:
        if args.cli:
            # Start CLI interface
            exit_code = app.start_cli()
        else:
            # Start GUI interface (default)
            exit_code = app.start_gui()
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()