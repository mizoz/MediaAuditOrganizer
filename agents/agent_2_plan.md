# MediaAuditOrganizer — Agent 2 (PLANNER) Technical Implementation Plan

**Generated:** 2026-03-03 20:07 MST  
**Author:** Agent 2 (PLANNER)  
**Foundation:** Agent 1 Scout Results (`agent_1_scout_results.md`)  
**Constraints:** Open source only, no API keys, offline-capable, 10,000+ assets

---

## SECTION A — MASTER FOLDER AND NAMING CONVENTION

### A.1 Folder Structure Design

```
/media_library/
├── 00_INCOMING/                    # Temporary ingest staging
│   ├── drive_audit_YYYYMMDD/       # Per-drive audit results
│   └── pending_review/             # Files awaiting user approval
│
├── 01_PHOTOS/                      # Master photo library
│   ├── YYYY/                       # Year (from EXIF DateTimeOriginal)
│   │   ├── YYYY-MM_DD_EventName/  # Month + event descriptor
│   │   │   ├── RAW/               # RAW files (.CR2, .CR3, .ARW, .NEF, .DNG)
│   │   │   ├── JPG/               # JPEG files (including RAW+JPG pairs)
│   │   │   └── EDITED/            # Exported/edited versions
│   │   └── YYYY-MM_DD_EventName/
│   │
│   ├── UNKNOWN_DATE/               # Files with missing/unreadable EXIF
│   │   ├── YYYYMMDD_imported/     # Grouped by import date
│   │   └── review_required/       # Manual date assignment needed
│   │
│   └── SCREENSHOTS/                # Phone screenshots, UI captures
│       └── YYYY/
│
├── 02_VIDEOS/                      # Master video library
│   ├── YYYY/
│   │   ├── YYYY-MM_DD_EventName/
│   │   │   ├── ORIGINAL/          # Camera/drone originals (.MP4, .MOV, .MKV)
│   │   │   ├── TRANSCODED/        # H.264 proxy files for editing
│   │   │   └── CLIPS/             # Short extracted clips
│   │   └── YYYY-MM_DD_EventName/
│   │
│   └── UNKNOWN_DATE/
│
├── 03_PROJECTS/                    # Active client/personal projects
│   ├── ProjectName_YYYYMMDD/
│   │   ├── SELECTS/               # Final selects for delivery
│   │   ├── WORKING/               # In-progress edits
│   │   └── DELIVERABLES/          # Final exports
│   │
│   └── ProjectName_YYYYMMDD/
│
├── 04_CATALOGS/                    # Lightroom catalogs
│   ├── Master_Catalog/
│   │   ├── Master_Catalog.lrcat
│   │   ├── Master_Catalog.lrcat-data/
│   │   └── Previews/
│   │
│   ├── Project_Catalogs/          # Project-specific catalogs
│   └── Archive_Catalogs/          # Old catalogs (read-only)
│
├── 05_BACKUPS/                     # Local backup mirror
│   ├── daily/                     # Daily incremental (last 7 days)
│   ├── weekly/                    # Weekly snapshots (last 4 weeks)
│   └── monthly/                   # Monthly archives (last 12 months)
│
├── 06_METADATA/                    # Extracted metadata stores
│   ├── manifests/                 # Drive audit manifests (CSV/JSON)
│   ├── exif_data/                 # Extracted EXIF databases (SQLite)
│   ├── catalogs_parsed/           # Parsed .lrcat data (JSON/CSV)
│   └── reconciliation/            # Reconciliation reports
│
├── 07_LOGS/                        # Operation logs
│   ├── transfers/                 # rclone transfer logs
│   ├── backups/                   # Backup operation logs
│   ├── renames/                   # Bulk rename operation logs
│   └── audits/                    # Drive audit logs
│
└── 08_REPORTS/                     # Generated reports
    ├── per_drive/                 # Individual drive audit reports
    ├── monthly_summaries/         # Monthly library summaries
    └── reconciliation/            # Library reconciliation reports
```

### A.2 File Naming Conventions

#### Photos (RAW and JPG)

**Pattern:** `YYYYMMDD_HHMMSS_CameraModel_Sequence_RawType.ext`

**Examples:**
- `20250315_143022_D850_001.CR2` (RAW)
- `20250315_143022_D850_001.JPG` (JPG pair)
- `20250315_143022_D850_001_E.JPG` (Edited JPG)
- `20250315_143022_A7III_042.ARW` (Sony RAW)
- `20250315_091500_Mavic3_015.DNG` (Drone RAW)

**Components:**
| Component | Format | Source | Example |
|-----------|--------|--------|---------|
| Date | YYYYMMDD | EXIF DateTimeOriginal | 20250315 |
| Time | HHMMSS | EXIF DateTimeOriginal | 143022 |
| Camera | Model (spaces removed) | EXIF Model | D850, A7III, Mavic3 |
| Sequence | 3-digit padded | Incremental per shoot | 001, 042, 115 |
| RawType | _E (edited) | Manual flag | _E or empty |

**RAW+JPG Pair Handling:**
- Both files receive identical base name
- Only extension differs (.CR2/.JPG, .ARW/.JPG, .NEF/.JPG)
- Stored in parallel RAW/ and JPG/ subfolders
- Never separate pairs during any operation

#### Videos

**Pattern:** `YYYYMMDD_HHMMSS_DeviceType_Res_FPS_Sequence.ext`

**Examples:**
- `20250315_143000_D850_4K_30fps_001.MP4`
- `20250315_091500_Mavic3_5.4K_60fps_003.MOV`
- `20250315_160000_GoPro11_4K_120fps_012.MP4`
- `20250315_143000_D850_4K_30fps_001_proxy.MP4` (transcoded proxy)

**Components:**
| Component | Format | Source | Example |
|-----------|--------|--------|---------|
| Date | YYYYMMDD | File creation date / EXIF | 20250315 |
| Time | HHMMSS | File creation time | 143000 |
| Device | Type identifier | EXIF Make/Model | D850, Mavic3, GoPro11 |
| Res | Resolution | FFprobe width | 4K, 1080, 5.4K |
| FPS | Frame rate | FFprobe r_frame_rate | 30fps, 60fps, 120fps |
| Sequence | 3-digit padded | Incremental per shoot | 001, 012 |

#### Screenshots and Phone Photos (No EXIF)

**Pattern:** `SCREEN_YYYYMMDD_HHMMSS_Device_Sequence.ext`

**Examples:**
- `SCREEN_20250315_143022_iPhone14_001.HEIC`
- `SCREEN_20250315_091500_Desktop_042.PNG`

#### Files with Missing/Corrupted EXIF

**Pattern:** `NODATE_YYYYMMDD_import_HHMMSS_OriginalName_hash8.ext`

**Examples:**
- `NODATE_20250315_import_143022_IMG_1234_a3f5c8d2.CR2`
- `NODATE_20250315_import_091500_DSC_5678_b7e2f1a9.NEF`

**Handling:**
- Grouped in `UNKNOWN_DATE/YYYYMMDD_imported/`
- First 8 characters of SHA256 hash appended for uniqueness
- Flagged for manual review and date assignment

### A.3 Edge Case Handling

| Edge Case | Detection | Handling |
|-----------|-----------|----------|
| Missing EXIF date | ExifTool returns empty DateTimeOriginal | Use file modification date, prefix with NODATE_ |
| Multiple cameras same shoot | Different Model values, same date range | Include camera model in filename |
| RAW+JPG mismatch | One file missing pair | Log warning, process independently, flag for review |
| Duplicate sequence numbers | Same date/time/camera/sequence | Append hash8 to filename |
| Corrupted files | ExifTool/FFprobe fails | Move to `review_required/`, log error |
| Timezone ambiguity | EXIF has no timezone info | Assume local timezone (America/Edmonton), log assumption |
| Drone GPS vs camera GPS | GPS coordinates in video EXIF | Extract and store in metadata database, not filename |

### A.4 Lightroom Workflow Integration

