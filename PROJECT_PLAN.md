# MediaAuditOrganizer — Project Plan

**Version:** 1.0  
**Created:** 2026-03-03  
**Status:** Ready for Implementation  
**Constraint:** Open source only, no API keys, offline-capable

---

## Executive Summary

This project builds an automated media library management system for 10,000+ photo and video assets across multiple external drives, with existing Lightroom catalog integration.

**Goals:**
1. Organize all assets into a consistent, date-based folder structure
2. Reconcile existing files with Lightroom catalogs (find missing files, orphans, duplicates)
3. Implement verified transfer workflow with checksum validation
4. Set up 3-2-1 backup system (primary + local + cloud)
5. Generate automated reports for library health and audit trails
6. Maintain Lightroom catalog synchronization throughout

**Timeline:** 10 weeks to full production  
**Tools:** ExifTool, FFprobe, fd, rclone, Python, SQLite, Jinja2

---

## Section A: Master Folder & Naming Convention

### Folder Structure

```
/media_library/
├── 01_PHOTOS/YYYY/YYYY-MM_EventName/RAW/     # RAW files (.CR2, .ARW, .NEF)
├── 01_PHOTOS/YYYY/YYYY-MM_EventName/JPG/     # JPEG files
├── 02_VIDEOS/YYYY/YYYY-MM_EventName/         # Video files (.MP4, .MOV)
├── 03_PROJECTS/ProjectName_YYYYMMDD/         # Active client projects
├── 04_CATALOGS/Master_Catalog.lrcat          # Lightroom master catalog
├── 05_BACKUPS/                               # Local backup mirror
├── 06_METADATA/                              # Extracted metadata databases
├── 07_LOGS/                                  # Operation logs
└── 08_REPORTS/                               # Generated reports
```

### File Naming Pattern

**Photos:** `YYYYMMDD_HHMMSS_CameraModel_Sequence.ext`
- Example: `20250315_143022_D850_001.CR2`
- Example: `20250315_143022_D850_001.JPG` (RAW+JPG pair)

**Videos:** `YYYYMMDD_HHMMSS_Device_Res_FPS_Sequence.ext`
- Example: `20250315_143000_D850_4K_30fps_001.MP4`

**Missing EXIF:** `NODATE_YYYYMMDD_import_HHMMSS_OriginalName_hash8.ext`
- Files without readable EXIF dates go to `UNKNOWN_DATE/` folder for manual review

### Key Rules

| Rule | Implementation |
|------|----------------|
| RAW+JPG pairs stay linked | Same base name, separate RAW/ and JPG/ subfolders |
| Date from EXIF DateTimeOriginal | Falls back to file date if missing |
| Camera model in filename | Enables filtering by device |
| 3-digit sequence numbers | Prevents collisions, maintains order |
| Videos separate from photos | Dedicated `02_VIDEOS/` tree |

---

## Section B: Drive Ingestion Workflow

### 10-Step Process (Mounted Drive → Ejected Drive)

| Step | Action | Automation | User Approval |
|------|--------|------------|---------------|
| 1 | Pre-flight checks (space, mount) | ✅ Auto | No |
| 2 | Audit scan (manifest + metadata) | ✅ Auto | No |
| 3 | Duplicate detection | ✅ Auto | No |
| 4 | Report generation (PDF) | ✅ Auto | No |
| 5 | **User review of report** | ❌ Manual | **YES** |
| 6 | Transfer with checksum verification | ✅ Auto | No (pre-approved) |
| 7 | Post-transfer integrity check | ✅ Auto | **YES** |
| 8 | Final organization (rename + move) | ✅ Auto | No (pre-approved) |
| 9 | Backup sync (local + cloud) | ✅ Auto | No |
| 10 | Log entry and cleanup | ✅ Auto | No |

**Total Time:** 2-4 hours for 500GB (mostly automated, user time: 15-20 minutes)

### Two Approval Gates

1. **Before Transfer:** Review audit report, confirm what will be transferred
2. **Before Organization:** Confirm integrity check passed, approve final moves

---

## Section C: Existing Library Reconciliation

### One-Time Process for 10,000+ Existing Assets

