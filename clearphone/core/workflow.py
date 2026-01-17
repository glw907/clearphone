# Clearphone - Configure Android phones for minimal distraction
# Copyright (C) 2026 glw907
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

"""Workflow orchestration for the configuration process.

Coordinates the full configuration flow:
1. Validate profile and catalog
2. Connect device and validate model
3. Camera choice (if applicable)
4. Extras selection
5. Remove packages
6. Download APKs
7. Install apps
8. Set defaults
"""

from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from pathlib import Path

from clearphone.api.events import (
    CameraChoiceEvent,
    DeviceEvent,
    Event,
    EventType,
    ExtrasSelectionEvent,
    PhaseEvent,
    WorkflowEvent,
)
from clearphone.core.adb import ADBDevice
from clearphone.core.apps_catalog import AppDefinition, AppsCatalog, load_apps_catalog
from clearphone.core.downloader import APKDownloader
from clearphone.core.exceptions import (
    CriticalConfigurationError,
    DeviceMismatchError,
)
from clearphone.core.installer import AppInstaller
from clearphone.core.profile import DeviceProfile, load_profile, validate_profile_apps
from clearphone.core.remover import PackageRemover


@dataclass
class WorkflowConfig:
    """Configuration for the workflow execution."""

    profile_path: Path
    project_root: Path
    dry_run: bool = False
    non_interactive: bool = False
    download_dir: Path | None = None


@dataclass
class UserChoices:
    """User choices collected during the workflow."""

    camera_choice: str = ""  # "stock" or "fossify"
    selected_extras_free: list[str] = field(default_factory=list)
    selected_extras_non_free: list[str] = field(default_factory=list)


# Type for callback functions
CameraChoiceCallback = Callable[[str, str], str]  # (stock_name, stock_package) -> choice
ExtrasChoiceCallback = Callable[
    [list[AppDefinition], list[AppDefinition]], tuple[list[str], list[str]]
]  # (free_apps, non_free_apps) -> (selected_free, selected_non_free)


@dataclass
class WorkflowResult:
    """Result summary from workflow execution."""

    packages_removed: int = 0
    packages_skipped: int = 0
    packages_failed: int = 0
    apps_installed: int = 0
    apps_failed: int = 0
    success: bool = True
    error_message: str = ""


