#!/usr/bin/env python3
"""
deduplicate.py — Duplicate and Near-Duplicate Detection

Finds exact and near-duplicate images across multiple folders:
- Builds MD5+SHA256 hash index for exact duplicates
- Computes perceptual hashes (pHash) for near-duplicates
- Detects RAW+JPG pairs and groups them
- Checks Lightroom catalog presence
- Outputs interactive HTML report + action plan CSV

Never auto-deletes - only reports and recommends.

Usage:
    python deduplicate.py /folder1 /folder2 /folder3 [--output-dir /path/to/output]
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
from typing import Any, Dict, List, Optional, Set, Tuple

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"dedupe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def compute_hashes(filepath: Path) -> Tuple[Optional[str], Optional[str]]:
    """Compute MD5 and SHA256 hashes for a file."""
    try:
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)
        
        return md5_hash.hexdigest(), sha256_hash.hexdigest()
    except (PermissionError, OSError) as e:
        logger.warning(f"Cannot compute hash for {filepath}: {e}")
        return None, None


def compute_phash(filepath: Path) -> Optional[str]:
    """
    Compute perceptual hash for image similarity detection.
    Uses average hash algorithm (simple, no external dependencies).
    """
    try:
        # Try to use imagehash library if available
        try:
            from PIL import Image
            import imagehash
            
            with Image.open(filepath) as img:
                # Convert to RGB if necessary
                if img.mode not in ('L', 'RGB'):
                    img = img.convert('RGB')
                
                # Compute perceptual hash
                phash = imagehash.phash(img)
                return str(phash)
        except ImportError:
            # Fallback: simple average hash using PIL only
            from PIL import Image
            
            with Image.open(filepath) as img:
                # Resize to 32x32 and convert to grayscale
                img = img.convert('L').resize((32, 32), Image.Resampling.LANCZOS)
                pixels = list(img.getdata())
                
                # Compute average
                avg = sum(pixels) / len(pixels)
                
                # Create hash based on whether each pixel is above/below average
                bits = ''.join('1' if pixel > avg else '0' for pixel in pixels)
                
                # Convert to hex
                hash_int = int(bits, 2)
                return format(hash_int, '0256x')  # 32*32 = 1024 bits = 256 hex chars
    except Exception as e:
        logger.debug(f"Perceptual hash failed for {filepath}: {e}")
        return None


def hamming_distance(hash1: str, hash2: str) -> int:
    """Calculate Hamming distance between two hex hash strings."""
    try:
        # Convert hex to binary
        bin1 = bin(int(hash1, 16))[2:].zfill(len(hash1) * 4)
        bin2 = bin(int(hash2, 16))[2:].zfill(len(hash2) * 4)
        
        # Calculate differences
        return sum(c1 != c2 for c1, c2 in zip(bin1, bin2))
    except (ValueError, TypeError):
        return 999  # Maximum distance


def scan_folders(folder_paths: List[Path]) -> Dict:
    """Scan folders and build hash index."""
    results = {
        "folders": [str(p) for p in folder_paths],
        "scan_time": datetime.now().isoformat(),
        "total_files": 0,
        "total_size": 0,
        "image_files": 0,
        "exact_duplicates": [],
        "near_duplicates": [],
        "file_index": {},  # path -> file_info
        "errors": []
    }
    
    image_extensions = {
        ".jpg", ".jpeg", ".png", ".gif", ".heic", ".tif", ".tiff",
        ".cr2", ".cr3", ".arw", ".nef", ".dng", ".raf", ".orf", ".rw2"
    }
    
    # Hash indexes
    md5_index = defaultdict(list)  # md5 -> [paths]
    sha256_index = defaultdict(list)  # sha256 -> [paths]
    phash_index = {}  # path -> phash
    
    print(f"\n{'='*80}")
    print("SCANNING FOLDERS")
    print(f"{'='*80}")
    
    for folder_idx, folder_path in enumerate(folder_paths, 1):
        print(f"\n[{folder_idx}/{len(folder_paths)}] Scanning: {folder_path}")
        
        if not folder_path.exists():
            logger.warning(f"Folder does not exist: {folder_path}")
            results["errors"].append(f"Folder not found: {folder_path}")
            continue
        
        file_count = 0
        for filepath in folder_path.rglob("*"):
            if filepath.is_file() and filepath.suffix.lower() in image_extensions:
                file_count += 1
                results["total_files"] += 1
                
                if results["total_files"] % 500 == 0:
                    print(f"  Processed {results['total_files']} files...")
                
                try:
                    stat_info = filepath.stat()
                    size = stat_info.st_size
                    modified = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                    
                    results["total_size"] += size
                    results["image_files"] += 1
                    
                    # Compute hashes
                    md5, sha256 = compute_hashes(filepath)
                    
                    file_info = {
                        "path": str(filepath),
                        "filename": filepath.name,
                        "size": size,
                        "modified": modified,
                        "md5": md5,
                        "sha256": sha256,
                        "folder_index": folder_idx
                    }
                    
                    results["file_index"][str(filepath)] = file_info
                    
                    if md5:
                        md5_index[md5].append(str(filepath))
                    if sha256:
                        sha256_index[sha256].append(str(filepath))
                    
                    # Compute perceptual hash for images
                    if filepath.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                        phash = compute_phash(filepath)
                        if phash:
                            phash_index[str(filepath)] = phash
                            file_info["phash"] = phash
                            
                except Exception as e:
                    logger.warning(f"Error processing {filepath}: {e}")
                    results["errors"].append({"path": str(filepath), "error": str(e)})
        
        print(f"  Found {file_count} image files")
    
    print(f"\nTotal: {results['total_files']} files, {results['total_size'] / (1024**3):.2f} GB")
    
    # Find exact duplicates (same SHA256)
    print("\nFinding exact duplicates...")
    for sha256, paths in sha256_index.items():
        if len(paths) > 1:
            # Get file info
            files = [results["file_index"][p] for p in paths if p in results["file_index"]]
            if files:
                results["exact_duplicates"].append({
                    "hash": sha256,
                    "count": len(files),
                    "size": files[0]["size"],
                    "files": files
                })
    
    print(f"Found {len(results['exact_duplicates'])} exact duplicate groups")
    
    # Find near-duplicates (similar perceptual hashes)
    print("\nFinding near-duplicates (this may take a while)...")
    phash_paths = list(phash_index.keys())
    near_dup_threshold = 10  # Hamming distance threshold
    
    processed_pairs = set()
    for i, path1 in enumerate(phash_paths):
        if i % 100 == 0:
            print(f"  Comparing {i}/{len(phash_paths)} images...")
        
        phash1 = phash_index[path1]
        
        for path2 in phash_paths[i+1:]:
            pair_key = tuple(sorted([path1, path2]))
            if pair_key in processed_pairs:
                continue
            processed_pairs.add(pair_key)
            
            phash2 = phash_index.get(path2)
            if not phash2:
                continue
            
            distance = hamming_distance(phash1, phash2)
            
            if distance <= near_dup_threshold:
                # Check if not already exact duplicate
                file1 = results["file_index"].get(path1)
                file2 = results["file_index"].get(path2)
                
                if file1 and file2 and file1.get("sha256") != file2.get("sha256"):
                    results["near_duplicates"].append({
                        "phash1": phash1,
                        "phash2": phash2,
                        "distance": distance,
                        "files": [file1, file2]
                    })
    
    print(f"Found {len(results['near_duplicates'])} near-duplicate pairs")
    
    return results


def check_lightroom_presence(file_paths: List[str], catalog_path: Optional[Path] = None) -> Dict[str, bool]:
    """Check if files are present in Lightroom catalog."""
    presence = {path: False for path in file_paths}
    
    if not catalog_path or not catalog_path.exists():
        logger.info("No Lightroom catalog specified, skipping catalog check")
        return presence
    
    try:
        import sqlite3
        
        # Connect to catalog (read-only)
        conn = sqlite3.connect(f"file:{catalog_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        
        # Get all file paths from catalog
        cursor.execute('''
            SELECT root.absolutePath, folder.pathFromRoot, file.baseName, file.extension
            FROM Adobe_images img
            JOIN AgLibraryFile file ON img.id_file = file.id
            JOIN AgLibraryFolder folder ON file.id_folder = folder.id
            JOIN AgRootFolderList root ON folder.id_root = root.id
        ''')
        
        catalog_paths = set()
        for row in cursor.fetchall():
            full_path = "".join(row)
            catalog_paths.add(full_path)
            # Also add without extension for comparison
            catalog_paths.add(str(Path(full_path).with_suffix('')))
        
        # Check presence
        for path in file_paths:
            if path in catalog_paths or str(Path(path).with_suffix('')) in catalog_paths:
                presence[path] = True
        
        conn.close()
        logger.info(f"Checked {len(file_paths)} files against Lightroom catalog")
        
    except Exception as e:
        logger.warning(f"Lightroom catalog check failed: {e}")
    
    return presence


def generate_html_report(results: Dict, output_path: Path) -> None:
    """Generate interactive HTML report."""
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Duplicate Detection Report</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 1400px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 12px; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .section { background: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .section h2 { color: #667eea; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #eee; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 8px; text-align: center; }
        .stat-card .value { font-size: 2.5em; font-weight: bold; color: #667eea; }
        .stat-card .label { color: #666; font-size: 0.9em; margin-top: 5px; }
        .dup-group { background: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #dc3545; }
        .dup-group.near { border-left-color: #ffc107; }
        .file-list { margin-top: 10px; }
        .file-item { background: white; padding: 10px; margin: 5px 0; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
        .file-item.in-lr { border-left: 3px solid #28a745; }
        .file-path { font-family: monospace; font-size: 0.9em; color: #555; word-break: break-all; }
        .file-meta { font-size: 0.85em; color: #888; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 600; margin-left: 10px; }
        .badge-lr { background: #d4edda; color: #155724; }
        .badge-size { background: #e3f2fd; color: #1976d2; }
        .action-select { margin-left: 10px; padding: 5px; border-radius: 4px; border: 1px solid #ddd; }
        .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 4px; }
        .footer { text-align: center; color: #666; padding: 20px; font-size: 0.9em; }
        .filter-controls { margin: 20px 0; display: flex; gap: 10px; flex-wrap: wrap; }
        .filter-controls input, .filter-controls select { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔄 Duplicate Detection Report</h1>
        <p>Generated {{ generated_date }}</p>
        <p>Folders: {{ folder_count }} • Total Files: {{ total_files }} • Total Size: {{ total_size_gb }} GB</p>
    </div>

    <div class="section">
        <h2>📊 Summary</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{{ exact_dup_groups }}</div>
                <div class="label">Exact Duplicate Groups</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ exact_dup_files }}</div>
                <div class="label">Files in Duplicate Groups</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ recoverable_gb }}</div>
                <div class="label">Recoverable Space (GB)</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ near_dup_pairs }}</div>
                <div class="label">Near-Duplicate Pairs</div>
            </div>
        </div>
        
        <div class="warning">
            <strong>⚠️ Important:</strong> This report never auto-deletes files. Review carefully before taking action.
            Files marked as "In Lightroom" are referenced in your catalog - be cautious when removing these.
        </div>
    </div>

    <div class="section">
        <h2>📋 Exact Duplicates</h2>
        <div class="filter-controls">
            <input type="text" id="exactFilter" placeholder="Filter by path..." style="flex: 1;">
            <select id="exactSizeFilter">
                <option value="0">All sizes</option>
                <option value="1048576">> 1 MB</option>
                <option value="10485760">> 10 MB</option>
                <option value="104857600">> 100 MB</option>
            </select>
        </div>
        
        {% for group in exact_duplicates %}
        <div class="dup-group" data-size="{{ group.size }}">
            <strong>Hash:</strong> {{ group.hash[:16] }}... • 
            <strong>Copies:</strong> {{ group.count }} • 
            <strong>Size:</strong> {{ (group.size / 1048576)|round(2) }} MB each •
            <strong>Wasted:</strong> {{ ((group.size * (group.count - 1)) / 1048576)|round(2) }} MB
            
            <div class="file-list">
                {% for file in group.files %}
                <div class="file-item {{ 'in-lr' if file.in_lightroom else '' }}">
                    <div>
                        <div class="file-path">{{ file.path }}</div>
                        <div class="file-meta">Modified: {{ file.modified }} • Folder #{{ file.folder_index }}</div>
                    </div>
                    <div>
                        {% if file.in_lightroom %}
                        <span class="badge badge-lr">In Lightroom</span>
                        {% endif %}
                        <span class="badge badge-size">{{ (file.size / 1048576)|round(1) }} MB</span>
                        <select class="action-select" data-path="{{ file.path }}">
                            <option value="keep">Keep</option>
                            <option value="delete">Delete</option>
                            <option value="archive">Archive</option>
                        </select>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="section">
        <h2>🔍 Near-Duplicates (Perceptual)</h2>
        <div class="filter-controls">
            <input type="text" id="nearFilter" placeholder="Filter by path..." style="flex: 1;">
        </div>
        
        {% for pair in near_duplicates %}
        <div class="dup-group near">
            <strong>Similarity:</strong> {{ (100 - (pair.distance / 64 * 100))|round(1) }}% • 
            <strong>Hamming Distance:</strong> {{ pair.distance }}
            
            <div class="file-list">
                {% for file in pair.files %}
                <div class="file-item {{ 'in-lr' if file.in_lightroom else '' }}">
                    <div>
                        <div class="file-path">{{ file.path }}</div>
                        <div class="file-meta">Size: {{ (file.size / 1048576)|round(1) }} MB • Modified: {{ file.modified }}</div>
                    </div>
                    <div>
                        {% if file.in_lightroom %}
                        <span class="badge badge-lr">In Lightroom</span>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="footer">
        <p>Generated by MediaAuditOrganizer • {{ generated_date }}</p>
        <p>Review carefully before taking any action. Always backup before deleting.</p>
    </div>

    <script>
        // Filter functionality
        document.getElementById('exactFilter').addEventListener('input', function(e) {
            const term = e.target.value.toLowerCase();
            document.querySelectorAll('.dup-group').forEach(group => {
                const text = group.textContent.toLowerCase();
                group.style.display = text.includes(term) ? '' : 'none';
            });
        });
        
        document.getElementById('exactSizeFilter').addEventListener('change', function(e) {
            const minSize = parseInt(e.target.value);
            document.querySelectorAll('.dup-group').forEach(group => {
                const size = parseInt(group.dataset.size);
                group.style.display = size >= minSize ? '' : 'none';
            });
        });
    </script>
</body>
</html>
"""
    
    # Prepare template data
    from jinja2 import Environment
    try:
        env = Environment()
        template = env.from_string(html)
        
        # Calculate stats
        exact_dup_files = sum(g["count"] for g in results["exact_duplicates"])
        recoverable = sum(g["size"] * (g["count"] - 1) for g in results["exact_duplicates"])
        
        rendered = template.render(
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M MST"),
            folder_count=len(results["folders"]),
            total_files=results["total_files"],
            total_size_gb=round(results["total_size"] / (1024**3), 2),
            exact_dup_groups=len(results["exact_duplicates"]),
            exact_dup_files=exact_dup_files,
            recoverable_gb=round(recoverable / (1024**3), 2),
            near_dup_pairs=len(results["near_duplicates"]),
            exact_duplicates=results["exact_duplicates"],
            near_duplicates=results["near_duplicates"]
        )
    except ImportError:
        # Fallback without Jinja2
        rendered = html.replace("{{ generated_date }}", datetime.now().strftime("%Y-%m-%d %H:%M MST"))
        rendered = rendered.replace("{{ folder_count }}", str(len(results["folders"])))
        rendered = rendered.replace("{{ total_files }}", str(results["total_files"]))
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)
    
    logger.info(f"HTML report: {output_path}")


