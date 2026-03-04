# MediaAuditOrganizer — Updated Project Plan

**Version:** 2.0 (Updated 2026-03-03)  
**Previous Version:** 1.0 (2026-03-03)  
**Status:** Strategic Review Complete — Ready for Phase 1 Execution  
**Updated by:** SA-16 (Project Planner Subagent)

---

## Executive Summary (Changes from v1.0)

**What Changed:**
- Added missing folders (03_PROJECTS/, 04_CATALOGS/, 09_ARCHIVE/)
- Refined rename pattern with sidecar preservation
- Added checkpoint/rollback system
- Clarified Lightroom integration timeline (Phase 2, not Phase 1)
- Added error recovery workflow
- Defined sample dataset for first transfer test (500 files, not full 55 GB)

**What Stayed the Same:**
- Core 12-subagent workflow
- Checksum verification requirement
- User confirmation gates
- 3-2-1 backup architecture
- Open source tool stack

**Timeline Impact:** +1 week (now 11 weeks total) for additional safeguards

---

## Revised Implementation Timeline

### Phase 0: Setup & Configuration (2026-03-04 to 2026-03-06) — 3 days

| Task | Owner | Status | Deliverable |
|------|-------|--------|-------------|
| **0.1:** Create missing folders (03, 04, 09) | AZ | ⏳ Pending | Folder structure complete |
| **0.2:** Update settings.yaml with new paths | AZ + Milo | ⏳ Pending | Updated config |
| **0.3:** SA-01 env-validator (verify tools) | Milo | ⏳ Pending | env_status.json |
| **0.4:** SA-02 config-auditor (validate config) | Milo | ⏳ Pending | config_audit.json |
| **0.5:** SA-03 db-init (initialize database) | Milo | ⏳ Pending | media_audit.db |

**Gate:** All Phase 0 tasks complete before Phase 1

---

### Phase 1: Foundation (2026-03-07 to 2026-03-14) — 8 days

| Task | Owner | Status | Deliverable |
|------|-------|--------|-------------|
| **1.1:** SA-13 landing page system | In progress | 🔄 Active | Landing page UI |
| **1.2:** SA-14 Tauri 2.0 GUI scaffold | In progress | 🔄 Active | Tauri app shell |
| **1.3:** SA-15 hardware acceleration | In progress | 🔄 Active | GPU-accelerated ops |
| **1.4:** SA-18 checkpoint/rollback system | New | ⏳ Pending | Checkpoint scripts |
| **1.5:** SA-19 pre-flight disk validation | New | ⏳ Pending | Space check script |
| **1.6:** Update rename script (per-day sequence + sidecars) | Milo | ⏳ Pending | rename_batch.py v2 |

**Gate:** GUI functional + checkpoint system working before first transfer

---

### Phase 2: First Transfer Test (2026-03-15 to 2026-03-21) — 7 days

| Task | Owner | Status | Deliverable |
|------|-------|--------|-------------|
| **2.1:** Select sample dataset (500 files, 2 shoot dates) | AZ | ⏳ Pending | File list |
| **2.2:** SA-05 audit-executor (sample dataset) | Milo | ⏳ Pending | audit_sample.csv |
| **2.3:** SA-06 dedupe-analyzer (sample) | Milo | ⏳ Pending | duplicates_sample.html |
| **2.4:** SA-07 rename-planner (sample, dry-run) | Milo | ⏳ Pending | rename_sample.csv |
| **2.5:** **USER GATE 1:** Review audit + duplicates | AZ | ⏳ Pending | Approval |
| **2.6:** **USER GATE 2:** Review rename preview | AZ | ⏳ Pending | Approval |
| **2.7:** SA-08 transfer-executor (sample) | Milo | ⏳ Pending | transfer.log |
| **2.8:** SA-09 backup-verifier (sample) | Milo | ⏳ Pending | integrity.json |
| **2.9:** Manual verification (spot check 20 files) | AZ | ⏳ Pending | Verification notes |

**Gate:** Sample transfer successful + verified before full transfer

---

### Phase 3: Full Transfer (2026-03-22 to 2026-03-28) — 7 days

| Task | Owner | Status | Deliverable |
|------|-------|--------|-------------|
| **3.1:** SA-05 audit-executor (full drive) | Milo | ⏳ Pending | audit_full.csv |
| **3.2:** SA-06 dedupe-analyzer (full) | Milo | ⏳ Pending | duplicates_full.html |
| **3.3:** SA-07 rename-planner (full, dry-run) | Milo | ⏳ Pending | rename_full.csv |
| **3.4:** **USER GATE 3:** Review full audit | AZ | ⏳ Pending | Approval |
| **3.5:** **USER GATE 4:** Review full rename plan | AZ | ⏳ Pending | Approval |
| **3.6:** SA-08 transfer-executor (full: 1,090 files) | Milo | ⏳ Pending | transfer_full.log |
| **3.7:** SA-09 backup-verifier (full) | Milo | ⏳ Pending | integrity_full.json |
| **3.8:** SA-12 cleanup-archiver (archive duplicates) | Milo | ⏳ Pending | cleanup.log |

