# Clearphone

Clearphone is a developer-focused tool for configuring Android phones into **low-distraction, privacy-respecting devices**.

It removes selected pre-installed system and vendor apps, installs a curated replacement app set, and applies device-specific configuration using explicit, repeatable steps — all **without root, custom ROMs, or Device Owner / MDM privileges**.

Clearphone is intentionally opinionated. It prioritizes clarity, auditability, and honest tradeoffs over flexibility or enforcement claims.

---

## Project Status

Clearphone is currently in **Phase I**.

Phase I delivers a **working command-line prototype** intended for developers and early adopters. It is not consumer-ready software and does not attempt to solve onboarding, UX polish, or long-term device management.

The CLI is treated as a reference interface for validating core architecture decisions.

---

## What Clearphone Does

Clearphone configures a supported Android device into a strict “clearphone” state by default:

- Removes or disables selected OEM, carrier, and system apps
- Removes or disables the stock browser
- Removes or disables the Google Play Store app
- Installs a curated set of replacement apps (primarily open source)
- Applies device-specific package handling via maintained profiles
- Makes all actions explicit and observable

Browser or Play Store access can be re-enabled only through explicit CLI commands.  
When enabled, the browser installed is **Fennec**; OEM browsers are not restored in Phase I.

---

## Rationale

Modern smartphones combine useful capabilities with defaults that encourage distraction, frequent app churn, and broad data collection.

Clearphone starts from a few practical assumptions:

- Some smartphone functions are necessary and valuable (calls, messages, maps, camera, utilities).
- Browsers and app stores are the primary vectors for unbounded usage and impulse installs.
- Partial or cosmetic restrictions often result in confusing or brittle systems.

Rather than attempting to lock devices down completely, Clearphone removes certain defaults entirely and replaces them with a smaller, curated surface area. Where Android imposes limits, those limits are surfaced explicitly rather than worked around.

---

## Supported Devices (Phase I)

Phase I officially supports two devices:

**Samsung Galaxy S24 (One UI, stock firmware)**  
The Galaxy S24 serves as a stress test for Clearphone’s device-profile approach. Samsung’s Android distribution includes a large number of preinstalled vendor apps and system integrations. Supporting a heavily customized OEM device helps validate that the profile-based model can handle complex environments.  
The Galaxy S24 is also the lead developer’s daily driver, which enables frequent real-world testing and rapid feedback as updates are released.

**Google Pixel 8 / 8a (stock Android)**  
The Pixel 8 and 8a represent the opposite end of the spectrum: relatively clean, stock Android devices with minimal manufacturer customization. These devices serve as the long-term baseline target for Clearphone due to predictable behavior, timely updates, and broad availability.

Supporting both devices early validates Clearphone across fundamentally different Android environments.

Clearphone uses a **maintainer model** for device support. Work on additional phones can begin when contributors are willing to maintain and test profiles on real hardware.

---

## Installation (v1.0)

Phase I targets developers and early adopters.

While installation via `pip` is supported, an explicit Phase I goal is to provide **platform-specific, Python-packaged downloads** (macOS, Linux, Windows) so testers do not need to manage Python environments or install dependencies manually. Until those packages are available, installation via `pip` is the supported path.

### Requirements

- Python **3.11+**
- A supported Android device
- USB debugging enabled
- **System `adb` available** in your PATH

### Installing ADB

Phase I requires the Android Debug Bridge (`adb`) to be available on your system. Clearphone does not bundle or install ADB.

Rather than duplicating installation instructions here, follow the official Android documentation:

- Official ADB overview: https://developer.android.com/tools/adb
- Download Android SDK Platform Tools (includes `adb`): https://developer.android.com/tools/releases/platform-tools

You do not need to install Android Studio. After installation, confirm `adb` is available on your PATH:

```bash
adb version
```

### Install

```bash
pip install clearphone
```

---

## Basic Usage

Connect your phone via USB and authorize debugging.

```bash
clearphone devices
clearphone configure
```

---

## Project Landscape

