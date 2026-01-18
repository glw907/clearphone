# Clearphone

**Transform your Android smartphone into a minimal, low-distraction device.**

Clearphone removes pre-installed apps and installs privacy-focused open-source alternatives, giving you a phone that respects your attention and your privacy.

## What It Does

- **Removes pre-installed apps**: Bixby, Samsung/Google/carrier apps, browser, and Play Store
- **Browserless and appstore-less by default**: No web browser, no app store — just the apps you need
- **Installs FOSS replacements**: Launcher, keyboard, dialer, messaging, contacts, gallery, file manager
- **Camera choice**: Keep your high-quality stock camera or install Fossify Camera for simpler integration
- **Optional extras**: Weather, music, calculator, calendar, maps, and more
- **Optional proprietary apps**: WhatsApp, Signal, Telegram, Discord (direct APK downloads, no Play Store)
- **No root required**: Works on locked bootloaders
- **Zero external dependencies**: No need to install ADB or Android SDK separately

## Quick Start

```bash
# Install
pip install clearphone

# Connect phone via USB (enable USB debugging first)
# Configure your phone
clearphone configure device-profiles/samsung-s24.toml
```

That's it. No ADB installation, no SDK setup, no path configuration.

**First-time setup:**
1. Enable USB debugging on your phone (Settings → Developer Options → USB debugging)
2. Connect your phone via USB
3. Run clearphone — it will prompt you to authorize the connection on your phone
4. Tap "Allow" on your phone's USB debugging prompt

**What happens during setup:**

1. **Camera choice** — Choose between stock camera (better quality) or Fossify Camera (simpler, lower quality)
2. **Additional apps prompt** — Do you need apps from Play Store? (banking, work apps, etc.)
   - **If no (default):** Browser and Play Store are disabled immediately
   - **If yes:** Play Store is kept temporarily — install what you need, then run `clearphone finalize`
3. **Pre-installed app removal** — Removes Bixby, carrier apps, social media, browser, etc.
4. **Core apps installation** — Downloads APKs from F-Droid repository and installs launcher, keyboard, dialer, messaging, contacts, gallery, file manager
5. **Optional apps** — Prompts you to choose from extras (open source and proprietary)
6. **Default configuration** — Sets installed apps as defaults

**Most users don't need the Play Store.** The Clearphone app suite covers essential phone functions, and messaging apps (Signal, WhatsApp, etc.) can be installed directly without Play Store. If you're unsure, choose "no" — you can always factory reset and try again if needed.

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
- **Zero-configuration install** — `pip install clearphone` and you're ready. No SDK, no ADB, no path setup.
- **Device profiles** maintained by real users testing on real hardware
- **Shared apps catalog** — no duplication across profiles
- **Interactive camera choice** with honest tradeoff explanation
- **Continue on recoverable errors** — better to complete with warnings than fail entirely
- **Event-driven architecture** — same core logic for CLI, TUI, and future web interface

## Design Philosophy

### Browserless and Appstore-less by Default

A Clearphone-configured device has **no web browser and no app store** by default. This is intentional:

- **The browser is the biggest distraction vector.** Social media, news, shopping, endless scrolling — it all happens through the browser. Removing it eliminates the temptation entirely.
- **The app store enables impulse installs.** Without it, you can't impulsively download distracting apps. Every app on your phone is there because you deliberately chose it during setup.
- **You don't need them.** Clearphone installs everything most people need: calls, texts, camera, maps, music, weather. Messaging apps (Signal, WhatsApp) can be installed directly without Play Store.

**For users who need more flexibility**, Clearphone will offer an option to keep the browser and/or Play Store available but hidden from the home screen (planned feature). This provides a middle ground between full lockdown and unrestricted access.

### Minimal External Dependencies

Clearphone aims for the simplest possible installation experience. We bundle or implement everything needed to communicate with your phone:

- **No ADB binary required** — We use a pure-Python USB implementation to communicate directly with your device
- **No Android SDK required** — Everything is self-contained
- **No system-level configuration** — No udev rules (Linux), no driver installation (Windows), no special setup
- **Single command install** — `pip install clearphone` includes everything

This means a user can go from "never heard of Clearphone" to "configuring their phone" in under a minute.

### Rootless Operation

Uses `pm uninstall --user 0`, which works on locked bootloaders and is safer than root operations. Your phone's warranty and security model remain intact.

### Honest Tradeoffs

We don't pretend everything is perfect. When you choose between stock camera and Fossify Camera, we tell you exactly what you gain and lose with each option.

## Key Design Decisions

**Pure-Python USB communication** — Connects directly to your phone via USB using the `adb-shell` library. No external ADB binary needed. RSA keys for device authentication are generated automatically and stored in `~/.clearphone/`.

**F-Droid Repository + Direct APK Downloads** — Open-source apps downloaded from F-Droid's repository; proprietary apps downloaded from official sources. No F-Droid app or Google Play required.

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

The entire F-Droid ecosystem makes this project possible. F-Droid provides trusted, reproducible builds of open-source Android apps and maintains the infrastructure for secure distribution. Without F-Droid, building a privacy-respecting phone with open-source apps would require users to compile and verify every app themselves.

### Fossify

The Fossify suite (formerly Simple Mobile Tools) provides essential phone functionality with clean, simple interfaces. Clearphone uses Fossify Dialer, Messages, Contacts, Gallery, Camera (optional), Files, Music, Calculator, Clock, Notes, Calendar, and Flashlight. These apps prove that open-source alternatives can be both beautiful and functional, without ads, tracking, or unnecessary permissions.

### Olauncher

Olauncher provides the minimal launcher that reduces distractions and helps users focus on what matters. Its clean, text-based interface is the foundation of the configured phone experience.

### FUTO Keyboard

FUTO Keyboard delivers privacy-focused typing with offline voice input, ensuring your keystrokes and voice data never leave your device.

### Breezy Weather

Breezy Weather is a beautiful, privacy-focused weather app that provides detailed forecasts without tracking or ads. It pulls data from multiple sources (Open-Meteo, AccuWeather, and others) and presents it in a clean, customizable interface. It proves open-source apps can match or exceed proprietary alternatives in both design and functionality.

### OsmAnd & OpenStreetMap

OsmAnd (OSM Automated Navigation Directions) provides offline maps and turn-by-turn navigation powered by OpenStreetMap data. This is crucial for a low-distraction, privacy-respecting phone — you can download entire regions for offline use, meaning no tracking, no data mining, and navigation that works even without cell service. OpenStreetMap itself deserves recognition as a community-built, open-data alternative to proprietary mapping services. It's proof that collaborative, open models can compete with tech giants.

### adb-shell

The [adb-shell](https://github.com/JeffLIrion/adb_shell) Python library enables Clearphone's zero-dependency approach by providing pure-Python ADB protocol implementation. This eliminates the need for users to install the Android SDK or configure ADB separately.

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