**Folder References:**
- Lightroom catalog references folders by absolute path
- When files move/rename, catalog references break
- Solution: Use Lightroom's "Update Folder Location" feature programmatically
- Store folder path mappings in `06_METADATA/catalog_folder_map.json`

**Smart Collections:**
- Create smart collections based on filename patterns
- Example: "All D850 RAW" matches `*_D850_*.CR2`
- Example: "2025 Q1" matches `202501*` through `202503*`

**Publish Services:**
- Configure Lightroom Publish Services to export to `01_PHOTOS/YYYY/.../EDITED/`
- Auto-publish on rating change (5-star → EDITED folder)

---

## SECTION B — DRIVE INGESTION WORKFLOW

### B.1 Complete Workflow Steps

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DRIVE INGESTION WORKFLOW                              │
│                  (Mounted Drive → Ejected Drive)                         │
└─────────────────────────────────────────────────────────────────────────┘

Step 1: PRE-FLIGHT CHECKS (Automated)
├─ 1.1 Verify drive mount point exists
├─ 1.2 Check available space on destination (must have 2x source size)
├─ 1.3 Verify drive is read-only or user confirms write permissions
├─ 1.4 Log drive info: model, serial, capacity, filesystem
└─ 1.5 Create audit directory: 00_INCOMING/drive_audit_YYYYMMDD_HHMMSS/

Step 2: AUDIT SCAN (Automated, 30-60 sec for 10k files)
├─ 2.1 Run fd to enumerate all files
├─ 2.2 Run sha256sum on all files → manifest.sha256
├─ 2.3 Run ExifTool on photos → photo_metadata.json
├─ 2.4 Run FFprobe on videos → video_metadata.json
├─ 2.5 Generate manifest.csv with: path, size, type, hash, date
└─ 2.6 Store in 00_INCOMING/drive_audit_YYYYMMDD_HHMMSS/

Step 3: DUPLICATE DETECTION (Automated, 2-5 min for 10k files)
├─ 3.1 Run rdfind against existing library → exact duplicates
├─ 3.2 Run fdupes for verification → duplicate_report.txt
├─ 3.3 Flag near-duplicates for manual review (dupeGuru later)
└─ 3.4 Generate duplicate_summary.json

Step 4: REPORT GENERATION (Automated, 30-60 sec)
├─ 4.1 Generate per-drive audit report (HTML + PDF)
├─ 4.2 Include: file counts, total size, date range, duplicates
├─ 4.3 Include: recommended actions (transfer/skip/review)
└─ 4.4 Save to 08_REPORTS/per_drive/ + email to user

Step 5: USER REVIEW (Manual, requires approval)
├─ 5.1 User reviews audit report (PDF/email)
├─ 5.2 User confirms: transfer all / selective / skip duplicates
├─ 5.3 User approves naming convention application
└─ 5.4 [CONFIRMATION GATE] — No transfer without explicit approval

Step 6: TRANSFER WITH VERIFICATION (Automated, 2-4 hours for 500GB)
├─ 6.1 Run rclone copy with --checksum flag
├─ 6.2 Transfer to 00_INCOMING/pending_review/
├─ 6.3 Log every file: source, dest, hash_before, hash_after, status
├─ 6.4 Auto-retry failed transfers (max 3 attempts)
└─ 6.5 Generate transfer_log.csv

Step 7: POST-TRANSFER INTEGRITY CHECK (Automated, 30-60 min)
├─ 7.1 Re-hash all transferred files
├─ 7.2 Compare against source hashes from manifest.sha256
├─ 7.3 Flag any mismatches for re-transfer
├─ 7.4 Generate integrity_report.json
└─ 7.5 [CONFIRMATION GATE] — User approves before final move

Step 8: FINAL ORGANIZATION (Automated after approval)
├─ 8.1 Apply ExifTool renaming based on metadata
├─ 8.2 Move files to final destinations (01_PHOTOS/ or 02_VIDEOS/)
├─ 8.3 Maintain RAW+JPG pair relationships
├─ 8.4 Update Lightroom catalog (import new folder)
└─ 8.5 Log all renames and moves

Step 9: BACKUP SYNC (Automated)
├─ 9.1 Trigger rclone sync to local backup (05_BACKUPS/daily/)
├─ 9.2 Trigger rclone sync to cloud (R2/B2) — if enabled
├─ 9.3 Log backup completion
└─ 9.4 Update backup_status.json

Step 10: LOG ENTRY AND CLEANUP (Automated)
├─ 10.1 Append to master ingestion_log.csv
├─ 10.2 Archive audit directory to 06_METADATA/manifests/
├─ 10.3 Empty 00_INCOMING/pending_review/
├─ 10.4 Update library_statistics.json
└─ 10.5 Safe eject prompt to user

┌─────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW COMPLETE                                │
└─────────────────────────────────────────────────────────────────────────┘
```

### B.2 Automation vs Human Approval Matrix

| Step | Automation Level | User Approval Required | Notes |
|------|------------------|----------------------|-------|
| 1. Pre-flight checks | Fully automated | No | Failures block workflow |
| 2. Audit scan | Fully automated | No | Generates report for review |
| 3. Duplicate detection | Fully automated | No | Flags for review |
| 4. Report generation | Fully automated | No | Report sent to user |
| 5. User review | Manual | **YES** | **GATE 1** — No transfer without approval |
| 6. Transfer | Automated after approval | No (pre-approved) | Checksum verification automatic |
| 7. Integrity check | Fully automated | **YES** | **GATE 2** — Approve before final move |
| 8. Final organization | Automated after approval | No (pre-approved) | Renaming and folder placement |
| 9. Backup sync | Fully automated | No | Runs after organization |
| 10. Log and cleanup | Fully automated | No | Archive and eject |

### B.3 Script Implementation Structure

```bash
#!/bin/bash
# drive_ingest.sh — Main ingestion orchestrator

DRIVE_MOUNT="/mnt/external_drive"
WORKSPACE="/home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
AUDIT_DIR="$WORKSPACE/00_INCOMING/drive_audit_$TIMESTAMP"

# Step 1: Pre-flight
./scripts/01_preflight.sh "$DRIVE_MOUNT" "$AUDIT_DIR" || exit 1

# Step 2: Audit scan
./scripts/02_audit_scan.sh "$DRIVE_MOUNT" "$AUDIT_DIR"

# Step 3: Duplicate detection
./scripts/03_duplicate_check.sh "$DRIVE_MOUNT" "$AUDIT_DIR"

# Step 4: Report generation
./scripts/04_generate_report.sh "$AUDIT_DIR"

# Step 5: USER APPROVAL GATE
echo "Review report at: $AUDIT_DIR/report.pdf"
read -p "Proceed with transfer? (yes/no): " APPROVAL
if [ "$APPROVAL" != "yes" ]; then
    echo "Transfer cancelled by user"
    exit 0
fi

# Step 6: Transfer
./scripts/05_transfer.sh "$DRIVE_MOUNT" "$AUDIT_DIR"

# Step 7: Integrity check
./scripts/06_integrity_check.sh "$AUDIT_DIR"

# USER APPROVAL GATE 2
read -p "Integrity check passed. Proceed with organization? (yes/no): " APPROVAL2
if [ "$APPROVAL2" != "yes" ]; then
    echo "Organization cancelled by user"
    exit 0
fi

# Step 8: Organization
./scripts/07_organize.sh "$AUDIT_DIR"

# Step 9: Backup
./scripts/08_backup.sh "$AUDIT_DIR"