**Duration:** 8-12 hours automated scan + 2-3 hours user review

### Four Categories Identified

| Category | Description | Count (Estimate) | Action |
|----------|-------------|------------------|--------|
| **A: In Catalog + On Disk** ✅ | Files properly tracked | ~70% | No action needed |
| **B: In Catalog, Missing From Disk** ⚠️ | Broken Lightroom references | ~10% | Locate or mark as lost |
| **C: On Disk, Not In Catalog** ⚠️ | Orphaned files | ~15% | Import or archive |
| **D: Exact Duplicates** ⚠️ | Same file, multiple locations | ~5% | Consolidate, recover space |

### Outputs

- `master_inventory.csv` — Complete file listing with SHA256 hashes
- `catalog_path_index.json` — All Lightroom references with metadata
- `reconciliation_report.pdf` — Visual report with charts
- `prioritized_action_plan.md` — Step-by-step remediation guide

### Priority Order

1. **Critical:** Find or mark missing files (Category B)
2. **High:** Import orphaned files (Category C)
3. **Medium:** Remove duplicates, recover space (Category D)
4. **Low:** Consolidate multiple catalogs (optional)

---

## Section D: Backup Architecture (3-2-1)

### Three Copies

| Copy | Location | Media | Capacity | Cost |
|------|----------|-------|----------|------|
| **Primary** | Workstation (`/media_library/`) | NVMe SSD/HDD | 2-4 TB | $0 |
| **Local Backup** | External drive (`/mnt/backup_drive/`) | HDD | 4-8 TB | $100-150 |
| **Offsite** | Cloudflare R2 | Cloud storage | Unlimited | ~$27/month for 1.8 TB |

### Sync Schedule

| Backup | Frequency | Time | Tool |
|--------|-----------|------|------|
| Local (daily) | Every day | 02:00 | rclone sync |
| Local (weekly) | Sunday | 03:00 | rclone copy to weekly/ |
| Cloud (weekly) | Sunday | 04:00 | rclone sync |
| Cloud (monthly) | 1st of month | 05:00 | rclone copy with versioning |

### Verification

- **Every transfer:** Checksum comparison (source vs destination hash)
- **Monthly audit:** Random 5% sample download and verify
- **Success criteria:** 100% hash match required

### Initial Cloud Upload Strategy

Upload 1.8 TB in phases to avoid bandwidth saturation:

| Phase | Content | Size | Duration |
|-------|---------|------|----------|
| 1 | Last 12 months (critical) | 100-200 GB | Week 1 |
| 2 | 1-3 years old (working) | 200-400 GB | Week 2-3 |
| 3 | 3+ years old (archive) | Remaining | Week 4-6 |
| 4 | Ongoing sync | Incremental only | Weekly |

---

## Section E: Reporting System

### Report Types

| Report | Frequency | Format | Purpose |
|--------|-----------|--------|---------|
| **Per-Drive Audit** | Each ingest | PDF + HTML | Review before transfer |
| **Transfer Summary** | Each ingest | PDF + CSV | Confirm success |
| **Monthly Library Summary** | Monthly | PDF + HTML | Library health overview |
| **Asset Ingestion Log** | Continuous | CSV | Running record of all transfers |
| **Backup Health Report** | Weekly | PDF | Backup status verification |

### Per-Drive Audit Report Includes

- File count by type (RAW, JPG, Video)
- Total size and date range
- Duplicate analysis (files and recoverable space)
- Recommended actions (transfer/skip/review)

### Monthly Summary Includes

- Total assets and storage used
- Month-over-month growth
- Backup health status
- Warnings and alerts
- Upcoming tasks

### Asset Ingestion Log (CSV)

Every transferred file logged with:
- Timestamp, source/destination paths
- File type, size, SHA256 hash
- EXIF date, camera model
- Transfer status (success/failure)

---

## Section F: Lightroom Integration

### Metadata Extraction

Before any file moves, extract from existing catalogs:

| Metadata | Priority | Notes |
|----------|----------|-------|
| Ratings (0-5 stars) | High | Preserved during organization |
| Flags (picked/rejected) | High | Maintained |
| Keywords | High | Hierarchical structure preserved |
| Collections | Medium | Recreated in new structure |
| Color labels | Medium | Preserved |
| Develop settings | Medium | All adjustments retained |
| File paths | Critical | Updated after moves |

