"""
Package searching functionality.

This module handles searching for Chocolatey packages, parsing results,
and providing search filtering and sorting capabilities.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from core import BaseWorker, run_command_with_timeout, PACKAGE_SEARCH_LIMIT
from .chocolatey_manager import ChocolateyManager


class SearchSort(Enum):
    """Package search sorting options."""
    RELEVANCE = "relevance"
    NAME = "name"
    DOWNLOADS = "downloads"
    UPDATED = "updated"


@dataclass
class PackageInfo:
    """Information about a Chocolatey package."""
    name: str
    version: str
    description: str
    summary: str = ""
    authors: str = ""
    downloads: int = 0
    tags: List[str] = None
    is_approved: bool = False
    is_trusted: bool = False
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class PackageSearcher:
    """
    Handles package searching operations.
    
    This class provides methods for searching Chocolatey packages with various
    filtering and sorting options.
    """
    
    def __init__(self):
        self.chocolatey_manager = ChocolateyManager()
    
    def search_packages(
        self,
        query: str,
        exact_match: bool = False,
        limit: int = PACKAGE_SEARCH_LIMIT,
        include_prereleases: bool = False,
        approved_only: bool = False
    ) -> Tuple[bool, List[PackageInfo], str]:
        """
        Search for packages using Chocolatey.
        
        Args:
            query: Search query string
            exact_match: Whether to search for exact name matches only
            limit: Maximum number of results to return
            include_prereleases: Whether to include prerelease packages
            approved_only: Whether to return only approved packages
        
        Returns:
            Tuple[bool, List[PackageInfo], str]: (success, packages, error_message)
        """
        if not self.chocolatey_manager.is_chocolatey_installed():
            return False, [], "Chocolatey is not installed"
        
        if not query.strip():
            return False, [], "Search query cannot be empty"
        
        try:
            # Build search command
            cmd_parts = ["choco", "search", f'"{query}"']
            
            if exact_match:
                cmd_parts.append("--exact")
            
            if include_prereleases:
                cmd_parts.append("--prerelease")
            
            if approved_only:
                cmd_parts.append("--approved-only")
            
            cmd_parts.extend(["--limit-output", f"--page-size={limit}"])
            
            cmd = " ".join(cmd_parts)
            
            return_code, stdout, stderr = run_command_with_timeout(
                cmd, timeout=60
            )
            
            if return_code != 0:
                # Try alternative search method
                return self._fallback_search(query, exact_match, limit)
            
            # Parse results
            packages = self._parse_search_results(stdout, query, exact_match, limit)
            
            return True, packages, ""
            
        except Exception as e:
            return False, [], f"Search error: {str(e)}"
    
    def _fallback_search(
        self, 
        query: str, 
        exact_match: bool, 
        limit: int
    ) -> Tuple[bool, List[PackageInfo], str]:
        """
        Fallback search method using choco list.
        
        Args:
            query: Search query
            exact_match: Whether to use exact matching
            limit: Result limit
        
        Returns:
            Tuple[bool, List[PackageInfo], str]: (success, packages, error_message)
        """
        try:
            cmd = f'choco list "{query}" --limit-output'
            
            return_code, stdout, stderr = run_command_with_timeout(
                cmd, timeout=60
            )
            
            if return_code == 0:
                packages = self._parse_search_results(stdout, query, exact_match, limit)
                return True, packages, ""
            else:
                return False, [], f"Fallback search failed: {stderr}"
                
        except Exception as e:
            return False, [], f"Fallback search error: {str(e)}"
    
    def _parse_search_results(
        self, 
        output: str, 
        query: str, 
        exact_match: bool, 
        limit: int
    ) -> List[PackageInfo]:
        """
        Parse Chocolatey search output into PackageInfo objects.
        
        Args:
            output: Raw search output
            query: Original search query
            exact_match: Whether exact matching was requested
            limit: Maximum number of results
        
        Returns:
            List[PackageInfo]: Parsed package information
        """
        packages = []
        query_lower = query.lower()
        
        for line in output.splitlines():
            if not line.strip():
                continue
                
            parts = line.split('|')
            if len(parts) < 2:
                continue
            
            package_name = parts[0].strip()
            version = parts[1].strip()
            description = parts[2].strip() if len(parts) > 2 else "No description available"
            
            # Apply filtering
            package_name_lower = package_name.lower()
            
            if exact_match:
                if package_name_lower != query_lower:
                    continue
            else:
                # Check if query matches package name or description
                if (query_lower not in package_name_lower and 
                    query_lower not in description.lower()):
                    continue
            
            # Create package info
            package_info = PackageInfo(
                name=package_name,
                version=version,
                description=description,
                summary=description[:100] + "..." if len(description) > 100 else description
            )
            
            packages.append(package_info)
            
            # Respect limit
            if len(packages) >= limit:
                break
        
        return packages
    
    def get_package_details(self, package_name: str) -> Tuple[bool, Optional[PackageInfo], str]:
        """
        Get detailed information about a specific package.
        
        Args:
            package_name: Name of the package
        
        Returns:
            Tuple[bool, Optional[PackageInfo], str]: (success, package_info, error_message)
        """
        try:
            cmd = f'choco info "{package_name}" --limit-output'
            
            return_code, stdout, stderr = run_command_with_timeout(
                cmd, timeout=30
            )
            
            if return_code == 0 and stdout.strip():
                # Parse the info output
                lines = stdout.strip().split('\n')
                if lines:
                    parts = lines[0].split('|')
                    if len(parts) >= 2:
                        package_info = PackageInfo(
                            name=parts[0].strip(),
                            version=parts[1].strip(),
                            description=parts[2].strip() if len(parts) > 2 else "No description available"
                        )
                        return True, package_info, ""
            
            return False, None, f"Package '{package_name}' not found"
            
        except Exception as e:
            return False, None, f"Error getting package details: {str(e)}"
    
    def validate_package_name(self, package_name: str) -> Tuple[bool, str]:
        """
        Validate a package name format.
        
        Args:
            package_name: Package name to validate
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not package_name or not package_name.strip():
            return False, "Package name cannot be empty"
        
        # Basic validation - package names should be alphanumeric with dots, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9._-]+$', package_name.strip()):
            return False, "Package name contains invalid characters"
        
        if len(package_name) > 100:
            return False, "Package name too long (max 100 characters)"
        
        return True, ""
    
    def filter_packages(
        self, 
        packages: List[PackageInfo], 
        filters: Dict[str, any]
    ) -> List[PackageInfo]:
        """
        Apply filters to a list of packages.
        
        Args:
            packages: List of packages to filter
            filters: Filter criteria dictionary
        
        Returns:
            List[PackageInfo]: Filtered packages
        """
        filtered = packages.copy()
        
        # Filter by name pattern
        if 'name_pattern' in filters:
            pattern = filters['name_pattern'].lower()
            filtered = [p for p in filtered if pattern in p.name.lower()]
        
        # Filter by description keywords
        if 'description_keywords' in filters:
            keywords = [kw.lower() for kw in filters['description_keywords']]
            filtered = [
                p for p in filtered 
                if any(kw in p.description.lower() for kw in keywords)
            ]
        
        # Filter by approval status
        if filters.get('approved_only', False):
            filtered = [p for p in filtered if p.is_approved]
        
        return filtered
    
    def sort_packages(
        self, 
        packages: List[PackageInfo], 
        sort_by: SearchSort = SearchSort.RELEVANCE,
        reverse: bool = False
    ) -> List[PackageInfo]:
        """
        Sort packages by specified criteria.
        
        Args:
            packages: List of packages to sort
            sort_by: Sorting criteria
            reverse: Whether to reverse the sort order
        
        Returns:
            List[PackageInfo]: Sorted packages
        """
        if sort_by == SearchSort.NAME:
            return sorted(packages, key=lambda p: p.name.lower(), reverse=reverse)
        elif sort_by == SearchSort.DOWNLOADS:
            return sorted(packages, key=lambda p: p.downloads, reverse=not reverse)
        else:  # RELEVANCE or default
            return packages  # Keep original order for relevance


