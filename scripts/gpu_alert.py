#!/usr/bin/env python3
"""
GPU Alert System for MediaAuditOrganizer
SA-22: Hardware Acceleration Mandate

Generates alerts when GPU acceleration is not available.
DO NOT PROCEED WITH TRANSFER IF GPU MISSING.
"""

import logging
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("GPUAlert")


class GPUAlertGenerator:
    """
    Generates GPU enforcement alerts.

    When GPU is not available, writes GPU_NOT_FOUND_ALERT.md with:
    - System information
    - Detection results
    - Missing drivers/software
    - Installation instructions
    """

    def __init__(self, workspace_path: str):
        """
        Initialize alert generator.

        Args:
            workspace_path: Path to MediaAuditOrganizer workspace
        """
        self.workspace_path = Path(workspace_path)
        self.alert_path = self.workspace_path / "GPU_NOT_FOUND_ALERT.md"

    def _run_command(self, args: list, timeout: int = 10) -> tuple:
        """Run shell command and return result."""
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def _get_system_info(self) -> dict:
        """Gather system information."""
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "timestamp": datetime.now().isoformat(),
        }

        # Get ffmpeg version
        success, stdout, stderr = self._run_command(["ffmpeg", "-version"])
        if success:
            info["ffmpeg_version"] = stdout.split("\n")[0]
        else:
            info["ffmpeg_version"] = "NOT FOUND"

        # Check for NVIDIA
        success, stdout, stderr = self._run_command(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"])
        if success and stdout.strip():
            parts = stdout.strip().split(", ")
            info["nvidia_gpu"] = parts[0] if len(parts) > 0 else "Unknown"
            info["nvidia_driver"] = parts[1] if len(parts) > 1 else "Unknown"
        else:
            info["nvidia_gpu"] = "NOT DETECTED"
            info["nvidia_driver"] = "N/A"

        # Check for AMD
        success, stdout, stderr = self._run_command(["rocm-smi", "--showproductname"])
        if success:
            info["amd_gpu"] = "DETECTED (ROCm)"
        else:
            success, stdout, stderr = self._run_command(["lspci"])
            if success and "AMD" in stdout:
                info["amd_gpu"] = "DETECTED (PCI)"
            else:
                info["amd_gpu"] = "NOT DETECTED"

        # Check for Intel GPU
        success, stdout, stderr = self._run_command(["lspci"])
        if success and ("Intel" in stdout or "i915" in stdout):
            info["intel_gpu"] = "DETECTED"
        else:
            info["intel_gpu"] = "NOT DETECTED"

        return info

    def _get_ffmpeg_encoder_info(self) -> dict:
        """Get FFmpeg encoder information."""
        info = {
            "nvenc_available": False,
            "amf_available": False,
            "videotoolbox_available": False,
            "qsv_available": False,
            "vaapi_available": False,
        }

        success, stdout, stderr = self._run_command(["ffmpeg", "-encoders"])
        if not success:
            return info

        output = stdout + stderr
        info["nvenc_available"] = "h264_nvenc" in output.lower()
        info["amf_available"] = "h264_amf" in output.lower()
        info["videotoolbox_available"] = "h264_videotoolbox" in output.lower()
        info["qsv_available"] = "h264_qsv" in output.lower()
        info["vaapi_available"] = "h264_vaapi" in output.lower()

        return info

    def _get_install_instructions(self, system_info: dict, encoder_info: dict) -> str:
        """Generate installation instructions based on system."""
        instructions = []

        # Check if NVIDIA GPU present but NVENC missing
        if system_info.get("nvidia_gpu") != "NOT DETECTED" and not encoder_info["nvenc_available"]:
            instructions.append("""
## NVIDIA GPU Detected but NVENC Not Available

Your system has an NVIDIA GPU, but FFmpeg was not compiled with NVENC support.

### Solution: Recompile FFmpeg with NVENC

1. **Install NVIDIA Video Codec SDK:**
   ```bash
   # Download from: https://developer.nvidia.com/video-codec-sdk
   # Extract to /opt/nvidia-video-codec-sdk
   ```

2. **Install build dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y build-essential yasm cmake libtool libc6 libc6-dev \
       libva-dev libvdpau-dev libx11-dev libxext-dev libxfixes-dev \
       libavcodec-dev libavformat-dev libavutil-dev
   ```

3. **Download and compile FFmpeg with NVENC:**
   ```bash
   cd /tmp
   git clone https://github.com/FFmpeg/FFmpeg.git
   cd FFmpeg
   ./configure --enable-nonfree --enable-nvenc --enable-cuda-llvm \
       --enable-libnpp --extra-cflags=-I/opt/nvidia-video-codec-sdk/Interfaces \
       --extra-ldflags=-L/opt/nvidia-video-codec-sdk/Lib/x64
   make -j$(nproc)
   sudo make install
   ```

4. **Verify NVENC is available:**
   ```bash
   ffmpeg -encoders | grep nvenc
   # Should show: h264_nvenc, hevc_nvenc
   ```

### Alternative: Use Pre-built FFmpeg with NVENC

```bash
# Using conda
conda install -c conda-forge ffmpeg

# Or download from: https://johnvansickle.com/ffmpeg/
# Look for builds with NVENC support
```
""")

        # If no GPU detected at all
        elif (system_info.get("nvidia_gpu") == "NOT DETECTED" and
              system_info.get("amd_gpu") == "NOT DETECTED" and
              system_info.get("intel_gpu") == "NOT DETECTED"):
            instructions.append("""
## No GPU Detected

Your system does not have a supported GPU for hardware acceleration.

### Options:

1. **Add a supported GPU:**
   - NVIDIA: GTX 10-series or newer (GTX 1650, RTX 2060, etc.)
   - AMD: RX 500-series or newer with VCE/VCN support
   - Intel: 6th gen or newer with Quick Sync

2. **Use a different machine:**
   - Transfer processing to a machine with GPU acceleration
   - Consider cloud instances (AWS G4, Azure NVv4, etc.)

3. **Request exception (NOT RECOMMENDED):**
   - Contact project maintainer for SA-22 waiver
   - Understand performance will be severely degraded
""")

        # AMD GPU but AMF missing
        elif system_info.get("amd_gpu") != "NOT DETECTED" and not encoder_info["amf_available"]:
            instructions.append("""
## AMD GPU Detected but AMF Not Available

Your system has an AMD GPU, but FFmpeg was not compiled with AMF support.

### Solution: Recompile FFmpeg with AMF

1. **Install AMD AMF SDK:**
   ```bash
   # Download from: https://github.com/GPUOpen-LibrariesAndSDKs/AMF
   git clone https://github.com/GPUOpen-LibrariesAndSDKs/AMF.git
   ```

2. **Compile FFmpeg with AMF:**
   ```bash
   cd /tmp
   git clone https://github.com/FFmpeg/FFmpeg.git
   cd FFmpeg
   ./configure --enable-amf --extra-cflags=-I../AMF/amf/public/include \
       --extra-ldflags=-L../AMF/bin/x64
   make -j$(nproc)
   sudo make install
   ```
""")

        # Intel GPU but QSV/VAAPI missing
        elif system_info.get("intel_gpu") != "NOT DETECTED" and not encoder_info["qsv_available"]:
            instructions.append("""
## Intel GPU Detected but QSV Not Available

Your system has an Intel GPU, but FFmpeg was not compiled with QSV support.

### Solution: Install VAAPI and QSV support

```bash
# Install VAAPI drivers
sudo apt-get install -y vainfo intel-media-va-driver-non-free libmfx1

# Verify VAAPI
vainfo

# Recompile FFmpeg with QSV
cd /tmp
git clone https://github.com/FFmpeg/FFmpeg.git
cd FFmpeg
./configure --enable-qsv --enable-vaapi --enable-libmfx
make -j$(nproc)
sudo make install
```
""")

        return "\n".join(instructions) if instructions else "No specific instructions available."

    def generate_alert(
        self,
        gpu_detected: bool = False,
        gpu_vendor: str = "Unknown",
        available_encoders: list = None,
        reason: str = "GPU acceleration not available",
    ) -> str:
        """
        Generate GPU alert markdown document.

        Args:
            gpu_detected: Whether GPU was detected
            gpu_vendor: GPU vendor name
            available_encoders: List of available hardware encoders
            reason: Reason for alert

        Returns:
            Alert markdown content
        """
        system_info = self._get_system_info()
        encoder_info = self._get_ffmpeg_encoder_info()
        install_instructions = self._get_install_instructions(system_info, encoder_info)

        alert_content = f"""# 🚨 GPU NOT FOUND ALERT - SA-22 Hardware Acceleration Mandate

**Generated:** {system_info['timestamp']}
**Status:** BLOCKED - Cannot proceed with video processing

---

## ⚠️ CRITICAL: Hardware Acceleration Required

Per **SA-22 (Hardware Acceleration Mandate)**, software encoding (libx264) is **FORBIDDEN** for MediaAuditOrganizer.

**Reason for Alert:** {reason}

---

## System Information

| Component | Value |
|-----------|-------|
| Operating System | {system_info['os']} {system_info['os_version']} |
| Architecture | {system_info['machine']} |
| Processor | {system_info['processor']} |
| Python Version | {system_info['python_version']} |
| FFmpeg Version | {system_info['ffmpeg_version']} |

### GPU Detection Results

| GPU Type | Status |
|----------|--------|
| NVIDIA | {system_info.get('nvidia_gpu', 'N/A')} (Driver: {system_info.get('nvidia_driver', 'N/A')}) |
| AMD | {system_info.get('amd_gpu', 'N/A')} |
| Intel | {system_info.get('intel_gpu', 'N/A')} |

### FFmpeg Hardware Encoder Support

| Encoder | Available |
|---------|-----------|
| h264_nvenc (NVIDIA) | {'✅ YES' if encoder_info['nvenc_available'] else '❌ NO'} |
| h264_amf (AMD) | {'✅ YES' if encoder_info['amf_available'] else '❌ NO'} |
| h264_qsv (Intel) | {'✅ YES' if encoder_info['qsv_available'] else '❌ NO'} |
| h264_vaapi (VAAPI) | {'✅ YES' if encoder_info['vaapi_available'] else '❌ NO'} |
| h264_videotoolbox (Apple) | {'✅ YES' if encoder_info['videotoolbox_available'] else '❌ NO'} |

---

## Detection Summary

- **GPU Detected:** {'YES' if gpu_detected else 'NO'}
- **GPU Vendor:** {gpu_vendor}
- **Available Hardware Encoders:** {', '.join(available_encoders) if available_encoders else 'NONE'}
- **Software Fallback (libx264):** ❌ FORBIDDEN per SA-22

---

## Resolution Instructions

{install_instructions}

---

## Next Steps

1. **Follow installation instructions above** to enable hardware encoding
2. **Verify encoder availability:**
   ```bash
   ffmpeg -encoders | grep -E "(nvenc|amf|qsv|vaapi|videotoolbox)"
   ```
3. **Re-run GPU enforcement check:**
   ```bash
   python scripts/gpu_enforcer.py --test
   ```
4. **Once GPU is available, processing will automatically resume**

---

## Contact

If you need assistance:
- Review SA-22 documentation: `/workspace/AZ_Projects/MediaAuditOrganizer/SOUL.md`
- Check hardware detection results: `hardware_detection_result.json`
- Run diagnostic: `python scripts/gpu_enforcer.py -v`

---

**DO NOT PROCEED WITH VIDEO TRANSFER UNTIL GPU ACCELERATION IS AVAILABLE**

*This alert was automatically generated by GPUAlert (SA-22 Enforcement)*
"""

        return alert_content

    def write_alert(
        self,
        gpu_detected: bool = False,
        gpu_vendor: str = "Unknown",
        available_encoders: list = None,
        reason: str = "GPU acceleration not available",
    ) -> Path:
        """
        Write alert to file.

        Args:
            gpu_detected: Whether GPU was detected
            gpu_vendor: GPU vendor name
            available_encoders: List of available hardware encoders
            reason: Reason for alert

        Returns:
            Path to written alert file
        """
        alert_content = self.generate_alert(
            gpu_detected=gpu_detected,
            gpu_vendor=gpu_vendor,
            available_encoders=available_encoders,
            reason=reason,
        )

        self.alert_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.alert_path, "w") as f:
            f.write(alert_content)

        logger.warning(f"GPU alert written to {self.alert_path}")
        return self.alert_path

    def check_and_alert(
        self,
        gpu_detected: bool,
        gpu_vendor: str,
        available_encoders: list,
    ) -> bool:
        """
        Check GPU status and generate alert if needed.

        Args:
            gpu_detected: Whether GPU was detected
            gpu_vendor: GPU vendor name
            available_encoders: List of available hardware encoders

        Returns:
            True if alert was generated (GPU not available)
        """
        # GPU is available if detected AND has hardware encoders
        if gpu_detected and available_encoders:
            logger.info(f"GPU acceleration available: {gpu_vendor} ({available_encoders})")
            return False

        # Generate alert
        reason = self._determine_reason(gpu_detected, gpu_vendor, available_encoders)
        self.write_alert(
            gpu_detected=gpu_detected,
            gpu_vendor=gpu_vendor,
            available_encoders=available_encoders,
            reason=reason,
        )
        return True

    def _determine_reason(
        self,
        gpu_detected: bool,
        gpu_vendor: str,
        available_encoders: list,
    ) -> str:
        """Determine the reason for GPU unavailability."""
        if not gpu_detected:
            return "No GPU detected in system"

        if gpu_vendor == "NVIDIA" and not available_encoders:
            return "NVIDIA GPU detected but FFmpeg lacks NVENC encoder support"

        if gpu_vendor == "AMD" and not available_encoders:
            return "AMD GPU detected but FFmpeg lacks AMF encoder support"

        if gpu_vendor == "Intel" and not available_encoders:
            return "Intel GPU detected but FFmpeg lacks QSV/VAAPI encoder support"

        return "GPU detected but no hardware encoders available in FFmpeg"


def main():
    """CLI entry point for alert generation."""
    import argparse

    parser = argparse.ArgumentParser(description="GPU Alert Generator (SA-22)")
    parser.add_argument("--workspace", type=str, default=".", help="Workspace path")
    parser.add_argument("--test", action="store_true", help="Test alert generation")
    parser.add_argument("--force", action="store_true", help="Force alert generation")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    generator = GPUAlertGenerator(args.workspace)

    if args.test or args.force:
        # Simulate GPU not found
        alert_path = generator.write_alert(
            gpu_detected=True,
            gpu_vendor="NVIDIA",
            available_encoders=[],
            reason="TEST ALERT: NVIDIA GPU detected but FFmpeg lacks NVENC support",
        )
        print(f"Alert generated: {alert_path}")
    else:
        print("Use --test to generate test alert")


if __name__ == "__main__":
    main()
