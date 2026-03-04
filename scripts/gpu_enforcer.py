#!/usr/bin/env python3
"""
GPU Enforcement Wrapper for MediaAuditOrganizer
SA-22: Hardware Acceleration Mandate

CRITICAL: Software encoding (libx264) is FORBIDDEN.
This module enforces GPU-only encoding and fails hard if no hardware encoder is available.

DO NOT FALLBACK TO CPU.
"""

import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger("GPUEnforcer")


class GPUVendor(Enum):
    """Supported GPU vendors."""
    NVIDIA = "NVIDIA"
    AMD = "AMD"
    APPLE = "Apple"
    INTEL = "Intel"
    UNKNOWN = "Unknown"


class HardwareEncoder(Enum):
    """Hardware encoder identifiers."""
    NVENC_H264 = "h264_nvenc"
    NVENC_HEVC = "hevc_nvenc"
    AMF_H264 = "h264_amf"
    AMF_HEVC = "hevc_amf"
    VIDEOTOOLBOX_H264 = "h264_videotoolbox"
    VIDEOTOOLBOX_HEVC = "hevc_videotoolbox"
    QSV_H264 = "h264_qsv"
    QSV_HEVC = "hevc_qsv"
    VAAPI_H264 = "h264_vaapi"
    VAAPI_HEVC = "hevc_vaapi"


@dataclass
class GPUInfo:
    """GPU detection information."""
    detected: bool
    vendor: GPUVendor
    model: str = ""
    driver_version: str = ""
    memory_mb: int = 0


@dataclass
class EncoderDetectionResult:
    """Result of encoder detection."""
    gpu_info: GPUInfo
    available_encoders: List[str]
    recommended_encoder: Optional[str]
    ffmpeg_has_nvenc: bool
    ffmpeg_has_amf: bool
    ffmpeg_has_videotoolbox: bool
    ffmpeg_has_qsv: bool
    ffmpeg_has_vaapi: bool


class GPUEnforcementError(Exception):
    """Raised when GPU acceleration is not available."""
    pass


