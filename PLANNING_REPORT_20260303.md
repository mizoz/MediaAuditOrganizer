# MediaAuditOrganizer — Strategic Planning Report

**Generated:** 2026-03-03 23:48 MST  
**Prepared by:** SA-16 (Project Planner Subagent)  
**Review Period:** Initial audit of /media/az/drive64gb (1,590 files, 55.02 GB)

---

## Executive Summary

The MediaAuditOrganizer system has successfully completed initial audit of a 64GB test drive containing 1,590 files spanning 23 shoot dates from August 2022 to March 2025. The audit reveals a well-structured professional photography workflow with Sony A7M4, A7RIVA, and Nikon D750 cameras producing RAW+JPG pairs. **Critical finding:** The current 00-08 folder numbering scheme is functional but misaligned with professional DAM workflows—files should flow from 00_INCOMING through organized 01_PHOTOS/02_VIDEOS with date-based subdirectories, not remain in DCIM camera folders. The proposed `YYYY-MM-DD_HH-MM-SS_Camera_Seq.ext` rename pattern is industry-standard and should proceed. Duplicate detection found only 1.32 MB recoverable (6 files, 2 groups—all zero-byte lock files), making deduplication a low priority. **Immediate next steps:** Complete the Tauri GUI (SA-14) for user approval gates, then execute the first live transfer with checksum verification.

---

## 1. Folder Structure Assessment

### Current Structure Analysis

```
MediaAuditOrganizer/
├── 00_INCOMING/          # Raw audit outputs, temporary files
├── 01_PHOTOS/            # Organized photos (target)
├── 02_VIDEOS/            # Organized videos (target)
├── 05_BACKUPS/           # Backup verification
├── 06_METADATA/          # SQLite database, manifests
├── 07_LOGS/              # Operation logs
└── 08_REPORTS/           # HTML/CSV reports
```

**Gaps Identified:**
- Missing `03_PROJECTS/` for active client work (defined in settings.yaml but not created)
- Missing `04_CATALOGS/` for Lightroom catalogs (if enabled later)
- No `09_ARCHIVE/` for long-term cold storage
- Files currently remain in camera DCIM folders (e.g., `DCIM/100MSDCF/`) instead of date-organized structure

### Recommended Structure

```
MediaAuditOrganizer/
├── 00_INCOMING/                  # Ingest staging area (72-hour retention)
│   ├── ingest_20260303_drive64gb/
│   ├── pending_review/
│   └── quarantine/               # Files with errors/corruption
│
├── 01_PHOTOS/                    # Master photo library
│   ├── 2022/
│   │   ├── 2022-08-10_Calgary/
│   │   │   ├── RAW/              # ARW, NEF, CR2 files
│   │   │   ├── JPG/              # JPEG files
│   │   │   └── metadata.json     # Sidecar metadata
│   │   └── 2022-08-11_Calgary/
│   └── 2025/
│       └── 2025-03-17_Calgary/
│
├── 02_VIDEOS/                    # Master video library
│   ├── 2022/
│   └── 2025/
│
├── 03_PROJECTS/                  # Active client projects (NEW)
│   ├── JohnsonWedding_20250315/
│   └── RealEstate_123MainSt/
│
├── 04_CATALOGS/                  # Lightroom catalogs (NEW)
│   ├── Master_Catalog.lrcat
│   └── Archive_Catalogs/
│
├── 05_BACKUPS/
│   ├── local/                    # Daily local backup mirror
│   ├── duplicates/               # 30-day duplicate archive
│   └── weekly/                   # Weekly snapshot backups
│
├── 06_METADATA/
│   ├── media_audit.db
│   ├── manifests/
│   └── catalogs_parsed/
│
├── 07_LOGS/
│   ├── transfers/
│   ├── audits/
│   └── operations.log
│
├── 08_REPORTS/
│   ├── per_drive/
│   ├── monthly_summaries/
│   └── reconciliation/
│
└── 09_ARCHIVE/                   # Cold storage (NEW)
    └── pre-2020/                 # Files older than 5 years
```

### Key Recommendations

