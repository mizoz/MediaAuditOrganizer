#!/usr/bin/env python3
"""
checkpoint_logger.py — Checkpoint and Resume System

Provides checkpoint saving/loading for file transfer operations.
- Saves checkpoint every N operations or T seconds
- Enables resume from exact position after interruption
- Tracks success/failure counts and last completed operation
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CheckpointLogger:
    """Manages checkpoint state for transfer operations."""
    
    def __init__(
        self,
        checkpoint_dir: Path,
        checkpoint_interval: int = 50,
        checkpoint_time_interval: int = 60
    ):
        """
        Initialize checkpoint logger.
        
        Args:
            checkpoint_dir: Directory to store checkpoint files
            checkpoint_interval: Save checkpoint every N operations
            checkpoint_time_interval: Save checkpoint every N seconds
        """
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_interval = checkpoint_interval
        self.checkpoint_time_interval = checkpoint_time_interval
        
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Checkpoint state
        self.state = {
            "last_completed_op_id": None,
            "last_completed_index": -1,
            "total_ops": 0,
            "success_count": 0,
            "fail_count": 0,
            "start_time": None,
            "last_checkpoint_time": None,
            "checkpoint_file": None
        }
        
        self.ops_since_checkpoint = 0
        self.last_checkpoint_timestamp = time.time()
    
    def initialize(self, total_ops: int, manifest_path: Path) -> None:
        """Initialize checkpoint for new transfer session."""
        self.state["total_ops"] = total_ops
        self.state["start_time"] = datetime.now().isoformat()
        self.state["last_checkpoint_time"] = datetime.now().isoformat()
        self.state["checkpoint_file"] = str(manifest_path)
        
        # Save initial checkpoint
        self.save_checkpoint()
        logger.info(f"📍 Checkpoint initialized: {total_ops} operations")
    
    def save_checkpoint(self) -> Path:
        """Save current state to checkpoint file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_path = self.checkpoint_dir / f"checkpoint_{timestamp}.json"
        
        self.state["last_checkpoint_time"] = datetime.now().isoformat()
        
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, default=str)
        
        # Also save as latest.json for easy access
        latest_path = self.checkpoint_dir / "checkpoint_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, default=str)
        
        self.ops_since_checkpoint = 0
        self.last_checkpoint_timestamp = time.time()
        
        logger.debug(f"💾 Checkpoint saved: {checkpoint_path}")
        return checkpoint_path
    
    def record_operation(
        self,
        op_id: str,
        op_index: int,
        success: bool,
        error: str = ""
    ) -> Optional[Path]:
        """
        Record completion of an operation.
        
        Returns checkpoint path if checkpoint was saved, None otherwise.
        """
        if success:
            self.state["success_count"] += 1
            self.state["last_completed_op_id"] = op_id
            self.state["last_completed_index"] = op_index
        else:
            self.state["fail_count"] += 1
            logger.warning(f"❌ Operation {op_id} failed: {error}")
        
        self.ops_since_checkpoint += 1
        
        # Check if we should save checkpoint
        should_save = (
            self.ops_since_checkpoint >= self.checkpoint_interval or
            (time.time() - self.last_checkpoint_timestamp) >= self.checkpoint_time_interval
        )
        
        if should_save:
            return self.save_checkpoint()
        
        return None
    
    def should_save_checkpoint(self) -> bool:
        """Check if checkpoint should be saved now."""
        return (
            self.ops_since_checkpoint >= self.checkpoint_interval or
            (time.time() - self.last_checkpoint_timestamp) >= self.checkpoint_time_interval
        )
    
    def get_resume_point(self) -> Dict:
        """Get the point to resume from."""
        return {
            "resume_from_index": self.state["last_completed_index"] + 1,
            "last_completed_op_id": self.state["last_completed_op_id"],
            "success_count": self.state["success_count"],
            "fail_count": self.state["fail_count"],
            "remaining_ops": self.state["total_ops"] - self.state["success_count"] - self.state["fail_count"]
        }
    
    def finalize(self) -> Path:
        """Save final checkpoint after all operations complete."""
        self.state["end_time"] = datetime.now().isoformat()
        return self.save_checkpoint()


def load_checkpoint(checkpoint_dir: Path) -> Optional[Dict]:
    """
    Load latest checkpoint from directory.
    
    Returns checkpoint state dict or None if no checkpoint exists.
    """
    latest_path = checkpoint_dir / "checkpoint_latest.json"
    
    if not latest_path.exists():
        # Try to find most recent checkpoint
        checkpoints = list(checkpoint_dir.glob("checkpoint_*.json"))
        if not checkpoints:
            return None
        latest_path = max(checkpoints, key=lambda p: p.stat().st_mtime)
    
    with open(latest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def can_resume(checkpoint_dir: Path) -> bool:
    """Check if a resume is possible."""
    return load_checkpoint(checkpoint_dir) is not None


def get_resume_info(checkpoint_dir: Path) -> Optional[Dict]:
    """Get human-readable resume information."""
    checkpoint = load_checkpoint(checkpoint_dir)
    if not checkpoint:
        return None
    
    return {
        "can_resume": True,
        "last_completed_op": checkpoint.get("last_completed_op_id"),
        "last_completed_index": checkpoint.get("last_completed_index", -1),
        "success_count": checkpoint.get("success_count", 0),
        "fail_count": checkpoint.get("fail_count", 0),
        "total_ops": checkpoint.get("total_ops", 0),
        "remaining": checkpoint.get("total_ops", 0) - checkpoint.get("success_count", 0) - checkpoint.get("fail_count", 0),
        "checkpoint_time": checkpoint.get("last_checkpoint_time"),
        "checkpoint_file": checkpoint.get("checkpoint_file")
    }


# Convenience functions for simple usage
_default_logger: Optional[CheckpointLogger] = None

def init_checkpoint(checkpoint_dir: Path, total_ops: int, manifest_path: Path, **kwargs):
    """Initialize default checkpoint logger."""
    global _default_logger
    _default_logger = CheckpointLogger(checkpoint_dir, **kwargs)
    _default_logger.initialize(total_ops, manifest_path)
    return _default_logger

def record_op(op_id: str, op_index: int, success: bool, error: str = ""):
    """Record operation with default logger."""
    if _default_logger:
        return _default_logger.record_operation(op_id, op_index, success, error)
    return None

def get_checkpoint():
    """Get default logger state."""
    if _default_logger:
        return _default_logger.state
    return None

def finalize_checkpoint():
    """Finalize default logger."""
    if _default_logger:
        return _default_logger.finalize()
    return None


if __name__ == "__main__":
    # Test checkpoint system
    import tempfile
    
    logging.basicConfig(level=logging.INFO)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_dir = Path(tmpdir)
        logger = CheckpointLogger(checkpoint_dir, checkpoint_interval=10)
        
        logger.initialize(100, Path("/test/manifest.json"))
        
        # Simulate operations
        for i in range(55):
            success = i % 10 != 0  # Fail every 10th op
            cp = logger.record_operation(f"OP_TEST_{i:04d}", i, success)
            if cp:
                print(f"Checkpoint saved at op {i}: {cp.name}")
        
        # Test resume
        resume_info = get_resume_info(checkpoint_dir)
        print(f"\nResume info: {json.dumps(resume_info, indent=2)}")
        
        # Test load
        checkpoint = load_checkpoint(checkpoint_dir)
        print(f"\nLoaded checkpoint: last_op={checkpoint['last_completed_op_id']}")
