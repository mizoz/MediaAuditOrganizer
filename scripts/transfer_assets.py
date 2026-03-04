#!/usr/bin/env python3
"""
transfer_assets.py — Verified File Transfer with Hash Validation

Transfers files from source to destination with comprehensive verification:
- SHA256 hash before copy
- Copy maintaining directory structure
- SHA256 hash after copy
- Compare and log VERIFIED/FAILED status
- Retry failed transfers up to 3 times
- Skip existing files with matching hash

Writes transfer log CSV to logs/ directory and prints summary.

Usage:
    python transfer_assets.py /source/path /dest/path [--manifest /path/to/manifest.csv]
"""

import argparse
import csv
import hashlib
import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
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


def get_files_to_transfer(
    source: Path,
    manifest_path: Optional[Path] = None
) -> List[Dict]:
    """Get list of files to transfer from manifest or by scanning source."""
    files = []
    
    if manifest_path and manifest_path.exists():
        # Load from manifest
        logger.info(f"Loading file list from manifest: {manifest_path}")
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                source_path = Path(row.get("path", ""))
                if source_path.is_absolute():
                    # Convert to relative path from source
                    try:
                        rel_path = source_path.relative_to(source)
                        source_path = source / rel_path
                    except ValueError:
                        pass
                
                if source_path.exists():
                    files.append({
                        "source": source_path,
                        "expected_hash": row.get("sha256", "")
                    })
    else:
        # Scan source directory
        logger.info(f"Scanning source directory: {source}")
        for filepath in source.rglob("*"):
            if filepath.is_file():
                files.append({
                    "source": filepath,
                    "expected_hash": None
                })
    
    return files


def transfer_files(
    source: Path,
    dest: Path,
    files: List[Dict],
    log_path: Path
) -> Dict:
    """Transfer all files and write log."""
    stats = {
        "total": len(files),
        "verified": 0,
        "skipped": 0,
        "failed": 0,
        "total_bytes": 0,
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "source": str(source),
        "destination": str(dest)
    }
    
    log_records = []
    
    print(f"\n{'='*80}")
    print("FILE TRANSFER STARTED")
    print(f"{'='*80}")
    print(f"Source: {source}")
    print(f"Destination: {dest}")
    print(f"Files to transfer: {stats['total']}")
    print(f"{'='*80}\n")
    
    # Write CSV header
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "source", "destination", "filename", "size_bytes",
            "hash_before", "hash_after", "status", "attempts", "error"
        ])
    
    for i, file_info in enumerate(files, 1):
        source_path = file_info["source"]
        expected_hash = file_info.get("expected_hash")
        
        # Calculate destination path
        try:
            rel_path = source_path.relative_to(source)
            dest_path = dest / rel_path
        except ValueError:
            rel_path = source_path.name
            dest_path = dest / source_path.name
        
        # Progress indicator
        if i % 10 == 0 or i == stats["total"]:
            print(f"  Progress: {i}/{stats['total']} ({100*i/stats['total']:.1f}%)")
        
        logger.info(f"[{i}/{stats['total']}] Transferring: {source_path.name}")
        
        # Transfer file
        success, status, metadata = copy_file_with_verify(
            source_path, dest_path, expected_hash
        )
        
        # Update stats
        if status == "VERIFIED":
            stats["verified"] += 1
            stats["total_bytes"] += metadata["size_bytes"]
        elif status in ("SKIPPED", "SKIPPED_EXISTING"):
            stats["skipped"] += 1
        else:
            stats["failed"] += 1
        
        # Log record
        log_record = {
            "timestamp": datetime.now().isoformat(),
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
    
    stats["end_time"] = datetime.now().isoformat()
    stats["log_records"] = log_records
    
    return stats


def print_summary(stats: Dict) -> None:
    """Print transfer summary."""
    duration = datetime.fromisoformat(stats["end_time"]) - datetime.fromisoformat(stats["start_time"])
    
    print(f"\n{'='*80}")
    print("TRANSFER SUMMARY")
    print(f"{'='*80}")
    print(f"\n📦 Total Files: {stats['total']}")
    print(f"✅ Verified: {stats['verified']} ({100*stats['verified']/max(stats['total'],1):.1f}%)")
    print(f"⏭️  Skipped: {stats['skipped']} ({100*stats['skipped']/max(stats['total'],1):.1f}%)")
    print(f"❌ Failed: {stats['failed']} ({100*stats['failed']/max(stats['total'],1):.1f}%)")
    print(f"\n💾 Total Data Transferred: {stats['total_bytes'] / (1024**3):.2f} GB")
    print(f"⏱️  Duration: {duration}")
    
    if stats["failed"] > 0:
        print(f"\n⚠️  {stats['failed']} files failed to transfer. Check logs for details.")
    else:
        print(f"\n✅ All files transferred successfully!")
    
    print(f"\n{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description="Transfer files with hash verification"
    )
    parser.add_argument(
        "source",
        type=Path,
        help="Source directory path"
    )
    parser.add_argument(
        "destination",
        type=Path,
        help="Destination directory path"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Optional CSV manifest with file paths and hashes"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "logs",
        help="Output directory for transfer logs (default: ./logs/)"
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
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate paths
    if not args.source.exists():
        logger.error(f"Source path does not exist: {args.source}")
        sys.exit(1)
    
    if not args.source.is_dir():
        logger.error(f"Source path is not a directory: {args.source}")
        sys.exit(1)
    
    # Create destination if needed
    try:
        args.destination.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Cannot create destination directory: {e}")
        sys.exit(1)
    
    try:
        # Get files to transfer
        files = get_files_to_transfer(args.source, args.manifest)
        
        if not files:
            logger.warning("No files to transfer")
            print("No files to transfer.")
            sys.exit(0)
        
        if args.dry_run:
            print(f"\n{'='*80}")
            print("DRY RUN - No files will be copied")
            print(f"{'='*80}")
            print(f"Files that would be transferred: {len(files)}")
            for f in files[:20]:
                print(f"  - {f['source'].name}")
            if len(files) > 20:
                print(f"  ... and {len(files) - 20} more")
            sys.exit(0)
        
        # Transfer files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = args.output_dir / f"transfer_{timestamp}.csv"
        
        stats = transfer_files(args.source, args.destination, files, log_path)
        
        # Write summary JSON
        summary_path = args.output_dir / f"transfer_{timestamp}.json"
        import json
        stats_to_save = {k: v for k, v in stats.items() if k != "log_records"}
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(stats_to_save, f, indent=2, default=str)
        
        # Print summary
        print_summary(stats)
        
        logger.info(f"Transfer log: {log_path}")
        logger.info(f"Transfer summary: {summary_path}")
        
        # Exit with error code if any failures
        if stats["failed"] > 0:
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Transfer interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Transfer failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
