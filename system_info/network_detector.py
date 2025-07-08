"""
Network information detection and gathering.

This module provides comprehensive network information detection including
IP addresses, MAC addresses, network adapters, and connectivity information.
"""

import subprocess
import socket
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from core import run_command_with_timeout, query_wmic


@dataclass
class NetworkAdapter:
    """Network adapter information structure."""
    name: str
    description: str = ""
    mac_address: str = ""
    ip_addresses: List[str] = None
    subnet_mask: str = ""
    default_gateway: str = ""
    dns_servers: List[str] = None
    dhcp_enabled: bool = False
    adapter_type: str = ""
    speed: str = ""
    status: str = ""
    
    def __post_init__(self):
        if self.ip_addresses is None:
            self.ip_addresses = []
        if self.dns_servers is None:
            self.dns_servers = []


@dataclass
class NetworkInfo:
    """Complete network information structure."""
    primary_ip: str
    primary_mac: str
    computer_name: str
    domain_workgroup: str
    adapters: List[NetworkAdapter] = None
    internet_connectivity: bool = False
    public_ip: str = ""
    
    def __post_init__(self):
        if self.adapters is None:
            self.adapters = []


class NetworkDetector:
    """
    Detects and gathers network information.
    
    This class provides methods for detecting network adapters, IP addresses,
    MAC addresses, and connectivity information.
    """
    
    def __init__(self):
        self.timeout = 30
    
    def detect_primary_network_info(self) -> Tuple[str, str]:
        """
        Detect primary IP and MAC addresses.
        
        Returns:
            Tuple[str, str]: (primary_ip, primary_mac)
        """
        try:
            # Method 1: PowerShell approach (most reliable)
            ip_addr, mac_addr = self._get_primary_network_powershell()
            
            if ip_addr != "Unknown" and mac_addr != "Unknown":
                return ip_addr, mac_addr
            
            # Method 2: Fallback to WMIC
            ip_addr, mac_addr = self._get_primary_network_wmic()
            
            if ip_addr != "Unknown" and mac_addr != "Unknown":
                return ip_addr, mac_addr
            
            # Method 3: Socket-based detection
            ip_addr = self._get_primary_ip_socket()
            
            return ip_addr, mac_addr
            
        except Exception:
            return "Unknown", "Unknown"
    
    def _get_primary_network_powershell(self) -> Tuple[str, str]:
        """Get primary network info using PowerShell."""
        try:
            # Get active network adapter with IP
            ip_cmd = (
                'powershell -Command "Get-NetIPConfiguration | '
                'Where-Object { $_.IPv4Address -and $_.NetAdapter.Status -eq \'Up\' } | '
                'Select-Object -First 1 -ExpandProperty IPv4Address | '
                'Select-Object -ExpandProperty IPAddress"'
            )
            
            return_code, stdout, stderr = run_command_with_timeout(ip_cmd, timeout=10)
            ip_addr = stdout.strip().split('\n')[0] if return_code == 0 and stdout.strip() else "Unknown"
            
            # Get MAC address of active adapter
            mac_cmd = (
                'powershell -Command "Get-NetAdapter | '
                'Where-Object { $_.Status -eq \'Up\' -and $_.Virtual -eq $false } | '
                'Select-Object -First 1 -ExpandProperty MacAddress"'
            )
            
            return_code, stdout, stderr = run_command_with_timeout(mac_cmd, timeout=10)
            mac_addr = stdout.strip() if return_code == 0 and stdout.strip() else "Unknown"
            
            return ip_addr, mac_addr
            
        except Exception:
            return "Unknown", "Unknown"
    
    def _get_primary_network_wmic(self) -> Tuple[str, str]:
        """Get primary network info using WMIC."""
        try:
            # Get IP address from active network adapter
            ip_addrs = query_wmic("wmic nicconfig where ipenabled=true get ipaddress")
            ip_addr = "Unknown"
            
            if ip_addrs:
                # Parse IP address array format
                for ip_line in ip_addrs:
                    if '{' in ip_line and '}' in ip_line:
                        # Extract first IP from array format {"192.168.1.100", "fe80::..."}
                        ip_part = ip_line.split('{')[1].split('}')[0]
                        if '"' in ip_part:
                            first_ip = ip_part.split('"')[1]
                            if self._is_valid_ipv4(first_ip):
                                ip_addr = first_ip
                                break
            
            # Get MAC address
            mac_addrs = query_wmic("wmic nicconfig where ipenabled=true get macaddress")
            mac_addr = mac_addrs[0] if mac_addrs and mac_addrs[0] != "Unknown" else "Unknown"
            
            return ip_addr, mac_addr
            
        except Exception:
            return "Unknown", "Unknown"
    
    def _get_primary_ip_socket(self) -> str:
        """Get primary IP using socket connection."""
        try:
            # Connect to external host to determine primary IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "Unknown"
    
    def _is_valid_ipv4(self, ip: str) -> bool:
        """Check if string is a valid IPv4 address."""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except Exception:
            return False
    
    def detect_network_adapters(self) -> List[NetworkAdapter]:
        """
        Detect all network adapters and their configurations.
        
        Returns:
            List[NetworkAdapter]: List of network adapters
        """
        adapters = []
        
        try:
            # Use PowerShell to get comprehensive adapter information
            adapters.extend(self._get_adapters_powershell())
            
            # Fallback to WMIC if PowerShell fails
            if not adapters:
                adapters.extend(self._get_adapters_wmic())
                
        except Exception:
            pass
        
        return adapters
    
    def _get_adapters_powershell(self) -> List[NetworkAdapter]:
        """Get network adapters using PowerShell."""
        adapters = []
        
        try:
            cmd = (
                'powershell -Command "'
                'Get-NetAdapter | Where-Object { $_.Virtual -eq $false } | '
                'ForEach-Object {'
                '    $adapter = $_; '
                '    $config = Get-NetIPConfiguration -InterfaceAlias $adapter.Name -ErrorAction SilentlyContinue; '
                '    if ($config) {'
                '        Write-Output \\"$($adapter.Name)|$($adapter.InterfaceDescription)|$($adapter.MacAddress)|$($config.IPv4Address.IPAddress)|$($config.IPv4Address.PrefixLength)|$($config.IPv4DefaultGateway.NextHop)|$($adapter.LinkSpeed)|$($adapter.Status)\\";'
                '    } else {'
                '        Write-Output \\"$($adapter.Name)|$($adapter.InterfaceDescription)|$($adapter.MacAddress)||||$($adapter.LinkSpeed)|$($adapter.Status)\\";'
                '    }'
                '}"'
            )
            
            return_code, stdout, stderr = run_command_with_timeout(cmd, timeout=20)
            
            if return_code == 0:
                for line in stdout.splitlines():
                    line = line.strip()
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 8:
                            name = parts[0]
                            description = parts[1]
                            mac_address = parts[2]
                            ip_address = parts[3]
                            prefix_length = parts[4]
                            gateway = parts[5]
                            speed = parts[6]
                            status = parts[7]
                            
                            # Format speed
                            if speed and speed.isdigit():
                                speed_mbps = int(speed) // 1000000
                                speed = f"{speed_mbps} Mbps" if speed_mbps > 0 else speed
                            
                            # Create subnet mask from prefix length
                            subnet_mask = self._prefix_to_subnet_mask(prefix_length) if prefix_length else ""
                            
                            adapter = NetworkAdapter(
                                name=name,
                                description=description,
                                mac_address=mac_address,
                                ip_addresses=[ip_address] if ip_address else [],
                                subnet_mask=subnet_mask,
                                default_gateway=gateway,
                                speed=speed,
                                status=status
                            )
                            
                            adapters.append(adapter)
        
        except Exception:
            pass
        
        return adapters
    
    def _get_adapters_wmic(self) -> List[NetworkAdapter]:
        """Get network adapters using WMIC."""
        adapters = []
        
        try:
            # Get physical adapters
            adapter_info = query_wmic("wmic path win32_networkadapter where physicaladapter=true get name,macaddress,speed,netconnectionstatus")
            
            for i, adapter_line in enumerate(adapter_info):
                if adapter_line and adapter_line != "Unknown":
                    # This is a simplified parsing - WMIC output can be complex
                    adapter = NetworkAdapter(
                        name=f"Network Adapter {i+1}",
                        description=adapter_line,
                        mac_address="",  # Would need additional WMIC calls
                        status="Unknown"
                    )
                    adapters.append(adapter)
        
        except Exception:
            pass
        
        return adapters
    
    def _prefix_to_subnet_mask(self, prefix_length: str) -> str:
        """Convert prefix length to subnet mask."""
        try:
            if prefix_length and prefix_length.isdigit():
                prefix = int(prefix_length)
                if 0 <= prefix <= 32:
                    # Create subnet mask from prefix length
                    mask = (0xffffffff >> (32 - prefix)) << (32 - prefix)
                    return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"
        except Exception:
            pass
        return ""
    
    def detect_connectivity(self) -> Tuple[bool, str]:
        """
        Test internet connectivity and get public IP.
        
        Returns:
            Tuple[bool, str]: (has_internet, public_ip)
        """
        # Test connectivity
        has_internet = self._test_internet_connectivity()
        
        # Get public IP if connected
        public_ip = ""
        if has_internet:
            public_ip = self._get_public_ip()
        
        return has_internet, public_ip
    
    def _test_internet_connectivity(self) -> bool:
        """Test internet connectivity."""
        test_hosts = [
            "8.8.8.8",        # Google DNS
            "1.1.1.1",        # Cloudflare DNS
            "208.67.222.222"  # OpenDNS
        ]
        
        for host in test_hosts:
            try:
                return_code, stdout, stderr = run_command_with_timeout(
                    f"ping {host} -n 1 -w 3000",
                    timeout=5
                )
                
                if return_code == 0:
                    return True
            except Exception:
                continue
        
        return False
    
    def _get_public_ip(self) -> str:
        """Get public IP address."""
        services = [
            "https://api.ipify.org",
            "https://icanhazip.com",
            "https://ipecho.net/plain"
        ]
        
        for service in services:
            try:
                cmd = f'powershell -Command "Invoke-RestMethod -Uri {service} -TimeoutSec 5"'
                return_code, stdout, stderr = run_command_with_timeout(cmd, timeout=10)
                
                if return_code == 0:
                    public_ip = stdout.strip()
                    if self._is_valid_ipv4(public_ip):
                        return public_ip
            except Exception:
                continue
        
        return ""
    
    def detect_domain_info(self) -> Tuple[str, str]:
        """
        Detect domain or workgroup information.
        
        Returns:
            Tuple[str, str]: (computer_name, domain_workgroup)
        """
        try:
            # Get computer name
            computer_name = query_wmic("wmic computersystem get name")
            computer_name = computer_name[0] if computer_name else "Unknown"
            
            # Get domain or workgroup
            domain_info = query_wmic("wmic computersystem get domain")
            domain = domain_info[0] if domain_info else "Unknown"
            
            # Check if it's a domain or workgroup
            part_of_domain = query_wmic("wmic computersystem get partofdomain")
            is_domain = part_of_domain and part_of_domain[0].lower() == "true"
            
            if is_domain:
                domain_workgroup = f"Domain: {domain}"
            else:
                domain_workgroup = f"Workgroup: {domain}"
            
            return computer_name, domain_workgroup
            
        except Exception:
            return "Unknown", "Unknown"
    
    def detect_dns_servers(self) -> List[str]:
        """
        Detect configured DNS servers.
        
        Returns:
            List[str]: List of DNS server addresses
        """
        dns_servers = []
        
        try:
            cmd = (
                'powershell -Command "'
                'Get-DnsClientServerAddress | '
                'Where-Object { $_.AddressFamily -eq 2 -and $_.ServerAddresses } | '
                'Select-Object -ExpandProperty ServerAddresses | '
                'Sort-Object -Unique"'
            )
            
            return_code, stdout, stderr = run_command_with_timeout(cmd, timeout=10)
            
            if return_code == 0:
                for line in stdout.splitlines():
                    ip = line.strip()
                    if self._is_valid_ipv4(ip):
                        dns_servers.append(ip)
        
        except Exception:
            # Fallback: try to get from network configuration
            try:
                dns_info = query_wmic("wmic nicconfig where ipenabled=true get dnsserversearchorder")
                if dns_info:
                    for dns_line in dns_info:
                        if '{' in dns_line and '}' in dns_line:
                            # Parse DNS array format
                            dns_part = dns_line.split('{')[1].split('}')[0]
                            if '"' in dns_part:
                                for dns_ip in dns_part.split(','):
                                    dns_ip = dns_ip.strip().strip('"')
                                    if self._is_valid_ipv4(dns_ip):
                                        dns_servers.append(dns_ip)
            except Exception:
                pass
        
        return dns_servers
    
    def get_comprehensive_network_info(self) -> NetworkInfo:
        """
        Get comprehensive network information.
        
        Returns:
            NetworkInfo: Complete network information
        """
        # Get primary network info
        primary_ip, primary_mac = self.detect_primary_network_info()
        
        # Get domain info
        computer_name, domain_workgroup = self.detect_domain_info()
        
        # Get connectivity info
        has_internet, public_ip = self.detect_connectivity()
        
        # Get all adapters
        adapters = self.detect_network_adapters()
        
        return NetworkInfo(
            primary_ip=primary_ip,
            primary_mac=primary_mac,
            computer_name=computer_name,
            domain_workgroup=domain_workgroup,
            adapters=adapters,
            internet_connectivity=has_internet,
            public_ip=public_ip
        )
    
    def format_network_summary(self, network_info: NetworkInfo) -> Dict[str, str]:
        """
        Format network information for display.
        
        Args:
            network_info: Network information to format
        
        Returns:
            Dict[str, str]: Formatted network information
        """
        return {
            "IP Address": network_info.primary_ip,
            "MAC Address": network_info.primary_mac,
            "Computer Name": network_info.computer_name,
            "Domain/Workgroup": network_info.domain_workgroup,
            "Internet Connection": "Yes" if network_info.internet_connectivity else "No",
            "Public IP": network_info.public_ip if network_info.public_ip else "N/A",
            "Active Adapters": str(len([a for a in network_info.adapters if a.status.lower() == "up"]))
        }