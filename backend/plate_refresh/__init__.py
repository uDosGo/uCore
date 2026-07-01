"""Plate Refresh Engine.

Render, validate, detect drift, and rebuild from plates.
Plates are canonical, versioned, recoverable blueprints.
"""

from plate_refresh.models import PlateMeta, DriftReport, RebuildResult
from plate_refresh.refresh import (
    discover_plates,
    load_plate,
    render_plates,
    validate_plate,
    validate_all_plates,
    detect_drift,
    detect_all_drift,
    destroy_and_rebuild,
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
