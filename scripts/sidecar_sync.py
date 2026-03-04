#!/usr/bin/env python3
"""
sidecar_sync.py — JSON Sidecar Generator for Media Files

Creates JSON sidecar files alongside media files to preserve original metadata
before rename/move operations. Each sidecar contains:
- Original filename and path
- New filename (planned)
- Unique ID (SHA256 hash)
- EXIF metadata (camera, lens, date, GPS, etc.)
- Transfer tracking information

Usage:
    python sidecar_sync.py --input-csv /path/to/rename_preview.csv --output-dir /path/to/output
    python sidecar_sync.py --file /path/to/media/file.ARW --new-filename "2022-08-10_10-03-43_A7M4_0003.arw"
"""

import argparse
import csv
import hashlib
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "07_LOGS"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"sidecar_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def compute_sha256(filepath: Path) -> Optional[str]:
    """Compute SHA256 hash of a file."""
    try:
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (PermissionError, OSError) as e:
        logger.error(f"Cannot compute hash for {filepath}: {e}")
        return None


def extract_metadata_exiftool(filepath: Path) -> Dict[str, Any]:
    """
    Extract metadata from media file using exiftool.
    
    Returns dict with camera, lens, date, GPS, and other EXIF data.
    """
    try:
        result = subprocess.run(
            ["exiftool", "-json", str(filepath)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.warning(f"exiftool failed for {filepath}: {result.stderr}")
            return {}
        
        metadata_list = json.loads(result.stdout)
        if not metadata_list:
            return {}
        
        raw = metadata_list[0]
        
        # Extract and normalize metadata
        metadata = {
            "camera_make": raw.get("Make", raw.get("CameraMake", None)),
            "camera_model": raw.get("Model", raw.get("CameraModel", None)),
            "lens_model": raw.get("LensModel", raw.get("Lens", None)),
            "date_taken": normalize_date(raw.get("DateTimeOriginal", raw.get("CreateDate", None))),
            "focal_length": format_focal_length(raw.get("FocalLength", None)),
            "iso": raw.get("ISO", None),
            "aperture": raw.get("FNumber", raw.get("ApertureValue", None)),
            "shutter_speed": format_shutter_speed(raw.get("ShutterSpeedValue", raw.get("ExposureTime", None))),
            "gps_latitude": extract_gps(raw.get("GPSLatitude", None), raw.get("GPSLatitudeRef", "N")),
            "gps_longitude": extract_gps(raw.get("GPSLongitude", None), raw.get("GPSLongitudeRef", "W")),
        }
        
        return metadata
        
    except subprocess.TimeoutExpired:
        logger.error(f"exiftool timeout for {filepath}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error for {filepath}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error extracting metadata from {filepath}: {e}")
        return {}


def normalize_date(date_str: Optional[str]) -> Optional[str]:
    """Normalize date string to ISO format."""
    if not date_str:
        return None
    
    # exiftool typically returns "YYYY:MM:DD HH:MM:SS"
    try:
        # Replace colons with dashes for date part
        if ":" in date_str:
            parts = date_str.split(" ")
            if len(parts) == 2:
                date_part = parts[0].replace(":", "-")
                time_part = parts[1]
                return f"{date_part}T{time_part}"
        return date_str
    except Exception:
        return date_str


def format_focal_length(value: Any) -> Optional[str]:
    """Format focal length with unit."""
    if value is None:
        return None
    try:
        # Handle "100.0 mm" or "100.0" formats
        val_str = str(value).replace(" mm", "").strip()
        return f"{val_str} mm"
    except Exception:
        return str(value)


def format_shutter_speed(value: Any) -> Optional[str]:
    """Format shutter speed value."""
    if value is None:
        return None
    try:
        # Handle fractions like "1/1000" or decimal values
        return str(value)
    except Exception:
        return str(value)


def extract_gps(value: Any, ref: str = "N") -> Optional[float]:
    """Extract GPS coordinate as decimal degrees."""
    if value is None:
        return None
    
    try:
        # Handle various GPS formats from exiftool
        if isinstance(value, (int, float)):
            return float(value)
        
        val_str = str(value)
        # Handle "51 deg 23' 12.34" N" format
        if "deg" in val_str:
            # Parse degrees, minutes, seconds
            parts = val_str.replace(",", "").split()
            if len(parts) >= 4:
                deg = float(parts[0])
                mins = float(parts[2])
                secs = float(parts[4]) if len(parts) > 4 else 0
                decimal = deg + mins/60 + secs/3600
                if ref in ["S", "W"]:
                    decimal = -decimal
                return round(decimal, 6)
        
        return float(val_str)
    except Exception:
        return None


def create_sidecar(file_path: str, new_filename: str, operation_id: str) -> Dict[str, Any]:
    """
    Create a JSON sidecar for a media file.
    
    Args:
        file_path: Path to the original media file
        new_filename: Planned new filename after rename
        operation_id: Unique operation identifier (e.g., "OP_20260304_000000_0001")
    
    Returns:
        Dict containing sidecar data, or None if failed
    """
    source_path = Path(file_path)
    
    if not source_path.exists():
        logger.error(f"Source file does not exist: {file_path}")
        return None
    
    # Compute unique ID (SHA256 hash)
    unique_id = compute_sha256(source_path)
    if not unique_id:
        logger.error(f"Failed to compute hash for {file_path}")
        return None
    
    # Extract metadata
    metadata = extract_metadata_exiftool(source_path)
    
    # Build sidecar structure
    sidecar = {
        "version": "1.0",
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "original_filename": source_path.name,
        "original_path": str(source_path.absolute()),
        "new_filename": new_filename,
        "unique_id": f"sha256:{unique_id}",
        "metadata": metadata,
        "transfer_info": {
            "operation_id": operation_id,
            "transferred_at": None,
            "verified_hash": None
        }
    }
    
    return sidecar


def write_sidecar(sidecar: Dict[str, Any], output_path: Path) -> bool:
    """Write sidecar JSON to file."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sidecar, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to write sidecar to {output_path}: {e}")
        return False


def validate_json(filepath: Path) -> bool:
    """Validate JSON syntax of a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        return False


def process_csv(
    input_csv: Path,
    output_dir: Path,
    operation_id: str,
    limit: int = 500,
    sidecar_output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Process a CSV file and create sidecars for each entry.
    
    Args:
        input_csv: Path to rename_preview CSV
        output_dir: Directory to write manifest
        operation_id: Operation identifier
        limit: Maximum number of files to process
        sidecar_output_dir: Directory to write sidecars (default: alongside originals if writable, else workspace)
    
    Returns:
        Summary dict with counts and status
    """
    results = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "failed_files": []
    }
    
    manifest_rows = []
    
    # Determine sidecar output location
    if sidecar_output_dir is None:
        # Try writing alongside original first, fall back to workspace
        sidecar_output_dir = Path(__file__).parent.parent / "05_SIDECARS"
        sidecar_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Writing sidecars to workspace: {sidecar_output_dir}")
    
    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for i, row in enumerate(reader):
            if i >= limit:
                break
            
            results["total"] += 1
            
            old_path = row.get("old_path", "")
            new_path = row.get("new_path", "")
            
            if not old_path:
                logger.warning(f"Row {i+1}: Missing old_path, skipping")
                results["skipped"] += 1
                continue
            
            source_file = Path(old_path)
            if not source_file.exists():
                logger.warning(f"Row {i+1}: File not found: {old_path}")
                results["skipped"] += 1
                manifest_rows.append({
                    "original_path": old_path,
                    "sidecar_path": "",
                    "unique_id": "",
                    "status": "FILE_NOT_FOUND",
                    "timestamp": datetime.now().isoformat()
                })
                continue
            
            # Extract new filename from new_path
            new_filename = Path(new_path).name if new_path else source_file.name
            
            # Create sidecar
            sidecar = create_sidecar(old_path, new_filename, operation_id)
            
            if not sidecar:
                results["failed"] += 1
                results["failed_files"].append(old_path)
                manifest_rows.append({
                    "original_path": old_path,
                    "sidecar_path": "",
                    "unique_id": "",
                    "status": "METADATA_EXTRACTION_FAILED",
                    "timestamp": datetime.now().isoformat()
                })
                continue
            
            # Write sidecar to output directory (preserve relative path structure)
            # Use original_path relative to /media/az/drive64gb as subdirectory
            try:
                rel_path = source_file.relative_to("/media/az/drive64gb")
                sidecar_subdir = sidecar_output_dir / rel_path.parent
                sidecar_subdir.mkdir(parents=True, exist_ok=True)
                sidecar_path = sidecar_subdir / (source_file.name + ".json")
            except ValueError:
                # Not under /media/az/drive64gb, just use filename
                sidecar_path = sidecar_output_dir / (source_file.name + ".json")
            
            if write_sidecar(sidecar, sidecar_path):
                results["success"] += 1
                
                # Validate the written JSON
                if not validate_json(sidecar_path):
                    logger.error(f"Validation failed for {sidecar_path}")
                    results["failed"] += 1
                    results["failed_files"].append(old_path)
                    continue
                
                manifest_rows.append({
                    "original_path": old_path,
                    "sidecar_path": str(sidecar_path),
                    "unique_id": sidecar["unique_id"],
                    "status": "SUCCESS",
                    "timestamp": datetime.now().isoformat()
                })
                
                if results["success"] % 50 == 0:
                    logger.info(f"Progress: {results['success']}/{results['total']} sidecars created")
            else:
                results["failed"] += 1
                results["failed_files"].append(old_path)
                manifest_rows.append({
                    "original_path": old_path,
                    "sidecar_path": "",
                    "unique_id": "",
                    "status": "WRITE_FAILED",
                    "timestamp": datetime.now().isoformat()
                })
    
    # Write manifest CSV
    manifest_path = output_dir / f"sidecar_manifest_{datetime.now().strftime('%Y%m%d')}.csv"
    with open(manifest_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["original_path", "sidecar_path", "unique_id", "status", "timestamp"])
        writer.writeheader()
        writer.writerows(manifest_rows)
    
    logger.info(f"Manifest written to {manifest_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Create JSON sidecars for media files")
    parser.add_argument("--input-csv", type=Path, help="Path to rename_preview CSV")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent.parent / "06_METADATA",
                       help="Output directory for manifest")
    parser.add_argument("--file", type=str, help="Single file to process")
    parser.add_argument("--new-filename", type=str, help="New filename for single file mode")
    parser.add_argument("--operation-id", type=str, default=f"OP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_0001",
                       help="Operation identifier")
    parser.add_argument("--limit", type=int, default=500, help="Max files to process (default: 500)")
    
    args = parser.parse_args()
    
    # Single file mode
    if args.file:
        if not args.new_filename:
            logger.error("--new-filename required for single file mode")
            sys.exit(1)
        
        sidecar = create_sidecar(args.file, args.new_filename, args.operation_id)
        if sidecar:
            source_path = Path(args.file)
            sidecar_path = source_path.with_suffix(source_path.suffix + ".json")
            if write_sidecar(sidecar, sidecar_path):
                print(f"Sidecar created: {sidecar_path}")
                print(json.dumps(sidecar, indent=2))
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            sys.exit(1)
    
    # CSV batch mode
    if args.input_csv:
        if not args.input_csv.exists():
            logger.error(f"Input CSV not found: {args.input_csv}")
            sys.exit(1)
        
        args.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Processing {args.input_csv} (limit: {args.limit})")
        results = process_csv(args.input_csv, args.output_dir, args.operation_id, args.limit)
        
        print(f"\n{'='*60}")
        print(f"SIDECAR GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"Total files processed: {results['total']}")
        print(f"Sidecars created:      {results['success']}")
        print(f"Failed:                {results['failed']}")
        print(f"Skipped:               {results['skipped']}")
        
        if results['failed_files']:
            print(f"\nFailed files ({len(results['failed_files'])}):")
            for f in results['failed_files'][:10]:
                print(f"  - {f}")
            if len(results['failed_files']) > 10:
                print(f"  ... and {len(results['failed_files']) - 10} more")
        
        print(f"\nManifest: {args.output_dir / f'sidecar_manifest_{datetime.now().strftime('%Y%m%d')}.csv'}")
        print(f"{'='*60}")
        
        sys.exit(0 if results['failed'] == 0 else 1)
    
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
