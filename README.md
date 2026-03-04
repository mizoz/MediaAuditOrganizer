# MediaAuditOrganizer

**Professional Media Library Management System for Photographers and Videographers**

---

## What It Does

MediaAuditOrganizer is an automated workflow system that ingests, audits, organizes, and backs up large photo and video libraries (10,000+ assets) with checksum-verified transfers, Lightroom catalog integration, and comprehensive reporting. It transforms scattered media across multiple drives into a consistent, date-organized library with 3-2-1 backup protection.

---

## What Problem It Solves

- **Scattered media files** across multiple external drives with no consistent organization
- **Broken Lightroom references** when files are moved or drives are disconnected
- **No backup verification** — unsure if backups are complete or corrupted
- **Duplicate files** wasting storage space across drives
- **No audit trail** — cannot track what was transferred, when, or if it succeeded
- **Manual, error-prone workflows** for renaming and organizing files by date
- **No visibility** into library health, growth, or backup status

---

## System Requirements

### Minimum Requirements

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **Operating System** | macOS 12+, Windows 10+, or Linux (Pop!_OS 22.04+) | Cross-platform |
| **Python** | 3.10 or higher | Required for scripts and reports |
| **RAM** | 8 GB minimum, 16 GB recommended | For large library scans |
| **Storage** | 2x available space of source drive | For verified transfers |
| **Disk Type** | SSD recommended for library, HDD acceptable for backups | Performance |

### Required Tools (All Open Source)

| Tool | Purpose | Install Command |
|------|---------|-----------------|
| **ExifTool** | Photo metadata extraction | See installation below |
| **FFmpeg (FFprobe)** | Video metadata extraction | See installation below |
| **fd** | Fast file scanning | See installation below |
| **rclone** | Verified file transfer and backup | See installation below |
| **rdfind** | Duplicate detection | See installation below |
| **fdupes** | Duplicate verification | See installation below |

---

## Installation

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install all required tools
brew install exiftool ffmpeg fd rclone rdfind fdupes python@3.12

# Verify installations
exiftool -ver
ffprobe -version
fd --version
rclone version
```

### Windows

```powershell
# Install Chocolatey if not already installed (run PowerShell as Administrator)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install required tools
choco install exiftool ffmpeg fd rclone rdfind python -y

# Add to PATH (restart terminal after installation)
refreshenv

# Verify installations
exiftool -ver
ffprobe -version
fd --version
rclone version
```

### Linux (Pop!_OS 24.04)

```bash
# Update package lists
sudo apt update

# Install system dependencies
sudo apt install -y libimage-exiftool-perl ffmpeg python3 python3-pip python3-venv

# Install fd (not in default repos)
curl -LO https://github.com/sharkdp/fd/releases/download/v9.0.0/fd_9.0.0_amd64.deb
sudo dpkg -i fd_9.0.0_amd64.deb
rm fd_9.0.0_amd64.deb

# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Install rdfind and fdupes
sudo apt install -y rdfind fdupes

# Install Python dependencies
pip3 install jinja2 weasyprint plotly pandas

# Verify installations
exiftool -ver
ffprobe -version
fd --version
rclone version
```

---

## Configuration

### Step 1: Clone or Download the Project

```bash
cd ~/Documents
git clone https://github.com/mizoz/MediaAuditOrganizer.git
cd MediaAuditOrganizer
```

### Step 2: Create settings.yaml

Copy the example configuration file:

```bash
cp configs/settings.yaml.example configs/settings.yaml
```

### Step 3: Edit settings.yaml

Open `configs/settings.yaml` in your text editor and configure these **3 essential settings**:

```yaml
# ============================================
# ESSENTIAL SETTINGS — Edit These Three Lines
# ============================================

# 1. Your master library location (where organized files will live)
library_root: "/home/az/MediaLibrary"

# 2. Your Lightroom catalog path (for metadata extraction and sync)
lightroom_catalog: "/home/az/Lightroom/Master_Catalog.lrcat"

# 3. Backup destination (external drive or NAS path)
local_backup_path: "/mnt/backup_drive/MediaBackup"

