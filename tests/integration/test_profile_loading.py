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

"""Integration tests for profile loading with real files."""

from pathlib import Path

from clearphone.core.apps_catalog import load_apps_catalog
from clearphone.core.profile import load_profile, validate_profile_apps


class TestRealProfileLoading:
    """Tests loading real profile files from the project."""

    def test_load_samsung_s24_profile(self, project_root: Path) -> None:
        """Should load the real Samsung S24 profile."""
        profile_path = project_root / "device-profiles" / "samsung-s24.toml"
        profile = load_profile(profile_path)

        # Verify device info
        assert profile.device.name == "Samsung Galaxy S24"
        assert profile.device.model_pattern == "SM-S921*"
        assert profile.device.android_version == "14"
        assert profile.device.maintainer == "glw907"

        # Verify packages
        assert len(profile.packages) > 0

        # Should have Bixby packages
        bixby_packages = [p for p in profile.packages if "bixby" in p.id.lower()]
        assert len(bixby_packages) > 0

        # Should have conditional camera package
        assert profile.has_camera_choice()
        camera_pkg = profile.get_stock_camera_package()
        assert camera_pkg is not None
        assert camera_pkg.name == "Samsung Camera"

    def test_profile_and_catalog_integration(self, project_root: Path) -> None:
        """Should validate profile apps exist in catalog."""
        profile_path = project_root / "device-profiles" / "samsung-s24.toml"
        profile = load_profile(profile_path)
        catalog = load_apps_catalog(project_root)

        errors = validate_profile_apps(profile, catalog)
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_catalog_has_all_required_apps(self, project_root: Path) -> None:
        """Should have all core apps in catalog."""
        catalog = load_apps_catalog(project_root)

        # Required core apps
        required_apps = [
            "launcher",
            "keyboard",
            "dialer",
            "messaging",
            "contacts",
            "gallery",
            "files",
        ]

        for app_id in required_apps:
            assert app_id in catalog.core_apps, f"Missing core app: {app_id}"

    def test_catalog_apps_have_required_fields(self, project_root: Path) -> None:
        """All catalog apps should have required fields."""
        catalog = load_apps_catalog(project_root)

        for app_id, app in catalog.core_apps.items():
            assert app.id, f"Core app {app_id} missing id"
            assert app.package_id, f"Core app {app_id} missing package_id"
            assert app.name, f"Core app {app_id} missing name"
            assert app.source in ("fdroid", "direct"), f"Core app {app_id} invalid source"

            if app.source == "fdroid":
                assert app.fdroid_package_name, f"F-Droid app {app_id} missing fdroid_package_name"

    def test_extras_have_descriptions(self, project_root: Path) -> None:
        """All extra apps should have descriptions."""
        catalog = load_apps_catalog(project_root)

        for app_id, app in catalog.extras_free.items():
            assert app.description, f"Free extra {app_id} missing description"

        for app_id, app in catalog.extras_non_free.items():
            assert app.description, f"Non-free extra {app_id} missing description"

    def test_conditional_filtering(self, project_root: Path) -> None:
        """Should correctly filter packages by conditional choices."""
        profile_path = project_root / "device-profiles" / "samsung-s24.toml"
        profile = load_profile(profile_path)

        # Without camera choice
        packages_no_camera = profile.get_packages_to_remove({})
        camera_in_list = any(p.id == "com.sec.android.app.camera" for p in packages_no_camera)
        assert not camera_in_list, "Camera should not be in list without choice"

        # With camera choice = True
        packages_with_camera = profile.get_packages_to_remove({"camera": True})
        camera_in_list = any(p.id == "com.sec.android.app.camera" for p in packages_with_camera)
        assert camera_in_list, "Camera should be in list with choice=True"

    def test_package_categories(self, project_root: Path) -> None:
        """Profile packages should have valid categories."""
        profile_path = project_root / "device-profiles" / "samsung-s24.toml"
        profile = load_profile(profile_path)

        valid_categories = {"bloatware", "google", "system", "carrier"}

        for pkg in profile.packages:
            assert pkg.category in valid_categories, (
                f"Package {pkg.id} has invalid category: {pkg.category}"
            )
