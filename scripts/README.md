# MediaAuditOrganizer Scripts

Production-ready Python scripts for professional media audit, organization, and backup workflows.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Install system dependencies
brew install exiftool ffmpeg  # macOS
# or
apt install libimage-exiftool-perl ffmpeg  # Linux

# Ingest a new drive (master orchestrator)
python ingest_new_drive.py /mnt/external_drive --project "Wedding_Smith_2026"
```

## Scripts Overview

### 1. `audit_drive.py` — Drive Audit
Scans a drive and captures comprehensive metadata.

```bash
python audit_drive.py /path/to/drive [--output-dir ./reports]
```

**Outputs:**
- `audit_YYYYMMDD_HHMMSS.csv` — Full file manifest
- `audit_YYYYMMDD_HHMMSS.json` — Structured data with statistics

**Captures:**
- Path, filename, extension, size, timestamps
- MD5 and SHA256 hashes
- MIME type
- EXIF data (images): date, camera, GPS, lens, ISO, etc.
- Video metadata: duration, codec, resolution, fps

---

### 2. `generate_report.py` — HTML Report Generator
Creates professional HTML reports from audit data.

```bash
python generate_report.py /path/to/audit.json --project-name "My Project"
```

**Features:**
- Chart.js pie chart (file types)
- Timeline chart (files over time)
- Largest files table
- Files without metadata
- Duplicate groups
- Searchable file manifest

---

### 3. `transfer_assets.py` — Verified File Transfer
Copies files with before/after hash verification.

```bash
python transfer_assets.py /source/path /dest/path [--manifest audit.csv]
```

**Features:**
- SHA256 hash before copy
- SHA256 hash after copy
- Automatic retry (up to 3x)
- Skip existing files with matching hash
- Detailed CSV logging

---

### 4. `backup_verify.py` — Backup Integrity Check
Compares primary and backup locations.

```bash
python backup_verify.py /primary/path /backup/path
```

**Reports:**
- Files missing from backup
- Extra files in backup
- Hash mismatches (corruption)
- Storage statistics at each location

**Exit code:** 1 if mismatches found

---

### 5. `rename_batch.py` — Batch Renaming
Renames files based on EXIF metadata.

```bash
# Preview mode
python rename_batch.py /photos --pattern "{YYYY}{MM}{DD}_{camera_model}_{sequence}" --preview

# Execute mode
python rename_batch.py /photos --pattern "{YYYY}{MM}{DD}_{camera_model}_{sequence}" --execute
```

**Tokens:**
- `{YYYY}`, `{MM}`, `{DD}`, `{HH}`, `{mm}`, `{ss}` — Date/time
- `{camera_make}`, `{camera_model}`, `{lens_model}` — Camera info
- `{sequence}` — Sequential number (3-digit)
- `{original_name}`, `{original_ext}` — Original filename
- `{iso}`, `{focal_length}` — EXIF values

**Features:**
- RAW+JPG pair handling
- Conflict detection
- Preview before execute

---

### 6. `deduplicate.py` — Duplicate Detection
Finds exact and near-duplicate images.

```bash
python deduplicate.py /folder1 /folder2 --lightroom-catalog /path/to/catalog.lrcat
```

**Features:**
- MD5+SHA256 for exact duplicates
- Perceptual hash (pHash) for near-duplicates
- Lightroom catalog presence check
- Interactive HTML report
- Action plan CSV (never auto-deletes)

---

### 7. `lightroom_export_parser.py` — Lightroom Catalog Parser
Extracts data from .lrcat SQLite catalogs.

```bash
python lightroom_export_parser.py /path/to/catalog.lrcat [--scan-paths /path1 /path2]
```

**Extracts:**
- File paths and metadata
- Keywords and hierarchy
- Collections (smart + manual)
- Ratings, flags, color labels
- Develop settings

**Reconciliation:**
- Missing from disk (in catalog but not found)
- Orphans on disk (found but not in catalog)
- Moved paths

---

### 8. `ingest_new_drive.py` — Master Orchestrator
Complete end-to-end drive ingestion workflow.

```bash
python ingest_new_drive.py /mnt/drive --project "Event_Name" [--backup /mnt/backup]
```

**Workflow:**
1. ✅ Audit drive
2. ✅ Generate report
3. ✅ Duplicate check
4. ✅ User confirmation
5. ✅ Rename files
6. ✅ Transfer with verification
7. ✅ Backup verify
8. ✅ Update index
9. ✅ Write summary

---

## Directory Structure

```
MediaAuditOrganizer/
├── scripts/
│   ├── audit_drive.py
│   ├── generate_report.py
│   ├── transfer_assets.py
│   ├── backup_verify.py
│   ├── rename_batch.py
│   ├── deduplicate.py
│   ├── lightroom_export_parser.py
│   ├── ingest_new_drive.py
│   ├── requirements.txt
│   └── README.md
├── logs/              # Operation logs
├── reports/           # Generated reports
├── 00_INCOMING/       # Staging area
├── 01_PHOTOS/         # Master photo library
├── 02_VIDEOS/         # Master video library
├── 04_CATALOGS/       # Lightroom catalogs
└── 06_METADATA/       # Metadata stores
```

## Dependencies

### Python Packages
```bash
pip install -r requirements.txt
```

### System Tools
- **ExifTool** — Metadata extraction
  - macOS: `brew install exiftool`
  - Linux: `apt install libimage-exiftool-perl`
  
- **FFmpeg/FFprobe** — Video metadata
  - macOS: `brew install ffmpeg`
  - Linux: `apt install ffmpeg`

- **SQLite3** — Lightroom parsing (usually pre-installed)

## Logging

All scripts log to `logs/` directory with timestamps:
- `audit_YYYYMMDD_HHMMSS.log`
- `transfer_YYYYMMDD_HHMMSS.log`
- `dedupe_YYYYMMDD_HHMMSS.log`
- etc.

## Error Handling

- Permission errors are logged and skipped gracefully
- Hash computation failures are retried
- Network/IO errors trigger automatic retry (where applicable)
- All errors are logged with full stack traces

## Safety Features

- **No auto-delete** — Deduplication only reports, never deletes
- **Preview mode** — Rename shows changes before executing
- **Hash verification** — All transfers verified with SHA256
- **Conflict detection** — Rename refuses on naming conflicts
- **User confirmation** — Ingestion requires explicit approval

## Exit Codes

- `0` — Success
- `1` — Failure (mismatches, errors, etc.)
- `130` — Interrupted by user (Ctrl+C)

## Examples

### Full Drive Ingestion
```bash
python ingest_new_drive.py /mnt/samsung_t7 \
  --project "Wedding_Johnson_Mar2026" \
  --backup /mnt/nas/backups
```

### Audit Only
```bash
python audit_drive.py /mnt/old_drive --output-dir ./audit_results
```

### Find Duplicates
```bash
python deduplicate.py /photos/2024 /photos/2025 /photos/2026 \
  --lightroom-catalog ~/Lightroom/Master_Catalog.lrcat
```

### Rename with Preview
```bash
python rename_batch.py /incoming/raw \
  --pattern "{YYYY}{MM}{DD}_{camera_model}_{sequence}" \
  --preview
```

### Verify Backup
```bash
python backup_verify.py /media_library/01_PHOTOS /mnt/backup_drive/01_PHOTOS
```

## Support

For issues or questions, check logs in `logs/` directory or review the Agent 1-2 research documents in `agents/`.
