#!/usr/bin/env python3
"""
Thermal Monitor for MediaAuditOrganizer
Monitors drive temperature via S.M.A.R.T. data and provides auto-pause functionality.

Requirements:
- smartmontools package (sudo apt install smartmontools)
- Root/sudo access for S.M.A.R.T. queries (or drive configured for safe access)
"""

import subprocess
import time
import json
import re
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from threading import Thread, Event
import logging


class ThermalMonitor:
    """
    Thermal monitoring system for drive protection.

    Features:
    - Polls drive temperature via S.M.A.R.T.
    - Auto-pause at threshold (55°C)
    - Auto-resume with hysteresis (45°C)
    - Logging and alerting
    """

    def __init__(
        self,
        drive_path: str = "/dev/sda",
        pause_threshold_celsius: float = 55.0,
        resume_threshold_celsius: float = 45.0,
        poll_interval_seconds: int = 30,
        log_path: Optional[str] = None,
        alert_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize thermal monitor.

        Args:
            drive_path: Device path (e.g., /dev/sda, /dev/nvme0n1)
            pause_threshold_celsius: Temperature to pause operations
            resume_threshold_celsius: Temperature to resume operations
            poll_interval_seconds: How often to check temperature
            log_path: Path to log file
            alert_callback: Function to call for alerts (e.g., send message)
        """
        self.drive_path = drive_path
        self.pause_threshold = pause_threshold_celsius
        self.resume_threshold = resume_threshold_celsius
        self.poll_interval = poll_interval_seconds
        self.log_path = log_path
        self.alert_callback = alert_callback

        self.is_running = False
        self.is_paused = False
        self.pause_requested = False
        self.stop_event = Event()
        self.monitor_thread: Optional[Thread] = None

        # Temperature history
        self.temperature_history: List[Dict[str, Any]] = []
        self.thermal_events: List[Dict[str, Any]] = []

        # Setup logging
        self.logger = logging.getLogger("ThermalMonitor")
        self.logger.setLevel(logging.INFO)

        if log_path:
            handler = logging.FileHandler(log_path)
            handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            )
            self.logger.addHandler(handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(console_handler)

    def check_smartctl_available(self) -> bool:
        """Check if smartctl is installed."""
        try:
            result = subprocess.run(
                ["which", "smartctl"], capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_drive_temperature(self) -> Optional[float]:
        """
        Get current drive temperature via S.M.A.R.T.

        Returns:
            Temperature in Celsius or None if unavailable
        """
        try:
            # Try standard ATA command
            result = subprocess.run(
                ["smartctl", "-A", self.drive_path],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                # Try with -d option for different drive types
                result = subprocess.run(
                    ["smartctl", "-d", "auto", "-A", self.drive_path],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

            if result.returncode == 0:
                output = result.stdout

                # Parse temperature from various formats
                # Format 1: "Temperature_Celsius 194 0x0022 117 090 000 Old_age Always - 33"
                temp_match = re.search(
                    r"Temperature_Celsius\s+\d+\s+\S+\s+\d+\s+\d+\s+\d+\s+\S+\s+\S+\s+-\s+(\d+)",
                    output,
                )
                if temp_match:
                    return float(temp_match.group(1))

                # Format 2: "Temperature: 33 Celsius"
                temp_match = re.search(r"Temperature:\s*(\d+)\s*Celsius", output)
                if temp_match:
                    return float(temp_match.group(1))

                # Format 3: "Drive Temperature: 33°C"
                temp_match = re.search(r"Drive Temperature:\s*(\d+)", output)
                if temp_match:
                    return float(temp_match.group(1))

                # Format 4: NVMe format "Temperature: 33 Celsius"
                temp_match = re.search(r"temperature:\s*(\d+)\s*Celsius", output, re.I)
                if temp_match:
                    return float(temp_match.group(1))

                self.logger.warning(
                    f"Could not parse temperature from S.M.A.R.T. output for {self.drive_path}"
                )
                return None

            else:
                self.logger.warning(
                    f"smartctl failed for {self.drive_path}: {result.stderr}"
                )
                return None

        except subprocess.TimeoutExpired:
            self.logger.error(f"smartctl timeout for {self.drive_path}")
            return None
        except FileNotFoundError:
            self.logger.error("smartctl not found. Install: sudo apt install smartmontools")
            return None
        except Exception as e:
            self.logger.error(f"Error getting temperature: {e}")
            return None

    def _monitor_loop(self):
        """Background monitoring loop."""
        self.logger.info(f"Starting thermal monitoring for {self.drive_path}")
        self.logger.info(
            f"Pause threshold: {self.pause_threshold}°C, Resume threshold: {self.resume_threshold}°C"
        )

        while not self.stop_event.is_set():
            try:
                temperature = self.get_drive_temperature()

                if temperature is not None:
                    # Record temperature
                    record = {
                        "timestamp": datetime.now().isoformat(),
                        "temperature_celsius": temperature,
                        "drive": self.drive_path,
                    }
                    self.temperature_history.append(record)

                    # Keep history limited to last 1000 readings
                    if len(self.temperature_history) > 1000:
                        self.temperature_history = self.temperature_history[-1000:]

                    # Check thresholds
                    if temperature >= self.pause_threshold and not self.is_paused:
                        self._trigger_pause(temperature)
                    elif (
                        temperature <= self.resume_threshold
                        and self.is_paused
                        and self.pause_requested
                    ):
                        self._trigger_resume(temperature)

                    # Log periodically
                    if len(self.temperature_history) % 10 == 0:
                        self.logger.info(
                            f"Temperature: {temperature}°C (paused: {self.is_paused})"
                        )
                else:
                    self.logger.warning("Could not read temperature")

            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")

            # Wait for next poll
            self.stop_event.wait(self.poll_interval)

        self.logger.info("Thermal monitoring stopped")

    def _trigger_pause(self, temperature: float):
        """Trigger pause due to high temperature."""
        self.is_paused = True
        self.pause_requested = True

        event = {
            "timestamp": datetime.now().isoformat(),
            "event": "THERMAL_PAUSE",
            "temperature_celsius": temperature,
            "threshold": self.pause_threshold,
            "drive": self.drive_path,
        }
        self.thermal_events.append(event)

        self.logger.warning(
            f"🔥 THERMAL PAUSE: Temperature {temperature}°C exceeded threshold {self.pause_threshold}°C"
        )

        if self.alert_callback:
            alert_msg = (
                f"⚠️ THERMAL ALERT: Drive {self.drive_path} at {temperature}°C. "
                f"Operations paused. Resume at {self.resume_threshold}°C."
            )
            self.alert_callback(alert_msg)

    def _trigger_resume(self, temperature: float):
        """Trigger resume after cooling down."""
        self.is_paused = False
        self.pause_requested = False

        event = {
            "timestamp": datetime.now().isoformat(),
            "event": "THERMAL_RESUME",
            "temperature_celsius": temperature,
            "threshold": self.resume_threshold,
            "drive": self.drive_path,
        }
        self.thermal_events.append(event)

        self.logger.info(
            f"✅ THERMAL RESUME: Temperature cooled to {temperature}°C (below {self.resume_threshold}°C)"
        )

        if self.alert_callback:
            alert_msg = (
                f"✅ Operations resumed: Drive {self.drive_path} cooled to {temperature}°C"
            )
            self.alert_callback(alert_msg)

    def start(self):
        """Start background monitoring thread."""
        if not self.check_smartctl_available():
            self.logger.error(
                "smartctl not available. Install with: sudo apt install smartmontools"
            )
            self.logger.warning("Thermal monitoring will not function without smartctl")
            return False

        if self.is_running:
            self.logger.warning("Monitor already running")
            return False

        self.is_running = True
        self.stop_event.clear()
        self.monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        return True

    def stop(self):
        """Stop monitoring thread."""
        if not self.is_running:
            return

        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.is_running = False

    def wait_for_resume(self, timeout: Optional[float] = None) -> bool:
        """
        Wait until operations can resume (temperature below resume threshold).

        Args:
            timeout: Maximum time to wait (None = indefinite)

        Returns:
            True if resumed, False if timed out
        """
        if not self.is_paused:
            return True

        start_time = time.time()
        while self.is_paused:
            if timeout and (time.time() - start_time) > timeout:
                return False
            time.sleep(1)

        return True

    def is_operations_allowed(self) -> bool:
        """Check if operations are currently allowed (not paused)."""
        return not self.is_paused

    def get_current_temperature(self) -> Optional[float]:
        """Get current temperature reading."""
        return self.get_drive_temperature()

    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        current_temp = self.get_current_temperature()

        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "pause_requested": self.pause_requested,
            "current_temperature_celsius": current_temp,
            "pause_threshold_celsius": self.pause_threshold,
            "resume_threshold_celsius": self.resume_threshold,
            "drive": self.drive_path,
            "poll_interval_seconds": self.poll_interval,
            "temperature_readings_count": len(self.temperature_history),
            "thermal_events_count": len(self.thermal_events),
        }

    def get_thermal_events(self) -> List[Dict[str, Any]]:
        """Get all thermal events (pauses/resumes)."""
        return self.thermal_events

    def save_report(self, output_path: str):
        """Save thermal monitoring report to JSON file."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "drive": self.drive_path,
            "configuration": {
                "pause_threshold_celsius": self.pause_threshold,
                "resume_threshold_celsius": self.resume_threshold,
                "poll_interval_seconds": self.poll_interval,
            },
            "status": self.get_status(),
            "thermal_events": self.thermal_events,
            "temperature_history": self.temperature_history[-100:],  # Last 100 readings
            "statistics": self._calculate_statistics(),
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Thermal report saved to: {output_path}")

    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate temperature statistics."""
        if not self.temperature_history:
            return {}

        temps = [r["temperature_celsius"] for r in self.temperature_history]

        return {
            "min_temperature_celsius": min(temps),
            "max_temperature_celsius": max(temps),
            "avg_temperature_celsius": round(sum(temps) / len(temps), 2),
            "total_pause_events": len(
                [e for e in self.thermal_events if e["event"] == "THERMAL_PAUSE"]
            ),
            "total_resume_events": len(
                [e for e in self.thermal_events if e["event"] == "THERMAL_RESUME"]
            ),
        }


def detect_primary_drive() -> str:
    """Detect the primary system drive."""
    # Check for NVMe first
    nvme_result = subprocess.run(
        ["lsblk", "-o", "NAME,TYPE,MOUNTPOINT", "-n", "-d"],
        capture_output=True,
        text=True,
    )

    if nvme_result.stdout:
        for line in nvme_result.stdout.strip().split("\n"):
            if "nvme" in line.lower() and "/" in line:
                parts = line.split()
                return f"/dev/{parts[0]}"

    # Fallback to first non-removable disk
    result = subprocess.run(
        ["lsblk", "-o", "NAME,TYPE,MOUNTPOINT", "-n", "-d"],
        capture_output=True,
        text=True,
    )

    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            if "disk" in line and "/" in line:
                parts = line.split()
                return f"/dev/{parts[0]}"

    return "/dev/sda"  # Default fallback


def main():
    """CLI entry point for testing and standalone monitoring."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Thermal monitor for MediaAuditOrganizer"
    )
    parser.add_argument(
        "--drive",
        "-d",
        type=str,
        default=None,
        help="Drive path (auto-detected if not specified)",
    )
    parser.add_argument(
        "--pause-threshold",
        "-p",
        type=float,
        default=55.0,
        help="Pause threshold in Celsius (default: 55)",
    )
    parser.add_argument(
        "--resume-threshold",
        "-r",
        type=float,
        default=45.0,
        help="Resume threshold in Celsius (default: 45)",
    )
    parser.add_argument(
        "--poll-interval",
        "-i",
        type=int,
        default=30,
        help="Poll interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output report file path",
    )
    parser.add_argument(
        "--duration",
        "-t",
        type=int,
        default=None,
        help="Monitoring duration in seconds (None = indefinite)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a single temperature check and exit",
    )

    args = parser.parse_args()

    # Detect drive
    drive_path = args.drive or detect_primary_drive()
    print(f"🔍 Monitoring drive: {drive_path}")

    # Create monitor
    monitor = ThermalMonitor(
        drive_path=drive_path,
        pause_threshold_celsius=args.pause_threshold,
        resume_threshold_celsius=args.resume_threshold,
        poll_interval_seconds=args.poll_interval,
    )

    # Test mode
    if args.test:
        print("🌡️  Checking current temperature...")
        temp = monitor.get_drive_temperature()
        if temp is not None:
            print(f"   Current temperature: {temp}°C")
            print(f"   Status: {'⚠️  HIGH' if temp >= args.pause_threshold else '✅ OK'}")
        else:
            print("   ❌ Could not read temperature")
            print("   💡 Install smartmontools: sudo apt install smartmontools")
        return 0

    # Check smartctl
    if not monitor.check_smartctl_available():
        print("❌ smartctl not found")
        print("💡 Install with: sudo apt install smartmontools")
        return 1

    # Start monitoring
    print(f"🚀 Starting thermal monitoring...")
    print(f"   Pause at: {args.pause_threshold}°C")
    print(f"   Resume at: {args.resume_threshold}°C")
    print(f"   Poll interval: {args.poll_interval}s")

    if not monitor.start():
        print("❌ Failed to start monitoring")
        return 1

    try:
        if args.duration:
            print(f"   Duration: {args.duration}s")
            time.sleep(args.duration)
        else:
            print("   Duration: indefinite (Ctrl+C to stop)")
            while True:
                status = monitor.get_status()
                print(
                    f"\r🌡️  Temp: {status['current_temperature_celsius']}°C | "
                    f"Status: {'⏸️  PAUSED' if status['is_paused'] else '▶️  RUNNING'}",
                    end="",
                    flush=True,
                )
                time.sleep(5)

    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping monitoring...")

    finally:
        monitor.stop()

        if args.output:
            monitor.save_report(args.output)

        status = monitor.get_status()
        print(f"\n📊 Final Status:")
        print(f"   Total readings: {status['temperature_readings_count']}")
        print(f"   Thermal events: {status['thermal_events_count']}")

        stats = monitor._calculate_statistics()
        if stats:
            print(f"   Min temp: {stats.get('min_temperature_celsius', 'N/A')}°C")
            print(f"   Max temp: {stats.get('max_temperature_celsius', 'N/A')}°C")
            print(f"   Avg temp: {stats.get('avg_temperature_celsius', 'N/A')}°C")

    return 0


if __name__ == "__main__":
    exit(main())
