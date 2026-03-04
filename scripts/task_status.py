#!/usr/bin/env python3
"""
task_status.py — Task Status API for Heartbeat Protocol

Provides functions to query task status, list active tasks, and cancel tasks.

Usage:
    from task_status import get_task_status, list_active_tasks, cancel_task
    
    status = get_task_status("TASK_20260304_000500_TRANSFER_0001")
    active = list_active_tasks()
    cancelled = cancel_task("TASK_20260304_000500_TRANSFER_0001")
"""

import sqlite3
import json
import os
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Database path
DB_PATH = Path(__file__).parent.parent / "06_METADATA" / "media_audit.db"


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed status for a specific task.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Dict with task details or None if not found
    """
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM execution_logs
            WHERE task_id = ?
        """, (task_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        # Convert to dict
        status = dict(row)
        
        # Parse metadata JSON
        if status.get("metadata_json"):
            try:
                status["metadata"] = json.loads(status["metadata_json"])
            except json.JSONDecodeError:
                status["metadata"] = {}
        else:
            status["metadata"] = {}
        
        # Calculate time running
        if status.get("started_at"):
            started = datetime.fromisoformat(status["started_at"])
            now = datetime.now()
            status["running_duration_seconds"] = (now - started).total_seconds()
        
        return status
        
    except sqlite3.Error as e:
        print(f"❌ Failed to get task status: {e}")
        return None
    finally:
        if conn:
            conn.close()


def list_active_tasks(status_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    List all active tasks.
    
    Args:
        status_filter: Optional list of statuses to filter (default: STARTING, RUNNING, PAUSED)
        
    Returns:
        List of task status dicts
    """
    if status_filter is None:
        status_filter = ["STARTING", "RUNNING", "PAUSED"]
    
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        placeholders = ",".join("?" * len(status_filter))
        cursor.execute(f"""
            SELECT * FROM execution_logs
            WHERE status IN ({placeholders})
            ORDER BY started_at DESC
        """, status_filter)
        
        rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            task = dict(row)
            if task.get("metadata_json"):
                try:
                    task["metadata"] = json.loads(task["metadata_json"])
                except json.JSONDecodeError:
                    task["metadata"] = {}
            else:
                task["metadata"] = {}
            tasks.append(task)
        
        return tasks
        
    except sqlite3.Error as e:
        print(f"❌ Failed to list active tasks: {e}")
        return []
    finally:
        if conn:
            conn.close()


def cancel_task(task_id: str) -> bool:
    """
    Cancel a running task by sending SIGTERM to its process.
    
    Args:
        task_id: Task identifier
        
    Returns:
        True if cancellation initiated, False otherwise
    """
    # Get task info
    status = get_task_status(task_id)
    
    if not status:
        print(f"❌ Task not found: {task_id}")
        return False
    
    if status["status"] in ("COMPLETED", "FAILED", "CANCELLED"):
        print(f"⚠️  Task {task_id} is already {status['status']}")
        return False
    
    pid = status.get("pid")
    
    if not pid or pid < 0:
        print(f"⚠️  No PID recorded for task {task_id}")
        # Still mark as cancelled in DB
        _update_task_status(task_id, "CANCELLED", "Cancelled (no PID)")
        return True
    
    try:
        # Send SIGTERM
        os.kill(pid, signal.SIGTERM)
        print(f"✅ Sent SIGTERM to PID {pid} for task {task_id}")
        
        # Update database
        _update_task_status(task_id, "CANCELLED", f"Cancelled via SIGTERM to PID {pid}")
        
        return True
        
    except ProcessLookupError:
        print(f"⚠️  Process {pid} not found (already terminated)")
        _update_task_status(task_id, "CANCELLED", "Process not found")
        return True
        
    except PermissionError:
        print(f"❌ Permission denied to kill process {pid}")
        return False
        
    except OSError as e:
        print(f"❌ Failed to kill process: {e}")
        return False


def _update_task_status(task_id: str, status: str, message: str):
    """Update task status in database."""
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE execution_logs
            SET status = ?,
                status_message = ?,
                completed_at = ?,
                last_heartbeat = ?
            WHERE task_id = ?
        """, (status, message, now, now, task_id))
        
        conn.commit()
        
    except sqlite3.Error as e:
        print(f"⚠️  Warning: Failed to update task status: {e}")
    finally:
        if conn:
            conn.close()


def get_recent_tasks(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get most recent tasks regardless of status.
    
    Args:
        limit: Number of tasks to return
        
    Returns:
        List of task status dicts
    """
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM execution_logs
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            task = dict(row)
            if task.get("metadata_json"):
                try:
                    task["metadata"] = json.loads(task["metadata_json"])
                except json.JSONDecodeError:
                    task["metadata"] = {}
            else:
                task["metadata"] = {}
            tasks.append(task)
        
        return tasks
        
    except sqlite3.Error as e:
        print(f"❌ Failed to get recent tasks: {e}")
        return []
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python task_status.py <task_id|list|recent|cancel>")
        print("  list          - List active tasks")
        print("  recent [n]    - Show recent tasks (default: 10)")
        print("  <task_id>     - Get status for specific task")
        print("  cancel <id>   - Cancel a task")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "list":
        tasks = list_active_tasks()
        print(f"Active tasks: {len(tasks)}")
        for task in tasks:
            print(f"  {task['task_id']}: {task['status']} ({task['progress_pct']}%)")
    
    elif cmd == "recent":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        tasks = get_recent_tasks(limit)
        print(f"Recent tasks: {len(tasks)}")
        for task in tasks:
            print(f"  {task['task_id']}: {task['status']} ({task['progress_pct']}%)")
    
    elif cmd == "cancel":
        if len(sys.argv) < 3:
            print("❌ Missing task_id for cancel")
            sys.exit(1)
        success = cancel_task(sys.argv[2])
        print(f"✅ Cancelled" if success else "❌ Failed to cancel")
    
    else:
        status = get_task_status(cmd)
        if status:
            print(f"Task: {status['task_id']}")
            print(f"  Type: {status['task_type']}")
            print(f"  Status: {status['status']}")
            print(f"  Progress: {status['progress_pct']}%")
            print(f"  Started: {status['started_at']}")
            print(f"  Last Heartbeat: {status.get('last_heartbeat', 'N/A')}")
            print(f"  PID: {status.get('pid', 'N/A')}")
            print(f"  Message: {status.get('status_message', 'N/A')}")
        else:
            print(f"❌ Task not found: {cmd}")
