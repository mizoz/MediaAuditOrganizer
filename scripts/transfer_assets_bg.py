#!/usr/bin/env python3
"""
transfer_assets_bg.py — Background Transfer with Heartbeat Protocol

This is a wrapper around transfer_assets.py that integrates with the
heartbeat protocol for background execution.

Usage:
    # Quick spawn (returns immediately with task_id)
    python transfer_assets_bg.py /source /dest --spawn
    
    # Direct execution (blocks until complete)
    python transfer_assets_bg.py /source /dest --task-id TASK_20260304_000500_TRANSFER_0001
"""

import argparse
import sys
import time
import threading
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from task_manager import create_task
from background_runner import spawn_background_task
from heartbeat_logger import heartbeat, HeartbeatMonitor


def run_transfer_with_heartbeat(
    task_id: str,
    source: str,
    dest: str,
    **kwargs
):
    """
    Run transfer with periodic heartbeat updates.
    
    This function is called by the background process.
    """
    from transfer_assets import main as transfer_main
    
    # Use heartbeat monitor context manager
    with HeartbeatMonitor(task_id, interval_seconds=30) as monitor:
        # Import and run transfer
        # Note: We need to modify transfer_assets to accept progress callbacks
        # For now, we'll use periodic heartbeats in a separate thread
        
        heartbeat_thread_stop = threading.Event()
        
        def heartbeat_loop():
            """Send heartbeat every 30 seconds during transfer."""
            progress = 0
            while not heartbeat_thread_stop.is_set():
                time.sleep(30)
                if not heartbeat_thread_stop.is_set():
                    heartbeat(task_id, progress, "Transfer in progress...", {"phase": "transferring"})
        
        # Start heartbeat thread
        hb_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        hb_thread.start()
        
        try:
            # Run transfer (this will block)
            # We need to patch transfer_assets to call our heartbeat
            # For now, run it directly
            sys.argv = ["transfer_assets.py", source, dest]
            
            # Add any extra args
            if kwargs.get("manifest"):
                sys.argv.extend(["--manifest", kwargs["manifest"]])
            if kwargs.get("dry_run"):
                sys.argv.append("--dry-run")
            
            # Run transfer
            transfer_main()
            
            # Mark as complete
            heartbeat(task_id, 100.0, "Transfer completed successfully", status="COMPLETED")
            
        except SystemExit as e:
            if e.code == 0:
                heartbeat(task_id, 100.0, "Transfer completed", status="COMPLETED")
            else:
                heartbeat(task_id, 0.0, f"Transfer failed with code {e.code}", status="FAILED")
            raise
        except Exception as e:
            heartbeat(task_id, 0.0, f"Transfer failed: {e}", status="FAILED")
            raise
        finally:
            heartbeat_thread_stop.set()
            hb_thread.join(timeout=1)


def spawn_transfer_task(source: str, dest: str, **kwargs) -> str:
    """
    Spawn a background transfer task and return immediately.
    
    Args:
        source: Source directory path
        dest: Destination directory path
        **kwargs: Additional arguments (manifest, dry_run, etc.)
        
    Returns:
        task_id: Unique task identifier
        
    Time: < 5 seconds
    """
    # Create task record
    params = {
        "source": source,
        "destination": dest,
        **kwargs
    }
    task_id = create_task("TRANSFER", params)
    print(f"✅ Created task: {task_id}")
    
    # Build arguments for background script
    args = [source, dest, "--task-id", task_id]
    
    if kwargs.get("manifest"):
        args.extend(["--manifest", kwargs["manifest"]])
    if kwargs.get("dry_run"):
        args.append("--dry-run")
    if kwargs.get("skip_preflight"):
        args.append("--skip-preflight")
    
    # Spawn background process
    script_path = Path(__file__).parent / "transfer_assets_bg.py"
    pid = spawn_background_task(str(script_path), args, task_id)
    
    print(f"✅ Background task spawned (PID: {pid})")
    print(f"   Monitor with: python task_status.py {task_id}")
    
    return task_id


def main():
    parser = argparse.ArgumentParser(description="Background Transfer with Heartbeat")
    parser.add_argument("source", type=str, help="Source directory")
    parser.add_argument("destination", type=str, help="Destination directory")
    parser.add_argument("--spawn", action="store_true", help="Spawn as background task and return immediately")
    parser.add_argument("--task-id", type=str, help="Task ID (for background execution)")
    parser.add_argument("--manifest", type=str, help="Shadow manifest path")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no actual copy)")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip disk space check")
    
    args = parser.parse_args()
    
    # If --spawn, spawn background and return
    if args.spawn:
        task_id = spawn_transfer_task(
            args.source,
            args.destination,
            manifest=args.manifest,
            dry_run=args.dry_run,
            skip_preflight=args.skip_preflight
        )
        print(f"\nTask ID: {task_id}")
        print(f"Started: {datetime.now().isoformat()}")
        print(f"\nTo monitor:")
        print(f"  python task_status.py {task_id}")
        print(f"  python task_status.py list")
        return
    
    # If --task-id, run with heartbeat
    if args.task_id:
        # Initial heartbeat
        heartbeat(args.task_id, 0.0, "Starting transfer...", {"phase": "init"})
        
        # Run transfer with heartbeat monitoring
        run_transfer_with_heartbeat(
            args.task_id,
            args.source,
            args.destination,
            manifest=args.manifest,
            dry_run=args.dry_run
        )
        return
    
    # Otherwise, just run transfer directly (no heartbeat)
    from transfer_assets import main as transfer_main
    sys.argv = ["transfer_assets.py", args.source, args.destination]
    if args.manifest:
        sys.argv.extend(["--manifest", args.manifest])
    if args.dry_run:
        sys.argv.append("--dry-run")
    if args.skip_preflight:
        sys.argv.append("--skip-preflight")
    transfer_main()


if __name__ == "__main__":
    main()
