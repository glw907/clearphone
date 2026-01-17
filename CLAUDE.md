# CLAUDE.md — Development Guide

> **Meta-documentation note:** This file (CLAUDE.md) is for developers and AI assistants working on Clearphone. When making significant architecture or design changes, update BOTH this file AND README.md to keep them in sync. CLAUDE.md provides implementation details; README.md communicates project vision and user-facing information.

This document is for developers working on Clearphone, particularly when using Claude Code or similar AI-assisted development tools.

## Project Overview

Clearphone transforms Android smartphones into minimal, low-distraction devices by removing bloatware and installing privacy-focused alternatives.

**Current version:** 0.1.0 (CLI prototype)
**Target devices:** Samsung Galaxy S24, Google Pixel 8/8a
**Interface:** Command-line only
**App sources:** F-Droid repository (open source APKs), direct APK downloads (proprietary)
**Installation method:** ADB (no F-Droid app or Play Store required)

### Why Two Devices?

**Samsung Galaxy S24** — Stress test. One UI adds substantial bloatware: Bixby ecosystem, Samsung apps, carrier installers, pre-loaded social media. If the tool handles Samsung's complexity, it can handle anything.

**Google Pixel 8/8a** — Production target. Stock Android with minimal manufacturer additions, available at reasonable cost. This is the intended hardware for real-world deployment.

The dual-device strategy validates that the profile-based approach works across fundamentally different Android implementations.

### Interface Development Sequence

1. **CLI** (current) — Fastest path to working functionality; validates core logic
2. **TUI** (next) — Power-user and developer focus; richer interaction model without web complexity
3. **Web** (future) — Broader accessibility; requires UX expertise not currently on the team

The event-driven architecture means all three interfaces consume the same core logic—no duplication.

## Quick Start

```bash
# Read specifications
cat docs/requirements.md          # What we're building
cat docs/implementation-order.md  # Build sequence

# Run tests
pytest tests/

# Format code
ruff check --fix .
ruff format .
```

## Architecture

### Event-Driven Core

All core logic is **UI-agnostic** and communicates through events. No module prints directly to console—they emit events that interfaces consume.

```python
# Core modules yield events
for event in workflow.execute(profile, adb, dry_run=False):
    if event.type == EventType.PACKAGE_REMOVED:
        print(f"Removed: {event.package_name}")
```

This enables:
- Testing without UI (inspect event sequences)
- Multiple interfaces (CLI, TUI, web) from the same core
- Clean separation of concerns

### Module Structure

```
clearphone/
├── clearphone/
│   ├── core/
│   │   ├── profile.py      # TOML parsing and validation
│   │   ├── apps_catalog.py # Apps catalog loading
│   │   ├── adb.py          # ADB command wrapper
│   │   ├── downloader.py   # F-Droid and direct APK downloads
│   │   ├── installer.py    # App installation via ADB
│   │   ├── remover.py      # Package removal logic
│   │   ├── workflow.py     # Orchestration
│   │   └── exceptions.py   # Exception hierarchy
│   ├── api/
│   │   ├── events.py       # Event dataclasses
│   │   └── controller.py   # ConfigurationController
│   └── cli.py              # Typer CLI interface
├── device-profiles/        # Device-specific TOML files
├── apps/                   # Shared apps catalog
│   ├── core.toml
│   └── extras/
│       ├── free.toml
│       └── non-free.toml
├── docs/                   # Technical specifications
├── guides/                 # User documentation
└── tests/
```

### Key Classes

**`DeviceProfile`** — Parses and validates device profile TOML files  
**`AppsCatalog`** — Loads and resolves the shared apps catalog  
**`ADBDevice`** — Wraps ADB commands with error handling  
**`ConfigurationController`** — Entry point for all UIs  
**`ConfigurationWorkflow`** — Orchestrates the full process

## Apps Catalog

Replacement apps are defined in a shared catalog, separate from device profiles. This avoids duplication across profiles and centralizes app metadata.

### Catalog Structure

