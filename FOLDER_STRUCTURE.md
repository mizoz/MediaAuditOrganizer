# MediaAuditOrganizer — Folder Structure

**Generated:** 2026-03-04  
**Phase:** Phase 2 — Option B (Full Industrial Structure)  
**Decision:** DECISION_LOG_20260303.md — Decision #1 Approved

---

## Complete Directory Tree

```
MediaAuditOrganizer/
├── 00_INCOMING/                    # Raw audit outputs, temporary files
│   ├── audit_20260303_224251/
│   ├── audit_20260303_230705/
│   ├── ingest_*/
│   ├── pending_review/
│   └── unknown_types/
│
├── 01_PHOTOS/                      # Organized photos (target directory)
│
├── 02_VIDEOS/                      # Organized videos (target directory)
│
├── 03_PROJECTS/                    # Client/project-based organization [NEW]
│   ├── .gitkeep
│   └── README.md
│
├── 04_CATALOGS/                    # Lightroom catalogs, Capture One sessions [NEW]
│   ├── .gitkeep
│   └── README.md
│
├── 05_BACKUPS/                     # Backup verification
│   ├── cloud/
│   ├── duplicates/
│   └── local/
│
├── 06_METADATA/                    # SQLite database, manifests
│   └── catalogs_parsed/
│
├── 07_LOGS/                        # Operation logs
│
├── 08_REPORTS/                     # HTML/CSV reports
│   ├── monthly_summaries/
│   ├── per_drive/
│   └── reconciliation/
│
├── 09_ARCHIVE/                     # Duplicates, rejected files, old versions [NEW]
│   ├── .gitkeep
│   ├── README.md
│   └── duplicates_20260304/        # 5 files archived from SA-06 audit
│       ├── .gitkeep
│       ├── .PM_lock
│       ├── 100MSDCF_.PM_lock
│       ├── AVIN0001.BNP (1.32 MB)
│       ├── ROOT_.PM_lock
│       └── SONYCARD.IND
│
├── .axiom_catalog/                 # Hidden system directory [NEW]
│   ├── .gitkeep
│   ├── README.md
│   ├── sqlite_backups/             # Automated DB backups
│   │   └── .gitkeep
│   └── system/                     # Shadow manifests, checkpoints
│       └── .gitkeep
│
├── agents/                         # Agent scripts and configurations
├── configs/                        # Configuration files
├── gui/                            # Graphical user interface
├── logs/                           # Application logs
├── reports/                        # Generated reports
├── scripts/                        # Automation scripts
│   ├── analyze_duplicates.py
│   ├── deduplicate.py
│   └── __pycache__/
└── templates/                      # Report templates
```

---

## Directory Purposes

### Active Workflow Directories

| Directory | Purpose | Status |
|-----------|---------|--------|
| `00_INCOMING/` | Raw audit outputs, temporary staging | Active |
| `01_PHOTOS/` | Organized photos (final destination) | Target |
| `02_VIDEOS/` | Organized videos (final destination) | Target |
| `05_BACKUPS/` | Backup verification and storage | Active |
| `06_METADATA/` | SQLite database, manifests, parsed catalogs | Active |
| `07_LOGS/` | Operation logs, audit trails | Active |
| `08_REPORTS/` | HTML/CSV reports, summaries | Active |

### New Directories (Phase 2)

| Directory | Purpose | Created |
|-----------|---------|---------|
| `03_PROJECTS/` | Client/project-based organization | 2026-03-04 |
| `04_CATALOGS/` | Lightroom catalogs, Capture One sessions | 2026-03-04 |
| `09_ARCHIVE/` | Duplicates, rejected files, old versions | 2026-03-04 |
| `.axiom_catalog/` | Hidden system directory (SQLite backups, shadow manifests) | 2026-03-04 |

### Hidden System Directories

| Directory | Purpose | Access |
|-----------|---------|--------|
| `.axiom_catalog/sqlite_backups/` | Automated database backups | System only |
| `.axiom_catalog/system/` | Shadow manifests, checkpoints | System only |
| `.gitkeep` | Preserves empty directories in git | All |

---

## Archive Contents (as of 2026-03-04)

**Location:** `09_ARCHIVE/duplicates_20260304/`

| File | Original Path | Size | Source |
|------|--------------|------|--------|
| `.PM_lock` | `/media/az/drive64gb/DCIM/.PM_lock` | 0 B | SA-06 Duplicate Group #1 |
| `100MSDCF_.PM_lock` | `/media/az/drive64gb/DCIM/100MSDCF/.PM_lock` | 0 B | SA-06 Duplicate Group #1 |
| `ROOT_.PM_lock` | `/media/az/drive64gb/.PM_lock` | 0 B | SA-06 Duplicate Group #1 |
| `SONYCARD.IND` | `/media/az/drive64gb/PRIVATE/SONY/SONYCARD.IND` | 0 B | SA-06 Duplicate Group #1 |
| `AVIN0001.BNP` | `/media/az/drive64gb/AVF_INFO/AVIN0001.BNP` | 1.32 MB | SA-06 Duplicate Group #2 |

**Total Archived:** 5 files (1.32 MB recoverable space)

---

## Naming Conventions

### Project Folders (03_PROJECTS/)
```
YYYY_ProjectName/
Example: 2022_SageGrouse/
         2023_Wildlife_Contract/
```

### Archive Folders (09_ARCHIVE/)
```
YYYYMMDD_Reason/
Example: duplicates_20260304/
         rejected_20260315/
         old_versions_20260401/
```

### Catalog Folders (04_CATALOGS/)
```
SoftwareName/
Example: Lightroom/
         CaptureOne/
         MetadataDB/
```

---

## Git Configuration

All empty directories contain `.gitkeep` files to preserve structure in version control.

**Directories with .gitkeep:**
- `03_PROJECTS/.gitkeep`
- `04_CATALOGS/.gitkeep`
- `09_ARCHIVE/.gitkeep`
- `09_ARCHIVE/duplicates_20260304/.gitkeep`
- `.axiom_catalog/.gitkeep`
- `.axiom_catalog/sqlite_backups/.gitkeep`
- `.axiom_catalog/system/.gitkeep`
- `05_BACKUPS/duplicates/.gitkeep`

---

## Next Steps

**Ready for:**
- SA-19 (Capacity Validator) — Validate storage capacity projections
- SA-20 (Sidecar Sync) — Implement sidecar file synchronization

**Pending:**
- Populate `03_PROJECTS/` with actual client projects
- Configure automated backups to `.axiom_catalog/sqlite_backups/`
- Set up shadow manifest system in `.axiom_catalog/system/`

---

**Document Version:** 1.0  
**Last Updated:** 2026-03-04  
**Maintained By:** MediaAuditOrganizer Phase 2