# ============================================
# OPTIONAL SETTINGS — Customize As Needed
# ============================================

# Cloud backup (Cloudflare R2 or Backblaze B2)
cloud_backup:
  enabled: false  # Set to true to enable cloud backup
  provider: "r2"  # Options: "r2" or "b2"
  bucket_name: "your-bucket-name"
  # Credentials stored in ~/.config/rclone/rclone.conf

# File naming pattern
naming:
  photos: "{date}_{time}_{camera}_{sequence}"
  # Example output: 20250315_143022_D850_001.CR2
  
  videos: "{date}_{time}_{device}_{res}_{fps}_{sequence}"
  # Example output: 20250315_143000_D850_4K_30fps_001.MP4

# Duplicate handling
duplicates:
  exact_match: true      # Detect byte-identical duplicates
  near_match: false      # Detect similar images (slower)
  action: "flag"         # Options: "flag", "hardlink", "delete"

# Reports
reports:
  format: ["pdf", "html"]
  email_on_complete: false  # Set to true to email reports
  email_address: "your@email.com"
```

### Step 4: Configure rclone for Cloud Backup (Optional)

If enabling cloud backup, configure rclone:

```bash
rclone config
```

Follow the prompts:
1. Choose `s3` for Cloudflare R2 or `b2` for Backblaze B2
2. Enter your credentials
3. Name the remote (e.g., `myr2` or `myb2`)

Test the connection:

```bash
rclone lsd myr2:
```

---

## How to Run Each Script

### 1. Drive Ingestion (New Drive)

When you plug in a new external drive with photos/videos:

```bash
# Mount your drive (macOS/Linux auto-mounts, Windows assigns drive letter)

# Run the ingestion script
python scripts/drive_ingest.py /mnt/external_drive

# Or on Windows:
python scripts\drive_ingest.py E:\
```

**What happens:**
1. Scans drive and generates audit report (PDF)
2. Detects duplicates against existing library
3. Pauses for your approval
4. Transfers files with checksum verification
5. Organizes files by date/camera
6. Updates Lightroom catalog
7. Syncs to backup locations

**Example output:**
```
[INFO] Drive audit complete: 1,247 files (156.3 GB)
[INFO] Duplicates found: 34 files (4.2 GB recoverable)
[INFO] Report saved to: reports/per_drive/audit_20260303_200700.pdf

⚠️  REVIEW REQUIRED
Review the audit report and run:
  python scripts/approve_transfer.py audit_20260303_200700

Transfer will begin after approval.
```

### 2. Library Reconciliation (One-Time for Existing Library)

To analyze and reconcile your existing scattered library:

```bash
python scripts/reconcile_library.py --locations /mnt/drive1 /mnt/drive2 ~/Pictures
```

**What happens:**
1. Scans all specified locations
2. Parses Lightroom catalogs
3. Cross-references files vs catalog entries
4. Identifies missing files, orphans, and duplicates
5. Generates reconciliation report with prioritized action plan

**Example output:**
```
[INFO] Scanned 12,847 files across 3 locations
[INFO] Parsed 2 Lightroom catalogs (8,934 references)

RECONCILIATION RESULTS:
  ✅ Category A (In catalog + on disk): 8,234 files (64%)
  ⚠️  Category B (In catalog, missing): 1,200 files (9%)
  ⚠️  Category C (On disk, not in catalog): 1,913 files (15%)
  ⚠️  Category D (Duplicates): 1,500 files (12%)

Report saved to: reports/reconciliation/reconciliation_report.pdf
Action plan saved to: reports/reconciliation/prioritized_action_plan.md
```

### 3. Monthly Library Summary

Generate a monthly health report:

```bash
python scripts/generate_monthly_report.py --year 2026 --month 3
```

**What happens:**
1. Aggregates ingestion logs for the month
2. Calculates storage usage and growth
3. Checks backup health status
4. Generates summary report (PDF + HTML)

### 4. Backup Sync (Manual Trigger)

Manually trigger backup sync:

```bash
# Local backup only
python scripts/backup_sync.py --target local

# Cloud backup only
python scripts/backup_sync.py --target cloud

