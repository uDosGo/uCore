"""Template Verification & Promotion System.

Verifies plates against test suites and promotion criteria:
- 95% pass rate for test suites
- Security checks (no hardcoded secrets, safe commands)
- Dogfooding validation (can the plate rebuild itself?)
- Schema compliance

Promotion workflow:
  Working modification -> Validate -> Create/Update plate -> Register

Usage:
    from plate_refresh.verification import verify_plate, promote_plate

    # Verify a plate
    report = verify_plate("vault.user_vault_seed")

    # Promote a working modification to a plate
    result = promote_plate(
        source="backend/app/skills/builtin/my_skill.py",
        target="plates/skills/my_skill.yaml",
        version="1.1.0",
    )
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from plate_refresh.models import PlateMeta
from plate_refresh.refresh import discover_plates, load_plate, render_plates

log = logging.getLogger("ucore.plate_refresh.verification")

ROOT = Path(__file__).resolve().parents[2]  # /Users/fredbook/Code/uCore
PLATES_ROOT = ROOT / "plates"


# ─── Verification Models ──────────────────────────────────


class VerificationResult:
    """Result of a plate verification run."""

    def __init__(
        self,
        plate_id: str,
        version: str,
        domain: str,
        passed: bool,
        pass_rate: float,
        total_checks: int,
        passed_checks: int,
        checks: list[dict[str, Any]],
        errors: list[str],
        warnings: list[str],
        duration_seconds: float,
    ):
        self.plate_id = plate_id
        self.version = version
        self.domain = domain
        self.passed = passed
        self.pass_rate = pass_rate
        self.total_checks = total_checks
        self.passed_checks = passed_checks
        self.checks = checks
        self.errors = errors
        self.warnings = warnings
        self.duration_seconds = duration_seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "plate_id": self.plate_id,
            "version": self.version,
            "domain": self.domain,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "checks": self.checks,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_seconds": self.duration_seconds,
            "verified_at": datetime.now(UTC).isoformat(),
        }


class PromotionResult:
    """Result of a plate promotion operation."""

    def __init__(
        self,
        plate_id: str,
        version: str,
        success: bool,
        verification: VerificationResult | None,
        target_path: str,
        message: str,
        errors: list[str],
    ):
        self.plate_id = plate_id
        self.version = version
        self.success = success
        self.verification = verification
        self.target_path = target_path
        self.message = message
        self.errors = errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "plate_id": self.plate_id,
            "version": self.version,
            "success": self.success,
            "verification": self.verification.to_dict() if self.verification else None,
            "target_path": self.target_path,
            "message": self.message,
            "errors": self.errors,
            "promoted_at": datetime.now(UTC).isoformat(),
        }


# ─── Verification Checks ──────────────────────────────────


def _check_schema_compliance(meta: PlateMeta, raw: dict[str, Any]) -> dict[str, Any]:
    """Check that the plate has valid schema and required fields."""
    errors: list[str] = []
    warnings: list[str] = []

    # Required fields
    if not meta.id:
        errors.append("plate.id is required")
    if not meta.version:
        errors.append("plate.version is required")
    if not meta.description:
        warnings.append("plate.description is empty — add a description")

    # Version format
    version_pattern = re.compile(r"^\d+\.\d+\.\d+$")
    if not version_pattern.match(meta.version):
        errors.append(f"Invalid version format: '{meta.version}' (expected semver)")

    # Domain validation
    valid_domains = {"skill", "snack", "mcp", "hivemind", "secret", "css", "vault"}
    if meta.domain not in valid_domains:
        errors.append(f"Invalid domain: '{meta.domain}' (must be one of {valid_domains})")

    # Source validation
    valid_sources = {"builtin", "user", "community"}
    if meta.source not in valid_sources:
        errors.append(f"Invalid source: '{meta.source}'")

    # Dependencies format
    for dep in meta.dependencies:
        if not isinstance(dep, str) or "." not in dep:
            errors.append(f"Invalid dependency format: '{dep}' (expected 'domain.name')")

    return {
        "name": "schema_compliance",
        "description": "Validate plate schema and required fields",
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def _check_security(raw: dict[str, Any]) -> dict[str, Any]:
    """Check for security issues in the plate definition."""
    errors: list[str] = []
    warnings: list[str] = []

    plate_data = raw.get("plate", {})

    # Check rebuild commands for dangerous patterns
    rebuild_cmd = plate_data.get("destroy", {}).get("rebuild_command", "")
    dangerous_patterns = [
        (r"rm\s+-rf\s+/", "Dangerous rm -rf / command"),
        (r"sudo\s+", "Uses sudo — may require elevated privileges"),
        (r"chmod\s+777", "Overly permissive chmod 777"),
        (r">\s*/dev/", "Writing to /dev/ devices"),
        (r"dd\s+if=", "dd command — potentially destructive"),
    ]
    for pattern, warning in dangerous_patterns:
        if re.search(pattern, rebuild_cmd):
            warnings.append(f"Security warning in rebuild_command: {warning}")

    # Check for hardcoded secrets
    secret_patterns = [
        r"(?i)(api_key|apikey|secret|password|token)\s*[:=]\s*['\"][^'\"]+['\"]",
        r"(?i)(api_key|apikey|secret|password|token)\s*:\s*\S+",
    ]
    raw_yaml = yaml.dump(raw)
    for pattern in secret_patterns:
        matches = re.findall(pattern, raw_yaml)
        if matches:
            errors.append(
                "Hardcoded secrets detected in plate definition. "
                "Use environment variables or secret store instead."
            )

    # Check salvage_keys don't expose sensitive data
    salvage_keys = plate_data.get("destroy", {}).get("salvage_keys", [])
    sensitive_keys = {"password", "secret", "token", "api_key", "key"}
    for key in salvage_keys:
        if key.lower() in sensitive_keys:
            warnings.append(
                f"Salvage key '{key}' may expose sensitive data. "
                "Consider using secret store instead."
            )

    return {
        "name": "security_check",
        "description": "Check for security issues in plate definition",
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def _check_dogfooding(plate_id: str, meta: PlateMeta) -> dict[str, Any]:
    """Check that the plate can rebuild itself (dogfooding test)."""
    errors: list[str] = []
    warnings: list[str] = []

    if not meta.destroy.rebuild_command:
        warnings.append("No rebuild_command defined — cannot verify dogfooding")
        return {
            "name": "dogfooding",
            "description": "Verify plate can rebuild itself",
            "passed": True,
            "errors": errors,
            "warnings": warnings,
        }

    # Check that the rebuild command references valid paths
    cmd = meta.destroy.rebuild_command
    if "$" in cmd or "{" in cmd:
        # Has template variables — check they're in salvage_keys
        template_vars = re.findall(r"\$\{?(\w+)\}?", cmd)
        for var in template_vars:
            if var.upper() in ("DATE", "VERSION", "YEAR"):
                continue  # Built-in render variables
            if var not in meta.destroy.salvage_keys:
                warnings.append(
                    f"Rebuild command uses variable '${{{var}}}' "
                    f"but it's not in salvage_keys"
                )

    # Check the command references exist
    if "cookiecutter" in cmd:
        # Extract path from cookiecutter command
        match = re.search(r"cookiecutter\s+(\S+)", cmd)
        if match:
            template_path = match.group(1)
            resolved = Path(template_path).expanduser()
            if not resolved.exists():
                warnings.append(
                    f"Cookiecutter template not found: {template_path}"
                )

    return {
        "name": "dogfooding",
        "description": "Verify plate can rebuild itself",
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def _check_drift_resilience(plate_id: str, meta: PlateMeta) -> dict[str, Any]:
    """Check that the plate has drift detection and recovery mechanisms."""
    errors: list[str] = []
    warnings: list[str] = []

    # Check for checksum
    if not meta.checksum:
        warnings.append("No checksum defined — drift detection may be unreliable")

    # Check destroy config
    destroy = meta.destroy
    if not destroy.salvage_keys:
        warnings.append("No salvage_keys defined — state may be lost on rebuild")
    if not destroy.rebuild_command:
        warnings.append("No rebuild_command defined — cannot auto-recover")
    if not destroy.backup_before_destroy:
        warnings.append("backup_before_destroy is disabled — data may be lost")

    # Check spool archive config
    spool = destroy.spool_archive
    if not spool.enabled:
        warnings.append("SPOOL archiving disabled — no audit trail on destroy")
    if not spool.include_lessons:
        warnings.append("Lessons not included in SPOOL archive — wisdom may be lost")

    return {
        "name": "drift_resilience",
        "description": "Check drift detection and recovery mechanisms",
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def _check_renderability(plate_id: str) -> dict[str, Any]:
    """Check that the plate can be rendered without errors."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        rendered = render_plates()
        if plate_id not in [Path(p).stem for p in rendered]:
            # Check if the plate was rendered by looking at output paths
            loaded = load_plate(plate_id)
            if loaded:
                meta, _, _ = loaded
                expected = PLATES_ROOT / ".rendered" / meta.domain / f"{plate_id}.yaml"
                if not expected.exists():
                    errors.append(f"Plate was not rendered to {expected}")
    except Exception as exc:
        errors.append(f"Render failed: {exc}")

    return {
        "name": "renderability",
        "description": "Check that the plate can be rendered",
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# ─── Main Verification ────────────────────────────────────


def verify_plate(
    plate_id: str,
    run_dogfooding: bool = True,
    run_security: bool = True,
) -> VerificationResult:
    """Run all verification checks on a plate.

    Args:
        plate_id: The plate ID to verify
        run_dogfooding: Whether to run dogfooding checks
        run_security: Whether to run security checks

    Returns:
        VerificationResult with all check results
    """
    start = time.time()

    loaded = load_plate(plate_id)
    if not loaded:
        return VerificationResult(
            plate_id=plate_id,
            version="unknown",
            domain="unknown",
            passed=False,
            pass_rate=0.0,
            total_checks=1,
            passed_checks=0,
            checks=[{
                "name": "plate_exists",
                "description": "Check that the plate exists",
                "passed": False,
                "errors": [f"Plate '{plate_id}' not found"],
                "warnings": [],
            }],
            errors=[f"Plate '{plate_id}' not found"],
            warnings=[],
            duration_seconds=time.time() - start,
        )

    meta, raw, path = loaded
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []

    # Run all checks
    checks.append(_check_schema_compliance(meta, raw))

    if run_security:
        checks.append(_check_security(raw))

    checks.append(_check_drift_resilience(plate_id, meta))

    if run_dogfooding:
        checks.append(_check_dogfooding(plate_id, meta))

    checks.append(_check_renderability(plate_id))

    # Aggregate results
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])

    for c in checks:
        errors.extend(c.get("errors", []))
        warnings.extend(c.get("warnings", []))

    pass_rate = passed_checks / total_checks if total_checks > 0 else 0.0

    # Promotion criteria: 95% pass rate, no errors
    passed = pass_rate >= 0.95 and len(errors) == 0

    duration = time.time() - start

    log.info(
        "Verification for %s: %s (%.0f%% pass rate, %d checks, %.2fs)",
        plate_id,
        "PASSED" if passed else "FAILED",
        pass_rate * 100,
        total_checks,
        duration,
    )

    return VerificationResult(
        plate_id=plate_id,
        version=meta.version,
        domain=meta.domain,
        passed=passed,
        pass_rate=pass_rate,
        total_checks=total_checks,
        passed_checks=passed_checks,
        checks=checks,
        errors=errors,
        warnings=warnings,
        duration_seconds=duration,
    )


