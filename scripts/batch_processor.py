#!/usr/bin/env python3
"""
Batch Processor for MediaAuditOrganizer
Parallel hash computation with ProcessPoolExecutor.
Supports MD5 + SHA256 with memory-efficient streaming.
"""

import hashlib
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
import time


@dataclass
class HashResult:
    """Result of hash computation for a single file."""

    file_path: str
    md5: Optional[str] = None
    sha256: Optional[str] = None
    size_bytes: int = 0
    error: Optional[str] = None
    processing_time_ms: float = 0.0


def compute_file_hashes(
    file_path: str, compute_md5: bool = True, compute_sha256: bool = True
) -> HashResult:
    """
    Compute hashes for a single file using streaming (memory-efficient).

    Args:
        file_path: Path to the file
        compute_md5: Whether to compute MD5 hash
        compute_sha256: Whether to compute SHA256 hash

    Returns:
        HashResult with computed hashes
    """
    start_time = time.time()
    result = HashResult(file_path=file_path)

    try:
        # Get file size
        result.size_bytes = os.path.getsize(file_path)

        # Initialize hash objects
        md5_hash = hashlib.md5() if compute_md5 else None
        sha256_hash = hashlib.sha256() if compute_sha256 else None

        # Stream the file in chunks (64KB chunks for memory efficiency)
        chunk_size = 64 * 1024  # 64KB

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                if md5_hash:
                    md5_hash.update(chunk)
                if sha256_hash:
                    sha256_hash.update(chunk)

        # Get final hash values
        if md5_hash:
            result.md5 = md5_hash.hexdigest()
        if sha256_hash:
            result.sha256 = sha256_hash.hexdigest()

    except Exception as e:
        result.error = str(e)

    result.processing_time_ms = (time.time() - start_time) * 1000
    return result


def calculate_optimal_workers(
    storage_type: str = "SSD", cpu_count: Optional[int] = None
) -> int:
    """
    Calculate optimal number of worker processes.

    Args:
        storage_type: Type of storage (NVMe, SSD, HDD)
        cpu_count: Number of CPU cores (auto-detected if None)

    Returns:
        Optimal worker count
    """
    if cpu_count is None:
        cpu_count = os.cpu_count() or 4

    # Multipliers based on storage type
    multipliers = {
        "NVMe": 4,  # High parallelism for NVMe
        "SSD": 2,  # Good parallelism for SSD
        "HDD": 0.5,  # Limited parallelism for HDD (avoid I/O bottleneck)
    }

    multiplier = multipliers.get(storage_type.upper(), 2)
    workers = int(cpu_count * multiplier)

    # Ensure at least 1 worker, max 32
    return max(1, min(workers, 32))


class BatchProcessor:
    """
    Batch processor for parallel file operations.

    Features:
    - ProcessPoolExecutor for parallel processing
    - Progress tracking with callbacks
    - Memory-efficient streaming hash computation
    - Configurable worker count
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        storage_type: str = "SSD",
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ):
        """
        Initialize batch processor.

        Args:
            max_workers: Maximum number of worker processes (auto-calculated if None)
            storage_type: Storage type for worker calculation (NVMe, SSD, HDD)
            progress_callback: Callback function(current, total) for progress updates
        """
        self.max_workers = max_workers or calculate_optimal_workers(storage_type)
        self.storage_type = storage_type
        self.progress_callback = progress_callback
        self.results: List[HashResult] = []
        self.errors: List[HashResult] = []

    def _update_progress(self, current: int, total: int):
        """Update progress if callback is registered."""
        if self.progress_callback:
            self.progress_callback(current, total)

    def process_files(
        self,
        file_paths: List[str],
        compute_md5: bool = True,
        compute_sha256: bool = True,
    ) -> List[HashResult]:
        """
        Process multiple files in parallel.

        Args:
            file_paths: List of file paths to process
            compute_md5: Whether to compute MD5 hashes
            compute_sha256: Whether to compute SHA256 hashes

        Returns:
            List of HashResult objects
        """
        if not file_paths:
            return []

        total = len(file_paths)
        self.results = []
        self.errors = []

        print(f"🔄 Processing {total} files with {self.max_workers} workers...")
        start_time = time.time()

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(
                    compute_file_hashes, path, compute_md5, compute_sha256
                ): path
                for path in file_paths
            }

            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_path):
                result = future.result()
                self.results.append(result)

                if result.error:
                    self.errors.append(result)

                completed += 1
                self._update_progress(completed, total)

                # Print progress every 10% or for small batches
                if total >= 10:
                    if completed % max(1, total // 10) == 0:
                        elapsed = time.time() - start_time
                        rate = completed / elapsed if elapsed > 0 else 0
                        print(
                            f"   Progress: {completed}/{total} ({rate:.1f} files/sec)"
                        )
                else:
                    print(f"   Processed: {completed}/{total}")

        elapsed = time.time() - start_time
        print(
            f"✅ Completed {len(self.results)} files in {elapsed:.2f}s ({len(self.results)/elapsed:.1f} files/sec)"
        )

        if self.errors:
            print(f"⚠️  {len(self.errors)} files had errors")

        return self.results

    def process_directory(
        self,
        directory: str,
        recursive: bool = True,
        extensions: Optional[List[str]] = None,
        compute_md5: bool = True,
        compute_sha256: bool = True,
    ) -> List[HashResult]:
        """
        Process all files in a directory.

        Args:
            directory: Path to directory
            recursive: Whether to process subdirectories
            extensions: Filter by file extensions (e.g., ['.jpg', '.mp4'])
            compute_md5: Whether to compute MD5 hashes
            compute_sha256: Whether to compute SHA256 hashes

        Returns:
            List of HashResult objects
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        # Collect files
        file_paths = []
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"

        for file_path in dir_path.glob(pattern):
            if file_path.is_file():
                if extensions is None or file_path.suffix.lower() in extensions:
                    file_paths.append(str(file_path))

        print(f"📁 Found {len(file_paths)} files in {directory}")
        return self.process_files(file_paths, compute_md5, compute_sha256)

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        if not self.results:
            return {}

        successful = [r for r in self.results if not r.error]
        total_size = sum(r.size_bytes for r in successful)
        total_time = sum(r.processing_time_ms for r in successful)

        return {
            "total_files": len(self.results),
            "successful": len(successful),
            "errors": len(self.errors),
            "total_size_bytes": total_size,
            "total_size_gb": round(total_size / (1024**3), 3),
            "total_processing_time_ms": round(total_time, 2),
            "avg_processing_time_ms": round(total_time / len(successful), 2)
            if successful
            else 0,
            "throughput_mbps": round(
                (total_size / (1024 * 1024)) / (total_time / 1000), 2
            )
            if total_time > 0
            else 0,
        }


