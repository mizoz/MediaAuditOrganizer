#!/usr/bin/env python3
"""
transfer_assets.py — Verified File Transfer with Checkpoint & Rollback System

Transfers files from source to destination with comprehensive verification:
- SHA256 hash before copy
- Copy maintaining directory structure
- SHA256 hash after copy
- Compare and log VERIFIED/FAILED status
- Retry failed transfers up to 3 times
- Skip existing files with matching hash
- Checkpoint system for resume capability
- Shadow manifest for rollback support

Writes transfer log CSV to logs/ directory and prints summary.

Usage:
    python transfer_assets.py /source/path /dest/path [--manifest /path/to/manifest.csv]
    python transfer_assets.py --resume  # Resume from last checkpoint
"""

import argparse
import csv
import hashlib
import json
import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable

# Import checkpoint system
from checkpoint_logger import (
    CheckpointLogger,
    load_checkpoint,
    can_resume,
    get_resume_info
)

# Import heartbeat system (optional)
try:
    from heartbeat_logger import heartbeat
    HEARTBEAT_AVAILABLE = True
except ImportError:
    HEARTBEAT_AVAILABLE = False

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "07_LOGS"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"transfer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def compute_sha256(filepath: Path, chunk_size: int = 8192) -> Optional[str]:
    """Compute SHA256 hash of a file."""
    try:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (PermissionError, OSError) as e:
        logger.error(f"Cannot compute hash for {filepath}: {e}")
        return None


def copy_file_with_verify(
    source: Path,
    dest: Path,
    expected_hash: Optional[str] = None,
    max_retries: int = 3
) -> Tuple[bool, str, Dict]:
    """
    Copy a file with hash verification before and after.
    
    Returns:
        Tuple of (success, status, metadata_dict)
    """
    metadata = {
        "source": str(source),
        "destination": str(dest),
        "size_bytes": 0,
        "hash_before": "",
        "hash_after": "",
        "status": "",
        "attempts": 0,
        "error": ""
    }
    
    # Check if source exists
    if not source.exists():
        metadata["status"] = "SKIPPED"
        metadata["error"] = "Source file does not exist"
        return False, "SKIPPED", metadata
    
    # Get source file size
    try:
        metadata["size_bytes"] = source.stat().st_size
    except OSError as e:
        metadata["status"] = "SKIPPED"
        metadata["error"] = f"Cannot stat source: {e}"
        return False, "SKIPPED", metadata
    
    # Check if destination already exists with matching hash
    if dest.exists():
        dest_hash = compute_sha256(dest)
        if expected_hash and dest_hash == expected_hash:
            metadata["status"] = "SKIPPED_EXISTING"
            metadata["hash_after"] = dest_hash
            metadata["error"] = "Destination exists with matching hash"
            logger.info(f"  ⏭️  Skip (exists): {source.name}")
            return True, "SKIPPED_EXISTING", metadata
        elif not expected_hash:
            # No expected hash, check if source matches dest
            source_hash = compute_sha256(source)
            if source_hash == dest_hash:
                metadata["status"] = "SKIPPED_EXISTING"
                metadata["hash_before"] = source_hash
                metadata["hash_after"] = dest_hash
                logger.info(f"  ⏭️  Skip (verified): {source.name}")
                return True, "SKIPPED_EXISTING", metadata
    
    # Compute hash before copy
    logger.debug(f"  Computing hash before copy: {source.name}")
    hash_before = compute_sha256(source)
    metadata["hash_before"] = hash_before
    
    if not hash_before:
        metadata["status"] = "FAILED"
        metadata["error"] = "Failed to compute source hash"
        return False, "FAILED", metadata
    
    # Check against expected hash if provided
    if expected_hash and hash_before != expected_hash:
        metadata["status"] = "FAILED"
        metadata["error"] = f"Source hash mismatch: expected {expected_hash}, got {hash_before}"
        logger.warning(f"  ❌ Hash mismatch: {source.name}")
        return False, "FAILED", metadata
    
    # Create destination directory
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        metadata["status"] = "FAILED"
        metadata["error"] = f"Cannot create destination directory: {e}"
        return False, "FAILED", metadata
    
    # Copy with retries
    for attempt in range(1, max_retries + 1):
        metadata["attempts"] = attempt
        
        try:
            logger.debug(f"  Copying (attempt {attempt}/{max_retries}): {source.name}")
            shutil.copy2(source, dest)  # copy2 preserves metadata
            
            # Compute hash after copy
            hash_after = compute_sha256(dest)
            metadata["hash_after"] = hash_after
            
            if not hash_after:
                raise Exception("Failed to compute destination hash")
            
            # Verify hash
            if hash_before == hash_after:
                metadata["status"] = "VERIFIED"
                logger.info(f"  ✅ Verified: {source.name}")
                return True, "VERIFIED", metadata
            else:
                logger.warning(f"  ⚠️  Hash mismatch after copy (attempt {attempt}): {source.name}")
                if attempt < max_retries:
                    # Remove failed copy and retry
                    dest.unlink()
                    time.sleep(1)  # Brief delay before retry
                else:
                    metadata["status"] = "FAILED"
                    metadata["error"] = f"Hash mismatch after {max_retries} attempts"
                    return False, "FAILED", metadata
                    
        except Exception as e:
            logger.warning(f"  ⚠️  Copy failed (attempt {attempt}): {source.name} - {e}")
            metadata["error"] = str(e)
            
            # Clean up partial copy
            if dest.exists():
                try:
                    dest.unlink()
                except:
                    pass
            
            if attempt < max_retries:
                time.sleep(2)  # Exponential backoff
            else:
                metadata["status"] = "FAILED"
                metadata["error"] = f"Copy failed after {max_retries} attempts: {e}"
                return False, "FAILED", metadata
    
    metadata["status"] = "FAILED"
    metadata["error"] = "Unknown failure"
    return False, "FAILED", metadata