**Gate:** Full transfer complete + verified before Phase 4

---

### Phase 4: Lightroom Integration (2026-03-29 to 2026-04-11) — 14 days

| Task | Owner | Status | Deliverable |
|------|-------|--------|-------------|
| **4.1:** SA-20 XMP sidecar preservation | New | ⏳ Pending | XMP handler script |
| **4.2:** SA-21 RAW+JPG pair verification | New | ⏳ Pending | Pair integrity check |
| **4.3:** Enable Lightroom (read-only) | AZ + Milo | ⏳ Pending | Catalog parsed |
| **4.4:** SA-11 lightroom-reconciler (reconcile paths) | Milo | ⏳ Pending | reconciliation_report.pdf |
| **4.5:** Update Lightroom folder paths | Milo | ⏳ Pending | Catalog updated |
| **4.6:** **USER GATE 5:** Verify Lightroom sync | AZ | ⏳ Pending | Confirmation |

**Gate:** Lightroom fully synced before Phase 5

---

### Phase 5: Automation & Reporting (2026-04-12 to 2026-04-25) — 14 days

| Task | Owner | Status | Deliverable |
|------|-------|--------|-------------|
| **5.1:** SA-10 report-generator (monthly reports) | Existing | ⏳ Pending | Monthly report template |
| **5.2:** SA-22 error recovery + retry logic | New | ⏳ Pending | Retry handler |
| **5.3:** Configure automated schedules (cron) | AZ + Milo | ⏳ Pending | Cron jobs active |
| **5.4:** SA-24 cloud backup (R2) setup | New | ⏳ Pending | R2 bucket configured |
| **5.5:** **USER GATE 6:** Review automation setup | AZ | ⏳ Pending | Approval |

**Gate:** Automation tested and approved

---

### Phase 6: Production Handoff (2026-04-26 to 2026-05-02) — 7 days

| Task | Owner | Status | Deliverable |
|------|-------|--------|-------------|
| **6.1:** Full system documentation | Milo | ⏳ Pending | USER_GUIDE.md |
| **6.2:** Disaster recovery runbook | Milo | ⏳ Pending | RECOVERY.md |
| **6.3:** Final backup verification | Milo | ⏳ Pending | backup_verify_final.pdf |
| **6.4:** **USER GATE 7:** Production approval | AZ | ⏳ Pending | Sign-off |
| **6.5:** System handoff | Milo → AZ | ⏳ Pending | Production ready |

---

## Revised Subagent Inventory

### Original 12 Subagents (Unchanged)

| ID | Name | Purpose | Status |
|----|------|---------|--------|
| SA-01 | env-validator | Verify tool installations | Phase 0 |
| SA-02 | config-auditor | Validate config files | Phase 0 |
| SA-03 | db-init | Initialize SQLite database | Phase 0 |
| SA-04 | drive-scanner | Detect mounted drives | Phase 1 |
| SA-05 | audit-executor | Run audit, extract metadata | Phase 1-3 |
| SA-06 | dedupe-analyzer | Detect duplicates | Phase 1-3 |
| SA-07 | rename-planner | Plan file renames | Phase 1-3 |
| SA-08 | transfer-executor | Execute transfers | Phase 2-3 |
| SA-09 | backup-verifier | Verify backup integrity | Phase 2-3 |
| SA-10 | report-generator | Generate reports | Phase 1, 5 |
| SA-11 | lightroom-reconciler | Reconcile Lightroom paths | Phase 4 |
| SA-12 | cleanup-archiver | Archive duplicates, clean up | Phase 3 |

### New Subagents (Added per Strategic Review)

| ID | Name | Purpose | Phase | Priority |
|----|------|---------|-------|----------|
| **SA-13** | landing-page | Web UI for status/reports | Phase 1 | P0 |
| **SA-14** | tauri-gui | Desktop GUI (Tauri 2.0) | Phase 1 | P0 |
| **SA-15** | hardware-accel | GPU acceleration | Phase 1 | P0 |
| **SA-18** | checkpoint-system | Checkpoint/rollback system | Phase 1 | P0 |
| **SA-19** | preflight-check | Disk space validation | Phase 1 | P0 |
| **SA-20** | xmp-sidecar | XMP sidecar preservation | Phase 4 | P1 |
| **SA-21** | pair-verify | RAW+JPG pair verification | Phase 4 | P1 |
| **SA-22** | error-recovery | Error handling + retry logic | Phase 5 | P1 |
| **SA-24** | cloud-backup | Cloudflare R2 integration | Phase 5 | P2 |

