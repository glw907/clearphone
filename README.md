# Clearphone

**Transform your Android smartphone into a minimal, low-distraction device.**

Clearphone removes bloatware and installs privacy-focused open-source alternatives, giving you a phone that respects your attention and your privacy.

## What It Does

- **Removes bloatware**: Bixby, Samsung/Google/carrier pre-installed apps
- **Installs FOSS replacements**: Launcher, keyboard, dialer, messaging, contacts, gallery, file manager
- **Camera choice**: Keep your high-quality stock camera or install Fossify Camera for simpler integration
- **Optional extras**: Weather, music, calculator, calendar, maps, and more
- **Optional proprietary apps**: WhatsApp, Signal, Telegram, Discord (direct APK downloads, no Play Store)
- **No root required**: Uses ADB commands that work on locked bootloaders

## Quick Start

```bash
# Install
pip install clearphone

# Connect phone via USB (enable USB debugging first)
adb devices

# Configure your phone
clearphone configure device-profiles/samsung-s24.toml
```

**What happens:**
1. **Camera choice** — Choose between stock camera (better quality, broken gallery links) or Fossify Camera (simpler, lower quality)
2. **Package removal** — Removes bloatware and conditionally removes stock camera if you chose Fossify
3. **Core apps installation** — Installs launcher, keyboard, dialer, messaging, contacts, gallery, file manager from F-Droid
4. **Optional apps** — Prompts you to choose from extras (open source and proprietary)
5. **Default configuration** — Sets installed apps as defaults

## Supported Devices

| Device | Profile | Maintainer |
|--------|---------|------------|
| Samsung Galaxy S24 | `device-profiles/samsung-s24.toml` | @glw907 |
| Google Pixel 8/8a | `device-profiles/pixel-8a.toml` | *Planned* |

## Project Status

**Current version:** 0.1.0 (CLI prototype)
**Interface:** Command-line only
**Stability:** Early development — expect changes

## Why Clearphone?

Modern smartphones come loaded with apps you didn't ask for and can't remove. Carriers, manufacturers, and platform providers all want your attention and your data. Clearphone gives you a phone that serves you, not them.

**What makes Clearphone different:**
- Device profiles maintained by real users testing on real hardware
- Shared apps catalog — no duplication across profiles
- Interactive camera choice with honest tradeoff explanation
- Continue on recoverable errors — better to complete with warnings than fail entirely
- Event-driven architecture — same core logic for CLI, TUI, and future web interface

## Key Design Decisions

**Rootless ADB only** — Uses `pm uninstall --user 0`, which works on locked bootloaders and is safer than root operations.

**F-Droid + Direct APK** — Open-source apps from F-Droid; select proprietary apps via official direct downloads. No Google Play dependency.

**Device maintainer model** — Each profile has a dedicated maintainer who tests on real hardware and keeps it current.

**Camera choice before removal** — Ask users whether they want stock camera (better photos, broken UI links) or Fossify Camera (simpler, lower quality) BEFORE removing packages. Conditional package removal based on choice.

**No customization UI** — Device profiles define everything. Technical users edit TOML directly. No "just this once" options.

**Continue on recoverable errors** — Some packages can't be removed (Knox-protected, system-critical). Configuration completes with warnings.

## Architecture

**Event-driven core** — All core logic is UI-agnostic and communicates through events. No module prints directly to console.

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

## Documentation

- `docs/requirements.md` — Scope and constraints
- `docs/implementation-order.md` — Phase-by-phase build plan
- `docs/profile-schema.md` — Device profile TOML structure
- `docs/apps-catalog-schema.md` — Apps catalog TOML structure
- `docs/cli-spec.md` — CLI output formats
- `docs/style-guide.md` — Terminology and writing standards
- `CLAUDE.md` — Development guide for AI-assisted development

## Contributing

This project is in early development. Device profile contributions are welcome once the core is stable.

If you want to become a device maintainer:
1. Test the tool on your device
2. Create or update a device profile
3. Commit to keeping it current with OS updates

See `CONTRIBUTING.md` for guidelines.

## Acknowledgments

This project stands on the shoulders of giants:

### F-Droid

The entire F-Droid ecosystem makes this project possible. F-Droid provides trusted, reproducible builds of open-source Android apps and maintains the infrastructure for secure distribution. Without F-Droid, building a Google-free phone would require users to compile and verify every app themselves.

### Fossify Apps

The Fossify suite provides essential phone functionality with clean, simple interfaces:

- **Olauncher** — Minimal launcher that reduces distractions
- **FUTO Keyboard** — Privacy-focused keyboard with offline voice typing
- **Fossify Dialer** — Clean dialer with call blocking and recording
- **Fossify Messages** — Simple SMS/MMS without Google dependencies
- **Fossify Contacts** — Contact management with import/export
- **Fossify Gallery** — Photo and video gallery with editing tools
- **Fossify Camera** — Simple camera app (optional replacement for stock)
- **Fossify Files** — File manager with network storage support
- **Fossify Music** — Local music player with playlists and equalizer
- **Fossify Calculator** — Basic and scientific calculator modes
- **Fossify Clock** — Alarms, timer, and stopwatch
- **Fossify Notes** — Quick note-taking with export options
- **Fossify Calendar** — Event management and reminders
- **Fossify Flashlight** — Brightness control and SOS mode

### Other Open Source Projects

- **Breezy Weather** — Beautiful, detailed weather forecasts
- **OsmAnd** — Offline maps and navigation powered by OpenStreetMap

### Proprietary Software Vendors

Thank you to **Meta** (WhatsApp), **Signal Foundation** (Signal), **Telegram** (Telegram), and **Discord** for making direct APK downloads available. This allows users to install these apps without Google Play Services, preserving choice and reducing platform lock-in.

### Google and the Android Open Source Project

Thank you to **Google** for keeping Android open enough for projects like this to exist. The ability to use ADB to remove pre-installed apps and sideload alternatives is not guaranteed — it requires deliberate decisions to preserve user freedom.

We hope Google continues to maintain Android's openness, even as platform and business pressures push toward more restrictive models.

## License

Clearphone is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

**What this means:**
- ✓ You can use, modify, and distribute this software freely
- ✓ You must share modifications under the same license
- ✓ Source code must be made available
- ✓ No warranty is provided

**About the apps Clearphone installs:**

The GPL v3 license applies **only to the Clearphone tool itself** (the code that configures your phone). It does **not** apply to the apps that Clearphone installs.

Each app (Fossify Gallery, WhatsApp, Signal, etc.) has its own license. Installing proprietary apps via Clearphone does not make them GPL-licensed. The GPL's "mere aggregation" principle means distributing GPL software alongside non-GPL software is perfectly fine, as long as they remain separate works.

Clearphone is a configuration tool, not an app distributor — it directs your phone to download apps from their original sources (F-Droid, official APK sites).

See `LICENSE` for the full license text.

---

**Status:** Early development
**Maintainer:** @glw907
**Contributions:** Welcome once core is stable