def load_transfer_manifest(manifest_path: Path) -> List[Dict]:
    """Load operations from shadow manifest JSON."""
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("operations", [])


def save_operation_to_manifest(
    manifest_path: Path,
    op_id: str,
    hash_before: str,
    hash_after: str,
    status: str,
    error: str = ""
) -> None:
    """Update a single operation in the shadow manifest."""
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for op in data.get("operations", []):
        if op.get("operation_id") == op_id:
            op["hash_before"] = hash_before
            op["hash_after"] = hash_after
            op["status"] = status
            op["error"] = error
            op["timestamp"] = datetime.now().isoformat()
            if status == "completed":
                op["completed_at"] = datetime.now().isoformat()
            break
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def transfer_files_with_checkpoint(
    source: Path,
    dest: Path,
    manifest_path: Path,
    checkpoint_dir: Path,
    log_path: Path,
    resume: bool = False,
    task_id: Optional[str] = None,
    heartbeat_callback: Optional[Callable] = None
) -> Dict:
    """Transfer all files with checkpoint support.
    
    Args:
        task_id: Optional task ID for heartbeat tracking
        heartbeat_callback: Optional callback function(task_id, progress, message)
    """
    
    # Load operations from shadow manifest
    operations = load_transfer_manifest(manifest_path)
    
    if not operations:
        logger.error("No operations found in manifest")
        return {"error": "No operations in manifest"}
    
    # Initialize checkpoint logger
    checkpoint_logger = CheckpointLogger(
        checkpoint_dir,
        checkpoint_interval=50,
        checkpoint_time_interval=60
    )
    
    # Check for resume
    start_index = 0
    if resume and can_resume(checkpoint_dir):
        resume_info = get_resume_info(checkpoint_dir)
        if resume_info:
            start_index = resume_info["resume_from_index"]
            logger.info(f"🔄 Resuming from operation {start_index}")
            logger.info(f"   Last completed: {resume_info['last_completed_op']}")
            logger.info(f"   Success: {resume_info['success_count']}, Failed: {resume_info['fail_count']}")
            logger.info(f"   Remaining: {resume_info['remaining']}")
    
    checkpoint_logger.initialize(len(operations), manifest_path)
    
    stats = {
        "total": len(operations),
        "verified": 0,
        "skipped": 0,
        "failed": 0,
        "total_bytes": 0,
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "source": str(source),
        "destination": str(dest),
        "start_index": start_index,
        "resumed": resume and start_index > 0
    }
    
    log_records = []
    
    print(f"\n{'='*80}")
    print("FILE TRANSFER WITH CHECKPOINT")
    print(f"{'='*80}")
    print(f"Source: {source}")
    print(f"Destination: {dest}")
    print(f"Operations: {stats['total']}")
    if resume and start_index > 0:
        print(f"⚡ RESUMING from operation {start_index}")
    print(f"{'='*80}\n")
    
    # Write CSV header
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "operation_id", "source", "destination", "filename", "size_bytes",
            "hash_before", "hash_after", "status", "attempts", "error"
        ])
    
    for i, op in enumerate(operations):
        # Skip completed operations if resuming
        if i < start_index:
            logger.debug(f"Skipping already completed: {op.get('operation_id')}")
            continue
        
        op_id = op.get("operation_id", f"OP_UNKNOWN_{i}")
        original_path = Path(op.get("original_path", ""))
        new_path = Path(op.get("new_path", ""))
        
        # Calculate actual paths (adjust for source/dest if needed)
        # For rename operations, paths are already absolute
        source_path = original_path
        dest_path = new_path
        
        # Progress indicator
        progress = i + 1
        progress_pct = 100.0 * progress / stats["total"]
        
        if progress % 10 == 0 or progress == stats["total"]:
            print(f"  Progress: {progress}/{stats['total']} ({progress_pct:.1f}%)")
        
        # Send heartbeat every 10 files (or if task_id provided)
        if task_id and HEARTBEAT_AVAILABLE and (progress % 10 == 0 or progress == 1):
            try:
                heartbeat(task_id, progress_pct, f"Transferring {source_path.name}", {
                    "current_file": source_path.name,
                    "processed": progress,
                    "total": stats["total"]
                })
            except Exception as e:
                logger.debug(f"Heartbeat failed: {e}")
        
        logger.info(f"[{progress}/{stats['total']}] Transferring: {source_path.name}")
        
        # Update manifest: mark as in_progress
        save_operation_to_manifest(
            manifest_path, op_id, "", "", "in_progress"
        )
        
        try:
            # Transfer file
            success, status, metadata = copy_file_with_verify(
                source_path, dest_path, None
            )
            
            # Update stats
            if status == "VERIFIED":
                stats["verified"] += 1
                stats["total_bytes"] += metadata["size_bytes"]
                final_status = "completed"
            elif status in ("SKIPPED", "SKIPPED_EXISTING"):
                stats["skipped"] += 1
                final_status = "completed"  # Skipped is still "done"
            else:
                stats["failed"] += 1
                final_status = "failed"
            
            # Update manifest with results
            save_operation_to_manifest(
                manifest_path,
                op_id,
                metadata["hash_before"],
                metadata["hash_after"],
                final_status,
                metadata["error"]
            )
            
            # Record checkpoint
            checkpoint_saved = checkpoint_logger.record_operation(
                op_id, i, success, metadata["error"]
            )
            if checkpoint_saved:
                logger.info(f"  💾 Checkpoint saved: {checkpoint_saved.name}")
            
            # Log record
            log_record = {
                "timestamp": datetime.now().isoformat(),
                "operation_id": op_id,
                "source": metadata["source"],
                "destination": metadata["destination"],
                "filename": source_path.name,
                "size_bytes": metadata["size_bytes"],
                "hash_before": metadata["hash_before"],
                "hash_after": metadata["hash_after"],
                "status": metadata["status"],
                "attempts": metadata["attempts"],
                "error": metadata["error"]
            }
            log_records.append(log_record)
            
            # Append to log CSV
            with open(log_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    log_record["timestamp"],
                    log_record["operation_id"],
                    log_record["source"],
                    log_record["destination"],
                    log_record["filename"],
                    log_record["size_bytes"],
                    log_record["hash_before"],
                    log_record["hash_after"],
                    log_record["status"],
                    log_record["attempts"],
                    log_record["error"]
                ])
                
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Transfer interrupted by user")
            logger.info("Saving final checkpoint...")
            checkpoint_logger.finalize()
            logger.info(f"Checkpoint saved. Resume with: python transfer_assets.py --resume")
            stats["interrupted"] = True
            break
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            stats["failed"] += 1
            save_operation_to_manifest(
                manifest_path, op_id, "", "", "failed", str(e)
            )
            checkpoint_logger.record_operation(op_id, i, False, str(e))
            # Continue to next file
    
    stats["end_time"] = datetime.now().isoformat()
    stats["log_records"] = log_records
    
    # Final checkpoint
    if not stats.get("interrupted"):
        checkpoint_logger.finalize()
    
    return stats