class GPUEnforcer:
    """
    GPU Enforcement Wrapper.

    Enforces hardware-accelerated encoding mandate (SA-22).
    NO SOFTWARE ENCODING FALLBACK.

    Usage:
        enforcer = GPUEnforcer()
        enforcer.require_gpu()  # Raises exception if no GPU encoder available
        encoder = enforcer.get_preferred_encoder()
        cmd = enforcer.get_encoding_command(input_path, output_path, encoder)
    """

    def __init__(self, log_level: int = logging.INFO):
        """Initialize GPU enforcer."""
        logger.setLevel(log_level)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            logger.addHandler(handler)

        self._detection_result: Optional[EncoderDetectionResult] = None
        self._detect()

    def _run_command(self, args: List[str], timeout: int = 10) -> Tuple[bool, str, str]:
        """Run shell command and return result."""
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except FileNotFoundError:
            return False, "", f"Command not found: {args[0]}"
        except Exception as e:
            return False, "", str(e)

    def _detect_nvidia_gpu(self) -> Optional[GPUInfo]:
        """Detect NVIDIA GPU using nvidia-smi."""
        success, stdout, stderr = self._run_command(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]
        )
        if success and stdout.strip():
            parts = stdout.strip().split(", ")
            if len(parts) >= 3:
                return GPUInfo(
                    detected=True,
                    vendor=GPUVendor.NVIDIA,
                    model=parts[0],
                    memory_mb=int(parts[1].replace(" MiB", "")),
                    driver_version=parts[2],
                )
        return None

    def _detect_amd_gpu(self) -> Optional[GPUInfo]:
        """Detect AMD GPU using rocm-smi or lspci."""
        # Try rocm-smi first
        success, stdout, stderr = self._run_command(["rocm-smi", "--showproductname"])
        if success and stdout.strip():
            return GPUInfo(detected=True, vendor=GPUVendor.AMD)

        # Fallback to lspci
        success, stdout, stderr = self._run_command(["lspci", "-v"])
        if success and "AMD" in stdout:
            return GPUInfo(detected=True, vendor=GPUVendor.AMD)

        return None

    def _detect_intel_gpu(self) -> Optional[GPUInfo]:
        """Detect Intel GPU using lspci."""
        success, stdout, stderr = self._run_command(["lspci", "-v"])
        if success and ("Intel" in stdout or "i915" in stdout):
            return GPUInfo(detected=True, vendor=GPUVendor.INTEL)
        return None

    def _detect_apple_gpu(self) -> Optional[GPUInfo]:
        """Detect Apple GPU (VideoToolbox always available on macOS)."""
        # Check if we're on macOS
        success, stdout, stderr = self._run_command(["uname", "-s"])
        if success and "Darwin" in stdout:
            return GPUInfo(detected=True, vendor=GPUVendor.APPLE)
        return None

    def _detect_ffmpeg_encoders(self) -> List[str]:
        """Detect available FFmpeg encoders."""
        success, stdout, stderr = self._run_command(["ffmpeg", "-encoders"])
        if not success:
            return []

        output = stdout + stderr
        encoders = []

        # Check for hardware encoders
        hardware_encoders = [
            "h264_nvenc", "hevc_nvenc",
            "h264_amf", "hevc_amf",
            "h264_videotoolbox", "hevc_videotoolbox",
            "h264_qsv", "hevc_qsv",
            "h264_vaapi", "hevc_vaapi",
        ]

        for enc in hardware_encoders:
            if enc in output.lower():
                encoders.append(enc)

        return encoders

    def _detect(self) -> None:
        """Run full GPU and encoder detection."""
        # Detect GPU
        gpu_info = self._detect_nvidia_gpu()
        if not gpu_info:
            gpu_info = self._detect_amd_gpu()
        if not gpu_info:
            gpu_info = self._detect_intel_gpu()
        if not gpu_info:
            gpu_info = self._detect_apple_gpu()

        if not gpu_info:
            gpu_info = GPUInfo(detected=False, vendor=GPUVendor.UNKNOWN)

        # Detect FFmpeg encoders
        available_encoders = self._detect_ffmpeg_encoders()

        # Determine recommended encoder (priority: NVENC > AMF > QSV > VAAPI > VideoToolbox)
        recommended = None
        for priority_encoder in ["h264_nvenc", "h264_amf", "h264_qsv", "h264_vaapi", "h264_videotoolbox"]:
            if priority_encoder in available_encoders:
                recommended = priority_encoder
                break

        self._detection_result = EncoderDetectionResult(
            gpu_info=gpu_info,
            available_encoders=available_encoders,
            recommended_encoder=recommended,
            ffmpeg_has_nvenc="h264_nvenc" in available_encoders,
            ffmpeg_has_amf="h264_amf" in available_encoders,
            ffmpeg_has_videotoolbox="h264_videotoolbox" in available_encoders,
            ffmpeg_has_qsv="h264_qsv" in available_encoders,
            ffmpeg_has_vaapi="h264_vaapi" in available_encoders,
        )

        logger.info(f"GPU Detection: {gpu_info.vendor.value} - {'DETECTED' if gpu_info.detected else 'NOT FOUND'}")
        logger.info(f"Hardware Encoders: {available_encoders if available_encoders else 'NONE'}")
        logger.info(f"Recommended Encoder: {recommended if recommended else 'NONE AVAILABLE'}")

    def verify_gpu_available(self) -> bool:
        """
        Verify GPU is available for hardware encoding.

        Returns:
            True if GPU and hardware encoder available

        Raises:
            GPUEnforcementError: If no GPU encoder available
        """
        if not self._detection_result:
            self._detect()

        result = self._detection_result

        # Check if GPU is physically present
        if not result.gpu_info.detected:
            raise GPUEnforcementError(
                "NO GPU DETECTED: Hardware acceleration required per SA-22 mandate. "
                "System has no NVIDIA, AMD, Intel, or Apple GPU detected."
            )

        # Check if ffmpeg has hardware encoder support
        if not result.available_encoders:
            vendor = result.gpu_info.vendor.value
            raise GPUEnforcementError(
                f"GPU DETECTED ({vendor}) BUT FFMPEG LACKS HARDWARE ENCODER SUPPORT. "
                f"FFmpeg must be recompiled with hardware encoder support. "
                f"For NVIDIA: --enable-nonfree --enable-nvenc"
            )

        return True

    def get_preferred_encoder(self) -> str:
        """
        Get the preferred hardware encoder.

        Returns:
            Encoder name (e.g., 'h264_nvenc')

        Raises:
            GPUEnforcementError: If no hardware encoder available
        """
        self.require_gpu()  # Enforce GPU availability

        if self._detection_result and self._detection_result.recommended_encoder:
            return self._detection_result.recommended_encoder

        raise GPUEnforcementError("No hardware encoder available")

    def require_gpu(self) -> None:
        """
        Require GPU acceleration - fails hard if not available.

        DO NOT FALLBACK TO CPU.

        Raises:
            GPUEnforcementError: If GPU acceleration not available
        """
        self.verify_gpu_available()
        logger.info("GPU enforcement check passed - hardware acceleration available")

    def get_encoding_command(
        self,
        input_path: str,
        output_path: str,
        encoder: Optional[str] = None,
        quality: int = 21,
        preset: str = "p2",
    ) -> List[str]:
        """
        Build FFmpeg encoding command with hardware encoder.

        Args:
            input_path: Input video file path
            output_path: Output video file path
            encoder: Encoder name (auto-selected if None)
            quality: Quality value (lower = better, encoder-specific)
            preset: Encoding preset (encoder-specific)

        Returns:
            FFmpeg command as list of arguments

        Raises:
            GPUEnforcementError: If GPU not available
        """
        self.require_gpu()  # Enforce GPU before building command

        if encoder is None:
            encoder = self.get_preferred_encoder()

        # Build encoder-specific parameters
        encoder_args = ["-c:v", encoder]

        if "nvenc" in encoder:
            encoder_args.extend(["-preset", preset, "-cq", str(quality)])
        elif "amf" in encoder:
            encoder_args.extend(["-quality", "quality", "-qp_i", str(quality)])
        elif "videotoolbox" in encoder:
            encoder_args.extend(["-q:v", str(quality)])
        elif "qsv" in encoder:
            encoder_args.extend(["-preset", preset, "-q", str(quality)])
        elif "vaapi" in encoder:
            encoder_args.extend(["-qp", str(quality)])

        # Build full command
        command = [
            "ffmpeg",
            "-i", str(input_path),
            *encoder_args,
            "-c:a", "copy",  # Copy audio stream
            "-y",  # Overwrite output
            str(output_path),
        ]

        logger.info(f"Encoding command: ffmpeg -i {input_path} -c:v {encoder} ... {output_path}")
        return command

    def get_detection_result(self) -> dict:
        """Get detection result as dictionary."""
        if not self._detection_result:
            self._detect()

        result = self._detection_result
        return {
            "gpu_detected": result.gpu_info.detected,
            "gpu_vendor": result.gpu_info.vendor.value,
            "gpu_model": result.gpu_info.model,
            "gpu_memory_mb": result.gpu_info.memory_mb,
            "driver_version": result.gpu_info.driver_version,
            "available_encoders": result.available_encoders,
            "recommended_encoder": result.recommended_encoder,
            "ffmpeg_has_nvenc": result.ffmpeg_has_nvenc,
            "ffmpeg_has_amf": result.ffmpeg_has_amf,
            "ffmpeg_has_videotoolbox": result.ffmpeg_has_videotoolbox,
            "ffmpeg_has_qsv": result.ffmpeg_has_qsv,
            "ffmpeg_has_vaapi": result.ffmpeg_has_vaapi,
        }

    def save_detection_result(self, output_path: str) -> None:
        """Save detection result to JSON file."""
        result = self.get_detection_result()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        logger.info(f"Detection result saved to {output_path}")


