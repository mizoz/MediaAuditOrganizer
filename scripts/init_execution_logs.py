#!/usr/bin/env python3
"""
init_execution_logs.py — Initialize execution_logs table for heartbeat protocol

Creates the execution_logs table in media_audit.db if it doesn't exist.
This table tracks all background task execution with heartbeat monitoring.

Usage:
    python init_execution_logs.py
"""

import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "06_METADATA" / "media_audit.db"


def init_execution_logs_table():
    """Create execution_logs table if not exists."""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS execution_logs (
        task_id TEXT PRIMARY KEY,
        task_type TEXT NOT NULL,
        status TEXT NOT NULL,
        progress_pct REAL DEFAULT 0,
        started_at TEXT,
        completed_at TEXT,
        last_heartbeat TEXT,
        pid INTEGER,
        log_path TEXT,
        status_message TEXT,
        metadata_json TEXT,
        error_message TEXT
    )
    """
    
    # Create index on status for quick filtering
    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_execution_logs_status 
    ON execution_logs(status)
    """
    
    # Create index on last_heartbeat for timeout detection
    create_heartbeat_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_execution_logs_heartbeat 
    ON execution_logs(last_heartbeat)
    """
    
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute(create_table_sql)
        cursor.execute(create_index_sql)
        cursor.execute(create_heartbeat_index_sql)
        
        conn.commit()
        
        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='execution_logs'")
        result = cursor.fetchone()
        
        if result:
            print(f"✅ execution_logs table created/verified in {DB_PATH}")
            return True
        else:
            print(f"❌ Failed to create execution_logs table")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    success = init_execution_logs_table()
    exit(0 if success else 1)