def print_summary(stats: Dict) -> None:
    """Print transfer summary."""
    duration = datetime.fromisoformat(stats["end_time"]) - datetime.fromisoformat(stats["start_time"])
    
    print(f"\n{'='*80}")
    print("TRANSFER SUMMARY")
    print(f"{'='*80}")
    print(f"\n📦 Total Operations: {stats['total']}")
    print(f"✅ Verified: {stats['verified']} ({100*stats['verified']/max(stats['total'],1):.1f}%)")
    print(f"⏭️  Skipped: {stats['skipped']} ({100*stats['skipped']/max(stats['total'],1):.1f}%)")
    print(f"❌ Failed: {stats['failed']} ({100*stats['failed']/max(stats['total'],1):.1f}%)")
    print(f"\n💾 Total Data Transferred: {stats['total_bytes'] / (1024**3):.2f} GB")
    print(f"⏱️  Duration: {duration}")
    
    if stats.get("resumed"):
        print(f"\n🔄 Resumed from operation {stats.get('start_index', 0)}")
    
    if stats.get("interrupted"):
        print(f"\n⚠️  Transfer interrupted. Resume with: python transfer_assets.py --resume")
    elif stats["failed"] > 0:
        print(f"\n⚠️  {stats['failed']} files failed to transfer. Check logs for details.")
    else:
        print(f"\n✅ All files transferred successfully!")
    
    print(f"\n{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description="Transfer files with hash verification and checkpoint support"
    )
    parser.add_argument(
        "source",
        type=Path,
        nargs="?",
        help="Source directory path"
    )
    parser.add_argument(
        "destination",
        type=Path,
        nargs="?",
        help="Destination directory path"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).parent.parent / "06_METADATA/shadow_manifest_20260304.json",
        help="Shadow manifest JSON (default: 06_METADATA/shadow_manifest_20260304.json)"
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=Path(__file__).parent.parent / "07_LOGS/checkpoints",
        help="Checkpoint directory (default: 07_LOGS/checkpoints)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be transferred without actually copying"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--task-id",
        type=str,
        help="Task ID for heartbeat tracking (optional)"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate paths
    if not args.resume and (not args.source or not args.destination):
        parser.error("source and destination required unless --resume")
    
    if args.source and not args.source.exists():
        logger.error(f"Source path does not exist: {args.source}")
        sys.exit(1)
    
    # Create destination if needed
    if args.destination:
        try:
            args.destination.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Cannot create destination directory: {e}")
            sys.exit(1)
    
    # Check manifest
    if not args.manifest.exists():
        logger.error(f"Manifest not found: {args.manifest}")
        sys.exit(1)
    
    try:
        # Check for resume
        if args.resume:
            if not can_resume(args.checkpoint_dir):
                logger.error("No checkpoint found to resume from")
                sys.exit(1)
            
            resume_info = get_resume_info(args.checkpoint_dir)
            print(f"\n🔄 Found checkpoint:")
            print(f"   Last completed: {resume_info['last_completed_op']}")
            print(f"   Remaining operations: {resume_info['remaining']}")
            response = input("\nContinue? [y/N]: ")
            if response.lower() != 'y':
                print("Aborted.")
                sys.exit(0)
        
        if args.dry_run:
            operations = load_transfer_manifest(args.manifest)
            print(f"\n{'='*80}")
            print("DRY RUN - No files will be copied")
            print(f"{'='*80}")
            print(f"Operations that would be processed: {len(operations)}")
            for op in operations[:20]:
                print(f"  - {Path(op.get('original_path', '')).name}")
            if len(operations) > 20:
                print(f"  ... and {len(operations) - 20} more")
            sys.exit(0)
        
        # Transfer files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = LOG_DIR / f"transfer_{timestamp}.csv"
        
        stats = transfer_files_with_checkpoint(
            args.source or Path("/"),
            args.destination or Path("/"),
            args.manifest,
            args.checkpoint_dir,
            log_path,
            resume=args.resume,
            task_id=args.task_id
        )
        
        # Write summary JSON
        summary_path = LOG_DIR / f"transfer_{timestamp}.json"
        stats_to_save = {k: v for k, v in stats.items() if k != "log_records"}
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(stats_to_save, f, indent=2, default=str)
        
        # Print summary
        print_summary(stats)
        
        # Send final heartbeat
        if args.task_id and HEARTBEAT_AVAILABLE:
            try:
                status = "COMPLETED" if stats["failed"] == 0 else "COMPLETED_WITH_ERRORS"
                heartbeat(args.task_id, 100.0, f"Transfer complete: {stats['verified']} verified, {stats['failed']} failed", status=status)
            except Exception as e:
                logger.debug(f"Final heartbeat failed: {e}")
        
        logger.info(f"Transfer log: {log_path}")
        logger.info(f"Transfer summary: {summary_path}")
        
        # Exit with error code if any failures or interrupted
        if stats.get("interrupted") or stats["failed"] > 0:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Transfer failed: {e}")
        
        # Send failure heartbeat
        if args.task_id and HEARTBEAT_AVAILABLE:
            try:
                heartbeat(args.task_id, 0.0, f"Transfer failed: {e}", status="FAILED")
            except Exception as he:
                logger.debug(f"Failure heartbeat failed: {he}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
