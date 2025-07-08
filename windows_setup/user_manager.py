"""
Local User Manager Module

Provides functionality to create and manage local Windows user accounts.
Requires administrator privileges for user account operations.
"""

import subprocess
import platform
import re
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum


class UserAccountType(Enum):
    """Types of user accounts"""
    STANDARD = "standard"
    ADMINISTRATOR = "administrator"
    GUEST = "guest"


class PasswordPolicy(Enum):
    """Password policy options"""
    CAN_CHANGE = "can_change"
    CANNOT_CHANGE = "cannot_change"
    NEVER_EXPIRES = "never_expires"
    EXPIRES = "expires"


@dataclass
class UserAccount:
    """Represents a Windows user account"""
    username: str
    full_name: Optional[str] = None
    description: Optional[str] = None
    password: Optional[str] = None
    account_type: UserAccountType = UserAccountType.STANDARD
    password_policies: List[PasswordPolicy] = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.password_policies is None:
            self.password_policies = []


@dataclass
class UserCreationResult:
    """Result of user account creation"""
    success: bool
    username: str
    created: bool = False
    added_to_group: bool = False
    policies_applied: bool = False
    error_message: Optional[str] = None


class LocalUserManager:
    """Manages local Windows user accounts"""
    
    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize LocalUserManager
        
        Args:
            progress_callback: Optional callback function for progress updates
        """
        self._validate_platform()
        self.progress_callback = progress_callback or self._default_progress_callback
    
    def _validate_platform(self) -> None:
        """Ensure we're running on Windows"""
        if platform.system() != "Windows":
            raise OSError("User management is only supported on Windows")
    
    def _default_progress_callback(self, message: str) -> None:
        """Default progress callback that prints to console"""
        print(message)
    
    def validate_username(self, username: str) -> Tuple[bool, str]:
        """
        Validate username according to Windows requirements
        
        Args:
            username: Username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username:
            return False, "Username cannot be empty"
        
        if len(username) > 20:
            return False, "Username cannot be longer than 20 characters"
        
        if len(username) < 1:
            return False, "Username must be at least 1 character"
        
        # Check for invalid characters
        invalid_chars = r'["/\[\]:;|=,+*?<>]'
        if re.search(invalid_chars, username):
            return False, "Username contains invalid characters"
        
        # Check for reserved names
        reserved_names = [
            "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
            "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4",
            "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
        ]
        if username.upper() in reserved_names:
            return False, f"'{username}' is a reserved name and cannot be used"
        
        # Check if username ends with period
        if username.endswith('.'):
            return False, "Username cannot end with a period"
        
        return True, ""
    
    def validate_password(self, password: str) -> Tuple[bool, str]:
        """
        Validate password according to basic Windows requirements
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password cannot be empty"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if len(password) > 127:
            return False, "Password cannot be longer than 127 characters"
        
        # Check password complexity (basic)
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        complexity_count = sum([has_upper, has_lower, has_digit, has_special])
        
        if complexity_count < 3:
            return False, "Password should contain at least 3 of: uppercase, lowercase, digits, special characters"
        
        return True, ""
    
    def user_exists(self, username: str, timeout: int = 15) -> bool:
        """
        Check if a user account already exists
        
        Args:
            username: Username to check
            timeout: Command timeout in seconds
            
        Returns:
            bool: True if user exists, False otherwise
        """
        try:
            cmd = f'net user "{username}"'
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # If command succeeds, user exists
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
    
    def create_user_account(self, user_account: UserAccount, timeout: int = 30) -> UserCreationResult:
        """
        Create a new local user account
        
        Args:
            user_account: UserAccount object with user details
            timeout: Command timeout in seconds
            
        Returns:
            UserCreationResult with creation status and details
        """
        result = UserCreationResult(success=False, username=user_account.username)
        
        # Validate inputs
        username_valid, username_error = self.validate_username(user_account.username)
        if not username_valid:
            result.error_message = f"Invalid username: {username_error}"
            return result
        
        if user_account.password:
            password_valid, password_error = self.validate_password(user_account.password)
            if not password_valid:
                result.error_message = f"Invalid password: {password_error}"
                return result
        
        # Check if user already exists
        if self.user_exists(user_account.username):
            result.error_message = f"User '{user_account.username}' already exists"
            return result
        
        self.progress_callback(f"=== CREATING LOCAL USER ACCOUNT ===")
        self.progress_callback(f"Creating user account: {user_account.username}")
        self.progress_callback("")
        
        try:
            # Step 1: Create the user account
            self.progress_callback("Creating user account...")
            
            # Build create command
            cmd_parts = ["net", "user", f'"{user_account.username}"']
            
            if user_account.password:
                cmd_parts.append(f'"{user_account.password}"')
            
            cmd_parts.append("/add")
            
            if user_account.full_name:
                cmd_parts.extend([f'/fullname:"{user_account.full_name}"'])
            
            if user_account.description:
                cmd_parts.extend([f'/comment:"{user_account.description}"'])
            
            if not user_account.is_active:
                cmd_parts.append("/active:no")
            
            create_cmd = " ".join(cmd_parts)
            create_result = subprocess.run(
                create_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if create_result.returncode == 0:
                self.progress_callback(f"✓ User account '{user_account.username}' created successfully")
                result.created = True
            else:
                result.error_message = f"Failed to create user: {create_result.stderr}"
                return result
            
            # Step 2: Add to appropriate group if administrator
            if user_account.account_type == UserAccountType.ADMINISTRATOR:
                self.progress_callback("Adding user to Administrators group...")
                
                admin_cmd = f'net localgroup administrators "{user_account.username}" /add'
                admin_result = subprocess.run(
                    admin_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                if admin_result.returncode == 0:
                    self.progress_callback(f"✓ User '{user_account.username}' added to Administrators group")
                    result.added_to_group = True
                else:
                    self.progress_callback(f"✗ Failed to add user to Administrators group: {admin_result.stderr}")
                    # Don't fail completely - user was created successfully
            else:
                result.added_to_group = True  # Not needed for standard users
            
            # Step 3: Apply password policies
            if user_account.password_policies:
                self.progress_callback("Applying password policies...")
                policy_success = self._apply_password_policies(user_account.username, user_account.password_policies, timeout)
                result.policies_applied = policy_success
                
                if policy_success:
                    self.progress_callback("✓ Password policies applied successfully")
                else:
                    self.progress_callback("⚠ Some password policies could not be applied")
            else:
                result.policies_applied = True  # No policies to apply
            
            # Final success check
            result.success = result.created and result.added_to_group and result.policies_applied
            
            self.progress_callback("")
            self.progress_callback("=== ACCOUNT CREATION COMPLETE ===")
            if result.success:
                self.progress_callback(f"Local {'administrator' if user_account.account_type == UserAccountType.ADMINISTRATOR else 'user'} '{user_account.username}' created successfully!")
                self.progress_callback("The new account is ready to use.")
            else:
                self.progress_callback("Account creation completed with warnings. See details above.")
            
            return result
            
        except subprocess.TimeoutExpired:
            result.error_message = "Operation timed out"
            self.progress_callback("✗ Operation timed out")
            return result
        except Exception as e:
            result.error_message = f"Unexpected error: {str(e)}"
            self.progress_callback(f"✗ Error creating user account: {str(e)}")
            return result
    
    def _apply_password_policies(self, username: str, policies: List[PasswordPolicy], timeout: int = 15) -> bool:
        """
        Apply password policies to a user account
        
        Args:
            username: Username to apply policies to
            policies: List of password policies
            timeout: Command timeout in seconds
            
        Returns:
            bool: True if all policies were applied successfully
        """
        success_count = 0
        total_policies = len(policies)
        
        for policy in policies:
            try:
                if policy == PasswordPolicy.NEVER_EXPIRES:
                    cmd = f'wmic useraccount where "name=\'{username}\'" set PasswordExpires=FALSE'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
                    if result.returncode == 0:
                        success_count += 1
                        self.progress_callback("  ✓ Password set to never expire")
                    else:
                        self.progress_callback("  ✗ Failed to set password never expires")
                
                elif policy == PasswordPolicy.CANNOT_CHANGE:
                    cmd = f'net user "{username}" /passwordchg:no'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
                    if result.returncode == 0:
                        success_count += 1
                        self.progress_callback("  ✓ User cannot change password")
                    else:
                        self.progress_callback("  ✗ Failed to set cannot change password")
                
                elif policy == PasswordPolicy.CAN_CHANGE:
                    cmd = f'net user "{username}" /passwordchg:yes'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
                    if result.returncode == 0:
                        success_count += 1
                        self.progress_callback("  ✓ User can change password")
                    else:
                        self.progress_callback("  ✗ Failed to set can change password")
                
                # Note: EXPIRES policy would require more complex WMIC commands
                # and is not implemented in this basic version
                
            except Exception as e:
                self.progress_callback(f"  ✗ Error applying policy {policy.value}: {str(e)}")
        
        return success_count == total_policies
    
    def delete_user_account(self, username: str, timeout: int = 30) -> bool:
        """
        Delete a local user account
        
        Args:
            username: Username to delete
            timeout: Command timeout in seconds
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            # Validate username
            username_valid, username_error = self.validate_username(username)
            if not username_valid:
                self.progress_callback(f"Invalid username: {username_error}")
                return False
            
            # Check if user exists
            if not self.user_exists(username):
                self.progress_callback(f"User '{username}' does not exist")
                return False
            
            self.progress_callback(f"Deleting user account: {username}")
            
            cmd = f'net user "{username}" /delete'
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                self.progress_callback(f"✓ User account '{username}' deleted successfully")
                return True
            else:
                self.progress_callback(f"✗ Failed to delete user: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.progress_callback(f"✗ Timeout deleting user '{username}'")
            return False
        except Exception as e:
            self.progress_callback(f"✗ Error deleting user '{username}': {str(e)}")
            return False
    
    def list_local_users(self, timeout: int = 30) -> List[str]:
        """
        Get list of local user accounts
        
        Args:
            timeout: Command timeout in seconds
            
        Returns:
            List of usernames
        """
        try:
            cmd = "net user"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                users = []
                
                # Parse the output to extract usernames
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('-') and not line.startswith('User accounts'):
                        # Split by spaces and filter out empty strings
                        line_users = [user.strip() for user in line.split() if user.strip()]
                        users.extend(line_users)
                
                # Filter out non-username lines (like "The command completed successfully")
                filtered_users = [user for user in users if not any(phrase in user.lower() for phrase in [
                    'command', 'completed', 'successfully', 'accounts', 'for'
                ])]
                
                return filtered_users
            else:
                return []
                
        except subprocess.TimeoutExpired:
            return []
        except Exception:
            return []
    
    def get_user_info(self, username: str, timeout: int = 15) -> Optional[Dict[str, str]]:
        """
        Get detailed information about a user account
        
        Args:
            username: Username to query
            timeout: Command timeout in seconds
            
        Returns:
            Dict with user information or None if user doesn't exist
        """
        try:
            cmd = f'net user "{username}"'
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                info = {}
                for line in result.stdout.splitlines():
                    if ':' in line:
                        key, value = line.split(':', 1)
                        info[key.strip()] = value.strip()
                return info
            else:
                return None
                
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None


# Convenience functions
def get_user_manager(progress_callback: Optional[Callable[[str], None]] = None) -> LocalUserManager:
    """Get a configured LocalUserManager instance"""
    return LocalUserManager(progress_callback)


def create_admin_user(username: str, password: str, full_name: Optional[str] = None,
                     password_never_expires: bool = False, cannot_change_password: bool = False,
                     progress_callback: Optional[Callable[[str], None]] = None) -> UserCreationResult:
    """
    Quick function to create a local administrator account
    
    Args:
        username: Username for the new account
        password: Password for the new account
        full_name: Optional full name
        password_never_expires: Whether password should never expire
        cannot_change_password: Whether user can change their password
        progress_callback: Optional progress callback function
        
    Returns:
        UserCreationResult with creation status
    """
    manager = LocalUserManager(progress_callback)
    
    # Build password policies
    policies = []
    if password_never_expires:
        policies.append(PasswordPolicy.NEVER_EXPIRES)
    if cannot_change_password:
        policies.append(PasswordPolicy.CANNOT_CHANGE)
    else:
        policies.append(PasswordPolicy.CAN_CHANGE)
    
    # Create user account object
    user_account = UserAccount(
        username=username,
        password=password,
        full_name=full_name,
        account_type=UserAccountType.ADMINISTRATOR,
        password_policies=policies
    )
    
    return manager.create_user_account(user_account)