# .axiom_catalog

Hidden system directory for SQLite backups, shadow manifests, and system metadata.

## Purpose

This directory contains internal system files used by the MediaAuditOrganizer for database backups, checkpoint files, and shadow manifests. Do not modify manually.

## Structure

```
.axiom_catalog/
├── sqlite_backups/
│   └── [timestamp]_backup.db
├── system/
│   ├── shadow_manifest.json
│   └── checkpoints/
└── .gitkeep
```

## Subdirectories

### sqlite_backups/
Automated SQLite database backups. Created by backup processes.

### system/
Shadow manifests and checkpoint files for system state recovery.

## Access

- Read: System processes only
- Write: Automated backup systems only
- Manual modification: **NOT RECOMMENDED**

## Created

2026-03-04 as part of MediaAuditOrganizer Phase 2 (Option B — Full Industrial Structure)
