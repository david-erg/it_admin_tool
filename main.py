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
    from core.config import load_application_config, save_application_config
    
    # Import all functional modules
    from software import ChocolateyManager, PackageInstaller, PackageSearcher, PresetsManager
    from system_info import SystemInfoWorker, HardwareDetector, SoftwareDetector, NetworkDetector
    from windows_setup import BloatwareRemover, WindowsSettingsManager, LocalUserManager, RegistryHelper
    from file_ops import FolderManager, PathUtilities
    
    # Import UI components
    from ui.main_window import ITAdminTool
    
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {e}")
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
        self.config = load_application_config()
        
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
            main_window = ITAdminTool()
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
                print("2. System Information")
                print("3. Windows Setup")
                print("4. File Operations")
                print("5. Quick Setup")
                print("0. Exit")
                
                choice = input("\nSelect an option (0-5): ").strip()
                
                if choice == "0":
                    print("Goodbye!")
                    return 0
                elif choice == "1":
                    self._cli_software_management()
                elif choice == "2":
                    self._cli_system_information()
                elif choice == "3":
                    self._cli_windows_setup()
                elif choice == "4":
                    self._cli_file_operations()
                elif choice == "5":
                    self._cli_quick_setup()
                else:
                    print("Invalid choice. Please try again.")
            
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
        
        choice = input("Select option (1-4): ").strip()
        
        if choice == "1":
            query = input("Enter search term: ").strip()
            if query:
                searcher = PackageSearcher()
                packages = searcher.search_packages(query)
                print(f"\nFound {len(packages)} packages:")
                for pkg in packages[:10]:  # Show first 10
                    print(f"  - {pkg}")
        
        elif choice == "2":
            packages = input("Enter package names (comma-separated): ").strip()
            if packages:
                package_list = [pkg.strip() for pkg in packages.split(',')]
                installer = PackageInstaller(lambda msg: print(f"[INSTALL] {msg}"))
                installer.install_packages(package_list)
        
        elif choice == "3":
            presets_manager = PresetsManager()
            available_presets = presets_manager.get_available_presets()
            print("\nAvailable presets:")
            for i, preset_name in enumerate(available_presets, 1):
                print(f"  {i}. {preset_name}")
            
            try:
                selection = int(input("Select preset number: ")) - 1
                if 0 <= selection < len(available_presets):
                    preset_name = available_presets[selection]
                    packages = presets_manager.get_preset_packages(preset_name)
                    print(f"Preset '{preset_name}' contains {len(packages)} packages")
                    
                    confirm = input("Install these packages? (y/n): ").strip().lower()
                    if confirm == 'y':
                        installer = PackageInstaller(lambda msg: print(f"[INSTALL] {msg}"))
                        installer.install_packages(packages)
            except (ValueError, IndexError):
                print("Invalid selection.")
        
        elif choice == "4":
            chocolatey = ChocolateyManager()
            if chocolatey.is_installed():
                version = chocolatey.get_version()
                print(f"Chocolatey is installed (version: {version})")
            else:
                print("Chocolatey is not installed")
                install = input("Install Chocolatey? (y/n): ").strip().lower()
                if install == 'y':
                    chocolatey.install_chocolatey()
    
    def _cli_system_information(self):
        """CLI system information operations"""
        print("\n--- System Information ---")
        print("Gathering system information...")
        
        worker = SystemInfoWorker()
        system_info = worker.gather_system_info()
        
        print("\nSystem Information:")
        print("-" * 40)
        for key, value in system_info.items():
            print(f"{key:20}: {value}")
        
        save = input("\nSave to file? (y/n): ").strip().lower()
        if save == 'y':
            filename = f"system_info_{worker.get_timestamp()}.csv"
            worker.export_to_csv(system_info, filename)
            print(f"Saved to: {filename}")
    
    def _cli_windows_setup(self):
        """CLI Windows setup operations"""
        print("\n--- Windows Setup ---")
        print("1. Remove bloatware")
        print("2. Apply settings")
        print("3. Create admin user")
        
        choice = input("Select option (1-3): ").strip()
        
        if choice == "1":
            bloatware_remover = BloatwareRemover(lambda msg: print(f"[BLOATWARE] {msg}"))
            common_apps = bloatware_remover.get_common_bloatware()
            
            print(f"\nCommon bloatware apps ({len(common_apps)}):")
            for app in common_apps[:10]:
                print(f"  - {app}")
            
            confirm = input("\nRemove common bloatware? (y/n): ").strip().lower()
            if confirm == 'y':
                successful, failed = bloatware_remover.remove_multiple_apps(common_apps)
                print(f"Removed {len(successful)} apps, {len(failed)} failed")
        
        elif choice == "2":
            settings_manager = WindowsSettingsManager(lambda msg: print(f"[SETTINGS] {msg}"))
            recommended = settings_manager.get_recommended_settings()
            
            print(f"\nRecommended settings ({len(recommended)}):")
            for setting in recommended[:10]:
                print(f"  - {setting}")
            
            confirm = input("\nApply recommended settings? (y/n): ").strip().lower()
            if confirm == 'y':
                successful, failed = settings_manager.apply_multiple_settings(recommended)
                print(f"Applied {len(successful)} settings, {len(failed)} failed")
        
        elif choice == "3":
            from windows_setup.user_manager import create_admin_user
            
            username = input("Enter username: ").strip()
            password = input("Enter password: ").strip()
            
            if username and password:
                result = create_admin_user(
                    username, password, 
                    progress_callback=lambda msg: print(f"[USER] {msg}")
                )
                if result.success:
                    print("Admin user created successfully!")
                else:
                    print(f"Failed to create user: {result.error_message}")
    
    def _cli_file_operations(self):
        """CLI file operations"""
        print("\n--- File Operations ---")
        print("1. Copy folder to public desktop")
        print("2. List available folders")
        print("3. Get folder information")
        
        choice = input("Select option (1-3): ").strip()
        
        folder_manager = FolderManager(lambda msg: print(f"[FILES] {msg}"))
        
        if choice == "1":
            folders = folder_manager.get_available_folders()
            if folders:
                print("\nAvailable folders:")
                for i, folder in enumerate(folders, 1):
                    print(f"  {i}. {folder.name}")
                
                try:
                    selection = int(input("Select folder number: ")) - 1
                    if 0 <= selection < len(folders):
                        selected_folder = folders[selection]
                        result = folder_manager.copy_to_public_desktop(selected_folder)
                        if result.success:
                            print(f"Copied {result.files_copied} files successfully!")
                        else:
                            print(f"Copy failed: {result.errors}")
                except (ValueError, IndexError):
                    print("Invalid selection.")
        
        elif choice == "2":
            folders = folder_manager.get_available_folders()
            print(f"\nFound {len(folders)} folders:")
            for folder in folders:
                print(f"  - {folder.name}")
        
        elif choice == "3":
            folder_name = input("Enter folder name: ").strip()
            if folder_name:
                folder_path = get_application_path() / folder_name
                info = folder_manager.get_folder_info(folder_path)
                
                print(f"\nFolder Information:")
                for key, value in info.items():
                    print(f"  {key}: {value}")
    
    def _cli_quick_setup(self):
        """CLI quick setup - combines multiple operations"""
        print("\n--- Quick Setup ---")
        print("This will perform a complete Windows setup:")
        print("1. Remove common bloatware")
        print("2. Apply recommended settings")
        print("3. Install essential software")
        
        confirm = input("\nProceed with quick setup? (y/n): ").strip().lower()
        if confirm != 'y':
            return
        
        print("\nStarting quick setup...")
        
        # 1. Remove bloatware
        print("\n1. Removing bloatware...")
        bloatware_remover = BloatwareRemover(lambda msg: print(f"  [BLOAT] {msg}"))
        common_apps = bloatware_remover.get_common_bloatware()
        successful_removals, failed_removals = bloatware_remover.remove_multiple_apps(common_apps)
        
        # 2. Apply settings
        print("\n2. Applying Windows settings...")
        settings_manager = WindowsSettingsManager(lambda msg: print(f"  [SETTINGS] {msg}"))
        recommended = settings_manager.get_recommended_settings()
        successful_settings, failed_settings = settings_manager.apply_multiple_settings(recommended)
        
        # 3. Install software
        print("\n3. Installing essential software...")
        presets_manager = PresetsManager()
        essential_packages = presets_manager.get_preset_packages("Basic Office Setup")
        installer = PackageInstaller(lambda msg: print(f"  [INSTALL] {msg}"))
        installer.install_packages(essential_packages)
        
        print("\n--- Quick Setup Complete ---")
        print(f"Bloatware removed: {len(successful_removals)}")
        print(f"Settings applied: {len(successful_settings)}")
        print(f"Software packages installed: {len(essential_packages)}")
        print("\nRecommended: Restart your computer to complete all changes.")


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
    
    # Initialize application
    app = ITAdminApp()
    
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
        print(f"FATAL ERROR: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()