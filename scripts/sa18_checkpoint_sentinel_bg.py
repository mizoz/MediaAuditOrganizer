#!/usr/bin/env python3
"""
SA-18 Recovery: Checkpoint Sentinel & Shadow Manifest

Background job that creates checkpoint system for rollback/recovery.
Generates shadow manifest and enables resume-from-failure capability.

Usage:
    python scripts/sa18_checkpoint_sentinel_bg.py --task-id TASK_...
"""

import argparse
import csv
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

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
    return logging.getLogger(f"SA18_{task_id}")


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


def generate_operation_id(idx: int, base_timestamp: datetime) -> str:
    """Generate unique operation ID."""
    return f"OP_{base_timestamp.strftime('%Y%m%d_%H%M%S')}_{idx+1:04d}"


def create_shadow_manifest(entries: List[Dict], limit: int = 500) -> Dict:
    """Create shadow manifest from rename preview entries."""
    base_timestamp = datetime.now()
    operations = []
    
    for idx, entry in enumerate(entries[:limit]):
        op_id = generate_operation_id(idx, base_timestamp)
        
        operation = {
            "operation_id": op_id,
            "original_path": entry.get('old_path', entry.get('source', '')),
            "new_path": entry.get('new_path', entry.get('destination', '')),
            "original_filename": entry.get('old_filename', Path(entry.get('old_path', '')).name),
            "new_filename": entry.get('new_filename', Path(entry.get('new_path', '')).name),
            "hash_before": "",  # Will be computed during transfer
            "hash_after": "",   # Will be computed after transfer
            "timestamp": base_timestamp.isoformat(),
            "status": "pending",
            "file_size": int(entry.get('size', 0) or 0),
            "error": "",
            "rolled_back": False,
            "checkpoint_id": f"CP_{op_id}"
        }
        operations.append(operation)
    
    manifest = {
        "metadata": {
            "created": base_timestamp.isoformat(),
            "version": "2.0",
            "total_operations": len(operations),
            "scope": "first_500_files",
            "source_drive": "/media/az/drive64gb",
            "description": "Shadow manifest for checkpoint/rollback system - SA-18 Recovery",
            "task_id": None  # Will be set by caller
        },
        "operations": operations,
        "checkpoints": {
            "enabled": True,
            "directory": str(Path(__file__).parent.parent / "06_METADATA" / "checkpoints"),
            "auto_save_interval": 10,  # Save checkpoint every 10 operations
            "rollback_enabled": True
        }
    }
    
    return manifest


def create_checkpoint_files(manifest: Dict, task_id: str):
    """Create individual checkpoint files for each operation."""
    checkpoints_dir = Path(__file__).parent.parent / "06_METADATA" / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    
    for op in manifest["operations"]:
        checkpoint = {
            "checkpoint_id": op["checkpoint_id"],
            "operation_id": op["operation_id"],
            "created": datetime.now().isoformat(),
            "task_id": task_id,
            "original_path": op["original_path"],
            "new_path": op["new_path"],
            "status": "pending",
            "can_rollback": True,
            "rollback_path": None,
            "metadata": {
                "file_size": op["file_size"],
                "original_filename": op["original_filename"],
                "new_filename": op["new_filename"]
            }
        }
        
        checkpoint_file = checkpoints_dir / f"{op['checkpoint_id']}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="SA-18 Checkpoint Sentinel Background Job")
    parser.add_argument("--task-id", required=True, help="Task ID from task_manager")
    parser.add_argument("--limit", type=int, default=500, help="Number of operations to process")
    args = parser.parse_args()

    task_id = args.task_id
    limit = args.limit
    logger = setup_logging(task_id)

    logger.info(f"🚀 SA-18 Checkpoint Sentinel started (Task: {task_id})")
    logger.info(f"   Limit: {limit} operations")

    # Load rename preview
    logger.info("📁 Loading rename preview...")
    entries = load_rename_preview()
    
    if not entries:
        logger.warning("⚠️  No rename preview found - creating empty manifest")
        entries = []
    
    logger.info(f"   Loaded {len(entries)} entries")

    # Generate shadow manifest
    logger.info("📋 Generating shadow manifest...")
    update_heartbeat(task_id, 25, "RUNNING", "Generating shadow manifest")
    
    manifest = create_shadow_manifest(entries, limit)
    manifest["metadata"]["task_id"] = task_id

    # Save shadow manifest
    manifest_file = Path(__file__).parent.parent / "06_METADATA" / f"shadow_manifest_{task_id}.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"✅ Shadow manifest saved: {manifest_file}")

    # Create checkpoint files
    logger.info("📍 Creating checkpoint files...")
    update_heartbeat(task_id, 50, "RUNNING", "Creating checkpoint files")
    
    create_checkpoint_files(manifest, task_id)
    
    checkpoints_dir = Path(__file__).parent.parent / "06_METADATA" / "checkpoints"
    checkpoint_count = len(list(checkpoints_dir.glob("CP_*.json")))
    
    logger.info(f"✅ Created {checkpoint_count} checkpoint files")

    # Create checkpoint index
    logger.info("📇 Creating checkpoint index...")
    update_heartbeat(task_id, 75, "RUNNING", "Creating checkpoint index")
    
    index = {
        "task_id": task_id,
        "created": datetime.now().isoformat(),
        "total_checkpoints": checkpoint_count,
        "manifest_file": str(manifest_file),
        "checkpoints_directory": str(checkpoints_dir),
        "status": "ready",
        "rollback_enabled": True
    }
    
    index_file = checkpoints_dir / f"index_{task_id}.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)
    
    logger.info(f"✅ Checkpoint index saved: {index_file}")

    # Final heartbeat
    logger.info(f"✅ SA-18 Checkpoint Sentinel complete")
    logger.info(f"   Manifest: {manifest_file}")
    logger.info(f"   Checkpoints: {checkpoint_count}")
    logger.info(f"   Index: {index_file}")
    
    update_heartbeat(task_id, 100, "COMPLETED", f"Created {checkpoint_count} checkpoints")

    sys.exit(0)


if __name__ == "__main__":
    main()
