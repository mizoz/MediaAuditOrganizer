# Subagent Orchestration Plan — MediaAuditOrganizer

**Created:** 2026-03-03 22:30 MST  
**Status:** Planning Phase (Simulation Mode)  
**Agent:** Milo (Main Channel) + Subagents (Execution)

---

## Overview

This document defines the subagent orchestration strategy for the MediaAuditOrganizer system. The main channel (Telegram) receives status updates only — all execution happens in isolated subagents.

**Key Principle:** Main channel = coordination & alerts. Subagents = execution & logging.

---

## Subagent Inventory

| ID | Name | Runtime | Purpose | Max Parallel |
|----|------|---------|---------|--------------|
| SA-01 | `env-validator` | subagent | Verify tool installations, Python deps, config files | 1 |
| SA-02 | `config-auditor` | subagent | Validate settings.yaml, rename_rules.yaml, path existence | 1 |
| SA-03 | `db-init` | subagent | Initialize SQLite schema, run integrity checks | 1 |
| SA-04 | `drive-scanner` | subagent | Scan mounted drives, detect new media | 2 |
| SA-05 | `audit-executor` | subagent | Run audit_drive.py, extract metadata, compute hashes | 2 |
| SA-06 | `dedupe-analyzer` | subagent | Run deduplicate.py, generate duplicate reports | 1 |
| SA-07 | `rename-planner` | subagent | Dry-run rename_batch.py, generate preview CSV | 1 |
| SA-08 | `transfer-executor` | subagent | Run transfer_assets.py with rclone verification | 2 |
| SA-09 | `backup-verifier` | subagent | Run backup_verify.py, cross-check hashes | 1 |
| SA-10 | `report-generator` | subagent | Generate PDF/HTML reports from audit data | 1 |
| SA-11 | `lightroom-reconciler` | subagent | Parse Lightroom catalog, reconcile file paths | 1 |
| SA-12 | `cleanup-archiver` | subagent | Archive duplicates, clean 00_INCOMING, rotate logs | 1 |

**Total Subagents:** 12  
**Max Concurrent:** 5-6 (during peak workflow phases)

---

## Workflow Phases & Subagent Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 0: INITIALIZATION (One-time setup)                                    │
└─────────────────────────────────────────────────────────────────────────────┘

[SA-01] env-validator ─────────────────────────────────────────────────────┐
    ├── Check: exiftool, ffmpeg, fd, rclone, rdfind, python3               │
    ├── Check: requirements.txt installed                                  │
    └── Output: env_status.json                                            │
                                                                           │
[SA-02] config-auditor ────────────────────────────────────────────────────┤
    ├── Validate: settings.yaml (3 required paths edited)                  │
    ├── Validate: rename_rules.yaml (syntax check)                         │
    └── Output: config_audit.json                                          │
                                                                           │
[SA-03] db-init ───────────────────────────────────────────────────────────┤
    ├── Create: media_audit.db (if not exists)                             │
    ├── Verify: 11 tables created                                          │
    └── Output: db_status.json                                             │
                                                                           │
                                    ┌──────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: DRIVE DETECTION (Runs on mount or manual trigger)                  │
└─────────────────────────────────────────────────────────────────────────────┘

[SA-04] drive-scanner ─────────────────────────────────────────────────────┐
    ├── Scan: /media/, /mnt/, /Volumes/                                    │
    ├── Detect: New drives (compare to last_scan.json)                     │
    └── Output: detected_drives.json                                       │
                                                                           │
                                    ┌──────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: AUDIT & METADATA EXTRACTION                                        │
└─────────────────────────────────────────────────────────────────────────────┘

[SA-05] audit-executor ────────────────────────────────────────────────────┐
    ├── Run: python scripts/audit_drive.py /path/to/drive                  │
    ├── Extract: EXIF (photos), video metadata, hashes                     │
    ├── Output: manifest.csv, metadata.json, audit_*.log                   │
    └── Trigger: [SA-10] report-generator                                  │
                                                                           │
                                    ┌──────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: DUPLICATE ANALYSIS                                                 │
└─────────────────────────────────────────────────────────────────────────────┘

[SA-06] dedupe-analyzer ───────────────────────────────────────────────────┐
    ├── Run: python scripts/deduplicate.py /drive /library                 │
    ├── Compare: Hash-based (exact) + perceptual (near-duplicates)         │
    ├── Output: duplicates_report.html, duplicates_action_plan.csv         │
    └── Status: PENDING_USER_REVIEW (main channel alerts)                  │
                                                                           │
                                    ┌──────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: USER REVIEW GATE ⚠️                                                 │
