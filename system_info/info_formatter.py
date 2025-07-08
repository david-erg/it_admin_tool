"""
System information formatting and export utilities.

This module provides comprehensive formatting and export capabilities for
system information including text, CSV, JSON, and HTML output formats.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import xml.etree.ElementTree as ET

from .hardware_detector import CPUInfo, MemoryInfo, StorageInfo, GPUInfo, SystemInfo
from .software_detector import OperatingSystemInfo, OfficeInfo, AntivirusInfo
from .network_detector import NetworkInfo, NetworkAdapter


@dataclass
class SystemInfoReport:
    """Complete system information report structure."""
    collection_timestamp: str
    hardware: Dict[str, Any]
    software: Dict[str, Any]
    network: Dict[str, Any]
    summary: Dict[str, str]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {
                'report_version': '1.0',
                'generated_by': 'IT Admin Tool',
                'collection_method': 'WMI/PowerShell'
            }


class InfoFormatter:
    """
    Formats and exports system information in various formats.
    
    This class provides methods for formatting system information into
    different output formats including text, CSV, JSON, HTML, and XML.
    """
    
    def __init__(self):
        self.timestamp_format = "%Y-%m-%d %H:%M:%S"
    
    def create_report(
        self, 
        hardware_info: Dict[str, Any],
        software_info: Dict[str, Any],
        network_info: NetworkInfo
    ) -> SystemInfoReport:
        """
        Create a comprehensive system information report.
        
        Args:
            hardware_info: Hardware information dictionary
            software_info: Software information dictionary
            network_info: Network information object
        
        Returns:
            SystemInfoReport: Complete system report
        """
        timestamp = datetime.now().strftime(self.timestamp_format)
        
        # Convert objects to dictionaries for JSON serialization
        hardware_dict = self._convert_to_dict(hardware_info)
        software_dict = self._convert_to_dict(software_info)
        network_dict = self._convert_to_dict(network_info)
        
        # Create summary for quick overview
        summary = self._create_summary(hardware_info, software_info, network_info)
        
        return SystemInfoReport(
            collection_timestamp=timestamp,
            hardware=hardware_dict,
            software=software_dict,
            network=network_dict,
            summary=summary
        )
    
    def _convert_to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert objects to dictionaries recursively."""
        if hasattr(obj, '__dict__'):
            return asdict(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_dict(item) for item in obj]
        else:
            return obj
    
    def _create_summary(
        self, 
        hardware_info: Dict[str, Any],
        software_info: Dict[str, Any], 
        network_info: NetworkInfo
    ) -> Dict[str, str]:
        """Create a summary of key system information."""
        summary = {}
        
        try:
            # System identification
            if 'system' in hardware_info:
                system = hardware_info['system']
                summary['Device Name'] = getattr(system, 'device_name', 'Unknown')
                summary['Manufacturer'] = getattr(system, 'manufacturer', 'Unknown')
                summary['Model'] = getattr(system, 'model', 'Unknown')
                summary['Serial Number'] = getattr(system, 'serial_number', 'Unknown')
            
            # Hardware summary
            if 'cpu' in hardware_info:
                cpu = hardware_info['cpu']
                summary['CPU'] = getattr(cpu, 'name', 'Unknown')
            
            if 'memory' in hardware_info:
                memory = hardware_info['memory']
                summary['RAM (GB)'] = str(getattr(memory, 'total_gb', 0))
            
            if 'storage' in hardware_info:
                storage = hardware_info['storage']
                drives = getattr(storage, 'drives', [])
                if drives:
                    drive_summaries = []
                    for drive in drives:
                        if isinstance(drive, dict):
                            letter = drive.get('letter', 'X:')
                            total = drive.get('total_gb', 0)
                            free = drive.get('free_gb', 0)
                            drive_summaries.append(f"{letter} {total}GB (Free: {free}GB)")
                    summary['Storage'] = ", ".join(drive_summaries) if drive_summaries else "Unknown"
                else:
                    summary['Storage'] = "Unknown"
            
            if 'gpu' in hardware_info:
                gpu_list = hardware_info['gpu']
                if gpu_list and len(gpu_list) > 0:
                    primary_gpu = gpu_list[0]
                    summary['GPU'] = getattr(primary_gpu, 'name', 'Unknown')
                else:
                    summary['GPU'] = "Unknown"
            
            # Software summary
            if 'operating_system' in software_info:
                os_info = software_info['operating_system']
                summary['OS Edition'] = getattr(os_info, 'name', 'Unknown')
            
            if 'antivirus_software' in software_info:
                av_list = software_info['antivirus_software']
                if av_list and len(av_list) > 0:
                    av_names = [getattr(av, 'display_name', 'Unknown') for av in av_list]
                    summary['Anti-Virus'] = ", ".join(av_names)
                else:
                    summary['Anti-Virus'] = "Not Detected"
            
            if 'office_products' in software_info:
                office_list = software_info['office_products']
                if office_list and len(office_list) > 0:
                    office_names = [getattr(office, 'product_name', 'Unknown') for office in office_list]
                    summary['Office Installed'] = ", ".join(office_names)
                else:
                    summary['Office Installed'] = "None detected"
            
            # Network summary
            summary['IP Address'] = network_info.primary_ip
            summary['MAC Address'] = network_info.primary_mac
            
            # Logged user
            try:
                import os
                summary['Logged User Name'] = os.getlogin() if hasattr(os, 'getlogin') else os.environ.get('USERNAME', 'Unknown')
            except Exception:
                summary['Logged User Name'] = 'Unknown'
            
            # Updated time
            summary['Updated Time'] = datetime.now().strftime(self.timestamp_format)
            
        except Exception as e:
            summary['Error'] = f"Summary generation error: {str(e)}"
        
        return summary
    
    def format_as_text(self, report: SystemInfoReport, detailed: bool = True) -> str:
        """
        Format report as text.
        
        Args:
            report: System information report
            detailed: Whether to include detailed information
        
        Returns:
            str: Formatted text report
        """
        lines = []
        
        # Header
        lines.append("=" * 60)
        lines.append("SYSTEM INFORMATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {report.collection_timestamp}")
        lines.append("")
        
        # Summary section
        lines.append("SUMMARY")
        lines.append("-" * 40)
        for key, value in report.summary.items():
            lines.append(f"{key:20}: {value}")
        lines.append("")
        
        if detailed:
            # Hardware section
            lines.append("HARDWARE INFORMATION")
            lines.append("-" * 40)
            lines.extend(self._format_hardware_text(report.hardware))
            lines.append("")
            
            # Software section
            lines.append("SOFTWARE INFORMATION")
            lines.append("-" * 40)
            lines.extend(self._format_software_text(report.software))
            lines.append("")
            
            # Network section
            lines.append("NETWORK INFORMATION")
            lines.append("-" * 40)
            lines.extend(self._format_network_text(report.network))
            lines.append("")
        
        # Footer
        lines.append("=" * 60)
        lines.append("End of Report")
        lines.append("=" * 60)
        
        return "\\n".join(lines)
    
    def _format_hardware_text(self, hardware: Dict[str, Any]) -> List[str]:
        """Format hardware information as text lines."""
        lines = []
        
        # System info
        if 'system' in hardware:
            system = hardware['system']
            lines.append("System:")
            for key, value in system.items():
                lines.append(f"  {key.replace('_', ' ').title()}: {value}")
            lines.append("")
        
        # CPU info
        if 'cpu' in hardware:
            cpu = hardware['cpu']
            lines.append("Processor:")
            for key, value in cpu.items():
                lines.append(f"  {key.replace('_', ' ').title()}: {value}")
            lines.append("")
        
        # Memory info
        if 'memory' in hardware:
            memory = hardware['memory']
            lines.append("Memory:")
            for key, value in memory.items():
                lines.append(f"  {key.replace('_', ' ').title()}: {value}")
            lines.append("")
        
        # Storage info
        if 'storage' in hardware:
            storage = hardware['storage']
            lines.append("Storage:")
            if 'drives' in storage and storage['drives']:
                for i, drive in enumerate(storage['drives'], 1):
                    lines.append(f"  Drive {i}:")
                    for key, value in drive.items():
                        lines.append(f"    {key.replace('_', ' ').title()}: {value}")
            lines.append("")
        
        # GPU info
        if 'gpu' in hardware:
            gpu_list = hardware['gpu']
            lines.append("Graphics:")
            if gpu_list:
                for i, gpu in enumerate(gpu_list, 1):
                    lines.append(f"  GPU {i}:")
                    for key, value in gpu.items():
                        lines.append(f"    {key.replace('_', ' ').title()}: {value}")
            lines.append("")
        
        return lines
    
    def _format_software_text(self, software: Dict[str, Any]) -> List[str]:
        """Format software information as text lines."""
        lines = []
        
        # Operating system
        if 'operating_system' in software:
            os_info = software['operating_system']
            lines.append("Operating System:")
            for key, value in os_info.items():
                lines.append(f"  {key.replace('_', ' ').title()}: {value}")
            lines.append("")
        
        # Office products
        if 'office_products' in software:
            office_list = software['office_products']
            lines.append("Microsoft Office:")
            if office_list:
                for i, office in enumerate(office_list, 1):
                    lines.append(f"  Product {i}:")
                    for key, value in office.items():
                        lines.append(f"    {key.replace('_', ' ').title()}: {value}")
            lines.append("")
        
        # Antivirus software
        if 'antivirus_software' in software:
            av_list = software['antivirus_software']
            lines.append("Antivirus Software:")
            if av_list:
                for i, av in enumerate(av_list, 1):
                    lines.append(f"  Product {i}:")
                    for key, value in av.items():
                        lines.append(f"    {key.replace('_', ' ').title()}: {value}")
            lines.append("")
        
        return lines
    
    def _format_network_text(self, network: Dict[str, Any]) -> List[str]:
        """Format network information as text lines."""
        lines = []
        
        # Primary network info
        lines.append(f"Primary IP Address: {network.get('primary_ip', 'Unknown')}")
        lines.append(f"Primary MAC Address: {network.get('primary_mac', 'Unknown')}")
        lines.append(f"Computer Name: {network.get('computer_name', 'Unknown')}")
        lines.append(f"Domain/Workgroup: {network.get('domain_workgroup', 'Unknown')}")
        lines.append(f"Internet Connectivity: {'Yes' if network.get('internet_connectivity', False) else 'No'}")
        
        if network.get('public_ip'):
            lines.append(f"Public IP Address: {network['public_ip']}")
        
        lines.append("")
        
        # Network adapters
        if 'adapters' in network and network['adapters']:
            lines.append("Network Adapters:")
            for i, adapter in enumerate(network['adapters'], 1):
                lines.append(f"  Adapter {i}:")
                for key, value in adapter.items():
                    if key != 'adapters':  # Avoid recursion
                        lines.append(f"    {key.replace('_', ' ').title()}: {value}")
        
        return lines
    
    def export_as_csv(self, report: SystemInfoReport, file_path: Path) -> bool:
        """
        Export report as CSV file.
        
        Args:
            report: System information report
            file_path: Path to save CSV file
        
        Returns:
            bool: True if export was successful
        """
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['Category', 'Property', 'Value'])
                
                # Write summary
                for key, value in report.summary.items():
                    writer.writerow(['Summary', key, value])
                
                # Write hardware info
                self._write_dict_to_csv(writer, report.hardware, 'Hardware')
                
                # Write software info
                self._write_dict_to_csv(writer, report.software, 'Software')
                
                # Write network info
                self._write_dict_to_csv(writer, report.network, 'Network')
                
                # Write metadata
                writer.writerow(['Metadata', 'Collection Time', report.collection_timestamp])
                for key, value in report.metadata.items():
                    writer.writerow(['Metadata', key, value])
            
            return True
            
        except Exception:
            return False
    
    def _write_dict_to_csv(self, writer: csv.writer, data: Dict[str, Any], category: str, prefix: str = ''):
        """Recursively write dictionary data to CSV."""
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                self._write_dict_to_csv(writer, value, category, full_key)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._write_dict_to_csv(writer, item, category, f"{full_key}[{i}]")
                    else:
                        writer.writerow([category, f"{full_key}[{i}]", str(item)])
            else:
                writer.writerow([category, full_key, str(value)])
    
    def export_as_json(self, report: SystemInfoReport, file_path: Path, pretty: bool = True) -> bool:
        """
        Export report as JSON file.
        
        Args:
            report: System information report
            file_path: Path to save JSON file
            pretty: Whether to format JSON with indentation
        
        Returns:
            bool: True if export was successful
        """
        try:
            report_dict = asdict(report)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(report_dict, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(report_dict, f, ensure_ascii=False)
            
            return True
            
        except Exception:
            return False
    
    def export_as_html(self, report: SystemInfoReport, file_path: Path) -> bool:
        """
        Export report as HTML file.
        
        Args:
            report: System information report
            file_path: Path to save HTML file
        
        Returns:
            bool: True if export was successful
        """
        try:
            html_content = self._generate_html_report(report)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
            
        except Exception:
            return False
    
    def _generate_html_report(self, report: SystemInfoReport) -> str:
        """Generate HTML report content."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Information Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .section h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .timestamp {{ color: #7f8c8d; font-style: italic; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>System Information Report</h1>
        <p class="timestamp">Generated: {report.collection_timestamp}</p>
    </div>
    
    <div class="section">
        <h2>Summary</h2>
        <table>
            <tr><th>Property</th><th>Value</th></tr>
"""
        
        # Add summary table
        for key, value in report.summary.items():
            html += f"            <tr><td>{key}</td><td>{value}</td></tr>\\n"
        
        html += """        </table>
    </div>
    
    <div class="section">
        <h2>Hardware Information</h2>
"""
        
        # Add hardware tables
        html += self._dict_to_html_tables(report.hardware)
        
        html += """    </div>
    
    <div class="section">
        <h2>Software Information</h2>
"""
        
        # Add software tables
        html += self._dict_to_html_tables(report.software)
        
        html += """    </div>
    
    <div class="section">
        <h2>Network Information</h2>
"""
        
        # Add network tables
        html += self._dict_to_html_tables(report.network)
        
        html += """    </div>
    
    <div class="section">
        <h2>Report Metadata</h2>
        <table>
            <tr><th>Property</th><th>Value</th></tr>
"""
        
        # Add metadata
        for key, value in report.metadata.items():
            html += f"            <tr><td>{key}</td><td>{value}</td></tr>\\n"
        
        html += """        </table>
    </div>
</body>
</html>"""
        
        return html
    
    def _dict_to_html_tables(self, data: Dict[str, Any]) -> str:
        """Convert dictionary data to HTML tables."""
        html = ""
        
        for section_name, section_data in data.items():
            if isinstance(section_data, dict):
                html += f"        <h3>{section_name.replace('_', ' ').title()}</h3>\\n"
                html += "        <table>\\n"
                html += "            <tr><th>Property</th><th>Value</th></tr>\\n"
                
                for key, value in section_data.items():
                    if not isinstance(value, (dict, list)):
                        html += f"            <tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>\\n"
                
                html += "        </table>\\n"
            
            elif isinstance(section_data, list):
                html += f"        <h3>{section_name.replace('_', ' ').title()}</h3>\\n"
                
                for i, item in enumerate(section_data):
                    if isinstance(item, dict):
                        html += f"        <h4>Item {i+1}</h4>\\n"
                        html += "        <table>\\n"
                        html += "            <tr><th>Property</th><th>Value</th></tr>\\n"
                        
                        for key, value in item.items():
                            if not isinstance(value, (dict, list)):
                                html += f"            <tr><td>{key.replace('_', ' ').title()}</td><td>{value}</td></tr>\\n"
                        
                        html += "        </table>\\n"
        
        return html
    
    def get_export_formats(self) -> List[str]:
        """
        Get list of supported export formats.
        
        Returns:
            List[str]: List of supported format extensions
        """
        return ['txt', 'csv', 'json', 'html']
    
    def export_report(
        self, 
        report: SystemInfoReport, 
        file_path: Path, 
        format_type: str = None
    ) -> bool:
        """
        Export report in specified format.
        
        Args:
            report: System information report
            file_path: Path to save file
            format_type: Export format ('txt', 'csv', 'json', 'html') or None to auto-detect
        
        Returns:
            bool: True if export was successful
        """
        if format_type is None:
            format_type = file_path.suffix.lower().lstrip('.')
        
        if format_type == 'txt':
            text_content = self.format_as_text(report, detailed=True)
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                return True
            except Exception:
                return False
        elif format_type == 'csv':
            return self.export_as_csv(report, file_path)
        elif format_type == 'json':
            return self.export_as_json(report, file_path)
        elif format_type == 'html':
            return self.export_as_html(report, file_path)
        else:
            return False