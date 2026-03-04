# MediaAuditOrganizer — Decision Log

**Generated:** 2026-03-03 23:48 MST  
**Prepared by:** SA-16 (Project Planner Subagent)  
**Purpose:** Track decisions requiring user input before proceeding

---

## Decision #1: Folder Structure — Add Missing Folders

**Context:** Current structure has gaps (missing 03_PROJECTS/, 04_CATALOGS/, 09_ARCHIVE/)

### Options

**Option A: Minimal (Current Structure)**
- Keep existing 00-08 numbering
- Create only 03_PROJECTS/ when needed
- No 04_CATALOGS/ (Lightroom disabled anyway)
- No 09_ARCHIVE/

**Pros:**
- ✅ No disruption to current workflow
- ✅ Fewer folders to manage
- ✅ Matches current settings.yaml

**Cons:**
- ❌ No dedicated space for active client projects
- ❌ Cannot enable Lightroom integration later without restructuring
- ❌ No cold storage strategy for old files

**Option B: Recommended (Full Structure)**
- Create all folders: 03_PROJECTS/, 04_CATALOGS/, 09_ARCHIVE/
- Implement date-based subdirs in 01_PHOTOS/ (`YYYY/YYYY-MM_EventName/RAW/`)
- Separate RAW/JPG into subfolders

**Pros:**
- ✅ Professional DAM workflow standard
- ✅ Ready for Lightroom integration
- ✅ Clear separation: active projects vs. master library vs. archive
- ✅ Scalable to 100,000+ files

**Cons:**
- ⚠️ Requires initial folder creation (5 minutes)
- ⚠️ Slightly more complex navigation

**Option C: Hybrid (Compromise)**
- Create 03_PROJECTS/ only
- Use flat structure in 01_PHOTOS/ (no date subdirs)
- Add 09_ARCHIVE/ later when needed

**Pros:**
- ✅ Middle ground complexity
- ✅ Supports client work immediately

**Cons:**
- ❌ Still lacks Lightroom readiness
- ❌ Flat structure becomes unmanageable at scale

### Recommendation: **Option B (Full Structure)**

**Rationale:** You're building a professional-grade system for 10,000+ files. The 30 minutes spent creating proper folder structure now saves hours of restructuring later. Lightroom integration is likely inevitable for a photography workflow.

**Impact if Accepted:**
- Create folders: `03_PROJECTS/`, `04_CATALOGS/`, `09_ARCHIVE/`
- Update settings.yaml to reflect new paths
- Future ingests go to `01_PHOTOS/YYYY/YYYY-MM_EventName/RAW/` structure

**Impact if Rejected:**
- Continue with current structure
- Must restructure before Lightroom integration
- May need to reorganize at 5,000+ files

---

## Decision #2: Rename Pattern — Proceed or Adjust?

**Context:** SA-07 proposed `YYYY-MM-DD_HH-MM-SS_Camera_Seq.ext` pattern

### Options

**Option A: Approve As-Is**
- Use pattern exactly as proposed in rename_preview_20260303.csv
- Example: `2022-08-10_10-03-43_A7M4_0003.arw`
- Sequence resets per camera folder

**Pros:**
- ✅ Industry-standard format
- ✅ Chronologically sortable
- ✅ Already tested on 1,544 files (0 conflicts)
- ✅ Ready to execute immediately

**Cons:**
- ❌ Sequence resets per folder, not per day
- ❌ Original filename not preserved anywhere

**Option B: Approve with Adjustments**
- Use same pattern but:
  - Reset sequence per day (not per folder)
  - Create JSON sidecar with original filename
  - Add burst_index for >3 files in same second

**Pros:**
- ✅ All benefits of Option A
- ✅ Better handles multi-card shoots
- ✅ Preserves original filename for searchability
- ✅ Professional burst shot handling

**Cons:**
- ⚠️ Requires minor script updates (1-2 hours)
- ⚠️ Creates additional sidecar files

**Option C: Alternative Pattern**
- Use `YYYYMMDD_HHMMSS_Camera_Seq` (no dashes/underscores in date/time)
- Example: `20220810_100343_A7M4_0003.arw`

**Pros:**
- ✅ Shorter filenames
- ✅ No special characters (max compatibility)

**Cons:**
- ❌ Less human-readable
- ❌ Non-standard format
- ❌ Requires pattern change in settings.yaml

### Recommendation: **Option B (Approve with Adjustments)**

**Rationale:** The core pattern is excellent. Minor adjustments (sidecar preservation, per-day sequence) add robustness without complexity. This is a one-time script update that prevents future issues.

**Impact if Accepted:**
- Update `scripts/rename_batch.py` to reset sequence per day
- Add JSON sidecar generation
- Delay rename execution by 1-2 days for script updates

**Impact if Rejected:**
- Proceed with current rename_preview_20260303.csv
- May need manual intervention for multi-card shoots
- Original filenames not recoverable