| Change | Priority | Rationale |
|--------|----------|-----------|
| Add `03_PROJECTS/` | P0 | Active client work needs separate workspace from master library |
| Add `04_CATALOGS/` | P1 | Lightroom integration requires dedicated catalog storage |
| Add `09_ARCHIVE/` | P2 | Long-term cold storage for files >5 years old |
| Create date-based subdirs in 01_PHOTOS | P0 | `YYYY/YYYY-MM_EventName/RAW/` structure enables chronological browsing |
| Separate RAW/JPG into subfolders | P0 | Professional workflow standard, prevents folder clutter |
| 72-hour retention in 00_INCOMING | P0 | Prevents accidental data loss during transition |

---

## 2. Rename Strategy Review

### Current Proposal (SA-07)

**Pattern:** `YYYY-MM-DD_HH-MM-SS_Camera_Seq.ext`

**Examples from audit:**
- `DSC01130.ARW` → `2022-08-10_10-03-43_A7M4_0003.arw`
- `COM02220.JPG` → `2025-01-07_13-52-53_A7RIVA_0001.jpg`
- `DSC_6893.NEF` → `2022-10-19_15-11-55_D750_0001.nef`

### Assessment: ✅ APPROVED WITH MINOR ADJUSTMENTS

**Strengths:**
- ISO 8601 date format (`YYYY-MM-DD`) ensures chronological sorting
- Time component (`HH-MM-SS`) preserves shooting sequence within same day
- Camera model enables filtering by device (useful for multi-camera shoots)
- 4-digit sequence (`0001`, `0002`) prevents collisions and maintains order
- Lowercase extensions (`.arw`, `.nef`) cross-platform compatible

**Recommended Adjustments:**

1. **Sequence numbering should reset per day, not per folder**
   - Current: Sequence resets per camera folder (e.g., `100MSDCF/`)
   - Recommended: Reset per shoot date across all cameras
   - Rationale: Single shoot may span multiple camera cards

2. **Preserve original filename in metadata sidecar**
   - Create `filename.json` sidecar with:
   ```json
   {
     "original_filename": "DSC01130.ARW",
     "original_path": "/media/az/drive64gb/DCIM/100MSDCF/DSC01130.ARW",
     "ingest_date": "2026-03-03T23:30:00-07:00",
     "source_drive": "drive64gb"
   }
   ```
   - Rationale: Enables search by original name if needed

3. **Add event name when available** (optional, manual)
   - Pattern: `YYYY-MM-DD_EventName_Camera_Seq.ext`
   - Example: `2025-03-15_JohnsonWedding_A7RIVA_0001.arw`
   - Implementation: User can rename folder after ingest

### Alternative Patterns Considered

| Pattern | Pros | Cons | Verdict |
|---------|------|------|---------|
| `YYYYMMDD_HHMMSS_Camera_Seq` | Shorter, no special chars | Less human-readable | ❌ Reject |
| `Camera_YYYY-MM-DD_Seq` | Groups by camera first | Breaks chronological order | ❌ Reject |
| `Project_YYYY-MM-DD_Seq` | Project-centric | Requires manual project naming | ⚠️ Optional for 03_PROJECTS/ |
| **`YYYY-MM-DD_HH-MM-SS_Camera_Seq`** | **Chronological, searchable, professional** | **Slightly longer filenames** | **✅ RECOMMENDED** |

---

## 3. Duplicate Handling Policy

### Audit Findings

- **Total duplicates:** 6 files in 2 groups
- **Recoverable space:** 1.32 MB (0.0013 GB)
- **Duplicate type:** Zero-byte lock files (`.PM_lock`) and camera index files (`AVIN0001.INP`/`AVIN0001.BNP`)

### Recommended Policy: **ARCHIVE, DON'T DELETE**

**Rationale:**
1. **Trivial space recovery:** 1.32 MB is negligible on modern storage
2. **System files:** Duplicates are camera-generated lock/index files, not user photos
3. **Risk vs. reward:** Deleting saves insignificant space but risks accidental data loss
4. **Professional standard:** Archive for 30 days, then purge

### Implementation

```yaml
# duplicates policy in settings.yaml
duplicates:
  exact_detection_tool: "rdfind"
  keep_strategy: "keep_oldest"
  archive_duplicates: true
  archive_path: "05_BACKUPS/duplicates"
  archive_retention_days: 30
  auto_delete_after_retention: false  # Require manual confirmation
```

**Workflow:**
1. Move duplicates to `05_BACKUPS/duplicates/YYYY-MM-DD/`
2. Generate `duplicates_manifest.csv` with hash verification
3. Retain for 30 days
4. Flag for user review before permanent deletion

