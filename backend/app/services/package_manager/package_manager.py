"""Package Manager Implementation

Module-aware package management for uCore.
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .models import DependencyInfo, PackageInfo, PackageOperationResult, PackageStatus

log = logging.getLogger("package_manager")


class PackageManager:
    """Manage uCore packages and modules"""

    def __init__(self, packages_dir: Optional[Path] = None):
        """Initialize package manager

        Args:
            packages_dir: Directory to store package metadata (default: backend/packages)
        """
        self.packages_dir = packages_dir or Path(__file__).parent.parent.parent / "packages"
        self.packages_dir.mkdir(parents=True, exist_ok=True)

        # Load installed packages
        self.installed_packages: Dict[str, PackageInfo] = {}
        self._load_installed_packages()

    def _load_installed_packages(self):
        """Load installed packages from disk"""
        metadata_file = self.packages_dir / "installed.json"

        if not metadata_file.exists():
            log.info("No installed packages found")
            return

        try:
            with open(metadata_file, "r") as f:
                data = json.load(f)

            for name, pkg_data in data.items():
                self.installed_packages[name] = PackageInfo(
                    name=pkg_data["name"],
                    version=pkg_data["version"],
                    status=PackageStatus(pkg_data["status"]),
                    description=pkg_data.get("description", ""),
                    author=pkg_data.get("author", ""),
                    dependencies=[
                        DependencyInfo(**d) for d in pkg_data.get("dependencies", [])
                    ],
                    installed_path=pkg_data.get("installed_path"),
                    last_updated=datetime.fromisoformat(pkg_data["last_updated"])
                    if pkg_data.get("last_updated") else None,
                    metadata=pkg_data.get("metadata", {}),
                    size_bytes=pkg_data.get("size_bytes", 0),
                    checksum=pkg_data.get("checksum"),
                )

            log.info(f"Loaded {len(self.installed_packages)} installed packages")
        except Exception as e:
            log.error(f"Failed to load installed packages: {e}")

    def _save_installed_packages(self):
        """Save installed packages to disk"""
        metadata_file = self.packages_dir / "installed.json"

        try:
            data = {
                name: pkg.to_dict()
                for name, pkg in self.installed_packages.items()
            }

            with open(metadata_file, "w") as f:
                json.dump(data, f, indent=2)

            log.info(f"Saved {len(self.installed_packages)} packages")
        except Exception as e:
            log.error(f"Failed to save installed packages: {e}")

    def _calculate_checksum(self, path: Path) -> str:
        """Calculate SHA256 checksum of a file"""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def list_packages(self) -> List[PackageInfo]:
        """List all installed packages"""
        return list(self.installed_packages.values())

    def get_package(self, name: str) -> Optional[PackageInfo]:
        """Get package information"""
        return self.installed_packages.get(name)

    def install_package(
        self,
        name: str,
        version: Optional[str] = None,
        force: bool = False,
    ) -> PackageOperationResult:
        """Install a package

        Args:
            name: Package name
            version: Specific version to install (default: latest)
            force: Force reinstallation

        Returns:
            PackageOperationResult with installation status
        """
        start_time = datetime.utcnow()

        try:
            # Check if package already exists
            if name in self.installed_packages and not force:
                existing = self.installed_packages[name]
                if existing.status == PackageStatus.INSTALLED:
                    return PackageOperationResult(
                        success=False,
                        package_name=name,
                        message=f"Package {name} is already installed (version {existing.version})",
                    )

            # TODO: Implement actual package installation
            # This would involve:
            # 1. Fetching package from registry
            # 2. Downloading package files
            # 3. Extracting to installed_path
            # 4. Verifying checksum
            # 5. Installing dependencies
            # 6. Updating metadata

            # For now, simulate installation
            package_info = PackageInfo(
                name=name,
                version=version or "1.0.0",
                status=PackageStatus.INSTALLED,
                description=f"Package {name}",
                installed_path=f"/path/to/{name}",
                last_updated=datetime.utcnow(),
            )

            self.installed_packages[name] = package_info
            self._save_installed_packages()

            duration = (datetime.utcnow() - start_time).total_seconds()

            return PackageOperationResult(
                success=True,
                package_name=name,
                message=f"Package {name} installed successfully",
                package_info=package_info,
                duration_seconds=duration,
            )

        except Exception as e:
            log.error(f"Failed to install package {name}: {e}")
            duration = (datetime.utcnow() - start_time).total_seconds()

            return PackageOperationResult(
                success=False,
                package_name=name,
                message=f"Failed to install package {name}: {str(e)}",
                duration_seconds=duration,
            )

    def update_package(
        self,
        name: str,
        force: bool = False,
    ) -> PackageOperationResult:
        """Update a package

        Args:
            name: Package name
            force: Force update even if already latest

        Returns:
            PackageOperationResult with update status
        """
        start_time = datetime.utcnow()

        try:
            package = self.installed_packages.get(name)

            if not package:
                return PackageOperationResult(
                    success=False,
                    package_name=name,
                    message=f"Package {name} is not installed",
                )

            if package.status == PackageStatus.REMOVED:
                return PackageOperationResult(
                    success=False,
                    package_name=name,
                    message=f"Package {name} has been removed",
                )

            # TODO: Implement actual package update
            # This would involve:
            # 1. Fetching latest version from registry
            # 2. Downloading updated files
            # 3. Backing up current version
            # 4. Replacing files
            # 5. Verifying checksum
            # 6. Updating version metadata

            # For now, simulate update
            package.version = "2.0.0"
            package.status = PackageStatus.UPDATED
            package.last_updated = datetime.utcnow()

            self._save_installed_packages()

            duration = (datetime.utcnow() - start_time).total_seconds()

            return PackageOperationResult(
                success=True,
                package_name=name,
                message=f"Package {name} updated to version {package.version}",
                package_info=package,
                duration_seconds=duration,
            )

        except Exception as e:
            log.error(f"Failed to update package {name}: {e}")
            duration = (datetime.utcnow() - start_time).total_seconds()

            return PackageOperationResult(
                success=False,
                package_name=name,
                message=f"Failed to update package {name}: {str(e)}",
                duration_seconds=duration,
            )

    def remove_package(
        self,
        name: str,
        force: bool = False,
    ) -> PackageOperationResult:
        """Remove a package

        Args:
            name: Package name
            force: Force removal even if dependencies exist

        Returns:
            PackageOperationResult with removal status
        """
        start_time = datetime.utcnow()

        try:
            package = self.installed_packages.get(name)

            if not package:
                return PackageOperationResult(
                    success=False,
                    package_name=name,
                    message=f"Package {name} is not installed",
                )

            # TODO: Implement actual package removal
            # This would involve:
            # 1. Removing installed files
            # 2. Uninstalling dependencies
            # 3. Cleaning up metadata
            # 4. Updating status

            # For now, simulate removal
            package.status = PackageStatus.REMOVED
            package.installed_path = None

            del self.installed_packages[name]
            self._save_installed_packages()

            duration = (datetime.utcnow() - start_time).total_seconds()

            return PackageOperationResult(
                success=True,
                package_name=name,
                message=f"Package {name} removed successfully",
                duration_seconds=duration,
            )

        except Exception as e:
            log.error(f"Failed to remove package {name}: {e}")
            duration = (datetime.utcnow() - start_time).total_seconds()

            return PackageOperationResult(
                success=False,
                package_name=name,
                message=f"Failed to remove package {name}: {str(e)}",
                duration_seconds=duration,
            )

    def check_integrity(self, name: str) -> bool:
        """Check package integrity

        Args:
            name: Package name

        Returns:
            True if package is intact, False otherwise
        """
        package = self.installed_packages.get(name)

        if not package or not package.installed_path:
            return False

        # TODO: Implement actual integrity check
        # This would involve:
        # 1. Verifying checksum
        # 2. Checking file existence
        # 3. Verifying permissions
        # 4. Checking dependencies

        return True

    def get_package_dependencies(self, name: str) -> List[DependencyInfo]:
        """Get package dependencies

        Args:
            name: Package name

        Returns:
            List of dependency information
        """
        package = self.installed_packages.get(name)
        return package.dependencies if package else []

    def get_all_dependencies(self) -> Dict[str, List[DependencyInfo]]:
        """Get all package dependencies

        Returns:
            Dictionary mapping package names to their dependencies
        """
        return {
            name: pkg.dependencies
            for name, pkg in self.installed_packages.items()
        }