class ConfigurationWorkflow:
    """Orchestrates the complete phone configuration workflow."""

    TOTAL_PHASES = 8

    def __init__(
        self,
        config: WorkflowConfig,
        camera_choice_callback: CameraChoiceCallback | None = None,
        extras_choice_callback: ExtrasChoiceCallback | None = None,
    ) -> None:
        """Initialize the workflow.

        Args:
            config: Workflow configuration
            camera_choice_callback: Callback for camera choice (interactive mode)
            extras_choice_callback: Callback for extras selection (interactive mode)
        """
        self.config = config
        self.camera_choice_callback = camera_choice_callback
        self.extras_choice_callback = extras_choice_callback
        self.choices = UserChoices()
        self.result = WorkflowResult()

        # Components initialized during execution
        self._profile: DeviceProfile | None = None
        self._catalog: AppsCatalog | None = None
        self._adb: ADBDevice | None = None

    @property
    def profile(self) -> DeviceProfile:
        """Get the loaded profile."""
        if self._profile is None:
            raise CriticalConfigurationError("Profile not loaded")
        return self._profile

    @property
    def catalog(self) -> AppsCatalog:
        """Get the loaded catalog."""
        if self._catalog is None:
            raise CriticalConfigurationError("Catalog not loaded")
        return self._catalog

    @property
    def adb(self) -> ADBDevice:
        """Get the ADB connection."""
        if self._adb is None:
            raise CriticalConfigurationError("ADB not connected")
        return self._adb

    def execute(self) -> Generator[Event, None, WorkflowResult]:
        """Execute the full configuration workflow.

        Yields:
            Events throughout the workflow

        Returns:
            WorkflowResult with summary statistics
        """
        yield WorkflowEvent(
            type=EventType.WORKFLOW_STARTED,
            message="Starting configuration workflow",
            profile_name=str(self.config.profile_path),
        )

        try:
            # Phase 1: Load and validate profile
            yield from self._phase_load_profile()

            # Phase 2: Load apps catalog
            yield from self._phase_load_catalog()

            # Phase 3: Connect to device
            yield from self._phase_connect_device()

            # Phase 4: Validate device model
            yield from self._phase_validate_device()

            # Phase 5: Camera choice
            yield from self._phase_camera_choice()

            # Phase 6: Extras selection
            yield from self._phase_extras_selection()

            # Phase 7: Remove packages
            yield from self._phase_remove_packages()

            # Phase 8: Download and install apps
            yield from self._phase_download_and_install()

            self.result.success = True
            yield WorkflowEvent(
                type=EventType.WORKFLOW_COMPLETED,
                message="Configuration completed successfully",
                profile_name=str(self.config.profile_path),
                device_name=self.adb.device_info.model if self._adb else "",
            )

        except CriticalConfigurationError as e:
            self.result.success = False
            self.result.error_message = str(e)
            yield WorkflowEvent(
                type=EventType.WORKFLOW_FAILED,
                message=str(e),
                profile_name=str(self.config.profile_path),
            )

        except Exception as e:
            self.result.success = False
            self.result.error_message = str(e)
            yield WorkflowEvent(
                type=EventType.WORKFLOW_FAILED,
                message=f"Unexpected error: {e}",
                profile_name=str(self.config.profile_path),
            )

        return self.result

    def _emit_phase(self, phase_num: int, name: str, started: bool = True) -> PhaseEvent:
        """Create a phase event."""
        return PhaseEvent(
            type=EventType.PHASE_STARTED if started else EventType.PHASE_COMPLETED,
            message=f"{'Starting' if started else 'Completed'}: {name}",
            phase_name=name,
            phase_number=phase_num,
            total_phases=self.TOTAL_PHASES,
        )

    def _phase_load_profile(self) -> Generator[Event, None, None]:
        """Phase 1: Load and validate the device profile."""
        yield self._emit_phase(1, "Loading profile")

        self._profile = load_profile(self.config.profile_path)

        yield self._emit_phase(1, "Loading profile", started=False)

    def _phase_load_catalog(self) -> Generator[Event, None, None]:
        """Phase 2: Load the apps catalog."""
        yield self._emit_phase(2, "Loading apps catalog")

        self._catalog = load_apps_catalog(self.config.project_root)

        # Validate profile apps exist in catalog
        errors = validate_profile_apps(self.profile, self.catalog)
        if errors:
            raise CriticalConfigurationError(
                "Profile validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        yield self._emit_phase(2, "Loading apps catalog", started=False)

    def _phase_connect_device(self) -> Generator[Event, None, None]:
        """Phase 3: Connect to the Android device."""
        yield self._emit_phase(3, "Connecting to device")

        self._adb = ADBDevice()
        device_info = self._adb.connect()

        yield DeviceEvent(
            type=EventType.DEVICE_CONNECTED,
            message=f"Connected to {device_info.manufacturer} {device_info.model}",
            serial=device_info.serial,
            model=device_info.model,
            android_version=device_info.android_version,
            manufacturer=device_info.manufacturer,
        )

        yield self._emit_phase(3, "Connecting to device", started=False)

    def _phase_validate_device(self) -> Generator[Event, None, None]:
        """Phase 4: Validate the device matches the profile."""
        yield self._emit_phase(4, "Validating device")

        if not self.adb.validate_device_model(self.profile.device.model_pattern):
            raise DeviceMismatchError(
                expected_pattern=self.profile.device.model_pattern,
                expected_name=self.profile.device.name,
                actual_model=self.adb.device_info.model,
            )

        yield DeviceEvent(
            type=EventType.DEVICE_VALIDATED,
            message=f"Device validated: {self.profile.device.name}",
            serial=self.adb.device_info.serial,
            model=self.adb.device_info.model,
            android_version=self.adb.device_info.android_version,
            manufacturer=self.adb.device_info.manufacturer,
        )

        yield self._emit_phase(4, "Validating device", started=False)

    def _phase_camera_choice(self) -> Generator[Event, None, None]:
        """Phase 5: Handle camera choice if applicable."""
        yield self._emit_phase(5, "Camera choice")

        if not self.profile.has_camera_choice():
            yield self._emit_phase(5, "Camera choice", started=False)
            return

        stock_camera = self.profile.get_stock_camera_package()
        if stock_camera is None:
            yield self._emit_phase(5, "Camera choice", started=False)
            return

        yield CameraChoiceEvent(
            type=EventType.CAMERA_CHOICE_REQUIRED,
            message="Camera choice required",
            stock_camera_name=stock_camera.name,
            stock_camera_package=stock_camera.id,
        )

        if self.config.non_interactive:
            # In non-interactive mode, default to keeping stock camera
            self.choices.camera_choice = "stock"
        elif self.camera_choice_callback:
            self.choices.camera_choice = self.camera_choice_callback(
                stock_camera.name, stock_camera.id
            )
        else:
            self.choices.camera_choice = "stock"

        yield CameraChoiceEvent(
            type=EventType.CAMERA_CHOICE_MADE,
            message=f"Camera choice: {self.choices.camera_choice}",
            stock_camera_name=stock_camera.name,
            stock_camera_package=stock_camera.id,
            user_choice=self.choices.camera_choice,
        )

        yield self._emit_phase(5, "Camera choice", started=False)

    def _phase_extras_selection(self) -> Generator[Event, None, None]:
        """Phase 6: Handle extras app selection."""
        yield self._emit_phase(6, "Selecting extra apps")

        free_apps = self.catalog.get_all_extras_free()
        non_free_apps = self.catalog.get_all_extras_non_free()

        yield ExtrasSelectionEvent(
            type=EventType.EXTRAS_SELECTION_REQUIRED,
            message="Extra apps selection required",
            available_free=[a.id for a in free_apps],
            available_non_free=[a.id for a in non_free_apps],
        )

        if self.config.non_interactive:
            # In non-interactive mode, use profile defaults
            self.choices.selected_extras_free = self.profile.apps.extras_free
            self.choices.selected_extras_non_free = self.profile.apps.extras_non_free
        elif self.extras_choice_callback:
            (
                self.choices.selected_extras_free,
                self.choices.selected_extras_non_free,
            ) = self.extras_choice_callback(free_apps, non_free_apps)
        else:
            # Default to profile settings
            self.choices.selected_extras_free = self.profile.apps.extras_free
            self.choices.selected_extras_non_free = self.profile.apps.extras_non_free

        yield ExtrasSelectionEvent(
            type=EventType.EXTRAS_SELECTION_MADE,
            message="Extra apps selected",
            available_free=[a.id for a in free_apps],
            available_non_free=[a.id for a in non_free_apps],
            selected_free=self.choices.selected_extras_free,
            selected_non_free=self.choices.selected_extras_non_free,
        )

        yield self._emit_phase(6, "Selecting extra apps", started=False)

    def _phase_remove_packages(self) -> Generator[Event, None, None]:
        """Phase 7: Remove packages from the device."""
        yield self._emit_phase(7, "Removing packages")

        # Determine conditional choices
        conditional_choices = {}
        if self.choices.camera_choice == "fossify":
            conditional_choices["camera"] = True

        packages = self.profile.get_packages_to_remove(conditional_choices)
        remover = PackageRemover(self.adb, dry_run=self.config.dry_run)

        gen = remover.remove_packages(packages)
        try:
            while True:
                event = next(gen)
                yield event
        except StopIteration as e:
            removed, skipped, failed = e.value
            self.result.packages_removed = removed
            self.result.packages_skipped = skipped
            self.result.packages_failed = failed

        yield self._emit_phase(7, "Removing packages", started=False)

    def _phase_download_and_install(self) -> Generator[Event, None, None]:
        """Phase 8: Download and install apps."""
        yield self._emit_phase(8, "Installing apps")

        # Build list of apps to install
        apps_to_install: list[AppDefinition] = []

        # Core apps always installed
        apps_to_install.extend(self.catalog.get_core_apps_sorted())

        # Add camera if user chose fossify
        if self.choices.camera_choice == "fossify" and "camera" in self.catalog.extras_free:
            apps_to_install.append(self.catalog.extras_free["camera"])

        # Add selected extras
        apps_to_install.extend(
            self.catalog.resolve_extras(
                self.choices.selected_extras_free,
                self.choices.selected_extras_non_free,
            )
        )

        # Download APKs
        download_dir = self.config.download_dir or (self.config.project_root / "downloads")
        downloaded: list[tuple[AppDefinition, Path]] = []

        with APKDownloader(download_dir) as downloader:
            for app in apps_to_install:
                gen = downloader.download_app(app)
                result: Path | None = None
                try:
                    while True:
                        event = next(gen)
                        yield event
                except StopIteration as e:
                    result = e.value

                if result:
                    downloaded.append((app, result))

        # Install apps
        installer = AppInstaller(self.adb, dry_run=self.config.dry_run)
        install_gen = installer.install_apps(downloaded)
        try:
            while True:
                event = next(install_gen)
                yield event
        except StopIteration as e:
            installed, failed = e.value
            self.result.apps_installed = installed
            self.result.apps_failed = failed

        # Set default apps
        default_apps: dict[str, AppDefinition] = {}
        for app in apps_to_install:
            if app.id in ("launcher", "dialer", "messaging", "keyboard", "gallery"):
                default_apps[app.id] = app

        for event in installer.set_default_apps(default_apps):
            yield event

        yield self._emit_phase(8, "Installing apps", started=False)
