#!/usr/bin/env python3
"""
generate_report.py — HTML Report Generator

Reads audit CSV/JSON data and generates professional HTML reports with:
- Project name and totals
- Chart.js pie chart (file types distribution)
- Timeline chart (files over time)
- Largest files table
- Files without metadata
- Duplicate groups
- Searchable file manifest

Saves timestamped reports to reports/ directory.

Usage:
    python generate_report.py /path/to/audit.json [--project-name "My Project"]
"""

import argparse
import csv
import json
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# HTML Template with embedded Chart.js
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ project_name }} - Media Audit Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 1400px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 12px; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .section { background: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .section h2 { color: #667eea; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #eee; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 8px; text-align: center; }
        .stat-card .value { font-size: 2.5em; font-weight: bold; color: #667eea; }
        .stat-card .label { color: #666; font-size: 0.9em; margin-top: 5px; }
        .chart-container { position: relative; height: 400px; margin: 20px 0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; color: #555; }
        tr:hover { background: #f8f9fa; }
        .search-box { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 1em; margin-bottom: 20px; }
        .search-box:focus { outline: none; border-color: #667eea; }
        .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; border-radius: 4px; }
        .success { background: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 15px 0; border-radius: 4px; }
        .duplicate-group { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #dc3545; }
        .footer { text-align: center; color: #666; padding: 20px; font-size: 0.9em; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: 600; }
        .badge-image { background: #e3f2fd; color: #1976d2; }
        .badge-video { background: #fce4ec; color: #c2185b; }
        .badge-other { background: #f3e5f5; color: #7b1fa2; }
        .progress-bar { background: #e0e0e0; border-radius: 10px; height: 20px; overflow: hidden; margin: 10px 0; }
        .progress-fill { background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; transition: width 0.3s; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 {{ project_name }}</h1>
        <p>Media Audit Report • Generated {{ generated_date }}</p>
        <p>Source: {{ source_path }}</p>
    </div>

    <div class="section">
        <h2>📈 Summary Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{{ total_files }}</div>
                <div class="label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ total_size_gb }} GB</div>
                <div class="label">Total Size</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ image_count }}</div>
                <div class="label">Images</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ video_count }}</div>
                <div class="label">Videos</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ no_metadata_count }}</div>
                <div class="label">No Metadata</div>
            </div>
            <div class="stat-card">
                <div class="value">{{ duplicate_groups }}</div>
                <div class="label">Duplicate Groups</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>🥧 File Type Distribution</h2>
        <div class="chart-container">
            <canvas id="fileTypeChart"></canvas>
        </div>
    </div>

    <div class="section">
        <h2>📅 Timeline (Files by Month)</h2>
        <div class="chart-container">
            <canvas id="timelineChart"></canvas>
        </div>
    </div>

    {% if largest_files %}
    <div class="section">
        <h2>💾 Largest Files</h2>
        <table>
            <thead>
                <tr>
                    <th>Filename</th>
                    <th>Path</th>
                    <th>Size</th>
                    <th>Type</th>
                </tr>
            </thead>
            <tbody>
                {% for file in largest_files %}
                <tr>
                    <td>{{ file.filename }}</td>
                    <td title="{{ file.path }}">{{ file.path|truncate(60) }}</td>
                    <td>{{ file.size_gb }} GB</td>
                    <td><span class="badge badge-{{ file.badge }}">{{ file.file_type }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}

    {% if no_metadata_files %}
    <div class="section">
        <h2>⚠️ Files Without Metadata</h2>
        <div class="warning">
            <strong>{{ no_metadata_count }} files</strong> are missing EXIF/video metadata. These may need manual review.
        </div>
        <table>
            <thead>
                <tr>
                    <th>Filename</th>
                    <th>Path</th>
                    <th>Type</th>
                    <th>Modified</th>
                </tr>
            </thead>
            <tbody>
                {% for file in no_metadata_files %}
                <tr>
                    <td>{{ file.filename }}</td>
                    <td title="{{ file.path }}">{{ file.path|truncate(60) }}</td>
                    <td>{{ file.file_type }}</td>
                    <td>{{ file.modified }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}

    {% if duplicate_groups %}
    <div class="section">
        <h2>🔄 Duplicate Groups</h2>
        <div class="warning">
            <strong>{{ duplicate_groups }} groups</strong> of exact duplicates found (same SHA256 hash).
            Potential space savings: {{ duplicate_space_gb }} GB
        </div>
        {% for group in duplicate_groups %}
        <div class="duplicate-group">
            <strong>Hash:</strong> {{ group.hash[:16] }}... • 
            <strong>Copies:</strong> {{ group.count }} • 
            <strong>Size Each:</strong> {{ group.size_mb }} MB
            <ul style="margin-top: 10px; padding-left: 20px;">
                {% for file in group.files %}
                <li>{{ file }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="section">
        <h2>🔍 File Manifest (Searchable)</h2>
        <input type="text" class="search-box" id="fileSearch" placeholder="Search files by name, path, type, or camera...">
        <table id="fileManifest">
            <thead>
                <tr>
                    <th>Filename</th>
                    <th>Path</th>
                    <th>Size</th>
                    <th>Type</th>
                    <th>Camera</th>
                    <th>Date Taken</th>
                    <th>SHA256</th>
                </tr>
            </thead>
            <tbody>
                {% for file in all_files %}
                <tr>
                    <td>{{ file.filename }}</td>
                    <td title="{{ file.path }}">{{ file.path|truncate(50) }}</td>
                    <td>{{ file.size_mb }} MB</td>
                    <td><span class="badge badge-{{ file.badge }}">{{ file.file_type }}</span></td>
                    <td>{{ file.camera_model or '-' }}</td>
                    <td>{{ file.date_taken or '-' }}</td>
                    <td title="{{ file.sha256 }}">{{ file.sha256[:16] }}...</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="footer">
        <p>Generated by MediaAuditOrganizer • {{ generated_date }}</p>
    </div>

    <script>
        // File Type Pie Chart
        const fileTypeCtx = document.getElementById('fileTypeChart').getContext('2d');
        new Chart(fileTypeCtx, {
            type: 'pie',
            data: {
                labels: {{ file_type_labels|tojson }},
                datasets: [{
                    data: {{ file_type_data|tojson }},
                    backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe', '#43e97b', '#38f9d7']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed + ' files';
                            }
                        }
                    }
                }
            }
        });

        // Timeline Chart
        const timelineCtx = document.getElementById('timelineChart').getContext('2d');
        new Chart(timelineCtx, {
            type: 'bar',
            data: {
                labels: {{ timeline_labels|tojson }},
                datasets: [{
                    label: 'Files',
                    data: {{ timeline_data|tojson }},
                    backgroundColor: 'rgba(102, 126, 234, 0.7)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        // Search functionality
        document.getElementById('fileSearch').addEventListener('input', function(e) {
            const term = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#fileManifest tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    </script>
</body>
</html>
"""


def load_audit_data(input_path: Path) -> Dict[str, Any]:
    """Load audit data from JSON or CSV file."""
    if input_path.suffix == ".json":
        with open(input_path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif input_path.suffix == ".csv":
        records = []
        with open(input_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        return {"file_records": records}
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")


def process_audit_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process audit data and generate report statistics."""
    file_records = data.get("file_records", [])
    
    if not file_records:
        logger.warning("No file records found in audit data")
        return {}
    
    # Basic statistics
    total_files = len(file_records)
    total_size = sum(int(r.get("size_bytes", 0)) for r in file_records)
    
    # File type distribution
    file_types = defaultdict(int)
    for r in file_records:
        ft = r.get("file_type", "OTHER")
        file_types[ft] += 1
    
    # Timeline (files by month)
    timeline = defaultdict(int)
    for r in file_records:
        date_taken = r.get("date_taken") or r.get("created") or r.get("modified")
        if date_taken:
            try:
                # Parse various date formats
                if "T" in date_taken:
                    dt = datetime.fromisoformat(date_taken.replace("Z", "+00:00"))
                else:
                    dt = datetime.strptime(date_taken[:10], "%Y-%m-%d")
                month_key = dt.strftime("%Y-%m")
                timeline[month_key] += 1
            except (ValueError, TypeError):
                pass
    
    # Largest files
    sorted_by_size = sorted(file_records, key=lambda x: int(x.get("size_bytes", 0)), reverse=True)
    largest_files = []
    for r in sorted_by_size[:20]:
        size_gb = int(r.get("size_bytes", 0)) / (1024**3)
        badge = "image" if r.get("file_type") == "IMAGE" else "video" if r.get("file_type") == "VIDEO" else "other"
        largest_files.append({
            "filename": r.get("filename", ""),
            "path": r.get("path", ""),
            "size_gb": f"{size_gb:.3f}",
            "file_type": r.get("file_type", "OTHER"),
            "badge": badge
        })
    
    # Files without metadata
    no_metadata = []
    for r in file_records:
        has_exif = any([
            r.get("date_taken"),
            r.get("camera_make"),
            r.get("camera_model")
        ])
        has_video = any([
            r.get("duration"),
            r.get("codec"),
            r.get("fps")
        ])
        
        if r.get("file_type") == "IMAGE" and not has_exif:
            no_metadata.append(r)
        elif r.get("file_type") == "VIDEO" and not has_video:
            no_metadata.append(r)
    
    no_metadata_files = []
    for r in no_metadata[:50]:  # Limit to 50
        no_metadata_files.append({
            "filename": r.get("filename", ""),
            "path": r.get("path", ""),
            "file_type": r.get("file_type", "OTHER"),
            "modified": r.get("modified", "")
        })
    
    # Duplicate groups (by SHA256)
    hash_groups = defaultdict(list)
    for r in file_records:
        sha256 = r.get("sha256")
        if sha256:
            hash_groups[sha256].append(r)
    
    duplicate_groups_data = []
    duplicate_space = 0
    for sha256, files in hash_groups.items():
        if len(files) > 1:
            size_mb = int(files[0].get("size_bytes", 0)) / (1024**2)
            duplicate_space += size_mb * (len(files) - 1)
            duplicate_groups_data.append({
                "hash": sha256,
                "count": len(files),
                "size_mb": f"{size_mb:.2f}",
                "files": [f.get("path", "") for f in files]
            })
    
    duplicate_groups_data.sort(key=lambda x: x["count"], reverse=True)
    
    # All files for manifest
    all_files = []
    for r in file_records:
        size_mb = int(r.get("size_bytes", 0)) / (1024**2)
        badge = "image" if r.get("file_type") == "IMAGE" else "video" if r.get("file_type") == "VIDEO" else "other"
        all_files.append({
            "filename": r.get("filename", ""),
            "path": r.get("path", ""),
            "size_mb": f"{size_mb:.2f}",
            "file_type": r.get("file_type", "OTHER"),
            "badge": badge,
            "camera_model": r.get("camera_model") or r.get("Make"),
            "date_taken": r.get("date_taken"),
            "sha256": r.get("sha256", "")
        })
    
    return {
        "total_files": total_files,
        "total_size_gb": f"{total_size / (1024**3):.2f}",
        "image_count": file_types.get("IMAGE", 0),
        "video_count": file_types.get("VIDEO", 0),
        "no_metadata_count": len(no_metadata),
        "duplicate_groups": len(duplicate_groups_data),
        "duplicate_space_gb": f"{duplicate_space / 1024:.2f}",
        "file_types": dict(file_types),
        "timeline": dict(sorted(timeline.items())),
        "largest_files": largest_files,
        "no_metadata_files": no_metadata_files,
        "duplicate_groups_data": duplicate_groups_data[:20],  # Limit to 20 groups
        "all_files": all_files
    }


def generate_html_report(processed: Dict[str, Any], project_name: str, source_path: str, output_path: Path) -> None:
    """Generate HTML report from processed data."""
    try:
        from jinja2 import Environment
    except ImportError:
        logger.error("Jinja2 not installed. Install with: pip install jinja2")
        # Fallback to simple string replacement
        html = HTML_TEMPLATE
        html = html.replace("{{ project_name }}", project_name)
        html = html.replace("{{ generated_date }}", datetime.now().strftime("%Y-%m-%d %H:%M MST"))
        html = html.replace("{{ source_path }}", source_path)
        html = html.replace("{{ total_files }}", str(processed.get("total_files", 0)))
        html = html.replace("{{ total_size_gb }}", processed.get("total_size_gb", "0"))
        html = html.replace("{{ image_count }}", str(processed.get("image_count", 0)))
        html = html.replace("{{ video_count }}", str(processed.get("video_count", 0)))
        html = html.replace("{{ no_metadata_count }}", str(processed.get("no_metadata_count", 0)))
        html = html.replace("{{ duplicate_groups }}", str(processed.get("duplicate_groups", 0)))
    else:
        env = Environment()
        env.filters["truncate"] = lambda s, length: s[:length] + "..." if len(s) > length else s
        template = env.from_string(HTML_TEMPLATE)
        
        html = template.render(
            project_name=project_name,
            generated_date=datetime.now().strftime("%Y-%m-%d %H:%M MST"),
            source_path=source_path,
            **processed,
            file_type_labels=list(processed.get("file_types", {}).keys()),
            file_type_data=list(processed.get("file_types", {}).values()),
            timeline_labels=list(processed.get("timeline", {}).keys()),
            timeline_data=list(processed.get("timeline", {}).values())
        )
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    logger.info(f"HTML report written: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate HTML report from audit data"
    )
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to audit JSON or CSV file"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "reports",
        help="Output directory for reports (default: ./reports/)"
    )
    parser.add_argument(
        "--project-name",
        type=str,
        default="Media Library Audit",
        help="Project name for the report"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input
    if not args.input_path.exists():
        logger.error(f"Input file does not exist: {args.input_path}")
        sys.exit(1)
    
    try:
        print(f"\n{'='*80}")
        print("GENERATING REPORT")
        print(f"{'='*80}")
        print(f"Input: {args.input_path}")
        print(f"Output: {args.output_dir}")
        print(f"{'='*80}\n")
        
        # Load data
        logger.info("Loading audit data...")
        data = load_audit_data(args.input_path)
        
        # Process data
        logger.info("Processing audit data...")
        processed = process_audit_data(data)
        
        if not processed:
            logger.error("Failed to process audit data")
            sys.exit(1)
        
        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = args.output_dir / f"report_{timestamp}.html"
        
        logger.info("Generating HTML report...")
        generate_html_report(
            processed,
            args.project_name,
            str(args.input_path),
            output_path
        )
        
        # Print summary
        print(f"\n{'='*80}")
        print("REPORT SUMMARY")
        print(f"{'='*80}")
        print(f"📁 Total Files: {processed['total_files']:,}")
        print(f"💾 Total Size: {processed['total_size_gb']} GB")
        print(f"📸 Images: {processed['image_count']:,}")
        print(f"🎥 Videos: {processed['video_count']:,}")
        print(f"⚠️  No Metadata: {processed['no_metadata_count']}")
        print(f"🔄 Duplicate Groups: {processed['duplicate_groups']}")
        print(f"💰 Potential Space Savings: {processed['duplicate_space_gb']} GB")
        print(f"\n✅ Report saved to: {output_path}")
        print(f"{'='*80}\n")
        
        logger.info("Report generation completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Report generation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