---

## Decision #3: Duplicate Handling — Archive or Delete?

**Context:** 6 duplicate files found (1.32 MB recoverable)

### Options

**Option A: Archive for 30 Days (Recommended)**
- Move duplicates to `05_BACKUPS/duplicates/YYYY-MM-DD/`
- Generate manifest with hashes
- Flag for review after 30 days
- Require manual confirmation before deletion

**Pros:**
- ✅ Safe — no accidental data loss
- ✅ Professional standard workflow
- ✅ 30-day window to catch mistakes
- ✅ Negligible storage impact (1.32 MB)

**Cons:**
- ⚠️ Requires manual review after 30 days
- ⚠️ Temporary storage used (minimal)

**Option B: Delete Immediately**
- Delete duplicates after checksum verification
- Log deletions in database
- No archive

**Pros:**
- ✅ Immediate space recovery (1.32 MB)
- ✅ No ongoing maintenance

**Cons:**
- ❌ Risk of accidental data loss
- ❌ No recovery option if mistake discovered later
- ❌ Violates "never delete without confirmation" safety rule

**Option C: Ignore Duplicates**
- Leave duplicates in place
- No action taken
- Document in report

**Pros:**
- ✅ Zero risk
- ✅ No processing time

**Cons:**
- ❌ Wastes storage (though minimal)
- ❌ Doesn't demonstrate system capability
- ❌ Sets bad precedent for future larger duplicate sets

### Recommendation: **Option A (Archive for 30 Days)**

**Rationale:** 1.32 MB is trivial, but establishing a safe duplicate policy now prevents problems when future audits find GBs of duplicates. The 30-day archive is industry standard.

**Impact if Accepted:**
- Move 6 files to `05_BACKUPS/duplicates/2026-03-03/`
- Create `duplicates_manifest.csv` with hashes
- Schedule review for 2026-04-02

**Impact if Rejected:**
- If Option B: Immediate deletion, no recovery possible
- If Option C: No action, duplicates remain in source folders

---

## Decision #4: Lightroom Integration — Enable Now or Later?

**Context:** Lightroom integration is currently disabled in settings.yaml

### Options

**Option A: Enable Now (Read-Only)**
- Set `lightroom.enabled: true`
- Provide path to Master_Catalog.lrcat
- Extract metadata (ratings, keywords, flags)
- Do NOT update catalog paths yet

**Pros:**
- ✅ Preserves existing Lightroom work
- ✅ Enables reconciliation (find missing files)
- ✅ Read-only is safe, reversible

**Cons:**
- ⚠️ Requires catalog path configuration
- ⚠️ Adds complexity to initial setup

**Option B: Enable Later (After First Transfer)**
- Keep `lightroom.enabled: false` for now
- Complete first transfer without Lightroom
- Enable after system is stable

**Pros:**
- ✅ Simpler initial setup
- ✅ Focus on core functionality first
- ✅ Can test transfer workflow independently

**Cons:**
- ❌ Existing Lightroom metadata not preserved in first ingest
- ❌ Must re-run metadata extraction later

**Option C: Skip Lightroom Entirely**
- Never enable Lightroom integration
- Use alternative (digiKam, darktable, or custom DAM)

**Pros:**
- ✅ No Lightroom dependency
- ✅ Open source alternatives available

**Cons:**
- ❌ Loses existing Lightroom catalog work
- ❌ Requires learning new software
- ❌ Wastes 12-subagent plan investment

### Recommendation: **Option B (Enable Later)**

**Rationale:** Get the core transfer workflow working first. Lightroom integration adds complexity that's not needed for the first test ingest. Enable read-only mode after first successful transfer.

**Impact if Accepted:**
- Keep `lightroom.enabled: false` for initial tests
- Plan Lightroom enablement for Phase 2 (week 3-4)
- First ingest won't have Lightroom metadata

**Impact if Rejected:**
- If Option A: Must configure catalog path before first ingest
- If Option C: Abandon Lightroom integration entirely

---

## Decision #5: First Live Transfer — Test Dataset Size

**Context:** Planning first live transfer test

### Options

**Option A: Full Drive (55 GB, 1,590 files)**
- Transfer entire drive64gb contents
- Tests system at scale
- 2-4 hour transfer time

**Pros:**
- ✅ Tests system under realistic load
- ✅ Complete test of all workflows
- ✅ Immediate 55 GB organized library

**Cons:**
- ⚠️ 2-4 hours to complete
- ⚠️ Harder to debug if issues arise
- ⚠️ More data at risk if something goes wrong

**Option B: Sample Dataset (500 files, ~5 GB)**
- Select 1-2 shoot dates only
- Example: 2025-01-07 and 2025-01-09 (520 files)
- 15-30 minute transfer time

**Pros:**
- ✅ Fast iteration (test, debug, retest)
- ✅ Lower risk (less data)
- ✅ Easier to manually verify results

