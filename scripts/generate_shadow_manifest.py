#!/usr/bin/env python3
"""
Generate shadow manifest from rename preview CSV.
Creates entries for first 500 files with pending status.
"""

import csv
import json
from datetime import datetime
from pathlib import Path

def generate_shadow_manifest(csv_path: Path, output_path: Path, limit: int = 500):
    """Generate shadow manifest JSON from CSV."""
    
    base_timestamp = datetime.now()
    operations = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader):
            if idx >= limit:
                break
            
            # Generate operation ID: OP_YYYYMMDD_HHMMSS_SEQ
            op_timestamp = base_timestamp
            op_id = f"OP_{op_timestamp.strftime('%Y%m%d_%H%M%S')}_{idx+1:04d}"
            
            operation = {
                "operation_id": op_id,
                "original_path": row.get('old_path', ''),
                "new_path": row.get('new_path', ''),
                "hash_before": "",  # Will be computed during transfer
                "hash_after": "",   # Will be computed after transfer
                "timestamp": op_timestamp.isoformat(),
                "status": "pending",
                "file_size": 0,
                "error": "",
                "rolled_back": False
            }
            operations.append(operation)
    
    manifest = {
        "metadata": {
            "created": base_timestamp.isoformat(),
            "version": "1.0",
            "total_operations": len(operations),
            "sample_scope": "first_500_files",
            "source_drive": "/media/az/drive64gb",
            "description": "Shadow manifest for checkpoint/rollback system - Phase 2 sample transfer"
        },
        "operations": operations
    }
    
    # Write manifest
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✅ Generated shadow manifest: {output_path}")
    print(f"   Total operations: {len(operations)}")
    print(f"   All status: pending")
    
    return manifest

if __name__ == "__main__":
    csv_path = Path(__file__).parent.parent / "08_REPORTS/rename_preview_20260303.csv"
    output_path = Path(__file__).parent.parent / "06_METADATA/shadow_manifest_20260304.json"
    
    generate_shadow_manifest(csv_path, output_path, limit=500)