**Total Subagents:** 20 (12 original + 8 new)

---

## Updated Folder Structure

```
MediaAuditOrganizer/
├── 00_INCOMING/                  # Ingest staging (72-hour retention)
│   ├── ingest_20260303_drive64gb/
│   ├── pending_review/
│   └── quarantine/
│
├── 01_PHOTOS/                    # Master photo library
│   ├── 2022/
│   │   └── 2022-08-10_Calgary/
│   │       ├── RAW/              # ARW, NEF, CR2
│   │       ├── JPG/              # JPEG
│   │       └── metadata.json
│   └── 2025/
│       └── 2025-01-07_Calgary/
│
├── 02_VIDEOS/                    # Master video library
│   └── (same structure as 01_PHOTOS)
│
├── 03_PROJECTS/                  # Active client projects [NEW]
│   ├── JohnsonWedding_20250315/
│   └── RealEstate_123MainSt/
│
├── 04_CATALOGS/                  # Lightroom catalogs [NEW]
│   ├── Master_Catalog.lrcat
│   └── Archive_Catalogs/
│
├── 05_BACKUPS/
│   ├── local/                    # Daily local backup
│   ├── duplicates/               # 30-day duplicate archive
│   └── weekly/                   # Weekly snapshots
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
└── 09_ARCHIVE/                   # Cold storage [NEW]
    └── pre-2020/
```

---

## Updated Confirmation Gates

### Gate 1: Audit Review (After SA-05)

**When:** After audit complete, before transfer  
**User Reviews:** `audit_report.pdf` (file count, size, date range)  
**Decision:** APPROVE / MODIFY / ABORT  
**Location:** Telegram or Tauri GUI

### Gate 2: Duplicate Review (After SA-06)

**When:** After duplicate analysis  
**User Reviews:** `duplicates_report.html` (what will be archived)  
**Decision:** ARCHIVE / KEEP ALL / REVIEW  
**Location:** Telegram or Tauri GUI

### Gate 3: Rename Preview (After SA-07)

**When:** After rename planning (dry-run)  
**User Reviews:** `rename_preview.csv` (sample of new names)  
**Decision:** APPROVE / ADJUST / ABORT  
**Location:** Telegram or Tauri GUI

### Gate 4: Transfer Confirmation (Before SA-08)

**When:** Before transfer execution  
**User Reviews:** Source/dest paths, file count, total size  
**Decision:** TRANSFER / MODIFY PATHS / ABORT  
**Location:** Telegram or Tauri GUI

### Gate 5: Lightroom Sync (After SA-11)

**When:** After Lightroom path updates  
**User Reviews:** `reconciliation_report.pdf`  
**Decision:** CONFIRM / ROLLBACK / REVIEW  
**Location:** Telegram or Tauri GUI

### Gate 6: Automation Setup (After Phase 5)

**When:** After cron jobs configured  
**User Reviews:** Schedule list, backup targets  
**Decision:** ENABLE / MODIFY / DISABLE  
**Location:** Telegram or Tauri GUI

### Gate 7: Production Approval (End of Phase 6)

**When:** All phases complete  
**User Reviews:** Final reports, documentation  
**Decision:** APPROVE PRODUCTION / REQUEST CHANGES  
**Location:** Telegram or Tauri GUI

---

## Risk Mitigation Updates

### New Safeguards (Added in v2.0)

| Safeguard | Implementation | Phase |
|-----------|----------------|-------|
| **Checkpoint system** | Save state before each operation, resume from failure | Phase 1 |
| **Rollback scripts** | Undo last rename/transfer operation | Phase 1 |
| **Pre-flight disk check** | Verify 2x source space available | Phase 1 |
| **File integrity validation** | Try decode before transfer | Phase 1 |
| **XMP sidecar preservation** | Read/write XMP alongside files | Phase 4 |
| **RAW+JPG pair verification** | Ensure pairs stay together | Phase 4 |
| **Error recovery workflow** | Retry failed transfers, flag unfixable | Phase 5 |

### Updated Risk Matrix

| Risk | Probability | Impact | Mitigation | Status |
|------|-------------|--------|------------|--------|
| Data loss during transfer | Low | Critical | Checksum verification, archive-before-delete | ✅ Covered |
| Wrong files deleted | Low | High | 30-day archive, manual confirmation | ✅ Covered |
| Lightroom catalog corruption | Medium | High | Read-only first, backup before changes | ✅ Covered (Phase 4) |
| Timezone errors in filenames | Medium | Medium | Flag ambiguous timezones | ⚠️ Partial (Phase 4) |
| Disk full during transfer | Medium | High | Pre-flight space check | ✅ Covered (Phase 1) |
| Corrupted source files | Low | Medium | File integrity validation | ✅ Covered (Phase 1) |
| Network/cloud sync failure | Medium | Low | Local backup first | ✅ Covered |

