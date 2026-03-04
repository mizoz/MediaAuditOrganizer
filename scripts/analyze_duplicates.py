#!/usr/bin/env python3
"""
analyze_duplicates.py — Duplicate Detection from Audit CSV

Reads audit CSV data and generates duplicate detection reports.
Never auto-deletes - only reports and recommends.

Usage:
    python analyze_duplicates.py <audit_csv> [--output-dir <path>]
"""

import csv
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Setup logging
LOG_DIR = Path(__file__).parent.parent / "07_LOGS"
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / f"dedupe_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def read_audit_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """Read audit CSV and return list of file records."""
    files = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            files.append(row)
    logger.info(f"Read {len(files)} files from {csv_path}")
    return files


def find_exact_duplicates(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group files by SHA256 hash to find exact duplicates."""
    sha256_index = defaultdict(list)
    
    for file_info in files:
        sha256 = file_info.get('sha256', '')
        if sha256:
            sha256_index[sha256].append(file_info)
    
    duplicate_groups = []
    for sha256, file_list in sha256_index.items():
        if len(file_list) > 1:
            duplicate_groups.append({
                'hash': sha256,
                'count': len(file_list),
                'size': int(file_list[0].get('size_bytes', 0)),
                'files': file_list
            })
    
    logger.info(f"Found {len(duplicate_groups)} exact duplicate groups")
    return duplicate_groups


