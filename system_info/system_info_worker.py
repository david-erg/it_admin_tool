"""
Main system information worker and coordinator.

This module provides the main SystemInfoWorker class that coordinates
all system information detection and provides a unified interface for
the UI components.
"""

from typing import Dict, Optional, Any
from pathlib import Path
import traceback

from core import BaseWorker, is_windows_platform
from .hardware_detector import HardwareDetector
from .software_detector import SoftwareDetector
from .network_detector import NetworkDetector
from .info_formatter import InfoFormatter, SystemInfoReport


class SystemInfoManager:
    """
    Manages system information detection and formatting.
    
    This class provides a high-level interface for gathering comprehensive
    system information using multiple detection modules.
    """
    
    def __init__(self):
        self.hardware_detector = HardwareDetector()
        self.software_detector = SoftwareDetector()
        self.network_detector = NetworkDetector()
        self.formatter = InfoFormatter()
    
    def gather_all_info(self, progress_callback=None) -> Dict[str, Any]:
        """
        Gather comprehensive system information.
        
        Args:
            progress_callback: Optional callback for progress updates
        
        Returns:
            Dict[str, Any]: Complete system information
        """
        system_info = {}
        
        try:
            # Check platform compatibility
            if not is_windows_platform():
                if progress_callback:
                    progress_callback("Warning: Non-Windows platform detected")
            
            # Gather hardware information
            if progress_callback:
                progress_callback("Detecting hardware information...")
            
            hardware_info = self.hardware_detector.get_comprehensive_hardware_info()
            system_info['hardware'] = hardware_info
            
            if progress_callback:
                progress_callback("Hardware detection completed")
            
            # Gather software information
            if progress_callback:
                progress_callback("Detecting software information...")
            
            software_info = self.software_detector.get_comprehensive_software_info()
            system_info['software'] = software_info
            
            if progress_callback:
                progress_callback("Software detection completed")
            
            # Gather network information
            if progress_callback:
                progress_callback("Detecting network information...")
            
            network_info = self.network_detector.get_comprehensive_network_info()
            system_info['network'] = network_info
            
            if progress_callback:
                progress_callback("Network detection completed")
            
            # Create formatted summary
            if progress_callback:
                progress_callback("Creating system information summary...")
            
            summary = self._create_legacy_summary(hardware_info, software_info, network_info)
            system_info['summary'] = summary
            
            if progress_callback:
                progress_callback("System information gathering completed successfully")
            
        except Exception as e:
            error_msg = f"Error gathering system information: {str(e)}"
            if progress_callback:
                progress_callback(error_msg)
            system_info['error'] = error_msg
            system_info['traceback'] = traceback.format_exc()
        
        return system_info
    
    def _create_legacy_summary(
        self, 
        hardware_info: Dict[str, Any],
        software_info: Dict[str, Any],
        network_info: Any
    ) -> Dict[str, str]:
        """
        Create legacy format summary for backward compatibility.
        
        This method creates a summary in the same format as the original
        system_info_data dictionary for UI compatibility.
        """
        from datetime import datetime
        import os
        
        summary = {}
        
        try:
            # Device identification
            if 'system' in hardware_info:
                system = hardware_info['system']
                summary['Device Name'] = getattr(system, 'device_name', 'Unknown')
                summary['Manufacturer'] = getattr(system, 'manufacturer', 'Unknown')
                summary['Model'] = getattr(system, 'model', 'Unknown')
                summary['Serial Number'] = getattr(system, 'serial_number', 'Unknown')
            else:
                summary['Device Name'] = 'Unknown'
                summary['Manufacturer'] = 'Unknown'
                summary['Model'] = 'Unknown'
                summary['Serial Number'] = 'Unknown'
            
            # User information
            try:
                summary['Logged User Name'] = os.getlogin() if hasattr(os, 'getlogin') else os.environ.get('USERNAME', 'Unknown')
            except Exception:
                summary['Logged User Name'] = 'Unknown'
            
            # Hardware summary
            if 'cpu' in hardware_info:
                cpu = hardware_info['cpu']
                summary['CPU'] = getattr(cpu, 'name', 'Unknown')
            else:
                summary['CPU'] = 'Unknown'
            
            if 'gpu' in hardware_info:
                gpu_list = hardware_info['gpu']
                if gpu_list and len(gpu_list) > 0:
                    primary_gpu = gpu_list[0]
                    summary['GPU'] = getattr(primary_gpu, 'name', 'Unknown')
                else:
                    summary['GPU'] = 'Unknown'
            else:
                summary['GPU'] = 'Unknown'
            
            if 'memory' in hardware_info:
                memory = hardware_info['memory']
                summary['RAM (GB)'] = str(getattr(memory, 'total_gb', 0))
            else:
                summary['RAM (GB)'] = '0'
            
            if 'storage' in hardware_info:
                storage = hardware_info['storage']
                summary['Storage'] = self.hardware_detector.format_storage_summary(storage)
            else:
                summary['Storage'] = 'Unknown'
            
            # Software summary
            if 'operating_system' in software_info:
                os_info = software_info['operating_system']
                summary['OS Edition'] = getattr(os_info, 'name', 'Unknown')
            else:
                summary['OS Edition'] = 'Unknown'
            
            if 'antivirus_software' in software_info:
                av_list = software_info['antivirus_software']
                if av_list and len(av_list) > 0:
                    av_names = []
                    for av in av_list:
                        av_name = getattr(av, 'display_name', 'Unknown')
                        if av_name != 'Unknown':
                            av_names.append(av_name)
                    summary['Anti-Virus'] = ", ".join(av_names) if av_names else "Not Detected"
                else:
                    summary['Anti-Virus'] = "Not Detected"
            else:
                summary['Anti-Virus'] = "Not Detected"
            
            if 'office_products' in software_info:
                office_list = software_info['office_products']
                if office_list and len(office_list) > 0:
                    office_names = []
                    for office in office_list:
                        office_name = getattr(office, 'product_name', 'Unknown')
                        if office_name not in ['Unknown', 'None detected']:
                            office_names.append(office_name)
                    summary['Office Installed'] = ", ".join(office_names) if office_names else "None detected"
                else:
                    summary['Office Installed'] = "None detected"
            else:
                summary['Office Installed'] = "None detected"
            
            # Network summary
            summary['IP Address'] = getattr(network_info, 'primary_ip', 'Unknown')
            summary['MAC Address'] = getattr(network_info, 'primary_mac', 'Unknown')
            
            # Timestamp
            summary['Updated Time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception as e:
            # Ensure we always return a valid summary even if there are errors
            summary['Error'] = f"Summary creation error: {str(e)}"
            summary['Updated Time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return summary
    
    def create_report(self, system_info: Dict[str, Any]) -> Optional[SystemInfoReport]:
        """
        Create a formatted system information report.
        
        Args:
            system_info: Raw system information dictionary
        
        Returns:
            Optional[SystemInfoReport]: Formatted report or None if error
        """
        try:
            if 'hardware' in system_info and 'software' in system_info and 'network' in system_info:
                return self.formatter.create_report(
                    system_info['hardware'],
                    system_info['software'],
                    system_info['network']
                )
        except Exception:
            pass
        
        return None
    
    def export_info(
        self, 
        system_info: Dict[str, Any], 
        file_path: Path, 
        format_type: str = 'csv'
    ) -> bool:
        """
        Export system information to file.
        
        Args:
            system_info: System information dictionary
            file_path: Path to save file
            format_type: Export format ('csv', 'json', 'html', 'txt')
        
        Returns:
            bool: True if export was successful
        """
        try:
            report = self.create_report(system_info)
            if report:
                return self.formatter.export_report(report, file_path, format_type)
            else:
                # Fallback: export summary as CSV
                if format_type == 'csv' and 'summary' in system_info:
                    return self._export_summary_csv(system_info['summary'], file_path)
        except Exception:
            pass
        
        return False
    
    def _export_summary_csv(self, summary: Dict[str, str], file_path: Path) -> bool:
        """Export summary as simple CSV file."""
        try:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Property', 'Value'])
                for key, value in summary.items():
                    writer.writerow([key, value])
            return True
        except Exception:
            return False


class SystemInfoWorker(BaseWorker):
    """
    Worker class for gathering system information in the background.
    
    This worker handles comprehensive system information gathering without
    blocking the main UI thread, providing progress updates and results.
    """
    
    def __init__(self, include_detailed: bool = True):
        super().__init__()
        self.include_detailed = include_detailed
        self.manager = SystemInfoManager()
    
    def run(self):
        """Gather system information without blocking UI."""
        try:
            self.emit_progress("Starting system information gathering...")
            
            # Check platform compatibility
            if not is_windows_platform():
                self.emit_progress("Warning: Running on non-Windows platform - some features may not work")
            
            # Gather information with progress updates
            system_info = self.manager.gather_all_info(
                progress_callback=self.emit_progress
            )
            
            # Check for errors
            if 'error' in system_info:
                self.emit_error(system_info['error'])
            else:
                self.emit_progress("System information gathering completed successfully")
            
            # Return the summary for backward compatibility with UI
            if 'summary' in system_info:
                self.emit_result(system_info['summary'])
            else:
                self.emit_error("Failed to create system information summary")
            
            # Store full information for detailed access
            self._full_system_info = system_info
            
        except Exception as e:
            error_msg = f"System information gathering failed: {str(e)}"
            self.emit_error(error_msg)
            self.emit_result({})  # Return empty dict to prevent UI errors
        finally:
            self.emit_finished()
    
    def get_full_system_info(self) -> Dict[str, Any]:
        """
        Get complete system information (all detected data).
        
        Returns:
            Dict[str, Any]: Complete system information
        """
        return getattr(self, '_full_system_info', {})
    
    def get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware information only."""
        full_info = self.get_full_system_info()
        return full_info.get('hardware', {})
    
    def get_software_info(self) -> Dict[str, Any]:
        """Get software information only."""
        full_info = self.get_full_system_info()
        return full_info.get('software', {})
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information only."""
        full_info = self.get_full_system_info()
        return full_info.get('network', {})
    
    def create_detailed_report(self) -> Optional[SystemInfoReport]:
        """
        Create a detailed formatted report.
        
        Returns:
            Optional[SystemInfoReport]: Formatted report or None
        """
        full_info = self.get_full_system_info()
        return self.manager.create_report(full_info)
    
    def export_to_file(self, file_path: Path, format_type: str = 'csv') -> bool:
        """
        Export gathered information to file.
        
        Args:
            file_path: Path to save file
            format_type: Export format
        
        Returns:
            bool: True if export was successful
        """
        full_info = self.get_full_system_info()
        return self.manager.export_info(full_info, file_path, format_type)
    
    def get_system_summary(self) -> Dict[str, str]:
        """
        Get system summary in legacy format for UI compatibility.
        
        Returns:
            Dict[str, str]: System summary
        """
        full_info = self.get_full_system_info()
        return full_info.get('summary', {})
    
    def validate_system_requirements(self) -> Dict[str, bool]:
        """
        Validate system requirements for information gathering.
        
        Returns:
            Dict[str, bool]: System requirements status
        """
        return {
            'windows_platform': is_windows_platform(),
            'wmi_available': True,  # Assume available on Windows
            'powershell_available': True,  # Assume available on modern Windows
            'sufficient_privileges': True  # Information gathering doesn't require admin
        }
    
    def get_detection_capabilities(self) -> Dict[str, bool]:
        """
        Get information about detection capabilities.
        
        Returns:
            Dict[str, bool]: Detection capabilities
        """
        return {
            'hardware_detection': True,
            'software_detection': True,
            'network_detection': True,
            'office_detection': True,
            'antivirus_detection': True,
            'detailed_reporting': True,
            'multiple_export_formats': True
        }