# Both targets
python scripts/backup_sync.py --target all
```

### 5. Duplicate Cleanup

Find and handle duplicates:

```bash
# Scan for duplicates (dry run)
python scripts/find_duplicates.py --scan /media_library/01_PHOTOS

# Replace duplicates with hardlinks (saves space, reversible)
python scripts/find_duplicates.py --action hardlink /media_library/01_PHOTOS

# Move duplicates to archive (safe, review before deletion)
python scripts/find_duplicates.py --action archive /media_library/01_PHOTOS
```

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MEDIA AUDIT ORGANIZER WORKFLOW                       │
└─────────────────────────────────────────────────────────────────────────────┘

                                    ┌──────────────┐
                                    │  New Drive   │
                                    │  Plugged In  │
                                    └──────┬───────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: AUDIT (Automated, 30-60 seconds for 10k files)                      │
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Scan      │ →  │  Extract    │ →  │   Detect    │ →  │  Generate   │  │
│  │   Files     │    │  Metadata   │    │ Duplicates  │    │   Report    │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                  │                  │          │
│         ▼                  ▼                  ▼                  ▼          │
│    manifest.csv      metadata.json     duplicates.txt     report.pdf       │
└──────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: USER REVIEW (Manual, 5-10 minutes)                                  │
│                                                                              │
│         ┌─────────────────────────────────────────────────┐                 │
│         │  Review audit report (PDF)                      │                 │
│         │  • Total files and size                         │                 │
│         │  • Date range                                   │                 │
│         │  • Duplicates found                             │                 │
│         │  • Recommended actions                          │                 │
│         └─────────────────────────────────────────────────┘                 │
│                                    │                                        │
│                          [APPROVE TRANSFER]                                 │
└──────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: TRANSFER (Automated, 2-4 hours for 500GB)                           │
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   rclone    │ →  │   Verify    │ →  │    Log      │ →  │   Integrity │  │
│  │   Copy      │    │  Checksums  │    │  Every File │    │    Check    │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                  │                  │          │
│         ▼                  ▼                  ▼                  ▼          │
│   pending_review/    checksums.md5    transfer.log     integrity.json     │
│                                                                              │
│                          [APPROVE ORGANIZATION]                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ PHASE 4: ORGANIZE (Automated, 10-20 minutes for 10k files)                   │
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  ExifTool   │ →  │   Move to   │ →  │  Update     │ →  │   Log       │  │
│  │   Rename    │    │ Final Dirs  │    │  Lightroom  │    │  Changes    │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                  │                  │          │
│         ▼                  ▼                  ▼                  ▼          │
│  YYYYMMDD_HHMMSS_   01_PHOTOS/2025/   Master_Catalog    rename_log.csv    │
│  D850_001.CR2       /2025-03_Event/   .lrcat updated                       │
└──────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ PHASE 5: BACKUP (Automated, runs in background)                              │
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                       │
│  │   Local     │ →  │   Cloud     │ →  │   Verify    │                       │
│  │   Backup    │    │   Backup    │    │  Checksums  │                       │
│  └─────────────┘    └─────────────┘    └─────────────┘                       │
│         │                  │                  │                               │
│         ▼                  ▼                  ▼                               │
│  /mnt/backup_drive/  myr2:media-     backup_verify.                         │
│  05_BACKUPS/daily/   backup/         log                                    │
└──────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │   Complete   │
                                    │  Eject Drive │
                                    └──────────────┘
```

---

## Troubleshooting

### Issue 1: "ExifTool not found" or "command not found: exiftool"

**Cause:** ExifTool is not installed or not in your PATH.

**Solution:**

**macOS:**
```bash
brew install exiftool
```

**Windows:**
```powershell
choco install exiftool
refreshenv
```

**Linux:**
```bash
sudo apt install libimage-exiftool-perl
```

**Verify:**
```bash
exiftool -ver
# Should output version number (e.g., 13.00)
```

---

### Issue 2: "Permission denied" when writing to library root

**Cause:** The script doesn't have write permissions to the target directory.

**Solution:**

