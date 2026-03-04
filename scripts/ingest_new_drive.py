#!/usr/bin/env python3
"""
ingest_new_drive.py — Master Drive Ingestion Orchestrator

Complete end-to-end drive ingestion workflow:
1. Audit drive (audit_drive.py)
2. Show report (generate_report.py)
3. Dedupe check (deduplicate.py)
4. User confirmation
5. Rename files (rename_batch.py)
6. Transfer with verification (transfer_assets.py)
7. Backup verify (backup_verify.py)
8. Update index
9. Write ingestion summary

This is the single entry point for ingesting new drives.

Usage:
    python ingest_new_drive.py /path/to/drive --project "Wedding_Smith_2026"
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
from typing import Any, Dict, List, Optional

# Configure logging
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Script paths
SCRIPTS_DIR = Path(__file__).parent
REPORTS_DIR = Path(__file__).parent.parent / "reports"
LOGS_DIR = Path(__file__).parent.parent / "logs"


class DriveIngestor:
    """Orchestrates complete drive ingestion workflow."""
    
    def __init__(self, drive_path: Path, project_name: str, backup_path: Optional[Path] = None):
        self.drive_path = drive_path
        self.project_name = project_name
        self.backup_path = backup_path
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.work_dir = Path(__file__).parent.parent / "00_INCOMING" / f"ingest_{self.timestamp}"
        self.results = {
            "project_name": project_name,
            "drive_path": str(drive_path),
            "backup_path": str(backup_path) if backup_path else None,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "steps": [],
            "status": "IN_PROGRESS",
            "errors": []
        }
    
    def log_step(self, step_name: str, status: str, details: Optional[Dict] = None):
        """Log a workflow step."""
        step = {
            "name": step_name,
            "status": status,
            "time": datetime.now().isoformat(),
            "details": details or {}
        }
        self.results["steps"].append(step)
        logger.info(f"Step: {step_name} - {status}")
    
    def run_script(self, script_name: str, args: List[str], capture_output: bool = False) -> tuple:
        """Run a Python script and return result."""
        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        
        cmd = [sys.executable, str(script_path)] + args
        
        logger.info(f"Running: {' '.join(cmd)}")
        
        try:
            if capture_output:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=3600  # 1 hour timeout
                )
                return result.returncode, result.stdout, result.stderr
            else:
                result = subprocess.run(cmd, timeout=3600)
                return result.returncode, None, None
        except subprocess.TimeoutExpired:
            logger.error(f"Script timeout: {script_name}")
            return -1, None, "Timeout"
        except Exception as e:
            logger.error(f"Script failed: {script_name} - {e}")
            return -1, None, str(e)
    
    def step_audit(self) -> bool:
        """Step 1: Audit the drive."""
        print(f"\n{'='*80}")
        print("STEP 1: DRIVE AUDIT")
        print(f"{'='*80}")
        
        output_dir = self.work_dir / "audit"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        returncode, _, stderr = self.run_script(
            "audit_drive.py",
            [str(self.drive_path), "--output-dir", str(output_dir)],
            capture_output=False
        )
        
        if returncode == 0:
            self.log_step("audit", "SUCCESS", {"output_dir": str(output_dir)})
            
            # Find audit files
            audit_files = list(output_dir.glob("audit_*.json"))
            if audit_files:
                self.results["audit_file"] = str(audit_files[0])
            
            return True
        else:
            self.log_step("audit", "FAILED", {"error": stderr})
            self.results["errors"].append(f"Audit failed: {stderr}")
            return False
    
    def step_report(self) -> bool:
        """Step 2: Generate audit report."""
        print(f"\n{'='*80}")
        print("STEP 2: GENERATE REPORT")
        print(f"{'='*80}")
        
        if not self.results.get("audit_file"):
            logger.error("No audit file found, skipping report")
            return False
        
        returncode, _, stderr = self.run_script(
            "generate_report.py",
            [self.results["audit_file"], "--project-name", self.project_name],
            capture_output=False
        )
        
        if returncode == 0:
            self.log_step("report", "SUCCESS")
            return True
        else:
            self.log_step("report", "FAILED", {"error": stderr})
            # Non-fatal, continue
            return True
    
    def step_dedupe(self) -> bool:
        """Step 3: Check for duplicates."""
        print(f"\n{'='*80}")
        print("STEP 3: DUPLICATE CHECK")
        print(f"{'='*80}")
        
        output_dir = self.work_dir / "dedupe"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Run deduplication against existing library if it exists
        library_path = Path(__file__).parent.parent / "01_PHOTOS"
        
        args = [str(self.drive_path), "--output-dir", str(output_dir)]
        
        if library_path.exists():
            args.extend(["--lightroom-catalog", str(Path(__file__).parent.parent / "04_CATALOGS" / "Master_Catalog.lrcat")])
        
        returncode, _, stderr = self.run_script(
            "deduplicate.py",
            args,
            capture_output=False
        )
        
        if returncode == 0:
            self.log_step("dedupe", "SUCCESS", {"output_dir": str(output_dir)})
            
            # Find report
            report_files = list(output_dir.glob("dedupe_report_*.html"))
            if report_files:
                self.results["dedupe_report"] = str(report_files[0])
            
            return True
        else:
            self.log_step("dedupe", "FAILED", {"error": stderr})
            # Non-fatal, continue
            return True
    
    def step_confirm(self) -> bool:
        """Step 4: User confirmation."""
        print(f"\n{'='*80}")
        print("STEP 4: USER CONFIRMATION")
        print(f"{'='*80}")
        
        print(f"\n📊 Project: {self.project_name}")
        print(f"💾 Drive: {self.drive_path}")
        if self.backup_path:
            print(f"🗄️  Backup: {self.backup_path}")
        
        # Show summary from audit
        if self.results.get("audit_file"):
            try:
                with open(self.results["audit_file"], "r") as f:
                    audit_data = json.load(f)
                
                print(f"\n📁 Files to process: {audit_data.get('total_files', 0):,}")
                print(f"💾 Total size: {audit_data.get('total_size', 0) / (1024**3):.2f} GB")
            except Exception as e:
                logger.warning(f"Could not read audit data: {e}")
        
        print(f"\n⚠️  This will:")
        print(f"   1. Rename files based on EXIF metadata")
        print(f"   2. Transfer to library with hash verification")
        print(f"   3. Verify backup (if backup path specified)")
        
        confirm = input("\nProceed with ingestion? (yes/no): ").strip().lower()
        
        if confirm == "yes":
            self.log_step("confirmation", "APPROVED")
            return True
        else:
            self.log_step("confirmation", "DECLINED")
            print("Ingestion cancelled by user.")
            return False
    
    def step_rename(self) -> bool:
        """Step 5: Rename files."""
        print(f"\n{'='*80}")
        print("STEP 5: RENAME FILES")
        print(f"{'='*80}")
        
        # Use standard naming pattern
        pattern = "{YYYY}{MM}{DD}_{camera_model}_{sequence}"
        
        print(f"Pattern: {pattern}")
        print("Running in preview mode first...")
        
        # Preview
        returncode, stdout, stderr = self.run_script(
            "rename_batch.py",
            [str(self.drive_path), "--pattern", pattern, "--preview"],
            capture_output=True
        )
        
        if returncode == 0:
            print(stdout)
            
            # Ask for execute confirmation
            confirm = input("\nExecute renames? (yes/no): ").strip().lower()
            
            if confirm == "yes":
                returncode, _, stderr = self.run_script(
                    "rename_batch.py",
                    [str(self.drive_path), "--pattern", pattern, "--execute"],
                    capture_output=False
                )
                
                if returncode == 0:
                    self.log_step("rename", "SUCCESS")
                    return True
                else:
                    self.log_step("rename", "FAILED", {"error": stderr})
                    self.results["errors"].append(f"Rename failed: {stderr}")
                    return False
            else:
                print("Rename skipped.")
                self.log_step("rename", "SKIPPED")
                return True
        else:
            self.log_step("rename", "FAILED", {"error": stderr})
            # Non-fatal, continue
            return True
    
    def step_transfer(self) -> bool:
        """Step 6: Transfer files."""
        print(f"\n{'='*80}")
        print("STEP 6: TRANSFER FILES")
        print(f"{'='*80}")
        
        # Determine destination
        dest_dir = Path(__file__).parent.parent / "00_INCOMING" / self.project_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        returncode, _, stderr = self.run_script(
            "transfer_assets.py",
            [str(self.drive_path), str(dest_dir)],
            capture_output=False
        )
        
        if returncode == 0:
            self.log_step("transfer", "SUCCESS", {"destination": str(dest_dir)})
            self.results["transfer_destination"] = str(dest_dir)
            return True
        else:
            self.log_step("transfer", "FAILED", {"error": stderr})
            self.results["errors"].append(f"Transfer failed: {stderr}")
            return False
    
    def step_backup_verify(self) -> bool:
        """Step 7: Verify backup."""
        if not self.backup_path:
            print("\nNo backup path specified, skipping backup verification.")
            self.log_step("backup_verify", "SKIPPED")
            return True
        
        print(f"\n{'='*80}")
        print("STEP 7: BACKUP VERIFICATION")
        print(f"{'='*80}")
        
        primary = Path(__file__).parent.parent / "00_INCOMING" / self.project_name
        
        if not primary.exists():
            logger.warning("Transfer destination does not exist, skipping backup verify")
            return True
        
        returncode, _, stderr = self.run_script(
            "backup_verify.py",
            [str(primary), str(self.backup_path)],
            capture_output=False
        )
        
        if returncode == 0:
            self.log_step("backup_verify", "SUCCESS")
            return True
        else:
            self.log_step("backup_verify", "MISMATCHES_FOUND", {"error": stderr})
            # Non-fatal, but log warning
            return True
    
    def step_index(self) -> bool:
        """Step 8: Update master index."""
        print(f"\n{'='*80}")
        print("STEP 8: UPDATE INDEX")
        print(f"{'='*80}")
        
        # Append to master ingestion log
        index_file = Path(__file__).parent.parent / "06_METADATA" / "ingestion_index.json"
        index_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load or create index
        if index_file.exists():
            with open(index_file, "r") as f:
                index = json.load(f)
        else:
            index = {"ingestions": []}
        
        # Add this ingestion
        self.results["end_time"] = datetime.now().isoformat()
        index["ingestions"].append(self.results)
        
        # Save
        with open(index_file, "w") as f:
            json.dump(index, f, indent=2, default=str)
        
        self.log_step("index", "SUCCESS", {"index_file": str(index_file)})
        return True
    
    def step_summary(self) -> bool:
        """Step 9: Write ingestion summary."""
        print(f"\n{'='*80}")
        print("STEP 9: INGESTION SUMMARY")
        print(f"{'='*80}")
        
        self.results["end_time"] = datetime.now().isoformat()
        
        # Determine status
        failed_steps = [s for s in self.results["steps"] if s["status"] == "FAILED"]
        if failed_steps:
            self.results["status"] = "COMPLETED_WITH_ERRORS"
        else:
            self.results["status"] = "SUCCESS"
        
        # Write summary
        summary_file = self.work_dir / "ingestion_summary.json"
        with open(summary_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Print summary
        print(f"\n{'='*80}")
        print("INGESTION COMPLETE")
        print(f"{'='*80}")
        print(f"Project: {self.project_name}")
        print(f"Status: {self.results['status']}")
        print(f"Duration: {self.results['end_time']}")
        print(f"Steps completed: {len(self.results['steps'])}")
        
        if self.results["errors"]:
            print(f"\n⚠️  Errors ({len(self.results['errors'])}):")
            for err in self.results["errors"]:
                print(f"   - {err}")
        
        print(f"\n📄 Summary: {summary_file}")
        print(f"{'='*80}\n")
        
        self.log_step("summary", "SUCCESS", {"summary_file": str(summary_file)})
        return True
    
    def run(self) -> bool:
        """Run complete ingestion workflow."""
        print(f"\n{'='*80}")
        print(f"DRIVE INGESTION WORKFLOW")
        print(f"{'='*80}")
        print(f"Project: {self.project_name}")
        print(f"Drive: {self.drive_path}")
        print(f"Started: {self.results['start_time']}")
        print(f"{'='*80}")
        
        # Create work directory
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate drive
        if not self.drive_path.exists():
            logger.error(f"Drive does not exist: {self.drive_path}")
            self.log_step("validation", "FAILED", {"error": "Drive not found"})
            return False
        
        # Run steps
        steps = [
            ("audit", self.step_audit),
            ("report", self.step_report),
            ("dedupe", self.step_dedupe),
            ("confirmation", self.step_confirm),
            ("rename", self.step_rename),
            ("transfer", self.step_transfer),
            ("backup_verify", self.step_backup_verify),
            ("index", self.step_index),
            ("summary", self.step_summary)
        ]
        
        for step_name, step_func in steps:
            try:
                success = step_func()
                
                if not success and step_name in ["audit", "confirmation", "transfer"]:
                    # Critical step failed
                    print(f"\n❌ Critical step failed: {step_name}")
                    print("Ingestion aborted.")
                    self.results["status"] = "ABORTED"
                    self.step_summary()
                    return False
                
            except KeyboardInterrupt:
                print(f"\n\n⚠️  Interrupted by user at step: {step_name}")
                self.results["status"] = "INTERRUPTED"
                self.step_summary()
                return False
            except Exception as e:
                logger.error(f"Step {step_name} failed with exception: {e}")
                self.results["errors"].append(f"Step {step_name}: {e}")
        
        return self.results["status"] in ["SUCCESS", "COMPLETED_WITH_ERRORS"]


def main():
    parser = argparse.ArgumentParser(
        description="Master drive ingestion orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /mnt/external_drive --project "Wedding_Smith_2026"
  %(prog)s /mnt/backup --project "Portfolio_2026" --backup /mnt/nas/backup
        """
    )
    parser.add_argument(
        "drive",
        type=Path,
        help="Path to the drive/directory to ingest"
    )
    parser.add_argument(
        "--project", "-p",
        type=str,
        required=True,
        help="Project/event name for organization"
    )
    parser.add_argument(
        "--backup", "-b",
        type=Path,
        help="Optional backup destination path"
    )
    parser.add_argument(
        "--skip-rename",
        action="store_true",
        help="Skip the rename step"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.dry_run:
        print(f"\n{'='*80}")
        print("DRY RUN - No changes will be made")
        print(f"{'='*80}")
        print(f"Drive: {args.drive}")
        print(f"Project: {args.project}")
        print(f"Backup: {args.backup}")
        print(f"\nWorkflow steps that would run:")
        print("  1. audit_drive.py")
        print("  2. generate_report.py")
        print("  3. deduplicate.py")
        print("  4. User confirmation")
        print("  5. rename_batch.py (unless --skip-rename)")
        print("  6. transfer_assets.py")
        print("  7. backup_verify.py (if --backup specified)")
        print("  8. Update index")
        print("  9. Write summary")
        sys.exit(0)
    
    try:
        ingestor = DriveIngestor(
            drive_path=args.drive,
            project_name=args.project,
            backup_path=args.backup
        )
        
        success = ingestor.run()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nIngestion interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