# Step 10: Cleanup
./scripts/09_cleanup.sh "$AUDIT_DIR"
```

### B.4 Error Handling and Recovery

| Error Type | Detection | Recovery Action |
|------------|-----------|-----------------|
| Drive disconnect mid-transfer | rclone I/O error | Pause, prompt user to reconnect, resume with --ignore-existing |
| Hash mismatch post-transfer | integrity_check.sh | Flag file, re-transfer single file, log incident |
| Insufficient disk space | Pre-flight check df | Abort immediately, notify user |
| ExifTool timeout | Process timeout > 300s | Skip file, log error, continue with remaining |
| Lightroom catalog locked | SQLite lock error | Retry 3x with 10s delay, then skip catalog update |
| Network failure (cloud backup) | rclone connection error | Retry with exponential backoff, queue for later |

---

## SECTION C — EXISTING LIBRARY RECONCILIATION PLAN

### C.1 One-Time Reconciliation Process Overview

**Objective:** Catalog all 10,000+ existing assets across all drives and locations, reconcile with Lightroom catalogs, identify gaps and duplicates, produce prioritized action plan.

**Estimated Duration:** 8-12 hours for initial scan (can run overnight)  
**Human Time Required:** 2-3 hours for review and decision-making

### C.2 Phase 1: Discovery and Inventory (Automated)

```
Phase 1: DISCOVERY AND INVENTORY
Duration: 4-6 hours for 10k files across multiple drives

Step 1.1: Identify All Storage Locations
├─ Scan /mnt/ for mounted drives
├─ Scan /media/ for user-mounted volumes
├─ Check ~/Pictures/, ~/Photos/, ~/Lightroom/
├─ Check external paths from Lightroom catalog preferences
└─ Output: locations.json (list of all paths to scan)

Step 1.2: Build Master File Inventory
├─ For each location:
│   ├─ Run fd --type file --exec-batch sha256sum
│   ├─ Run ExifTool -json on all images
│   ├─ Run FFprobe on all videos
│   └─ Append to master_inventory.csv
│
├─ master_inventory.csv columns:
│   ├── sha256_hash
│   ├── full_path
│   ├── filename
│   ├── size_bytes
│   ├── file_type (RAW/JPG/VIDEO/OTHER)
│   ├── date_created (EXIF or filesystem)
│   ├── date_modified
│   ├── camera_make
│   ├── camera_model
│   └── location_id (which drive/folder)
│
└─ Output: master_inventory.csv, master_inventory.json

Step 1.3: Generate Inventory Statistics
├─ Total file count by type
├─ Total storage used by type
├─ Date range (earliest to latest capture)
├─ Unique cameras/devices identified
├─ Files per location
└─ Output: inventory_summary.json
```

### C.3 Phase 2: Lightroom Catalog Parsing (Automated)

```
Phase 2: LIGHTROOM CATALOG PARSING
Duration: 1-2 hours depending on catalog count

Step 2.1: Locate All .lrcat Files
├─ Search ~/Lightroom/, ~/Pictures/, Documents/
├─ Search paths from locations.json
└─ Output: catalog_paths.json

Step 2.2: Parse Each Catalog (Python SQLite Parser)
├─ For each catalog.lrcat:
│   ├─ Open as SQLite database
│   ├─ Extract from Adobe_images table:
│   │   ├─ id_file (links to AgLibraryFile)
│   │   ├─ captureTime
│   │   ├─ rating (0-5)
│   │   ├─ hasFlags (picked/rejected)
│   │   └─ fileExtension
│   │
│   ├─ Extract from AgLibraryFile:
│   │   ├─ baseName
│   │   ├─ extension
│   │   └─ id_folder
│   │
│   ├─ Extract from AgLibraryFolder:
│   │   ├─ pathFromRoot
│   │   └─ id_root
│   │
│   ├─ Extract from AgRootFolderList:
│   │   └─ absolutePath
│   │
│   ├─ Extract from KeywordImages + AgKeyword:
│   │   └─ keyword hierarchy
│   │
│   └─ Output: catalog_NAME_images.json
│
└─ Merge all catalogs → all_catalogs_records.json

Step 2.3: Build Catalog Path Database
├─ For each image in all catalogs:
│   ├─ Reconstruct full absolute path
│   │   path = rootFolder.absolutePath + folder.pathFromRoot + file.baseName + file.extension
│   ├─ Store in catalog_path_index.json
│   └─ Include: rating, keywords, collections, flags
│
└─ Output: catalog_path_index.json (master reference)
```

### C.4 Phase 3: Cross-Reference and Gap Analysis (Automated)

```
Phase 3: CROSS-REFERENCE AND GAP ANALYSIS
Duration: 30-60 minutes

Step 3.1: Reconciliation Matrix
├─ Load master_inventory.csv (actual files on disk)
├─ Load catalog_path_index.json (files in Lightroom)
├─ Compare and categorize:
│   │
│   ├─ Category A: In Catalog AND On Disk ✅
│   │   └─ Path matches, file exists
│   │
│   ├─ Category B: In Catalog BUT Missing From Disk ⚠️
│   │   └─ Lightroom reference broken (file moved/deleted)
│   │
│   ├─ Category C: On Disk BUT Not In Any Catalog ⚠️
│   │   └─ Orphaned files (never imported or removed from catalog)
│   │
│   └─ Category D: Duplicate Hashes ⚠️
│       └─ Same SHA256, different paths (exact duplicates)
│
└─ Output: reconciliation_matrix.json

Step 3.2: Detailed Analysis per Category

Category B (Missing Files):
├─ Count: X files missing
├─ Group by original folder location
├─ Check if files exist elsewhere (hash match in Category C)
├─ Possible causes:
│   ├─ File moved but not updated in Lightroom
│   ├─ File deleted from disk
│   └─ Drive no longer mounted
└─ Output: missing_files_report.csv

Category C (Orphaned Files):
├─ Count: Y files not in any catalog
├─ Group by location/folder
├─ Check EXIF dates — are these new imports?
├─ Check if these are exports/derivatives (should not be in catalog)
├─ Possible causes:
│   ├─ Never imported to Lightroom
│   ├─ Removed from catalog accidentally
│   ├─ Exports from Lightroom (EDITED folder)
│   └─ Screenshots/phone photos (not meant for catalog)
└─ Output: orphaned_files_report.csv

Category D (Duplicates):
├─ Group by SHA256 hash
├─ For each duplicate set:
│   ├─ Identify which copy is in Lightroom catalog
│   ├─ Identify which copy is in "correct" location per naming convention
│   ├─ Flag others for deletion/archive
│   └─ Calculate space recoverable
└─ Output: duplicates_report.csv

Step 3.3: Generate Reconciliation Report
├─ Executive summary (totals, percentages)
├─ Category breakdown with counts
├─ Storage impact analysis
├─ Prioritized action items
├─ Estimated time to resolve each category
└─ Output: reconciliation_report.pdf + .html
```

### C.5 Phase 4: Prioritized Action Plan

```
RECONCILIATION ACTION PLAN — Priority Order

Priority 1: CRITICAL — Missing Files (Category B)
├─ Action: Locate or mark as lost
├─ Steps:
│   1. Search all drives for hash matches (may have been moved)
│   2. If found: update Lightroom folder location
│   3. If not found: mark as "Missing" in Lightroom (do not delete catalog entry)
│   4. Document in missing_files_log.csv
├─ Estimated effort: 1-2 hours
└─ Automation: Hash search script, Lightroom folder update script

Priority 2: HIGH — Orphaned Files (Category C)
├─ Action: Import or archive
├─ Steps:
│   1. Filter out EDITED/ exports and SCREENSHOTS/ (exclude from import)
│   2. Review remaining orphaned files
│   3. Import valid photos to Lightroom (add to appropriate catalog)
│   4. Apply naming convention during import
│   5. Move to correct folder structure
├─ Estimated effort: 2-4 hours (depending on count)
└─ Automation: ExifTool rename, Lightroom import script

Priority 3: MEDIUM — Duplicates (Category D)
├─ Action: Consolidate and remove
├─ Steps:
│   1. For each duplicate set, keep copy in "correct" location
│   2. Ensure kept copy is referenced in Lightroom
│   3. Move other copies to archive (do not delete immediately)
│   4. After 30-day review, delete archived duplicates
│   5. Update Lightroom if any catalog references changed
├─ Estimated effort: 1-2 hours
├─ Space recoverable: Estimate 10-20% of library
└─ Automation: rdfind for identification, rclone for archival

