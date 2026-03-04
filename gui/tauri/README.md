# MediaAuditOrganizer — Tauri 2.0 Desktop GUI

Professional media management desktop application built with Tauri 2.0, React 19, and TypeScript.

## Overview

MediaAuditOrganizer is a high-performance desktop GUI that wraps the Python orchestration engine for media audit, deduplication, and organization. Designed for photographers and videographers who need local-first, GPU-accelerated media management.

**Design Philosophy:** DaVinci Resolve aesthetic — dark mode, high-density information layout, professional tool feel.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19 + TypeScript + Vite |
| **UI Components** | Shadcn/UI (Radix primitives) |
| **Styling** | Tailwind CSS + Custom Design Tokens |
| **State Management** | TanStack Query (React Query) |
| **Desktop Bridge** | Tauri 2.0 (Rust) |
| **Backend** | Python 3.12 sidecar |
| **Database** | SQLite (via sqlx) |

## Prerequisites

### System Requirements

- **OS:** Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM:** 8GB minimum, 16GB recommended
- **Disk:** 500MB for application + workspace for media files
- **GPU:** Optional (for hardware-accelerated operations)

### Development Dependencies

#### 1. Rust Toolchain

```bash
# Install rustup (Rust installer)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Verify installation
rustc --version
cargo --version
```

#### 2. Node.js & npm

```bash
# Install Node.js 18+ (LTS recommended)
# https://nodejs.org/

# Verify installation
node --version  # Should be 18.x or higher
npm --version
```

#### 3. Python Environment

```bash
# Python 3.12 required
python3 --version

# Create virtual environment (if not exists)
cd /path/to/MediaAuditOrganizer
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r scripts/requirements.txt
```

#### 4. System Dependencies

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install -y \
  libwebkit2gtk-4.1-dev \
  build-essential \
  curl \
  wget \
  libssl-dev \
  libgtk-3-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev \
  exiftool \
  ffmpeg \
  python3-venv
```

**macOS:**
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install dependencies via Homebrew
brew install exiftool ffmpeg
```

**Windows:**
```powershell
# Install WebView2 (usually pre-installed on Windows 10/11)
# https://developer.microsoft.com/en-us/microsoft-edge/webview2/

# Install Visual Studio C++ Build Tools
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

## Project Structure

```
gui/
├── tauri.conf.json          # Tauri configuration
├── package.json             # Node.js dependencies
├── vite.config.ts           # Vite build configuration
├── tailwind.config.js       # Tailwind CSS configuration
├── tsconfig.json            # TypeScript configuration
├── index.html               # HTML entry point
├── src/
│   ├── main.tsx             # React entry point
│   ├── App.tsx              # Root component
│   ├── index.css            # Global styles
│   ├── components/
│   │   ├── Dashboard.tsx    # Main dashboard layout
│   │   ├── AgentMonitor.tsx # Sub-agent status monitor
│   │   ├── DriveMap.tsx     # Drive selection interface
│   │   ├── DatabaseView.tsx # SQLite database viewer
│   │   ├── ConfirmationGate.tsx # Approval modal
│   │   ├── WorkflowPhases.tsx   # Workflow progress
│   │   └── ui/              # Shadcn/UI components
│   ├── hooks/
│   │   ├── useAgentStatus.ts    # Agent status hook
│   │   └── useWorkflowStatus.ts # Workflow hook
│   ├── lib/
│   │   └── utils.ts         # Utility functions
│   ├── mock/
│   │   └── data.ts          # Mock data for development
│   ├── styles/
│   │   └── design-tokens.css # Design system tokens
│   └── types/
│       └── index.ts         # TypeScript types
└── src-tauri/
    ├── Cargo.toml           # Rust dependencies
    ├── build.rs             # Tauri build script
    ├── tauri.conf.json      # Tauri config (symlink)
    └── src/
        └── main.rs          # Rust backend entry point
