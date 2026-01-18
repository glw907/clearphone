# Clearphone Requirements

> **Version:** 0.1.0
> **Last Updated:** 2026-01-17
> **Status:** Draft

This document defines the functional and non-functional requirements for Clearphone, organized by development phase.

---

## 1. Functional Requirements

### Phase One: Core & CLI

#### FR-1.1: Device Connection

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-1.1.1 | Connect to Android device via USB without external ADB binary | Must | - |
| FR-1.1.2 | Auto-generate RSA keys for device authentication | Must | - |
| FR-1.1.3 | Detect device model and Android version | Must | - |
| FR-1.1.4 | Validate device matches profile's model pattern | Must | - |
| FR-1.1.5 | Handle "Allow USB debugging" prompt gracefully | Must | - |
| FR-1.1.6 | Detect when no device is connected | Must | - |
| FR-1.1.7 | Detect when multiple devices are connected | Should | - |

#### FR-1.2: Device Profiles

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-1.2.1 | Load device profile from TOML file | Must | - |
| FR-1.2.2 | Validate profile has required fields (device, packages) | Must | - |
| FR-1.2.3 | Support conditional package removal based on user choice | Must | - |
| FR-1.2.4 | Samsung Galaxy S24 profile complete and tested | Must | - |
| FR-1.2.5 | Google Pixel 8/8a profile complete and tested | Should | #2 |
| FR-1.2.6 | Validate profile app references against apps catalog | Must | - |

#### FR-1.3: Apps Catalog

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-1.3.1 | Load core apps from `apps/core.toml` | Must | - |
| FR-1.3.2 | Load optional free apps from `apps/extras/free.toml` | Must | - |
| FR-1.3.3 | Load optional proprietary apps from `apps/extras/non-free.toml` | Must | - |
| FR-1.3.4 | Resolve app references by ID | Must | - |
| FR-1.3.5 | Report unknown app IDs in profile | Must | - |

#### FR-1.4: Package Removal

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-1.4.1 | Remove packages using `pm uninstall --user 0` | Must | - |
| FR-1.4.2 | Skip packages not installed on device | Must | - |
| FR-1.4.3 | Skip Knox-protected packages with warning | Must | - |
| FR-1.4.4 | Continue on removal failure, report at end | Must | - |
| FR-1.4.5 | Support dry-run mode (no actual changes) | Must | - |
| FR-1.4.6 | Remove stock browsers (Chrome, Samsung Browser) always | Must | - |

#### FR-1.5: App Download

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-1.5.1 | Download APKs from F-Droid repository | Must | - |
| FR-1.5.2 | Verify F-Droid APK checksums (SHA-256) | Must | - |
| FR-1.5.3 | Download APKs from direct URLs (proprietary apps) | Must | #3 |
| FR-1.5.4 | Show download progress | Should | - |
| FR-1.5.5 | Cache downloaded APKs for retry/reuse | Should | - |
| FR-1.5.6 | Handle network errors gracefully | Must | - |

#### FR-1.6: App Installation

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-1.6.1 | Install APKs via ADB push + pm install | Must | - |
| FR-1.6.2 | Install core apps in priority order | Must | - |
| FR-1.6.3 | Report installation failures | Must | - |
| FR-1.6.4 | Clean up temporary APK files after install | Should | - |

#### FR-1.7: Default App Configuration

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-1.7.1 | Set Olauncher as default launcher | Must | - |
| FR-1.7.2 | Set FUTO Keyboard as default input method | Must | - |
| FR-1.7.3 | Set Fossify Dialer as default phone app | Must | - |
| FR-1.7.4 | Set Fossify Messages as default SMS app | Must | - |
| FR-1.7.5 | Set Fossify Gallery as default gallery | Should | - |
| FR-1.7.6 | Configure MMS-friendly defaults in Fossify Messages | Should | #14 |

#### FR-1.8: CLI Commands

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-1.8.1 | `clearphone configure <profile>` - main configuration | Must | #20 |
| FR-1.8.2 | `clearphone list-profiles` - show available profiles | Must | #20 |
| FR-1.8.3 | `clearphone show-profile <profile>` - show profile details | Should | #20 |
| FR-1.8.4 | `--dry-run` flag for preview mode | Must | #20 |
| FR-1.8.5 | `--interactive` flag for guided prompts | Must | #20 |
| FR-1.8.6 | Non-interactive mode as default | Must | #20 |

#### FR-1.9: CLI Global Toggles

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-1.9.1 | `--enable-browser` - install Fennec browser | Must | #20 |
| FR-1.9.2 | `--disable-browser` - remove Fennec browser | Must | #20 |
| FR-1.9.3 | `--enable-play-store` - keep Play Store | Must | #20 |
| FR-1.9.4 | `--disable-play-store` - disable Play Store | Must | #20 |
| FR-1.9.5 | `--safe-mode` - disable both browser and Play Store | Must | #20 |
| FR-1.9.6 | `--smartphone-mode` - enable both browser and Play Store | Must | #20 |