**macOS/Linux:**
```bash
# Create the directory if it doesn't exist
mkdir -p /path/to/your/library

# Set ownership to your user
sudo chown -R $USER:$USER /path/to/your/library

# Set permissions (read/write for owner)
chmod -R 755 /path/to/your/library
```

**Windows:**
1. Right-click the folder → Properties → Security
2. Click "Edit" → Select your user account
3. Check "Full control" → Apply

---

### Issue 3: Transfer fails with "checksum mismatch" errors

**Cause:** File corruption during transfer, often due to faulty USB cable/port or drive issues.

**Solution:**

1. **Check drive health:**
   ```bash
   # macOS
   diskutil verifyVolume /Volumes/YourDrive
   
   # Linux
   sudo smartctl -a /dev/sdX
   ```

2. **Retry the transfer:**
   ```bash
   # rclone will skip already-copied files and retry failures
   python scripts/drive_ingest.py /mnt/external_drive --retry
   ```

3. **If persistent:**
   - Try a different USB cable
   - Try a different USB port (prefer USB 3.0+)
   - Check drive for errors (Windows: chkdsk, macOS: First Aid)

---

### Issue 4: Lightroom shows "missing files" after organization

**Cause:** Lightroom catalog wasn't updated after files were moved.

**Solution:**

1. **Run the Lightroom sync script:**
   ```bash
   python scripts/sync_lightroom_folders.py
   ```

2. **Or manually in Lightroom:**
   - Right-click the folder with the `?` icon
   - Choose "Find Missing Folder..."
   - Navigate to the new location
   - Click "Choose"

3. **Prevention:** Always run the ingestion workflow completely (don't interrupt before Lightroom update step).

---

### Issue 5: "Out of disk space" during transfer

**Cause:** Destination drive doesn't have enough free space.

**Solution:**

1. **Check available space:**
   ```bash
   # macOS/Linux
   df -h /path/to/library
   
   # Windows
   fsutil volume diskfree C:
   ```

2. **Free up space:**
   - Run duplicate cleanup: `python scripts/find_duplicates.py --action archive /path/to/library`
   - Move old archives to external drive
   - Delete unwanted files

3. **Requirement:** You need at least 1.5x the source drive size available for verified transfers.

---

### Issue 6: Cloud backup is too slow

**Cause:** Upload bandwidth saturation or rate limiting.

**Solution:**

1. **Limit bandwidth during business hours:**
   Edit `configs/settings.yaml`:
   ```yaml
   cloud_backup:
     bandwidth_limit: "500K"  # 500 KB/s during day
     bandwidth_limit_night: "0"  # Unlimited at night
   ```

2. **Schedule uploads for overnight:**
   ```bash
   # Run cloud backup only at night
   python scripts/backup_sync.py --target cloud --schedule overnight
   ```

3. **Prioritize recent files:**
   ```bash
   # Upload last 12 months first
   python scripts/backup_sync.py --target cloud --newer-than 2025-01-01
   ```

---

### Issue 7: Script crashes on large libraries (10k+ files)

**Cause:** Memory exhaustion during scanning.

**Solution:**

1. **Increase Python memory limit:**
   ```bash
   # Run with increased recursion limit
   python -c "import sys; sys.setrecursionlimit(10000); import scripts.reconcile_library"
   ```

2. **Scan in batches:**
   ```bash
   # Scan one folder at a time
   python scripts/reconcile_library.py --locations /mnt/drive1/2024
   python scripts/reconcile_library.py --locations /mnt/drive1/2025
   ```

3. **Use streaming mode:**
   Edit `configs/settings.yaml`:
   ```yaml
   performance:
     streaming_mode: true  # Process files one at a time
     batch_size: 100  # Process in batches of 100
   ```

---

## License

**MIT License**

Copyright (c) 2026 AZ

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

## Support

- **Documentation:** See `QUICK_START.md` for simplified setup guide
- **Issue Tracker:** https://github.com/mizoz/MediaAuditOrganizer/issues
- **Email:** zalabany3@gmail.com

---

**Version:** 1.0  
**Last Updated:** 2026-03-03  
**Maintained by:** AZ
