#!/usr/bin/env python3
"""
backup_verify.py — Backup Verification and Integrity Check

Compares primary and backup locations to verify backup integrity:
- Builds SHA256 hash index of both locations
- Reports files missing from backup
- Reports extra files in backup (not in primary)
- Reports hash mismatches (potential corruption)
- Reports total storage at each location

Outputs verification report to reports/ directory.
Exits with code 1 if any mismatches found.

Usage:
    python backup_verify.py /primary/path /backup/path
"""

import argparse
import csv
import hashlib
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"backup_verify_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
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
        logger.warning(f"Cannot compute hash for {filepath}: {e}")
        return None


def build_hash_index(
    root_path: Path,
    progress_callback: Optional[callable] = None
) -> Tuple[Dict[str, str], Dict[str, int], int]:
    """
    Build hash index for all files in a directory.
    
    Returns:
        Tuple of (hash_to_path_dict, path_to_size_dict, total_size)
    """
    hash_index = {}  # sha256 -> relative_path
    size_index = {}  # relative_path -> size_bytes
    total_size = 0
    file_count = 0
    
    print(f"  Scanning: {root_path}")
    
    for filepath in root_path.rglob("*"):
        if filepath.is_file():
            file_count += 1
            
            if progress_callback and file_count % 100 == 0:
                progress_callback(file_count)
            
            try:
                rel_path = str(filepath.relative_to(root_path))
                size = filepath.stat().st_size
                total_size += size
                
                sha256 = compute_sha256(filepath)
                if sha256:
                    hash_index[sha256] = rel_path
                    size_index[rel_path] = size
            except (OSError, ValueError) as e:
                logger.warning(f"Error processing {filepath}: {e}")
    
    return hash_index, size_index, total_size


def verify_backup(
    primary_path: Path,
    backup_path: Path
) -> Dict:
    """
    Verify backup against primary location.
    
    Returns verification results dictionary.
    """
    results = {
        "primary_path": str(primary_path),
        "backup_path": str(backup_path),
        "verification_time": datetime.now().isoformat(),
        "primary_stats": {"file_count": 0, "total_size": 0},
        "backup_stats": {"file_count": 0, "total_size": 0},
        "missing_from_backup": [],  # Files in primary but not in backup
        "extra_in_backup": [],  # Files in backup but not in primary
        "hash_mismatches": [],  # Files with different hashes
        "verified_count": 0,
        "status": "PASS"
    }
    
    print(f"\n{'='*80}")
    print("BACKUP VERIFICATION")
    print(f"{'='*80}")
    print(f"Primary: {primary_path}")
    print(f"Backup:  {backup_path}")
    print(f"{'='*80}\n")
    
    # Build hash index for primary
    print("Step 1: Building primary hash index...")
    primary_hashes = {}  # rel_path -> sha256
    primary_sizes = {}
    primary_total = 0
    primary_count = 0
    
    for filepath in primary_path.rglob("*"):
        if filepath.is_file():
            primary_count += 1
            if primary_count % 500 == 0:
                print(f"  Primary: {primary_count} files...")
            
            try:
                rel_path = str(filepath.relative_to(primary_path))
                size = filepath.stat().st_size
                primary_total += size
                
                sha256 = compute_sha256(filepath)
                if sha256:
                    primary_hashes[rel_path] = sha256
                    primary_sizes[rel_path] = size
            except (OSError, ValueError) as e:
                logger.warning(f"Error processing primary file {filepath}: {e}")
    
    results["primary_stats"] = {
        "file_count": primary_count,
        "total_size": primary_total,
        "total_size_gb": primary_total / (1024**3)
    }
    print(f"  Primary: {primary_count} files, {primary_total / (1024**3):.2f} GB\n")
    
    # Build hash index for backup
    print("Step 2: Building backup hash index...")
    backup_hashes = {}  # rel_path -> sha256
    backup_sizes = {}
    backup_total = 0
    backup_count = 0
    
    for filepath in backup_path.rglob("*"):
        if filepath.is_file():
            backup_count += 1
            if backup_count % 500 == 0:
                print(f"  Backup: {backup_count} files...")
            
            try:
                rel_path = str(filepath.relative_to(backup_path))
                size = filepath.stat().st_size
                backup_total += size
                
                sha256 = compute_sha256(filepath)
                if sha256:
                    backup_hashes[rel_path] = sha256
                    backup_sizes[rel_path] = size
            except (OSError, ValueError) as e:
                logger.warning(f"Error processing backup file {filepath}: {e}")
    
    results["backup_stats"] = {
        "file_count": backup_count,
        "total_size": backup_total,
        "total_size_gb": backup_total / (1024**3)
    }
    print(f"  Backup: {backup_count} files, {backup_total / (1024**3):.2f} GB\n")
    
    # Compare
    print("Step 3: Comparing primary vs backup...")
    
    primary_paths = set(primary_hashes.keys())
    backup_paths = set(backup_hashes.keys())
    
    # Missing from backup
    missing = primary_paths - backup_paths
    results["missing_from_backup"] = sorted(list(missing))
    
    # Extra in backup
    extra = backup_paths - primary_paths
    results["extra_in_backup"] = sorted(list(extra))
    
    # Hash mismatches (files in both but different hashes)
    common = primary_paths & backup_paths
    mismatches = []
    verified = 0
    
    for i, rel_path in enumerate(sorted(common), 1):
        if i % 1000 == 0:
            print(f"  Verifying: {i}/{len(common)} files...")
        
        if primary_hashes[rel_path] != backup_hashes[rel_path]:
            mismatches.append({
                "path": rel_path,
                "primary_hash": primary_hashes[rel_path],
                "backup_hash": backup_hashes[rel_path],
                "primary_size": primary_sizes.get(rel_path, 0),
                "backup_size": backup_sizes.get(rel_path, 0)
            })
        else:
            verified += 1
    
    results["hash_mismatches"] = mismatches
    results["verified_count"] = verified
    
    # Determine overall status
    if missing or extra or mismatches:
        results["status"] = "FAIL"
    else:
        results["status"] = "PASS"
    
    print(f"\n  Comparison complete.\n")
    
    return results


