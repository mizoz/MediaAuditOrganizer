#!/usr/bin/env python3
"""
audit_drive.py — Hardware-Accelerated Drive Audit and Metadata Extraction

Scans a drive and captures comprehensive file metadata including:
- Path, filename, extension, size, created, modified timestamps
- MD5 and SHA256 hashes (parallel computation)
- MIME type detection
- EXIF data for images (date taken, camera, GPS)
- Video metadata (duration, codec, resolution, fps)
- Fast I-frame thumbnail extraction (500% speedup)

Hardware Acceleration Features:
- Parallel hashing via ProcessPoolExecutor (scales to CPU core count)
- GPU-accelerated video processing (NVENC/AMF/QSV/VAAPI)
- Fast I-frame thumbnail extraction
- Thermal monitoring with auto-pause (requires smartctl)

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
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

# Add script directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# Import hardware acceleration modules
try:
    from batch_processor import BatchProcessor, HashResult, calculate_optimal_workers
    from video_processor import VideoProcessor, ThumbnailResult
    from thermal_monitor import ThermalMonitor
    from hardware_detection import detect_all
    HARDWARE_ACCEL_AVAILABLE = True
except ImportError as e:
    HARDWARE_ACCEL_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"Hardware acceleration modules not available: {e}")

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


def compute_hashes_parallel(
    file_paths: List[Path],
    storage_type: str = "SSD",
    max_workers: Optional[int] = None
) -> Dict[str, Dict[str, str]]:
    """
    Compute hashes for multiple files in parallel using BatchProcessor.
    
    Args:
        file_paths: List of file paths
        storage_type: Storage type (NVMe, SSD, HDD)
        max_workers: Override worker count
        
    Returns:
        Dict mapping file path string to hash dict
    """
    if not HARDWARE_ACCEL_AVAILABLE:
        # Fallback to sequential
        result = {}
        for fp in file_paths:
            hashes = compute_hashes_sequential(fp)
            result[str(fp)] = hashes
        return result
    
    # Use batch processor
    processor = BatchProcessor(
        max_workers=max_workers,
        storage_type=storage_type,
        progress_callback=None,
    )
    
    path_strings = [str(fp) for fp in file_paths]
    hash_results = processor.process_files(
        path_strings,
        compute_md5=True,
        compute_sha256=True,
    )
    
    # Convert to dict
    result = {}
    for hr in hash_results:
        if not hr.error:
            result[hr.file_path] = {
                "md5": hr.md5 or "",
                "sha256": hr.sha256 or "",
            }
        else:
            result[hr.file_path] = {"md5": "", "sha256": "", "error": hr.error}
    
    return result


def compute_hashes_sequential(filepath: Path) -> Dict[str, str]:
    """Compute MD5 and SHA256 hashes for a single file (sequential fallback)."""
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


def extract_video_metadata(filepath: Path, video_processor: Optional[VideoProcessor] = None) -> Dict[str, Any]:
    """Extract video metadata using FFprobe or VideoProcessor."""
    video_data = {
        "duration": None,
        "codec": None,
        "width": None,
        "height": None,
        "fps": None,
        "bitrate": None,
        "creation_time": None,
        "thumbnail_path": None,
        "thumbnail_encoder": None,
        "thumbnail_time_ms": None,
    }
    
    # Use VideoProcessor if available (hardware-accelerated)
    if HARDWARE_ACCEL_AVAILABLE and video_processor:
        try:
            metadata = video_processor.extract_metadata(str(filepath))
            video_data.update({
                "duration": metadata.duration_sec,
                "codec": metadata.codec,
                "width": metadata.width,
                "height": metadata.height,
                "fps": metadata.fps,
                "bitrate": metadata.bitrate_bps,
                "creation_time": metadata.creation_time,
            })
            
            # Extract thumbnail using fast I-frame method
            thumb_dir = Path(__file__).parent.parent / "06_METADATA" / "thumbnails"
            thumb_dir.mkdir(parents=True, exist_ok=True)
            thumb_path = thumb_dir / f"{filepath.stem}.jpg"
            
            thumb_result = video_processor.extract_thumbnail(
                str(filepath),
                str(thumb_path),
                width=320,
                use_i_frame_only=True,  # Fast I-frame extraction
            )
            
            if thumb_result.success:
                video_data["thumbnail_path"] = str(thumb_path)
                video_data["thumbnail_encoder"] = thumb_result.encoder_used
                video_data["thumbnail_time_ms"] = round(thumb_result.extraction_time_ms, 2)
                logger.debug(f"Thumbnail: {thumb_result.extraction_time_ms:.1f}ms ({thumb_result.encoder_used})")
            
        except Exception as e:
            logger.debug(f"VideoProcessor failed for {filepath}: {e}")
            # Fallback to ffprobe
            return extract_video_metadata_ffprobe(filepath, video_data)
    else:
        return extract_video_metadata_ffprobe(filepath, video_data)
    
    return video_data


def extract_video_metadata_ffprobe(filepath: Path, video_data: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback video metadata extraction using ffprobe."""
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