```
apps/
├── core.toml           # Always installed
└── extras/
    ├── free.toml       # Optional open-source apps
    └── non-free.toml   # Optional proprietary apps
```

### Core Apps (`apps/core.toml`)

Always installed on every configured phone:

```toml
[launcher]
id = "launcher"
package_id = "app.olauncher"
name = "Olauncher"
source = "fdroid"
fdroid_package_name = "app.olauncher"
installation_priority = 1

[keyboard]
id = "keyboard"
package_id = "org.futo.inputmethod.latin"
name = "FUTO Keyboard"
source = "fdroid"
fdroid_package_name = "org.futo.inputmethod.latin"
installation_priority = 5

[dialer]
id = "dialer"
package_id = "com.simplemobiletools.dialer"
name = "Fossify Dialer"
source = "fdroid"
fdroid_package_name = "com.simplemobiletools.dialer"
installation_priority = 10

[messaging]
id = "messaging"
package_id = "com.simplemobiletools.smsmessenger"
name = "Fossify Messages"
source = "fdroid"
fdroid_package_name = "com.simplemobiletools.smsmessenger"
installation_priority = 10

[contacts]
id = "contacts"
package_id = "com.simplemobiletools.contacts.pro"
name = "Fossify Contacts"
source = "fdroid"
fdroid_package_name = "com.simplemobiletools.contacts.pro"
installation_priority = 20

[gallery]
id = "gallery"
package_id = "com.simplemobiletools.gallery.pro"
name = "Fossify Gallery"
source = "fdroid"
fdroid_package_name = "com.simplemobiletools.gallery.pro"
installation_priority = 20

[files]
id = "files"
package_id = "com.simplemobiletools.filemanager.pro"
name = "Fossify Files"
source = "fdroid"
fdroid_package_name = "com.simplemobiletools.filemanager.pro"
installation_priority = 30
```

### Extra Free Apps (`apps/extras/free.toml`)

Optional open-source apps with APKs downloaded from F-Droid's repository and installed via ADB. **All extras require a `description` field** for interactive selection:

```toml
[camera]
id = "camera"
package_id = "com.simplemobiletools.camera"
name = "Fossify Camera"
description = "Simple camera that works well with Fossify Gallery. Lower photo quality than stock camera (no advanced post-processing)."
source = "fdroid"
fdroid_package_name = "com.simplemobiletools.camera"

[weather]
id = "weather"
package_id = "org.breezyweather"
name = "Breezy Weather"
description = "Beautiful, privacy-focused weather app with detailed forecasts and customizable widgets."
source = "fdroid"
fdroid_package_name = "org.breezyweather"

[music]
id = "music"
package_id = "com.simplemobiletools.musicplayer"
name = "Fossify Music"
description = "Simple music player with playlist support, equalizer, and sleep timer."
source = "fdroid"
fdroid_package_name = "com.simplemobiletools.musicplayer"

[calculator]
id = "calculator"
package_id = "com.simplemobiletools.calculator"
name = "Fossify Calculator"
description = "Clean calculator with basic and scientific modes."
source = "fdroid"
fdroid_package_name = "com.simplemobiletools.calculator"

[clock]
id = "clock"
package_id = "com.simplemobiletools.clock"
name = "Fossify Clock"
description = "Alarm clock, timer, and stopwatch in one simple app."
source = "fdroid"
fdroid_package_name = "com.simplemobiletools.clock"

[notes]
id = "notes"
package_id = "com.simplemobiletools.notes.pro"
name = "Fossify Notes"
description = "Quick and simple note-taking app with export options."
source = "fdroid"
fdroid_package_name = "com.simplemobiletools.notes.pro"

[calendar]
id = "calendar"
package_id = "com.simplemobiletools.calendar.pro"
name = "Fossify Calendar"
description = "Calendar and event planner with customizable reminders."
source = "fdroid"
fdroid_package_name = "com.simplemobiletools.calendar.pro"

[flashlight]
id = "flashlight"
package_id = "com.simplemobiletools.flashlight"
name = "Fossify Flashlight"
description = "Simple flashlight with brightness control and SOS mode."
source = "fdroid"
fdroid_package_name = "com.simplemobiletools.flashlight"

[maps]
id = "maps"
package_id = "net.osmand"
name = "OsmAnd"
description = "Offline maps and navigation powered by OpenStreetMap."
source = "fdroid"
fdroid_package_name = "net.osmand"
```

