#!/usr/bin/env python3
"""
lightroom_export_parser.py — Lightroom Catalog Parser and Reconciliation

Parses Lightroom .lrcat (SQLite) catalogs to extract:
- File paths
- Keywords and keyword hierarchy
- Collections (smart and manual)
- Ratings, color labels, pick flags
- Develop settings
- Cross-references catalog paths vs filesystem

Outputs reconciliation report showing:
- Files in catalog but missing from disk
- Files on disk but not in catalog (orphans)
- Moved paths
- Storage statistics

Usage:
    python lightroom_export_parser.py /path/to/catalog.lrcat [--scan-paths /path1 /path2]
"""

import argparse
import csv
import json
import logging
import sqlite3
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
        logging.FileHandler(LOG_DIR / f"lightroom_parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class LightroomCatalogParser:
    """Parser for Lightroom .lrcat SQLite catalogs."""
    
    def __init__(self, catalog_path: Path):
        self.catalog_path = catalog_path
        self.conn = None
        self.data = {
            "catalog_path": str(catalog_path),
            "parse_time": datetime.now().isoformat(),
            "images": [],
            "keywords": [],
            "collections": [],
            "folders": [],
            "develop_settings": [],
            "statistics": {}
        }
    
    def connect(self) -> bool:
        """Connect to catalog database (read-only)."""
        try:
            # Connect in read-only mode
            self.conn = sqlite3.connect(
                f"file:{self.catalog_path}?mode=ro",
                uri=True
            )
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to catalog: {self.catalog_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to catalog: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def extract_images(self) -> List[Dict]:
        """Extract all images with metadata."""
        logger.info("Extracting images...")
        
        images = []
        try:
            cursor = self.conn.cursor()
            
            # Main image query
            cursor.execute('''
                SELECT 
                    img.id AS image_id,
                    img.captureTime,
                    img.rating,
                    img.hasFlags,
                    img.pickFlags,
                    img.colorLabels,
                    img.fileType,
                    img.fileWidth,
                    img.fileHeight,
                    img.fileSize,
                    file.baseName,
                    file.extension,
                    folder.pathFromRoot,
                    root.absolutePath
                FROM Adobe_images img
                JOIN AgLibraryFile file ON img.id_file = file.id
                JOIN AgLibraryFolder folder ON file.id_folder = folder.id
                JOIN AgRootFolderList root ON folder.id_root = root.id
                ORDER BY img.captureTime
            ''')
            
            for row in cursor.fetchall():
                # Reconstruct full path
                full_path = ""
                if row["absolutePath"] and row["pathFromRoot"]:
                    full_path = row["absolutePath"] + row["pathFromRoot"]
                if row["baseName"]:
                    full_path += row["baseName"]
                if row["extension"]:
                    full_path += "." + row["extension"]
                
                image_data = {
                    "image_id": row["image_id"],
                    "capture_time": row["captureTime"],
                    "rating": row["rating"],
                    "has_flags": bool(row["hasFlags"]),
                    "pick_flag": row["pickFlags"],  # -1 = rejected, 0 = none, 1 = picked
                    "color_labels": row["colorLabels"],
                    "file_type": row["fileType"],
                    "width": row["fileWidth"],
                    "height": row["fileHeight"],
                    "size": row["fileSize"],
                    "filename": row["baseName"] + "." + row["extension"] if row["baseName"] else "",
                    "folder_path": row["pathFromRoot"],
                    "root_path": row["absolutePath"],
                    "full_path": full_path
                }
                
                images.append(image_data)
            
            logger.info(f"Extracted {len(images)} images")
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
        
        self.data["images"] = images
        return images
    
    def extract_keywords(self) -> List[Dict]:
        """Extract keywords and hierarchy."""
        logger.info("Extracting keywords...")
        
        keywords = []
        try:
            cursor = self.conn.cursor()
            
            # Get keyword hierarchy
            cursor.execute('''
                SELECT 
                    kw.id,
                    kw.name,
                    kw.parent,
                    parent_kw.name as parent_name
                FROM AgKeyword kw
                LEFT JOIN AgKeyword parent_kw ON kw.parent = parent_kw.id
            ''')
            
            keyword_map = {}
            for row in cursor.fetchall():
                keyword_map[row["id"]] = {
                    "id": row["id"],
                    "name": row["name"],
                    "parent_id": row["parent"],
                    "parent_name": row["parent_name"]
                }
            
            # Get keyword-image associations
            cursor.execute('''
                SELECT 
                    ki.id_keyword,
                    ki.id_image
                FROM KeywordImages ki
            ''')
            
            keyword_images = defaultdict(list)
            for row in cursor.fetchall():
                keyword_images[row["id_keyword"]].append(row["id_image"])
            
            # Build keyword list with image counts
            for kw_id, kw_data in keyword_map.items():
                kw_data["image_count"] = len(keyword_images.get(kw_id, []))
                keywords.append(kw_data)
            
            logger.info(f"Extracted {len(keywords)} keywords")
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
        
        self.data["keywords"] = keywords
        return keywords
    
    def extract_collections(self) -> List[Dict]:
        """Extract collections (smart and manual)."""
        logger.info("Extracting collections...")
        
        collections = []
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT 
                    coll.id,
                    coll.name,
                    coll.collectionType,
                    coll.parentCollectionId,
                    parent.name as parent_name,
                    COUNT(ci.id_image) as image_count
                FROM AgLibraryCollection coll
                LEFT JOIN AgLibraryCollection parent ON coll.parentCollectionId = parent.id
                LEFT JOIN AgCollectionImage ci ON coll.id = ci.id_collection
                GROUP BY coll.id
            ''')
            
            for row in cursor.fetchall():
                collections.append({
                    "id": row["id"],
                    "name": row["name"],
                    "type": row["collectionType"],  # 0 = normal, 1 = smart
                    "parent_id": row["parentCollectionId"],
                    "parent_name": row["parent_name"],
                    "image_count": row["image_count"]
                })
            
            logger.info(f"Extracted {len(collections)} collections")
            
        except Exception as e:
            logger.error(f"Error extracting collections: {e}")
        
        self.data["collections"] = collections
        return collections
    
    def extract_folders(self) -> List[Dict]:
        """Extract folder structure."""
        logger.info("Extracting folders...")
        
        folders = []
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT 
                    folder.id,
                    folder.pathFromRoot,
                    root.absolutePath,
                    COUNT(file.id) as file_count
                FROM AgLibraryFolder folder
                JOIN AgRootFolderList root ON folder.id_root = root.id
                LEFT JOIN AgLibraryFile file ON file.id_folder = folder.id
                GROUP BY folder.id
            ''')
            
            for row in cursor.fetchall():
                folders.append({
                    "id": row["id"],
                    "path": row["pathFromRoot"],
                    "root": row["absolutePath"],
                    "full_path": (row["absolutePath"] or "") + (row["pathFromRoot"] or ""),
                    "file_count": row["file_count"]
                })
            
            logger.info(f"Extracted {len(folders)} folders")
            
        except Exception as e:
            logger.error(f"Error extracting folders: {e}")
        
        self.data["folders"] = folders
        return folders
    
    def extract_develop_settings(self) -> List[Dict]:
        """Extract develop settings for images."""
        logger.info("Extracting develop settings...")
        
        settings = []
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT 
                    id,
                    processVersion,
                    exposure,
                    contrast,
                    highlights,
                    shadows,
                    whites,
                    blacks,
                    clarity,
                    vibrance,
                    saturation,
                    temperature,
                    tint,
                    cropTop,
                    cropLeft,
                    cropBottom,
                    cropRight,
                    rotation
                FROM ImageDevelopSettings
                WHERE exposure IS NOT NULL OR cropTop IS NOT NULL
            ''')
            
            for row in cursor.fetchall():
                settings.append({
                    "image_id": row["id"],
                    "process_version": row["processVersion"],
                    "exposure": row["exposure"],
                    "contrast": row["contrast"],
                    "highlights": row["highlights"],
                    "shadows": row["shadows"],
                    "whites": row["whites"],
                    "blacks": row["blacks"],
                    "clarity": row["clarity"],
                    "vibrance": row["vibrance"],
                    "saturation": row["saturation"],
                    "temperature": row["temperature"],
                    "tint": row["tint"],
                    "crop_top": row["cropTop"],
                    "crop_left": row["cropLeft"],
                    "crop_bottom": row["cropBottom"],
                    "crop_right": row["cropRight"],
                    "rotation": row["rotation"]
                })
            
            logger.info(f"Extracted {len(settings)} develop settings")
            
        except Exception as e:
            logger.error(f"Error extracting develop settings: {e}")
        
        self.data["develop_settings"] = settings
        return settings
    
    def parse_all(self) -> Dict:
        """Extract all data from catalog."""
        if not self.connect():
            return self.data
        
        try:
            self.extract_images()
            self.extract_keywords()
            self.extract_collections()
            self.extract_folders()
            self.extract_develop_settings()
            
            # Calculate statistics
            self.data["statistics"] = {
                "total_images": len(self.data["images"]),
                "total_keywords": len(self.data["keywords"]),
                "total_collections": len(self.data["collections"]),
                "total_folders": len(self.data["folders"]),
                "images_with_develop": len(self.data["develop_settings"]),
                "images_by_rating": self._count_by_rating(),
                "images_by_flag": self._count_by_flag()
            }
            
        finally:
            self.close()
        
        return self.data
    
    def _count_by_rating(self) -> Dict:
        """Count images by star rating."""
        counts = defaultdict(int)
        for img in self.data["images"]:
            rating = img.get("rating") or 0
            counts[str(rating)] += 1
        return dict(counts)
    
    def _count_by_flag(self) -> Dict:
        """Count images by pick flag."""
        counts = {"picked": 0, "rejected": 0, "unflagged": 0}
        for img in self.data["images"]:
            flag = img.get("pick_flag")
            if flag == 1:
                counts["picked"] += 1
            elif flag == -1:
                counts["rejected"] += 1
            else:
                counts["unflagged"] += 1
        return counts


def scan_filesystem(paths: List[Path]) -> Set[str]:
    """Scan filesystem paths and return set of file paths."""
    filesystem_paths = set()
    
    for scan_path in paths:
        if not scan_path.exists():
            logger.warning(f"Scan path does not exist: {scan_path}")
            continue
        
        logger.info(f"Scanning: {scan_path}")
        count = 0
        
        for filepath in scan_path.rglob("*"):
            if filepath.is_file():
                filesystem_paths.add(str(filepath))
                count += 1
        
        logger.info(f"  Found {count} files")
    
    return filesystem_paths


def reconcile_catalog_vs_filesystem(
    catalog_data: Dict,
    filesystem_paths: Optional[Set[str]] = None
) -> Dict:
    """Compare catalog paths against filesystem."""
    results = {
        "reconciliation_time": datetime.now().isoformat(),
        "catalog_path": catalog_data["catalog_path"],
        "total_catalog_images": len(catalog_data["images"]),
        "missing_from_disk": [],
        "orphans_on_disk": [],
        "moved_paths": [],
        "statistics": {}
    }
    
    # Get catalog paths
    catalog_paths = set()
    path_to_image = {}
    
    for img in catalog_data["images"]:
        full_path = img.get("full_path")
        if full_path:
            catalog_paths.add(full_path)
            path_to_image[full_path] = img
    
    # Compare with filesystem
    if filesystem_paths:
        # Missing from disk (in catalog but not on disk)
        missing = catalog_paths - filesystem_paths
        results["missing_from_disk"] = [
            {
                "path": path,
                "image": path_to_image.get(path, {})
            }
            for path in sorted(missing)
        ]
        
        # Orphans on disk (on disk but not in catalog)
        # Filter to image files only
        image_extensions = {".jpg", ".jpeg", ".png", ".cr2", ".cr3", ".arw", ".nef", ".dng", ".raf", ".mp4", ".mov"}
        orphans = {
            p for p in filesystem_paths
            if Path(p).suffix.lower() in image_extensions
        } - catalog_paths
        
        results["orphans_on_disk"] = sorted(list(orphans))[:1000]  # Limit to 1000
    
    # Statistics
    results["statistics"] = {
        "catalog_paths": len(catalog_paths),
        "filesystem_paths": len(filesystem_paths) if filesystem_paths else 0,
        "missing_count": len(results["missing_from_disk"]),
        "orphan_count": len(results["orphans_on_disk"]),
        "match_percentage": (
            100 * (len(catalog_paths) - len(results["missing_from_disk"])) / max(len(catalog_paths), 1)
        )
    }
    
    return results


def generate_report(
    catalog_data: Dict,
    reconciliation: Dict,
    output_dir: Path
) -> Tuple[Path, Path]:
    """Generate reconciliation reports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON report
    json_path = output_dir / f"lightroom_report_{timestamp}.json"
    report_data = {
        **catalog_data,
        "reconciliation": reconciliation
    }
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, default=str)
    
    # CSV for missing files
    csv_path = output_dir / f"lightroom_missing_{timestamp}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "path", "filename", "capture_time", "rating", "pick_flag",
            "color_labels", "file_type", "root_path", "folder_path"
        ])
        
        for item in reconciliation.get("missing_from_disk", []):
            img = item.get("image", {})
            writer.writerow([
                item["path"],
                img.get("filename", ""),
                img.get("capture_time", ""),
                img.get("rating", ""),
                img.get("pick_flag", ""),
                img.get("color_labels", ""),
                img.get("file_type", ""),
                img.get("root_path", ""),
                img.get("folder_path", "")
            ])
    
    return json_path, csv_path


def print_summary(catalog_data: Dict, reconciliation: Dict) -> None:
    """Print summary to console."""
    stats = catalog_data.get("statistics", {})
    recon_stats = reconciliation.get("statistics", {})
    
    print(f"\n{'='*80}")
    print("LIGHTROOM CATALOG PARSER SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n📊 Catalog Statistics:")
    print(f"   Total Images: {stats.get('total_images', 0):,}")
    print(f"   Total Keywords: {stats.get('total_keywords', 0):,}")
    print(f"   Total Collections: {stats.get('total_collections', 0):,}")
    print(f"   Total Folders: {stats.get('total_folders', 0):,}")
    print(f"   Images with Develop Settings: {stats.get('images_with_develop', 0):,}")
    
    print(f"\n⭐ Ratings Distribution:")
    for rating, count in sorted(stats.get('images_by_rating', {}).items()):
        stars = "★" * int(rating) if rating != "0" else "No rating"
        print(f"   {stars:12s}: {count:,}")
    
    print(f"\n🚩 Flags:")
    flags = stats.get('images_by_flag', {})
    print(f"   Picked: {flags.get('picked', 0):,}")
    print(f"   Rejected: {flags.get('rejected', 0):,}")
    print(f"   Unflagged: {flags.get('unflagged', 0):,}")
    
    if reconciliation:
        print(f"\n🔍 Reconciliation:")
        print(f"   Catalog Paths: {recon_stats.get('catalog_paths', 0):,}")
        print(f"   Filesystem Paths: {recon_stats.get('filesystem_paths', 0):,}")
        print(f"   Missing from Disk: {recon_stats.get('missing_count', 0):,}")
        print(f"   Orphans on Disk: {recon_stats.get('orphan_count', 0):,}")
        print(f"   Match Rate: {recon_stats.get('match_percentage', 0):.1f}%")
        
        if recon_stats.get('missing_count', 0) > 0:
            print(f"\n⚠️  {recon_stats.get('missing_count', 0):,} files in catalog are missing from disk!")
            print(f"   These may have been moved, deleted, or the drive is not mounted.")
    
    print(f"\n{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Parse Lightroom catalog and reconcile with filesystem"
    )
    parser.add_argument(
        "catalog",
        type=Path,
        help="Path to Lightroom catalog (.lrcat file)"
    )
    parser.add_argument(
        "--scan-paths",
        type=Path,
        nargs="*",
        help="Filesystem paths to scan for reconciliation"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "reports",
        help="Output directory for reports (default: ./reports/)"
    )
    parser.add_argument(
        "--no-reconcile",
        action="store_true",
        help="Skip filesystem reconciliation"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate catalog
    if not args.catalog.exists():
        logger.error(f"Catalog does not exist: {args.catalog}")
        sys.exit(1)
    
    if args.catalog.suffix.lower() != ".lrcat":
        logger.warning(f"File may not be a Lightroom catalog: {args.catalog}")
    
    try:
        print(f"\n{'='*80}")
        print("LIGHTROOM CATALOG PARSER")
        print(f"{'='*80}")
        print(f"Catalog: {args.catalog}")
        print(f"{'='*80}\n")
        
        # Parse catalog
        parser_obj = LightroomCatalogParser(args.catalog)
        catalog_data = parser_obj.parse_all()
        
        if not catalog_data["images"]:
            logger.warning("No images found in catalog")
        
        # Reconcile with filesystem
        reconciliation = {}
        if not args.no_reconcile:
            scan_paths = args.scan_paths or []
            
            # Auto-add root paths from catalog
            for folder in catalog_data.get("folders", []):
                root = folder.get("root")
                if root:
                    root_path = Path(root)
                    if root_path.exists() and root_path not in scan_paths:
                        scan_paths.append(root_path)
            
            if scan_paths:
                print("\nScanning filesystem for reconciliation...")
                filesystem_paths = scan_filesystems(scan_paths)
                reconciliation = reconcile_catalog_vs_filesystem(catalog_data, filesystem_paths)
            else:
                logger.info("No filesystem paths to scan, skipping reconciliation")
        
        # Generate reports
        json_path, csv_path = generate_report(catalog_data, reconciliation, args.output_dir)
        
        # Print summary
        print_summary(catalog_data, reconciliation)
        
        print(f"📄 Full Report: {json_path}")
        print(f"📊 Missing Files CSV: {csv_path}")
        
    except KeyboardInterrupt:
        logger.info("Parser interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Parser failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
