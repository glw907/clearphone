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

"""Tests for the apps_catalog module."""

from pathlib import Path

import pytest

from clearphone.core.apps_catalog import (
    AppDefinition,
    AppsCatalog,
    load_apps_catalog,
)
from clearphone.core.exceptions import AppNotFoundError, CatalogNotFoundError


class TestAppDefinition:
    """Tests for AppDefinition dataclass."""

    def test_create_fdroid_app(self) -> None:
        """Should create an F-Droid app definition."""
        app = AppDefinition(
            id="launcher",
            package_id="app.olauncher",
            name="Olauncher",
            source="fdroid",
            fdroid_package_name="app.olauncher",
        )
        assert app.id == "launcher"
        assert app.source == "fdroid"
        assert app.fdroid_package_name == "app.olauncher"

    def test_create_direct_app(self) -> None:
        """Should create a direct download app definition."""
        app = AppDefinition(
            id="whatsapp",
            package_id="com.whatsapp",
            name="WhatsApp",
            source="direct",
            download_url="https://whatsapp.com/android/",
        )
        assert app.source == "direct"
        assert app.download_url == "https://whatsapp.com/android/"

    def test_default_priority(self) -> None:
        """Should have default installation priority of 50."""
        app = AppDefinition(id="test", package_id="test.app", name="Test", source="fdroid")
        assert app.installation_priority == 50

    def test_from_dict(self) -> None:
        """Should create from dictionary."""
        data = {
            "package_id": "app.olauncher",
            "name": "Olauncher",
            "source": "fdroid",
            "fdroid_package_name": "app.olauncher",
            "installation_priority": 1,
        }
        app = AppDefinition.from_dict("launcher", data)
        assert app.id == "launcher"
        assert app.installation_priority == 1


class TestAppsCatalog:
    """Tests for AppsCatalog class."""

    def test_get_app_from_core(self) -> None:
        """Should find app in core apps."""
        catalog = AppsCatalog()
        catalog.core_apps["launcher"] = AppDefinition(
            id="launcher",
            package_id="app.olauncher",
            name="Olauncher",
            source="fdroid",
        )

        app = catalog.get_app("launcher")
        assert app.name == "Olauncher"

    def test_get_app_from_extras_free(self) -> None:
        """Should find app in free extras."""
        catalog = AppsCatalog()
        catalog.extras_free["camera"] = AppDefinition(
            id="camera",
            package_id="com.fossify.camera",
            name="Fossify Camera",
            source="fdroid",
        )

        app = catalog.get_app("camera")
        assert app.name == "Fossify Camera"

    def test_get_app_not_found(self) -> None:
        """Should raise AppNotFoundError for unknown app."""
        catalog = AppsCatalog()

        with pytest.raises(AppNotFoundError) as exc_info:
            catalog.get_app("nonexistent")

        assert exc_info.value.app_id == "nonexistent"

    def test_get_core_apps_sorted(self) -> None:
        """Should return core apps sorted by priority."""
        catalog = AppsCatalog()
        catalog.core_apps["keyboard"] = AppDefinition(
            id="keyboard",
            package_id="org.futo",
            name="FUTO Keyboard",
            source="fdroid",
            installation_priority=5,
        )
        catalog.core_apps["launcher"] = AppDefinition(
            id="launcher",
            package_id="app.olauncher",
            name="Olauncher",
            source="fdroid",
            installation_priority=1,
        )

        sorted_apps = catalog.get_core_apps_sorted()
        assert sorted_apps[0].id == "launcher"
        assert sorted_apps[1].id == "keyboard"

    def test_resolve_extras(self) -> None:
        """Should resolve extra app IDs to definitions."""
        catalog = AppsCatalog()
        catalog.extras_free["weather"] = AppDefinition(
            id="weather",
            package_id="org.breezyweather",
            name="Breezy Weather",
            source="fdroid",
        )
        catalog.extras_non_free["signal"] = AppDefinition(
            id="signal",
            package_id="org.thoughtcrime.securesms",
            name="Signal",
            source="direct",
        )

        apps = catalog.resolve_extras(["weather"], ["signal"])
        assert len(apps) == 2
        assert apps[0].id == "weather"
        assert apps[1].id == "signal"

    def test_resolve_extras_not_found(self) -> None:
        """Should raise AppNotFoundError for unknown extra."""
        catalog = AppsCatalog()

        with pytest.raises(AppNotFoundError):
            catalog.resolve_extras(["unknown"], [])


class TestLoadAppsCatalog:
    """Tests for load_apps_catalog function."""

    def test_load_real_catalog(self, project_root: Path) -> None:
        """Should load the real apps catalog."""
        catalog = load_apps_catalog(project_root)

        # Core apps should be loaded
        assert len(catalog.core_apps) > 0
        assert "launcher" in catalog.core_apps
        assert "keyboard" in catalog.core_apps

        # Extras should be loaded
        assert len(catalog.extras_free) > 0
        assert len(catalog.extras_non_free) > 0

    def test_load_nonexistent_path(self, tmp_path: Path) -> None:
        """Should raise CatalogNotFoundError for missing catalog."""
        with pytest.raises(CatalogNotFoundError):
            load_apps_catalog(tmp_path)
