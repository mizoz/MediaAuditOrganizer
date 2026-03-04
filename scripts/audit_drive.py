#!/usr/bin/env python3
"""
audit_drive.py — Drive Audit and Metadata Extraction

Scans a drive and captures comprehensive file metadata including:
- Path, filename, extension, size, created, modified timestamps
- MD5 and SHA256 hashes
- MIME type detection
- EXIF data for images (date taken, camera, GPS)
- Video metadata (duration, codec, resolution, fps)

Outputs timestamped CSV and JSON files to reports/ directory.
Handles permission errors gracefully and prints progress summaries.

Usage:
    python audit_drive.py /path/to/drive [--output-dir /path/to/output]
"""

import argparse
import csv
import hashlib
import json
import logging
import mimetypes
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def compute_hashes(filepath: Path) -> Dict[str, str]:
    """Compute MD5 and SHA256 hashes for a file."""
    hashes = {"md5": "", "sha256": ""}
    try:
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)
        
        hashes["md5"] = md5_hash.hexdigest()
        hashes["sha256"] = sha256_hash.hexdigest()
    except (PermissionError, OSError) as e:
        logger.warning(f"Cannot compute hash for {filepath}: {e}")
    
    return hashes


def get_mime_type(filepath: Path) -> str:
    """Get MIME type for a file."""
    mime_type, _ = mimetypes.guess_type(str(filepath))
    return mime_type or "application/octet-stream"


def extract_exif_data(filepath: Path) -> Dict[str, Any]:
    """Extract EXIF data using ExifTool."""
    exif_data = {
        "date_taken": None,
        "camera_make": None,
        "camera_model": None,
        "lens_model": None,
        "iso": None,
        "shutter_speed": None,
        "aperture": None,
        "focal_length": None,
        "gps_latitude": None,
        "gps_longitude": None
    }
    
    try:
        result = subprocess.run(
            [
                "exiftool", "-json",
                "-DateTimeOriginal", "-Make", "-Model", "-LensModel",
                "-ISO", "-ShutterSpeedValue", "-ApertureValue", "-FocalLength",
                "-GPSLatitude", "-GPSLongitude",
                "-fast2",  # Faster extraction
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
                    "shutter_speed": data[0].get("ShutterSpeedValue"),
                    "aperture": data[0].get("ApertureValue"),
                    "focal_length": data[0].get("FocalLength"),
                    "gps_latitude": data[0].get("GPSLatitude"),
                    "gps_longitude": data[0].get("GPSLongitude")
                })
    except FileNotFoundError:
        logger.warning("ExifTool not found. Install with: brew install exiftool")
    except subprocess.TimeoutExpired:
        logger.warning(f"ExifTool timeout for {filepath}")
    except Exception as e:
        logger.debug(f"EXIF extraction failed for {filepath}: {e}")
    
    return exif_data


def extract_video_metadata(filepath: Path) -> Dict[str, Any]:
    """Extract video metadata using FFprobe."""
    video_data = {
        "duration": None,
        "codec": None,
        "width": None,
        "height": None,
        "fps": None,
        "bitrate": None,
        "creation_time": None
    }
    
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                str(filepath)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            
            # Format-level metadata
            fmt = data.get("format", {})
            video_data["duration"] = fmt.get("duration")
            video_data["bitrate"] = fmt.get("bit_rate")
            video_data["creation_time"] = fmt.get("tags", {}).get("creation_time")
            
            # Stream-level metadata (video stream)
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_data["codec"] = stream.get("codec_name")
                    video_data["width"] = stream.get("width")
                    video_data["height"] = stream.get("height")
                    fps = stream.get("r_frame_rate", "")
                    if fps and "/" in fps:
                        num, den = fps.split("/")
                        video_data["fps"] = round(int(num) / int(den), 2) if int(den) != 0 else None
                    break
    except FileNotFoundError:
        logger.warning("FFprobe not found. Install with: brew install ffmpeg")
    except subprocess.TimeoutExpired:
        logger.warning(f"FFprobe timeout for {filepath}")
    except Exception as e:
        logger.debug(f"Video metadata extraction failed for {filepath}: {e}")
    
    return video_data