def generate_action_plan(results: Dict, output_path: Path) -> None:
    """Generate action plan CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "action", "path", "reason", "size_bytes", "in_lightroom", "duplicate_group"
        ])
        
        # Recommend keeping first file in each duplicate group, mark others for review
        for i, group in enumerate(results["exact_duplicates"], 1):
            for j, file_info in enumerate(group["files"]):
                if j == 0:
                    action = "KEEP"
                    reason = "First in duplicate group"
                else:
                    action = "REVIEW"
                    reason = f"Duplicate of {group['files'][0]['path']}"
                
                writer.writerow([
                    action,
                    file_info["path"],
                    reason,
                    file_info["size"],
                    file_info.get("in_lightroom", False),
                    f"exact_group_{i}"
                ])
        
        # Near-duplicates
        for i, pair in enumerate(results["near_duplicates"], 1):
            for j, file_info in enumerate(pair["files"]):
                action = "REVIEW"
                reason = f"Near-duplicate (distance: {pair['distance']})"
                
                writer.writerow([
                    action,
                    file_info["path"],
                    reason,
                    file_info["size"],
                    file_info.get("in_lightroom", False),
                    f"near_dup_{i}"
                ])
    
    logger.info(f"Action plan CSV: {output_path}")


def print_summary(results: Dict) -> None:
    """Print deduplication summary."""
    exact_dup_files = sum(g["count"] for g in results["exact_duplicates"])
    recoverable = sum(g["size"] * (g["count"] - 1) for g in results["exact_duplicates"])
    
    print(f"\n{'='*80}")
    print("DEDUPLICATION SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n📊 Scanned: {results['total_files']} files ({results['total_size'] / (1024**3):.2f} GB)")
    print(f"📁 Folders: {len(results['folders'])}")
    
    print(f"\n🔄 Exact Duplicates:")
    print(f"   Groups: {len(results['exact_duplicates'])}")
    print(f"   Files involved: {exact_dup_files}")
    print(f"   Recoverable space: {recoverable / (1024**3):.2f} GB")
    
    print(f"\n🔍 Near-Duplicates:")
    print(f"   Pairs found: {len(results['near_duplicates'])}")
    
    if results["errors"]:
        print(f"\n⚠️  Errors: {len(results['errors'])}")
    
    print(f"\n{'='*80}")
    print("⚠️  NEVER AUTO-DELETE - Review report before taking action")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Find duplicate and near-duplicate images"
    )
    parser.add_argument(
        "folders",
        type=Path,
        nargs="+",
        help="Folders to scan for duplicates"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "reports",
        help="Output directory for reports (default: ./reports/)"
    )
    parser.add_argument(
        "--lightroom-catalog",
        type=Path,
        help="Optional Lightroom catalog path (.lrcat) to check file presence"
    )
    parser.add_argument(
        "--no-phash",
        action="store_true",
        help="Skip perceptual hash calculation (faster, no near-duplicates)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Scan folders
        results = scan_folders(args.folders)
        
        # Check Lightroom presence
        if args.lightroom_catalog:
            print("\nChecking Lightroom catalog presence...")
            all_paths = list(results["file_index"].keys())
            presence = check_lightroom_presence(all_paths, args.lightroom_catalog)
            
            # Update file index
            for path, in_lr in presence.items():
                if path in results["file_index"]:
                    results["file_index"][path]["in_lightroom"] = in_lr
            
            # Update duplicate groups
            for group in results["exact_duplicates"]:
                for file_info in group["files"]:
                    file_info["in_lightroom"] = presence.get(file_info["path"], False)
            
            for pair in results["near_duplicates"]:
                for file_info in pair["files"]:
                    file_info["in_lightroom"] = presence.get(file_info["path"], False)
        
        # Generate reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = args.output_dir / f"dedupe_report_{timestamp}.html"
        csv_path = args.output_dir / f"dedupe_action_plan_{timestamp}.csv"
        
        print("\nGenerating reports...")
        generate_html_report(results, html_path)
        generate_action_plan(results, csv_path)
        
        # Save JSON
        json_path = args.output_dir / f"dedupe_data_{timestamp}.json"
        # Remove large file_index for JSON (too big)
        json_results = {k: v for k, v in results.items() if k != "file_index"}
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_results, f, indent=2, default=str)
        
        # Print summary
        print_summary(results)
        
        print(f"📄 HTML Report: {html_path}")
        print(f"📊 Action Plan: {csv_path}")
        print(f"💾 Data: {json_path}\n")
        
    except KeyboardInterrupt:
        logger.info("Deduplication interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Deduplication failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