```

## Installation

### 1. Clone and Navigate

```bash
cd /path/to/MediaAuditOrganizer/gui
```

### 2. Install Node.js Dependencies

```bash
npm install
```

### 3. Install Rust Dependencies

```bash
cd src-tauri
cargo build
cd ..
```

### 4. Verify Python Sidecar

```bash
# Ensure virtual environment is activated
source ../.venv/bin/activate

# Test Python scripts
python ../scripts/audit_drive.py --help
```

## Development

### Start Development Server

```bash
# Run Tauri in development mode (hot reload enabled)
npm run tauri:dev
```

This will:
1. Start Vite dev server on `http://localhost:1420`
2. Build and launch the Tauri desktop window
3. Enable hot module replacement for frontend changes
4. Auto-rebuild Rust backend on changes

### Separate Commands

```bash
# Frontend only (browser)
npm run dev

# Tauri dev (desktop app)
npm run tauri:dev

# Rust backend only
cd src-tauri && cargo build
```

## Building for Production

### Build All Platforms

```bash
npm run tauri:build
```

This creates distributable packages in `src-tauri/target/release/bundle/`:

- **Linux:** `.deb`, `.AppImage`
- **macOS:** `.app`, `.dmg`
- **Windows:** `.exe`, `.msi`

### Platform-Specific Builds

```bash
# Linux only
npm run tauri build -- --target x86_64-unknown-linux-gnu

# macOS only (Intel)
npm run tauri build -- --target x86_64-apple-darwin

# macOS only (Apple Silicon)
npm run tauri build -- --target aarch64-apple-darwin

# Windows only
npm run tauri build -- --target x86_64-pc-windows-msvc
```

### Build Output Locations

```
src-tauri/target/release/bundle/
├── deb/
│   └── media-audit-organizer_1.0.0_amd64.deb
├── appimage/
│   └── media-audit-organizer_1.0.0_amd64.AppImage
├── macos/
│   └── MediaAuditOrganizer.app
├── dmg/
│   └── MediaAuditOrganizer_1.0.0_x64.dmg
├── msi/
│   └── MediaAuditOrganizer_1.0.0_x64_en-US.msi
└── nsis/
    └── MediaAuditOrganizer_1.0.0_x64-setup.exe
```

## Configuration

### Tauri Configuration (`tauri.conf.json`)

Key settings:

```json
{
  "productName": "MediaAuditOrganizer",
  "version": "1.0.0",
  "identifier": "com.mediamaudit.organizer",
  "app": {
    "windows": [{
      "width": 1600,
      "height": 1000,
      "theme": "Dark"
    }]
  },
  "bundle": {
    "resources": [
      "../scripts/*.py",
      "../.venv/**/*"
    ],
    "externalBin": ["python", "exiftool", "ffmpeg"]
  }
}
```

### Python Sidecar Configuration

The Python sidecar is bundled with the application and executed via Tauri's shell plugin:

```rust
// In src-tauri/src/main.rs
let output = Command::new("python")
    .arg("../scripts/audit_drive.py")
    .arg("--source")
    .arg(&source_path)
    .output()?;
```

### Allowed Filesystem Paths

Configured in `tauri.conf.json`:

```json
{
  "fs": {
    "scope": [
      "/media/**",
      "/mnt/**",
      "/Volumes/**",
      "$HOME/Pictures/**",
      "$HOME/Videos/**"
    ]
  }
}
```

## Features

### 1. Sub-Agent Monitor

Real-time status monitoring for all 12 sub-agents:
- SA-01: Environment Validator
- SA-02: Configuration Auditor
- SA-03: Database Initiator
- SA-04: Drive Scanner
- SA-05: Audit Executor
- SA-06: Dedupe Analyzer
- SA-07: Rename Planner
- SA-08: Transfer Executor
- SA-09: Backup Verifier
- SA-10: Report Generator
- SA-11: Lightroom Reconciler
- SA-12: Cleanup Archiver

