# Quick Start Guide — MediaAuditOrganizer

**For Non-Technical Users — Get Started in 15 Minutes**

---

## Section 1: What to Install

Copy and paste these commands into your terminal (one at a time).

### If You're on Mac:

```bash
# Step 1: Install Homebrew (if you don't have it)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Step 2: Install all required tools
brew install exiftool ffmpeg fd rclone rdfind fdupes python@3.12

# Step 3: Verify installation
exiftool -ver
```

**Expected output:** A version number like `13.00`

---

### If You're on Windows:

```powershell
# Step 1: Install Chocolatey (run PowerShell as Administrator)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Step 2: Install all required tools
choco install exiftool ffmpeg fd rclone rdfind python -y

# Step 3: Restart your terminal, then verify
exiftool -ver
```

**Expected output:** A version number like `13.00`

---

### If You're on Linux (Pop!_OS):

```bash
# Step 1: Install all required tools
sudo apt update
sudo apt install -y libimage-exiftool-perl ffmpeg python3 python3-pip rdfind fdupes

# Step 2: Install fd (fast file finder)
curl -LO https://github.com/sharkdp/fd/releases/download/v9.0.0/fd_9.0.0_amd64.deb
sudo dpkg -i fd_9.0.0_amd64.deb
rm fd_9.0.0_amd64.deb

# Step 3: Install rclone
curl https://rclone.org/install.sh | sudo bash

# Step 4: Install Python dependencies
pip3 install jinja2 weasyprint plotly pandas

# Step 5: Verify installation
exiftool -ver
```

**Expected output:** A version number like `13.00`

---

## Section 2: What to Configure Once

After installation, you need to edit **3 lines** in one file.

### Step 1: Open the Settings File

Navigate to where you downloaded MediaAuditOrganizer, then open:

```
configs/settings.yaml
```

Use any text editor (Notepad, TextEdit, VS Code, etc.)

---

### Step 2: Edit These 3 Lines

Find these lines near the top of the file:

```yaml
library_root: "/home/az/MediaLibrary"
lightroom_catalog: "/home/az/Lightroom/Master_Catalog.lrcat"
local_backup_path: "/mnt/backup_drive/MediaBackup"
```

**Change them to match your system:**

| Setting | What to Put | Example |
|---------|-------------|---------|
| `library_root` | Where you want your organized photos to live | `C:\Users\YourName\Pictures\MediaLibrary` (Windows)<br>`/Users/YourName/Pictures/MediaLibrary` (Mac)<br>`/home/az/MediaLibrary` (Linux) |
| `lightroom_catalog` | Where your Lightroom catalog is | `C:\Users\YourName\Pictures\Lightroom\Master_Catalog.lrcat` (Windows)<br>`/Users/YourName/Pictures/Lightroom/Master_Catalog.lrcat` (Mac)<br>`/home/az/Lightroom/Master_Catalog.lrcat` (Linux) |
| `local_backup_path` | Where your backup drive is mounted | `E:\MediaBackup` (Windows)<br>`/Volumes/BackupDrive/MediaBackup` (Mac)<br>`/mnt/backup_drive/MediaBackup` (Linux) |

---

### Step 3: Save the File

Save `settings.yaml` and close it. You're done with configuration!

---

## Section 3: What to Do Every Time You Plug in a New Drive

**Three simple steps:**

### Step 1: Run the Ingest Script

Open your terminal and run:

```bash
# Replace /mnt/external_drive with your drive path
# Windows example: python scripts\drive_ingest.py E:\
# Mac example: python scripts/drive_ingest.py /Volumes/YOUR_DRIVE

python scripts/drive_ingest.py /mnt/external_drive
```

**Don't know your drive path?**