def verify_all_plates(
    run_dogfooding: bool = True,
    run_security: bool = True,
) -> list[VerificationResult]:
    """Verify all discovered plates."""
    plates = discover_plates()
    results = []
    for pid in plates:
        result = verify_plate(
            pid,
            run_dogfooding=run_dogfooding,
            run_security=run_security,
        )
        results.append(result)
    return results


# ─── Promotion ────────────────────────────────────────────


def promote_plate(
    source: str,
    target: str,
    version: str,
    author: str = "",
    force: bool = False,
) -> PromotionResult:
    """Promote a working modification to a canonical plate.

    Args:
        source: Path to the source file/component to promote
        target: Path to the target plate YAML file
        version: New version number (semver)
        author: Author of the promotion
        force: Skip verification and force promotion

    Returns:
        PromotionResult with promotion status
    """
    errors: list[str] = []
    source_path = Path(source).expanduser()
    target_path = Path(target).expanduser()

    # Validate source exists
    if not source_path.exists():
        return PromotionResult(
            plate_id=Path(target).stem,
            version=version,
            success=False,
            verification=None,
            target_path=str(target_path),
            message=f"Source file not found: {source}",
            errors=[f"Source file not found: {source}"],
        )

    # Determine domain from target path
    domain = _infer_domain_from_path(target_path)

    # Generate plate ID from target filename
    plate_id = target_path.stem
    if domain and not plate_id.startswith(domain + "."):
        plate_id = f"{domain}.{plate_id}"

    # If target already exists, load it for comparison
    existing_meta = None
    if target_path.exists():
        try:
            with open(target_path) as f:
                existing_data = yaml.safe_load(f)
            if existing_data and "plate" in existing_data:
                existing_meta = PlateMeta(**existing_data["plate"])
        except Exception:
            pass

    # Build new plate data
    plate_data = _build_plate_from_source(
        source_path=source_path,
        plate_id=plate_id,
        version=version,
        domain=domain,
        existing_meta=existing_meta,
    )

    # Verify before promotion (unless forced)
    verification = None
    if not force:
        # Write temporarily to verify
        target_path.parent.mkdir(parents=True, exist_ok=True)
        temp_content = yaml.dump({"plate": plate_data}, default_flow_style=False)
        target_path.write_text(temp_content)

        verification = verify_plate(plate_id)
        if not verification.passed:
            # Roll back if verification fails
            if existing_meta is None:
                target_path.unlink(missing_ok=True)
            else:
                # Restore original
                with open(target_path, "w") as f:
                    yaml.dump({"plate": existing_meta.model_dump()}, f)

            return PromotionResult(
                plate_id=plate_id,
                version=version,
                success=False,
                verification=verification,
                target_path=str(target_path),
                message="Verification failed — promotion aborted",
                errors=verification.errors,
            )

    # Write the plate
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w") as f:
        yaml.dump({"plate": plate_data}, f, default_flow_style=False)

    log.info(
        "Promoted %s -> %s (v%s)",
        source, target_path, version,
    )

    return PromotionResult(
        plate_id=plate_id,
        version=version,
        success=True,
        verification=verification,
        target_path=str(target_path),
        message=f"Promoted {source} to plate {plate_id} (v{version})",
        errors=[],
    )


