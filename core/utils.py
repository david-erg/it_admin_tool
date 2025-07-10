"""
Core Utilities for IT Admin Tool

Provides essential utility functions for system operations, validation,
and common tasks. GUI-only version with simplified error handling.
"""

import os
import sys
import ctypes
import platform
import subprocess
import shlex
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Tuple
import json
import logging
from datetime import datetime

from .constants import (
    DEFAULT_COMMAND_TIMEOUT,
    WMI_QUERY_TIMEOUT,
    VALID_USERNAME_PATTERN,
    VALID_FILENAME_PATTERN,
    ERROR_MESSAGES
)


# =============================================================================
# SYSTEM INFORMATION
# =============================================================================

def is_windows_platform() -> bool:
    """
    Check if running on Windows platform.
    
    Returns:
        bool: True if Windows, False otherwise
    """
    return platform.system().lower() == 'windows'


def check_admin_privileges() -> bool:
    """
    Check if the current process has administrator privileges.
    
    Returns:
        bool: True if running as administrator
    """
    if not is_windows_platform():
        return False
    
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except (AttributeError, OSError):
        return False


def get_application_path() -> Path:
    """
    Get the application's base directory path.
    
    Returns:
        Path: Application directory path
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys.executable).parent
    else:
        # Running as Python script
        return Path(__file__).parent.parent


def get_system_info() -> Dict[str, str]:
    """
    Get basic system information.
    
    Returns:
        Dict[str, str]: System information dictionary
    """
    try:
        return {
            'platform': platform.platform(),
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'username': os.getenv('USERNAME', 'Unknown'),
            'computername': os.getenv('COMPUTERNAME', 'Unknown')
        }
    except Exception as e:
        logging.error(f"Failed to get system info: {e}")
        return {'error': str(e)}


# =============================================================================
# COMMAND EXECUTION
# =============================================================================

def run_command_with_timeout(
    command: Union[str, List[str]], 
    timeout: int = DEFAULT_COMMAND_TIMEOUT,
    shell: bool = False,
    capture_output: bool = True,
    check: bool = False
) -> Tuple[int, str, str]:
    """
    Run a command with timeout and proper error handling.
    
    Args:
        command: Command to execute (string or list)
        timeout: Command timeout in seconds
        shell: Whether to use shell
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise exception on non-zero exit
        
    Returns:
        Tuple[int, str, str]: (return_code, stdout, stderr)
        
    Raises:
        subprocess.TimeoutExpired: If command times out
        subprocess.CalledProcessError: If command fails and check=True
    """
    try:
        # Ensure command is properly formatted
        if isinstance(command, str) and not shell:
            command = shlex.split(command)
        
        # Run command with timeout
        result = subprocess.run(
            command,
            timeout=timeout,
            shell=shell,
            capture_output=capture_output,
            text=True,
            check=check
        )
        
        return result.returncode, result.stdout or "", result.stderr or ""
        
    except subprocess.TimeoutExpired as e:
        logging.error(f"Command timed out after {timeout}s: {command}")
        raise
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with exit code {e.returncode}: {command}")
        if capture_output and e.stderr:
            logging.error(f"Command stderr: {e.stderr}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error running command: {e}")
        raise


def query_wmic(query: str, timeout: int = WMI_QUERY_TIMEOUT) -> List[str]:
    """
    Execute a WMI query and return cleaned results.
    
    Args:
        query: WMI query string (e.g., "wmic cpu get name")
        timeout: Query timeout in seconds
        
    Returns:
        List[str]: Cleaned query results (empty lines and headers removed)
    """
    try:
        return_code, stdout, stderr = run_command_with_timeout(
            query, 
            timeout=timeout,
            shell=True,
            capture_output=True
        )
        
        if return_code != 0:
            logging.warning(f"WMI query returned non-zero exit code: {return_code}")
            return []
        
        # Clean and filter results
        lines = stdout.split('\n')
        cleaned = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines and headers
            if line and not line.lower().startswith(('name', 'caption', 'description')):
                cleaned.append(line)
        
        return cleaned
        
    except subprocess.TimeoutExpired:
        logging.error(f"WMI query timed out: {query}")
        return []
    except Exception as e:
        logging.error(f"WMI query failed: {query} - Error: {e}")
        return []


def safe_get_env_var(var_name: str, default: str = "") -> str:
    """
    Safely get environment variable with default fallback.
    
    Args:
        var_name: Environment variable name
        default: Default value if variable not found
        
    Returns:
        str: Environment variable value or default
    """
    try:
        return os.environ.get(var_name, default)
    except Exception:
        return default


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate a Windows username.
    
    Args:
        username: Username to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not username:
        return False, "Username cannot be empty"
    
    if len(username) > 20:
        return False, "Username too long (max 20 characters)"
    
    if not VALID_USERNAME_PATTERN.match(username):
        return False, "Username contains invalid characters"
    
    reserved_names = [
        'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4',
        'com5', 'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3',
        'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
    ]
    
    if username.lower() in reserved_names:
        return False, f"'{username}' is a reserved name"
    
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate a Windows password.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if len(password) > 127:
        return False, "Password too long (max 127 characters)"
    
    # Check for complexity requirements
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    complexity_count = sum([has_upper, has_lower, has_digit, has_special])
    
    if complexity_count < 3:
        return False, "Password must contain at least 3 of: uppercase, lowercase, digits, special characters"
    
    return True, ""


def validate_filename(filename: str) -> Tuple[bool, str]:
    """
    Validate a filename for Windows compatibility.
    
    Args:
        filename: Filename to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not filename:
        return False, "Filename cannot be empty"
    
    if len(filename) > 255:
        return False, "Filename too long (max 255 characters)"
    
    if not VALID_FILENAME_PATTERN.match(filename):
        return False, "Filename contains invalid characters"
    
    if filename.endswith('.') or filename.endswith(' '):
        return False, "Filename cannot end with period or space"
    
    return True, ""


