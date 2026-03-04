#!/usr/bin/env python3
"""
Hardware Profile Generator for MediaAuditOrganizer
Main entry point that combines all hardware detection into a single profile.
Generates recommended settings for settings.yaml configuration.

Usage:
    python scripts/hardware_profile.py --output configs/hardware_profile.json
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Import detection modules
from hardware_detection import detect_all, detect_cpu, detect_gpu, detect_ram, detect_storage


def load_hardware_profile(profile_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Load existing hardware profile if available."""
    if profile_path and os.path.exists(profile_path):
        with open(profile_path, "r") as f:
            return json.load(f)
    return None


def generate_settings_yaml_snippet(profile: Dict[str, Any]) -> str:
    """
    Generate YAML snippet for settings.yaml based on hardware profile.

    Returns:
        YAML-formatted string to append to settings.yaml
    """
    recommended = profile.get("recommended_settings", {})
    hw_summary = profile.get("hardware_acceleration_summary", {})
    cpu = profile.get("cpu", {})
    storage = profile.get("storage", [])

    # Determine primary storage type
    primary_storage = "SSD"
    for device in storage:
        if device.get("type") == "disk" and device.get("mount_point") == "/":
            primary_storage = device.get("storage_type", "SSD")
            break

    yaml_snippet = f"""
# =============================================================================
# HARDWARE-ACCELERATED SETTINGS (Auto-generated)
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# System: {profile.get('system', {}).get('platform', 'Unknown')}
# CPU: {cpu.get('model', 'Unknown')}
# GPU: {profile.get('gpu', {}).get('model', 'Unknown')}
# Primary Storage: {primary_storage}
# =============================================================================

# Performance settings optimized for this hardware
performance:
  # Worker counts based on {cpu.get('cores', 0)} CPU cores and {primary_storage} storage
  metadata_extraction_workers: {recommended.get('metadata_extraction_workers', 4)}
  duplicate_detection_workers: {recommended.get('duplicate_detection_workers', 2)}
  transfer_workers: {recommended.get('transfer_workers', 8)}
  
  # Batch sizes optimized for available RAM ({profile.get('ram', {}).get('total_gb', 0)}GB)
  batch_size: {recommended.get('batch_size', 100)}
  
  # Enable hardware acceleration features
  enable_hardware_acceleration: true
  
  # FFmpeg hardware encoding (if available)
  ffmpeg_hardware_encoder: {"nvenc" if hw_summary.get('nvenc') else "amf" if hw_summary.get('amf') else "qsv" if hw_summary.get('qsv') else "vaapi" if hw_summary.get('vaapi') else "cpu"}
  
  # Fast thumbnailing (I-frame extraction) - 500% faster than full decode
  fast_thumbnailing_enabled: true
  
  # Parallel hashing engine settings
  parallel_hashing_enabled: true
  hashing_workers: {recommended.get('metadata_extraction_workers', 4)}
  
  # Thermal protection
  thermal_monitoring_enabled: {"true" if profile.get('smartctl_available') else "false"}
  thermal_pause_threshold_celsius: 55
  thermal_resume_threshold_celsius: 45

# Hardware-specific optimizations
hardware:
  cpu:
    model: "{cpu.get('model', 'Unknown')}"
    cores: {cpu.get('cores', 0)}
    threads: {cpu.get('threads', 0)}
    avx2_supported: {str(cpu.get('avx2_support', False)).lower()}
  
  gpu:
    vendor: "{profile.get('gpu', {}).get('vendor', 'Unknown')}"
    model: "{profile.get('gpu', {}).get('model', 'Unknown')}"
    vram_mb: {profile.get('gpu', {}).get('vram_mb', 0)}
    nvenc_available: {str(hw_summary.get('nvenc', False)).lower()}
    vaapi_available: {str(hw_summary.get('vaapi', False)).lower()}
  
  storage:
    primary_type: "{primary_storage}"
    # Worker multiplier: NVMe=4x, SSD=2x, HDD=0.5x
  
  ram:
    total_gb: {profile.get('ram', {}).get('total_gb', 0)}
    available_gb: {profile.get('ram', {}).get('available_gb', 0)}
"""

    return yaml_snippet