### Catalog Strategy

**Recommendation:** Single master catalog for daily work + archive catalogs for historical data

```
Master_Catalog.lrcat          # 2024-present, active work
Archive_Catalogs/
  ├── 2020-2023_Archive.lrcat  # Historical, read-only
  └── Pre-2020_Archive.lrcat   # Legacy, read-only
```

### Folder Sync

Monthly automated check to ensure Lightroom folder tree matches actual disk structure:

- Folders in LR but not on disk → Remove from catalog
- Folders on disk but not in LR → Import to catalog
- File count mismatches → Investigate and resolve

### Auto-Import Setup

Configure Lightroom to watch `00_INCOMING/pending_review/` folder:

- New files automatically imported after ingest
- Applied keywords from folder name
- Build standard previews
- Add to minimal catalog for review

---

## Tool Stack

| Function | Tool | License | Notes |
|----------|------|---------|-------|
| Metadata extraction | ExifTool | GPL/Artistic | Industry standard |
| Video metadata | FFprobe (FFmpeg) | LGPL | Part of FFmpeg |
| File scanning | fd + sha256sum | MIT/Apache | Fast, parallel |
| Duplicate detection | fdupes + rdfind | GPL/MIT | Two-stage approach |
| Lightroom parsing | Custom Python + SQLite | MIT | Direct catalog access |
| File transfer | rclone | MIT | Checksum verification |
| Backup (cloud) | rclone + Cloudflare R2 | MIT | No egress fees |
| Reports | Python + Jinja2 + WeasyPrint | BSD-3/GPL | PDF from templates |
| Bulk renaming | ExifTool | GPL/Artistic | Pattern-based |
| DAM (optional) | digiKam | GPL-2.0 | Lightroom alternative |

---

## Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1-2 | Core Tools | ExifTool, FFprobe, fd, rclone installed and tested |
| 2-3 | Audit Scripts | Drive audit, metadata extraction, duplicate detection |
| 3-4 | Lightroom Parser | SQLite catalog parser, metadata extraction |
| 4-5 | Reconciliation | Full library scan, reconciliation report |
| 5-6 | Transfer Workflow | rclone scripts, verification, logging |
| 6-7 | Backup System | Local + cloud backup configured, automated |
| 7-8 | Reports | Jinja2 templates, PDF generation |
| 8-9 | Lightroom Integration | Folder sync, path updates, auto-import |
| 9-10 | Testing | Full end-to-end test with sample dataset |
| 10+ | Production | Process existing library, ongoing operations |

---

## What Requires Your Approval

| Action | When | How |
|--------|------|-----|
| Transfer files from drive | After audit report generated | Review PDF, run `./approve_transfer.sh` |
| Final organization | After integrity check passes | Review report, run `./approve_organization.sh` |
| Delete duplicates | After 30-day archive period | Review archive, confirm deletion |
| Cloud backup configuration | Before initial setup | Review cost estimate, enable |
| Catalog consolidation | Optional, if desired | Review merge plan, approve |

**Nothing is deleted without explicit approval.** All operations are logged and reversible until final confirmation.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Data loss during transfer | Checksum verification, backup before any operation |
| Lightroom catalog corruption | Backup catalogs before changes, test on copy first |
| Cloud cost overrun | Monthly monitoring, budget alerts, R2 (no egress fees) |
| Script bugs | Dry-run mode, extensive logging, confirmation gates |
| Drive failure | Work on copies, never modify source drives directly |

---

## Next Steps

1. **Review this plan** — Confirm approach aligns with your workflow
2. **Approve Phase 1** — Begin core tool installation and testing
3. **Provide test dataset** — 100-200 files for validation before full run
4. **Schedule reconciliation** — Block 1-2 days for existing library processing

---

**Questions or adjustments?** This plan is a starting point — all details can be modified based on your specific workflow preferences.

**Agent 2 (PLANNER) — Complete**

Technical implementation details: `agents/agent_2_plan.md`