### Extra Non-Free Apps (`apps/extras/non-free.toml`)

Optional proprietary apps with direct APK downloads. **All extras require a `description` field**:

```toml
[whatsapp]
id = "whatsapp"
package_id = "com.whatsapp"
name = "WhatsApp"
description = "End-to-end encrypted messaging. Proprietary but allows direct APK download."
source = "direct"
download_url = "https://www.whatsapp.com/android/"
notes = "Download latest APK from official site"

[signal]
id = "signal"
package_id = "org.thoughtcrime.securesms"
name = "Signal"
description = "Privacy-focused encrypted messaging. Proprietary but open source and Play Services optional."
source = "direct"
download_url = "https://signal.org/android/apk/"
notes = "Official APK, no Play Services required"

[telegram]
id = "telegram"
package_id = "org.telegram.messenger"
name = "Telegram"
description = "Cloud-based messaging with channels and bots. Proprietary with official direct download."
source = "direct"
download_url = "https://telegram.org/android"
notes = "Official APK download"

[discord]
id = "discord"
package_id = "com.discord"
name = "Discord"
description = "Voice, video, and text chat platform. Proprietary with official direct APK."
source = "direct"
download_url = "https://discord.com/api/download?platform=android"
notes = "Official APK download"
```

### Device Profile App Selection

Device profiles reference apps by ID. **Note:** `camera` is NOT in the extras list — it's handled via interactive choice prompt.

```toml
# device-profiles/samsung-s24.toml

[apps]
# Core apps are always installed (implicit)
# Note: "camera" is NOT in this list - it's handled via interactive camera choice prompt
extras_free = ["weather", "music", "calculator", "clock", "notes", "calendar", "flashlight", "maps"]
extras_non_free = []
```

## Device Profiles

Device profiles live in `device-profiles/` and contain device-specific package removals plus app selections from the catalog.

### Maintainer Model

Each supported device has a dedicated maintainer responsible for:
- Keeping the profile current with OS updates
- Testing changes on real hardware
- Responding to issues related to that device

### Current Profiles

| Profile | Device | Maintainer |
|---------|--------|------------|
| `samsung-s24.toml` | Samsung Galaxy S24 | @glw907 |
| `pixel-8a.toml` | Google Pixel 8/8a | @glw907 (planned) |

### Conditional Package Removal

Some packages should only be removed based on user choice. Use the `conditional` field:

```toml
[[packages]]
id = "com.sec.android.app.camera"
name = "Samsung Camera"
source = "Samsung"
function = "Stock camera app with advanced post-processing"
category = "system"
action = "remove"
conditional = "camera"
removal_rationale = "Conditionally removed only if user chooses Fossify Camera. Offers better photo quality but has broken gallery links after configuration."
```

## Implementation Phases

Follow these in order. Each phase is testable independently.

### Phase 1: Foundation (1 day)
- `api/events.py` — Event types and dataclasses
- `core/profile.py` — Device profile TOML parsing, validation
- `core/apps_catalog.py` — Apps catalog loading and resolution
- `core/exceptions.py` — Exception hierarchy

**Test:** Load `device-profiles/samsung-s24.toml` and `apps/core.toml`, verify all fields parsed and apps resolved.

### Phase 2: ADB Wrapper (2 days)
- `core/adb.py` — Command execution, output parsing, error handling

**Test:** Mock `subprocess.run()`, verify correct commands generated.

### Phase 3: App Download (2 days)
- `core/downloader.py` — F-Droid index fetch, direct APK download, progress tracking

**Test:** Mock HTTP requests, verify download flow for both sources.

### Phase 4: Package Removal (1 day)
- `core/remover.py` — Iterate packages, handle failures gracefully