Priority 4: LOW — Catalog Consolidation
├─ Action: Merge multiple catalogs if desired
├─ Steps:
│   1. Review existing catalog structure
│   2. Decide: single master catalog vs project-based
│   3. If consolidating: use Lightroom's "Merge Catalogs" feature
│   4. Backup all catalogs before merge
│   5. Test merged catalog thoroughly
├─ Estimated effort: 2-3 hours
└─ Automation: Manual Lightroom operation (no safe automation)
```

### C.6 Reconciliation Script Structure

```python
#!/usr/bin/env python3
# reconcile_library.py — Main reconciliation orchestrator

import sqlite3
import json
import csv
import hashlib
from pathlib import Path

class LibraryReconciler:
    def __init__(self, workspace_root):
        self.root = Path(workspace_root)
        self.inventory = []
        self.catalog_records = []
        self.reconciliation = {
            'category_a': [],  # In catalog + on disk
            'category_b': [],  # In catalog, missing from disk
            'category_c': [],  # On disk, not in catalog
            'category_d': []   # Duplicates
        }
    
    def build_inventory(self, locations):
        """Scan all locations, build master inventory CSV"""
        # Implementation: fd + sha256sum + ExifTool
        pass
    
    def parse_catalogs(self, catalog_paths):
        """Parse all .lrcat files using SQLite"""
        for catalog_path in catalog_paths:
            conn = sqlite3.connect(f"file:{catalog_path}?mode=ro", uri=True)
            # Extract from Adobe_images, AgLibraryFile, AgLibraryFolder, AgRootFolderList
            # Append to self.catalog_records
            conn.close()
    
    def cross_reference(self):
        """Compare inventory vs catalog, populate reconciliation categories"""
        # Build hash index from inventory
        # Build path index from catalog
        # Compare and categorize
        pass
    
    def detect_duplicates(self):
        """Find files with identical SHA256 hashes"""
        # Group inventory by hash
        # Flag groups with count > 1
        pass
    
    def generate_report(self):
        """Generate reconciliation_report.pdf and .csv files"""
        # Use Jinja2 + WeasyPrint for PDF
        # Export CSVs for each category
        pass
    
    def generate_action_plan(self):
        """Generate prioritized_action_plan.md"""
        # Priority 1-4 actions with estimates
        pass

if __name__ == '__main__':
    reconciler = LibraryReconciler('/home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer')
    reconciler.build_inventory(['/mnt/drive1', '/mnt/drive2', '~/Pictures'])
    reconciler.parse_catalogs(['~/Lightroom/Master_Catalog.lrcat'])
    reconciler.cross_reference()
    reconciler.detect_duplicates()
    reconciler.generate_report()
    reconciler.generate_action_plan()
```

### C.7 Expected Outputs

| File | Format | Purpose |
|------|--------|---------|
| `master_inventory.csv` | CSV | Complete file listing with hashes |
| `catalog_path_index.json` | JSON | All catalog references with metadata |
| `reconciliation_matrix.json` | JSON | Category assignments for all files |
| `missing_files_report.csv` | CSV | Category B files (in catalog, missing) |
| `orphaned_files_report.csv` | CSV | Category C files (on disk, not in catalog) |
| `duplicates_report.csv` | CSV | Category D files (exact duplicates) |
| `reconciliation_report.pdf` | PDF | Visual report with charts and summaries |
| `prioritized_action_plan.md` | Markdown | Step-by-step remediation plan |

---

## SECTION D — BACKUP ARCHITECTURE — 3-2-1 IMPLEMENTATION

### D.1 3-2-1 Strategy Definition

**3 Copies:**
1. **Primary:** Master library on main workstation (`/media_library/`)
2. **Local Backup:** External drive/NAS (`05_BACKUPS/` mirror)
3. **Offsite Backup:** Cloud storage (Cloudflare R2 or Backblaze B2)

**2 Media Types:**
1. **Primary + Local:** Internal/external HDD or SSD
2. **Offsite:** Cloud object storage (S3-compatible)

**1 Offsite:**
- Cloudflare R2 (preferred) or Backblaze B2
- Geographically separate from primary location

### D.2 Backup Location Specifications

| Copy | Location | Media Type | Capacity | Cost | Access Speed |
|------|----------|------------|----------|------|--------------|
| Primary | `/media_library/` (workstation) | NVMe SSD / HDD | 2-4 TB | $0 (existing) | Instant |
| Local Backup | `/mnt/backup_drive/05_BACKUPS/` | External HDD | 4-8 TB | $100-150 (one-time) | USB 3.0 (100 MB/s) |
| Offsite | Cloudflare R2 bucket | Cloud object storage | Unlimited | $0.015/GB/month | Internet (variable) |

### D.3 Sync Frequency and Triggers

| Backup Layer | Frequency | Trigger | Tool |
|--------------|-----------|---------|------|
| Primary → Local | Daily (incremental) | Cron job at 02:00 | rclone sync |
| Primary → Local | Weekly (full snapshot) | Sunday 03:00 | rclone copy to weekly/ |
| Primary → Local | Monthly (archive) | 1st of month 04:00 | rclone copy to monthly/ |
| Primary → Cloud | Weekly (incremental) | Sunday 04:00 | rclone sync |
| Primary → Cloud | Monthly (archive) | 1st of month 05:00 | rclone copy with versioning |
| Post-Ingestion | Immediate | After each drive ingest | rclone copy (manual trigger) |

### D.4 Verification at Each Layer

```
VERIFICATION PROTOCOL

Layer 1: Primary → Local Backup
├─ Verification Method: rclone --checksum
├─ Process:
│   1. rclone computes MD5/SHA1 of source files
│   2. Transfers files to destination
│   3. rclone computes hash of destination files
│   4. Compares source vs destination hashes
│   5. Logs mismatches, retries failed transfers
│
├─ Verification Log: 07_LOGS/backups/local_backup_YYYYMMDD.log
├─ Success Criteria: 100% hash match
└─ Failure Action: Retry up to 3x, alert user if persistent

Layer 2: Primary → Cloud Backup
├─ Verification Method: rclone --checksum + cloud ETag
├─ Process:
│   1. rclone computes hash before upload
│   2. Uploads to R2/B2 with server-side encryption
│   3. Cloud provider returns ETag (hash of uploaded object)
│   4. rclone compares local hash vs ETag
│   5. Logs mismatches, re-uploads failed files
│
├─ Verification Log: 07_LOGS/backups/cloud_backup_YYYYMMDD.log
├─ Success Criteria: 100% ETag match
└─ Failure Action: Retry with exponential backoff, queue for next run

Layer 3: Monthly Integrity Audit
├─ Frequency: First Sunday of each month
├─ Process:
│   1. Random sample 5% of backed-up files (minimum 100 files)
│   2. Download from cloud backup to temp location
│   3. Compare hash against primary copy
│   4. Verify local backup hashes match primary
│   5. Generate integrity_audit_report.pdf
│
├─ Success Criteria: 100% sample match
└─ Failure Action: Full backup verification, re-sync affected files
```

### D.5 Initial Upload Strategy for 10k+ Files

**Challenge:** Initial cloud upload of 500GB-2TB can take days/weeks depending on bandwidth.

**Strategy: Phased Upload with Prioritization**

```
Phase 1: Critical Assets (Week 1)
├─ Files: Last 12 months of work (client deliverables, recent shoots)
├─ Estimated size: 100-200 GB
├─ Priority: Highest
├─ Bandwidth allocation: 80% of available upload
└─ Command: rclone copy --include-from recent_12months.txt

Phase 2: Working Library (Week 2-3)
├─ Files: 1-3 years old (active projects, reference material)
├─ Estimated size: 200-400 GB
├─ Priority: Medium
├─ Bandwidth allocation: 50% of available upload
└─ Command: rclone copy --include-from working_library.txt

Phase 3: Archive (Week 4-6)
├─ Files: 3+ years old (historical archive)
├─ Estimated size: Remaining library
├─ Priority: Low
├─ Bandwidth allocation: 30% of available upload (overnight only)
└─ Command: rclone copy --include-from archive.txt

Phase 4: Ongoing Sync (After initial upload complete)
├─ Incremental syncs only (changed/new files)
├─ Run weekly on Sunday 04:00
├─ Bandwidth allocation: 100% (small transfer volume)
└─ Command: rclone sync --checksum
```

**Bandwidth Management:**
```bash
# rclone bandwidth limits (adjust based on connection)
# Format: --bwlimit "HH:MM-UploadKBs,HH:MM-UploadKBs"

