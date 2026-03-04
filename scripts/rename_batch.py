#!/usr/bin/env python3
"""
rename_batch.py — Batch File Renaming with EXIF Metadata

Renames files based on EXIF metadata using customizable patterns.
Supports tokens for date, camera, sequence, and original name.
Handles RAW+JPG pairs as units.

Features:
- Preview mode (show without executing)
- Execute mode (perform renames)
- Conflict detection and refusal
- RAW+JPG pair handling
- Comprehensive logging

Usage:
    python rename_batch.py /path/to/folder --pattern "{YYYY}{MM}{DD}_{camera_model}_{sequence}"
    python rename_batch.py /path/to/folder --pattern "{YYYY}{MM}{DD}_{original_name}" --preview
"""

import argparse
import csv
import json
import logging
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"rename_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# Supported tokens
TOKENS = {
    "{YYYY}": "4-digit year",
    "{MM}": "2-digit month",
    "{DD}": "2-digit day",
    "{HH}": "2-digit hour",
    "{mm}": "2-digit minute",
    "{ss}": "2-digit second",
    "{camera_make}": "Camera manufacturer",
    "{camera_model}": "Camera model",
    "{lens_model}": "Lens model",
    "{sequence}": "Sequential number (3-digit)",
    "{original_name}": "Original filename without extension",
    "{original_ext}": "Original extension",
    "{iso}": "ISO value",
    "{focal_length}": "Focal length"
}