└─────────────────────────────────────────────────────────────────────────────┘

[MAIN CHANNEL] — Waits for user confirmation
    ├── Review: Audit report (PDF), duplicate report (HTML)
    ├── Confirm: "Approve transfer of X files (Y GB)"
    └── Decision: Proceed / Modify / Abort

                                    ▼ (User confirms)
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: RENAME PLANNING                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

[SA-07] rename-planner ────────────────────────────────────────────────────┐
    ├── Run: python scripts/rename_batch.py /path --dry-run                │
    ├── Generate: rename_plan.csv (old → new paths)                        │
    └── Status: PENDING_USER_REVIEW (main channel alerts)                  │
                                                                           │
                                    ┌──────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 6: RENAME CONFIRMATION GATE ⚠️                                         │
└─────────────────────────────────────────────────────────────────────────────┘

[MAIN CHANNEL] — Waits for user confirmation
    ├── Review: rename_plan.csv preview
    └── Decision: Approve renames / Adjust patterns / Abort

                                    ▼ (User confirms)
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 7: TRANSFER EXECUTION                                                 │
└─────────────────────────────────────────────────────────────────────────────┘

[SA-08] transfer-executor ─────────────────────────────────────────────────┐
    ├── Run: python scripts/transfer_assets.py /source /dest --verify      │
    ├── Verify: Checksum after each file                                   │
    ├── Retry: 3x on failure                                               │
    └── Output: transfer.log, checksums.md5, integrity.json                │
                                                                           │
                                    ┌──────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 8: BACKUP VERIFICATION                                                │
└─────────────────────────────────────────────────────────────────────────────┘

[SA-09] backup-verifier ───────────────────────────────────────────────────┐
    ├── Run: python scripts/backup_verify.py --target all                  │
    ├── Compare: Local hash vs cloud hash vs database hash                 │
    └── Output: backup_verify.log, integrity_report.json                   │
                                                                           │
                                    ┌──────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 9: REPORT GENERATION                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

[SA-10] report-generator ──────────────────────────────────────────────────┐
    ├── Run: python scripts/generate_report.py --audit-id AUDIT_ID         │
    ├── Generate: PDF + HTML reports                                       │
    └── Output: reports/per_drive/audit_*.pdf, audit_*.html                │
                                                                           │
                                    ┌──────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 10: LIGHTROOM RECONCILIATION (Optional)                               │
└─────────────────────────────────────────────────────────────────────────────┘

[SA-11] lightroom-reconciler ──────────────────────────────────────────────┐
    ├── Run: python scripts/lightroom_export_parser.py --catalog PATH      │
    ├── Reconcile: Catalog references vs actual files                      │
    └── Output: reconciliation_report.pdf, reconciliation_action_plan.csv  │
                                                                           │
                                    ┌──────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 11: CLEANUP & ARCHIVE                                                 │
└─────────────────────────────────────────────────────────────────────────────┘

[SA-12] cleanup-archiver ──────────────────────────────────────────────────┐
    ├── Archive: Duplicates to 05_BACKUPS/duplicates/ (30-day retention)   │
    ├── Clean: 00_INCOMING/ingest_* (after successful completion)          │
    ├── Rotate: Logs older than 90 days                                    │
    └── Output: cleanup_log.json                                           │
                                                                           │
                                    ┌──────────────────────────────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ COMPLETE — Main channel sends summary                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Simulation Mode Setup

Since no drive is connected yet, we'll run **Simulation Mode** to test the orchestration without actual file operations.

### Simulation Triggers

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Full Simulation** | `--simulate` flag | All scripts run with `--dry-run`, mock data generated |
| **Partial Simulation** | `--simulate=audit` | Only audit phase runs on sample folder |
| **Live Mode** | No flag | Full execution on real drive |

### Mock Data Structure for Testing