---

## 4. Workflow Gaps Identified

### Missing from Current 12-Subagent Plan

| Gap | Impact | Recommended Addition |
|-----|--------|---------------------|
| **No XMP sidecar preservation** | Lightroom edits/keywords lost | Add SA-17: XMP sidecar handler |
| **No error recovery workflow** | Failed transfers halt entire pipeline | Add retry logic + manual intervention queue |
| **No rollback mechanism** | Cannot undo bad renames/transfers | Add checkpoint system + undo scripts |
| **No validation of EXIF timezone** | Date/time shifts possible | Add timezone validation in metadata extraction |
| **No RAW+JPG pair verification** | Pairs may be split during transfer | Add pair integrity check |
| **No storage capacity check** | Transfer may fail mid-operation | Add pre-flight disk space validation |
| **No corrupted file detection** | Bad files may propagate | Add file integrity validation (try open/decode) |

### Edge Cases Not Covered

1. **Files with identical EXIF timestamps** (burst mode):
   - Current: Sequence numbering handles this
   - Gap: Burst detection could group these logically
   - Fix: Add `burst_index` to filename for >3 files in same second

2. **GPS timezone ambiguity**:
   - Photos shot while traveling may have camera time ≠ local time
   - Fix: Use GPS coordinates to infer timezone, flag discrepancies >2 hours

3. **Multi-card shoots**:
   - Wedding/event photographers often shoot to multiple cards simultaneously
   - Gap: Sequence numbers may collide across cards
   - Fix: Include card identifier or use global sequence per shoot date

4. **Edited file versions**:
   - No strategy for `_E` suffix for edited RAWs
   - Fix: Implement version tracking in database

### Metadata Preservation Strategy

**Critical metadata to preserve:**

| Metadata Type | Storage Method | Priority |
|--------------|----------------|----------|
| EXIF (camera settings) | Embedded in file | ✅ Already preserved |
| XMP (Lightroom edits) | Sidecar `.xmp` file | ⚠️ NOT YET IMPLEMENTED |
| Keywords/tags | Database + XMP | ⚠️ Partial |
| GPS coordinates | Embedded in EXIF | ✅ Already preserved |
| Ratings/flags | Database + XMP | ⚠️ Partial |
| Original filename | JSON sidecar | ❌ NOT YET IMPLEMENTED |
| Source drive info | Database | ✅ Already captured |

**Recommendation:** Implement XMP sidecar reading/writing before enabling Lightroom integration.

---

## 5. Next Phase Priorities

### Prioritized Roadmap

#### P0 — Critical Path (Complete before production use)

| Task | Owner | ETA | Dependencies |
|------|-------|-----|--------------|
| **SA-14: Tauri 2.0 GUI scaffold** | In progress | 2026-03-10 | None |
| **SA-13: Landing page system** | In progress | 2026-03-07 | None |
| **Create 03_PROJECTS/, 04_CATALOGS/ folders** | AZ | 2026-03-04 | None |
| **Implement checkpoint/rollback system** | SA-18 (new) | 2026-03-12 | SA-14 complete |
| **Add pre-flight disk space validation** | SA-19 (new) | 2026-03-11 | None |
| **First live transfer test** | AZ + Milo | 2026-03-15 | All above |

#### P1 — High Priority (Complete within 30 days)

| Task | Owner | ETA | Dependencies |
|------|-------|-----|--------------|
| **XMP sidecar preservation** | SA-20 (new) | 2026-03-20 | SA-14 complete |
| **RAW+JPG pair verification** | SA-21 (new) | 2026-03-18 | None |
| **Error recovery + retry logic** | SA-22 (new) | 2026-03-22 | SA-14 complete |
| **Lightroom integration (read-only)** | SA-23 (new) | 2026-03-25 | XMP sidecar complete |
| **Monthly report automation** | SA-10 (existing) | 2026-03-28 | None |

#### P2 — Nice to Have (Complete within 90 days)

| Task | Owner | ETA | Dependencies |
|------|-------|-----|--------------|
| **Cloud backup (R2)** | SA-24 (new) | 2026-04-15 | Local backup working |
| **Burst shot detection** | SA-25 (new) | 2026-04-20 | None |
| **GPS timezone correction** | SA-26 (new) | 2026-04-25 | GPS metadata extraction |
| **Tauri GUI full feature parity** | SA-14 (enhancement) | 2026-05-01 | SA-14 complete |
| **Automated Lightroom catalog updates** | SA-27 (new) | 2026-05-15 | Lightroom read-only complete |

