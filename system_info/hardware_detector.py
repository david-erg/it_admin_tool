"""
Hardware detection and information gathering.

This module provides comprehensive hardware detection capabilities including
CPU, memory, storage, GPU, and system identification information.
"""

import subprocess
import shutil
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from core import query_wmic, run_command_with_timeout, safe_get_env_var


@dataclass
class CPUInfo:
    """CPU information structure."""
    name: str
    cores: int = 0
    threads: int = 0
    architecture: str = ""
    max_clock_speed: str = ""
    current_clock_speed: str = ""
    manufacturer: str = ""


@dataclass
class MemoryInfo:
    """Memory information structure."""
    total_gb: float
    available_gb: float = 0.0
    used_gb: float = 0.0
    usage_percent: float = 0.0
    slots_total: int = 0
    slots_used: int = 0


@dataclass
class StorageInfo:
    """Storage information structure."""
    drives: List[Dict[str, any]]
    total_capacity_gb: float = 0.0
    total_free_gb: float = 0.0
    total_used_gb: float = 0.0


@dataclass
class GPUInfo:
    """GPU information structure."""
    name: str
    driver_version: str = ""
    memory_mb: int = 0
    status: str = ""


@dataclass
class SystemInfo:
    """System identification information."""
    device_name: str
    manufacturer: str = ""
    model: str = ""
    serial_number: str = ""
    bios_version: str = ""
    motherboard: str = ""