def scan_drive(drive_path: Path, output_dir: Path) -> Dict[str, Any]:
    """Scan drive and collect all file metadata."""
    stats = {
        "total_files": 0,
        "total_size": 0,
        "files_by_type": {},
        "errors": [],
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "drive_path": str(drive_path)
    }
    
    file_records = []
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".heic", ".cr2", ".cr3", ".arw", ".nef", ".dng", ".raf"}
    video_extensions = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".wmv"}
    
    print(f"\n{'='*80}")
    print(f"DRIVE AUDIT STARTED")
    print(f"{'='*80}")
    print(f"Drive: {drive_path}")
    print(f"Output: {output_dir}")
    print(f"{'='*80}\n")
    
    # Walk the drive
    for root, dirs, files in os.walk(drive_path):
        for filename in files:
            filepath = Path(root) / filename
            stats["total_files"] += 1
            
            # Progress indicator
            if stats["total_files"] % 100 == 0:
                print(f"  Processed {stats['total_files']} files...")
            
            try:
                # Basic file info
                stat_info = filepath.stat()
                file_size = stat_info.st_size
                created = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
                modified = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                
                stats["total_size"] += file_size
                
                # File type categorization
                ext = filepath.suffix.lower()
                if ext in image_extensions:
                    file_type = "IMAGE"
                elif ext in video_extensions:
                    file_type = "VIDEO"
                else:
                    file_type = "OTHER"
                
                stats["files_by_type"][file_type] = stats["files_by_type"].get(file_type, 0) + 1
                
                # Compute hashes
                hashes = compute_hashes(filepath)
                
                # Get MIME type
                mime_type = get_mime_type(filepath)
                
                # Extract metadata based on file type
                exif_data = {}
                video_data = {}
                
                if file_type == "IMAGE":
                    exif_data = extract_exif_data(filepath)
                elif file_type == "VIDEO":
                    video_data = extract_video_metadata(filepath)
                
                # Build record
                record = {
                    "path": str(filepath),
                    "filename": filename,
                    "extension": ext,
                    "size_bytes": file_size,
                    "created": created,
                    "modified": modified,
                    "md5": hashes["md5"],
                    "sha256": hashes["sha256"],
                    "mime_type": mime_type,
                    "file_type": file_type,
                    **exif_data,
                    **video_data
                }
                
                file_records.append(record)
                
            except PermissionError as e:
                error_msg = f"Permission denied: {filepath}"
                logger.warning(error_msg)
                stats["errors"].append({"path": str(filepath), "error": str(e)})
            except OSError as e:
                error_msg = f"OS error: {filepath} - {e}"
                logger.warning(error_msg)
                stats["errors"].append({"path": str(filepath), "error": str(e)})
            except Exception as e:
                error_msg = f"Unexpected error: {filepath} - {e}"
                logger.error(error_msg)
                stats["errors"].append({"path": str(filepath), "error": str(e)})
    
    stats["end_time"] = datetime.now().isoformat()
    stats["file_records"] = file_records
    
    return stats


def write_outputs(stats: Dict[str, Any], output_dir: Path) -> None:
    """Write CSV and JSON output files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write CSV
    csv_path = output_dir / f"audit_{timestamp}.csv"
    file_records = stats.pop("file_records", [])
    
    if file_records:
        fieldnames = list(file_records[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(file_records)
        logger.info(f"CSV written: {csv_path}")
    
    # Write JSON
    json_path = output_dir / f"audit_{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, default=str)
    logger.info(f"JSON written: {json_path}")
    
    # Restore file_records for summary
    stats["file_records"] = file_records


def print_summary(stats: Dict[str, Any]) -> None:
    """Print audit summary to console."""
    print(f"\n{'='*80}")
    print("AUDIT SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n📁 Total Files: {stats['total_files']:,}")
    print(f"💾 Total Size: {stats['total_size'] / (1024**3):.2f} GB")
    
    print(f"\n📊 Files by Type:")
    for file_type, count in sorted(stats["files_by_type"].items()):
        print(f"   {file_type}: {count:,}")
    
    duration = datetime.fromisoformat(stats["end_time"]) - datetime.fromisoformat(stats["start_time"])
    print(f"\n⏱️  Duration: {duration}")
    
    if stats["errors"]:
        print(f"\n⚠️  Errors: {len(stats['errors'])}")
        for err in stats["errors"][:5]:  # Show first 5 errors
            print(f"   - {err['path']}: {err['error']}")
        if len(stats["errors"]) > 5:
            print(f"   ... and {len(stats['errors']) - 5} more")
    else:
        print(f"\n✅ No errors encountered")
    
    print(f"\n{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description="Audit a drive and extract comprehensive file metadata"
    )
    parser.add_argument(
        "drive_path",
        type=Path,
        help="Path to the drive/directory to audit"
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
    
    # Validate drive path
    if not args.drive_path.exists():
        logger.error(f"Drive path does not exist: {args.drive_path}")
        sys.exit(1)
    
    if not args.drive_path.is_dir():
        logger.error(f"Drive path is not a directory: {args.drive_path}")
        sys.exit(1)
    
    try:
        # Run audit
        stats = scan_drive(args.drive_path, args.output_dir)
        
        # Write outputs
        write_outputs(stats, args.output_dir)
        
        # Print summary
        print_summary(stats)
        
        logger.info("Audit completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Audit interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