# Business hours (limit to 500 KB/s = 4 Mbps)
--bwlimit "08:00-500K,18:00-500K"

# Overnight (unlimited)
--bwlimit "18:00-0,08:00-0"

# Weekend (unlimited)
# Set manually or use cron with different bwlimit
```

### D.6 Ongoing Health Monitoring

```
HEALTH MONITORING SYSTEM

Daily Checks (Automated, 02:30)
├─ Check 1: Local backup completed successfully
│   └─ Parse 07_LOGS/backups/local_backup_*.log for errors
│
├─ Check 2: Disk space on backup drive > 20% free
│   └─ df /mnt/backup_drive, alert if < 20%
│
├─ Check 3: rclone config valid (cloud credentials)
│   └─ rclone lsd myr2: (test connection)
│
└─ Output: daily_health_check.json

Weekly Checks (Automated, Sunday 06:00)
├─ Check 1: Cloud backup completed successfully
│   └─ Parse 07_LOGS/backups/cloud_backup_*.log
│
├─ Check 2: Backup delta (new files not yet backed up)
│   └─ Compare primary vs backup file counts
│
├─ Check 3: Backup age (oldest file not backed up)
│   └─ Alert if any file > 7 days old not backed up
│
└─ Output: weekly_health_report.pdf

Monthly Checks (Automated, 1st of month 08:00)
├─ Check 1: Integrity audit (random sample verification)
│   └─ Download 5% sample, verify hashes
│
├─ Check 2: Storage cost projection
│   └─ Calculate current cloud storage cost
│   └─ Project 12-month cost based on growth rate
│
├─ Check 3: Backup retention policy enforcement
│   └─ Delete daily backups > 7 days old
│   └─ Delete weekly backups > 4 weeks old
│   └─ Delete monthly backups > 12 months old
│
└─ Output: monthly_backup_audit.pdf

Alert Channels
├─ Email: zalabany3@gmail.com (critical failures only)
├─ Telegram: Bot notification (daily summary)
└─ Log file: 07_LOGS/health_monitor.log
```

### D.7 rclone Configuration

```ini
# ~/.config/rclone/rclone.conf

[myr2]
type = s3
provider = Cloudflare
access_key_id = YOUR_R2_ACCESS_KEY
secret_access_key = YOUR_R2_SECRET_KEY
region = auto
endpoint = https://YOUR_ACCOUNT_ID.r2.cloudflarestorage.com
acl = private
versioning = true

[myb2]
type = b2
account = YOUR_BACKBLAZE_ACCOUNT
key = YOUR_BACKBLAZE_KEY
bucket = your-backup-bucket
versioning = true

[local_backup]
type = local
```

### D.8 Backup Scripts

```bash
#!/bin/bash
# backup_daily.sh — Daily incremental backup

SOURCE="/media_library/"
LOCAL_DEST="/mnt/backup_drive/05_BACKUPS/daily/"
CLOUD_DEST="myr2:media-backup/"
LOG_DIR="/home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer/07_LOGS/backups/"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Local backup
rclone sync "$SOURCE" "$LOCAL_DEST" \
    --checksum \
    --transfers=8 \
    --checkers=16 \
    --log-file="$LOG_DIR/local_backup_$TIMESTAMP.log" \
    --log-level=INFO \
    --stats=1m

# Cloud backup (weekly only, check day of week)
if [ $(date +%u) -eq 7 ]; then  # Sunday
    rclone sync "$SOURCE" "$CLOUD_DEST" \
        --checksum \
        --transfers=4 \
        --bwlimit "18:00-0,08:00-0" \
        --log-file="$LOG_DIR/cloud_backup_$TIMESTAMP.log" \
        --log-level=INFO \
        --stats=1m
fi

# Health check
./scripts/health_check.sh >> "$LOG_DIR/health_monitor.log"
```

---

## SECTION E — REPORTING SYSTEM

### E.1 Report Types and Schedules

| Report Type | Frequency | Format | Audience | Purpose |
|-------------|-----------|--------|----------|---------|
| Per-Drive Audit | Per ingest | PDF + HTML | User | Review before transfer |
| Transfer Summary | Per ingest | PDF + CSV | User | Confirm successful transfer |
| Monthly Library Summary | Monthly | PDF + HTML | User | Library health overview |
| Asset Ingestion Log | Continuous | CSV | System | Running record of all transfers |
| Reconciliation Report | One-time | PDF + CSV | User | Existing library analysis |
| Backup Health Report | Weekly | PDF | User | Backup status verification |
| Quarterly Archive Report | Quarterly | PDF | User | Long-term storage review |

### E.2 Per-Drive Audit Report Template

```
═══════════════════════════════════════════════════════════════════════════════
                           DRIVE AUDIT REPORT
═══════════════════════════════════════════════════════════════════════════════

Drive Information
─────────────────
  Mount Point:      /mnt/external_drive
  Drive Model:      Samsung T7 Shield
  Serial Number:    S1234567890
  Capacity:         2.0 TB
  Filesystem:       exFAT
  Audit Date:       2026-03-03 20:07 MST

File Inventory
──────────────
  Total Files:      1,247
  Total Size:       156.3 GB

  By Type:
    ┌──────────────┬─────────┬────────────┐
    │ Type         │ Count   │ Size       │
    ├──────────────┼─────────┼────────────┤
    │ RAW (CR2)    │   423   │  84.6 GB   │
    │ RAW (ARW)    │   112   │  22.4 GB   │
    │ JPEG         │   589   │  35.2 GB   │
    │ Video (MP4)  │    98   │  12.8 GB   │
    │ Video (MOV)  │    25   │   1.3 GB   │
    └──────────────┴─────────┴────────────┘

Date Range
──────────
  Earliest Capture:  2024-06-15 (Wedding_Johnson)
  Latest Capture:    2026-02-28 (Portrait_Session_Feb)
  Span:              1 year, 8 months

Duplicate Analysis
──────────────────
  Exact Duplicates Found:  34 files (2.7% of total)
  Space Recoverable:       4.2 GB

  Duplicate Sets:
    ┌────────────────────────────────────────────────────────────────────┐
    │ Hash (first 8)  │ Count  │ Files                                   │
    ├────────────────────────────────────────────────────────────────────┤
    │ a3f5c8d2        │   2    │ IMG_1234.CR2, Backup/IMG_1234.CR2       │
    │ b7e2f1a9        │   2    │ DSC_5678.NEF, Old_Drive/DSC_5678.NEF    │
    │ ...             │  ...   │ ...                                     │
    └────────────────────────────────────────────────────────────────────┘

Recommended Actions
───────────────────
  ✅ TRANSFER:     1,213 files (152.1 GB)
     → New files not in library

  ⚠️ REVIEW:       34 files (4.2 GB)
     → Exact duplicates — confirm before transfer

  ⏸️ SKIP:         0 files
     → Already in library (verified by hash)

Next Steps
──────────
  1. Review duplicate list above
  2. Confirm transfer approval (run: ./approve_transfer.sh audit_20260303_200700)
  3. Transfer will begin after approval

═══════════════════════════════════════════════════════════════════════════════
Report generated by MediaAuditOrganizer v1.0
Full data: /path/to/00_INCOMING/drive_audit_20260303_200700/
═══════════════════════════════════════════════════════════════════════════════
```

### E.3 Monthly Library Summary Template

```
═══════════════════════════════════════════════════════════════════════════════
                      MONTHLY LIBRARY SUMMARY
                         February 2026
═══════════════════════════════════════════════════════════════════════════════

Executive Summary
─────────────────
  Reporting Period:    2026-02-01 to 2026-02-28
  Library Status:      ✅ Healthy
  Total Assets:        12,847 files
  Total Storage:       1.84 TB
  Month-over-Month:    +234 files (+1.8%), +42.3 GB (+2.4%)

