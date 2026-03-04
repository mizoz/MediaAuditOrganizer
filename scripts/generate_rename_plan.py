#!/usr/bin/env python3
"""
Generate dry-run rename plan based on audit CSV and rename rules.
"""

import csv
import hashlib
from datetime import datetime
from pathlib import Path
import re

# Configuration
WORKSPACE = Path("/home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer")
AUDIT_CSV = WORKSPACE / "00_INCOMING" / "audit_20260303_230705" / "audit_20260303_233003.csv"
OUTPUT_CSV = WORKSPACE / "08_REPORTS" / "rename_preview_20260303.csv"
LOG_FILE = WORKSPACE / "07_LOGS" / "rename_plan_20260303.log"

# Camera model mapping (from rename_rules.yaml)
CAMERA_MAP = {
    "Nikon D850": "D850",
    "Canon EOS R5": "R5",
    "Sony ILCE-7M3": "A7III",
    "Sony ILCE-7RM4": "A7RIV",
    "Sony ILCE-7M4": "A7M4",
    "Sony ILCE-7RM4A": "A7RIVA",
    "Fujifilm X-T4": "XT4",
    "DJI Mavic 3": "Mavic3",
    "GoPro HERO11 Black": "GoPro11",
    "Apple iPhone 14 Pro": "iPhone14Pro",
    "Apple iPhone 15 Pro Max": "iPhone15ProMax",
    "NIKON D750": "D750",
}

# Photo extensions
PHOTO_EXTS = {'.arw', '.jpg', '.jpeg', '.nef', '.cr2', '.cr3', '.dng', '.heic', '.png'}

def normalize_camera_model(model):
    """Normalize camera model name using the mapping."""
    if not model:
        return "UNK"
    # Try exact match first
    if model in CAMERA_MAP:
        return CAMERA_MAP[model]
    # Try case-insensitive match
    for key, value in CAMERA_MAP.items():
        if key.lower() == model.lower():
            return value
    # Fallback: use last part of model name
    parts = model.split()
    if parts:
        return parts[-1].replace(" ", "")
    return "UNK"

def parse_date_taken(date_str):
    """Parse EXIF date format (YYYY:MM:DD HH:MM:SS) to datetime."""
    if not date_str:
        return None
    try:
        # Try EXIF format first: "2022:08:10 10:03:43"
        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        pass
    try:
        # Try ISO format: "2022-08-10T04:03:43.410000"
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        pass
    return None

def generate_new_filename(row, sequence_num):
    """Generate new filename based on rename rules."""
    ext = Path(row['filename']).suffix.lower()
    
    # Only process photo files
    if ext not in PHOTO_EXTS:
        return None, "not_photo"
    
    # Parse date taken
    date_taken = parse_date_taken(row.get('date_taken', ''))
    if not date_taken:
        # Fallback to file modified date
        date_taken = parse_date_taken(row.get('modified', ''))
    
    if not date_taken:
        return None, "no_date"
    
    # Get camera model
    camera_make = row.get('camera_make', '')
    camera_model = row.get('camera_model', '')
    full_camera = f"{camera_make} {camera_model}".strip()
    camera_short = normalize_camera_model(full_camera)
    
    # Build new filename: YYYY-MM-DD_HH-MM-SS_Camera_Seq.ext
    date_part = date_taken.strftime("%Y-%m-%d")
    time_part = date_taken.strftime("%H-%M-%S")
    seq_part = f"{sequence_num:04d}"
    
    new_name = f"{date_part}_{time_part}_{camera_short}_{seq_part}{ext}"
    
    return new_name, "ok"