def extract_exif_data(filepath: Path) -> Dict[str, Any]:
    """Extract EXIF data using ExifTool."""
    exif_data = {
        "date_taken": None,
        "camera_make": None,
        "camera_model": None,
        "lens_model": None,
        "iso": None,
        "focal_length": None
    }
    
    try:
        result = subprocess.run(
            [
                "exiftool", "-json",
                "-DateTimeOriginal", "-Make", "-Model", "-LensModel",
                "-ISO", "-FocalLength",
                "-fast2",
                str(filepath)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            if data:
                exif_data.update({
                    "date_taken": data[0].get("DateTimeOriginal"),
                    "camera_make": data[0].get("Make"),
                    "camera_model": data[0].get("Model"),
                    "lens_model": data[0].get("LensModel"),
                    "iso": data[0].get("ISO"),
                    "focal_length": data[0].get("FocalLength")
                })
    except FileNotFoundError:
        logger.error("ExifTool not found. Install with: brew install exiftool")
    except subprocess.TimeoutExpired:
        logger.warning(f"ExifTool timeout for {filepath}")
    except Exception as e:
        logger.debug(f"EXIF extraction failed for {filepath}: {e}")
    
    return exif_data


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse EXIF date string to datetime object."""
    if not date_str:
        return None
    
    try:
        # EXIF format: "YYYY:MM:DD HH:MM:SS"
        date_str = date_str.replace(":", "-", 2)  # Replace first two colons
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        try:
            # Alternative format: "YYYY-MM-DD HH:MM:SS"
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return None


def generate_new_name(
    filepath: Path,
    pattern: str,
    exif_data: Dict[str, Any],
    sequence: int
) -> Optional[str]:
    """Generate new filename based on pattern and EXIF data."""
    new_name = pattern
    
    # Parse date
    date_obj = parse_date(exif_data.get("date_taken"))
    
    # Replace tokens
    if date_obj:
        new_name = new_name.replace("{YYYY}", date_obj.strftime("%Y"))
        new_name = new_name.replace("{MM}", date_obj.strftime("%m"))
        new_name = new_name.replace("{DD}", date_obj.strftime("%d"))
        new_name = new_name.replace("{HH}", date_obj.strftime("%H"))
        new_name = new_name.replace("{mm}", date_obj.strftime("%M"))
        new_name = new_name.replace("{ss}", date_obj.strftime("%S"))
    else:
        # Use file modification date as fallback
        try:
            mod_date = datetime.fromtimestamp(filepath.stat().st_mtime)
            new_name = new_name.replace("{YYYY}", mod_date.strftime("%Y"))
            new_name = new_name.replace("{MM}", mod_date.strftime("%m"))
            new_name = new_name.replace("{DD}", mod_date.strftime("%d"))
            new_name = new_name.replace("{HH}", mod_date.strftime("%H"))
            new_name = new_name.replace("{mm}", mod_date.strftime("%M"))
            new_name = new_name.replace("{ss}", mod_date.strftime("%S"))
        except OSError:
            new_name = new_name.replace("{YYYY}", "NODATE")
            new_name = new_name.replace("{MM}", "01")
            new_name = new_name.replace("{DD}", "01")
            new_name = new_name.replace("{HH}", "00")
            new_name = new_name.replace("{mm}", "00")
            new_name = new_name.replace("{ss}", "00")
    
    # Camera tokens
    camera_make = exif_data.get("camera_make") or "Unknown"
    camera_model = exif_data.get("camera_model") or "Unknown"
    new_name = new_name.replace("{camera_make}", camera_make.replace(" ", "_"))
    new_name = new_name.replace("{camera_model}", camera_model.replace(" ", "_"))
    new_name = new_name.replace("{lens_model}", (exif_data.get("lens_model") or "Unknown").replace(" ", "_"))
    
    # Sequence
    new_name = new_name.replace("{sequence}", f"{sequence:03d}")
    
    # Original name
    new_name = new_name.replace("{original_name}", filepath.stem)
    new_name = new_name.replace("{original_ext}", filepath.suffix)
    
    # Other tokens
    new_name = new_name.replace("{iso}", str(exif_data.get("iso") or "0"))
    new_name = new_name.replace("{focal_length}", str(exif_data.get("focal_length") or "0"))
    
    # Clean up any remaining tokens
    new_name = re.sub(r'\{[^}]+\}', '', new_name)
    
    # Sanitize filename
    new_name = re.sub(r'[<>:"/\\|?*]', '_', new_name)
    new_name = re.sub(r'\s+', '_', new_name)
    new_name = new_name.strip("_. ")
    
    # Add extension
    if not new_name.lower().endswith(filepath.suffix.lower()):
        new_name += filepath.suffix
    
    return new_name if new_name else None


def find_raw_jpg_pairs(files: List[Path]) -> Dict[str, List[Path]]:
    """Find RAW+JPG pairs that should be renamed together."""
    raw_extensions = {".cr2", ".cr3", ".arw", ".nef", ".dng", ".raf", ".orf"}
    pairs = defaultdict(list)
    
    for filepath in files:
        if filepath.suffix.lower() in raw_extensions or filepath.suffix.lower() == ".jpg":
            # Group by base name and directory
            key = f"{filepath.parent}/{filepath.stem}"
            pairs[key].append(filepath)
    
    # Filter to only actual pairs
    return {k: v for k, v in pairs.items() if len(v) > 1}


def check_conflicts(renames: List[Dict], target_dir: Path) -> List[str]:
    """Check for naming conflicts."""
    conflicts = []
    seen_names = set()
    
    for rename in renames:
        new_name = rename["new_name"]
        new_path = target_dir / new_name
        
        # Check if name is used multiple times in rename list
        if new_name in seen_names:
            conflicts.append(f"Duplicate name: {new_name}")
        seen_names.add(new_name)
        
        # Check if file already exists
        if new_path.exists() and new_path != rename["source"]:
            conflicts.append(f"File exists: {new_path}")
    
    return conflicts


def process_directory(
    folder_path: Path,
    pattern: str,
    preview: bool = True,
    recursive: bool = True
) -> Dict:
    """Process all files in directory and generate rename plan."""
    results = {
        "folder": str(folder_path),
        "pattern": pattern,
        "preview": preview,
        "total_files": 0,
        "files_to_rename": 0,
        "skipped": 0,
        "conflicts": [],
        "renames": [],
        "pairs": [],
        "errors": []
    }
    
    # Find all image files
    image_extensions = {".jpg", ".jpeg", ".png", ".heic", ".cr2", ".cr3", ".arw", ".nef", ".dng", ".raf", ".tif", ".tiff"}
    files = []
    
    if recursive:
        for ext in image_extensions:
            files.extend(folder_path.rglob(f"*{ext}"))
            files.extend(folder_path.rglob(f"*{ext.upper()}"))
    else:
        for ext in image_extensions:
            files.extend(folder_path.glob(f"*{ext}"))
            files.extend(folder_path.glob(f"*{ext.upper()}"))
    
    results["total_files"] = len(files)
    print(f"Found {len(files)} image files\n")
    
    # Find RAW+JPG pairs
    pairs = find_raw_jpg_pairs(files)
    results["pairs"] = [{"base": k, "files": [str(f) for f in v]} for k, v in pairs.items()]
    print(f"Found {len(pairs)} RAW+JPG pairs\n")
    
    # Generate rename plan
    sequence = 1
    processed = set()
    
    for filepath in sorted(files):
        if filepath in processed:
            continue
        
        # Check if this file is part of a pair
        pair_key = f"{filepath.parent}/{filepath.stem}"
        pair_files = pairs.get(pair_key, [filepath])
        
        # Get EXIF data for first file in pair
        exif_data = extract_exif_data(filepath)
        
        # Generate new base name
        new_base = generate_new_name(filepath, pattern, exif_data, sequence)
        
        if not new_base:
            results["errors"].append({"file": str(filepath), "error": "Failed to generate name"})
            results["skipped"] += 1
            continue
        
        # Process all files in pair
        for i, pair_file in enumerate(pair_files):
            if pair_file in processed:
                continue
            
            processed.add(pair_file)
            
            # Generate full new name with correct extension
            new_name = Path(new_base).stem + pair_file.suffix
            
            if new_name != pair_file.name:
                results["renames"].append({
                    "source": str(pair_file),
                    "destination": str(pair_file.parent / new_name),
                    "new_name": new_name,
                    "pair_base": pair_key if len(pair_files) > 1 else None
                })
                results["files_to_rename"] += 1
            else:
                results["skipped"] += 1
        
        sequence += 1
    
    # Check for conflicts
    results["conflicts"] = check_conflicts(results["renames"], folder_path)
    
    return results


def execute_renames(renames: List[Dict], log_path: Path) -> Dict:
    """Execute the rename operations."""
    stats = {
        "total": len(renames),
        "success": 0,
        "failed": 0,
        "errors": []
    }
    
    # Write log header
    with open(log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "source", "destination", "status", "error"])
    
    for i, rename in enumerate(renames, 1):
        source = Path(rename["source"])
        dest = Path(rename["destination"])
        
        print(f"[{i}/{len(renames)}] Renaming: {source.name} → {dest.name}")
        
        try:
            if source.exists():
                source.rename(dest)
                stats["success"] += 1
                status = "SUCCESS"
                error = ""
                print(f"  ✅ Success")
            else:
                stats["failed"] += 1
                status = "FAILED"
                error = "Source file not found"
                print(f"  ❌ Source not found")
        except Exception as e:
            stats["failed"] += 1
            status = "FAILED"
            error = str(e)
            print(f"  ❌ Error: {e}")
        
        # Log
        with open(log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                rename["source"],
                rename["destination"],
                status,
                error
            ])
    
    return stats


def print_preview(results: Dict) -> None:
    """Print preview of proposed renames."""
    print(f"\n{'='*80}")
    print("RENAME PREVIEW")
    print(f"{'='*80}")
    print(f"Folder: {results['folder']}")
    print(f"Pattern: {results['pattern']}")
    print(f"{'='*80}\n")
    
    print(f"📊 Summary:")
    print(f"   Total files found: {results['total_files']}")
    print(f"   Files to rename: {results['files_to_rename']}")
    print(f"   Skipped (no change): {results['skipped']}")
    print(f"   RAW+JPG pairs: {len(results['pairs'])}")
    
    if results["conflicts"]:
        print(f"\n⚠️  CONFLICTS DETECTED ({len(results['conflicts'])}):")
        for conflict in results["conflicts"][:10]:
            print(f"   - {conflict}")
        if len(results["conflicts"]) > 10:
            print(f"   ... and {len(results['conflicts']) - 10} more")
        print(f"\n❌ Cannot proceed with conflicts. Resolve and retry.")
        return
    
    print(f"\n📝 Proposed Renames (first 20):")
    for i, rename in enumerate(results["renames"][:20], 1):
        source_name = Path(rename["source"]).name
        dest_name = Path(rename["destination"]).name
        pair_indicator = "📦 " if rename.get("pair_base") else ""
        print(f"   {i:2d}. {pair_indicator}{source_name}")
        print(f"       → {dest_name}")
    
    if len(results["renames"]) > 20:
        print(f"   ... and {len(results['renames']) - 20} more")
    
    print(f"\n{'='*80}")
    print("To execute renames, run with --execute flag")
    print(f"{'='*80}\n")


def print_summary(stats: Dict) -> None:
    """Print rename execution summary."""
    print(f"\n{'='*80}")
    print("RENAME SUMMARY")
    print(f"{'='*80}")
    print(f"Total: {stats['total']}")
    print(f"✅ Success: {stats['success']} ({100*stats['success']/max(stats['total'],1):.1f}%)")
    print(f"❌ Failed: {stats['failed']} ({100*stats['failed']/max(stats['total'],1):.1f}%)")
    
    if stats["errors"]:
        print(f"\n⚠️  Errors:")
        for err in stats["errors"][:10]:
            print(f"   - {err}")
    
    print(f"\n{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Batch rename files using EXIF metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available tokens:
{chr(10).join(f'  {k:20s} - {v}' for k, v in TOKENS.items())}

Examples:
  %(prog)s /photos --pattern "{{YYYY}}{{MM}}{{DD}}_{{camera_model}}_{{sequence}}"
  %(prog)s /photos --pattern "{{YYYY}}-{{MM}}-{{DD}}_{{original_name}}" --preview
  %(prog)s /photos --pattern "{{camera_make}}_{{YYYY}}{{MM}}{{DD}}_{{sequence}}" --execute
"""
    )
    parser.add_argument(
        "folder",
        type=Path,
        help="Folder containing files to rename"
    )
    parser.add_argument(
        "--pattern", "-p",
        type=str,
        required=True,
        help="Naming pattern with tokens (e.g., '{YYYY}{MM}{DD}_{camera_model}_{sequence}')"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        default=True,
        help="Preview mode (default) - show without executing"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute mode - perform the renames"
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't scan subdirectories"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "logs",
        help="Output directory for logs (default: ./logs/)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate folder
    if not args.folder.exists():
        logger.error(f"Folder does not exist: {args.folder}")
        sys.exit(1)
    
    if not args.folder.is_dir():
        logger.error(f"Not a directory: {args.folder}")
        sys.exit(1)
    
    # Execute mode overrides preview
    preview = not args.execute
    
    try:
        # Process directory
        results = process_directory(
            args.folder,
            args.pattern,
            preview=preview,
            recursive=not args.no_recursive
        )
        
        if not results["renames"]:
            print("No files need renaming.")
            sys.exit(0)
        
        if preview:
            # Show preview
            print_preview(results)
            
            # Check for conflicts
            if results["conflicts"]:
                sys.exit(1)
        else:
            # Check for conflicts before executing
            if results["conflicts"]:
                print("❌ Cannot execute: naming conflicts detected")
                for conflict in results["conflicts"][:5]:
                    print(f"   - {conflict}")
                sys.exit(1)
            
            # Confirm
            print(f"\n⚠️  About to rename {results['files_to_rename']} files.")
            confirm = input("Proceed? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("Cancelled.")
                sys.exit(0)
            
            # Execute
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = args.output_dir / f"rename_{timestamp}.csv"
            
            stats = execute_renames(results["renames"], log_path)
            
            # Save results JSON
            json_path = args.output_dir / f"rename_{timestamp}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({**results, "stats": stats}, f, indent=2, default=str)
            
            print_summary(stats)
            print(f"Log: {log_path}")
            
            if stats["failed"] > 0:
                sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Rename operation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Rename operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
