#!/usr/bin/env python3
"""
preflight_check.py — Disk Space Validation for File Transfers

Validates that target drive has sufficient space before initiating file transfers.
Accounts for:
- Original file data
- JSON sidecar files
- Temporary cache (hashing, thumbnails)
- Safety margin (default 150%)

Usage:
    python preflight_check.py /target/path --required-gb 5.55 --safety-margin 1.5
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "07_LOGS"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"preflight_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_drive_info(path: Path) -> Dict:
    """Get drive information including model, filesystem, and mount point."""
    info = {
        "mount_point": "",
        "filesystem": "",
        "device": "",
        "model": "Unknown",
        "total_gb": 0.0,
        "used_gb": 0.0,
        "available_gb": 0.0,
        "use_percent": 0.0
    }
    
    try:
        # Get mount point
        result = subprocess.run(
            ["findmnt", "-n", "-o", "SOURCE,TARGET,FSTYPE", str(path)],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split()
            if len(parts) >= 3:
                info["device"] = parts[0]
                info["mount_point"] = parts[1]
                info["filesystem"] = parts[2]
    except Exception as e:
        logger.debug(f"findmnt failed: {e}")
    
    # Fallback: use df for filesystem info
    if not info["filesystem"]:
        try:
            result = subprocess.run(
                ["df", "-T", str(path)],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 7:
                        info["device"] = parts[0]
                        info["filesystem"] = parts[1]
        except Exception as e:
            logger.debug(f"df failed: {e}")
    
    # Get disk usage stats
    try:
        total, used, free = shutil.disk_usage(str(path))
        info["total_gb"] = total / (1024**3)
        info["used_gb"] = used / (1024**3)
        info["available_gb"] = free / (1024**3)
        info["use_percent"] = (used / total) * 100 if total > 0 else 0
    except Exception as e:
        logger.error(f"Cannot get disk usage: {e}")
        raise
    
    # Try to get drive model from smartctl or hdparm
    if info["device"] and info["device"].startswith("/dev/"):
        try:
            # Try smartctl first
            result = subprocess.run(
                ["smartctl", "-i", info["device"]],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "Device Model:" in line or "Model Number:" in line:
                        info["model"] = line.split(":", 1)[1].strip()
                        break
        except Exception:
            pass
        
        # Fallback to hdparm if smartctl didn't work
        if info["model"] == "Unknown":
            try:
                result = subprocess.run(
                    ["hdparm", "-I", info["device"]],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    for line in result.stdout.split("\n"):
                        if "Model Number:" in line:
                            info["model"] = line.split(":", 1)[1].strip()
                            break
            except Exception:
                pass
    
    # Get SMART status if available
    info["smart_status"] = "Unknown"
    if info["device"] and info["device"].startswith("/dev/"):
        try:
            result = subprocess.run(
                ["smartctl", "-H", info["device"]],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                if "PASSED" in result.stdout:
                    info["smart_status"] = "PASSED"
                elif "FAILED" in result.stdout:
                    info["smart_status"] = "FAILED"
        except Exception:
            pass
    
    return info


def check_disk_space(
    target_path: Path,
    required_gb: float,
    safety_margin: float = 1.5
) -> Dict:
    """
    Check if target path has sufficient disk space.
    
    Args:
        target_path: Path to check
        required_gb: Required space in GB (before safety margin)
        safety_margin: Safety margin multiplier (default 1.5 = 150%)
    
    Returns:
        Dict with:
            - pass: bool (True if sufficient space)
            - available_gb: float (available space)
            - required_gb: float (required space with margin)
            - margin_pct: float (safety margin percentage)
            - drive_info: Dict (drive details)
            - timestamp: str (ISO format)
    """
    logger.info(f"Checking disk space for: {target_path}")
    logger.info(f"Required space: {required_gb:.2f} GB (before margin)")
    logger.info(f"Safety margin: {safety_margin}x ({safety_margin * 100:.0f}%)")
    
    # Get available space
    try:
        total, used, free = shutil.disk_usage(str(target_path))
        available_gb = free / (1024**3)
    except Exception as e:
        logger.error(f"Cannot get disk usage: {e}")
        return {
            "pass": False,
            "available_gb": 0.0,
            "required_gb": required_gb * safety_margin,
            "margin_pct": safety_margin * 100,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    
    # Calculate required space with margin
    required_with_margin = required_gb * safety_margin
    
    # Get drive info
    drive_info = get_drive_info(target_path)
    
    # Determine pass/fail
    passed = available_gb >= required_with_margin
    
    result = {
        "pass": passed,
        "available_gb": round(available_gb, 2),
        "required_gb": round(required_with_margin, 2),
        "required_base_gb": round(required_gb, 2),
        "margin_pct": round(safety_margin * 100, 0),
        "surplus_gb": round(available_gb - required_with_margin, 2),
        "drive_info": drive_info,
        "timestamp": datetime.now().isoformat(),
        "target_path": str(target_path)
    }
    
    # Log result
    if passed:
        logger.info(f"✅ PREFLIGHT PASS: {available_gb:.2f} GB available, {required_with_margin:.2f} GB required")
        logger.info(f"   Surplus: {result['surplus_gb']:.2f} GB")
    else:
        deficit = required_with_margin - available_gb
        logger.error(f"❌ PREFLIGHT FAIL: {available_gb:.2f} GB available, {required_with_margin:.2f} GB required")
        logger.error(f"   Deficit: {deficit:.2f} GB")
        result["deficit_gb"] = round(deficit, 2)
    
    return result


def write_report(result: Dict, report_dir: Path) -> Path:
    """Write preflight report to JSON file."""
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    report_path = report_dir / f"preflight_{timestamp}.json"
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    
    logger.info(f"Report written to: {report_path}")
    return report_path


def generate_dashboard_html(result: Dict, report_dir: Path) -> Path:
    """Generate HTML dashboard with visual gauge."""
    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    html_path = report_dir / f"capacity_status_{timestamp}.html"
    
    passed = result.get("pass", False)
    available = result.get("available_gb", 0)
    required = result.get("required_gb", 0)
    surplus = result.get("surplus_gb", 0)
    deficit = result.get("deficit_gb", 0)
    drive_info = result.get("drive_info", {})
    
    # Calculate gauge percentage
    if required > 0:
        gauge_pct = min(100, (available / required) * 100)
    else:
        gauge_pct = 0
    
    # Color based on pass/fail
    status_color = "#22c55e" if passed else "#ef4444"  # green-500 or red-500
    status_text = "PASS" if passed else "FAIL"
    gauge_color = status_color
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Capacity Status Dashboard - {timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }}
        .dashboard {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 24px;
            padding: 3rem;
            max-width: 800px;
            width: 100%;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 3rem;
        }}
        .header h1 {{
            color: #f8fafc;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        .header p {{
            color: #94a3b8;
            font-size: 0.95rem;
        }}
        .status-badge {{
            display: inline-block;
            padding: 0.5rem 2rem;
            border-radius: 9999px;
            font-size: 1.5rem;
            font-weight: 700;
            background: {status_color}22;
            color: {status_color};
            border: 2px solid {status_color};
            margin: 1rem 0;
        }}
        .gauge-container {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        .gauge {{
            position: relative;
            height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .gauge-bg {{
            position: absolute;
            width: 180px;
            height: 180px;
            border-radius: 50%;
            background: conic-gradient(
                {gauge_color} {gauge_pct}%,
                rgba(255, 255, 255, 0.1) {gauge_pct}%
            );
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .gauge-inner {{
            width: 140px;
            height: 140px;
            border-radius: 50%;
            background: #1e293b;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .gauge-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #f8fafc;
        }}
        .gauge-label {{
            font-size: 0.85rem;
            color: #94a3b8;
            margin-top: 0.25rem;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .metric-card {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
        }}
        .metric-value {{
            font-size: 1.75rem;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 0.5rem;
        }}
        .metric-label {{
            font-size: 0.85rem;
            color: #94a3b8;
        }}
        .drive-info {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 12px;
            padding: 1.5rem;
        }}
        .drive-info h3 {{
            color: #f8fafc;
            font-size: 1.1rem;
            margin-bottom: 1rem;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.75rem;
        }}
        .info-item {{
            display: flex;
            flex-direction: column;
        }}
        .info-label {{
            font-size: 0.75rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .info-value {{
            font-size: 0.95rem;
            color: #e2e8f0;
            font-weight: 500;
        }}
        .footer {{
            text-align: center;
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .footer p {{
            color: #64748b;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>📊 Capacity Status Dashboard</h1>
            <p>Preflight Check for Media Audit Organizer Transfer</p>
            <div class="status-badge">{status_text}</div>
        </div>
        
        <div class="gauge-container">
            <div class="gauge">
                <div class="gauge-bg">
                    <div class="gauge-inner">
                        <div class="gauge-value">{gauge_pct:.0f}%</div>
                        <div class="gauge-label">Capacity</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value" style="color: #22c55e;">{available:.2f} GB</div>
                <div class="metric-label">Available Space</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: #f59e0b;">{required:.2f} GB</div>
                <div class="metric-label">Required (with margin)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" style="color: {'#22c55e' if surplus >= 0 else '#ef4444'};">
                    {'+' if surplus >= 0 else ''}{surplus if surplus >= 0 else -deficit:.2f} GB
                </div>
                <div class="metric-label">{'Surplus' if surplus >= 0 else 'Deficit'}</div>
            </div>
        </div>
        
        <div class="drive-info">
            <h3>💾 Target Drive Information</h3>
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Device</span>
                    <span class="info-value">{drive_info.get('device', 'N/A')}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Model</span>
                    <span class="info-value">{drive_info.get('model', 'Unknown')}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Filesystem</span>
                    <span class="info-value">{drive_info.get('filesystem', 'N/A')}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Mount Point</span>
                    <span class="info-value">{drive_info.get('mount_point', 'N/A')}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Total Capacity</span>
                    <span class="info-value">{drive_info.get('total_gb', 0):.0f} GB</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Usage</span>
                    <span class="info-value">{drive_info.get('use_percent', 0):.1f}%</span>
                </div>
                <div class="info-item">
                    <span class="info-label">SMART Status</span>
                    <span class="info-value">{drive_info.get('smart_status', 'Unknown')}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Safety Margin</span>
                    <span class="info-value">{result.get('margin_pct', 150):.0f}%</span>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated: {result.get('timestamp', datetime.now().isoformat())}</p>
            <p>Target Path: {result.get('target_path', 'N/A')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    logger.info(f"Dashboard written to: {html_path}")
    return html_path


def main():
    parser = argparse.ArgumentParser(
        description="Preflight disk space check for file transfers"
    )
    parser.add_argument(
        "target_path",
        type=Path,
        help="Target directory path to check"
    )
    parser.add_argument(
        "--required-gb",
        type=float,
        required=True,
        help="Required space in GB (before safety margin)"
    )
    parser.add_argument(
        "--safety-margin",
        type=float,
        default=1.5,
        help="Safety margin multiplier (default: 1.5 = 150%%)"
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path(__file__).parent.parent / "08_REPORTS",
        help="Output directory for reports (default: ./08_REPORTS/)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate target path
    if not args.target_path.exists():
        logger.info(f"Target path does not exist, creating: {args.target_path}")
        try:
            args.target_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Cannot create target path: {e}")
            sys.exit(1)
    
    # Run preflight check
    result = check_disk_space(
        args.target_path,
        args.required_gb,
        args.safety_margin
    )
    
    # Write reports
    write_report(result, args.report_dir)
    generate_dashboard_html(result, args.report_dir)
    
    # Print summary
    print(f"\n{'='*80}")
    print("PREFLIGHT CHECK RESULT")
    print(f"{'='*80}")
    print(f"Status: {'✅ PASS' if result['pass'] else '❌ FAIL'}")
    print(f"Available Space: {result['available_gb']:.2f} GB")
    print(f"Required Space: {result['required_gb']:.2f} GB (including {result['margin_pct']:.0f}% safety margin)")
    
    if result['pass']:
        print(f"Surplus: {result['surplus_gb']:.2f} GB")
    else:
        print(f"Deficit: {result['deficit_gb']:.2f} GB")
        print(f"\n⚠️  CRITICAL: Insufficient space. Do not proceed with transfer.")
    
    drive_info = result.get('drive_info', {})
    print(f"\nTarget Drive:")
    print(f"  Device: {drive_info.get('device', 'N/A')}")
    print(f"  Model: {drive_info.get('model', 'Unknown')}")
    print(f"  Filesystem: {drive_info.get('filesystem', 'N/A')}")
    print(f"  Mount Point: {drive_info.get('mount_point', 'N/A')}")
    print(f"{'='*80}\n")
    
    # Exit with appropriate code
    sys.exit(0 if result['pass'] else 1)


if __name__ == "__main__":
    main()