Asset Growth
────────────
  New Assets This Month:     234 files
    ├── Photos:              198 files (156 RAW, 42 JPG)
    └── Videos:              36 files

  Assets by Type (Total Library):
    ┌──────────────┬─────────┬────────────┬──────────┐
    │ Type         │ Count   │ Size       │ % of Lib │
    ├──────────────┼─────────┼────────────┼──────────┤
    │ RAW          │  6,234  │  1.24 TB   │   67.4%  │
    │ JPEG         │  4,891  │  298 GB    │   16.2%  │
    │ Video        │  1,522  │  267 GB    │   14.5%  │
    │ Other        │    200  │   35 GB    │    1.9%  │
    └──────────────┴─────────┴────────────┴──────────┘

Storage Usage
─────────────
  Primary Storage (/media_library/):
    ├── Used:      1.84 TB
    ├── Available: 2.16 TB
    └── Capacity:  4.00 TB (46% used)

  Local Backup (/mnt/backup_drive/):
    ├── Used:      1.82 TB
    ├── Available: 6.18 TB
    └── Capacity:  8.00 TB (23% used)

  Cloud Backup (Cloudflare R2):
    ├── Used:      1.79 TB
    ├── Monthly Cost: $26.85 USD
    └── Versioning: Enabled (30-day retention)

Backup Health
─────────────
  Last Local Backup:   2026-03-03 02:15 MST ✅ Success
  Last Cloud Backup:   2026-03-02 04:30 MST ✅ Success
  Backup Lag:          0 files (all files backed up within 24h)

  Integrity Audit (Monthly):
    ├── Sample Size:   128 files (1% of library)
    ├── Verification:  100% hash match
    └── Status:        ✅ All backups verified

Warnings and Alerts
───────────────────
  ⚠️ None — All systems healthy

Activity Log Summary
────────────────────
  Drive Ingests:       3 drives processed
  Files Transferred:   234 files
  Duplicates Removed:  12 files (1.8 GB recovered)
  Catalog Updates:     3 imports to Master_Catalog.lrcat

Upcoming Tasks
──────────────
  □ March 1: Monthly backup archive (automated)
  □ March 1: Integrity audit (automated)
  □ March 15: Quarterly review (manual)

═══════════════════════════════════════════════════════════════════════════════
Report generated: 2026-03-03 20:07 MST
Next report: 2026-04-01
═══════════════════════════════════════════════════════════════════════════════
```

### E.4 Asset Ingestion Log (CSV Format)

```csv
# asset_ingestion_log.csv — Running log of every file transferred
# Columns: timestamp,source_path,dest_path,filename,file_type,size_bytes,sha256_hash,source_drive,exif_date,camera_model,status

timestamp,source_path,dest_path,filename,file_type,size_bytes,sha256_hash,source_drive,exif_date,camera_model,status
2026-03-03T20:15:22,/mnt/drive1/DCIM/100CANON,/media_library/01_PHOTOS/2025/2025-03_Wedding_Johnson/RAW,20250315_143022_D850_001.CR2,RAW,31457280,a3f5c8d2e5f7b9c1d3e5f7a9b1c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9,drive1,2025-03-15T14:30:22,Nikon D850,success
2026-03-03T20:15:23,/mnt/drive1/DCIM/100CANON,/media_library/01_PHOTOS/2025/2025-03_Wedding_Johnson/JPG,20250315_143022_D850_001.JPG,JPG,8388608,b7e2f1a9c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7,drive1,2025-03-15T14:30:22,Nikon D850,success
2026-03-03T20:15:24,/mnt/drive1/DCIM/101CANON,/media_library/02_VIDEOS/2025/2025-03_Wedding_Johnson/ORIGINAL,20250315_143000_D850_4K_30fps_001.MP4,VIDEO,524288000,c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1,drive1,2025-03-15T14:30:00,Nikon D850,success
...
```

### E.5 Report Generation Implementation

```python
#!/usr/bin/env python3
# generate_reports.py — Report generation engine

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import json
import csv
from datetime import datetime
from pathlib import Path

