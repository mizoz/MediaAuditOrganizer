#!/usr/bin/env python3
"""
task_manager.py — Task ID Generator for Heartbeat Protocol

Generates unique task IDs and creates initial execution log records.
Task ID format: TASK_YYYYMMDD_HHMMSS_<TYPE>_<SEQ>
Example: TASK_20260304_000500_TRANSFER_0001

Usage:
    from task_manager import create_task
    task_id = create_task("TRANSFER", {"source": "/path", "dest": "/path"})
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Database path
DB_PATH = Path(__file__).parent.parent / "06_METADATA" / "media_audit.db"


def get_next_sequence(task_type: str) -> int:
    """Get the next sequence number for a task type."""
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Get today's date prefix
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"TASK_{today}%"
        
        cursor.execute("""
            SELECT task_id FROM execution_logs 
            WHERE task_id LIKE ? AND task_type = ?
            ORDER BY task_id DESC
            LIMIT 1
        """, (prefix, task_type))
        
        result = cursor.fetchone()
        
        if result:
            # Extract sequence from existing task_id
            last_task_id = result[0]
            try:
                last_seq = int(last_task_id.split("_")[-1])
                return last_seq + 1
            except (ValueError, IndexError):
                return 1
        else:
            return 1
            
    except sqlite3.Error:
        return 1
    finally:
        if conn:
            conn.close()


def create_task(task_type: str, params: Optional[Dict] = None) -> str:
    """
    Create a new task and return task_id immediately.
    
    Args:
        task_type: Type of task (e.g., "TRANSFER", "VIDEO_PROCESS", "DEDUPLICATE")
        params: Optional dictionary of task parameters
        
    Returns:
        task_id: Unique task identifier (e.g., TASK_20260304_000500_TRANSFER_0001)
        
    Time: < 1 second
    """
    # Generate timestamp
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    # Get sequence number
    seq = get_next_sequence(task_type)
    
    # Generate task_id
    task_id = f"TASK_{timestamp}_{task_type}_{seq:04d}"
    
    # Insert initial record
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO execution_logs (
                task_id,
                task_type,
                status,
                progress_pct,
                started_at,
                metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            task_id,
            task_type,
            "STARTING",
            0.0,
            now.isoformat(),
            json.dumps(params or {})
        ))
        
        conn.commit()
        return task_id
        
    except sqlite3.Error as e:
        raise RuntimeError(f"Failed to create task: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    # Test task creation
    import sys
    
    task_type = sys.argv[1] if len(sys.argv) > 1 else "TEST"
    task_id = create_task(task_type, {"test": True})
    print(f"Created task: {task_id}")
