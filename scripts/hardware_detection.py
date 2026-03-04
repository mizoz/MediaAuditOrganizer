#!/usr/bin/env python3
"""
Hardware Detection Module for MediaAuditOrganizer
Detects CPU, GPU, RAM, and storage capabilities for optimization.
Outputs: hardware_profile.json
"""

import json
import os
import subprocess
import re
import platform
from pathlib import Path
from typing import Dict, Any, Optional, List


def run_command(cmd: List[str], timeout: int = 10) -> Optional[str]:
    """Run a shell command and return stdout or None on failure."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def detect_cpu() -> Dict[str, Any]:
    """Detect CPU information."""
    cpu_info = {
        "model": "Unknown",
        "vendor": "Unknown",
        "cores": 0,
        "threads": 0,
        "sockets": 0,
        "flags": [],
        "avx_support": False,
        "avx2_support": False,
        "avx512_support": False,
    }

    # Get CPU count
    cpu_info["threads"] = os.cpu_count() or 0

    # Read /proc/cpuinfo for Linux
    try:
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()

        # Extract model name
        model_match = re.search(r"model name\s*:\s*(.+)", cpuinfo)
        if model_match:
            cpu_info["model"] = model_match.group(1).strip()

        # Extract vendor
        vendor_match = re.search(r"vendor_id\s*:\s*(.+)", cpuinfo)
        if vendor_match:
            cpu_info["vendor"] = vendor_match.group(1).strip()

        # Count physical cores (unique core IDs)
        core_ids = set(re.findall(r"core id\s*:\s*(\d+)", cpuinfo))
        cpu_info["cores"] = len(core_ids) if core_ids else cpu_info["threads"] // 2

        # Count sockets
        physical_ids = set(re.findall(r"physical id\s*:\s*(\d+)", cpuinfo))
        cpu_info["sockets"] = len(physical_ids) if physical_ids else 1

        # Extract flags from first processor
        flags_match = re.search(r"flags\s*:\s*(.+)", cpuinfo)
        if flags_match:
            flags = flags_match.group(1).strip().split()
            cpu_info["flags"] = flags
            cpu_info["avx_support"] = "avx" in flags
            cpu_info["avx2_support"] = "avx2" in flags
            cpu_info["avx512_support"] = any("avx512" in f for f in flags)

    except FileNotFoundError:
        # Fallback for non-Linux systems
        cpu_info["cores"] = cpu_info["threads"] // 2

    return cpu_info


def detect_gpu() -> Dict[str, Any]:
    """Detect GPU information and encoder support."""
    gpu_info = {
        "vendor": "Unknown",
        "model": "Unknown",
        "vram_mb": 0,
        "drivers_installed": [],
        "ffmpeg_encoders": [],
        "nvenc_available": False,
        "amf_available": False,
        "qsv_available": False,
        "vaapi_available": False,
        "videotoolbox_available": False,
    }

    # Check NVIDIA first (highest priority for dedicated GPUs)
    nvidia_smi = run_command(["nvidia-smi", "-L"])
    if nvidia_smi:
        gpu_info["vendor"] = "NVIDIA"
        gpu_info["drivers_installed"].append("nvidia")
        # Parse GPU model - format: "GPU 0: NVIDIA GeForce GTX 960 (UUID: ...)"
        model_match = re.search(r"GPU \d+: (NVIDIA [^\(]+)", nvidia_smi)
        if model_match:
            gpu_info["model"] = model_match.group(1).strip()
        else:
            # Fallback: try simpler pattern
            model_match = re.search(r"GPU \d+: (.+?) \(UUID", nvidia_smi)
            if model_match:
                gpu_info["model"] = model_match.group(1).strip()
        # Parse VRAM from nvidia-smi -q
        nvidia_query = run_command(["nvidia-smi", "-q", "-i", "0"])
        if nvidia_query:
            vram_match = re.search(r"FB Memory Usage\s*:\s*Total\s*:\s*(\d+)\s*MiB", nvidia_query)
            if vram_match:
                gpu_info["vram_mb"] = int(vram_match.group(1))

    # Check AMD ROCm (only if no NVIDIA found)
    if gpu_info["vendor"] == "Unknown":
        rocm_smi = run_command(["rocm-smi", "--showproductname"])
        if rocm_smi:
            gpu_info["vendor"] = "AMD"
            gpu_info["drivers_installed"].append("rocm")
            # Simplified model detection
            if "AMD" in rocm_smi:
                gpu_info["model"] = "AMD Radeon (ROCm)"

    # Check Intel integrated GPU via lspci (only if no dedicated GPU found)
    if gpu_info["vendor"] == "Unknown":
        lspci_vga = run_command(["lspci", "-v"])
        if lspci_vga:
            # Look for VGA compatible controller with Intel
            for line in lspci_vga.split("\n"):
                if "VGA compatible controller" in line and "Intel" in line:
                    gpu_info["vendor"] = "Intel"
                    gpu_info["drivers_installed"].append("intel")
                    intel_match = re.search(r"Intel Corporation ([^(]+)", line)
                    if intel_match:
                        gpu_info["model"] = intel_match.group(1).strip()
                    break

    # Check ffmpeg hardware encoders
    ffmpeg_encoders = run_command(["ffmpeg", "-encoders"])
    if ffmpeg_encoders:
        if "nvenc" in ffmpeg_encoders:
            gpu_info["ffmpeg_encoders"].append("h264_nvenc")
            gpu_info["ffmpeg_encoders"].append("hevc_nvenc")
            gpu_info["nvenc_available"] = True
        if "amf" in ffmpeg_encoders:
            gpu_info["ffmpeg_encoders"].append("h264_amf")
            gpu_info["ffmpeg_encoders"].append("hevc_amf")
            gpu_info["amf_available"] = True
        if "qsv" in ffmpeg_encoders:
            gpu_info["ffmpeg_encoders"].append("h264_qsv")
            gpu_info["ffmpeg_encoders"].append("hevc_qsv")
            gpu_info["qsv_available"] = True
        if "vaapi" in ffmpeg_encoders:
            gpu_info["ffmpeg_encoders"].append("h264_vaapi")
            gpu_info["ffmpeg_encoders"].append("hevc_vaapi")
            gpu_info["vaapi_available"] = True
        if "videotoolbox" in ffmpeg_encoders:
            gpu_info["ffmpeg_encoders"].append("h264_videotoolbox")
            gpu_info["videotoolbox_available"] = True

    return gpu_info


def detect_ram() -> Dict[str, Any]:
    """Detect RAM information."""
    ram_info = {
        "total_gb": 0,
        "available_gb": 0,
        "used_gb": 0,
        "percent_available": 0,
    }

    try:
        import psutil
        mem = psutil.virtual_memory()
        ram_info["total_gb"] = round(mem.total / (1024**3), 2)
        ram_info["available_gb"] = round(mem.available / (1024**3), 2)
        ram_info["used_gb"] = round(mem.used / (1024**3), 2)
        ram_info["percent_available"] = round(mem.available / mem.total * 100, 1)
    except ImportError:
        # Fallback: read /proc/meminfo
        try:
            with open("/proc/meminfo", "r") as f:
                meminfo = f.read()

            total_match = re.search(r"MemTotal:\s+(\d+)\s+kB", meminfo)
            avail_match = re.search(r"MemAvailable:\s+(\d+)\s+kB", meminfo)

            if total_match:
                ram_info["total_gb"] = round(int(total_match.group(1)) / 1024**2, 2)
            if avail_match:
                ram_info["available_gb"] = round(int(avail_match.group(1)) / 1024**2, 2)
                ram_info["used_gb"] = round(
                    ram_info["total_gb"] - ram_info["available_gb"], 2
                )
        except FileNotFoundError:
            pass

    return ram_info


def detect_storage() -> List[Dict[str, Any]]:
    """Detect storage devices and their types."""
    storage_devices = []

    # Use lsblk to get block devices
    lsblk_output = run_command(
        ["lsblk", "-o", "NAME,TYPE,MODEL,SIZE,ROTATIONAL,MOUNTPOINT", "-n", "-d"]
    )

    if not lsblk_output:
        return storage_devices

    for line in lsblk_output.strip().split("\n"):
        if not line.strip():
            continue

        parts = line.split()
        if len(parts) < 5:
            continue

        device = {
            "name": parts[0],
            "type": parts[1],
            "model": parts[2] if len(parts) > 2 else "Unknown",
            "size": parts[3] if len(parts) > 3 else "Unknown",
            "is_rotational": parts[4] == "1" if len(parts) > 4 else False,
            "mount_point": parts[5] if len(parts) > 5 else None,
            "storage_type": "Unknown",
        }

        # Determine storage type
        if device["type"] == "disk":
            # NVMe detection
            if "nvme" in device["name"].lower():
                device["storage_type"] = "NVMe"
            # SSD vs HDD detection
            elif device["is_rotational"]:
                device["storage_type"] = "HDD"
            else:
                # Check model name for SSD indicators
                model_lower = device["model"].lower()
                if any(
                    x in model_lower
                    for x in ["ssd", "solid", "nvme", "m.2", "sata ssd"]
                ):
                    device["storage_type"] = "SSD"
                else:
                    device["storage_type"] = "SSD"  # Default non-rotational to SSD

        storage_devices.append(device)

    return storage_devices


def detect_network() -> Dict[str, Any]:
    """Detect network interface information."""
    network_info = {
        "interfaces": [],
        "primary_interface": None,
        "estimated_bandwidth_mbps": 0,
    }

    # Get interface list
    ip_output = run_command(["ip", "-o", "link", "show"])
    if ip_output:
        for line in ip_output.strip().split("\n"):
            match = re.search(r"\d+:\s+(\w+):", line)
            if match:
                iface = match.group(1)
                if iface != "lo":  # Skip loopback
                    network_info["interfaces"].append(iface)

    # Try to estimate bandwidth from interface name
    if network_info["interfaces"]:
        # Assume primary interface is first non-lo
        network_info["primary_interface"] = network_info["interfaces"][0]

        # Rough bandwidth estimation based on interface naming
        iface = network_info["primary_interface"].lower()
        if "eth" in iface or "enp" in iface:
            network_info["estimated_bandwidth_mbps"] = 1000  # Assume 1Gbps
        elif "wl" in iface or "wlan" in iface:
            network_info["estimated_bandwidth_mbps"] = 300  # Assume WiFi

    return network_info


def detect_smartctl() -> bool:
    """Check if smartctl is available."""
    return run_command(["which", "smartctl"]) is not None


def calculate_recommended_workers(
    cpu_cores: int, storage_type: str, ram_gb: float
) -> Dict[str, int]:
    """Calculate optimal worker counts based on hardware."""
    # Base calculation on CPU cores
    base_workers = cpu_cores

    # Adjust based on storage type
    if storage_type == "NVMe":
        # NVMe can handle high parallelism
        multiplier = 4
    elif storage_type == "SSD":
        # SSD can handle good parallelism
        multiplier = 2
    else:  # HDD
        # HDD needs limited parallelism to avoid I/O bottleneck
        multiplier = 0.5

    # Adjust based on available RAM (ensure we don't exceed memory)
    # Assume ~500MB per worker for hash operations
    max_workers_by_ram = int(ram_gb * 2)  # 2 workers per GB as safety limit

    optimal_workers = int(base_workers * multiplier)
    optimal_workers = min(optimal_workers, max_workers_by_ram)
    optimal_workers = max(optimal_workers, 1)  # At least 1 worker

    return {
        "metadata_extraction_workers": optimal_workers,
        "duplicate_detection_workers": max(optimal_workers // 2, 1),
        "transfer_workers": min(optimal_workers, 8),  # Cap at 8 for network
        "batch_size": optimal_workers * 10,  # 10 files per worker per batch
    }


def detect_all() -> Dict[str, Any]:
    """Run all detection routines and return complete profile."""
    print("🔍 Detecting hardware capabilities...")

    cpu = detect_cpu()
    print(f"  ✓ CPU: {cpu['model']} ({cpu['cores']} cores, {cpu['threads']} threads)")

    gpu = detect_gpu()
    print(f"  ✓ GPU: {gpu['vendor']} {gpu['model']} ({gpu['vram_mb']}MB VRAM)")

    ram = detect_ram()
    print(f"  ✓ RAM: {ram['total_gb']}GB total, {ram['available_gb']}GB available")

    storage = detect_storage()
    storage_types = set(d["storage_type"] for d in storage if d["type"] == "disk")
    print(f"  ✓ Storage: {', '.join(storage_types) if storage_types else 'Unknown'}")

    network = detect_network()
    print(
        f"  ✓ Network: {network['primary_interface']} (~{network['estimated_bandwidth_mbps']}Mbps)"
    )

    smartctl_available = detect_smartctl()
    print(f"  ✓ smartctl: {'Available' if smartctl_available else 'NOT INSTALLED'}")

    # Determine primary storage type for worker calculation
    primary_storage = "SSD"  # Default
    for device in storage:
        if device["type"] == "disk" and device["mount_point"] == "/":
            primary_storage = device["storage_type"]
            break

    # Calculate recommended settings
    recommended = calculate_recommended_workers(
        cpu["cores"], primary_storage, ram["available_gb"]
    )

    profile = {
        "detected_at": subprocess.run(
            ["date", "+%Y-%m-%d %H:%M:%S"], capture_output=True, text=True
        ).stdout.strip(),
        "system": {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "cpu": cpu,
        "gpu": gpu,
        "ram": ram,
        "storage": storage,
        "network": network,
        "smartctl_available": smartctl_available,
        "recommended_settings": recommended,
        "hardware_acceleration_summary": {
            "gpu_encoding_available": any(
                [
                    gpu["nvenc_available"],
                    gpu["amf_available"],
                    gpu["qsv_available"],
                    gpu["vaapi_available"],
                ]
            ),
            "nvenc": gpu["nvenc_available"],
            "amf": gpu["amf_available"],
            "qsv": gpu["qsv_available"],
            "vaapi": gpu["vaapi_available"],
            "videotoolbox": gpu["videotoolbox_available"],
            "fast_thumbnailing_supported": True,  # All ffmpeg versions support I-frame extraction
        },
    }

    return profile


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect hardware capabilities for MediaAuditOrganizer"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="hardware_profile.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress progress output"
    )

    args = parser.parse_args()

    if args.quiet:
        import sys

        sys.stdout = open(os.devnull, "w")

    profile = detect_all()

    # Write to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(profile, f, indent=2)

    print(f"\n✅ Hardware profile saved to: {output_path}")
    print(f"\n📊 Recommended Settings:")
    for key, value in profile["recommended_settings"].items():
        print(f"   {key}: {value}")

    if not profile["smartctl_available"]:
        print(
            "\n⚠️  WARNING: smartctl not installed. Install with: sudo apt install smartmontools"
        )

    if not profile["hardware_acceleration_summary"]["gpu_encoding_available"]:
        print(
            "\n⚠️  NOTE: No GPU hardware encoders detected in ffmpeg."
        )
        print(
            "   Fast I-frame thumbnailing will still work, but GPU encoding unavailable."
        )

    return profile


if __name__ == "__main__":
    main()
