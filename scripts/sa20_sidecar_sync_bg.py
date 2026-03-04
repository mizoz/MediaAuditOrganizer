#!/usr/bin/env python3
"""
SA-20 Recovery: Sidecar Sync Completion

Background job that completes remaining sidecar JSON files and creates manifest.
Continues from previous progress (450/500 done) to finish remaining 50 sidecars.

Usage:
    python scripts/sa20_sidecar_sync_bg.py --task-id TASK_...
"""

import argparse
import csv
import hashlib
import json
import logging
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Database path
DB_PATH = Path(__file__).parent.parent / "06_METADATA" / "media_audit.db"

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "07_LOGS"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging(task_id: str):
    """Configure logging for this task."""
    log_file = LOG_DIR / f"task_{task_id}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(f"SA20_{task_id}")


def update_heartbeat(task_id: str, progress: float, status: str, message: str = ""):
    """Update execution_logs with heartbeat."""
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE execution_logs
            SET last_heartbeat = ?,
                progress_pct = ?,
                status = ?,
                status_message = ?
            WHERE task_id = ?
        """, (datetime.now().isoformat(), progress, status, message, task_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Warning: Failed to update heartbeat: {e}")
    finally:
        if conn:
            conn.close()


def compute_sha256(filepath: Path) -> Optional[str]:
    """Compute SHA256 hash of a file."""
    try:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (PermissionError, OSError):
        return None


def extract_metadata(filepath: Path) -> Dict[str, Any]:
    """Extract metadata using exiftool."""
    try:
        result = subprocess.run(
            ["exiftool", "-json", str(filepath)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return {}
        
        metadata_list = json.loads(result.stdout)
        if not metadata_list:
            return {}
        
        raw = metadata_list[0]
        
        return {
            "camera_make": raw.get("Make"),
            "camera_model": raw.get("Model"),
            "lens_model": raw.get("LensModel"),
            "date_taken": raw.get("DateTimeOriginal"),
            "focal_length": raw.get("FocalLength"),
            "iso": raw.get("ISO"),
            "aperture": raw.get("FNumber"),
            "shutter_speed": raw.get("ExposureTime"),
            "gps_latitude": raw.get("GPSLatitude"),
            "gps_longitude": raw.get("GPSLongitude"),
        }
    except Exception:
        return {}


def load_rename_preview() -> List[Dict]:
    """Load rename preview CSV."""
    csv_path = Path(__file__).parent.parent / "08_REPORTS" / "rename_preview_20260303.csv"
    
    if not csv_path.exists():
        return []
    
    entries = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(dict(row))
    
    return entries


def count_existing_sidecars(sidecars_dir: Path) -> int:
    """Count existing sidecar JSON files."""
    if not sidecars_dir.exists():
        return 0
    
    count = 0
    for f in sidecars_dir.rglob("*.json"):
        # Skip manifest files
        if "manifest" not in f.name.lower():
            count += 1
    
    return count


def generate_sidecar(entry: Dict, idx: int, sidecars_dir: Path) -> Optional[Dict]:
    """Generate sidecar JSON for a media file."""
    old_path = entry.get('old_path', entry.get('source', ''))
    new_filename = entry.get('new_filename', entry.get('new_path', Path(old_path).name))
    
    if not old_path:
        return None
    
    filepath = Path(old_path)
    
    if not filepath.exists():
        return None
    
    # Compute hash
    file_hash = compute_sha256(filepath)
    
    # Extract metadata
    metadata = extract_metadata(filepath)
    
    # Generate sidecar
    sidecar = {
        "sidecar_id": f"SC_{idx+1:05d}",
        "created": datetime.now().isoformat(),
        "original": {
            "filename": filepath.name,
            "path": str(filepath),
            "hash": file_hash,
            "size": filepath.stat().st_size if filepath.exists() else 0
        },
        "planned": {
            "filename": new_filename,
            "path": None  # Will be set during transfer
        },
        "metadata": metadata,
        "transfer": {
            "status": "pending",
            "started_at": None,
            "completed_at": None,
            "verified": False
        }
    }
    
    # Save sidecar
    sidecar_file = sidecars_dir / f"{filepath.stem}.json"
    sidecar_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(sidecar_file, 'w', encoding='utf-8') as f:
        json.dump(sidecar, f, indent=2)
    
    return sidecar


def main():
    parser = argparse.ArgumentParser(description="SA-20 Sidecar Sync Background Job")
    parser.add_argument("--task-id", required=True, help="Task ID from task_manager")
    parser.add_argument("--target", type=int, default=500, help="Target number of sidecars")
    args = parser.parse_args()

    task_id = args.task_id
    target = args.target
    logger = setup_logging(task_id)

    logger.info(f"🚀 SA-20 Sidecar Sync started (Task: {task_id})")
    logger.info(f"   Target: {target} sidecars")

    # Setup directories
    sidecars_dir = Path(__file__).parent.parent / "05_SIDECARS"
    sidecars_dir.mkdir(parents=True, exist_ok=True)

    # Count existing sidecars
    existing_count = count_existing_sidecars(sidecars_dir)
    logger.info(f"📊 Existing sidecars: {existing_count}")
    
    if existing_count >= target:
        logger.info("✅ Target already reached - marking complete")
        update_heartbeat(task_id, 100, "COMPLETED", f"{existing_count} sidecars already exist")
        sys.exit(0)

    # Load rename preview
    logger.info("📁 Loading rename preview...")
    entries = load_rename_preview()
    
    if not entries:
        logger.error("❌ No rename preview found")
        update_heartbeat(task_id, 0, "FAILED", "No rename preview found")
        sys.exit(1)
    
    logger.info(f"   Loaded {len(entries)} entries")

    # Generate remaining sidecars
    needed = target - existing_count
    logger.info(f"📝 Generating {needed} remaining sidecars...")
    
    generated = 0
    errors = 0
    sidecars = []

    for idx, entry in enumerate(entries):
        if generated >= needed:
            break
        
        # Update heartbeat every 10 sidecars
        if generated % 10 == 0 and generated > 0:
            progress = (generated / needed) * 100
            update_heartbeat(task_id, progress, "RUNNING", f"Generated {generated}/{needed}")

        try:
            sidecar = generate_sidecar(entry, existing_count + generated, sidecars_dir)
            if sidecar:
                sidecars.append(sidecar)
                generated += 1
            else:
                errors += 1
        except Exception as e:
            logger.warning(f"⚠️  Failed to generate sidecar: {e}")
            errors += 1

    logger.info(f"✅ Generated {generated} sidecars")
    logger.info(f"   Errors: {errors}")

    # Create sidecar manifest
    logger.info("📋 Creating sidecar manifest...")
    update_heartbeat(task_id, 80, "RUNNING", "Creating manifest")
    
    total_sidecars = existing_count + generated
    
    manifest = {
        "metadata": {
            "created": datetime.now().isoformat(),
            "task_id": task_id,
            "version": "1.0",
            "total_sidecars": total_sidecars,
            "generated_this_run": generated,
            "errors": errors,
            "status": "complete"
        },
        "sidecars": sidecars,
        "summary": {
            "target": target,
            "achieved": total_sidecars,
            "percentage": (total_sidecars / target) * 100 if target > 0 else 0,
            "complete": total_sidecars >= target
        }
    }
    
    manifest_file = sidecars_dir / f"sidecar_manifest_{task_id}.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"✅ Manifest saved: {manifest_file}")

    # Update database - mark manifest as complete
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO execution_logs (task_id, task_type, status, progress_pct, completed_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (f"MANIFEST_{task_id}", "SIDECAR_MANIFEST", "COMPLETED", 100, 
              datetime.now().isoformat(), json.dumps({"sidecars": total_sidecars, "manifest": str(manifest_file)})))
        conn.commit()
    except sqlite3.Error as e:
        logger.warning(f"⚠️  Failed to update database: {e}")
    finally:
        if conn:
            conn.close()

    # Final heartbeat
    logger.info(f"✅ SA-20 Sidecar Sync complete")
    logger.info(f"   Total sidecars: {total_sidecars}/{target}")
    logger.info(f"   Generated: {generated}")
    logger.info(f"   Manifest: {manifest_file}")
    
    update_heartbeat(task_id, 100, "COMPLETED", f"{total_sidecars} sidecars, manifest complete")

    sys.exit(0 if errors == 0 else 1)


if __name__ == "__main__":
    main()