```
/home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer/00_INCOMING/simulated_drive/
├── DCIM/
│   ├── 100CANON/
│   │   ├── IMG_0001.CR2 (mock: 25MB, EXIF: 2025-03-15, Canon EOS R5)
│   │   ├── IMG_0002.CR2 (mock: 25MB, EXIF: 2025-03-15, Canon EOS R5)
│   │   └── IMG_0001.JPG (mock: 8MB, EXIF: 2025-03-15, Canon EOS R5) ← RAW+JPG pair
│   └── 101CANON/
│       └── IMG_0003.CR2 (mock: 25MB, EXIF: 2025-03-16, Canon EOS R5)
├── VIDEO/
│   ├── GOPR0001.MP4 (mock: 500MB, 4K 60fps, GoPro Hero 11)
│   └── DJI_0001.MP4 (mock: 350MB, 5.4K 30fps, DJI Mini 3)
└── SCREENSHOTS/
    └── Screenshot_2025-03-15.png (mock: 2MB, no EXIF)
```

**Total mock files:** 7  
**Total mock size:** ~630MB  
**Expected duplicates:** 0 (clean test set)  
**Expected RAW+JPG pairs:** 1 (IMG_0001.CR2 + IMG_0001.JPG)

---

## Main Channel Communication Protocol

### Status Update Format

```
[MediaAudit] Phase X: <phase_name> — <status>
├─ Subagent: SA-XX (<name>)
├─ Progress: N/M files (XX%)
├─ ETA: X minutes
└─ Next: <next_phase>
```

### Alert Triggers (Main Channel Messages User)

| Trigger | Priority | Message Format |
|---------|----------|----------------|
| Phase complete | Low | "✅ Phase X complete — <summary>" |
| User review required | High | "⚠️ Review required: <report_link>. Reply: APPROVE / MODIFY / ABORT" |
| Error detected | High | "❌ Error in Phase X: <error>. Recovery: <suggestion>" |
| Simulation complete | Low | "🎯 Simulation complete — <summary>. Ready for live run." |

### Confirmation Gates (Require User Reply)

1. **After Phase 3 (Duplicate Analysis):** Review duplicates, decide keep/archive/delete
2. **After Phase 5 (Rename Planning):** Review rename plan, approve patterns
3. **Before Phase 7 (Transfer):** Confirm source/dest paths and file count
4. **Before Phase 11 (Cleanup):** Confirm duplicate archive action

---

## File Paths & Configuration

### Project Root
```
/home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer/
```

### Required Paths (To be configured in settings.yaml)

| Setting | Current Value | Required Action |
|---------|---------------|-----------------|
| `general.workspace_root` | `/path/to/MediaAuditOrganizer` | Update to project root |
| `organization.photos_root` | `01_PHOTOS` | Create folder if missing |
| `organization.videos_root` | `02_VIDEOS` | Create folder if missing |
| `organization.incoming_root` | `00_INCOMING` | Create folder if missing |
| `metadata.assume_timezone` | `America/Edmonton` | ✅ Already correct |
| `backup.local_path` | `/mnt/backup_drive/05_BACKUPS/` | Update to actual backup path |
| `lightroom.master_catalog` | `~/Lightroom/Master_Catalog.lrcat` | Update if using Lightroom |

### Test Drive Path (Simulation)
```
/home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer/00_INCOMING/simulated_drive/
```

### Live Drive Path (To be provided by user)
```
/mnt/<drive_label>/  OR  /media/az/<drive_label>/  OR  /Volumes/<drive_label>/
```

---

## Subagent Spawn Commands (Reference)

### Phase 0: Initialization
```bash
# SA-01: Environment Validator
sessions_spawn --runtime=subagent --mode=run \
  --task="Validate MediaAuditOrganizer environment: check exiftool, ffmpeg, fd, rclone, rdfind, python3.10+, requirements.txt. Output: env_status.json" \
  --label="env-validator"

# SA-02: Config Auditor
sessions_spawn --runtime=subagent --mode=run \
  --task="Audit MediaAuditOrganizer config: validate settings.yaml (3 required paths), rename_rules.yaml syntax, folder existence. Output: config_audit.json" \
  --label="config-auditor"

# SA-03: Database Init
sessions_spawn --runtime=subagent --mode=run \
  --task="Initialize MediaAuditOrganizer SQLite database: create 11 tables if not exists, verify schema, run integrity check. Output: db_status.json" \
  --label="db-init"
```

