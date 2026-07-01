"""Maintenance Service

Handles system maintenance operations:
- Backup and restore
- Archive and cleanup
- Feed and spool management
- Compost and recovery
- Reboot and shutdown
- Health monitoring
- Self-healing

Usage:
    from app.services.maintenance import MaintenanceService
    ms = MaintenanceService()
    
    # Create backup
    backup = ms.create_backup()
    
    # Restore from backup
    ms.restore_backup(backup_id)
    
    # Archive old data
    ms.archive_old_data(days=30)
    
    # Compost system
    ms.compost_system()
    
    # Reboot system
    ms.reboot_system()
"""

from .maintenance_service import MaintenanceService
from .models import BackupInfo, ArchiveInfo, CompostResult, MaintenanceOperationResult

__all__ = ["MaintenanceService", "BackupInfo", "ArchiveInfo", "CompostResult", "MaintenanceOperationResult"]