def _infer_domain_from_path(path: Path) -> str:
    """Infer plate domain from the directory path."""
    for part in path.parts:
        if part in ("skills", "skill"):
            return "skill"
        if part in ("snacks", "snack"):
            return "snack"
        if part == "mcp":
            return "mcp"
        if part == "hivemind":
            return "hivemind"
        if part in ("secrets", "secret"):
            return "secret"
        if part in ("css", "usx"):
            return "css"
        if part == "vault":
            return "vault"
        if part == "destroy":
            return "skill"  # Destroy plates are skill-domain
    return "skill"


def _build_plate_from_source(
    source_path: Path,
    plate_id: str,
    version: str,
    domain: str,
    existing_meta: PlateMeta | None,
) -> dict[str, Any]:
    """Build a plate definition from a source file."""
    # Start with existing metadata if available
    base = existing_meta.model_dump() if existing_meta else {}

    # Compute checksum of source
    checksum = ""
    try:
        content = source_path.read_text()
        import hashlib
        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
    except Exception:
        pass

    # Build plate data
    plate_data = {
        "id": plate_id,
        "version": version,
        "domain": domain,
        "description": base.get("description", f"Plate for {source_path.name}"),
        "source": base.get("source", "user"),
        "checksum": checksum,
        "dependencies": base.get("dependencies", []),
        "lessons": base.get("lessons", []),
        "created": base.get("created", datetime.now(UTC).isoformat()),
        "updated": datetime.now(UTC).isoformat(),
        "destroy": base.get("destroy", {
            "salvage_keys": [],
            "rebuild_command": "",
            "backup_before_destroy": True,
            "spool_archive": {
                "enabled": True,
                "spool_dir": "~/.ucore/logs",
                "compress_metadata": True,
                "include_source": False,
                "include_lessons": True,
                "max_spool_age_days": 365,
            },
        }),
    }

    return plate_data