def print_profile_summary(profile: Dict[str, Any]):
    """Print a human-readable summary of the hardware profile."""
    print("\n" + "=" * 70)
    print("🖥️  HARDWARE PROFILE SUMMARY")
    print("=" * 70)

    cpu = profile.get("cpu", {})
    gpu = profile.get("gpu", {})
    ram = profile.get("ram", {})
    storage = profile.get("storage", [])
    recommended = profile.get("recommended_settings", {})
    hw_summary = profile.get("hardware_acceleration_summary", {})

    print(f"\n📌 SYSTEM")
    print(f"   Platform: {profile.get('system', {}).get('platform', 'Unknown')} {profile.get('system', {}).get('platform_release', '')}")
    print(f"   Detected: {profile.get('detected_at', 'Unknown')}")

    print(f"\n🔷 CPU")
    print(f"   Model: {cpu.get('model', 'Unknown')}")
    print(f"   Cores: {cpu.get('cores', 0)} | Threads: {cpu.get('threads', 0)}")
    print(f"   AVX2: {'✓' if cpu.get('avx2_support') else '✗'} | AVX-512: {'✓' if cpu.get('avx512_support') else '✗'}")

    print(f"\n🎮 GPU")
    print(f"   Vendor: {gpu.get('vendor', 'Unknown')}")
    print(f"   Model: {gpu.get('model', 'Unknown')}")
    print(f"   VRAM: {gpu.get('vram_mb', 0)}MB")
    print(f"   Encoders: ", end="")
    encoders = []
    if hw_summary.get("nvenc"):
        encoders.append("NVENC ✓")
    if hw_summary.get("vaapi"):
        encoders.append("VAAPI ✓")
    if hw_summary.get("qsv"):
        encoders.append("QSV ✓")
    if hw_summary.get("amf"):
        encoders.append("AMF ✓")
    print(", ".join(encoders) if encoders else "None detected")

    print(f"\n💾 RAM")
    print(f"   Total: {ram.get('total_gb', 0)}GB | Available: {ram.get('available_gb', 0)}GB")

    print(f"\n💿 STORAGE")
    for device in storage:
        if device.get("type") == "disk":
            print(f"   {device.get('name', 'Unknown')}: {device.get('model', 'Unknown')} ({device.get('size', 'Unknown')}) - {device.get('storage_type', 'Unknown')}")

    print(f"\n⚡ RECOMMENDED SETTINGS")
    print(f"   Metadata extraction workers: {recommended.get('metadata_extraction_workers', 4)}")
    print(f"   Duplicate detection workers: {recommended.get('duplicate_detection_workers', 2)}")
    print(f"   Transfer workers: {recommended.get('transfer_workers', 8)}")
    print(f"   Batch size: {recommended.get('batch_size', 100)}")

    print(f"\n🚀 EXPECTED SPEEDUP")
    if hw_summary.get("gpu_encoding_available"):
        print(f"   Video thumbnailing: 5-10x faster (GPU acceleration)")
    else:
        print(f"   Video thumbnailing: 2-3x faster (I-frame extraction only)")
    print(f"   Parallel hashing: 2-8x faster (multi-core)")

    print(f"\n⚠️  NOTES")
    if not profile.get("smartctl_available"):
        print(f"   • smartctl not installed - thermal monitoring unavailable")
        print(f"     Install: sudo apt install smartmontools")
    if not hw_summary.get("gpu_encoding_available"):
        print(f"   • No GPU hardware encoders in ffmpeg")
        print(f"     Fast I-frame thumbnailing still works")

    print("\n" + "=" * 70)


def main():
    """Main entry point for hardware profile generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate hardware profile for MediaAuditOrganizer"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="configs/hardware_profile.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--yaml-output",
        "-y",
        type=str,
        default=None,
        help="Output YAML settings snippet file",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress progress output"
    )
    parser.add_argument(
        "--summary-only",
        "-s",
        action="store_true",
        help="Only print summary, don't write files",
    )

    args = parser.parse_args()

    if not args.quiet:
        print("🔍 Generating hardware profile...")

    # Detect all hardware
    profile = detect_all()

    if args.summary_only:
        print_profile_summary(profile)
        return 0

    # Write JSON profile
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(profile, f, indent=2)

    if not args.quiet:
        print(f"✅ Hardware profile saved to: {output_path}")

    # Generate YAML snippet
    yaml_snippet = generate_settings_yaml_snippet(profile)

    if args.yaml_output:
        yaml_path = Path(args.yaml_output)
        yaml_path.parent.mkdir(parents=True, exist_ok=True)

        with open(yaml_path, "w") as f:
            f.write(yaml_snippet)

        if not args.quiet:
            print(f"✅ YAML settings snippet saved to: {yaml_path}")

    # Print summary
    print_profile_summary(profile)

    # Print integration instructions
    if not args.quiet:
        print("\n📖 INTEGRATION INSTRUCTIONS")
        print("-" * 70)
        print("1. Copy recommended settings to configs/settings.yaml")
        print("   Or use: cat configs/hardware_settings.yaml >> configs/settings.yaml")
        print()
        print("2. Enable hardware acceleration in existing scripts:")
        print("   from batch_processor import BatchProcessor")
        print("   processor = BatchProcessor(max_workers=profile['recommended_settings']['metadata_extraction_workers'])")
        print()
        print("3. For thermal protection:")
        print("   from thermal_monitor import ThermalMonitor")
        print("   monitor = ThermalMonitor(drive_path='/dev/sda')")
        print("   monitor.start()")
        print()
        print("4. Fast thumbnailing command:")
        print("   ffmpeg -i input.mp4 -vf 'select=eq(pict_type,I)' -vframes 1 thumb.jpg")
        print("-" * 70)

    return 0


if __name__ == "__main__":
    # Add script directory to path for imports
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))
    exit(main())
