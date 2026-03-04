#!/usr/bin/env python3
"""
rollback_engine.py — Rollback System for File Operations

Provides ability to undo last N operations by:
- Restoring original filenames from shadow manifest
- Verifying hash matches original (ensuring no corruption)
- Logging all rollback operations
"""

import csv
import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RollbackEngine:
    """Manages rollback operations for file transfers."""
    
    def __init__(
        self,
        manifest_path: Path,
        log_dir: Path,
        backup_dir: Optional[Path] = None
    ):
        """
        Initialize rollback engine.
        
        Args:
            manifest_path: Path to shadow manifest JSON
            log_dir: Directory for rollback logs
            backup_dir: Optional directory for backup copies during rollback
        """
        self.manifest_path = manifest_path
        self.log_dir = log_dir
        self.backup_dir = backup_dir or (log_dir / "rollback_backups")
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.manifest = self._load_manifest()
        self.rollback_log = []
    
    def _load_manifest(self) -> Dict:
        """Load shadow manifest."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Shadow manifest not found: {self.manifest_path}")
        
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_manifest(self) -> None:
        """Save updated manifest."""
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2)
    
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
    
    def _log_rollback(self, message: str, level: str = "INFO") -> None:
        """Log rollback operation."""
        timestamp = datetime.now().isoformat()
        self.rollback_log.append({
            "timestamp": timestamp,
            "level": level,
            "message": message
        })
        logger.log(getattr(logging, level), message)
    
    def _save_rollback_log(self, rollback_id: str) -> Path:
        """Save rollback log to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = self.log_dir / f"rollback_{rollback_id}_{timestamp}.log"
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(self.rollback_log, f, indent=2)
        
        # Also create human-readable version
        txt_path = self.log_dir / f"rollback_{rollback_id}_{timestamp}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"ROLLBACK LOG - {rollback_id}\n")
            f.write(f"Generated: {timestamp}\n")
            f.write("=" * 80 + "\n\n")
            for entry in self.rollback_log:
                f.write(f"[{entry['timestamp']}] {entry['level']}: {entry['message']}\n")
        
        self.rollback_log = []  # Clear after saving
        return log_path
    
    def get_completed_operations(self) -> List[Dict]:
        """Get list of completed operations from manifest."""
        return [
            op for op in self.manifest.get("operations", [])
            if op.get("status") == "completed"
        ]
    
    def get_last_n_operations(self, n: int = 50) -> List[Dict]:
        """Get last N completed operations."""
        completed = self.get_completed_operations()
        # Sort by timestamp descending
        completed.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return completed[:n]
    
    def undo_last_n(
        self,
        n: int = 50,
        verify_hash: bool = True,
        dry_run: bool = False
    ) -> Dict:
        """
        Undo last N operations.
        
        Args:
            n: Number of operations to rollback
            verify_hash: Verify hash before rollback
            dry_run: Show what would be done without doing it
        
        Returns:
            Dict with rollback results
        """
        rollback_id = f"RB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._log_rollback(f"Starting rollback of last {n} operations", "INFO")
        
        operations = self.get_last_n_operations(n)
        
        if not operations:
            self._log_rollback("No completed operations to rollback", "WARNING")
            return {
                "rollback_id": rollback_id,
                "success": False,
                "message": "No completed operations to rollback",
                "operations_rolled_back": 0,
                "operations_failed": 0
            }
        
        results = {
            "rollback_id": rollback_id,
            "success": True,
            "operations_rolled_back": 0,
            "operations_failed": 0,
            "details": []
        }
        
        for op in operations:
            op_id = op.get("operation_id", "UNKNOWN")
            original_path = Path(op.get("original_path", ""))
            new_path = Path(op.get("new_path", ""))
            hash_before = op.get("hash_before", "")
            
            self._log_rollback(f"Processing {op_id}: {new_path.name}")
            
            # Check if new file exists
            if not new_path.exists():
                self._log_rollback(f"  ⚠️  New file does not exist: {new_path}", "WARNING")
                results["details"].append({
                    "operation_id": op_id,
                    "status": "skipped",
                    "reason": "New file does not exist"
                })
                continue
            
            # Verify current hash matches hash_after (if we have it)
            hash_after = op.get("hash_after", "")
            if verify_hash and hash_after:
                current_hash = self._compute_hash(new_path)
                if current_hash != hash_after:
                    self._log_rollback(
                        f"  ❌ Hash mismatch! Expected {hash_after[:16]}..., got {current_hash[:16] if current_hash else 'None'}",
                        "ERROR"
                    )
                    results["operations_failed"] += 1
                    results["details"].append({
                        "operation_id": op_id,
                        "status": "failed",
                        "reason": f"Hash mismatch: expected {hash_after[:16]}..., got {current_hash[:16] if current_hash else 'None'}"
                    })
                    results["success"] = False
                    continue
            
            if dry_run:
                self._log_rollback(f"  [DRY RUN] Would restore: {original_path.name}")
                results["details"].append({
                    "operation_id": op_id,
                    "status": "dry_run",
                    "would_restore": str(original_path)
                })
                continue
            
            # Create backup of current file
            backup_path = self.backup_dir / f"{rollback_id}_{new_path.name}"
            try:
                shutil.copy2(new_path, backup_path)
                self._log_rollback(f"  💾 Backed up to: {backup_path.name}")
            except Exception as e:
                self._log_rollback(f"  ⚠️  Backup failed: {e}", "WARNING")
            
            # Restore original path (rename back)
            try:
                original_path.parent.mkdir(parents=True, exist_ok=True)
                
                # If original exists, we need to handle conflict
                if original_path.exists():
                    # Check if it's the same file (already rolled back)
                    if original_path.samefile(new_path):
                        self._log_rollback(f"  ⏭️  Already rolled back", "INFO")
                        results["details"].append({
                            "operation_id": op_id,
                            "status": "already_rolled_back"
                        })
                        continue
                    
                    # Create timestamped backup of existing original
                    conflict_backup = self.backup_dir / f"{rollback_id}_conflict_{original_path.name}"
                    shutil.copy2(original_path, conflict_backup)
                    self._log_rollback(f"  ⚠️  Original exists, backed up to: {conflict_backup.name}", "WARNING")
                
                # Rename new_path back to original_path
                shutil.move(str(new_path), str(original_path))
                
                # Update manifest
                op["status"] = "rolled_back"
                op["rolled_back"] = True
                op["rollback_timestamp"] = datetime.now().isoformat()
                op["rollback_id"] = rollback_id
                
                self._log_rollback(f"  ✅ Restored: {original_path.name}")
                results["operations_rolled_back"] += 1
                results["details"].append({
                    "operation_id": op_id,
                    "status": "rolled_back",
                    "restored_path": str(original_path)
                })
                
            except Exception as e:
                self._log_rollback(f"  ❌ Rollback failed: {e}", "ERROR")
                results["operations_failed"] += 1
                results["success"] = False
                results["details"].append({
                    "operation_id": op_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Save manifest updates
        if not dry_run:
            self._save_manifest()
        
        # Save rollback log
        log_path = self._save_rollback_log(rollback_id)
        results["log_file"] = str(log_path)
        
        # Summary
        self._log_rollback(
            f"Rollback complete: {results['operations_rolled_back']} restored, "
            f"{results['operations_failed']} failed",
            "INFO"
        )
        
        return results
    
    def verify_integrity(self, op: Dict) -> Tuple[bool, str]:
        """
        Verify integrity of a single operation.
        
        Returns:
            Tuple of (is_valid, message)
        """
        new_path = Path(op.get("new_path", ""))
        hash_before = op.get("hash_before", "")
        hash_after = op.get("hash_after", "")
        
        if not new_path.exists():
            return False, "File does not exist"
        
        if not hash_before:
            return False, "No hash_before recorded"
        
        current_hash = self._compute_hash(new_path)
        
        if not current_hash:
            return False, "Cannot compute current hash"
        
        # Check against hash_after if available, otherwise hash_before
        expected_hash = hash_after if hash_after else hash_before
        
        if current_hash == expected_hash:
            return True, f"Hash verified: {current_hash[:16]}..."
        else:
            return False, f"Hash mismatch: expected {expected_hash[:16]}..., got {current_hash[:16]}..."
    
    def get_rollback_candidates(self, max_age_hours: int = 24) -> List[Dict]:
        """Get operations that can be rolled back (within time limit)."""
        completed = self.get_completed_operations()
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        
        candidates = []
        for op in completed:
            try:
                op_time = datetime.fromisoformat(op.get("timestamp", "")).timestamp()
                if op_time >= cutoff:
                    candidates.append(op)
            except (ValueError, TypeError):
                continue
        
        return candidates


def quick_rollback(
    manifest_path: Path,
    log_dir: Path,
    n: int = 50,
    dry_run: bool = False
) -> Dict:
    """Quick rollback of last N operations."""
    engine = RollbackEngine(manifest_path, log_dir)
    return engine.undo_last_n(n, dry_run=dry_run)


if __name__ == "__main__":
    import argparse
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    parser = argparse.ArgumentParser(description="Rollback file transfer operations")
    parser.add_argument("manifest", type=Path, help="Path to shadow manifest JSON")
    parser.add_argument("--n", type=int, default=50, help="Number of operations to rollback")
    parser.add_argument("--log-dir", type=Path, default=Path("07_LOGS"), help="Log directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--no-verify", action="store_true", help="Skip hash verification")
    
    args = parser.parse_args()
    
    engine = RollbackEngine(args.manifest, args.log_dir)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    results = engine.undo_last_n(args.n, verify_hash=not args.no_verify, dry_run=args.dry_run)
    
    print(f"\n{'='*80}")
    print("ROLLBACK RESULTS")
    print(f"{'='*80}")
    print(f"Rollback ID: {results['rollback_id']}")
    print(f"Success: {results['success']}")
    print(f"Operations rolled back: {results['operations_rolled_back']}")
    print(f"Operations failed: {results['operations_failed']}")
    print(f"Log file: {results.get('log_file', 'N/A')}")
    
    if results.get('details'):
        print(f"\nDetails:")
        for detail in results['details'][:10]:
            print(f"  - {detail['operation_id']}: {detail['status']}")
        if len(results['details']) > 10:
            print(f"  ... and {len(results['details']) - 10} more")
    
    sys.exit(0 if results['success'] else 1)