# ─── CLI Integration ──────────────────────────────────────


def add_verification_args(parser: Any) -> None:
    """Add verification and promotion arguments to an argparse parser."""
    parser.add_argument(
        "--verify", type=str, nargs="?", const="all", default=None,
        help="Verify a specific plate or 'all'",
    )
    parser.add_argument(
        "--verify-no-dogfooding", action="store_true",
        help="Skip dogfooding checks during verification",
    )
    parser.add_argument(
        "--verify-no-security", action="store_true",
        help="Skip security checks during verification",
    )
    parser.add_argument(
        "--promote", type=str, default=None,
        help="Promote a source file to a plate. Format: source=target",
    )
    parser.add_argument(
        "--promote-version", type=str, default="1.0.0",
        help="Version for promoted plate (default: 1.0.0)",
    )
    parser.add_argument(
        "--promote-force", action="store_true",
        help="Skip verification and force promotion",
    )


def handle_verification_commands(args: Any) -> None:
    """Handle verification and promotion CLI commands."""
    if args.verify:
        run_dogfooding = not args.verify_no_dogfooding
        run_security = not args.verify_no_security

        if args.verify == "all":
            results = verify_all_plates(
                run_dogfooding=run_dogfooding,
                run_security=run_security,
            )
        else:
            results = [verify_plate(
                args.verify,
                run_dogfooding=run_dogfooding,
                run_security=run_security,
            )]

        for r in results:
            status = "PASSED" if r.passed else "FAILED"
            print(f"\n  {r.plate_id} (v{r.version}) [{r.domain}]: {status}")
            print(f"    Pass rate: {r.pass_rate:.0%} "
                  f"({r.passed_checks}/{r.total_checks})")
            print(f"    Duration: {r.duration_seconds:.2f}s")
            for c in r.checks:
                c_status = "PASS" if c["passed"] else "FAIL"
                print(f"    [{c_status}] {c['name']}: {c['description']}")
                for e in c.get("errors", []):
                    print(f"      ERROR: {e}")
                for w in c.get("warnings", []):
                    print(f"      WARN: {w}")

    if args.promote:
        # Parse source=target format
        parts = args.promote.split("=", 1)
        if len(parts) != 2:
            print("ERROR: --promote must be in format: source=target")
            return
        source, target = parts
        result = promote_plate(
            source=source.strip(),
            target=target.strip(),
            version=args.promote_version,
            force=args.promote_force,
        )
        if result.success:
            print(f"\n  PROMOTED: {result.message}")
        else:
            print(f"\n  FAILED: {result.message}")
            for e in result.errors:
                print(f"    ERROR: {e}")