def scan_drive(
    drive_path: Path,
    output_dir: Path,
    enable_hardware_accel: bool = True,
    storage_type: str = "SSD",
    max_workers: Optional[int] = None,
    thermal_monitor: Optional[ThermalMonitor] = None,
) -> Dict[str, Any]:
    """
    Scan drive and collect all file metadata with hardware acceleration.
    
    Args:
        drive_path: Path to drive/directory to scan
        output_dir: Output directory for reports
        enable_hardware_accel: Enable parallel hashing and GPU video processing
        storage_type: Storage type for worker optimization (NVMe, SSD, HDD)
        max_workers: Override worker count for parallel hashing
        thermal_monitor: Optional thermal monitor for drive protection
    """
    stats = {
        "total_files": 0,
        "total_size": 0,
        "files_by_type": {},
        "errors": [],
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "drive_path": str(drive_path),
        "hardware_accel_enabled": enable_hardware_accel and HARDWARE_ACCEL_AVAILABLE,
        "video_processor_encoder": None,
        "hashing_workers": 0,
        "thermal_monitoring": False,
    }
    
    file_records = []
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".heic", ".cr2", ".cr3", ".arw", ".nef", ".dng", ".raf"}
    video_extensions = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".wmv"}
    
    # Initialize hardware acceleration components
    video_processor = None
    if enable_hardware_accel and HARDWARE_ACCEL_AVAILABLE:
        try:
            video_processor = VideoProcessor(log_path=str(LOG_DIR / "video_processor.log"))
            encoder_stats = video_processor.get_encoder_statistics()
            stats["video_processor_encoder"] = encoder_stats.get("selected_encoder")
            logger.info(f"Video processor initialized: {stats['video_processor_encoder']}")
        except Exception as e:
            logger.warning(f"Failed to initialize video processor: {e}")
    
    # Start thermal monitoring if available
    if thermal_monitor:
        try:
            if thermal_monitor.start():
                stats["thermal_monitoring"] = True
                logger.info("Thermal monitoring started")
        except Exception as e:
            logger.warning(f"Failed to start thermal monitoring: {e}")
    
    # First pass: collect all file paths
    print(f"\n{'='*80}")
    print(f"DRIVE AUDIT STARTED (Hardware-Accelerated)" if enable_hardware_accel else f"DRIVE AUDIT STARTED")
    print(f"{'='*80}")
    print(f"Drive: {drive_path}")
    print(f"Output: {output_dir}")
    if enable_hardware_accel and HARDWARE_ACCEL_AVAILABLE:
        print(f"Hardware Acceleration: ✓ Enabled")
        print(f"Video Encoder: {stats['video_processor_encoder']}")
        print(f"Storage Type: {storage_type}")
    else:
        print(f"Hardware Acceleration: ✗ Disabled/Unavailable")
    print(f"{'='*80}\n")
    
    # Collect all files first
    all_files = []
    for root, dirs, files in os.walk(drive_path):
        for filename in files:
            filepath = Path(root) / filename
            all_files.append(filepath)
    
    print(f"📁 Found {len(all_files)} files to process")
    
    # Calculate optimal workers for parallel hashing
    if enable_hardware_accel and HARDWARE_ACCEL_AVAILABLE:
        stats["hashing_workers"] = max_workers or calculate_optimal_workers(storage_type)
        logger.info(f"Parallel hashing: {stats['hashing_workers']} workers")
    
    # Process files in batches for parallel hashing
    batch_size = 100
    thumbnail_stats = {"total_time_ms": 0, "count": 0, "encoder_usage": {}}
    
    for batch_start in range(0, len(all_files), batch_size):
        batch_files = all_files[batch_start:batch_start + batch_size]
        
        # Check thermal status before processing batch
        if thermal_monitor and not thermal_monitor.is_operations_allowed():
            logger.info("Waiting for thermal resume...")
            thermal_monitor.wait_for_resume(timeout=300)
        
        # Collect file info for batch
        batch_info = []
        for filepath in batch_files:
            stats["total_files"] += 1
            try:
                stat_info = filepath.stat()
                file_size = stat_info.st_size
                created = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
                modified = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                
                stats["total_size"] += file_size
                
                ext = filepath.suffix.lower()
                if ext in image_extensions:
                    file_type = "IMAGE"
                elif ext in video_extensions:
                    file_type = "VIDEO"
                else:
                    file_type = "OTHER"
                
                stats["files_by_type"][file_type] = stats["files_by_type"].get(file_type, 0) + 1
                
                batch_info.append({
                    "path": filepath,
                    "filename": filepath.name,
                    "extension": ext,
                    "size_bytes": file_size,
                    "created": created,
                    "modified": modified,
                    "file_type": file_type,
                })
            except (PermissionError, OSError) as e:
                logger.warning(f"Cannot stat {filepath}: {e}")
                stats["errors"].append({"path": str(filepath), "error": str(e)})
        
        # Compute hashes in parallel for this batch
        if enable_hardware_accel and HARDWARE_ACCEL_AVAILABLE and batch_info:
            batch_paths = [info["path"] for info in batch_info]
            hash_results = compute_hashes_parallel(
                batch_paths,
                storage_type=storage_type,
                max_workers=max_workers,
            )
        else:
            # Sequential fallback
            hash_results = {}
            for info in batch_info:
                hash_results[str(info["path"])] = compute_hashes_sequential(info["path"])
        
        # Process each file in batch
        for info in batch_info:
            filepath = info["path"]
            hashes = hash_results.get(str(filepath), {"md5": "", "sha256": ""})
            
            # Get MIME type
            mime_type = get_mime_type(filepath)
            
            # Extract metadata based on file type
            exif_data = {}
            video_data = {}
            
            if info["file_type"] == "IMAGE":
                exif_data = extract_exif_data(filepath)
            elif info["file_type"] == "VIDEO" and video_processor:
                video_data = extract_video_metadata(filepath, video_processor)
                # Track thumbnail stats
                if video_data.get("thumbnail_time_ms"):
                    thumbnail_stats["total_time_ms"] += video_data["thumbnail_time_ms"]
                    thumbnail_stats["count"] += 1
                    encoder = video_data.get("thumbnail_encoder", "unknown")
                    thumbnail_stats["encoder_usage"][encoder] = thumbnail_stats["encoder_usage"].get(encoder, 0) + 1
            elif info["file_type"] == "VIDEO":
                video_data = extract_video_metadata_ffprobe(filepath, {})
            
            # Build record
            record = {
                "path": str(filepath),
                "filename": info["filename"],
                "extension": info["extension"],
                "size_bytes": info["size_bytes"],
                "created": info["created"],
                "modified": info["modified"],
                "md5": hashes.get("md5", ""),
                "sha256": hashes.get("sha256", ""),
                "mime_type": mime_type,
                "file_type": info["file_type"],
                **exif_data,
                **video_data
            }
            
            file_records.append(record)
        
        # Progress indicator
        progress = min(batch_start + batch_size, len(all_files))
        if progress % 100 == 0 or progress == len(all_files):
            print(f"  Processed {progress}/{len(all_files)} files...")
    
    # Stop thermal monitoring
    if thermal_monitor:
        thermal_monitor.stop()
    
    stats["end_time"] = datetime.now().isoformat()
    stats["file_records"] = file_records
    
    # Add thumbnail statistics
    if thumbnail_stats["count"] > 0:
        stats["thumbnail_statistics"] = {
            "total_thumbnails": thumbnail_stats["count"],
            "avg_time_ms": round(thumbnail_stats["total_time_ms"] / thumbnail_stats["count"], 2),
            "encoder_usage": thumbnail_stats["encoder_usage"],
        }
        logger.info(f"Thumbnail stats: {thumbnail_stats['count']} files, avg {stats['thumbnail_statistics']['avg_time_ms']:.1f}ms")
    
    return stats


