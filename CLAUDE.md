# CLAUDE.md — Clearphone Development Guide (Canonical)

> This file is the **core development document** for Clearphone.
>
> It is optimized for **coding assistants first** (Claude Code, etc.), and secondarily for human contributors.
> When making significant architecture or design changes, update both **CLAUDE.md** and **README.md** to keep them aligned.
>
> **Authority model**
> - CLAUDE.md is authoritative for **architecture, behavior, and implementation rules**.
> - GitHub Projects are authoritative for **timing and scope (current phase vs future)**.

---

## Session Startup Protocol (for coding assistants)

At the start of a development session, review this document and then review the **current Phase Delivery project** at a high level. Read only item titles and statuses, not full issue bodies. Summarize the current state of the phase briefly and ask the user what they would like to work on next.

Do not scan closed issues or the Planning & Roadmap project unless explicitly asked. If deeper context is required for a specific task, request it before proceeding.

The Phase Delivery project is authoritative for current work; do not infer scope or priorities from Planning & Roadmap items.

---

## 0. Project Overview

Clearphone configures Android phones into low-distraction, privacy-respecting devices by removing or disabling selected vendor and system apps and installing a curated replacement app set. It avoids root access, custom ROMs, and Device Owner / MDM privileges.

Clearphone is **not** a device management or surveillance system.

**Current phase:** Phase I — working CLI prototype  
**Target devices (Phase I):** Samsung Galaxy S24; Google Pixel 8 / 8a  
**Primary interface:** Command-line interface (CLI)

---

## 1. Phase I Charter — Working CLI Prototype

Phase I exists to produce a **working, opinionated CLI prototype** that validates the Clearphone model in practice. Its purpose is not polish or enforcement, but validation: proving that the device-profile approach, app catalog, and configuration workflow are coherent, maintainable, and honest about their limits.

In Phase I, Clearphone is a **developer-facing tool**. The CLI is intentionally treated as a reference client for the event-driven core. It is expected to be explicit and sometimes verbose. This is intentional and acceptable. The CLI’s role is to exercise the core system, surface edge cases, and make architectural tradeoffs visible before committing to additional interfaces.

By default, Phase I configures supported devices into a strict “clearphone” state. Stock OEM browsers and the Google Play Store app are removed or disabled. Re-enabling browser or Play Store access requires explicit CLI commands. Enabling a browser installs **only Fennec**; OEM browsers are never restored in Phase I.

Phase I avoids root, custom ROMs, Device Owner privileges, kiosk modes, install sessions, launcher forks, and enforcement guarantees. Computer-based setup and external tooling (including system `adb`) are acceptable. Where Android imposes limits, Phase I surfaces them clearly rather than attempting to bypass them.

Phase I is complete when the CLI prototype is stable enough that another developer could reasonably add support for a new device profile or build an alternative front-end on top of the same core.

---

## 2. Project Planning & Roadmap Charter

Clearphone uses GitHub Projects to separate **intent from execution**. This separation keeps active work focused, prevents scope creep, and makes future ideas visible without prematurely committing to them.

Clearphone always has two kinds of projects.

The **Planning & Roadmap** project is long-lived and intentionally non-executable. It captures future directions, architectural questions, and possible initiatives without turning them into active work. Items there answer “Should we ever do this?” or “What would it take?” They are not commitments or deliverables.

Each development phase has a **Delivery project** dedicated to that phase. A Delivery project contains only executable work required to complete the phase’s stated goal. Every issue in a Delivery project must block phase completion. Delivery projects are created when a phase begins and archived when the phase ends.

Work moves from Planning into a Delivery project only when it is explicitly in scope. Planning items are promoted, not duplicated, and are not kept in sync with Delivery work. Once execution begins, the Delivery project is the sole source of truth for that phase.

---

## 3. Phase I Deliverable Summary

Phase I delivers a working CLI that can detect a supported device, apply the correct device profile, remove or disable selected system and vendor packages, and install curated applications from approved sources.

The default configured state removes the OEM browser and the Google Play Store app. Browser access can be enabled only by installing Fennec via the CLI. The Play Store can be enabled or disabled via the CLI on a best-effort basis.

Phase I also supports updating Clearphone-managed apps and auditing devices for configuration drift, such as unexpected packages appearing due to OEM updates.