class ReportGenerator:
    def __init__(self, workspace_root):
        self.root = Path(workspace_root)
        self.templates = self.root / 'templates' / 'reports'
        self.output = self.root / '08_REPORTS'
        self.env = Environment(loader=FileSystemLoader(self.templates))
    
    def load_audit_data(self, audit_dir):
        """Load audit data from JSON/CSV files"""
        with open(audit_dir / 'manifest.json') as f:
            manifest = json.load(f)
        with open(audit_dir / 'duplicates.json') as f:
            duplicates = json.load(f)
        return {'manifest': manifest, 'duplicates': duplicates}
    
    def generate_per_drive_report(self, audit_dir):
        """Generate per-drive audit report (PDF + HTML)"""
        data = self.load_audit_data(audit_dir)
        template = self.env.get_template('per_drive_audit.html')
        html = template.render(
            data=data,
            generated=datetime.now().strftime('%Y-%m-%d %H:%M MST')
        )
        
        # Save HTML
        html_path = self.output / 'per_drive' / f"audit_{audit_dir.name}.html"
        html_path.write_text(html)
        
        # Generate PDF
        pdf_path = self.output / 'per_drive' / f"audit_{audit_dir.name}.pdf"
        HTML(string=html).write_pdf(pdf_path)
        
        return {'html': html_path, 'pdf': pdf_path}
    
    def generate_monthly_summary(self, year, month):
        """Generate monthly library summary"""
        # Aggregate data from ingestion log
        # Calculate statistics
        # Generate report
        pass
    
    def append_to_ingestion_log(self, transfer_records):
        """Append transfer records to master ingestion log CSV"""
        log_path = self.root / '06_METADATA' / 'asset_ingestion_log.csv'
        
        # Create header if file doesn't exist
        if not log_path.exists():
            with open(log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'source_path', 'dest_path', 'filename',
                    'file_type', 'size_bytes', 'sha256_hash', 'source_drive',
                    'exif_date', 'camera_model', 'status'
                ])
        
        # Append records
        with open(log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            for record in transfer_records:
                writer.writerow([
                    record['timestamp'], record['source_path'],
                    record['dest_path'], record['filename'],
                    record['file_type'], record['size_bytes'],
                    record['sha256_hash'], record['source_drive'],
                    record['exif_date'], record['camera_model'],
                    record['status']
                ])
```

### E.6 Report Templates Directory Structure

```
/home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer/templates/reports/
├── per_drive_audit.html      # Per-drive audit template
├── monthly_summary.html      # Monthly library summary template
├── reconciliation.html       # Reconciliation report template
├── backup_health.html        # Backup health report template
├── css/
│   └── reports.css           # Shared styles for all reports
└── partials/
    ├── header.html           # Report header (logo, title, date)
    ├── footer.html           # Report footer (generated by, page numbers)
    ├── file_table.html       # Reusable file listing table
    └── chart_container.html  # Placeholder for embedded charts
```

---

## SECTION F — LIGHTROOM INTEGRATION STRATEGY

### F.1 Metadata Extraction from Existing Catalogs

**Objective:** Extract all metadata from existing .lrcat catalogs before any file moves/renames to preserve ratings, keywords, collections, and develop settings.

**Extraction Scope:**
| Metadata Type | Table(s) | Priority | Notes |
|---------------|----------|----------|-------|
| Ratings | Adobe_images.rating | High | 0-5 star ratings |
| Flags | Adobe_images.hasFlags, pickFlags | High | Picked/rejected status |
| Keywords | KeywordImages, AgKeyword | High | Hierarchical keyword structure |
| Collections | AgLibraryCollection, AgCollectionImage | Medium | Smart + manual collections |
| Labels | Adobe_images.colorLabels | Medium | Color labels (red, yellow, etc.) |
| Develop Settings | ImageDevelopSettings | Medium | All develop module adjustments |
| Crop/Transform | ImageDevelopSettings.crop* | Low | Crop rectangle, rotation |
| Presets Applied | ImageDevelopSettings.processVersion | Low | Preset names/versions |
| File Paths | AgLibraryFile, AgLibraryFolder, AgRootFolderList | Critical | For path reconciliation |

**Extraction Script:**
```python
#!/usr/bin/env python3
# extract_catalog_metadata.py — Extract all metadata from .lrcat

import sqlite3
import json
from pathlib import Path

def extract_catalog_metadata(catalog_path):
    """Extract complete metadata from Lightroom catalog"""
    conn = sqlite3.connect(f"file:{catalog_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    metadata = {
        'catalog_path': str(catalog_path),
        'images': [],
        'keywords': [],
        'collections': [],
        'folders': []
    }
    
    # Extract images with all metadata
    cursor.execute('''
        SELECT 
            img.id AS image_id,
            img.captureTime,
            img.rating,
            img.hasFlags,
            img.pickFlags,
            img.colorLabels,
            file.baseName,
            file.extension,
            folder.pathFromRoot,
            root.absolutePath,
            dev.cropTop,
            dev.cropLeft,
            dev.cropBottom,
            dev.cropRight,
            dev.processVersion
        FROM Adobe_images img
        JOIN AgLibraryFile file ON img.id_file = file.id
        JOIN AgLibraryFolder folder ON file.id_folder = folder.id
        JOIN AgRootFolderList root ON folder.id_root = root.id
        LEFT JOIN ImageDevelopSettings dev ON img.id = dev.id
    ''')
    
    for row in cursor.fetchall():
        metadata['images'].append(dict(row))
    
    # Extract keywords
    cursor.execute('''
        SELECT 
            kw.name,
            kw.parent,
            ki.id_image
        FROM AgKeyword kw
        JOIN KeywordImages ki ON kw.id = ki.id_keyword
    ''')
    
    for row in cursor.fetchall():
        metadata['keywords'].append(dict(row))
    
    # Extract collections
    cursor.execute('''
        SELECT 
            coll.name,
            coll.collectionType,
            ci.id_image
        FROM AgLibraryCollection coll
        JOIN AgCollectionImage ci ON coll.id = ci.id_collection
    ''')
    
    for row in cursor.fetchall():
        metadata['collections'].append(dict(row))
    
    conn.close()
    
    # Save to JSON
    output_path = catalog_path.parent / f"{catalog_path.stem}_metadata.json"
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata

# Usage
catalog = Path('/home/az/Lightroom/Master_Catalog.lrcat')
metadata = extract_catalog_metadata(catalog)
print(f"Extracted {len(metadata['images'])} images with metadata")
```

### F.2 Folder Reference Migration Strategy

**Problem:** When files are moved/renamed during organization, Lightroom folder references break.

**Solution:** Programmatic folder location update using Lightroom's SDK or SQLite path updates.

**Approach 1: Lightroom SDK (Recommended)**
```lua
-- update_folder_location.lua — Lightroom plugin
-- Run from Lightroom: File > Plugin Manager > Run

local LrApplication = import 'LrApplication'
local LrFileUtils = import 'LrFileUtils'

function updateFolderLocation(oldPath, newPath)
    local catalog = LrApplication.activeCatalog()
    
    -- Find folder by old path
    local folder = catalog:getFolderByPath(oldPath)
    
    if folder then
        -- Update location
        folder:move(newPath)
        print("Updated: " .. oldPath .. " → " .. newPath)
    else
        print("Folder not found: " .. oldPath)
    end
end

-- Batch update from JSON mapping
local pathMapping = require('path_mapping.json')
for oldPath, newPath in pairs(pathMapping) do
    updateFolderLocation(oldPath, newPath)
end
```

**Approach 2: Direct SQLite Update (Advanced, use with caution)**
```python
#!/usr/bin/env python3
# update_catalog_paths.py — Direct catalog path update

import sqlite3
import json

def update_catalog_paths(catalog_path, path_mapping):
    """
    Update folder paths in Lightroom catalog SQLite database.
    
    WARNING: Backup catalog before running. Only use if Lightroom SDK approach fails.
    
    Args:
        catalog_path: Path to .lrcat file
        path_mapping: Dict of {old_path: new_path}
    """
    # Create backup
    backup_path = catalog_path.parent / f"{catalog_path.stem}_backup_{timestamp}.lrcat"
    shutil.copy(catalog_path, backup_path)
    
    conn = sqlite3.connect(catalog_path)
    cursor = conn.cursor()
    
    for old_path, new_path in path_mapping.items():
        # Update AgLibraryFolder.pathFromRoot
        cursor.execute('''
            UPDATE AgLibraryFolder
            SET pathFromRoot = ?
            WHERE pathFromRoot = ?
        ''', (new_path, old_path))
        
        # Update AgRootFolderList.absolutePath if root changed
        cursor.execute('''
            UPDATE AgRootFolderList
            SET absolutePath = ?
            WHERE absolutePath = ?
        ''', (new_path, old_path))
    
    conn.commit()
    conn.close()
    
    print(f"Updated {len(path_mapping)} folder paths")
    print(f"Backup saved to: {backup_path}")
```

**Path Mapping File Format:**
```json
{
  "/old/drive/path/Photos/2025/Wedding_Johnson": "/media_library/01_PHOTOS/2025/2025-03_Wedding_Johnson",
  "/old/drive/path/Videos/2025": "/media_library/02_VIDEOS/2025"
}
```

### F.3 Consolidate vs Project-Based Catalogs Decision

**Decision Matrix:**

| Factor | Single Master Catalog | Project-Based Catalogs | Recommendation |
|--------|----------------------|------------------------|----------------|
| Library Size | < 50,000 images | Any size | Master for < 50k |
| Performance | Slight slowdown at 100k+ | Consistent | Project for > 50k |
| Search Across Projects | ✅ Excellent | ⚠️ Requires multiple catalogs | Master |
| Backup/Transfer | Single file | Multiple files | Master |
| Collaboration | ⚠️ Single user only | ✅ Can share project catalogs | Project |
| Risk | Single point of failure | Distributed risk | Project |
| Portability | Large file (~GB) | Smaller files | Project |

**Recommendation for AZ's Workflow:**

Given 10,000+ assets (growing), use **Hybrid Approach:**

```
Catalog Structure:
├── Master_Catalog.lrcat
│   └─ Primary catalog for all work 2024-present
│   └─ Contains all images, keywords, collections
│   └─ Used for daily work and searching
│
├── Archive_Catalogs/
│   ├── 2020-2023_Archive.lrcat
│   │   └─ Historical work (read-only)
│   │   └─ Backed up, rarely opened
│   │
│   └── Pre-2020_Archive.lrcat
│       └─ Legacy work (read-only)
│
└── Project_Catalogs/ (optional, for large client projects)
    ├── ClientName_Wedding_2026.lrcat
    │   └─ Temporary catalog for active project
    │   └─ Merged to Master_Catalog on project completion
    │
    └── Commercial_Project_X.lrcat
        └─ Isolated for client delivery
```

**Merge Workflow:**
1. Work in project catalog during active project
2. On completion: File > Export as Catalog (with negatives)
3. Import into Master_Catalog: File > Import from Another Catalog
4. Verify all metadata transferred
5. Archive project catalog (do not delete for 30 days)

### F.4 Watched Folders for Auto-Import

**Setup:** Configure Lightroom auto-import for `00_INCOMING/pending_review/` folder.

**Lightroom Auto-Import Configuration:**
```
File > Auto Import > Auto Import Settings...

Watched Folder: /media_library/00_INCOMING/pending_review/
Destination:    /media_library/01_PHOTOS/YYYY/YYYY-MM_EventName/
File Naming:    Custom (based on EXIF — use ExifTool pre-rename)

Options:
  ✅ Add to minimal catalog (for review)
  ✅ Build previews (Standard)
  ✅ Apply develop preset (if desired)
  ✅ Add keywords (auto from folder name)
  ⏸️ Do not import duplicates (by filename)
```

**Automation Script:**
```bash
#!/bin/bash
# trigger_lightroom_import.sh — Trigger Lightroom auto-import

WATCHED_FOLDER="/media_library/00_INCOMING/pending_review/"

# Check if files exist in watched folder
if [ $(find "$WATCHED_FOLDER" -type f | wc -l) -gt 0 ]; then
    # Touch a trigger file to wake Lightroom watcher
    touch "$WATCHED_FOLDER/.import_trigger"
    
    # Log
    echo "$(date): Import triggered for $WATCHED_FOLDER" >> 07_LOGS/lightroom_import.log
else
    echo "$(date): No files to import" >> 07_LOGS/lightroom_import.log
fi
```

**Caveats:**
- Lightroom must be running for auto-import to work
- Alternative: Use `lr-cli` or AppleScript to trigger import programmatically
- For headless/server setups: Use digiKam instead (has CLI import)

### F.5 Keeping LR Folder Structure Synced with Master Library

**Challenge:** Lightroom maintains its own folder tree, which can drift from actual disk structure.

**Sync Strategy:**

```
SYNC WORKFLOW (Run monthly or after major reorganization)

Step 1: Export Lightroom Folder Structure
├─ Run catalog parser to extract current folder tree
├─ Save to lr_folder_tree.json
└─ Format: {folder_path: [image_count, last_modified]}

Step 2: Scan Actual Disk Structure
├─ Run fd on /media_library/01_PHOTOS/ and 02_VIDEOS/
├─ Save to disk_folder_tree.json
└─ Format: {folder_path: [file_count, total_size]}

Step 3: Compare and Identify Drift
├─ Folders in LR but not on disk → Missing files (Category B)
├─ Folders on disk but not in LR → Orphaned (Category C)
├─ Folder names differ → Rename drift

Step 4: Resolution Actions
├─ For missing folders: Remove from Lightroom (File > Remove from Catalog)
├─ For orphaned folders: Import to Lightroom (File > Import)
├─ For renamed folders: Update folder location in Lightroom

Step 5: Verification
├─ Re-run comparison
├─ Confirm 100% match
└─ Log sync completion
```

**Sync Script:**
```python
#!/usr/bin/env python3
# sync_lightroom_folders.py — Sync LR folder tree with disk

import json
from pathlib import Path
import sqlite3

class LightroomFolderSync:
    def __init__(self, catalog_path, library_root):
        self.catalog_path = Path(catalog_path)
        self.library_root = Path(library_root)
    
    def get_lr_folders(self):
        """Extract folder structure from Lightroom catalog"""
        conn = sqlite3.connect(f"file:{self.catalog_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT root.absolutePath || folder.pathFromRoot as full_path,
                   COUNT(file.id) as file_count
            FROM AgLibraryFolder folder
            JOIN AgRootFolderList root ON folder.id_root = root.id
            JOIN AgLibraryFile file ON file.id_folder = folder.id
            GROUP BY full_path
        ''')
        
        folders = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return folders
    
    def get_disk_folders(self):
        """Scan actual disk folder structure"""
        folders = {}
        for photo_dir in (self.library_root / '01_PHOTOS').glob('**/'):
            files = list(photo_dir.glob('*.*'))
            if files:
                folders[str(photo_dir)] = len(files)
        
        for video_dir in (self.library_root / '02_VIDEOS').glob('**/'):
            files = list(video_dir.glob('*.*'))
            if files:
                folders[str(video_dir)] = len(files)
        
        return folders
    
    def compare(self):
        """Compare LR folders vs disk folders"""
        lr_folders = self.get_lr_folders()
        disk_folders = self.get_disk_folders()
        
        drift = {
            'lr_only': set(lr_folders.keys()) - set(disk_folders.keys()),
            'disk_only': set(disk_folders.keys()) - set(lr_folders.keys()),
            'mismatched_counts': []
        }
        
        for path in set(lr_folders.keys()) & set(disk_folders.keys()):
            if lr_folders[path] != disk_folders[path]:
                drift['mismatched_counts'].append({
                    'path': path,
                    'lr_count': lr_folders[path],
                    'disk_count': disk_folders[path]
                })
        
        return drift
    
    def generate_sync_report(self, drift):
        """Generate report of required sync actions"""
        report = []
        
        if drift['lr_only']:
            report.append("❌ Folders in Lightroom but missing from disk:")
            for path in drift['lr_only']:
                report.append(f"   — {path}")
        
        if drift['disk_only']:
            report.append("📁 Folders on disk but not in Lightroom:")
            for path in drift['disk_only']:
                report.append(f"   — {path}")
        
        if drift['mismatched_counts']:
            report.append("⚠️ File count mismatches:")
            for item in drift['mismatched_counts']:
                report.append(f"   — {item['path']}: LR={item['lr_count']}, Disk={item['disk_count']}")
        
        return '\n'.join(report)

# Usage
sync = LightroomFolderSync(
    '/home/az/Lightroom/Master_Catalog.lrcat',
    '/media_library'
)
drift = sync.compare()
report = sync.generate_sync_report(drift)
print(report)
```

### F.6 Lightroom Integration Checklist

```
LIGHTROOM INTEGRATION CHECKLIST

Pre-Organization:
  □ Backup all .lrcat catalogs (copy to 04_CATALOGS/Archive_Catalogs/)
  □ Run extract_catalog_metadata.py on all catalogs
  □ Save metadata exports to 06_METADATA/catalogs_parsed/
  □ Document current folder structure (lr_folder_tree.json)

During Organization:
  □ Do not open Lightroom while files are being moved/renamed
  □ Complete all file operations before catalog updates
  □ Keep path_mapping.json updated with all moves

Post-Organization:
  □ Run update_catalog_paths.py (or Lightroom SDK script)
  □ Open Lightroom, verify no missing folders
  □ Run sync_lightroom_folders.py to verify alignment
  □ Test search by keyword, rating, date range
  □ Verify collections intact
  □ Verify develop settings preserved

Ongoing Maintenance:
  □ Run monthly folder sync check
  □ Backup catalog after each major import session
  □ Export catalog metadata quarterly (for disaster recovery)
  □ Test catalog integrity annually (File > Optimize Catalog)
```

---

## IMPLEMENTATION TIMELINE

| Phase | Duration | Key Deliverables | Dependencies |
|-------|----------|------------------|--------------|
| **Phase 1: Core Tools** | Week 1-2 | ExifTool, FFprobe, fd, rclone installed and tested | None |
| **Phase 2: Audit Scripts** | Week 2-3 | Drive audit, metadata extraction, duplicate detection | Phase 1 |
| **Phase 3: Lightroom Parser** | Week 3-4 | SQLite catalog parser, metadata extraction | None |
| **Phase 4: Reconciliation** | Week 4-5 | Full library scan, reconciliation report | Phase 2, 3 |
| **Phase 5: Transfer Workflow** | Week 5-6 | rclone scripts, verification, logging | Phase 2 |
| **Phase 6: Backup System** | Week 6-7 | Local + cloud backup configured, automated | Phase 5 |
| **Phase 7: Reports** | Week 7-8 | Jinja2 templates, PDF generation | Phase 2, 5 |
| **Phase 8: Lightroom Integration** | Week 8-9 | Folder sync, path updates, auto-import | Phase 3, 4 |
| **Phase 9: Testing & Validation** | Week 9-10 | Full end-to-end test with sample dataset | All phases |
| **Phase 10: Production Rollout** | Week 10+ | Process existing library, ongoing operations | All phases |

---

## RISK MITIGATION

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Data loss during transfer | Low | Critical | Checksum verification, backup before any operation |
| Lightroom catalog corruption | Low | High | Backup catalogs before any changes, test on copy first |
| Cloud backup cost overrun | Medium | Medium | Monitor monthly, set budget alerts, use R2 (no egress fees) |
| Script bugs causing file loss | Medium | High | Dry-run mode, extensive logging, user confirmation gates |
| Performance issues with 10k+ files | Medium | Low | Test with subsets, optimize scripts, use parallel processing |
| Drive failure during reconciliation | Low | High | Work on copies, never modify source drives directly |

---

**Agent 2 (PLANNER) — Task Complete**

**Files Written:**
- `/home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer/agents/agent_2_plan.md` (this file — technical implementation plan)
- `/home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer/PROJECT_PLAN.md` (user-facing version — see below)

**Next Agent:** Agent 3 (IMPLEMENTOR) should begin Phase 1 implementation based on this plan.