def calculate_stats(files: List[Dict[str, Any]], duplicate_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics."""
    total_files = len(files)
    total_size = sum(int(f.get('size_bytes', 0)) for f in files)
    
    dup_file_count = sum(g['count'] for g in duplicate_groups)
    unique_files = total_files - dup_file_count + len(duplicate_groups)
    
    recoverable = sum(g['size'] * (g['count'] - 1) for g in duplicate_groups)
    
    return {
        'total_files': total_files,
        'total_size': total_size,
        'total_size_gb': round(total_size / (1024**3), 2),
        'unique_files': unique_files,
        'duplicate_groups': len(duplicate_groups),
        'duplicate_files': dup_file_count,
        'recoverable_bytes': recoverable,
        'recoverable_mb': round(recoverable / (1024**2), 2),
        'recoverable_gb': round(recoverable / (1024**3), 4)
    }


def generate_recommendations(duplicate_groups: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Generate keep/delete recommendations for duplicate groups."""
    recommendations = []
    
    for group in duplicate_groups:
        files = group['files']
        
        # Priority: prefer files in organized folders over root/misc
        def path_priority(path: str) -> int:
            path_lower = path.lower()
            if '/01_PHOTOS/' in path or '/02_VIDEOS/' in path:
                return 1
            if '/DCIM/' in path:
                return 2
            if '/PRIVATE/' in path:
                return 3
            if path.startswith('/media/az/drive64gb/'):
                return 4
            return 5
        
        # Sort by priority, then by path length (shorter = cleaner)
        sorted_files = sorted(files, key=lambda f: (path_priority(f['path']), len(f['path'])))
        
        # First file is keep, rest are delete candidates
        keep_file = sorted_files[0]
        for i, file_info in enumerate(sorted_files):
            if i == 0:
                action = 'KEEP'
                reason = 'First in duplicate group (preferred path)'
            else:
                action = 'DELETE'
                reason = f'Duplicate of {keep_file["filename"]}'
            
            recommendations.append({
                'action': action,
                'path': file_info['path'],
                'filename': file_info['filename'],
                'hash': group['hash'],
                'size_bytes': str(group['size']),
                'reason': reason,
                'modified': file_info.get('modified', '')
            })
    
    return recommendations


def generate_html_report(stats: Dict[str, Any], duplicate_groups: List[Dict[str, Any]], 
                         output_path: Path) -> None:
    """Generate HTML report."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Duplicate Detection Report - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 1400px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 12px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .section {{ background: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .section h2 {{ color: #667eea; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #eee; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-card .value {{ font-size: 2.5em; font-weight: bold; color: #667eea; }}
        .stat-card .label {{ color: #666; font-size: 0.9em; margin-top: 5px; }}
        .dup-group {{ background: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #dc3545; }}
        .file-list {{ margin-top: 10px; }}
        .file-item {{ background: white; padding: 10px; margin: 5px 0; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }}
        .file-item.keep {{ border-left: 3px solid #28a745; }}
        .file-item.delete {{ border-left: 3px solid #dc3545; }}
        .file-path {{ font-family: monospace; font-size: 0.85em; color: #555; word-break: break-all; }}
        .file-meta {{ font-size: 0.8em; color: #888; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 600; margin-left: 10px; }}
        .badge-keep {{ background: #d4edda; color: #155724; }}
        .badge-delete {{ background: #f8d7da; color: #721c24; }}
        .badge-size {{ background: #e3f2fd; color: #1976d2; }}
        .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 4px; }}
        .footer {{ text-align: center; color: #666; padding: 20px; font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .hash {{ font-family: monospace; font-size: 0.8em; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔄 Duplicate Detection Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M MST')}</p>
        <p>Source: audit_20260303_233003.csv • Drive: /media/az/drive64gb</p>
    </div>

    <div class="section">
        <h2>📊 Summary</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{stats['total_files']}</div>
                <div class="label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="value">{stats['unique_files']}</div>
                <div class="label">Unique Files</div>
            </div>
            <div class="stat-card">
                <div class="value">{stats['duplicate_groups']}</div>
                <div class="label">Duplicate Groups</div>
            </div>
            <div class="stat-card">
                <div class="value">{stats['duplicate_files']}</div>
                <div class="label">Files in Dup Groups</div>
            </div>
            <div class="stat-card">
                <div class="value">{stats['recoverable_mb']}</div>
                <div class="label">Recoverable (MB)</div>
            </div>
            <div class="stat-card">
                <div class="value">{stats['recoverable_gb']}</div>
                <div class="label">Recoverable (GB)</div>
            </div>
        </div>
        
        <div class="warning">
            <strong>⚠️ Important:</strong> This report never auto-deletes files. Review carefully before taking action.
            Always verify files before deletion and maintain backups.
        </div>
    </div>

    <div class="section">
        <h2>📋 Exact Duplicate Groups</h2>
        <p>Files grouped by SHA256 hash. Green = recommended to KEEP, Red = recommended to DELETE.</p>
"""
    
    for i, group in enumerate(duplicate_groups, 1):
        html += f"""
        <div class="dup-group">
            <strong>Group #{i}</strong> • 
            <strong>Hash:</strong> <span class="hash">{group['hash'][:32]}...</span> • 
            <strong>Copies:</strong> {group['count']} • 
            <strong>Size:</strong> {group['size'] / (1024**2):.2f} MB each •
            <strong>Wasted:</strong> {(group['size'] * (group['count'] - 1)) / (1024**2):.2f} MB
            
            <div class="file-list">
"""
        for j, file_info in enumerate(group['files']):
            badge_class = 'keep' if j == 0 else 'delete'
            badge_text = 'KEEP' if j == 0 else 'DELETE'
            html += f"""
                <div class="file-item {badge_class}">
                    <div>
                        <div class="file-path">{file_info['path']}</div>
                        <div class="file-meta">Modified: {file_info.get('modified', 'N/A')}</div>
                    </div>
                    <div>
                        <span class="badge badge-{badge_class}">{badge_text}</span>
                        <span class="badge badge-size">{int(file_info.get('size_bytes', 0)) / (1024**2):.1f} MB</span>
                    </div>
                </div>
"""
        html += """
            </div>
        </div>
"""
    
    html += f"""
    </div>

    <div class="footer">
        <p>Generated by MediaAuditOrganizer • {datetime.now().strftime('%Y-%m-%d %H:%M MST')}</p>
        <p>Review carefully before taking any action. Always backup before deleting.</p>
    </div>
</body>
</html>
"""
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    logger.info(f"HTML report written to: {output_path}")


def generate_action_plan(recommendations: List[Dict[str, str]], output_path: Path) -> None:
    """Generate CSV action plan."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['keep_path', 'delete_path', 'hash', 'size_bytes', 'reason'])
        
        # Group by hash to create keep/delete pairs
        hash_groups = defaultdict(list)
        for rec in recommendations:
            hash_groups[rec['hash']].append(rec)
        
        for hash_val, items in hash_groups.items():
            keep_item = next((i for i in items if i['action'] == 'KEEP'), None)
            delete_items = [i for i in items if i['action'] == 'DELETE']
            
            if keep_item:
                for del_item in delete_items:
                    writer.writerow([
                        keep_item['path'],
                        del_item['path'],
                        hash_val,
                        keep_item['size_bytes'],
                        del_item['reason']
                    ])
    
    logger.info(f"Action plan written to: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_duplicates.py <audit_csv> [--output-dir <path>]")
        sys.exit(1)
    
    csv_path = Path(sys.argv[1])
    output_dir = Path(__file__).parent.parent / "08_REPORTS"
    
    if '--output-dir' in sys.argv:
        idx = sys.argv.index('--output-dir')
        if idx + 1 < len(sys.argv):
            output_dir = Path(sys.argv[idx + 1])
    
    timestamp = datetime.now().strftime('%Y%m%d')
    
    print(f"\n{'='*80}")
    print("DUPLICATE ANALYSIS - MediaAuditOrganizer")
    print(f"{'='*80}")
    print(f"\nInput: {csv_path}")
    print(f"Output: {output_dir}")
    print(f"Timestamp: {timestamp}\n")
    
    logger.info(f"Starting duplicate analysis: {csv_path}")
    
    # Read audit data
    print("Reading audit CSV...")
    files = read_audit_csv(csv_path)
    
    # Find duplicates
    print("Finding exact duplicates...")
    duplicate_groups = find_exact_duplicates(files)
    
    # Calculate stats
    stats = calculate_stats(files, duplicate_groups)
    
    # Generate recommendations
    print("Generating recommendations...")
    recommendations = generate_recommendations(duplicate_groups)
    
    # Generate reports
    print("Generating HTML report...")
    html_path = output_dir / f"duplicates_{timestamp}.html"
    generate_html_report(stats, duplicate_groups, html_path)
    
    print("Generating action plan CSV...")
    csv_path_out = output_dir / f"duplicates_action_plan_{timestamp}.csv"
    generate_action_plan(recommendations, csv_path_out)
    
    # Print summary
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"\n📊 Total files scanned: {stats['total_files']}")
    print(f"📁 Total size: {stats['total_size_gb']} GB")
    print(f"\n🔄 Exact duplicate groups: {stats['duplicate_groups']}")
    print(f"📄 Files in duplicate groups: {stats['duplicate_files']}")
    print(f"💾 Recoverable space: {stats['recoverable_mb']} MB ({stats['recoverable_gb']} GB)")
    print(f"\n📄 HTML Report: {html_path}")
    print(f"📊 Action Plan: {csv_path_out}")
    print(f"📝 Log: {log_file}")
    print(f"\n{'='*80}")
    print("⚠️  NEVER AUTO-DELETE - Review report before taking action")
    print(f"{'='*80}\n")
    
    logger.info("Duplicate analysis complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
