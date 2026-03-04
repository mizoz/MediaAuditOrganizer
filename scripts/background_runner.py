#!/usr/bin/env python3
"""
background_runner.py — Background Task Executor for Heartbeat Protocol

Spawns detached background processes that survive main process termination.
Uses subprocess.Popen with start_new_session=True for proper detachment.

Usage:
    from background_runner import spawn_background_task
    pid = spawn_background_task(
        script_path="scripts/transfer_assets.py",
        args=["/source", "/dest"],
        task_id="TASK_20260304_000500_TRANSFER_0001"
    )
"""

import subprocess
import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Database path
DB_PATH = Path(__file__).parent.parent / "06_METADATA" / "media_audit.db"

# Log directory
LOG_DIR = Path(__file__).parent.parent / "07_LOGS"


def spawn_background_task(
    script_path: str,
    args: List[str],
    task_id: str,
    python_exec: Optional[str] = None
) -> int:
    """
    Spawn a detached background process.
    
    Args:
        script_path: Path to Python script to execute
        args: Command-line arguments for the script
        task_id: Task identifier for logging
        python_exec: Python executable path (defaults to current)
        
    Returns:
        pid: Process ID of spawned process
        
    Time: < 1 second
    """
    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Resolve script path
    script_path = Path(script_path)
    if not script_path.is_absolute():
        script_path = Path(__file__).parent / script_path
    
    # Determine Python executable
    if python_exec is None:
        python_exec = sys.executable
    
    # Build command
    cmd = [python_exec, str(script_path)] + args
    
    # Log file path
    log_path = LOG_DIR / f"task_{task_id}.log"
    
    # Open log file for stdout/stderr redirection
    log_file = open(log_path, "a", buffering=1)
    
    # Spawn detached process
    process = subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=log_file,
        start_new_session=True,  # Detach from parent session
        cwd=str(Path(__file__).parent.parent),
        env=os.environ.copy()
    )
    
    pid = process.pid
    
    # Update database with PID and log path
    _update_task_pid(task_id, pid, str(log_path))
    
    # Close log file handle in parent (child has its own)
    log_file.close()
    
    print(f"✅ Spawned background task {task_id} (PID: {pid})")
    print(f"   Log: {log_path}")
    
    return pid


def _update_task_pid(task_id: str, pid: int, log_path: str):
    """Update execution_logs with PID and log path."""
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE execution_logs
            SET pid = ?,
                log_path = ?,
                status = 'RUNNING'
            WHERE task_id = ?
        """, (pid, log_path, task_id))
        
        conn.commit()
        
    except sqlite3.Error as e:
        print(f"⚠️  Warning: Failed to update task PID: {e}")
    finally:
        if conn:
            conn.close()


def spawn_with_nohup(
    script_path: str,
    args: List[str],
    task_id: str
) -> int:
    """
    Alternative: Spawn using nohup for maximum detachment.
    
    This method is more robust for long-running tasks but slightly slower.
    
    Returns:
        pid: Process ID (may be shell PID, not actual process)
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    script_path = Path(script_path)
    if not script_path.is_absolute():
        script_path = Path(__file__).parent / script_path
    
    log_path = LOG_DIR / f"task_{task_id}.log"
    
    # Build command string
    cmd_parts = [sys.executable, str(script_path)] + args
    cmd_str = " ".join(cmd_parts)
    
    # Use nohup with output redirection
    nohup_cmd = f"nohup {cmd_str} > {log_path} 2>&1 &"
    
    # Execute via shell
    subprocess.run(nohup_cmd, shell=True, check=True)
    
    # Update database (PID will be approximate)
    _update_task_pid(task_id, -1, str(log_path))
    
    print(f"✅ Spawned background task {task_id} via nohup")
    print(f"   Log: {log_path}")
    
    return -1


if __name__ == "__main__":
    # Test background spawning
    if len(sys.argv) < 2:
        print("Usage: python background_runner.py <script> [args...]")
        sys.exit(1)
    
    script = sys.argv[1]
    args = sys.argv[2:]
    
    # Create a test task
    from task_manager import create_task
    task_id = create_task("BACKGROUND_TEST", {"script": script})
    
    pid = spawn_background_task(script, args, task_id)
    print(f"Task ID: {task_id}")
    print(f"PID: {pid}")
