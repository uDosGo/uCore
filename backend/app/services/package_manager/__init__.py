"""Package Manager Service

Module-aware package management for uCore:
- Track installed modules and their dependencies
- Manage package versions and updates
- Handle module lifecycle (install, update, remove)
- Dependency resolution
- Package integrity verification

Usage:
    from app.services.package_manager import PackageManager
    pm = PackageManager()
    
    # List installed packages
    packages = pm.list_packages()
    
    # Install a package
    pm.install_package("catalog")
    
    # Update a package
    pm.update_package("catalog")
    
    # Remove a package
    pm.remove_package("catalog")
"""

from .models import DependencyInfo, PackageInfo, PackageStatus
from .package_manager import PackageManager

__all__ = ["PackageManager", "PackageInfo", "PackageStatus", "DependencyInfo"]
