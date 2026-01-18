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

"""Controller API for all UIs.

Provides a thin wrapper around the workflow and core modules, managing
the ADB lifecycle and providing entry points for UIs.
"""

from collections.abc import Generator
from pathlib import Path

from clearphone.api.events import Event
from clearphone.core.apps_catalog import AppsCatalog, load_apps_catalog
from clearphone.core.profile import DeviceProfile, load_profile
from clearphone.core.workflow import (
    CameraChoiceCallback,
    ConfigurationWorkflow,
    ExtrasChoiceCallback,
    WorkflowConfig,
    WorkflowResult,
)


class ConfigurationController:
    """Entry point for all UIs to interact with Clearphone core."""

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize the controller.

        Args:
            project_root: Root directory of the Clearphone project.
                         Used to locate device-profiles/ and apps/ directories.
        """
        self.project_root = project_root or Path.cwd()

    def check_prerequisites(self) -> list[str]:
        """Check that all prerequisites are met.

        Returns:
            List of error messages (empty if all prerequisites met)
        """
        errors: list[str] = []

        apps_dir = self.project_root / "apps"
        if not apps_dir.exists():
            errors.append(f"Apps catalog not found at {apps_dir}")

        profiles_dir = self.project_root / "device-profiles"
        if not profiles_dir.exists():
            errors.append(f"Device profiles directory not found at {profiles_dir}")

        return errors

    def list_profiles(self) -> list[Path]:
        """List available device profiles.

        Returns:
            List of paths to profile TOML files
        """
        profiles_dir = self.project_root / "device-profiles"
        if not profiles_dir.exists():
            return []

        return sorted(profiles_dir.glob("*.toml"))

    def load_profile(self, profile_path: Path) -> DeviceProfile:
        """Load a device profile.

        Args:
            profile_path: Path to the profile TOML file

        Returns:
            Loaded DeviceProfile

        Raises:
            ProfileNotFoundError: If profile file not found
            ProfileParseError: If profile is invalid
        """
        # Handle relative paths
        if not profile_path.is_absolute():
            profile_path = self.project_root / profile_path

        return load_profile(profile_path)

    def load_catalog(self) -> AppsCatalog:
        """Load the apps catalog.

        Returns:
            Loaded AppsCatalog

        Raises:
            CatalogNotFoundError: If catalog not found
            CatalogParseError: If catalog is invalid
        """
        return load_apps_catalog(self.project_root)

    def get_profile_summary(self, profile_path: Path) -> dict[str, str | int | list[str]]:
        """Get a summary of a profile for display.

        Args:
            profile_path: Path to the profile

        Returns:
            Dictionary with profile summary information
        """
        profile = self.load_profile(profile_path)

        return {
            "name": profile.device.name,
            "model_pattern": profile.device.model_pattern,
            "android_version": profile.device.android_version,
            "maintainer": profile.device.maintainer,
            "package_count": len(profile.packages),
            "has_camera_choice": profile.has_camera_choice(),
            "extras_free": profile.apps.extras_free,
            "extras_non_free": profile.apps.extras_non_free,
        }

    def configure(
        self,
        profile_path: Path,
        dry_run: bool = False,
        interactive: bool = False,
        download_dir: Path | None = None,
        enable_browser: bool = False,
        enable_play_store: bool = False,
        keep_vendor_camera: bool = False,
        install_extras: list[str] | None = None,
        camera_choice_callback: CameraChoiceCallback | None = None,
        extras_choice_callback: ExtrasChoiceCallback | None = None,
    ) -> Generator[Event, None, WorkflowResult]:
        """Run the configuration workflow.

        Args:
            profile_path: Path to the device profile
            dry_run: If True, don't make actual changes
            interactive: If True, prompt for extras selection
            download_dir: Directory for downloaded APKs
            enable_browser: If True, install Fennec browser
            enable_play_store: If True, keep Play Store available
            keep_vendor_camera: If True, keep stock camera instead of Fossify
            install_extras: List of extra app IDs to install
            camera_choice_callback: Callback for camera choice
            extras_choice_callback: Callback for extras selection

        Yields:
            Events throughout the workflow

        Returns:
            WorkflowResult with summary statistics
        """
        # Handle relative paths
        if not profile_path.is_absolute():
            profile_path = self.project_root / profile_path

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

        workflow = ConfigurationWorkflow(
            config=config,
            camera_choice_callback=camera_choice_callback,
            extras_choice_callback=extras_choice_callback,
        )

        result = yield from workflow.execute()
        return result