def main():
    """CLI entry point for GPU enforcement testing."""
    import argparse

    parser = argparse.ArgumentParser(description="GPU Enforcement for MediaAuditOrganizer (SA-22)")
    parser.add_argument("--test", action="store_true", help="Test GPU availability")
    parser.add_argument("--encoder", action="store_true", help="Show recommended encoder")
    parser.add_argument("--command", type=str, nargs=2, metavar=("INPUT", "OUTPUT"), help="Build encoding command")
    parser.add_argument("--save-result", type=str, metavar="PATH", help="Save detection result to JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    enforcer = GPUEnforcer(log_level=log_level)

    if args.test:
        try:
            enforcer.require_gpu()
            print("✅ GPU ENFORCEMENT CHECK PASSED")
            print(f"   Recommended encoder: {enforcer.get_preferred_encoder()}")
        except GPUEnforcementError as e:
            print(f"❌ GPU ENFORCEMENT CHECK FAILED")
            print(f"   Error: {e}")
            sys.exit(1)

    if args.encoder:
        try:
            encoder = enforcer.get_preferred_encoder()
            print(f"Recommended encoder: {encoder}")
        except GPUEnforcementError as e:
            print(f"No hardware encoder available: {e}")
            sys.exit(1)

    if args.command:
        input_path, output_path = args.command
        try:
            cmd = enforcer.get_encoding_command(input_path, output_path)
            print(" ".join(cmd))
        except GPUEnforcementError as e:
            print(f"Cannot build command: {e}")
            sys.exit(1)

    if args.save_result:
        enforcer.save_detection_result(args.save_result)
        print(f"Detection result saved to {args.save_result}")

    if not any([args.test, args.encoder, args.command, args.save_result]):
        # Default: show detection summary
        result = enforcer.get_detection_result()
        print("\n=== GPU Detection Summary ===")
        print(f"GPU Detected: {result['gpu_detected']}")
        print(f"GPU Vendor: {result['gpu_vendor']}")
        if result['gpu_model']:
            print(f"GPU Model: {result['gpu_model']}")
        print(f"Available Hardware Encoders: {result['available_encoders'] if result['available_encoders'] else 'NONE'}")
        print(f"Recommended Encoder: {result['recommended_encoder'] if result['recommended_encoder'] else 'NONE'}")


if __name__ == "__main__":
    main()