**Cons:**
- ⚠️ Doesn't test at full scale
- ⚠️ Must run again for remaining files

**Option C: Minimal Test (50 files, ~500 MB)**
- Single shoot date (e.g., 2022-08-10)
- 5-10 minute transfer time
- Multiple test runs possible

**Pros:**
- ✅ Very fast iteration
- ✅ Minimal risk
- ✅ Can test edge cases repeatedly

**Cons:**
- ❌ Doesn't represent real workload
- ❌ Must run full transfer eventually anyway

### Recommendation: **Option B (Sample Dataset: 500 files, ~5 GB)**

**Rationale:** Balance between speed and realism. 500 files tests the workflow without committing 4 hours to a single test run. If successful, proceed with remaining 1,090 files.

**Impact if Accepted:**
- Select 1-2 shoot dates from rename_preview_20260303.csv
- Transfer to `01_PHOTOS/2025/2025-01-07_Test/`
- Verify checksums, review results
- Proceed with full transfer if successful

**Impact if Rejected:**
- If Option A: Commit to 2-4 hour first test
- If Option C: Very fast test but must re-run at scale

---

## Decision #6: Backup Strategy — Local Only or Cloud Included?

**Context:** Cloud backup (R2) is currently disabled in settings.yaml

### Options

**Option A: Local Backup Only (Initial)**
- Enable `backup.local_enabled: true`
- Keep `backup.cloud_enabled: false`
- Daily local backups to external drive
- Add cloud backup later

**Pros:**
- ✅ Simpler initial setup
- ✅ No cloud costs during testing
- ✅ Faster backup times

**Cons:**
- ❌ No offsite protection initially
- ❌ Must configure cloud later

**Option B: Enable Cloud Immediately**
- Configure Cloudflare R2 bucket
- Enable `backup.cloud_enabled: true`
- Weekly cloud sync from day 1

**Pros:**
- ✅ Immediate 3-2-1 compliance
- ✅ Offsite protection from start

**Cons:**
- ⚠️ Requires R2 setup ($27/month for 1.8 TB)
- ⚠️ Initial upload takes days/weeks
- ⚠️ Adds complexity to initial testing

**Option C: No Automated Backups (Manual)**
- Disable automated backup system
- User handles backups manually
- Revisit automation later

**Pros:**
- ✅ No configuration needed
- ✅ Full control

**Cons:**
- ❌ Defeats purpose of automation
- ❌ High risk of human error
- ❌ Not sustainable for 10,000+ files

### Recommendation: **Option A (Local Backup Only, Initial)**

**Rationale:** Get local backup working perfectly first. Cloud backup can wait 2-4 weeks until core workflow is stable. The 3-2-1 rule is important, but not on day 1 of testing.

**Impact if Accepted:**
- Configure `backup.local_path` to external drive
- Test daily local backup workflow
- Plan cloud enablement for Phase 3 (week 5-6)

**Impact if Rejected:**
- If Option B: Must configure R2 credentials before first test
- If Option C: No backup automation, manual process only

---

## Summary of Decisions

| # | Decision | Recommended Option | User Action Required |
|---|----------|-------------------|---------------------|
| 1 | Folder Structure | **B: Full Structure** | Create 03_PROJECTS/, 04_CATALOGS/, 09_ARCHIVE/ |
| 2 | Rename Pattern | **B: Approve with Adjustments** | Approve script updates (1-2 hours) |
| 3 | Duplicate Handling | **A: Archive for 30 Days** | Confirm archive policy |
| 4 | Lightroom Integration | **B: Enable Later** | Keep disabled for now |
| 5 | First Transfer Size | **B: Sample Dataset (500 files)** | Select test dates |
| 6 | Backup Strategy | **A: Local Only (Initial)** | Configure local backup path |

---

## Decisions Requiring Immediate Input (P0)

**These must be decided before proceeding:**

1. ✅ **Decision #1:** Folder structure — Create missing folders? (A/B/C)
2. ✅ **Decision #2:** Rename pattern — Approve as-is or with adjustments? (A/B/C)
3. ✅ **Decision #5:** First transfer size — How large for test? (A/B/C)

**These can wait 1-2 weeks:**

4. ⏸️ **Decision #3:** Duplicate policy — Archive or delete? (A/B/C)
5. ⏸️ **Decision #4:** Lightroom — Enable now or later? (A/B/C)
6. ⏸️ **Decision #6:** Cloud backup — When to enable? (A/B/C)

---

## How to Respond

**Reply format (Telegram):**

```
DECISIONS:
1: B
2: B
3: A
4: B
5: B
6: A

NOTES: [any additional comments or constraints]
```

**Or individually:**
- "Decision 1: Option B — approved"
- "For decision 2, I prefer option A because..."
- "Decision 5: Let's go with option C instead"

---

**Decision Log End**  
**Awaiting User Input**