class PackageSearchWorker(BaseWorker):
    """
    Worker class for searching packages in the background.
    
    This worker handles package searching without blocking the UI,
    providing progress updates and results.
    """
    
    def __init__(
        self, 
        query: str, 
        search_options: Dict[str, any] = None
    ):
        super().__init__()
        self.query = query
        self.search_options = search_options or {}
        self.searcher = PackageSearcher()
    
    def run(self):
        """Search for packages without blocking UI."""
        try:
            self.signals.emit_progress(f"Searching for packages containing '{self.query}'...")
            
            # Check prerequisites
            if not self.searcher.chocolatey_manager.is_chocolatey_installed():
                self.signals.emit_error("Chocolatey is not installed")
                return
            
            # Extract search options
            exact_match = self.search_options.get('exact_match', False)
            limit = self.search_options.get('limit', PACKAGE_SEARCH_LIMIT)
            include_prereleases = self.search_options.get('include_prereleases', False)
            approved_only = self.search_options.get('approved_only', False)
            
            # Perform search
            success, packages, error_message = self.searcher.search_packages(
                query=self.query,
                exact_match=exact_match,
                limit=limit,
                include_prereleases=include_prereleases,
                approved_only=approved_only
            )
            
            if success:
                # Apply additional filters if specified
                if 'filters' in self.search_options:
                    packages = self.searcher.filter_packages(
                        packages, 
                        self.search_options['filters']
                    )
                
                # Sort results if specified
                if 'sort_by' in self.search_options:
                    sort_by = self.search_options['sort_by']
                    reverse = self.search_options.get('sort_reverse', False)
                    packages = self.searcher.sort_packages(packages, sort_by, reverse)
                
                self.signals.emit_progress(f"Found {len(packages)} packages matching '{self.query}'")
                
                if len(packages) == 0:
                    self.signals.emit_progress("No packages found. Try a different search term or adjust filters.")
                elif len(packages) >= limit:
                    self.signals.emit_progress(f"Showing first {limit} results. Use more specific search terms for better results.")
                
                self.signals.emit_result(packages)
            else:
                self.signals.emit_error(f"Search failed: {error_message}")
                
        except Exception as e:
            self.signals.emit_error(f"Search error: {str(e)}")
    
    def get_search_summary(self) -> Dict[str, any]:
        """
        Get summary information about the search operation.
        
        Returns:
            Dict: Search operation summary
        """
        return {
            'query': self.query,
            'options': self.search_options,
            'chocolatey_available': self.searcher.chocolatey_manager.is_chocolatey_installed()
        }