**Test:** Mock ADB responses for success/failure cases.

### Phase 5: Workflow Orchestration (1 day)
- `core/workflow.py` — Coordinate validation → camera choice → removal → download → install

**Test:** Mock all dependencies, verify event sequences.

### Phase 6: Controller API (0.5 days)
- `api/controller.py` — Thin wrapper, manages ADB lifecycle

### Phase 7: CLI Interface (2.5 days)

**7.1: Basic CLI Structure (0.5 days)**
- `cli.py` — Typer commands, Rich output formatting
- Basic progress display

**7.2: Interactive Camera Choice (0.5 days)**
- Detect stock camera package in device profile
- Present camera choice with tradeoffs
- Store user choice for conditional removal

**7.3: Interactive App Selection (1 day)**
- Load extras from apps catalog
- Present each app with description and source (Open Source vs Proprietary)
- Collect user selections
- Non-interactive mode: install all free extras, skip non-free

**7.4: Set Default Apps (0.5 days)**
- Use ADB to set installed apps as defaults
- Handle launcher, keyboard, dialer, messaging, gallery

### Phase 8: Testing and Polish (2 days)
- Comprehensive tests, error message review, documentation

## Code Standards

### Type Hints Required

```python
def get_device_model(self) -> str:
    """Get the device model string."""
    ...
```

### Google-Style Docstrings

```python
def download_apk(url: str, dest: Path) -> Path:
    """
    Download an APK file from a URL.
    
    Args:
        url: Download URL for the APK
        dest: Destination path for the downloaded file
        
    Returns:
        Path to the downloaded file
        
    Raises:
        DownloadError: If download fails or verification fails
    """
```

### Explicit Error Handling

```python
# Good
try:
    result = subprocess.run(...)
except subprocess.TimeoutExpired:
    raise ADBError("Command timed out")

# Bad — never use bare except
try:
    result = subprocess.run(...)
except:
    pass
```

### Absolute Imports Only

```python
# Good
from clearphone.core.adb import ADBDevice

# Bad
from .adb import ADBDevice
```

### Formatting

Use `ruff` for formatting and linting:

```bash
ruff check --fix .
ruff format .
```

## Writing Standards

All project writing—documentation, error messages, comments, commit messages—should follow [docs/style-guide.md](docs/style-guide.md). Key points:

- **Terminology**: Use "configured phone" not "safe phone"; "remove" not "block"
- **Avoid**: "de-Google", "Google-free", "escaping [company]'s ecosystem"—inaccurate and unnecessarily adversarial
- **Project goal**: Low-distraction, privacy-respecting phones (not anti-any-company)
- **Tone**: Friendly, matter-of-fact, no hype
- **Error messages**: Explain what happened and how to fix it
- **Audience awareness**: Technical docs assume technical readers; guides do not

## Error Handling

### Three Categories

1. **Validation errors** — Fail fast before making changes
   - Invalid profile, wrong device model, no device connected
   - Exit immediately with clear message

2. **Recoverable errors** — Log and continue
   - Package can't be removed (Knox-protected)
   - App download fails (network timeout)
   - Emit warning event, proceed with remaining items

3. **Critical errors** — Abort immediately
   - Device disconnected mid-configuration
   - ADB daemon crash
   - Emit `WorkflowFailedEvent`, raise `CriticalConfigurationError`

### Error Messages

All errors must explain what happened and how to fix it:

```
✗ Error: Wrong device model

Expected: Samsung Galaxy S24 (SM-S921*)
Found: Samsung Galaxy S23 (SM-S911U)

This profile is specifically for the S24.

To configure this device:
  1. Check if device-profiles/samsung-s23.toml exists
  2. Or create a custom profile
```

## Testing

### Unit Tests — Mock External Dependencies

```python
from unittest.mock import patch, MagicMock

@patch('subprocess.run')
def test_package_removal(mock_run):
    mock_run.return_value = MagicMock(
        returncode=0,
        stdout="Success",
        stderr=""
    )
    # Test code here
```

