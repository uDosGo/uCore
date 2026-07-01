"""Package Manager — Wired to the plate system for install/update/repair.

Connects DistributionSystem to the plate refresh system so that:
- Installing a package creates/updates a plate definition
- Updating a package refreshes the plate
- Repairing a package re-renders the plate
- Removing a package triggers the destroy workflow
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from plate_refresh.models import PlateMeta
from plate_refresh.refresh import discover_plates, load_plate, render_plates
from plate_refresh.verification import verify_plate

from .distribution_system import DistributionSystem
from .models import (
    DistributionOperationResult,
    ModuleInfo,
    ModuleStatus,
)

log = logging.getLogger("ucore.package_manager")

ROOT = Path(__file__).resolve().parents[4]
PLATES_ROOT = ROOT / "plates"


class PackageManager:
    """Package manager wired to the plate system.

    Provides install/update/repair/remove operations that sync
    between the distribution system and the plate refresh system.
    """

    def __init__(self):
        self.dist = DistributionSystem()

    # ─── Plate Integration ────────────────────────────────

    def _find_plate_for_package(self, package_name: str) -> str | None:
        """Find a plate ID that corresponds to a package name.

        Searches by:
        1. Exact plate ID match
        2. Plate ID suffix match (e.g., 'vault.user_vault_seed' matches 'user_vault_seed')
        3. Description match
        """
        plates = discover_plates()

        # Exact match
        if package_name in plates:
            return package_name

        # Suffix match
        for pid in plates:
            if pid.endswith(package_name) or pid.endswith(f".{package_name}"):
                return pid

        # Description match
        for pid in plates:
            loaded = load_plate(pid)
            if loaded:
                meta, _, _ = loaded
                if package_name.lower() in meta.description.lower():
                    return pid

        return None

    def _create_plate_from_package(
        self,
        package_name: str,
        module: ModuleInfo,
    ) -> str:
        """Create a plate definition from an installed package.

        Args:
            package_name: Name of the package
            module: Module info from distribution system

        Returns:
            The plate ID that was created
        """
        domain = "skill"
        plate_id = f"{domain}.{package_name}"

        # Determine target path
        target_dir = PLATES_ROOT / domain
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{package_name}.yaml"

        # Build plate data
        plate_data = {
            "plate": {
                "id": plate_id,
                "version": module.version,
                "domain": domain,
                "description": module.description or f"Package: {package_name}",
                "source": "user",
                "checksum": "",
                "dependencies": module.dependencies,
                "lessons": [],
                "destroy": {
                    "salvage_keys": ["package_name", "version"],
                    "rebuild_command": (
                        f"python -m app.services.distribution_system "
                        f"--install {package_name}"
                    ),
                    "backup_before_destroy": True,
                    "spool_archive": {
                        "enabled": True,
                        "spool_dir": "~/.ucore/logs",
                        "compress_metadata": True,
                        "include_source": False,
                        "include_lessons": True,
                        "max_spool_age_days": 365,
                    },
                },
            }
        }

        # Write plate
        with open(target_path, "w") as f:
            import yaml
            yaml.dump(plate_data, f, default_flow_style=False)

        log.info("Created plate %s from package %s", plate_id, package_name)
        return plate_id

    # ─── Core Operations ──────────────────────────────────

    def install(
        self,
        package_name: str,
        version: str | None = None,
        force: bool = False,
    ) -> DistributionOperationResult:
        """Install a package and create/update its plate.

        Args:
            package_name: Name of the package to install
            version: Specific version to install
            force: Force reinstallation

        Returns:
            DistributionOperationResult with installation status
        """
        # Install via distribution system
        result = self.dist.install_module(
            name=package_name,
            version=version,
            force=force,
        )

        if not result.success:
            return result

        # Create or update plate for the package
        if result.module_info:
            plate_id = self._create_plate_from_package(
                package_name=package_name,
                module=result.module_info,
            )

            # Verify the new plate
            try:
                verify_result = verify_plate(plate_id)
                if not verify_result.passed:
                    log.warning(
                        "Plate %s created but verification had warnings: %s",
                        plate_id,
                        verify_result.warnings,
                    )
            except Exception as e:
                log.warning("Could not verify plate %s: %s", plate_id, e)

        return result

    def update(
        self,
        package_name: str,
        force: bool = False,
    ) -> DistributionOperationResult:
        """Update a package and refresh its plate.

        Args:
            package_name: Name of the package to update
            force: Force update

        Returns:
            DistributionOperationResult with update status
        """
        # Update via distribution system
        result = self.dist.update_module(
            name=package_name,
            force=force,
        )

        if not result.success:
            return result

        # Refresh the plate
        plate_id = self._find_plate_for_package(package_name)
        if plate_id:
            try:
                render_plates()
                log.info("Re-rendered plates after updating %s", package_name)
            except Exception as e:
                log.warning("Could not re-render plates: %s", e)

        return result

    def repair(
        self,
        package_name: str,
    ) -> DistributionOperationResult:
        """Repair a package by re-installing and re-rendering its plate.

        Args:
            package_name: Name of the package to repair

        Returns:
            DistributionOperationResult with repair status
        """
        # Repair via distribution system
        result = self.dist.repair_module(name=package_name)

        if not result.success:
            return result

        # Re-render the plate
        plate_id = self._find_plate_for_package(package_name)
        if plate_id:
            try:
                render_plates()
                log.info("Re-rendered plates after repairing %s", package_name)
            except Exception as e:
                log.warning("Could not re-render plates: %s", e)

        return result

    def remove(
        self,
        package_name: str,
        force: bool = False,
    ) -> DistributionOperationResult:
        """Remove a package and optionally its plate.

        Args:
            package_name: Name of the package to remove
            force: Force removal

        Returns:
            DistributionOperationResult with removal status
        """
        # Remove via distribution system
        result = self.dist.remove_module(
            name=package_name,
            force=force,
        )

        if not result.success:
            return result

        # Optionally remove the plate
        plate_id = self._find_plate_for_package(package_name)
        if plate_id:
            loaded = load_plate(plate_id)
            if loaded:
                _, _, path = loaded
                try:
                    path.unlink(missing_ok=True)
                    log.info("Removed plate %s (%s)", plate_id, path)
                except Exception as e:
                    log.warning("Could not remove plate %s: %s", plate_id, e)

        return result

    def list_packages(self) -> list[dict[str, Any]]:
        """List all installed packages with their plate status.

        Returns:
            List of package info dicts with plate status
        """
        modules = self.dist.list_modules()
        plates = discover_plates()

        results = []
        for module in modules:
            plate_id = self._find_plate_for_package(module.name)
            plate_status = "found" if plate_id else "not_found"

            results.append({
                "name": module.name,
                "version": module.version,
                "status": module.status.value,
                "health_status": module.health_status,
                "plate_id": plate_id,
                "plate_status": plate_status,
                "size_bytes": module.size_bytes,
                "installed_path": module.installed_path,
                "last_updated": (
                    module.last_updated.isoformat() if module.last_updated else None
                ),
            })

        return results

    def get_package_info(self, package_name: str) -> dict[str, Any] | None:
        """Get detailed info about a package including its plate.

        Args:
            package_name: Name of the package

        Returns:
            Package info dict or None if not found
        """
        module = self.dist.get_module(package_name)
        if not module:
            return None

        plate_id = self._find_plate_for_package(package_name)
        plate_info = None
        if plate_id:
            loaded = load_plate(plate_id)
            if loaded:
                meta, _, path = loaded
                plate_info = {
                    "id": meta.id,
                    "version": meta.version,
                    "domain": meta.domain,
                    "description": meta.description,
                    "path": str(path),
                }

        return {
            "name": module.name,
            "version": module.version,
            "status": module.status.value,
            "description": module.description,
            "health_status": module.health_status,
            "size_bytes": module.size_bytes,
            "installed_path": module.installed_path,
            "last_updated": (
                module.last_updated.isoformat() if module.last_updated else None
            ),
            "plate": plate_info,
            "dependencies": module.dependencies,
            "metadata": module.metadata,
        }

    def health_check(self) -> dict[str, Any]:
        """Run a health check on all packages and their plates.

        Returns:
            Health report dict
        """
        packages = self.list_packages()
        plates = discover_plates()

        issues = []
        recommendations = []

        for pkg in packages:
            if pkg["health_status"] == "unhealthy":
                issues.append(f"Package {pkg['name']} is unhealthy")
                recommendations.append(
                    f"Run: repair {pkg['name']}"
                )

            if pkg["plate_status"] == "not_found":
                issues.append(f"Package {pkg['name']} has no plate definition")
                recommendations.append(
                    f"Run: install {pkg['name']} to create plate"
                )

        # Check for orphaned plates (plates without packages)
        for pid in plates:
            has_package = any(
                pkg.get("plate_id") == pid for pkg in packages
            )
            if not has_package:
                issues.append(f"Orphaned plate: {pid} (no corresponding package)")

        return {
            "total_packages": len(packages),
            "total_plates": len(plates),
            "healthy_packages": sum(
                1 for p in packages if p["health_status"] == "healthy"
            ),
            "unhealthy_packages": sum(
                1 for p in packages if p["health_status"] == "unhealthy"
            ),
            "packages_with_plates": sum(
                1 for p in packages if p["plate_status"] == "found"
            ),
            "packages_without_plates": sum(
                1 for p in packages if p["plate_status"] == "not_found"
            ),
            "issues": issues,
            "recommendations": recommendations,
        }