def write_outputs(stats: Dict[str, Any], output_dir: Path) -> None:
    """Write CSV and JSON output files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Write CSV
    csv_path = output_dir / f"audit_{timestamp}.csv"
    file_records = stats.pop("file_records", [])
    
    if file_records:
        # Collect all unique fieldnames from all records (not just first)
        all_fieldnames = set()
        for record in file_records:
            all_fieldnames.update(record.keys())
        fieldnames = sorted(all_fieldnames)  # Sort for consistent ordering
        
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
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
    """Print audit summary to console with hardware acceleration stats."""
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
    
    # Hardware acceleration statistics
    if stats.get("hardware_accel_enabled"):
        print(f"\n🚀 HARDWARE ACCELERATION")
        print(f"   Enabled: ✓")
        if stats.get("hashing_workers"):
            print(f"   Parallel Hashing: {stats['hashing_workers']} workers")
        if stats.get("video_processor_encoder"):
            print(f"   Video Encoder: {stats['video_processor_encoder']}")
        if stats.get("thumbnail_statistics"):
            thumb_stats = stats["thumbnail_statistics"]
            print(f"   Thumbnails: {thumb_stats['total_thumbnails']} extracted")
            print(f"   Avg Thumbnail Time: {thumb_stats['avg_time_ms']:.1f}ms")
            if thumb_stats.get("encoder_usage"):
                print(f"   Encoder Usage: {thumb_stats['encoder_usage']}")
        if stats.get("thermal_monitoring"):
            print(f"   Thermal Monitoring: ✓ Active")
    else:
        print(f"\n🚀 HARDWARE ACCELERATION")
        print(f"   Enabled: ✗ (sequential processing)")
    
    # Calculate throughput
    total_seconds = duration.total_seconds()
    if total_seconds > 0:
        files_per_sec = stats['total_files'] / total_seconds
        mb_per_sec = (stats['total_size'] / (1024 * 1024)) / total_seconds
        print(f"\n📈 THROUGHPUT")
        print(f"   Files/sec: {files_per_sec:.1f}")
        print(f"   MB/sec: {mb_per_sec:.1f}")
    
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
        description="Hardware-accelerated drive audit and metadata extraction"
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
    parser.add_argument(
        "--no-hardware-accel",
        action="store_true",
        help="Disable hardware acceleration (use sequential processing)"
    )
    parser.add_argument(
        "--storage-type",
        type=str,
        choices=["NVMe", "SSD", "HDD"],
        default="SSD",
        help="Storage type for worker optimization (default: SSD)"
    )
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help="Override worker count for parallel hashing"
    )
    parser.add_argument(
        "--thermal-drive",
        type=str,
        default=None,
        help="Drive path for thermal monitoring (e.g., /dev/sda)"
    )
    parser.add_argument(
        "--thermal-pause",
        type=float,
        default=55.0,
        help="Temperature threshold to pause (default: 55°C)"
    )
    parser.add_argument(
        "--thermal-resume",
        type=float,
        default=45.0,
        help="Temperature threshold to resume (default: 45°C)"
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
        # Initialize thermal monitor if requested
        thermal_monitor = None
        if args.thermal_drive and HARDWARE_ACCEL_AVAILABLE:
            try:
                thermal_monitor = ThermalMonitor(
                    drive_path=args.thermal_drive,
                    pause_threshold_celsius=args.thermal_pause,
                    resume_threshold_celsius=args.thermal_resume,
                    log_path=str(LOG_DIR / "thermal_monitor.log"),
                )
                if not thermal_monitor.check_smartctl_available():
                    logger.warning("smartctl not available - thermal monitoring disabled")
                    thermal_monitor = None
            except Exception as e:
                logger.warning(f"Failed to initialize thermal monitor: {e}")
                thermal_monitor = None
        
        # Run audit with hardware acceleration
        enable_hardware_accel = not args.no_hardware_accel and HARDWARE_ACCEL_AVAILABLE
        
        stats = scan_drive(
            args.drive_path,
            args.output_dir,
            enable_hardware_accel=enable_hardware_accel,
            storage_type=args.storage_type,
            max_workers=args.workers,
            thermal_monitor=thermal_monitor,
        )
        
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