class HardwareDetector:
    """
    Detects and gathers hardware information.
    
    This class provides methods for detecting various hardware components
    and system identification information using WMI and system commands.
    """
    
    def __init__(self):
        self.timeout = 30  # Default timeout for hardware detection commands
    
    def detect_cpu_info(self) -> CPUInfo:
        """
        Detect CPU information.
        
        Returns:
            CPUInfo: CPU information structure
        """
        try:
            # Get CPU name
            cpu_names = query_wmic("wmic cpu get name")
            cpu_name = cpu_names[0] if cpu_names else "Unknown CPU"
            
            # Get CPU details
            cpu_details = self._get_cpu_details()
            
            return CPUInfo(
                name=cpu_name,
                cores=cpu_details.get('cores', 0),
                threads=cpu_details.get('threads', 0),
                architecture=cpu_details.get('architecture', ''),
                max_clock_speed=cpu_details.get('max_clock_speed', ''),
                current_clock_speed=cpu_details.get('current_clock_speed', ''),
                manufacturer=cpu_details.get('manufacturer', '')
            )
            
        except Exception as e:
            return CPUInfo(name=f"Detection Error: {str(e)}")
    
    def _get_cpu_details(self) -> Dict[str, any]:
        """Get detailed CPU information."""
        details = {}
        
        try:
            # Get core count
            cores = query_wmic("wmic cpu get NumberOfCores")
            if cores:
                details['cores'] = int(cores[0]) if cores[0].isdigit() else 0
            
            # Get thread count
            threads = query_wmic("wmic cpu get NumberOfLogicalProcessors")
            if threads:
                details['threads'] = int(threads[0]) if threads[0].isdigit() else 0
            
            # Get architecture
            architecture = query_wmic("wmic cpu get Architecture")
            if architecture:
                arch_map = {'0': 'x86', '1': 'MIPS', '2': 'Alpha', '3': 'PowerPC', '6': 'Itanium', '9': 'x64'}
                details['architecture'] = arch_map.get(architecture[0], 'Unknown')
            
            # Get clock speeds
            max_speed = query_wmic("wmic cpu get MaxClockSpeed")
            if max_speed and max_speed[0].isdigit():
                details['max_clock_speed'] = f"{int(max_speed[0])} MHz"
            
            current_speed = query_wmic("wmic cpu get CurrentClockSpeed")
            if current_speed and current_speed[0].isdigit():
                details['current_clock_speed'] = f"{int(current_speed[0])} MHz"
            
            # Get manufacturer
            manufacturer = query_wmic("wmic cpu get Manufacturer")
            if manufacturer:
                details['manufacturer'] = manufacturer[0]
                
        except Exception:
            pass  # Return partial details on error
        
        return details
    
    def detect_memory_info(self) -> MemoryInfo:
        """
        Detect memory information.
        
        Returns:
            MemoryInfo: Memory information structure
        """
        try:
            # Get total physical memory
            total_memory = query_wmic("wmic computersystem get TotalPhysicalMemory")
            total_gb = 0.0
            
            if total_memory and total_memory[0].isdigit():
                total_gb = round(int(total_memory[0]) / 1e9, 1)
            
            # Get available memory using PowerShell for more accuracy
            available_gb, used_gb, usage_percent = self._get_memory_usage()
            
            # Get memory slot information
            slots_info = self._get_memory_slots()
            
            return MemoryInfo(
                total_gb=total_gb,
                available_gb=available_gb,
                used_gb=used_gb,
                usage_percent=usage_percent,
                slots_total=slots_info.get('total_slots', 0),
                slots_used=slots_info.get('used_slots', 0)
            )
            
        except Exception as e:
            return MemoryInfo(total_gb=0.0)
    
    def _get_memory_usage(self) -> Tuple[float, float, float]:
        """Get current memory usage information."""
        try:
            cmd = '''powershell -Command "Get-CimInstance -ClassName Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory"'''
            return_code, stdout, stderr = run_command_with_timeout(cmd, timeout=15)
            
            if return_code == 0:
                lines = stdout.strip().split('\n')
                if len(lines) >= 2:
                    # Parse the output to extract memory values
                    for line in lines[1:]:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 2:
                                try:
                                    total_kb = int(parts[0])
                                    free_kb = int(parts[1])
                                    
                                    available_gb = round(free_kb / 1e6, 1)
                                    total_gb = round(total_kb / 1e6, 1)
                                    used_gb = round(total_gb - available_gb, 1)
                                    usage_percent = round((used_gb / total_gb) * 100, 1) if total_gb > 0 else 0.0
                                    
                                    return available_gb, used_gb, usage_percent
                                except (ValueError, IndexError):
                                    continue
        except Exception:
            pass
        
        return 0.0, 0.0, 0.0
    
    def _get_memory_slots(self) -> Dict[str, int]:
        """Get memory slot information."""
        try:
            # Get total memory slots
            total_slots = query_wmic("wmic memphysical get MemoryDevices")
            total = int(total_slots[0]) if total_slots and total_slots[0].isdigit() else 0
            
            # Get used memory slots (count of physical memory modules)
            used_slots_data = query_wmic("wmic memorychip get DeviceLocator")
            used = len([slot for slot in used_slots_data if slot.strip()]) if used_slots_data else 0
            
            return {'total_slots': total, 'used_slots': used}
            
        except Exception:
            return {'total_slots': 0, 'used_slots': 0}
    
    def detect_storage_info(self) -> StorageInfo:
        """
        Detect storage information.
        
        Returns:
            StorageInfo: Storage information structure
        """
        try:
            drives = []
            total_capacity = 0.0
            total_free = 0.0
            
            # Get logical disk information
            return_code, stdout, stderr = run_command_with_timeout(
                "wmic logicaldisk get size,freespace,caption,drivetype,filesystem",
                timeout=15
            )
            
            if return_code == 0:
                lines = stdout.splitlines()[1:]  # Skip header
                
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        try:
                            caption = parts[0]
                            drive_type = int(parts[1]) if parts[1].isdigit() else 0
                            filesystem = parts[2] if len(parts) > 2 else ""
                            free_bytes = int(parts[3]) if parts[3].isdigit() else 0
                            total_bytes = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
                            
                            # Only include hard drives (type 3) and removable drives (type 2)
                            if drive_type in [2, 3] and total_bytes > 0:
                                free_gb = round(free_bytes / 1e9, 1)
                                total_gb = round(total_bytes / 1e9, 1)
                                used_gb = round(total_gb - free_gb, 1)
                                
                                drive_info = {
                                    'letter': caption,
                                    'filesystem': filesystem,
                                    'total_gb': total_gb,
                                    'free_gb': free_gb,
                                    'used_gb': used_gb,
                                    'usage_percent': round((used_gb / total_gb) * 100, 1) if total_gb > 0 else 0,
                                    'drive_type': self._get_drive_type_name(drive_type)
                                }
                                
                                drives.append(drive_info)
                                total_capacity += total_gb
                                total_free += free_gb
                                
                        except (ValueError, IndexError):
                            continue
            
            total_used = total_capacity - total_free
            
            return StorageInfo(
                drives=drives,
                total_capacity_gb=round(total_capacity, 1),
                total_free_gb=round(total_free, 1),
                total_used_gb=round(total_used, 1)
            )
            
        except Exception as e:
            return StorageInfo(drives=[])
    
    def _get_drive_type_name(self, drive_type: int) -> str:
        """Convert drive type number to readable name."""
        drive_types = {
            0: "Unknown",
            1: "No Root Directory",
            2: "Removable Disk",
            3: "Local Disk",
            4: "Network Drive",
            5: "Compact Disc",
            6: "RAM Disk"
        }
        return drive_types.get(drive_type, "Unknown")
    
    def detect_gpu_info(self) -> List[GPUInfo]:
        """
        Detect GPU information.
        
        Returns:
            List[GPUInfo]: List of GPU information structures
        """
        gpus = []
        
        try:
            # Get GPU names
            gpu_names = query_wmic("wmic path win32_VideoController get name")
            
            # Get GPU driver versions
            gpu_drivers = query_wmic("wmic path win32_VideoController get DriverVersion")
            
            # Get GPU memory (adapter RAM)
            gpu_memory = query_wmic("wmic path win32_VideoController get AdapterRAM")
            
            # Get GPU status
            gpu_status = query_wmic("wmic path win32_VideoController get Status")
            
            # Combine the information
            max_count = max(len(gpu_names), len(gpu_drivers), len(gpu_memory), len(gpu_status))
            
            for i in range(max_count):
                name = gpu_names[i] if i < len(gpu_names) else "Unknown GPU"
                driver = gpu_drivers[i] if i < len(gpu_drivers) else ""
                memory_bytes = gpu_memory[i] if i < len(gpu_memory) else "0"
                status = gpu_status[i] if i < len(gpu_status) else ""
                
                # Convert memory to MB
                memory_mb = 0
                try:
                    if memory_bytes.isdigit():
                        memory_mb = int(int(memory_bytes) / 1048576)  # Convert bytes to MB
                except (ValueError, ZeroDivisionError):
                    memory_mb = 0
                
                # Skip generic or virtual displays
                if not any(skip in name.lower() for skip in ['microsoft basic', 'generic', 'virtual']):
                    gpu_info = GPUInfo(
                        name=name,
                        driver_version=driver,
                        memory_mb=memory_mb,
                        status=status
                    )
                    gpus.append(gpu_info)
            
        except Exception:
            # Fallback: at least try to get basic GPU name
            try:
                gpu_names = query_wmic("wmic path win32_VideoController get name")
                if gpu_names:
                    gpus.append(GPUInfo(name=gpu_names[0]))
            except Exception:
                gpus.append(GPUInfo(name="Detection Failed"))
        
        return gpus if gpus else [GPUInfo(name="No GPU Detected")]
    
    def detect_system_info(self) -> SystemInfo:
        """
        Detect system identification information.
        
        Returns:
            SystemInfo: System identification structure
        """
        try:
            # Device name
            device_name = safe_get_env_var("COMPUTERNAME", "Unknown")
            
            # Manufacturer and model
            manufacturer = query_wmic("wmic computersystem get manufacturer")
            manufacturer = manufacturer[0] if manufacturer else "Unknown"
            
            model = query_wmic("wmic computersystem get model")
            model = model[0] if model else "Unknown"
            
            # Serial number
            serial_number = query_wmic("wmic bios get serialnumber")
            serial_number = serial_number[0] if serial_number else "Unknown"
            
            # BIOS version
            bios_version = query_wmic("wmic bios get version")
            bios_version = bios_version[0] if bios_version else "Unknown"
            
            # Motherboard information
            motherboard = self._get_motherboard_info()
            
            return SystemInfo(
                device_name=device_name,
                manufacturer=manufacturer,
                model=model,
                serial_number=serial_number,
                bios_version=bios_version,
                motherboard=motherboard
            )
            
        except Exception as e:
            return SystemInfo(
                device_name=safe_get_env_var("COMPUTERNAME", "Unknown"),
                manufacturer=f"Detection Error: {str(e)}"
            )
    
    def _get_motherboard_info(self) -> str:
        """Get motherboard information."""
        try:
            # Get motherboard manufacturer and product
            mb_manufacturer = query_wmic("wmic baseboard get manufacturer")
            mb_product = query_wmic("wmic baseboard get product")
            
            manufacturer = mb_manufacturer[0] if mb_manufacturer else ""
            product = mb_product[0] if mb_product else ""
            
            if manufacturer and product:
                return f"{manufacturer} {product}".strip()
            elif manufacturer:
                return manufacturer
            elif product:
                return product
            else:
                return "Unknown"
                
        except Exception:
            return "Unknown"
    
    def get_comprehensive_hardware_info(self) -> Dict[str, any]:
        """
        Get comprehensive hardware information.
        
        Returns:
            Dict: Complete hardware information
        """
        return {
            'system': self.detect_system_info(),
            'cpu': self.detect_cpu_info(),
            'memory': self.detect_memory_info(),
            'storage': self.detect_storage_info(),
            'gpu': self.detect_gpu_info()
        }
    
    def format_storage_summary(self, storage_info: StorageInfo) -> str:
        """Format storage information for display."""
        if not storage_info.drives:
            return "No storage detected"
        
        drive_summaries = []
        for drive in storage_info.drives:
            drive_summaries.append(
                f"{drive['letter']} {drive['total_gb']}GB (Free: {drive['free_gb']}GB)"
            )
        
        return ", ".join(drive_summaries)
    
    def format_gpu_summary(self, gpu_info: List[GPUInfo]) -> str:
        """Format GPU information for display."""
        if not gpu_info:
            return "No GPU detected"
        
        # Return primary GPU name
        primary_gpu = gpu_info[0]
        if len(gpu_info) == 1:
            return primary_gpu.name
        else:
            return f"{primary_gpu.name} (+{len(gpu_info)-1} more)"