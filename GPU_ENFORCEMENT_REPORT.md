# GPU Enforcement Report — SA-22 Hardware Acceleration Mandate

**Generated:** 2026-03-04 00:12 MST  
**Workspace:** /home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer  
**Status:** ⚠️ BLOCKED — GPU Present but FFmpeg Lacks NVENC Support

---

## Executive Summary

| Item | Status |
|------|--------|
| GPU Detected | ✅ YES |
| GPU Vendor | NVIDIA |
| GPU Model | GeForce GTX 960 (4GB VRAM) |
| Driver Version | 580.119.02 |
| Hardware Encoders Available | ❌ NONE |
| NVENC Support | ❌ NOT AVAILABLE |
| SA-22 Compliance | ❌ BLOCKED |
| Software Fallback | ❌ FORBIDDEN |

**Verdict:** System has NVIDIA GPU but FFmpeg was not compiled with NVENC encoder support. Per SA-22 mandate, software encoding (libx264) is FORBIDDEN. Processing cannot proceed until FFmpeg is recompiled with NVENC support.

---

## Hardware Detection Results

### GPU Information

```
GPU Vendor: NVIDIA
GPU Model: NVIDIA GeForce GTX 960
VRAM: 4096 MiB
Driver: 580.119.02
```

### FFmpeg Encoder Detection

| Encoder Type | Status |
|--------------|--------|
| h264_nvenc (NVIDIA) | ❌ NOT AVAILABLE |
| h264_amf (AMD) | ❌ NOT AVAILABLE |
| h264_qsv (Intel) | ❌ NOT AVAILABLE |
| h264_vaapi (VAAPI) | ❌ NOT AVAILABLE |
| h264_videotoolbox (Apple) | ❌ NOT AVAILABLE |
| libx264 (CPU) | ✅ Available but FORBIDDEN |

### Available Encoders (Software Only)

- libx264 (H.264 software encoder)
- libx264rgb (H.264 RGB software encoder)
- libx265 (HEVC software encoder)
- h264_v4l2m2m (V4L2 mem2mem wrapper — not hardware)
- hevc_v4l2m2m (V4L2 mem2mem wrapper — not hardware)

**Note:** V4L2 wrappers are not true hardware encoders and do not satisfy SA-22 requirements.

---

## SA-22 Enforcement Policy

### Mandate

> **Software encoding (libx264) is FORBIDDEN for MediaAuditOrganizer.**
> 
> All video processing MUST use hardware acceleration (NVENC, AMF, QSV, VAAPI, or VideoToolbox).
> If hardware acceleration is not available, processing MUST fail hard — NO FALLBACK to CPU.

### Enforcement Mechanism

1. **GPU Enforcer** (`scripts/gpu_enforcer.py`):
   - `verify_gpu_available()` — Checks GPU and encoder presence
   - `require_gpu()` — Raises `GPUEnforcementError` if no GPU encoder
   - `get_preferred_encoder()` — Returns best available hardware encoder
   - `get_encoding_command()` — Builds FFmpeg command with hardware encoder

2. **Video Processor** (`scripts/video_processor.py`):
   - Calls `gpu_enforcer.require_gpu()` at initialization
   - Fails fast if no hardware encoder available
   - Removed all CPU fallback logic
   - Logs encoder used per operation

3. **GPU Alert** (`scripts/gpu_alert.py`):
   - Generates `GPU_NOT_FOUND_ALERT.md` when GPU unavailable
   - Includes system info and installation instructions
   - Blocks processing until resolved

### Violation Response

When SA-22 violation detected:
1. Raise `GPUEnforcementError` exception
2. Write `GPU_NOT_FOUND_ALERT.md` with resolution steps
3. Log violation to heartbeat/status
4. **DO NOT PROCEED** with video processing

---

## Resolution Required

### Problem

NVIDIA GPU (GTX 960) is present and drivers are installed, but FFmpeg lacks NVENC encoder support.

### Solution: Recompile FFmpeg with NVENC

#### Option 1: Install Pre-built FFmpeg with NVENC

```bash
# Using conda (recommended for simplicity)
conda install -c conda-forge ffmpeg

# Verify NVENC is available
ffmpeg -encoders | grep nvenc
# Should show: h264_nvenc, hevc_nvenc
```

#### Option 2: Build FFmpeg from Source with NVENC

1. **Install NVIDIA Video Codec SDK:**
   - Download from: https://developer.nvidia.com/video-codec-sdk
   - Extract to `/opt/nvidia-video-codec-sdk`

2. **Install build dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y build-essential yasm cmake libtool \
       libva-dev libvdpau-dev libx11-dev libxext-dev libxfixes-dev
   ```

3. **Build FFmpeg:**
   ```bash
   cd /tmp
   git clone https://github.com/FFmpeg/FFmpeg.git
   cd FFmpeg
   ./configure --enable-nonfree --enable-nvenc --enable-cuda-llvm \
       --enable-libnpp \
       --extra-cflags=-I/opt/nvidia-video-codec-sdk/Interfaces \
       --extra-ldflags=-L/opt/nvidia-video-codec-sdk/Lib/x64
   make -j$(nproc)
   sudo make install
   ```

4. **Verify:**
   ```bash
   ffmpeg -encoders | grep -E "nvenc"
   # Expected output:
   # V..... h264_nvenc           NVIDIA NVENC H.264 encoder
   # V..... hevc_nvenc            NVIDIA NVENC hevc encoder
   ```

---

## Deliverables Created

| File | Purpose |
|------|---------|
| `hardware_detection_result.json` | GPU detection results in JSON format |
| `scripts/gpu_enforcer.py` | GPU enforcement wrapper (SA-22 compliance) |
| `scripts/gpu_alert.py` | Alert generator for missing GPU |
| `scripts/video_processor.py` | Updated to use GPU enforcer (NO CPU FALLBACK) |
| `GPU_ENFORCEMENT_REPORT.md` | This report |

---

## Testing

### Test GPU Enforcement

```bash
cd /home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer
python scripts/gpu_enforcer.py --test
```

**Expected (current state):**
```
❌ GPU ENFORCEMENT CHECK FAILED
Error: GPU DETECTED (NVIDIA) BUT FFMPEG LACKS HARDWARE ENCODER SUPPORT
```

**Expected (after fix):**
```
✅ GPU ENFORCEMENT CHECK PASSED
Recommended encoder: h264_nvenc
```

### Test Video Processor

```bash
python scripts/video_processor.py --list-encoders
```

**Expected (current state):**
```
GPUEnforcementError: No hardware encoders available
```

**Expected (after fix):**
```
Selected: h264_nvenc (NVIDIA GPU)
```

---

## Next Actions

1. **[REQUIRED]** Recompile FFmpeg with NVENC support (see Resolution Required above)
2. Verify encoder availability: `ffmpeg -encoders | grep nvenc`
3. Test GPU enforcer: `python scripts/gpu_enforcer.py --test`
4. Once passed, video processing will automatically resume

---

## References

- SA-22 Hardware Acceleration Mandate
- FFmpeg NVENC Documentation: https://trac.ffmpeg.org/wiki/HWAccelIntro#NVENC
- NVIDIA Video Codec SDK: https://developer.nvidia.com/video-codec-sdk
- MediaAuditOrganizer Workspace: `/home/az/.openclaw/workspace/AZ_Projects/MediaAuditOrganizer`

---

**DO NOT PROCEED WITH VIDEO TRANSFER UNTIL GPU ACCELERATION IS AVAILABLE**

*Report generated by GPU Enforcer (SA-22 Enforcement) — 2026-03-04*