Removing the Play Store introduces real usability and security tradeoffs, including loss of automatic updates and increased reliance on APK sourcing. These tradeoffs are accepted in Phase I to create the clearest possible Clearphone experience for testing and to avoid fragile half-measures. Future phases may explore Play Store mediation rather than removal.

---

## 4. Phase I CLI — Definitive Target

**CLI help alignment**

The `--help` output is a first-class interface. Help text should remain aligned with the README command-line reference in structure, terminology, and defaults. When CLI behavior changes in a way visible to users, update both the help text and the README together.


### Global flags
- `--serial <SERIAL>`
- `--dry-run`
- `--json`
- `--verbose`
- `--debug`

### Commands

Diagnostics and discovery:
- `clearphone version`
- `clearphone doctor`
- `clearphone devices`

Configuration:
- `clearphone configure`
- `clearphone configure --profile <profile>`
- `--extra <id>` (repeatable)
- `--interactive`

Profiles and catalog:
- `clearphone profiles list`
- `clearphone profiles show <profile>`
- `clearphone extras list`
- `clearphone extras show <id>`

Toggles:
- `clearphone browser on`
- `clearphone browser off`
- `clearphone appstore on`
- `clearphone appstore off`

Maintenance and integrity:
- `clearphone update`
- `clearphone audit`

State:
- `clearphone state show`

Explicitly excluded in Phase I:
- Modes
- OEM browser restoration
- Install sessions, kiosk modes, approvals
- Reactive uninstall
- GUI, TUI, or web interfaces
- Device Owner or MDM behavior

---

## 5. Architecture (Preserve)

Clearphone uses an event-driven core. Core logic emits structured events; interfaces render them. Core code must never print directly.

Example:

```python
for event in workflow.execute(profile, adb, dry_run=False):
    ui.handle(event)
```

This design enables deterministic testing, multiple front-ends, and clear separation of concerns.

Expected module layout:

```
clearphone/
├── clearphone/
│   ├── core/
│   │   ├── profile.py
│   │   ├── apps_catalog.py
│   │   ├── adb.py
│   │   ├── downloader.py
│   │   ├── installer.py
│   │   ├── remover.py
│   │   ├── workflow.py
│   │   └── exceptions.py
│   ├── api/
│   │   ├── events.py
│   │   └── controller.py
│   └── cli.py
├── device-profiles/
├── apps/
└── tests/
```

Key classes:
- `DeviceProfile`
- `AppsCatalog`
- `ADBDevice`
- `ConfigurationWorkflow`
- `ConfigurationController`

---

## 6. Device Profiles and Apps Catalog

Apps are defined once in a shared catalog and referenced by ID in device profiles. Core apps are always installed. Extras are opt-in only via CLI.

Device profiles encode supported device matching, package removal or disable actions with rationale, conditional removals, and known limits. Supported devices require maintainers who validate profiles against stock firmware over time.

---

## 7. Browser and Play Store Semantics

Phase I always removes or disables OEM browsers defined by the profile. Phase I does not claim to eliminate all web access vectors; it claims that no user-facing browser exists unless explicitly enabled.

Enabling a browser installs **Fennec** only. There is no stock-browser restore path in Phase I.

The Google Play Store app is removed or disabled by default. Play Services may remain installed. Play Store enablement is best-effort and CLI-mediated.

---

## 8. Error Handling

Errors fall into three categories:
1. Validation errors (fail fast before changes)
2. Recoverable errors (warn and continue)
3. Critical errors (abort immediately)

All errors must explain what happened and what the user can do next.

---

## 9. Testing Strategy

Unit tests should mock transport and network dependencies and validate emitted event sequences. Integration-style tests should exercise the workflow with realistic mocked responses.

Edge cases to test include invalid profiles, unknown app IDs, protected packages, network failures, and device disconnection mid-run.

---

## 10. Code and Writing Standards

Python ≥ 3.11. Type hints required. Google-style docstrings. No bare `except`. Absolute imports only. Use `ruff` for formatting and linting.

Terminology rules:
- Use “configured phone” or “configured state”
- Use “remove” or “disable,” not “block”
- Avoid adversarial language
- Error messages must be actionable

---

## 11. License

Clearphone is licensed under GPLv3. Include the standard license header in all new Python files.
