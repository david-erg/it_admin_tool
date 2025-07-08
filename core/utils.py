"""
Common utility functions for the IT Admin Tool.

This module provides utility functions that are used across multiple
modules in the application.
"""

import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Optional, Tuple


def check_admin_privileges() -> bool:
    """
    Check if the application is running with administrator privileges.
    
    Returns:
        bool: True if running as administrator, False otherwise
    """
    try:
        if platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # For non-Windows systems, check if running as root
            import os
            return os.geteuid() == 0
    except Exception:
        return False


def is_windows_platform() -> bool:
    """
    Check if the current platform is Windows.
    
    Returns:
        bool: True if running on Windows, False otherwise
    """
    return platform.system() == "Windows"


def get_application_path() -> Path:
    """
    Get the directory where the application is running from.
    
    This handles both compiled executables and Python scripts.
    
    Returns:
        Path: The directory containing the application
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys.executable).parent
    else:
        # Running as Python script
        return Path(__file__).parent.parent


def query_wmic(command: str, timeout: int = 30) -> List[str]:
    """
    Safely query WMI with proper error handling.
    
    Args:
        command: The WMIC command to execute
        timeout: Timeout in seconds (default: 30)
    
    Returns:
        List[str]: List of output lines, excluding header
    """
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            errors='replace',
            timeout=timeout
        )
        
        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return lines[1:] if len(lines) > 1 else []  # Skip header
        return []
        
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return []


def run_command_with_timeout(
    command: str, 
    timeout: int = 30,
    shell: bool = True,
    capture_output: bool = True
) -> Tuple[int, str, str]:
    """
    Run a command with timeout and proper error handling.
    
    Args:
        command: Command to execute
        timeout: Timeout in seconds
        shell: Whether to run in shell
        capture_output: Whether to capture stdout/stderr
    
    Returns:
        Tuple[int, str, str]: (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=capture_output,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout
        )
        
        return result.returncode, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        return -2, "", f"Command execution error: {str(e)}"


def safe_get_env_var(var_name: str, default: str = "Unknown") -> str:
    """
    Safely get an environment variable with fallback.
    
    Args:
        var_name: Environment variable name
        default: Default value if variable not found
    
    Returns:
        str: Environment variable value or default
    """
    import os
    return os.environ.get(var_name, default)


def format_bytes(bytes_value: int) -> str:
    """
    Format byte values into human-readable strings.
    
    Args:
        bytes_value: Number of bytes
    
    Returns:
        str: Formatted string (e.g., "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate a username for Windows account creation.
    
    Args:
        username: Username to validate
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not username:
        return False, "Username cannot be empty"
    
    if len(username) > 20:
        return False, "Username cannot exceed 20 characters"
    
    # Check for invalid characters
    invalid_chars = ['/', '\\', '[', ']', ':', ';', '|', '=', ',', '+', '*', '?', '<', '>', '"']
    for char in invalid_chars:
        if char in username:
            return False, f"Username cannot contain '{char}'"
    
    # Check for reserved names
    reserved_names = [
        'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5',
        'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4',
        'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
    ]
    
    if username.lower() in reserved_names:
        return False, f"'{username}' is a reserved name and cannot be used"
    
    return True, ""


def validate_password(password: str, min_length: int = 8) -> Tuple[bool, str]:
    """
    Validate a password for Windows account creation.
    
    Args:
        password: Password to validate
        min_length: Minimum password length
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"
    
    # Additional security checks can be added here
    # For now, just basic length validation
    return True, ""


def escape_command_arg(arg: str) -> str:
    """
    Escape command line arguments for safe execution.
    
    Args:
        arg: Argument to escape
    
    Returns:
        str: Escaped argument
    """
    # Basic escaping for Windows commands
    if ' ' in arg or '"' in arg:
        return f'"{arg.replace('"', '""')}"'
    return arg