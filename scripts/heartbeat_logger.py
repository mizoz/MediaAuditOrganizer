#!/usr/bin/env python3
"""
heartbeat_logger.py — Heartbeat Logger for Background Tasks

Updates task progress and heartbeat timestamps in the execution_logs table.
Auto-detects failed tasks (no heartbeat for 5 minutes).

Usage:
    from heartbeat_logger import heartbeat
    heartbeat(task_id, progress_pct=50.0, message="Processing files...")
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any

# Database path
DB_PATH = Path(__file__).parent.parent / "06_METADATA" / "media_audit.db"

# Timeout threshold (5 minutes)
HEARTBEAT_TIMEOUT_MINUTES = 5


def heartbeat(
    task_id: str,
    progress_pct: float,
    message: str,
    metadata: Optional[Dict[str, Any]] = None,
    status: Optional[str] = None
) -> bool:
    """
    Update task heartbeat and progress.
    
    Args:
        task_id: Task identifier
        progress_pct: Progress percentage (0.0 - 100.0)
        message: Status message
        metadata: Optional additional metadata dict
        status: Optional status override (RUNNING, COMPLETED, FAILED, etc.)
        
    Returns:
        True if heartbeat recorded successfully
    """
    now = datetime.now()
    
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Build update query
        update_fields = [
            "progress_pct = ?",
            "last_heartbeat = ?",
            "status_message = ?"
        ]
        values = [progress_pct, now.isoformat(), message]
        
        if metadata is not None:
            update_fields.append("metadata_json = ?")
            values.append(json.dumps(metadata))
        
        if status is not None:
            update_fields.append("status = ?")
            values.append(status)
            
            if status in ("COMPLETED", "FAILED", "CANCELLED"):
                update_fields.append("completed_at = ?")
                values.append(now.isoformat())
        
        values.append(task_id)
        
        query = f"""
            UPDATE execution_logs
            SET {', '.join(update_fields)}
            WHERE task_id = ?
        """
        
        cursor.execute(query, values)
        conn.commit()
        
        if cursor.rowcount == 0:
            print(f"⚠️  Warning: No task found with id {task_id}")
            return False
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Heartbeat failed: {e}")
        return False
    finally:
        if conn:
            conn.close()


def check_stale_tasks() -> list:
    """
    Check for tasks with no heartbeat for 5+ minutes and mark as FAILED.
    
    Returns:
        List of task_ids marked as failed
    """
    now = datetime.now()
    timeout_threshold = now - timedelta(minutes=HEARTBEAT_TIMEOUT_MINUTES)
    
    conn = None
    failed_tasks = []
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Find stale running tasks
        cursor.execute("""
            SELECT task_id FROM execution_logs
            WHERE status IN ('STARTING', 'RUNNING', 'PAUSED')
            AND last_heartbeat < ?
        """, (timeout_threshold.isoformat(),))
        
        stale_tasks = cursor.fetchall()
        
        for (task_id,) in stale_tasks:
            cursor.execute("""
                UPDATE execution_logs
                SET status = 'FAILED',
                    completed_at = ?,
                    error_message = 'Heartbeat timeout - no update for 5 minutes'
                WHERE task_id = ?
            """, (now.isoformat(), task_id))
            failed_tasks.append(task_id)
        
        conn.commit()
        
        if failed_tasks:
            print(f"⚠️  Marked {len(failed_tasks)} stale tasks as FAILED")
        
        return failed_tasks
        
    except sqlite3.Error as e:
        print(f"❌ Failed to check stale tasks: {e}")
        return []
    finally:
        if conn:
            conn.close()


class HeartbeatMonitor:
    """Context manager for automatic heartbeat tracking."""
    
    def __init__(self, task_id: str, interval_seconds: int = 30):
        self.task_id = task_id
        self.interval_seconds = interval_seconds
        self.last_heartbeat = 0
        self._progress = 0.0
        self._message = "Initializing..."
        self._metadata = {}
    
    def update(self, progress_pct: float, message: str, metadata: Optional[Dict] = None):
        """Update progress without immediately writing to DB."""
        self._progress = progress_pct
        self._message = message
        if metadata:
            self._metadata = metadata
    
    def _should_heartbeat(self) -> bool:
        """Check if it's time to send a heartbeat."""
        now = datetime.now().timestamp()
        if now - self.last_heartbeat >= self.interval_seconds:
            self.last_heartbeat = now
            return True
        return False
    
    def flush(self):
        """Force a heartbeat write to DB."""
        heartbeat(
            self.task_id,
            self._progress,
            self._message,
            self._metadata
        )
    
    def __enter__(self):
        heartbeat(self.task_id, 0.0, "Starting...", {"phase": "init"})
        self.last_heartbeat = datetime.now().timestamp()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            heartbeat(self.task_id, 100.0, "Completed successfully", status="COMPLETED")
        else:
            heartbeat(
                self.task_id,
                self._progress,
                f"Failed: {exc_val}",
                status="FAILED"
            )
        return False  # Don't suppress exceptions


if __name__ == "__main__":
    # Test heartbeat
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python heartbeat_logger.py <task_id> [progress] [message]")
        sys.exit(1)
    
    task_id = sys.argv[1]
    progress = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    message = sys.argv[3] if len(sys.argv) > 3 else "Test heartbeat"
    
    success = heartbeat(task_id, progress, message)
    print(f"✅ Heartbeat recorded" if success else "❌ Heartbeat failed")
