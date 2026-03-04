# MediaAuditOrganizer — Safe Test Plan

**Created:** 2026-03-03 22:35 MST  
**Mode:** READ-ONLY SAFETY FIRST  
**Drive:** Pending mount confirmation  
**Status:** Environment validation in progress

---

## ⚠️ Safety Rules (Non-Negotiable)

1. **NO destructive actions** without explicit user confirmation
2. **Dry-run first** for all rename/transfer operations
3. **Archive, never delete** (30-day retention minimum)
4. **Backup database** before any schema changes
5. **Main channel alerts only** — subagents handle execution

---

## Phase 0: Environment Validation (SA-01) — IN PROGRESS

### Tools Verified (Quick Check)
| Tool | Status | Version |
|------|--------|---------|
| exiftool | ✅ Found | brew |
| ffmpeg | ✅ Found | brew |
| fd | ✅ Found | brew |
| rclone | ✅ Found | brew |
| rdfind | ✅ Found | brew |
| python3 | ✅ Found | 3.14.3 |

### SA-01 Full Validation Tasks
- [ ] Verify Python requirements.txt installed (jinja2, weasyprint, Pillow, imagehash)
- [ ] Check rclone configuration (remotes configured?)
- [ ] Verify folder structure exists (00_INCOMING, 01_PHOTOS, etc.)
- [ ] Check configs/settings.yaml exists and is editable
- [ ] Check configs/rename_rules.yaml exists

**Output:** `env_status.json`

---

## Phase 0b: GUI Status Check

### Current State
- GUI folder exists: `/home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer/gui/`
- Subfolders: `static/`, `templates/`
- **Missing:** `app.py` (Flask/FastAPI entry point)

### Can a Subagent Launch the GUI?
**Yes, but:** The GUI application needs to be created first. Options:

1. **Spawn subagent to build GUI** (Flask-based web interface)
   - Creates `app.py` with routes for: dashboard, audit view, duplicate review, transfer status
   - Runs on `http://localhost:5000`
   - Can be launched in background by subagent

2. **Use existing CLI workflow** (faster for testing)
   - All 8 scripts work via command line
   - Main channel provides status updates
   - Reports generated as PDF/HTML for browser viewing

**Recommendation:** Start with CLI workflow for testing (Phase 1-11). Build GUI as a separate enhancement project.

---

## Phase 1: Drive Detection — PENDING

### Issue
Path `/media/az/1-64gb/` not found. Drive may need to be:
- Mounted manually
- Accessed at different path
- Re-plugged

### Next Steps
1. User confirms drive is plugged in and mounted
2. Run `lsblk` or `df -h` to find actual mount point
3. Update test plan with correct path

### Alternative: Use Sample Data
If drive not ready, create simulated test data:
```
00_INCOMING/simulated_drive/
├── DCIM/100CANON/IMG_0001.CR2 (mock)
├── DCIM/100CANON/IMG_0001.JPG (mock)
└── VIDEO/GOPR0001.MP4 (mock)
```

---

## Phase 2: Audit (Read-Only) — SAFE TO RUN

Once drive path confirmed:

**SA-05: Audit Executor**
```bash
python scripts/audit_drive.py /path/to/drive \
  --output-dir 00_INCOMING/audit_test/ \
  --format both \
  --include-hashes
```

**What this does:**
- Scans all files recursively
- Extracts EXIF (photos) and video metadata
- Computes MD5 + SHA256 hashes
- **Does NOT modify any files**

**Output:**
- `manifest.csv` — File list with sizes, dates
- `metadata.json` — Full metadata
- `audit_*.log` — Execution log

**Duration:** ~5-10 minutes for 64GB drive (depends on file count)

---

## Phase 3: Duplicate Detection (Read-Only) — SAFE TO RUN

**SA-06: Dedupe Analyzer**
```bash
python scripts/deduplicate.py /path/to/drive \
  --output-dir 00_INCOMING/dedupe_test/ \
  --dry-run
```

**What this does:**
- Compares files by hash (exact duplicates)
- Perceptual hashing (near-duplicates, images only)
- **Does NOT delete or move anything** (dry-run mode)

**Output:**
- `duplicates_report.html` — Interactive report with previews
- `duplicates_action_plan.csv` — Recommendations

---

## Phase 4: User Review Gate ⚠️

**Main channel sends:**
- Audit summary (file count, total size, date range)
- Duplicate report link
- **Waits for user decision:** APPROVE / MODIFY / ABORT

---

## Phase 5: Rename Planning (Dry-Run) — SAFE

**SA-07: Rename Planner**
```bash
python scripts/rename_batch.py /path/to/drive \
  --config configs/rename_rules.yaml \
  --dry-run \
  --output-plan 00_INCOMING/rename_preview.csv
```

**Output:** `rename_preview.csv` showing old → new names

---

## Phase 6: Rename Confirmation ⚠️

User reviews preview, confirms or adjusts patterns.

---

## Phase 7+: Transfer, Backup, etc. — REQUIRES CONFIRMATION

These phases modify files and require explicit approval at each gate.

---

## Test Plan Summary

| Phase | Subagent | Safe? | Requires Confirmation? | Status |
|-------|----------|-------|------------------------|--------|
| 0: Env Validation | SA-01 | ✅ Yes | No | IN PROGRESS |
| 0b: GUI Check | — | ✅ Yes | No | COMPLETE (GUI needs build) |
| 1: Drive Detection | SA-04 | ✅ Yes | No | PENDING (path not found) |
| 2: Audit | SA-05 | ✅ Yes (read-only) | No | PENDING |
| 3: Duplicate Detection | SA-06 | ✅ Yes (dry-run) | No | PENDING |
| 4: User Review | MAIN | — | **YES** | PENDING |
| 5: Rename Planning | SA-07 | ✅ Yes (dry-run) | No | PENDING |
| 6: Rename Confirm | MAIN | — | **YES** | PENDING |
| 7: Transfer | SA-08 | ❌ NO (writes files) | **YES** | PENDING |
| 8: Backup Verify | SA-09 | ✅ Yes (read-only) | No | PENDING |
| 9: Report Gen | SA-10 | ✅ Yes | No | PENDING |
| 10: Lightroom | SA-11 | ⚠️ Depends | **YES** | PENDING |
| 11: Cleanup | SA-12 | ❌ NO (archives files) | **YES** | PENDING |

---

## Immediate Next Steps

1. **SA-01 spawning now** — Full environment validation (Python deps, config files, folder structure)
2. **User action:** Confirm drive mount path (run `df -h` or `lsblk` and share output)
3. **Decision:** Proceed with CLI workflow (ready now) or build GUI first (separate project)

---

## GUI Build Option (If Desired)

If you want a GUI, I can spawn a subagent to:
- Create Flask app (`app.py`)
- Add routes: `/` (dashboard), `/audit` (view audits), `/duplicates` (review), `/transfer` (status)
- Add simple HTML templates with Bootstrap
- Launch on `localhost:5000`

**Estimated time:** 30-45 minutes for basic functional GUI

**Trade-off:** CLI workflow is fully functional now. GUI is nice-to-have for visualization.

---

*Status updates after each subagent completion.*