def main():
    """CLI entry point for testing."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Batch hash processor for MediaAuditOrganizer"
    )
    parser.add_argument(
        "path", type=str, help="File or directory to process"
    )
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=None,
        help="Number of worker processes (auto-calculated if not specified)",
    )
    parser.add_argument(
        "--storage-type",
        "-s",
        type=str,
        choices=["NVMe", "SSD", "HDD"],
        default="SSD",
        help="Storage type for worker optimization",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output JSON file for results",
    )
    parser.add_argument(
        "--md5", action="store_true", default=True, help="Compute MD5 (default)"
    )
    parser.add_argument(
        "--sha256", action="store_true", default=True, help="Compute SHA256 (default)"
    )
    parser.add_argument(
        "--no-md5", action="store_true", help="Skip MD5 computation"
    )
    parser.add_argument(
        "--no-sha256", action="store_true", help="Skip SHA256 computation"
    )

    args = parser.parse_args()

    compute_md5 = args.md5 and not args.no_md5
    compute_sha256 = args.sha256 and not args.no_sha256

    path = Path(args.path)

    if not path.exists():
        print(f"❌ Path not found: {path}")
        return 1

    # Create processor
    processor = BatchProcessor(
        max_workers=args.workers,
        storage_type=args.storage_type,
        progress_callback=lambda c, t: None,  # Silent progress
    )

    # Process
    if path.is_file():
        results = processor.process_files([str(path)], compute_md5, compute_sha256)
    else:
        results = processor.process_directory(
            str(path), recursive=True, compute_md5=compute_md5, compute_sha256=compute_sha256
        )

    # Print results
    if results:
        print("\n📊 Results:")
        for result in results[:10]:  # Show first 10
            if result.error:
                print(f"   ❌ {result.file_path}: {result.error}")
            else:
                print(
                    f"   ✓ {result.file_path}: MD5={result.md5[:8]}... SHA256={result.sha256[:8]}..."
                )

        if len(results) > 10:
            print(f"   ... and {len(results) - 10} more files")

    # Print statistics
    stats = processor.get_statistics()
    if stats:
        print(f"\n📈 Statistics:")
        print(f"   Files processed: {stats['total_files']}")
        print(f"   Total size: {stats['total_size_gb']} GB")
        print(f"   Throughput: {stats['throughput_mbps']} MB/s")
        print(f"   Avg time per file: {stats['avg_processing_time_ms']:.2f} ms")

    # Write output
    if args.output:
        output_data = {
            "results": [
                {
                    "file_path": r.file_path,
                    "md5": r.md5,
                    "sha256": r.sha256,
                    "size_bytes": r.size_bytes,
                    "error": r.error,
                    "processing_time_ms": r.processing_time_ms,
                }
                for r in results
            ],
            "statistics": stats,
        }

        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"\n💾 Results saved to: {args.output}")

    return 0


if __name__ == "__main__":
    exit(main())
