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

"""Apps catalog loading and resolution.

Apps are defined in a shared catalog to avoid duplication across device profiles.
The catalog consists of:
- apps/core.toml - Always installed apps
- apps/extras/free.toml - Optional open source apps
- apps/extras/non-free.toml - Optional proprietary apps
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import toml

from clearphone.core.exceptions import (
    AppNotFoundError,
    CatalogNotFoundError,
    CatalogParseError,
)


@dataclass
class AppDefinition:
    """Definition of an app from the catalog."""

    id: str
    package_id: str
    name: str
    source: Literal["fdroid", "direct"]
    fdroid_package_name: str | None = None
    download_url: str | None = None
    description: str | None = None
    installation_priority: int = 50
    notes: str | None = None

    @classmethod
    def from_dict(cls, app_id: str, data: dict[str, str | int | None]) -> "AppDefinition":
        """Create an AppDefinition from a TOML dictionary.

        Args:
            app_id: The app identifier
            data: Dictionary from TOML parsing

        Returns:
            AppDefinition instance
        """
        priority_value = data.get("installation_priority", 50)
        return cls(
            id=app_id,
            package_id=str(data.get("package_id", "")),
            name=str(data.get("name", "")),
            source=str(data.get("source", "fdroid")),  # type: ignore[arg-type]
            fdroid_package_name=str(data["fdroid_package_name"])
            if "fdroid_package_name" in data
            else None,
            download_url=str(data["download_url"]) if "download_url" in data else None,
            description=str(data["description"]) if "description" in data else None,
            installation_priority=int(priority_value) if priority_value is not None else 50,
            notes=str(data["notes"]) if "notes" in data else None,
        )


@dataclass
class AppsCatalog:
    """Container for all apps in the catalog."""

    core_apps: dict[str, AppDefinition] = field(default_factory=dict)
    extras_free: dict[str, AppDefinition] = field(default_factory=dict)
    extras_non_free: dict[str, AppDefinition] = field(default_factory=dict)

    def get_app(self, app_id: str) -> AppDefinition:
        """Get an app by ID from any catalog section.

        Args:
            app_id: The app identifier

        Returns:
            The AppDefinition

        Raises:
            AppNotFoundError: If app not found in any catalog section
        """
        if app_id in self.core_apps:
            return self.core_apps[app_id]
        if app_id in self.extras_free:
            return self.extras_free[app_id]
        if app_id in self.extras_non_free:
            return self.extras_non_free[app_id]
        raise AppNotFoundError(app_id)

    def get_core_apps_sorted(self) -> list[AppDefinition]:
        """Get core apps sorted by installation priority.

        Returns:
            List of core apps sorted by priority (lowest first)
        """
        return sorted(self.core_apps.values(), key=lambda a: a.installation_priority)

    def resolve_extras(self, free_ids: list[str], non_free_ids: list[str]) -> list[AppDefinition]:
        """Resolve extra app IDs to AppDefinitions.

        Args:
            free_ids: List of free extra app IDs
            non_free_ids: List of non-free extra app IDs

        Returns:
            List of resolved AppDefinitions

        Raises:
            AppNotFoundError: If any app ID not found in extras
        """
        apps: list[AppDefinition] = []

        for app_id in free_ids:
            if app_id not in self.extras_free:
                raise AppNotFoundError(app_id, "extras_free")
            apps.append(self.extras_free[app_id])

        for app_id in non_free_ids:
            if app_id not in self.extras_non_free:
                raise AppNotFoundError(app_id, "extras_non_free")
            apps.append(self.extras_non_free[app_id])

        return apps

    def get_all_extras_free(self) -> list[AppDefinition]:
        """Get all free extra apps.

        Returns:
            List of all free extra apps
        """
        return list(self.extras_free.values())

    def get_all_extras_non_free(self) -> list[AppDefinition]:
        """Get all non-free extra apps.

        Returns:
            List of all non-free extra apps
        """
        return list(self.extras_non_free.values())


def _parse_catalog_file(path: Path) -> dict[str, AppDefinition]:
    """Parse a single catalog TOML file.

    Args:
        path: Path to the TOML file

    Returns:
        Dictionary mapping app IDs to AppDefinitions

    Raises:
        CatalogParseError: If TOML parsing fails
    """
    try:
        data = toml.load(path)
    except toml.TomlDecodeError as e:
        raise CatalogParseError(str(path), str(e)) from e

    apps: dict[str, AppDefinition] = {}
    for app_id, app_data in data.items():
        if isinstance(app_data, dict):
            apps[app_id] = AppDefinition.from_dict(app_id, app_data)

    return apps


def load_apps_catalog(base_path: Path) -> AppsCatalog:
    """Load the complete apps catalog from the apps directory.

    Args:
        base_path: Path to the apps/ directory

    Returns:
        Populated AppsCatalog

    Raises:
        CatalogNotFoundError: If apps directory or required files not found
        CatalogParseError: If TOML parsing fails
    """
    apps_dir = base_path / "apps"
    if not apps_dir.exists():
        raise CatalogNotFoundError(str(apps_dir))

    core_path = apps_dir / "core.toml"
    if not core_path.exists():
        raise CatalogNotFoundError(str(core_path))

    free_path = apps_dir / "extras" / "free.toml"
    non_free_path = apps_dir / "extras" / "non-free.toml"

    catalog = AppsCatalog()
    catalog.core_apps = _parse_catalog_file(core_path)

    if free_path.exists():
        catalog.extras_free = _parse_catalog_file(free_path)

    if non_free_path.exists():
        catalog.extras_non_free = _parse_catalog_file(non_free_path)

    return catalog
