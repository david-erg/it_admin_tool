"""
Registry Helper Module

Provides utilities for safe Windows registry manipulation.
All operations require administrator privileges.
"""

import subprocess
import platform
from typing import Optional, Dict, Any
from enum import Enum


class RegistryHive(Enum):
    """Windows Registry Hives"""
    HKLM = "HKEY_LOCAL_MACHINE"
    HKCU = "HKEY_CURRENT_USER"
    HKCR = "HKEY_CLASSES_ROOT"
    HKU = "HKEY_USERS"
    HKCC = "HKEY_CURRENT_CONFIG"


class RegistryValueType(Enum):
    """Windows Registry Value Types"""
    REG_SZ = "REG_SZ"           # String
    REG_DWORD = "REG_DWORD"     # 32-bit number
    REG_QWORD = "REG_QWORD"     # 64-bit number
    REG_BINARY = "REG_BINARY"   # Binary data
    REG_MULTI_SZ = "REG_MULTI_SZ"  # Multi-string
    REG_EXPAND_SZ = "REG_EXPAND_SZ"  # Expandable string


class RegistryHelper:
    """Helper class for Windows registry operations"""
    
    def __init__(self):
        self._validate_platform()
    
    def _validate_platform(self) -> None:
        """Ensure we're running on Windows"""
        if platform.system() != "Windows":
            raise OSError("Registry operations are only supported on Windows")
    
    def add_value(self, hive: RegistryHive, path: str, name: str, 
                  value: Any, value_type: RegistryValueType, 
                  force: bool = True, timeout: int = 15) -> bool:
        """
        Add or modify a registry value
        
        Args:
            hive: Registry hive (HKLM, HKCU, etc.)
            path: Registry path within the hive
            name: Value name
            value: Value data
            value_type: Type of registry value
            force: Use /f flag to force overwrite
            timeout: Command timeout in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Construct full registry path
            full_path = f'"{hive.value}\\{path.strip("\\")}"'
            
            # Build command
            cmd_parts = [
                "reg", "add", full_path,
                "/v", f'"{name}"',
                "/t", value_type.value,
                "/d", f'"{value}"'
            ]
            
            if force:
                cmd_parts.append("/f")
            
            # Execute command
            result = subprocess.run(
                " ".join(cmd_parts),
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
    
    def query_value(self, hive: RegistryHive, path: str, 
                   name: Optional[str] = None, timeout: int = 15) -> Optional[str]:
        """
        Query a registry value
        
        Args:
            hive: Registry hive
            path: Registry path within the hive
            name: Value name (None for default value)
            timeout: Command timeout in seconds
            
        Returns:
            str: Registry value or None if not found
        """
        try:
            full_path = f'"{hive.value}\\{path.strip("\\")}"'
            cmd_parts = ["reg", "query", full_path]
            
            if name:
                cmd_parts.extend(["/v", f'"{name}"'])
            
            result = subprocess.run(
                " ".join(cmd_parts),
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            return None
            
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None
    
    def delete_value(self, hive: RegistryHive, path: str, 
                    name: str, force: bool = True, timeout: int = 15) -> bool:
        """
        Delete a registry value
        
        Args:
            hive: Registry hive
            path: Registry path within the hive
            name: Value name to delete
            force: Use /f flag to force deletion
            timeout: Command timeout in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            full_path = f'"{hive.value}\\{path.strip("\\")}"'
            cmd_parts = ["reg", "delete", full_path, "/v", f'"{name}"']
            
            if force:
                cmd_parts.append("/f")
            
            result = subprocess.run(
                " ".join(cmd_parts),
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
    
    def create_key(self, hive: RegistryHive, path: str, 
                   force: bool = True, timeout: int = 15) -> bool:
        """
        Create a registry key
        
        Args:
            hive: Registry hive
            path: Registry path to create
            force: Use /f flag to force creation
            timeout: Command timeout in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            full_path = f'"{hive.value}\\{path.strip("\\")}"'
            cmd_parts = ["reg", "add", full_path]
            
            if force:
                cmd_parts.append("/f")
            
            result = subprocess.run(
                " ".join(cmd_parts),
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
    
    def apply_multiple_values(self, registry_changes: Dict[str, Dict[str, Any]], 
                            timeout: int = 15) -> Dict[str, bool]:
        """
        Apply multiple registry changes efficiently
        
        Args:
            registry_changes: Dictionary of registry changes in format:
                {
                    "change_name": {
                        "hive": RegistryHive.HKLM,
                        "path": "SOFTWARE\\...",
                        "name": "ValueName",
                        "value": "ValueData",
                        "type": RegistryValueType.REG_DWORD
                    }
                }
            timeout: Timeout per operation
            
        Returns:
            Dict[str, bool]: Results for each change
        """
        results = {}
        
        for change_name, change_data in registry_changes.items():
            try:
                success = self.add_value(
                    hive=change_data["hive"],
                    path=change_data["path"],
                    name=change_data["name"],
                    value=change_data["value"],
                    value_type=change_data["type"],
                    timeout=timeout
                )
                results[change_name] = success
            except Exception:
                results[change_name] = False
        
        return results


# Common registry helper functions for convenience
def get_registry_helper() -> RegistryHelper:
    """Get a configured RegistryHelper instance"""
    return RegistryHelper()


def quick_reg_add(hive_path: str, name: str, value: Any, 
                 value_type: str = "REG_DWORD") -> bool:
    """
    Quick registry add function for simple operations
    
    Args:
        hive_path: Full path like "HKCU\\Software\\Microsoft\\..."
        name: Value name
        value: Value data
        value_type: Registry value type string
        
    Returns:
        bool: Success status
    """
    try:
        helper = RegistryHelper()
        
        # Parse hive from path
        hive_mapping = {
            "HKLM": RegistryHive.HKLM,
            "HKCU": RegistryHive.HKCU,
            "HKCR": RegistryHive.HKCR,
            "HKU": RegistryHive.HKU,
            "HKCC": RegistryHive.HKCC
        }
        
        # Split path
        parts = hive_path.split("\\", 1)
        if len(parts) != 2:
            return False
        
        hive_str, path = parts
        hive = hive_mapping.get(hive_str.upper())
        if not hive:
            return False
        
        # Get value type
        try:
            reg_type = RegistryValueType(value_type.upper())
        except ValueError:
            reg_type = RegistryValueType.REG_DWORD
        
        return helper.add_value(hive, path, name, value, reg_type)
        
    except Exception:
        return False