**Status Indicators:**
- 🟡 Idle (gray)
- 🔵 Processing (blue, animated)
- 🟢 Success (green)
- 🔴 Error (red)

### 2. Drive Map

Visual drive selection interface:
- Drag-and-drop source drives
- Select target "Master" drive
- Real-time capacity visualization
- Mount point detection (`/media/`, `/mnt/`, `/Volumes/`)

### 3. Confirmation Gate

Safety checkpoint before critical operations:
- Displays findings (e.g., "Found 40GB of Duplicates")
- Risk level indicators (Low/Medium/High)
- Approve/Reject/Modify options
- Detailed breakdown before approval

### 4. Database View

SQLite media index browser:
- Filterable by camera model, date, file size, type
- Sortable columns
- Search functionality
- Duplicate indicators
- Pagination (100 items per page)

### 5. Workflow Phases

Visual workflow progress tracker:
- 11-phase workflow pipeline
- Dependency visualization
- Progress indicators
- Phase status (Pending/Active/Completed/Blocked)

## Design System

### Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| Obsidian-900 | `#1a1a1a` | Primary background |
| Slate-900 | `#0f172a` | Secondary background |
| Slate-800 | `#1e293b` | Cards, panels |
| Cyber-Lime-400 | `#a3e635` | Accent, highlights |
| Status-Idle | `#64748b` | Idle state |
| Status-Processing | `#3b82f6` | Active state |
| Status-Success | `#22c55e` | Success state |
| Status-Error | `#ef4444` | Error state |

### Typography

- **Font:** Inter (sans-serif), JetBrains Mono (code)
- **Scale:** 11px, 12px, 13px, 14px, 16px, 20px
- **Density:** High (professional tool aesthetic)

## Troubleshooting

### Common Issues

#### 1. "Tauri CLI not found"

```bash
npm install -g @tauri-apps/cli
```

#### 2. "Rust compiler not found"

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

#### 3. "WebView2 not found" (Windows)

Download and install WebView2:
https://developer.microsoft.com/en-us/microsoft-edge/webview2/

#### 4. "libwebkit2gtk not found" (Linux)

```bash
sudo apt install libwebkit2gtk-4.1-dev
```

#### 5. Python sidecar not found

Ensure virtual environment is activated and paths are correct:

```bash
# Check Python path
which python

# Verify scripts exist
ls -la ../scripts/
```

#### 6. Port 1420 already in use

```bash
# Kill process on port 1420
lsof -ti:1420 | xargs kill -9

# Or change port in vite.config.ts
```

### Debug Mode

Enable verbose logging:

```bash
# Frontend debug
TAURI_DEBUG=true npm run tauri:dev

# Backend debug (Rust)
RUST_LOG=debug npm run tauri:dev
```

View logs in:
- **Frontend:** Browser DevTools Console
- **Backend:** Terminal output or `~/.local/share/com.mediamaudit.organizer/logs/`

## Deployment

### Linux (.deb)

```bash
sudo dpkg -i src-tauri/target/release/bundle/deb/media-audit-organizer_1.0.0_amd64.deb
```

### macOS (.dmg)

```bash
# Open DMG and drag to Applications
open src-tauri/target/release/bundle/dmg/MediaAuditOrganizer_1.0.0_x64.dmg
```

### Windows (.exe)

```powershell
# Run installer
.\src-tauri\target\release\bundle\nsis\MediaAuditOrganizer_1.0.0_x64-setup.exe
```

## Testing

### Unit Tests (Frontend)

```bash
# Install testing libraries
npm install -D vitest @testing-library/react

# Run tests
npm run test
```

### Integration Tests (Tauri)

```bash
# Run Tauri tests
cd src-tauri
cargo test
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License — see LICENSE file for details.

## Support

- **Documentation:** `/README.md` in project root
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions

---

**Version:** 1.0.0  
**Last Updated:** 2026-03-03  
**Build:** Tauri 2.0 + React 19 + TypeScript