def main():
    # Ensure output directories exist
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    log_lines = []
    log_lines.append(f"Rename Plan Generation Log")
    log_lines.append(f"Generated: {datetime.now().isoformat()}")
    log_lines.append(f"Audit CSV: {AUDIT_CSV}")
    log_lines.append(f"=" * 60)
    
    # Read audit CSV
    files_to_rename = []
    with open(AUDIT_CSV, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            files_to_rename.append(row)
    
    log_lines.append(f"Total files in audit: {len(files_to_rename)}")
    
    # Group files by date for sequence numbering
    # Reset sequence on date change (as per rename_rules.yaml)
    files_by_date = {}
    for row in files_to_rename:
        date_taken = parse_date_taken(row.get('date_taken', ''))
        if not date_taken:
            date_taken = parse_date_taken(row.get('modified', ''))
        
        if date_taken:
            date_key = date_taken.strftime("%Y-%m-%d")
        else:
            date_key = "UNKNOWN_DATE"
        
        if date_key not in files_by_date:
            files_by_date[date_key] = []
        files_by_date[date_key].append(row)
    
    log_lines.append(f"Files grouped by {len(files_by_date)} unique dates")
    
    # Generate rename plan
    rename_plan = []
    conflicts = {}  # new_path -> list of old_paths
    stats = {
        'total': 0,
        'renamed': 0,
        'skipped_not_photo': 0,
        'skipped_no_date': 0,
        'conflicts': 0,
    }
    
    # Process each date group
    for date_key in sorted(files_by_date.keys()):
        date_files = files_by_date[date_key]
        # Sort by time within date for consistent sequencing
        date_files.sort(key=lambda r: r.get('date_taken', '') or r.get('modified', ''))
        
        seq_num = 1
        for row in date_files:
            stats['total'] += 1
            old_path = row['path']
            old_name = row['filename']
            ext = Path(old_name).suffix.lower()
            
            new_name, reason = generate_new_filename(row, seq_num)
            
            if reason == "not_photo":
                stats['skipped_not_photo'] += 1
                log_lines.append(f"SKIP (not photo): {old_name}")
                continue
            elif reason == "no_date":
                stats['skipped_no_date'] += 1
                log_lines.append(f"SKIP (no date): {old_name}")
                continue
            
            # Build new path (same directory as old)
            old_dir = str(Path(old_path).parent)
            new_path = f"{old_dir}/{new_name}"
            
            # Check for conflicts
            conflict_key = new_path.lower()
            if conflict_key in conflicts:
                conflicts[conflict_key].append(old_path)
                stats['conflicts'] += 1
                log_lines.append(f"CONFLICT: {new_name} <- {old_name} (also: {conflicts[conflict_key][0]})")
            else:
                conflicts[conflict_key] = [old_path]
            
            rename_plan.append({
                'old_path': old_path,
                'new_path': new_path,
                'reason': f"rename_{ext[1:]}",
                'conflict_check': 'CONFLICT' if conflict_key in conflicts and len(conflicts[conflict_key]) > 1 else 'ok'
            })
            
            stats['renamed'] += 1
            seq_num += 1
    
    # Write preview CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['old_path', 'new_path', 'reason', 'conflict_check']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rename_plan)
    
    log_lines.append(f"=" * 60)
    log_lines.append(f"Summary:")
    log_lines.append(f"  Total files processed: {stats['total']}")
    log_lines.append(f"  Files to rename: {stats['renamed']}")
    log_lines.append(f"  Skipped (not photo): {stats['skipped_not_photo']}")
    log_lines.append(f"  Skipped (no date): {stats['skipped_no_date']}")
    log_lines.append(f"  Conflicts detected: {stats['conflicts']}")
    log_lines.append(f"")
    log_lines.append(f"Output written to: {OUTPUT_CSV}")
    
    # Write log file
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log_lines))
    
    # Print summary
    print('\n'.join(log_lines))
    
    # Report conflicts for manual review
    conflict_count = sum(1 for paths in conflicts.values() if len(paths) > 1)
    if conflict_count > 0:
        print(f"\n⚠️  {conflict_count} path conflicts detected - flagged for manual review")

if __name__ == '__main__':
    main()
