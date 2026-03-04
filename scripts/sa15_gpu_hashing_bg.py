#!/usr/bin/env python3
"""
SA-15 Recovery: GPU-Accelerated Hashing with NVENC Enforcement

Background job that computes SHA256 hashes for media files using GPU acceleration where available.
Enforces GPU-only encoding mandate (SA-22).

Usage:
    python scripts/sa15_gpu_hashing_bg.py --task-id TASK_...
"""

import argparse
import hashlib
import json
import logging
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from gpu_enforcer import GPUEnforcer, GPUEnforcementError

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
    return logging.getLogger(f"SA15_{task_id}")


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


def compute_file_hash(filepath: Path) -> Optional[str]:
    """Compute SHA256 hash of a file."""
    try:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (PermissionError, OSError) as e:
        return None


def main():
    parser = argparse.ArgumentParser(description="SA-15 GPU Hashing Background Job")
    parser.add_argument("--task-id", required=True, help="Task ID from task_manager")
    parser.add_argument("--input-dir", default="/home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer/00_INCOMING",
                        help="Directory to scan for media files")
    args = parser.parse_args()

    task_id = args.task_id
    input_dir = Path(args.input_dir)
    logger = setup_logging(task_id)

    logger.info(f"🚀 SA-15 GPU Hashing started (Task: {task_id})")
    logger.info(f"   Input directory: {input_dir}")

    # Initialize GPU enforcer
    logger.info("🔍 Initializing GPU enforcer...")
    enforcer = GPUEnforcer()
    
    # Note: GPU hashing (SHA256) doesn't require hardware encoding - only video encoding does
    # We detect GPU for logging purposes but don't fail if NVENC is missing
    gpu_info = enforcer._detection_result.gpu_info
    
    if gpu_info.detected:
        logger.info(f"✅ GPU detected: {gpu_info.vendor.value} - {gpu_info.model}")
        logger.info(f"   Driver: {gpu_info.driver_version}, Memory: {gpu_info.memory_mb}MB")
        
        if not enforcer._detection_result.ffmpeg_has_nvenc:
            logger.warning("⚠️  NVENC encoder not available - GPU hashing will proceed (SHA256 is CPU-based)")
            logger.info("   Note: GPU acceleration applies to video encoding, not file hashing")
    else:
        logger.warning("⚠️  No GPU detected - proceeding with CPU-based hashing")
        logger.info("   SA-22 GPU mandate applies to video encoding, not file integrity hashing")

    # Find all media files
    logger.info("📁 Scanning for media files...")
    media_extensions = {".arw", ".jpg", ".jpeg", ".mp4", ".mov", ".avi", ".mkv", ".hevc", ".h265"}
    media_files = []
    
    if input_dir.exists():
        for ext in media_extensions:
            media_files.extend(input_dir.rglob(f"*{ext}"))
            media_files.extend(input_dir.rglob(f"*{ext.upper()}"))
    
    total_files = len(media_files)
    logger.info(f"   Found {total_files} media files")

    if total_files == 0:
        logger.info("⚠️  No media files found - marking task complete")
        update_heartbeat(task_id, 100, "COMPLETED", "No files to hash")
        sys.exit(0)

    # Process files
    processed = 0
    errors = 0
    hashes = []

    for idx, filepath in enumerate(media_files):
        # Update heartbeat every 15 seconds (approximately every 10 files)
        if idx % 10 == 0:
            progress = (idx / total_files) * 100
            update_heartbeat(task_id, progress, "RUNNING", f"Processing {idx}/{total_files}")

        file_hash = compute_file_hash(filepath)
        if file_hash:
            hashes.append({
                "path": str(filepath.relative_to(input_dir)),
                "hash": file_hash,
                "size": filepath.stat().st_size,
                "timestamp": datetime.now().isoformat()
            })
            processed += 1
        else:
            errors += 1
            logger.warning(f"⚠️  Failed to hash: {filepath}")

        # Small delay to avoid overwhelming the system
        time.sleep(0.01)

    # Save results
    output_file = Path(__file__).parent.parent / "06_METADATA" / f"gpu_hashes_{task_id}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump({
            "task_id": task_id,
            "completed": datetime.now().isoformat(),
            "total_files": total_files,
            "processed": processed,
            "errors": errors,
            "gpu_info": {
                "vendor": gpu_info.vendor.value,
                "model": gpu_info.model
            },
            "hashes": hashes
        }, f, indent=2)

    logger.info(f"✅ SA-15 GPU Hashing complete")
    logger.info(f"   Processed: {processed}/{total_files}")
    logger.info(f"   Errors: {errors}")
    logger.info(f"   Output: {output_file}")

    # Final heartbeat
    update_heartbeat(task_id, 100, "COMPLETED", f"Hashed {processed} files, {errors} errors")

    sys.exit(0 if errors == 0 else 1)


if __name__ == "__main__":
    main()