def write_report(results: Dict, output_dir: Path) -> Path:
    """Write verification report to file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write JSON report
    json_path = output_dir / f"backup_verify_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"JSON report: {json_path}")
    
    # Write CSV for mismatches
    if results["hash_mismatches"]:
        csv_path = output_dir / f"backup_mismatches_{timestamp}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["path", "primary_hash", "backup_hash", "primary_size", "backup_size"])
            for m in results["hash_mismatches"]:
                writer.writerow([
                    m["path"], m["primary_hash"], m["backup_hash"],
                    m["primary_size"], m["backup_size"]
                ])
        logger.info(f"Mismatches CSV: {csv_path}")
    
    # Write missing files list
    if results["missing_from_backup"]:
        missing_path = output_dir / f"backup_missing_{timestamp}.txt"
        with open(missing_path, "w", encoding="utf-8") as f:
            for path in results["missing_from_backup"]:
                f.write(path + "\n")
        logger.info(f"Missing files list: {missing_path}")
    
    return json_path


def print_summary(results: Dict) -> None:
    """Print verification summary."""
    status_icon = "✅" if results["status"] == "PASS" else "❌"
    
    print(f"\n{'='*80}")
    print(f"{status_icon} BACKUP VERIFICATION SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n📊 Primary Location:")
    print(f"   Path: {results['primary_path']}")
    print(f"   Files: {results['primary_stats']['file_count']:,}")
    print(f"   Size: {results['primary_stats'].get('total_size_gb', 0):.2f} GB")
    
    print(f"\n📊 Backup Location:")
    print(f"   Path: {results['backup_path']}")
    print(f"   Files: {results['backup_stats']['file_count']:,}")
    print(f"   Size: {results['backup_stats'].get('total_size_gb', 0):.2f} GB")
    
    print(f"\n📈 Verification Results:")
    print(f"   ✅ Verified: {results['verified_count']:,} files")
    
    if results["missing_from_backup"]:
        missing_count = len(results["missing_from_backup"])
        missing_size = sum(
            results['primary_stats'].get('total_size', 0) / results['primary_stats']['file_count']
            for _ in range(missing_count)
        ) if results['primary_stats']['file_count'] > 0 else 0
        print(f"   ⚠️  Missing from Backup: {missing_count:,} files (~{missing_size / (1024**3):.2f} GB)")
    
    if results["extra_in_backup"]:
        print(f"   ℹ️  Extra in Backup: {len(results['extra_in_backup']):,} files")
    
    if results["hash_mismatches"]:
        print(f"   ❌ Hash Mismatches: {len(results['hash_mismatches']):,} files (CORRUPTION DETECTED)")
    
    print(f"\n{'='*80}")
    print(f"OVERALL STATUS: {results['status']}")
    print(f"{'='*80}\n")
    
    if results["status"] == "FAIL":
        print("⚠️  Backup verification FAILED. Review issues above.")
        print("   - Missing files should be re-backed up")
        print("   - Hash mismatches indicate potential corruption")
        print("   - Extra files may be from previous backups or deletions\n")
    else:
        print("✅ Backup verification PASSED. All files verified.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Verify backup integrity against primary location"
    )
    parser.add_argument(
        "primary",
        type=Path,
        help="Primary (source) directory path"
    )
    parser.add_argument(
        "backup",
        type=Path,
        help="Backup directory path"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "reports",
        help="Output directory for reports (default: ./reports/)"
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
    if not args.primary.exists():
        logger.error(f"Primary path does not exist: {args.primary}")
        sys.exit(1)
    
    if not args.primary.is_dir():
        logger.error(f"Primary path is not a directory: {args.primary}")
        sys.exit(1)
    
    if not args.backup.exists():
        logger.error(f"Backup path does not exist: {args.backup}")
        sys.exit(1)
    
    if not args.backup.is_dir():
        logger.error(f"Backup path is not a directory: {args.backup}")
        sys.exit(1)
    
    try:
        # Run verification
        results = verify_backup(args.primary, args.backup)
        
        # Write report
        report_path = write_report(results, args.output_dir)
        print(f"📄 Full report: {report_path}")
        
        # Print summary
        print_summary(results)
        
        logger.info(f"Verification completed with status: {results['status']}")
        
        # Exit with code 1 if verification failed
        if results["status"] == "FAIL":
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Verification interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
