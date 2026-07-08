"""Plate Refresh Engine.

Render, validate, detect drift, and rebuild from plates.
Plates are canonical, versioned, recoverable blueprints.
"""

from plate_refresh.models import DriftReport, PlateMeta, RebuildResult
from plate_refresh.refresh import (
    destroy_and_rebuild,
    detect_all_drift,
    detect_drift,
    discover_plates,
    load_plate,
    render_plates,
    validate_all_plates,
    validate_plate,
)

__all__ = [
    "PlateMeta",
    "DriftReport",
    "RebuildResult",
    "discover_plates",
    "load_plate",
    "render_plates",
    "validate_plate",
    "validate_all_plates",
    "detect_drift",
    "detect_all_drift",
    "destroy_and_rebuild",
]
