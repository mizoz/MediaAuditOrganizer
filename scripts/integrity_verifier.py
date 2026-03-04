#!/usr/bin/env python3
"""
integrity_verifier.py — Post-Transfer Integrity Verification

Verifies file integrity after transfer by:
- Comparing hash_before vs hash_after for each operation
- Flagging mismatches for manual review
- Generating HTML integrity report
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class IntegrityVerifier:
    """Verifies integrity of transferred files."""
    
    def __init__(self, manifest_path: Path, reports_dir: Path):
        """
        Initialize verifier.
        
        Args:
            manifest_path: Path to shadow manifest JSON
            reports_dir: Directory for integrity reports
        """
        self.manifest_path = manifest_path
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.manifest = self._load_manifest()
        self.verification_results = []
    
    def _load_manifest(self) -> Dict:
        """Load shadow manifest."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Shadow manifest not found: {self.manifest_path}")
        
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _compute_hash(self, filepath: Path) -> Optional[str]:
        """Compute SHA256 hash of file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except (PermissionError, OSError) as e:
            logger.error(f"Cannot compute hash for {filepath}: {e}")
            return None
    
    def verify_single_file(self, op: Dict) -> Dict:
        """
        Verify integrity of a single file operation.
        
        Returns verification result dict.
        """
        op_id = op.get("operation_id", "UNKNOWN")
        new_path = Path(op.get("new_path", ""))
        hash_before = op.get("hash_before", "")
        hash_after = op.get("hash_after", "")
        status = op.get("status", "unknown")
        
        result = {
            "operation_id": op_id,
            "file_path": str(new_path),
            "filename": new_path.name if new_path else "UNKNOWN",
            "hash_before": hash_before,
            "hash_after": hash_after,
            "current_hash": None,
            "status": status,
            "verified": False,
            "error": "",
            "verified_at": datetime.now().isoformat()
        }
        
        # Skip if not completed
        if status not in ("completed", "rolled_back"):
            result["error"] = f"Operation not completed (status: {status})"
            return result
        
        # Check if file exists
        if not new_path.exists():
            result["error"] = "File does not exist"
            result["verified"] = False
            return result
        
        # Compute current hash
        current_hash = self._compute_hash(new_path)
        result["current_hash"] = current_hash
        
        if not current_hash:
            result["error"] = "Failed to compute current hash"
            return result
        
        # Compare hashes
        # Priority: hash_after > hash_before
        expected_hash = hash_after if hash_after else hash_before
        
        if not expected_hash:
            result["error"] = "No reference hash available"
            result["verified"] = False
            return result
        
        if current_hash == expected_hash:
            result["verified"] = True
            result["status"] = "verified"
        else:
            result["verified"] = False
            result["status"] = "mismatch"
            result["error"] = (
                f"Hash mismatch: expected {expected_hash[:32]}..., "
                f"got {current_hash[:32]}..."
            )
        
        return result
    
    def verify_all(self, filter_status: Optional[str] = None) -> Dict:
        """
        Verify all operations in manifest.
        
        Args:
            filter_status: Only verify operations with this status
        
        Returns:
            Summary dict with verification results
        """
        operations = self.manifest.get("operations", [])
        
        if filter_status:
            operations = [op for op in operations if op.get("status") == filter_status]
        
        logger.info(f"Verifying {len(operations)} operations...")
        
        self.verification_results = []
        stats = {
            "total": len(operations),
            "verified": 0,
            "mismatch": 0,
            "missing": 0,
            "error": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }
        
        for i, op in enumerate(operations, 1):
            if i % 50 == 0:
                logger.info(f"  Progress: {i}/{len(operations)}")
            
            result = self.verify_single_file(op)
            self.verification_results.append(result)
            
            if result["verified"]:
                stats["verified"] += 1
            elif result["error"] == "File does not exist":
                stats["missing"] += 1
            elif result["status"] == "mismatch":
                stats["mismatch"] += 1
            else:
                stats["error"] += 1
        
        stats["end_time"] = datetime.now().isoformat()
        stats["results"] = self.verification_results
        
        logger.info(
            f"Verification complete: {stats['verified']} verified, "
            f"{stats['mismatch']} mismatches, {stats['missing']} missing, "
            f"{stats['error']} errors"
        )
        
        return stats
    
    def generate_html_report(self, stats: Dict, output_path: Optional[Path] = None) -> Path:
        """
        Generate HTML integrity report.
        
        Args:
            stats: Verification statistics from verify_all()
            output_path: Optional custom output path
        
        Returns:
            Path to generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_path is None:
            output_path = self.reports_dir / f"integrity_report_{timestamp}.html"
        
        # Separate results by status
        verified = [r for r in self.verification_results if r["verified"]]
        mismatches = [r for r in self.verification_results if r["status"] == "mismatch"]
        missing = [r for r in self.verification_results if r["error"] == "File does not exist"]
        errors = [r for r in self.verification_results if r["error"] and r["error"] != "File does not exist"]
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Integrity Report - {timestamp}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .verified {{ color: #10b981; }}
        .mismatch {{ color: #ef4444; }}
        .missing {{ color: #f59e0b; }}
        .error {{ color: #6b7280; }}
        .section {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .section h2 {{
            margin-top: 0;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f9fafb;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f9fafb;
        }}
        .hash {{
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #666;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .status-verified {{
            background: #d1fae5;
            color: #065f46;
        }}
        .status-mismatch {{
            background: #fee2e2;
            color: #991b1b;
        }}
        .status-missing {{
            background: #fef3c7;
            color: #92400e;
        }}
        .status-error {{
            background: #e5e7eb;
            color: #374151;
        }}
        .alert {{
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .alert-warning {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
        }}
        .alert-success {{
            background: #d1fae5;
            border-left: 4px solid #10b981;
        }}
        .alert-error {{
            background: #fee2e2;
            border-left: 4px solid #ef4444;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Integrity Verification Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Manifest: {self.manifest_path.name}</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{stats['total']}</div>
            <div class="stat-label">Total Files</div>
        </div>
        <div class="stat-card">
            <div class="stat-value verified">{stats['verified']}</div>
            <div class="stat-label">✅ Verified</div>
        </div>
        <div class="stat-card">
            <div class="stat-value mismatch">{stats['mismatch']}</div>
            <div class="stat-label">❌ Mismatches</div>
        </div>
        <div class="stat-card">
            <div class="stat-value missing">{stats['missing']}</div>
            <div class="stat-label">⚠️ Missing</div>
        </div>
        <div class="stat-card">
            <div class="stat-value error">{stats['error']}</div>
            <div class="stat-label">🔧 Errors</div>
        </div>
    </div>
"""
        
        # Alert section
        if stats['mismatch'] > 0:
            html += f"""
    <div class="alert alert-error">
        <strong>⚠️ ATTENTION REQUIRED:</strong> {stats['mismatch']} file(s) have hash mismatches and need manual review.
    </div>
"""
        elif stats['missing'] > 0:
            html += f"""
    <div class="alert alert-warning">
        <strong>⚠️ WARNING:</strong> {stats['missing']} file(s) are missing from expected location.
    </div>
"""
        else:
            html += f"""
    <div class="alert alert-success">
        <strong>✅ ALL CLEAR:</strong> All {stats['verified']} files verified successfully.
    </div>
"""
        
        # Mismatches section
        if mismatches:
            html += """
    <div class="section">
        <h2>❌ Hash Mismatches (Manual Review Required)</h2>
        <table>
            <thead>
                <tr>
                    <th>Operation ID</th>
                    <th>File</th>
                    <th>Expected Hash</th>
                    <th>Current Hash</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
"""
            for r in mismatches:
                html += f"""
                <tr>
                    <td>{r['operation_id']}</td>
                    <td>{r['filename']}</td>
                    <td class="hash">{r['hash_after'][:32] if r['hash_after'] else r['hash_before'][:32]}...</td>
                    <td class="hash">{r['current_hash'][:32] if r['current_hash'] else 'N/A'}...</td>
                    <td>{r['error'][:100]}</td>
                </tr>
"""
            html += """
            </tbody>
        </table>
    </div>
"""
        
        # Missing files section
        if missing:
            html += """
    <div class="section">
        <h2>⚠️ Missing Files</h2>
        <table>
            <thead>
                <tr>
                    <th>Operation ID</th>
                    <th>Expected Path</th>
                    <th>Filename</th>
                </tr>
            </thead>
            <tbody>
"""
            for r in missing[:50]:  # Limit to 50
                html += f"""
                <tr>
                    <td>{r['operation_id']}</td>
                    <td class="hash">{r['file_path'][:80]}...</td>
                    <td>{r['filename']}</td>
                </tr>
"""
            if len(missing) > 50:
                html += f"""
                <tr>
                    <td colspan="3"><em>... and {len(missing) - 50} more</em></td>
                </tr>
"""
            html += """
            </tbody>
        </table>
    </div>
"""
        
        # Verified files section (collapsible in a real app, but simplified here)
        if verified:
            html += f"""
    <div class="section">
        <h2>✅ Verified Files ({len(verified)} files)</h2>
        <p><em>Showing first 20 verified files</em></p>
        <table>
            <thead>
                <tr>
                    <th>Operation ID</th>
                    <th>File</th>
                    <th>Hash</th>
                </tr>
            </thead>
            <tbody>
"""
            for r in verified[:20]:
                html += f"""
                <tr>
                    <td>{r['operation_id']}</td>
                    <td>{r['filename']}</td>
                    <td class="hash">{r['current_hash'][:32] if r['current_hash'] else 'N/A'}...</td>
                </tr>
"""
            if len(verified) > 20:
                html += f"""
                <tr>
                    <td colspan="3"><em>... and {len(verified) - 20} more</em></td>
                </tr>
"""
            html += """
            </tbody>
        </table>
    </div>
"""
        
        html += f"""
    <div class="footer">
        <p>Report generated by IntegrityVerifier v1.0</p>
        <p>Manifest: {self.manifest_path}</p>
    </div>
</body>
</html>
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"📊 HTML report generated: {output_path}")
        return output_path
    
    def get_mismatches(self) -> List[Dict]:
        """Get list of files with hash mismatches."""
        return [r for r in self.verification_results if r["status"] == "mismatch"]
    
    def get_missing(self) -> List[Dict]:
        """Get list of missing files."""
        return [r for r in self.verification_results if r["error"] == "File does not exist"]


def verify_integrity(
    manifest_path: Path,
    reports_dir: Path,
    generate_report: bool = True
) -> Dict:
    """Quick integrity verification."""
    verifier = IntegrityVerifier(manifest_path, reports_dir)
    stats = verifier.verify_all()
    
    if generate_report:
        report_path = verifier.generate_html_report(stats)
        stats["report_path"] = str(report_path)
    
    return stats


if __name__ == "__main__":
    import argparse
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    parser = argparse.ArgumentParser(description="Verify file transfer integrity")
    parser.add_argument("manifest", type=Path, help="Path to shadow manifest JSON")
    parser.add_argument("--reports-dir", type=Path, default=Path("08_REPORTS"), help="Reports directory")
    parser.add_argument("--no-report", action="store_true", help="Skip HTML report generation")
    parser.add_argument("--status", type=str, help="Only verify operations with this status")
    
    args = parser.parse_args()
    
    verifier = IntegrityVerifier(args.manifest, args.reports_dir)
    stats = verifier.verify_all(filter_status=args.status)
    
    if not args.no_report:
        report_path = verifier.generate_html_report(stats)
        print(f"\n📊 Report: {report_path}")
    
    print(f"\n{'='*80}")
    print("INTEGRITY VERIFICATION SUMMARY")
    print(f"{'='*80}")
    print(f"Total files: {stats['total']}")
    print(f"✅ Verified: {stats['verified']}")
    print(f"❌ Mismatches: {stats['mismatch']}")
    print(f"⚠️  Missing: {stats['missing']}")
    print(f"🔧 Errors: {stats['error']}")
    
    if stats['mismatch'] > 0:
        print(f"\n⚠️  ATTENTION: {stats['mismatch']} files need manual review!")
        mismatches = verifier.get_mismatches()
        for m in mismatches[:5]:
            print(f"  - {m['filename']}: {m['error'][:60]}")
    
    sys.exit(0 if stats['mismatch'] == 0 else 1)