def validate_path(path: Union[str, Path]) -> Tuple[bool, str]:
    """
    Validate a file system path.
    
    Args:
        path: Path to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    try:
        path_obj = Path(path)
        
        # Check if path is too long
        if len(str(path_obj)) > 260:
            return False, "Path too long (max 260 characters)"
        
        # Check if path is valid
        try:
            path_obj.resolve()
        except (OSError, ValueError):
            return False, "Invalid path format"
        
        return True, ""
        
    except Exception as e:
        return False, f"Path validation error: {str(e)}"


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_bytes(bytes_value: int) -> str:
    """
    Format byte value into human-readable string.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        str: Formatted string (e.g., "1.5 GB")
    """
    if bytes_value < 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    index = 0
    value = float(bytes_value)
    
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    
    if index == 0:
        return f"{int(value)} {units[index]}"
    else:
        return f"{value:.1f} {units[index]}"


def escape_command_arg(arg: str) -> str:
    """
    Escape a command line argument for safe execution.
    
    Args:
        arg: Argument to escape
        
    Returns:
        str: Escaped argument
    """
    # Simple escaping for Windows
    if ' ' in arg or '"' in arg:
        return f'"{arg.replace('"', '""')}"'
    return arg


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Remove trailing periods and spaces
    sanitized = sanitized.rstrip('. ')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed"
    
    return sanitized


def get_unique_filename(base_path: Path) -> Path:
    """
    Get a unique filename by appending numbers if file exists.
    
    Args:
        base_path: Base file path
        
    Returns:
        Path: Unique file path
    """
    if not base_path.exists():
        return base_path
    
    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent
    
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1


# =============================================================================
# CONFIGURATION HELPERS
# =============================================================================

def load_json_config(file_path: Path, default: Any = None) -> Any:
    """
    Load JSON configuration from file with error handling.
    
    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is invalid
        
    Returns:
        Any: Loaded configuration or default
    """
    try:
        if not file_path.exists():
            return default
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
        logging.error(f"Failed to load JSON config from {file_path}: {e}")
        return default
    except Exception as e:
        logging.error(f"Unexpected error loading JSON config: {e}")
        return default


def save_json_config(file_path: Path, data: Any) -> bool:
    """
    Save data to JSON file with error handling.
    
    Args:
        file_path: Path to save JSON file
        data: Data to save
        
    Returns:
        bool: True if saved successfully
    """
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON with pretty formatting
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
        
    except (OSError, UnicodeEncodeError) as e:
        logging.error(f"Failed to save JSON config to {file_path}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error saving JSON config: {e}")
        return False


# =============================================================================
# LOGGING
# =============================================================================

def setup_logging(log_file: Path, level: int = logging.INFO) -> None:
    """
    Set up application logging.
    
    Args:
        log_file: Path to log file
        level: Logging level
    """
    try:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logging.info(f"Logging initialized: {log_file}")
        
    except Exception as e:
        print(f"Failed to setup logging: {e}")


def get_error_message(error_key: str) -> str:
    """
    Get error message by key.
    
    Args:
        error_key: Error message key
        
    Returns:
        str: Error message
    """
    return ERROR_MESSAGES.get(error_key, f"Unknown error: {error_key}")