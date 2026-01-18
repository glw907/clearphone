# Clearphone Roadmap

This document outlines the direction of Clearphone development. It's a living document—priorities may shift based on community feedback and contributions.

## Core Philosophy

**Browserless and appstore-less by default.** A Clearphone-configured device has no web browser and no app store. This is the core value proposition:

- The browser is the primary distraction vector (social media, news, endless scrolling)
- The app store enables impulse installs
- Clearphone provides everything most users need; messaging apps can be installed directly

Users who need Play Store access for banking/work apps can opt in during setup, then run `clearphone finalize` when done.

## Current Status

**Version:** 0.1.0 (CLI prototype)
**Stage:** Early development
**Focus:** Core functionality on Samsung Galaxy S24

## Phase 1: CLI Foundation (Current)

The command-line interface that proves the core concept works.

- [x] Device profile system (TOML-based)
- [x] Shared apps catalog
- [x] Pure-Python ADB communication (no external dependencies)
- [x] Package removal with Knox protection handling
- [x] F-Droid APK downloads
- [x] Interactive camera choice
- [x] Optional extras selection
- [ ] "Need additional apps?" prompt (disable Play Store immediately if no)
- [ ] `clearphone finalize` command (for users who kept Play Store)
- [ ] Direct APK downloads for proprietary apps
- [ ] Google Pixel 8/8a device profile
- [ ] Post-install app configuration (MMS settings, launcher defaults, etc.)

## Phase 2: TUI Interface

A terminal user interface for power users and developers. Richer interaction without web complexity.

- [ ] Full-screen terminal UI (likely using Textual)
- [ ] Real-time progress visualization
- [ ] Interactive package selection with descriptions
- [ ] Profile browsing and comparison

## Phase 3: Web Interface

Broader accessibility for less technical users. Requires UX expertise.

- [ ] Local web server for configuration
- [ ] Mobile-friendly interface
- [ ] Step-by-step wizard
- [ ] Visual progress tracking

## Future Ideas

These are ideas that may become priorities based on community interest. They're not commitments.

### Configurable Browser/App Store Visibility

For users who need browser or Play Store but want reduced temptation:

- **Hidden mode**: Apps remain installed but hidden from Olauncher home screen
- **Visible mode**: Light-touch configuration for users who need full access
- User chooses during setup: disabled (default) / hidden / visible

### Clearphone Launcher (Olauncher Fork)

A fork of Olauncher with Clearphone-specific features:

- Programmatic configuration via ADB (hidden apps, layout, settings)
- Locked settings option to prevent accidental changes
- Integration with Clearphone Updater
- "Clearphone mode" enforcing minimal-distraction defaults

### Curated Wallpapers, Ringtones, and Alert Sounds

A small, thoughtfully curated set of personalization options:

- 5-10 wallpapers (muted colors, simple patterns, nature imagery)
- 3-5 ringtones and alert sounds (calm, unobtrusive)
- Installed during setup, with sensible defaults
- Makes the phone feel personal without endless customization rabbit holes

### Clearphone Updater

A companion app that keeps Clearphone-installed apps up to date. Would run on the configured phone itself.

- Check F-Droid for updates to installed apps
- Background update checks with notifications
- Manual or automatic update installation
- Respect the "no Play Store" philosophy

### Additional Device Support

- Samsung Galaxy S23, S22, A-series
- Google Pixel 7, 6 series
- OnePlus devices
- Other manufacturers with community maintainers

### Profile Sharing

- Community-contributed device profiles
- Profile validation and testing standards
- Searchable profile registry

### Backup and Restore

- Export list of installed apps and settings
- Restore configuration to a new/reset device
- Migration between devices

### Enterprise Features

- Fleet management for multiple devices
- Centralized profile distribution
- Compliance reporting

## Non-Goals

Things we explicitly won't build:

- **Root-required operations** — We stay within Android's user-space capabilities
- **Custom ROM flashing** — Out of scope; use existing tools
- **Play Store automation** — We don't automate downloads from Play Store; we disable it by default
- **Always-connected services** — The configured phone should work offline
- **Browser by default** — The default configuration is browserless; users must opt in to keep browser access

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get involved.

**Device maintainers wanted:** If you have a device not yet supported and want to create/maintain a profile, open an issue.

**Feature requests:** Open a GitHub issue with the `enhancement` label. Describe the use case, not just the solution.

## Versioning Plan

- **0.x** — Early development, breaking changes expected
- **1.0** — Stable CLI with Samsung S24 and Pixel 8/8a support
- **2.0** — TUI interface
- **3.0** — Web interface

---

*Last updated: January 2026*
