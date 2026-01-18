# Phase One Implementation Outline

> **Purpose:** Guide for implementing remaining Phase One CLI features.
> **Target:** Sonnet or developer following this outline.
> **Status:** Ready for implementation.

---

## Overview

The core infrastructure is complete. This outline covers adding CLI arguments to expose that functionality per the spec in [Issue #20](https://github.com/glw907/clearphone/issues/20).

**Files to modify:**
1. `clearphone/core/workflow.py` - Add new config options
2. `clearphone/api/controller.py` - Pass through new options
3. `clearphone/cli.py` - Add CLI arguments and global toggle commands

---

## Step 1: Update WorkflowConfig

**File:** `clearphone/core/workflow.py`

**Current:**
```python
@dataclass
class WorkflowConfig:
    profile_path: Path
    project_root: Path
    dry_run: bool = False
    non_interactive: bool = False
    download_dir: Path | None = None
```

**Change to:**
```python
@dataclass
class WorkflowConfig:
    profile_path: Path
    project_root: Path
    dry_run: bool = False
    interactive: bool = False  # RENAMED: was non_interactive (logic flipped)
    download_dir: Path | None = None
    # New options
    enable_browser: bool = False  # Install Fennec
    enable_play_store: bool = False  # Keep Play Store
    keep_vendor_camera: bool = False  # Default: replace with Fossify Camera
    install_extras: list[str] = field(default_factory=list)  # Explicit app IDs to install
```

**Update references:**
- In `_phase_camera_choice()`: Change `self.config.non_interactive` → `not self.config.interactive`
- In `_phase_extras_selection()`: Same change

---

## Step 2: Update UserChoices

**File:** `clearphone/core/workflow.py`

**Current:**
```python
@dataclass
class UserChoices:
    camera_choice: str = ""
    selected_extras_free: list[str] = field(default_factory=list)
    selected_extras_non_free: list[str] = field(default_factory=list)
```

**Add:**
```python
@dataclass
class UserChoices:
    camera_choice: str = ""
    selected_extras_free: list[str] = field(default_factory=list)
    selected_extras_non_free: list[str] = field(default_factory=list)
    # Derived from config
    browser_enabled: bool = False
    play_store_enabled: bool = False
```

---

## Step 3: Update Workflow Logic

**File:** `clearphone/core/workflow.py`

### 3a: Camera choice phase

In `_phase_camera_choice()`, respect `keep_vendor_camera`:

```python
def _phase_camera_choice(self) -> Generator[Event, None, None]:
    yield self._emit_phase(5, "Camera choice")

    if not self.profile.has_camera_choice():
        yield self._emit_phase(5, "Camera choice", started=False)
        return

    # If --keep-vendor-camera flag passed, keep stock camera
    if self.config.keep_vendor_camera:
        self.choices.camera_choice = "stock"
        yield self._emit_phase(5, "Camera choice", started=False)
        return

    # Default: use Fossify Camera (remove vendor camera)
    stock_camera = self.profile.get_stock_camera_package()
    # ... rest of existing logic, but check self.config.interactive instead of non_interactive
```

### 3b: Extras selection phase

In `_phase_extras_selection()`, use `install_extras` from config:

```python
def _phase_extras_selection(self) -> Generator[Event, None, None]:
    yield self._emit_phase(6, "Selecting extra apps")

    # If explicit extras provided via CLI flags, use those
    if self.config.install_extras:
        # Split into free and non-free based on catalog
        for app_id in self.config.install_extras:
            if app_id in self.catalog.extras_free:
                self.choices.selected_extras_free.append(app_id)
            elif app_id in self.catalog.extras_non_free:
                self.choices.selected_extras_non_free.append(app_id)
        yield self._emit_phase(6, "Selecting extra apps", started=False)
        return

    # If interactive mode, prompt
    if self.config.interactive:
        # ... existing callback logic
    else:
        # Non-interactive with no explicit extras: install nothing
        self.choices.selected_extras_free = []
        self.choices.selected_extras_non_free = []
```

### 3c: Browser handling

Add browser to install list if `enable_browser` is True. Browser app ID should be added to `apps/extras/free.toml` as "browser" (Fennec).

In `_phase_download_and_install()`:
```python
# Add browser if enabled
if self.config.enable_browser and "browser" in self.catalog.extras_free:
    apps_to_install.append(self.catalog.extras_free["browser"])
```

### 3d: Play Store handling

Play Store is handled during package removal, not installation. In `_phase_remove_packages()`:

The profile should have Play Store packages marked. If `enable_play_store` is True, filter them out of the removal list.

```python
def _phase_remove_packages(self) -> Generator[Event, None, None]:
    # ... existing code ...

    packages = self.profile.get_packages_to_remove(conditional_choices)

    # If smartphone mode, don't remove Play Store
    if self.config.enable_play_store:
        packages = [p for p in packages if not self._is_play_store_package(p.id)]

    # If browser enabled, don't remove stock browsers?
    # Actually no - we always remove stock browsers and install Fennec instead
```

---

## Step 4: Update Controller

**File:** `clearphone/api/controller.py`

Update `configure()` method signature:

```python
def configure(
    self,
    profile_path: Path,
    dry_run: bool = False,
    interactive: bool = False,  # RENAMED
    download_dir: Path | None = None,
    enable_browser: bool = False,
    enable_play_store: bool = False,
    keep_vendor_camera: bool = False,
    install_extras: list[str] | None = None,
    camera_choice_callback: CameraChoiceCallback | None = None,
    extras_choice_callback: ExtrasChoiceCallback | None = None,
) -> Generator[Event, None, WorkflowResult]:
```

Update WorkflowConfig creation:

```python
config = WorkflowConfig(
    profile_path=profile_path,
    project_root=self.project_root,
    dry_run=dry_run,
    interactive=interactive,
    download_dir=download_dir,
    enable_browser=enable_browser,
    enable_play_store=enable_play_store,
    keep_vendor_camera=keep_vendor_camera,
    install_extras=install_extras or [],
)
```

---

## Step 5: Update CLI - Configure Command

**File:** `clearphone/cli.py`

### 5a: Replace arguments

**Remove:**
```python
non_interactive: Annotated[bool, typer.Option("--non-interactive", "-y", ...)] = False,
```

**Add:**
```python
interactive: Annotated[
    bool,
    typer.Option(
        "--interactive", "-i",
        help="Guided prompts for extras selection",
    ),
] = False,
smartphone_mode: Annotated[
    bool,
    typer.Option(
        "--smartphone-mode",
        help="Enable both browser and Play Store",
    ),
] = False,
enable_browser: Annotated[
    bool,
    typer.Option(
        "--enable-browser",
        help="Install Fennec browser",
    ),
] = False,
enable_play_store: Annotated[
    bool,
    typer.Option(
        "--enable-play-store",
        help="Keep Play Store available",
    ),
] = False,
keep_vendor_camera: Annotated[
    bool,
    typer.Option(
        "--keep-vendor-camera",
        help="Keep stock camera instead of Fossify Camera",
    ),
] = False,
# Individual app install flags
install_weather: Annotated[bool, typer.Option("--install-weather")] = False,
install_music: Annotated[bool, typer.Option("--install-music")] = False,
install_calculator: Annotated[bool, typer.Option("--install-calculator")] = False,
install_clock: Annotated[bool, typer.Option("--install-clock")] = False,
install_notes: Annotated[bool, typer.Option("--install-notes")] = False,
install_calendar: Annotated[bool, typer.Option("--install-calendar")] = False,
install_flashlight: Annotated[bool, typer.Option("--install-flashlight")] = False,
install_maps: Annotated[bool, typer.Option("--install-maps")] = False,
install_whatsapp: Annotated[bool, typer.Option("--install-whatsapp")] = False,
install_signal: Annotated[bool, typer.Option("--install-signal")] = False,
install_telegram: Annotated[bool, typer.Option("--install-telegram")] = False,
install_discord: Annotated[bool, typer.Option("--install-discord")] = False,
```

### 5b: Process flags in configure()

```python
def configure(...) -> None:
    # Handle smartphone mode (sets both browser and play store)
    if smartphone_mode:
        enable_browser = True
        enable_play_store = True

    # Collect explicit install requests
    install_extras: list[str] = []
    if install_weather:
        install_extras.append("weather")
    if install_music:
        install_extras.append("music")
    # ... etc for all install flags

    # Update callback setup
    camera_callback = None if not interactive else camera_choice_prompt
    extras_callback = None if not interactive else extras_choice_prompt

    # Call controller
    gen = controller.configure(
        profile_path=profile,
        dry_run=dry_run,
        interactive=interactive,
        download_dir=download_dir,
        enable_browser=enable_browser,
        enable_play_store=enable_play_store,
        keep_vendor_camera=keep_vendor_camera,
        install_extras=install_extras,
        camera_choice_callback=camera_callback,
        extras_choice_callback=extras_callback,
    )
```

---

## Step 6: Add Global Toggle Commands

**File:** `clearphone/cli.py`

These work on already-configured phones (no profile needed).

```python
@app.command("enable-browser")
def enable_browser_cmd() -> None:
    """Install Fennec browser on a configured phone."""
    # Connect to device
    # Download Fennec from F-Droid
    # Install it
    pass

@app.command("disable-browser")
def disable_browser_cmd() -> None:
    """Remove Fennec browser from a configured phone."""
    # Connect to device
    # Uninstall Fennec package
    pass

@app.command("enable-play-store")
def enable_play_store_cmd() -> None:
    """Re-enable Play Store on a configured phone."""
    # Connect to device
    # Run: pm enable com.android.vending
    pass

@app.command("disable-play-store")
def disable_play_store_cmd() -> None:
    """Disable Play Store on a configured phone."""
    # Connect to device
    # Run: pm disable-user --user 0 com.android.vending
    pass

@app.command("clearphone-mode")
def clearphone_mode_cmd() -> None:
    """Disable both browser and Play Store."""
    disable_browser_cmd()
    disable_play_store_cmd()

@app.command("smartphone-mode")
def smartphone_mode_cmd() -> None:
    """Enable both browser and Play Store."""
    enable_browser_cmd()
    enable_play_store_cmd()
```

**Note:** These commands need their own ADB connection logic. Consider extracting a helper or lightweight workflow.

---

## Step 7: Add Fennec to Apps Catalog

**File:** `apps/extras/free.toml`

Add:
```toml
[browser]
id = "browser"
package_id = "org.mozilla.fennec_fdroid"
name = "Fennec"
description = "Privacy-focused Firefox fork from F-Droid. No telemetry."
source = "fdroid"
fdroid_package_name = "org.mozilla.fennec_fdroid"
```

---

## Step 8: Mark Play Store Packages in Profile

**File:** `device-profiles/samsung-s24.toml`

Ensure Play Store packages have a way to be identified. Options:
1. Add a `category = "play_store"` to relevant packages
2. Or just hardcode the package IDs in workflow

Relevant packages:
- `com.android.vending` (Play Store)
- `com.google.android.gms` (Play Services - probably keep this)

---

## Testing Checklist

After implementation:

```bash
# Basic configure (should install core apps only, no extras, no browser)
clearphone configure device-profiles/samsung-s24.toml --dry-run

# With extras
clearphone configure device-profiles/samsung-s24.toml --install-weather --install-whatsapp --dry-run

# Smartphone mode
clearphone configure device-profiles/samsung-s24.toml --smartphone-mode --dry-run

# Interactive mode
clearphone configure device-profiles/samsung-s24.toml --interactive --dry-run

# Global toggles (need real device)
clearphone enable-browser
clearphone disable-browser
clearphone smartphone-mode
clearphone clearphone-mode
```

---

## Implementation Order

1. **WorkflowConfig + UserChoices** - Add new fields
2. **Workflow logic** - Handle new options
3. **Controller** - Pass through options
4. **CLI configure command** - Add all flags
5. **Fennec in catalog** - Add browser app
6. **Global toggle commands** - Add standalone commands
7. **Test with --dry-run** - Verify logic
8. **Test on real device** - End-to-end validation

---

## Notes for Implementer

- The `--keep-vendor-camera` defaults to `False` (replace with Fossify Camera) - consistent with Clearphone philosophy of FOSS replacements
- In non-interactive mode with no `--install-*` flags, install **no extras** (core apps only)
- Stock browsers (Chrome, Samsung Browser) are **always** removed regardless of `--enable-browser`
- `--enable-browser` installs Fennec; it doesn't preserve stock browsers
- Play Services (`com.google.android.gms`) should probably be kept even in clearphone mode for app compatibility