---

## Success Criteria (Updated)

### Phase 1 Success (Foundation)

- [ ] All tools installed and verified (SA-01)
- [ ] Config validated (SA-02)
- [ ] Database initialized (SA-03)
- [ ] Tauri GUI functional (SA-14)
- [ ] Checkpoint system working (SA-18)
- [ ] Pre-flight checks passing (SA-19)

### Phase 2 Success (Sample Transfer)

- [ ] 500 files transferred successfully
- [ ] 100% checksum match
- [ ] Manual verification: 20/20 files correct
- [ ] No data loss
- [ ] Rollback tested and working

### Phase 3 Success (Full Transfer)

- [ ] 1,590 files transferred successfully
- [ ] 100% checksum match
- [ ] Duplicates archived (6 files)
- [ ] All files renamed per pattern
- [ ] Lightroom-ready structure

### Phase 4 Success (Lightroom)

- [ ] XMP sidecars preserved
- [ ] RAW+JPG pairs verified
- [ ] Lightroom catalog synced
- [ ] No missing files in Lightroom

### Phase 5 Success (Automation)

- [ ] Daily local backup running
- [ ] Weekly cloud backup running
- [ ] Monthly reports generating
- [ ] Error recovery working

### Phase 6 Success (Production)

- [ ] All documentation complete
- [ ] Disaster recovery tested
- [ ] User trained and approved
- [ ] System handed off to production

---

## What's NOT in Scope (Explicitly Excluded)

| Feature | Reason | May Revisit |
|---------|--------|-------------|
| **AI-based photo culling** | Out of scope for v1.0 | Phase 7+ |
| **Facial recognition** | Requires additional tools | Phase 7+ |
| **Mobile app** | Beyond initial scope | Future |
| **Multi-user support** | Single-user system | Future |
| **Real-time sync** | Complex, not needed | Future |
| **Video transcoding** | Separate workflow | Future |
| **Print shop integration** | Out of scope | Future |

---

## Budget & Resource Requirements

### One-Time Costs

| Item | Cost | When |
|------|------|------|
| External backup drive (8 TB) | $150-200 | Phase 1 |
| **Total** | **$150-200** | |

### Recurring Costs

| Item | Cost | When |
|------|------|------|
| Cloudflare R2 (1.8 TB) | ~$27/month | Phase 5+ |
| **Total** | **~$27/month** | Phase 5+ |

### Time Investment (AZ)

| Phase | Estimated Time | When |
|-------|----------------|------|
| Phase 0: Setup | 2 hours | 2026-03-04 to 03-06 |
| Phase 1: Foundation | 4 hours | 2026-03-07 to 03-14 |
| Phase 2: Sample Transfer | 3 hours | 2026-03-15 to 03-21 |
| Phase 3: Full Transfer | 4 hours | 2026-03-22 to 03-28 |
| Phase 4: Lightroom | 3 hours | 2026-03-29 to 04-11 |
| Phase 5: Automation | 2 hours | 2026-04-12 to 04-25 |
| Phase 6: Handoff | 2 hours | 2026-04-26 to 05-02 |
| **Total** | **20 hours** | 11 weeks |

---

## Next Actions (Immediate)

### For AZ (User)

1. **Review DECISION_LOG_20260303.md** — Respond with decisions (6 total)
2. **Create missing folders:**
   ```bash
   cd /home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer
   mkdir -p 03_PROJECTS 04_CATALOGS 09_ARCHIVE
   ```
3. **Select sample dataset** for Phase 2 (recommend: 2025-01-07 and 2025-01-09, 520 files)
4. **Confirm external backup drive path** for `backup.local_path` in settings.yaml

### For Milo (Agent)

1. **Await AZ decisions** from DECISION_LOG_20260303.md
2. **Update rename_batch.py** with per-day sequence + sidecar generation
3. **Spawn SA-18** (checkpoint-system) after decisions received
4. **Spawn SA-19** (preflight-check) after decisions received
5. **Schedule Phase 2** after folder creation complete

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-03-03 | Initial project plan | AZ |
| 2.0 | 2026-03-03 | Strategic review updates, new subagents, revised timeline | SA-16 |

---

**Plan End**  
**Status:** Awaiting User Decisions (DECISION_LOG_20260303.md)  
**Next Milestone:** Phase 0 Setup (2026-03-04)