#### FR-1.10: CLI App Install Options

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-1.10.1 | `--keep-vendor-camera` - keep stock camera | Must | #20 |
| FR-1.10.2 | `--install-weather` - install Breezy Weather | Should | #20 |
| FR-1.10.3 | `--install-music` - install Fossify Music | Should | #20 |
| FR-1.10.4 | `--install-calculator` - install Fossify Calculator | Should | #20 |
| FR-1.10.5 | `--install-clock` - install Fossify Clock | Should | #20 |
| FR-1.10.6 | `--install-notes` - install Fossify Notes | Should | #20 |
| FR-1.10.7 | `--install-calendar` - install Fossify Calendar | Should | #20 |
| FR-1.10.8 | `--install-flashlight` - install Fossify Flashlight | Should | #20 |
| FR-1.10.9 | `--install-maps` - install OsmAnd | Should | #20 |
| FR-1.10.10 | `--install-whatsapp` - install WhatsApp | Should | #20 |
| FR-1.10.11 | `--install-signal` - install Signal | Should | #20 |
| FR-1.10.12 | `--install-telegram` - install Telegram | Should | #20 |
| FR-1.10.13 | `--install-discord` - install Discord | Should | #20 |

#### FR-1.11: Progress and Feedback

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-1.11.1 | Show phase-by-phase progress | Must | - |
| FR-1.11.2 | Show package removal progress | Must | - |
| FR-1.11.3 | Show download progress | Should | - |
| FR-1.11.4 | Show installation progress | Must | - |
| FR-1.11.5 | Display summary at end (success/warning/failure counts) | Must | - |
| FR-1.11.6 | Show clear error messages with remediation steps | Must | - |

---

### Phase Two: Olauncher Fork

#### FR-2.1: Launcher Customization

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-2.1.1 | Fork Olauncher repository | Must | #7 |
| FR-2.1.2 | Add Clearphone branding/theming | Should | #7 |
| FR-2.1.3 | Hide browser from home screen (configurable) | Must | #6 |
| FR-2.1.4 | Hide Play Store from home screen (configurable) | Must | #6 |
| FR-2.1.5 | Pre-configure home screen layout | Should | #7 |
| FR-2.1.6 | Read configuration from file (Clearphone integration) | Should | #7 |

#### FR-2.2: Companion App (Optional)

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-2.2.1 | Clearphone Updater app for OTA profile updates | Could | #4 |
| FR-2.2.2 | Check for app updates from F-Droid | Could | #4 |

---

### Phase Three: TUI Interface

#### FR-3.1: Terminal UI

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-3.1.1 | Interactive device profile selection | Must | #5 |
| FR-3.1.2 | Real-time progress display with rich formatting | Must | #5 |
| FR-3.1.3 | Interactive camera choice with visual comparison | Must | #5 |
| FR-3.1.4 | Extras selection with descriptions and categories | Must | #5 |
| FR-3.1.5 | Error display with recovery options | Should | #5 |
| FR-3.1.6 | Configuration summary and confirmation | Must | #5 |
| FR-3.1.7 | Keyboard navigation | Must | #5 |

---

### Phase Four: Web Interface

#### FR-4.1: Web UI

| ID | Requirement | Priority | Issue |
|----|-------------|----------|-------|
| FR-4.1.1 | Browser-based configuration wizard | Must | - |
| FR-4.1.2 | Device connection via local server or WebUSB | Must | - |
| FR-4.1.3 | Profile browser with filtering | Should | - |
| FR-4.1.4 | Step-by-step guided workflow | Must | - |
| FR-4.1.5 | Progress visualization | Must | - |
| FR-4.1.6 | Mobile-friendly responsive design | Should | - |
| FR-4.1.7 | Self-hosting documentation | Should | - |

---

## 2. Non-Functional Requirements

### NFR-1: Installation & Dependencies

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-1.1 | Install with single `pip install clearphone` command | Must |
| NFR-1.2 | No external ADB binary required | Must |
| NFR-1.3 | No Android SDK required | Must |
| NFR-1.4 | No system-level configuration (udev rules, drivers) | Must |
| NFR-1.5 | Work on Python 3.11+ | Must |
| NFR-1.6 | Work on macOS, Linux, Windows | Must |

### NFR-2: Performance

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-2.1 | Full configuration completes in under 30 minutes | Should |
| NFR-2.2 | Profile loading under 1 second | Must |
| NFR-2.3 | APK downloads show progress, don't appear frozen | Must |
| NFR-2.4 | Handle slow/unreliable network connections | Should |