### Test Edge Cases Explicitly

- Invalid TOML syntax
- Missing required fields
- Unknown app ID in device profile
- Knox-protected packages (Samsung)
- Network timeouts
- Device disconnection

### Integration Tests

- Load `device-profiles/samsung-s24.toml` with apps catalog
- Mock ADB and HTTP responses
- Verify event sequences
- Test full workflow end-to-end

## Key Design Decisions

### Shared Apps Catalog

Apps are defined once in `apps/` and referenced by ID in device profiles. This:
- Eliminates duplication across device profiles
- Centralizes app metadata and download URLs
- Keeps device profiles focused on device-specific concerns

### Interactive Camera Choice

Present camera choice BEFORE package removal:
- Stock camera: Better photo quality, broken UI links to removed gallery
- Fossify Camera: Simpler integration, lower photo quality
- Use `conditional = "camera"` field to remove stock camera only if user chooses Fossify

### Rootless ADB Only

Uses `pm uninstall --user 0` (no root required). Works on locked bootloaders, safer than root operations.

### Continue on Recoverable Errors

Some packages can't be removed (Knox-protected on Samsung, system-critical). Better to complete configuration with warnings than fail entirely.

### F-Droid + Direct APK

Open-source APKs downloaded from F-Droid's repository; proprietary APKs downloaded from official sources. All apps installed via ADB. No F-Droid app or Play Store required.

### No Customization UI

Device profiles define everything. No settings, no options, no "just this once." Technical users edit TOML directly.

### Device Maintainer Model

Each profile has a dedicated maintainer. This ensures profiles stay current and someone is accountable for device-specific issues.

## ADB Command Reference

```bash
# Device info
adb shell getprop ro.product.model
adb shell getprop ro.build.version.release

# Package management
adb shell pm list packages
adb shell pm uninstall --user 0 <package-id>
adb shell pm disable-user --user 0 <package-id>

# App installation
adb install <path-to-apk>
adb install -r <path-to-apk>  # Overwrite existing

# Set default apps
adb shell cmd role add-role-holder android.app.role.HOME <launcher-package>
adb shell settings put secure default_input_method <keyboard-package>

# Connection
adb devices
adb wait-for-device
adb kill-server
```

Always use `--user 0` for package operations. Parse both stdout and stderr—some commands return exit code 0 on failure.

## Dependencies

```toml
[project]
requires-python = ">=3.11"
dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.0.0",
    "httpx>=0.27.0",
]
```

## Specifications Reference

| Document | Purpose |
|----------|---------|
| `docs/requirements.md` | Scope and constraints |
| `docs/implementation-order.md` | Phase-by-phase build plan |
| `docs/api-spec.md` | Event system and controller |
| `docs/profile-schema.md` | Device profile TOML structure |
| `docs/apps-catalog-schema.md` | Apps catalog TOML structure |
| `docs/adb-commands.md` | ADB command reference |
| `docs/fdroid-integration.md` | F-Droid download implementation |
| `docs/direct-apk-integration.md` | Direct APK download security |
| `docs/error-handling.md` | All error scenarios |
| `docs/cli-spec.md` | CLI output formats |
| `docs/style-guide.md` | Terminology and writing standards |

## Success Criteria

The tool should:

1. Install cleanly (`pip install .`)
2. Connect to Samsung S24 or Pixel 8/8a via USB
3. Present camera choice with honest tradeoffs
4. Run `clearphone configure device-profiles/<device>.toml`
5. Prompt for optional apps with descriptions
6. Show clear progress updates
7. Complete configuration in 15–30 minutes
8. Provide a summary of successes and failures

## What We're NOT Building (v0.1.0)

- TUI interface (next phase)
- Web interface (future, pending UX expertise)
- Device support beyond S24 and Pixel 8/8a
- Play Store integration
- GUI
- Custom ROM flashing
- Root-required operations

## License

This project is licensed under GPL v3. Add this header to all new Python files:

```python
# Clearphone - Configure Android phones for minimal distraction
# Copyright (C) 2026 [Your Name]
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
