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

"""Device profile loading and validation.

Device profiles are TOML files that define:
- Device model pattern for validation
- Packages to remove
- App selections from the catalog
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import toml

from clearphone.core.apps_catalog import AppsCatalog
from clearphone.core.exceptions import (
    ProfileNotFoundError,
    ProfileParseError,
)


@dataclass
class PackageToRemove:
    """A package that should be removed from the device."""

    id: str
    name: str
    source: str
    function: str
    category: str
    action: Literal["remove", "disable"]
    conditional: str | None = None
    removal_rationale: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, str | None]) -> "PackageToRemove":
        """Create a PackageToRemove from a TOML dictionary.

        Args:
            data: Dictionary from TOML parsing

        Returns:
            PackageToRemove instance
        """
        conditional_value = data.get("conditional")
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            source=str(data.get("source", "")),
            function=str(data.get("function", "")),
            category=str(data.get("category", "")),
            action=str(data.get("action", "remove")),  # type: ignore[arg-type]
            conditional=str(conditional_value) if conditional_value is not None else None,
            removal_rationale=str(data.get("removal_rationale", "")),
        )


@dataclass
class DeviceInfo:
    """Device identification information from the profile."""

    model_pattern: str
    name: str
    android_version: str
    maintainer: str


@dataclass
class AppsConfig:
    """App selection configuration from the profile."""

    extras_free: list[str] = field(default_factory=list)
    extras_non_free: list[str] = field(default_factory=list)


@dataclass
class DeviceProfile:
    """Complete device profile parsed from TOML."""

    path: Path
    device: DeviceInfo
    apps: AppsConfig
    packages: list[PackageToRemove]

    def get_packages_to_remove(
        self, conditional_choices: dict[str, bool] | None = None
    ) -> list[PackageToRemove]:
        """Get packages to remove, filtering by conditional choices.

        Args:
            conditional_choices: Dict mapping conditional names to boolean
                indicating whether the condition is met. For example,
                {"camera": True} means the user chose to replace the stock camera.

        Returns:
            List of packages that should be removed based on choices
        """
        if conditional_choices is None:
            conditional_choices = {}

        result: list[PackageToRemove] = []
        for pkg in self.packages:
            if pkg.action != "remove":
                continue

            # Non-conditional packages are always included
            if pkg.conditional is None:
                result.append(pkg)
                continue

            # Conditional packages only included if condition is True
            if conditional_choices.get(pkg.conditional, False):
                result.append(pkg)

        return result

    def get_conditional_packages(self) -> list[PackageToRemove]:
        """Get packages that have conditional removal.

        Returns:
            List of packages with conditional field set
        """
        return [pkg for pkg in self.packages if pkg.conditional is not None]

    def has_camera_choice(self) -> bool:
        """Check if this profile has a camera choice to present.

        Returns:
            True if there's a package with conditional="camera"
        """
        return any(pkg.conditional == "camera" for pkg in self.packages)

    def get_stock_camera_package(self) -> PackageToRemove | None:
        """Get the stock camera package if it exists.

        Returns:
            The stock camera package or None
        """
        for pkg in self.packages:
            if pkg.conditional == "camera":
                return pkg
        return None


def load_profile(path: Path) -> DeviceProfile:
    """Load a device profile from a TOML file.

    Args:
        path: Path to the profile TOML file

    Returns:
        Parsed DeviceProfile

    Raises:
        ProfileNotFoundError: If file does not exist
        ProfileParseError: If TOML is invalid or missing required fields
    """
    if not path.exists():
        raise ProfileNotFoundError(str(path))

    try:
        data = toml.load(path)
    except toml.TomlDecodeError as e:
        raise ProfileParseError(str(path), str(e)) from e

    # Parse device section
    if "device" not in data:
        raise ProfileParseError(str(path), "Missing required [device] section")

    device_data = data["device"]
    required_device_fields = ["model_pattern", "name", "android_version", "maintainer"]
    for field_name in required_device_fields:
        if field_name not in device_data:
            raise ProfileParseError(str(path), f"Missing required field: device.{field_name}")

    device = DeviceInfo(
        model_pattern=device_data["model_pattern"],
        name=device_data["name"],
        android_version=device_data["android_version"],
        maintainer=device_data["maintainer"],
    )

    # Parse apps section
    apps_data = data.get("apps", {})
    apps = AppsConfig(
        extras_free=apps_data.get("extras_free", []),
        extras_non_free=apps_data.get("extras_non_free", []),
    )

    # Parse packages
    packages: list[PackageToRemove] = []
    for pkg_data in data.get("packages", []):
        if "id" not in pkg_data:
            raise ProfileParseError(str(path), "Package missing required 'id' field")
        packages.append(PackageToRemove.from_dict(pkg_data))

    return DeviceProfile(path=path, device=device, apps=apps, packages=packages)


def validate_profile_apps(profile: DeviceProfile, catalog: AppsCatalog) -> list[str]:
    """Validate that all app IDs in the profile exist in the catalog.

    Args:
        profile: The device profile to validate
        catalog: The apps catalog to check against

    Returns:
        List of error messages (empty if valid)

    Raises:
        AppNotFoundError: If any app ID is not found (optional, based on strict mode)
    """
    errors: list[str] = []

    for app_id in profile.apps.extras_free:
        if app_id not in catalog.extras_free:
            errors.append(f"App '{app_id}' not found in extras/free.toml")

    for app_id in profile.apps.extras_non_free:
        if app_id not in catalog.extras_non_free:
            errors.append(f"App '{app_id}' not found in extras/non-free.toml")

    return errors
