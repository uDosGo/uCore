"""Distribution System Implementation

Handles packaging, distribution, and lifecycle management.
Wired to GitHub pulls via vendor/sources.yaml definitions.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Dict, Optional

import yaml

from .models import ModuleInfo, ModuleStatus, DistributionOperationResult, SystemHealthReport

log = logging.getLogger("distribution_system")

ROOT = Path(__file__).resolve().parents[4]  # /Users/fredbook/Code/uCore
VENDOR_DIR = ROOT / "vendor"
SOURCES_FILE = VENDOR_DIR / "sources.yaml"
DIST_DIR = VENDOR_DIR / "dist"


class DistributionSystem:
    """Manage uCore distribution and lifecycle with GitHub pull support."""

    def __init__(self, modules_dir: Optional[Path] = None):
        """Initialize distribution system

        Args:
            modules_dir: Directory to store modules (default: backend/modules)
        """
        self.modules_dir = modules_dir or Path(__file__).parent.parent.parent / "modules"
        self.modules_dir.mkdir(parents=True, exist_ok=True)

        # Load source definitions
        self.sources: dict[str, dict[str, Any]] = {}
        self._load_sources()

        # Load installed modules
        self.installed_modules: Dict[str, ModuleInfo] = {}
        self._load_installed_modules()

    def _load_sources(self) -> None:
        """Load source definitions from vendor/sources.yaml."""
        if not SOURCES_FILE.exists():
            log.warning("Sources file not found: %s", SOURCES_FILE)
            return

        try:
            with open(SOURCES_FILE) as f:
                data = yaml.safe_load(f)
            self.sources = data.get("sources", {})
            log.info("Loaded %d source definitions", len(self.sources))
        except Exception as e:
            log.error("Failed to load sources: %s", e)

    def _load_installed_modules(self):
        """Load installed modules from disk"""
        metadata_file = self.modules_dir / "installed.json"

        if not metadata_file.exists():
            log.info("No installed modules found")
            return

        try:
            with open(metadata_file, "r") as f:
                data = json.load(f)

            for name, module_data in data.items():
                self.installed_modules[name] = ModuleInfo(
                    name=module_data["name"],
                    version=module_data["version"],
                    status=ModuleStatus(module_data["status"]),
                    description=module_data.get("description", ""),
                    type=module_data.get("type", "service"),
                    dependencies=module_data.get("dependencies", []),
                    health_status=module_data.get("health_status", "unknown"),
                    last_health_check=datetime.fromisoformat(module_data["last_health_check"])
                    if module_data.get("last_health_check") else None,
                    installed_path=module_data.get("installed_path"),
                    last_updated=datetime.fromisoformat(module_data["last_updated"])
                    if module_data.get("last_updated") else None,
                    metadata=module_data.get("metadata", {}),
                    size_bytes=module_data.get("size_bytes", 0),
                )

            log.info("Loaded %d installed modules", len(self.installed_modules))
        except Exception as e:
            log.error("Failed to load installed modules: %s", e)

    def _save_installed_modules(self):
        """Save installed modules to disk"""
        metadata_file = self.modules_dir / "installed.json"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            data = {
                name: module.to_dict()
                for name, module in self.installed_modules.items()
            }

            with open(metadata_file, "w") as f:
                json.dump(data, f, indent=2)

            log.info("Saved %d modules", len(self.installed_modules))
        except Exception as e:
            log.error("Failed to save installed modules: %s", e)

    def list_modules(self) -> List[ModuleInfo]:
        """List all installed modules"""
        return list(self.installed_modules.values())

    def get_module(self, name: str) -> Optional[ModuleInfo]:
        """Get module information"""
        return self.installed_modules.get(name)

    def _get_source(self, name: str) -> dict[str, Any] | None:
        """Get source definition for a module name.

        Tries exact match first, then checks if name matches a source key
        or if name is a subpath of a source.
        """
        # Exact match
        if name in self.sources:
            return self.sources[name]

        # Check if name matches a source key with different casing
        for key, source in self.sources.items():
            if key.lower() == name.lower():
                return source

        return None

    def _pull_from_github(
        self,
        source: dict[str, Any],
        target_dir: Path,
    ) -> tuple[bool, str]:
        """Pull source from GitHub using git sparse checkout.

        Args:
            source: Source definition dict with url, ref, subpath
            target_dir: Directory to extract into

        Returns:
            Tuple of (success, message)
        """
        url = source.get("url", "")
        ref = source.get("ref", "main")
        subpath = source.get("subpath", "")

        if not url:
            return False, "No URL defined in source"

        # Extract repo URL for git operations
        repo_url = url.rstrip(".git")
        if not repo_url.endswith(".git"):
            repo_url += ".git"

        try:
            target_dir.mkdir(parents=True, exist_ok=True)

            # Use git clone with sparse checkout for efficiency
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)

                # Initialize git repo
                result = subprocess.run(
                    ["git", "init"],
                    cwd=tmp_path,
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode != 0:
                    return False, f"Git init failed: {result.stderr}"

                # Add remote
                result = subprocess.run(
                    ["git", "remote", "add", "origin", repo_url],
                    cwd=tmp_path,
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode != 0:
                    return False, f"Git remote add failed: {result.stderr}"

                # Enable sparse checkout
                result = subprocess.run(
                    ["git", "sparse-checkout", "init", "--cone"],
                    cwd=tmp_path,
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode != 0:
                    log.warning("Sparse checkout init failed, trying full clone")

                # Set sparse checkout path if subpath specified
                if subpath:
                    result = subprocess.run(
                        ["git", "sparse-checkout", "set", subpath],
                        cwd=tmp_path,
                        capture_output=True, text=True, timeout=30,
                    )
                    if result.returncode != 0:
                        log.warning(
                            "Sparse checkout set failed for %s, "
                            "falling back to full clone", subpath
                        )

                # Pull from remote
                log.info("Pulling %s ref %s from %s", subpath or "(root)", ref, repo_url)
                result = subprocess.run(
                    ["git", "pull", "--depth", "1", "origin", ref],
                    cwd=tmp_path,
                    capture_output=True, text=True, timeout=120,
                )
                if result.returncode != 0:
                    return False, f"Git pull failed: {result.stderr}"

                # Copy the subpath to target directory
                source_path = tmp_path
                if subpath:
                    source_path = tmp_path / subpath

                if not source_path.exists():
                    return False, f"Subpath '{subpath}' not found in repository"

                # Remove existing target contents
                for item in target_dir.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()

                # Copy new contents
                for item in source_path.iterdir():
                    dest = target_dir / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dest)

            return True, f"Successfully pulled from {url}"

        except subprocess.TimeoutExpired:
            return False, "Git operation timed out"
        except Exception as e:
            return False, f"Git pull failed: {e}"

    def install_module(
        self,
        name: str,
        version: Optional[str] = None,
        force: bool = False,
    ) -> DistributionOperationResult:
        """Install a module by pulling from GitHub source.

        Args:
            name: Module name (must match a key in vendor/sources.yaml)
            version: Specific version/ref to install
            force: Force reinstallation

        Returns:
            DistributionOperationResult with installation status
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Check if module already exists
            if name in self.installed_modules and not force:
                existing = self.installed_modules[name]
                if existing.status == ModuleStatus.INSTALLED:
                    return DistributionOperationResult(
                        success=False,
                        operation="install",
                        module_name=name,
                        message=f"Module {name} is already installed "
                                f"(version {existing.version})",
                    )

            # Get source definition
            source = self._get_source(name)
            if not source:
                return DistributionOperationResult(
                    success=False,
                    operation="install",
                    module_name=name,
                    message=f"No source definition found for '{name}' "
                            f"in {SOURCES_FILE}",
                )

            # Determine target directory
            target_dir = DIST_DIR / name
            target_dir.mkdir(parents=True, exist_ok=True)

            # Pull from GitHub
            if source.get("type") == "github":
                ref = version or source.get("ref", "main")
                pull_source = dict(source)
                pull_source["ref"] = ref

                success, message = self._pull_from_github(pull_source, target_dir)
                if not success:
                    return DistributionOperationResult(
                        success=False,
                        operation="install",
                        module_name=name,
                        message=f"GitHub pull failed: {message}",
                    )

                # Calculate size
                size_bytes = sum(
                    f.stat().st_size for f in target_dir.rglob("*") if f.is_file()
                )

                # Create module info
                module_info = ModuleInfo(
                    name=name,
                    version=ref,
                    status=ModuleStatus.INSTALLED,
                    description=source.get("description", f"Module {name}"),
                    type="service",
                    installed_path=str(target_dir),
                    last_updated=datetime.now(timezone.utc),
                    size_bytes=size_bytes,
                    metadata={
                        "source_url": source.get("url", ""),
                        "source_ref": ref,
                        "source_subpath": source.get("subpath", ""),
                    },
                )

                self.installed_modules[name] = module_info
                self._save_installed_modules()

                duration = (datetime.now(timezone.utc) - start_time).total_seconds()

                return DistributionOperationResult(
                    success=True,
                    operation="install",
                    module_name=name,
                    message=f"Module {name} installed successfully from {ref}",
                    module_info=module_info,
                    duration_seconds=duration,
                )
            else:
                return DistributionOperationResult(
                    success=False,
                    operation="install",
                    module_name=name,
                    message=f"Unsupported source type: {source.get('type')}",
                )

        except Exception as e:
            log.error("Failed to install module %s: %s", name, e)
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            return DistributionOperationResult(
                success=False,
                operation="install",
                module_name=name,
                message=f"Failed to install module {name}: {e}",
                duration_seconds=duration,
            )

    def update_module(
        self,
        name: str,
        force: bool = False,
    ) -> DistributionOperationResult:
        """Update a module by re-pulling from GitHub.

        Args:
            name: Module name
            force: Force update even if already latest

        Returns:
            DistributionOperationResult with update status
        """
        start_time = datetime.now(timezone.utc)

        try:
            module = self.installed_modules.get(name)

            if not module:
                return DistributionOperationResult(
                    success=False,
                    operation="update",
                    module_name=name,
                    message=f"Module {name} is not installed",
                )

            if module.status == ModuleStatus.REMOVED:
                return DistributionOperationResult(
                    success=False,
                    operation="update",
                    module_name=name,
                    message=f"Module {name} has been removed",
                )

            # Re-install to get latest
            return self.install_module(name=name, force=True)

        except Exception as e:
            log.error("Failed to update module %s: %s", name, e)
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            return DistributionOperationResult(
                success=False,
                operation="update",
                module_name=name,
                message=f"Failed to update module {name}: {e}",
                duration_seconds=duration,
            )

    def remove_module(
        self,
        name: str,
        force: bool = False,
    ) -> DistributionOperationResult:
        """Remove a module

        Args:
            name: Module name
            force: Force removal even if dependencies exist

        Returns:
            DistributionOperationResult with removal status
        """
        start_time = datetime.now(timezone.utc)

        try:
            module = self.installed_modules.get(name)

            if not module:
                return DistributionOperationResult(
                    success=False,
                    operation="remove",
                    module_name=name,
                    message=f"Module {name} is not installed",
                )

            # Remove installed files
            if module.installed_path:
                install_path = Path(module.installed_path)
                if install_path.exists():
                    shutil.rmtree(install_path)
                    log.info("Removed installed files for %s", name)

            # Remove from registry
            del self.installed_modules[name]
            self._save_installed_modules()

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            return DistributionOperationResult(
                success=True,
                operation="remove",
                module_name=name,
                message=f"Module {name} removed successfully",
                duration_seconds=duration,
            )

        except Exception as e:
            log.error("Failed to remove module %s: %s", name, e)
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            return DistributionOperationResult(
                success=False,
                operation="remove",
                module_name=name,
                message=f"Failed to remove module {name}: {e}",
                duration_seconds=duration,
            )

    def repair_module(self, name: str) -> DistributionOperationResult:
        """Repair a module by re-installing from source.

        Args:
            name: Module name

        Returns:
            DistributionOperationResult with repair status
        """
        start_time = datetime.now(timezone.utc)

        try:
            module = self.installed_modules.get(name)

            if not module:
                return DistributionOperationResult(
                    success=False,
                    operation="repair",
                    module_name=name,
                    message=f"Module {name} is not installed",
                )

            # Re-install to repair
            result = self.install_module(name=name, force=True)

            if result.success:
                # Update health status
                module = self.installed_modules.get(name)
                if module:
                    module.health_status = "healthy"
                    module.last_health_check = datetime.now(timezone.utc)
                    self._save_installed_modules()

            return result

        except Exception as e:
            log.error("Failed to repair module %s: %s", name, e)
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            return DistributionOperationResult(
                success=False,
                operation="repair",
                module_name=name,
                message=f"Failed to repair module {name}: {e}",
                duration_seconds=duration,
            )

    def update_all_modules(self) -> List[DistributionOperationResult]:
        """Update all installed modules

        Returns:
            List of operation results
        """
        results = []

        for name, module in self.installed_modules.items():
            if module.status in [ModuleStatus.INSTALLED, ModuleStatus.UPDATED]:
                result = self.update_module(name)
                results.append(result)

        return results

    def repair_all_modules(self) -> List[DistributionOperationResult]:
        """Repair all installed modules

        Returns:
            List of operation results
        """
        results = []

        for name, module in self.installed_modules.items():
            if module.status in [ModuleStatus.INSTALLED, ModuleStatus.UPDATED]:
                result = self.repair_module(name)
                results.append(result)

        return results

    def destroy_system(self, force: bool = False) -> DistributionOperationResult:
        """Destroy the entire system

        Args:
            force: Force destruction even if modules are in use

        Returns:
            DistributionOperationResult with destruction status
        """
        start_time = datetime.now(timezone.utc)

        try:
            # Remove all installed modules
            for name in list(self.installed_modules.keys()):
                self.remove_module(name, force=True)

            # Clean up dist directory
            if DIST_DIR.exists():
                shutil.rmtree(DIST_DIR)
                log.info("Removed dist directory: %s", DIST_DIR)

            self.installed_modules.clear()
            self._save_installed_modules()

            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            return DistributionOperationResult(
                success=True,
                operation="destroy",
                module_name="system",
                message="System destroyed successfully",
                duration_seconds=duration,
            )

        except Exception as e:
            log.error("Failed to destroy system: %s", e)
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()

            return DistributionOperationResult(
                success=False,
                operation="destroy",
                module_name="system",
                message=f"Failed to destroy system: {e}",
                duration_seconds=duration,
            )

    def get_system_health_report(self) -> SystemHealthReport:
        """Get system health report

        Returns:
            SystemHealthReport with current system status
        """
        modules = list(self.installed_modules.values())

        # Check each module's health
        for module in modules:
            if module.installed_path:
                install_path = Path(module.installed_path)
                if not install_path.exists():
                    module.health_status = "unhealthy"
                else:
                    module.health_status = "healthy"
            module.last_health_check = datetime.now(timezone.utc)

        # Determine overall status
        unhealthy_count = sum(1 for m in modules if m.health_status == "unhealthy")

        if unhealthy_count == 0:
            overall_status = "healthy"
        elif unhealthy_count < len(modules):
            overall_status = "degraded"
        else:
            overall_status = "critical"

        return SystemHealthReport(
            overall_status=overall_status,
            modules=modules,
            services=[],
            issues=[],
            recommendations=[],
        )