Clearphone uses **two GitHub Projects** to separate planning from execution. This separation is intentional and helps keep active development focused while still making future ideas visible.

**Planning & Roadmap**  
This is a long-lived, non-executable project. It captures future ideas, architectural questions, and deferred initiatives. Items in Planning & Roadmap are exploratory and do not represent commitments or scheduled work.

**Phase Delivery Projects**  
Each development phase has a dedicated Delivery project (for example, “Phase I — Delivery”). A Delivery project contains only executable work required to complete that phase. Every issue in a Delivery project blocks phase completion. When a phase ships, its Delivery project is archived and not reused.

Work moves from Planning & Roadmap into a Phase Delivery project only when it is explicitly in scope. Items are promoted, not duplicated, and once work begins the Delivery project is the sole source of truth for that phase.

If you want to contribute code, start with the current Phase Delivery project. If you want to discuss future directions or constraints, start with Planning & Roadmap.

---

## Command-Line Reference (Phase I)

The Clearphone CLI is designed for power users and developers. Commands are explicit, observable, and reversible where Android permits.

### Global Options

These flags apply to most commands.

| Option | Description |
|------|-------------|
| `--serial <SERIAL>` | Select a specific device if multiple are connected |
| `--dry-run` | Show planned actions without making changes |
| `--json` | Emit machine-readable event output |
| `--verbose` | Increase output detail |
| `--debug` | Maximum diagnostics (implies `--verbose`) |
| `--help` | Show structured help for the current command |

### Core Commands

| Command | Purpose |
|------|---------|
| `clearphone version` | Show Clearphone version |
| `clearphone doctor` | Check environment and device connectivity |
| `clearphone devices` | List connected Android devices |

### Configuration

| Command | Purpose |
|------|---------|
| `clearphone configure` | Configure a supported device (auto-detects profile) |
| `--profile <profile>` | Explicitly select a device profile |
| `--extra <id>` | Install an optional app (repeatable) |
| `--interactive` | Prompt for optional extras during configuration |

### Profiles and Extras

| Command | Purpose |
|------|---------|
| `clearphone profiles list` | List available device profiles |
| `clearphone profiles show <profile>` | Show details of a device profile |
| `clearphone extras list` | List available optional apps (“extras”) |
| `clearphone extras show <id>` | Show details for a specific extra |

### Feature Toggles

| Command | Purpose |
|------|---------|
| `clearphone browser on` | Enable browser access (installs Fennec) |
| `clearphone browser off` | Disable browser access |
| `clearphone appstore on` | Enable the Google Play Store app (best effort) |
| `clearphone appstore off` | Disable the Play Store app |

### Maintenance and Integrity

| Command | Purpose |
|------|---------|
| `clearphone update` | Update Clearphone-managed apps |
| `clearphone audit` | Detect configuration drift |
| `clearphone state show` | Show Clearphone’s view of the device state |

---

## Usage Examples

Configure a connected device:

```bash
clearphone configure
```

Preview changes without modifying the device:

```bash
clearphone configure --dry-run
```

Configure a device and install multiple extras:

```bash
clearphone configure --extra weather --extra maps --extra signal
```

Enable and disable browser access:

```bash
clearphone browser on
clearphone browser off
```

Update all Clearphone-managed apps:

```bash
clearphone update
```

Audit the device for unexpected apps:

```bash
clearphone audit
```

---

## `--help` Behavior

The `--help` flag is intended to be a local, command-specific view of the same information presented in the command-line reference above. At every level (`clearphone --help`, `clearphone configure --help`, `clearphone browser --help`), help output should show available subcommands and options with short, factual descriptions, using the same terminology and defaults as this README.

---

## Contributing

For architectural context, development rules, and guidance for AI-assisted development, read **CLAUDE.md**. For day-to-day work, follow the current Phase Delivery project.

---

## License

Clearphone is licensed under the **GNU GPL v3 (GPL-3.0)**.

The GPL applies to the Clearphone tool itself. Apps installed by Clearphone are governed by their own licenses and are downloaded from their original sources.