### Phase 1-11: Workflow Execution
```bash
# SA-04: Drive Scanner
sessions_spawn --runtime=subagent --mode=run \
  --task="Scan /media/, /mnt/, /Volumes/ for new drives. Compare to last_scan.json. Output: detected_drives.json" \
  --label="drive-scanner"

# SA-05: Audit Executor
sessions_spawn --runtime=subagent --mode=run \
  --task="Run audit_drive.py on /path/to/drive. Extract EXIF, video metadata, hashes. Output: manifest.csv, metadata.json" \
  --label="audit-executor"

# SA-06: Dedupe Analyzer
sessions_spawn --runtime=subagent --mode=run \
  --task="Run deduplicate.py on /drive and /library. Generate duplicates_report.html, duplicates_action_plan.csv" \
  --label="dedupe-analyzer"

# SA-07: Rename Planner
sessions_spawn --runtime=subagent --mode=run \
  --task="Run rename_batch.py --dry-run on /path. Generate rename_plan.csv preview" \
  --label="rename-planner"

# SA-08: Transfer Executor
sessions_spawn --runtime=subagent --mode=run \
  --task="Run transfer_assets.py /source /dest --verify. Verify checksums, retry failures. Output: transfer.log" \
  --label="transfer-executor"

# SA-09: Backup Verifier
sessions_spawn --runtime=subagent --mode=run \
  --task="Run backup_verify.py --target all. Compare hashes across local/cloud. Output: integrity_report.json" \
  --label="backup-verifier"

# SA-10: Report Generator
sessions_spawn --runtime=subagent --mode=run \
  --task="Run generate_report.py --audit-id AUDIT_ID. Generate PDF + HTML reports" \
  --label="report-generator"

# SA-11: Lightroom Reconciler
sessions_spawn --runtime=subagent --mode=run \
  --task="Run lightroom_export_parser.py --catalog PATH. Reconcile catalog vs files. Output: reconciliation_report.pdf" \
  --label="lightroom-reconciler"

# SA-12: Cleanup Archiver
sessions_spawn --runtime=subagent --mode=run \
  --task="Archive duplicates to 05_BACKUPS/duplicates/, clean 00_INCOMING/, rotate logs >90 days" \
  --label="cleanup-archiver"
```

---

## Safety Gates & Rollback Procedures

### Before Any Destructive Action

1. **Backup database:**
   ```bash
   cp 06_METADATA/media_audit.db 06_METADATA/media_audit.db.backup_$(date +%Y%m%d_%H%M%S)
   ```

2. **Backup config:**
   ```bash
   cp configs/settings.yaml configs/settings.yaml.backup_$(date +%Y%m%d_%H%M%S)
   ```

3. **Dry-run first:**
   - All rename operations: `--dry-run` before actual run
   - All transfer operations: Preview file list before transfer
   - All delete operations: Archive, never delete (30-day retention)

### Rollback Triggers

| Trigger | Rollback Action |
|---------|-----------------|
| Checksum mismatch > 5% | Abort transfer, flag source drive |
| Database integrity failure | Restore from last backup |
| User abort at any gate | Stop all subagents, clean partial work |
| Disk full | Abort, free space, retry from checkpoint |

---

## Next Steps (Action Items)

### Immediate (Before Simulation)

- [ ] **AZ:** Provide test drive path (or confirm simulated_drive folder creation)
- [ ] **AZ:** Edit `configs/settings.yaml` with 3 required paths
- [ ] **Milo:** Spawn SA-01 (env-validator) to check tool installations
- [ ] **Milo:** Spawn SA-02 (config-auditor) to validate configuration
- [ ] **Milo:** Spawn SA-03 (db-init) to initialize database

### Simulation Run

- [ ] **Milo:** Create mock data structure in `00_INCOMING/simulated_drive/`
- [ ] **Milo:** Spawn SA-04 through SA-12 in sequence
- [ ] **Milo:** Send status updates to main channel after each phase
- [ ] **AZ:** Review reports at confirmation gates
- [ ] **Milo:** Generate final simulation report

### Live Run (After drive plugged in)

- [ ] **AZ:** Plug in drive, provide mount path
- [ ] **Milo:** Spawn SA-04 (drive-scanner) to detect
- [ ] **Milo:** Execute full workflow Phases 2-11
- [ ] **AZ:** Review and confirm at gates
- [ ] **Milo:** Send completion summary + backup confirmation

---

## Status

**Current State:** Planning Complete — Awaiting User Confirmation  
**Next Action:** Create simulated_drive mock data + spawn SA-01 (env-validator)  
**Estimated Setup Time:** 10-15 minutes (tool verification + config audit)

---

*This document is auto-maintained. Milo updates phase completion status after each subagent run.*