- **Windows:** Open File Explorer, look at the drive letter (e.g., `E:\`)
- **Mac:** Open Finder, your drive appears under "Locations" — the path is `/Volumes/DriveName`
- **Linux:** Run `ls /mnt/` or `df -h` to see mounted drives

---

### Step 2: Review the Report

The script will generate a PDF report and tell you where it is. Open it and check:

- ✅ Total number of files found
- ✅ Total size (make sure it fits on your destination)
- ✅ Any duplicates flagged

**If everything looks good, run:**

```bash
python scripts/approve_transfer.py audit_YYYYMMDD_HHMMSS
```

(The script will tell you the exact audit ID to use)

---

### Step 3: Wait for Completion

The transfer will now run automatically. This takes:

- **100 GB:** ~30-60 minutes
- **500 GB:** ~2-4 hours
- **1 TB:** ~4-8 hours

**You can walk away — it's fully automated.**

When it's done, you'll see:

```
✅ Transfer complete: 1,247 files organized
✅ Backup synced
✅ Lightroom catalog updated

You can safely eject your drive now.
```

**Eject your drive and you're done!**

---

## Section 4: Where to Find Your Reports

All reports are saved in the `reports/` folder:

```
MediaAuditOrganizer/
└── reports/
    ├── per_drive/          # Individual drive audit reports
    │   ├── audit_20260303_200700.pdf
    │   └── audit_20260303_200700.html
    │
    ├── monthly_summaries/  # Monthly library summaries
    │   └── 2026-03_summary.pdf
    │
    └── reconciliation/     # One-time library analysis (if run)
        └── reconciliation_report.pdf
```

**To view a report:**

- **PDF:** Double-click to open in your PDF reader
- **HTML:** Double-click to open in your web browser

**Reports are also emailed to you** if you enabled email in `settings.yaml`.

---

## Section 5: What to Do If Something Goes Wrong

### Problem 1: "Command not found" or "ExifTool not found"

**What happened:** A tool didn't install correctly.

**Fix:**

1. Re-run the installation commands from Section 1
2. Restart your terminal/computer
3. Try running `exiftool -ver` again

If it still doesn't work, reinstall that specific tool:

```bash
# Mac
brew reinstall exiftool

# Windows
choco reinstall exiftool

# Linux
sudo apt reinstall libimage-exiftool-perl
```

---

### Problem 2: "Permission denied" error

**What happened:** The script can't write to the folder you specified.

**Fix:**

**Mac/Linux:**
```bash
# Create the folder if it doesn't exist
mkdir -p /path/to/your/library

# Give yourself ownership
sudo chown -R $USER:$USER /path/to/your/library
```

**Windows:**

1. Right-click the folder → Properties → Security
2. Click "Edit" → Select your user
3. Check "Full control" → Click "Apply"

Then try running the script again.

---

### Problem 3: Transfer stops halfway or says "checksum mismatch"

**What happened:** The file got corrupted during transfer (bad cable, loose connection, etc.)

**Fix:**

1. **Don't panic** — no files were deleted
2. Check your USB cable and try a different port
3. Run the script again with the `--retry` flag:

```bash
python scripts/drive_ingest.py /mnt/external_drive --retry
```

The script will skip already-copied files and only retry the failed ones.

---

## Still Stuck?

1. **Check the logs:** Look in `logs/` folder for detailed error messages
2. **Read the full docs:** See `README.md` for detailed troubleshooting
3. **Open an issue:** https://github.com/mizoz/MediaAuditOrganizer/issues
4. **Email for help:** zalabany3@gmail.com

---

**That's it!** You now have a fully automated media library management system.

**Next steps:**
- Run your first drive ingest (Section 3)
- Optionally run library reconciliation for existing files: `python scripts/reconcile_library.py`
- Set up cloud backup in `settings.yaml` (optional)

---

**Quick Reference Card**

| Task | Command |
|------|---------|
| Ingest new drive | `python scripts/drive_ingest.py /path/to/drive` |
| Approve transfer | `python scripts/approve_transfer.py audit_ID` |
| Monthly report | `python scripts/generate_monthly_report.py --year 2026 --month 3` |
| Find duplicates | `python scripts/find_duplicates.py --scan /path/to/library` |
| Sync backups | `python scripts/backup_sync.py --target all` |

---

**Version:** 1.0  
**Last Updated:** 2026-03-03