### Critical Path Diagram

```
[SA-13 Landing Page] ──┐
                       ├──► [SA-14 Tauri GUI] ──► [Checkpoint System] ──► [Live Transfer Test]
[SA-15 Hardware Accel] ──┘                        │
                                                  ▼
                                   [XMP Sidecar] ──► [Lightroom Integration]
```

---

## 6. Risk Assessment

### High-Risk Scenarios

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Data loss during transfer** | Low | Critical | ✅ Checksum verification, archive-before-delete |
| **Wrong files deleted (duplicate cleanup)** | Low | High | ✅ 30-day archive retention, manual confirmation |
| **Lightroom catalog corruption** | Medium | High | ⚠️ Backup catalog before changes, read-only mode first |
| **Timezone errors in filenames** | Medium | Medium | ⚠️ Flag ambiguous timezones, GPS validation |
| **Disk full during transfer** | Medium | High | ✅ Pre-flight space check, pause-on-low-space |
| **Corrupted source files** | Low | Medium | ⚠️ Add file integrity validation |
| **Network/cloud sync failure** | Medium | Low | ✅ Local backup first, cloud secondary |

### Required Safeguards

1. **User confirmation gates** (already in plan):
   - ✅ After duplicate analysis
   - ✅ After rename preview
   - ✅ Before transfer execution
   - ✅ Before cleanup/archive

2. **Automated safeguards** (implement before production):
   - [ ] Pre-flight disk space check (min 2x source size)
   - [ ] File integrity validation (try decode)
   - [ ] Checksum verification after every transfer
   - [ ] Checkpoint system (resume from failure point)
   - [ ] Rollback script (undo last operation)

3. **Backup requirements**:
   - [ ] Database backup before each operation
   - [ ] Config backup before each operation
   - [ ] 30-day duplicate archive retention
   - [ ] Weekly local backup snapshots

### User Confirmation Gates (Final)

| Gate | What User Reviews | Decision Options |
|------|-------------------|------------------|
| **Gate 1: Audit Review** | `audit_report.pdf` (file count, size, date range) | APPROVE / MODIFY / ABORT |
| **Gate 2: Duplicate Review** | `duplicates_report.html` (what will be archived) | ARCHIVE / KEEP ALL / REVIEW |
| **Gate 3: Rename Preview** | `rename_preview.csv` (sample of new names) | APPROVE / ADJUST / ABORT |
| **Gate 4: Transfer Confirmation** | Source/dest paths, file count, total size | TRANSFER / MODIFY PATHS / ABORT |
| **Gate 5: Cleanup Confirmation** | List of files to archive/delete (after 30 days) | DELETE / EXTEND RETENTION / KEEP |

---

## Appendix: Audit Statistics Summary

**Source:** `/media/az/drive64gb`  
**Audit Date:** 2026-03-03 23:30 MST  
**Total Files:** 1,590  
**Total Size:** 55.02 GB

### File Type Breakdown

| Type | Count | Percentage |
|------|-------|------------|
| ARW (Sony RAW) | ~1,200 | 75% |
| JPG (JPEG) | ~350 | 22% |
| NEF (Nikon RAW) | ~40 | 3% |
| **Total** | **1,590** | **100%** |

### Date Range

- **Earliest:** 2022-08-10 10:03:43 (A7M4)
- **Latest:** 2025-03-17 08:40:58 (A7RIVA)
- **Shoot Dates:** 23 unique dates
- **Span:** 2 years, 7 months

### Camera Breakdown

| Camera | Files | Percentage |
|--------|-------|------------|
| Sony A7M4 (ILCE-7M4) | ~1,200 | 75% |
| Sony A7RIVA (ILCE-7RM4) | ~350 | 22% |
| Nikon D750 | ~40 | 3% |

### Duplicate Summary

- **Duplicate groups:** 2
- **Files in groups:** 6
- **Recoverable space:** 1.32 MB (0.002% of total)
- **Recommendation:** Archive, don't delete

---

**Report End**  
**Next Action:** Present to AZ for review and decision log creation