### NFR-3: Security

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-3.1 | Store RSA keys securely in `~/.clearphone/` | Must |
| NFR-3.2 | Verify F-Droid APK checksums | Must |
| NFR-3.3 | Download proprietary APKs only from official sources | Must |
| NFR-3.4 | No root access required | Must |
| NFR-3.5 | Use HTTPS for all downloads | Must |
| NFR-3.6 | Don't store or transmit user data | Must |

### NFR-4: Reliability

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-4.1 | Continue on recoverable errors (Knox-protected packages) | Must |
| NFR-4.2 | Fail fast on validation errors (before making changes) | Must |
| NFR-4.3 | Detect device disconnection and abort safely | Must |
| NFR-4.4 | Provide clear error messages with remediation steps | Must |
| NFR-4.5 | Dry-run mode for safe preview | Must |

### NFR-5: Maintainability

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-5.1 | Event-driven architecture for UI-agnostic core | Must |
| NFR-5.2 | Type hints on all functions | Must |
| NFR-5.3 | Google-style docstrings | Should |
| NFR-5.4 | Unit test coverage for core modules | Must |
| NFR-5.5 | Integration tests for full workflow | Should |
| NFR-5.6 | Code formatted with ruff | Must |

### NFR-6: Usability

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-6.1 | Non-technical users can follow guided prompts | Should |
| NFR-6.2 | Technical users can use non-interactive mode | Must |
| NFR-6.3 | Clear documentation for first-time setup | Must |
| NFR-6.4 | Honest tradeoff explanations (camera choice) | Must |

### NFR-7: Compatibility

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-7.1 | Samsung Galaxy S24 (One UI 6, Android 14) | Must |
| NFR-7.2 | Google Pixel 8/8a (Stock Android 14) | Should |
| NFR-7.3 | Locked bootloaders supported | Must |
| NFR-7.4 | USB debugging enabled required | Must |

---

## 3. Acceptance Criteria

### Phase One: Core & CLI

The phase is complete when:

1. **Installation works**
   - `pip install clearphone` succeeds on macOS, Linux, Windows
   - No additional dependencies need manual installation

2. **Device connection works**
   - Samsung S24 connects via USB
   - RSA keys generated automatically
   - "Allow USB debugging" prompt handled

3. **Configuration completes**
   - `clearphone configure device-profiles/samsung-s24.toml` runs to completion
   - Pre-installed apps removed (Bixby, Samsung apps, carrier apps)
   - Core apps installed (Olauncher, FUTO Keyboard, Fossify suite)
   - Default apps set correctly

4. **CLI options work**
   - `--dry-run` shows changes without making them
   - `--interactive` prompts for extras
   - `--install-whatsapp` installs WhatsApp
   - `--smartphone-mode` keeps browser and Play Store
   - Global toggles work on configured phones

5. **Error handling works**
   - Knox-protected packages skipped with warning
   - Summary shows success/warning/failure counts
   - Clear error messages with remediation steps

6. **Tests pass**
   - `pytest tests/unit/` passes
   - `pytest tests/integration/` passes
   - `ruff check .` passes
   - `mypy clearphone/` passes

### Phase Two: Olauncher Fork

The phase is complete when:

1. Forked Olauncher available on F-Droid or as APK
2. Browser/Play Store hidden from home screen by default
3. Configuration readable from Clearphone settings file
4. Clearphone CLI installs forked launcher instead of stock Olauncher

### Phase Three: TUI Interface

The phase is complete when:

1. `clearphone --tui` launches terminal interface
2. All CLI functionality accessible via TUI
3. Keyboard navigation works throughout
4. Rich progress display with colors and spinners
5. Works in standard terminal emulators (iTerm, GNOME Terminal, Windows Terminal)

### Phase Four: Web Interface

The phase is complete when:

1. `clearphone --web` launches local web server
2. Browser connects to local server and detects device
3. Step-by-step wizard guides user through configuration
4. Progress visualization works
5. Mobile-friendly layout

---

## 4. Traceability

### Labels

| Label | Description |
|-------|-------------|
| `phase: one` | Core & CLI |
| `phase: two` | Olauncher fork |
| `phase: three` | TUI interface |
| `phase: four` | Web interface |

### Key Issues

| Issue | Title | Phase |
|-------|-------|-------|
| #2 | Add Google Pixel 8/8a device profile | Phase One |
| #3 | Implement direct APK downloads for proprietary apps | Phase One |
| #5 | TUI interface | Phase Three |
| #6 | Configurable Play Store and browser visibility | Phase Two |
| #7 | Develop configurable Olauncher fork | Phase Two |
| #14 | Set MMS-friendly defaults in Fossify Messages | Phase One |
| #17 | Project Roadmap | All |
| #20 | Set up command line arguments | Phase One |

### Document References

| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | Development guide, architecture, implementation |
| `docs/style-guide.md` | Terminology and writing standards |
| `device-profiles/*.toml` | Device-specific configurations |
| `apps/*.toml` | App catalog definitions |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-01-17 | @glw907 | Initial draft |
