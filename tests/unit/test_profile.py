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

"""Tests for the profile module."""

from pathlib import Path

import pytest

from clearphone.core.apps_catalog import AppsCatalog
from clearphone.core.exceptions import ProfileNotFoundError, ProfileParseError
from clearphone.core.profile import (
    DeviceProfile,
    PackageToRemove,
    load_profile,
    validate_profile_apps,
)


class TestPackageToRemove:
    """Tests for PackageToRemove dataclass."""

    def test_create_package(self) -> None:
        """Should create a package to remove."""
        pkg = PackageToRemove(
            id="com.samsung.bixby",
            name="Bixby",
            source="Samsung",
            function="Voice assistant",
            category="bloatware",
            action="remove",
        )
        assert pkg.id == "com.samsung.bixby"
        assert pkg.conditional is None

    def test_create_conditional_package(self) -> None:
        """Should create a conditional package."""
        pkg = PackageToRemove(
            id="com.sec.android.app.camera",
            name="Samsung Camera",
            source="Samsung",
            function="Camera",
            category="system",
            action="remove",
            conditional="camera",
        )
        assert pkg.conditional == "camera"

    def test_from_dict(self) -> None:
        """Should create from dictionary."""
        data = {
            "id": "com.samsung.bixby",
            "name": "Bixby",
            "source": "Samsung",
            "function": "Voice assistant",
            "category": "bloatware",
            "action": "remove",
        }
        pkg = PackageToRemove.from_dict(data)
        assert pkg.id == "com.samsung.bixby"


class TestDeviceProfile:
    """Tests for DeviceProfile class."""

    def test_get_packages_to_remove_unconditional(self, sample_profile_path: Path) -> None:
        """Should return all unconditional packages."""
        profile = load_profile(sample_profile_path)
        packages = profile.get_packages_to_remove()

        # Should include unconditional packages
        package_ids = [p.id for p in packages]
        assert "com.samsung.android.bixby.agent" in package_ids

        # Should NOT include conditional packages
        assert "com.sec.android.app.camera" not in package_ids

    def test_get_packages_to_remove_with_condition(self, sample_profile_path: Path) -> None:
        """Should include conditional packages when condition is True."""
        profile = load_profile(sample_profile_path)
        packages = profile.get_packages_to_remove({"camera": True})

        # Should now include camera
        package_ids = [p.id for p in packages]
        assert "com.sec.android.app.camera" in package_ids

    def test_has_camera_choice(self, sample_profile_path: Path) -> None:
        """Should detect camera choice in profile."""
        profile = load_profile(sample_profile_path)
        assert profile.has_camera_choice() is True

    def test_get_stock_camera_package(self, sample_profile_path: Path) -> None:
        """Should return the stock camera package."""
        profile = load_profile(sample_profile_path)
        camera_pkg = profile.get_stock_camera_package()

        assert camera_pkg is not None
        assert camera_pkg.id == "com.sec.android.app.camera"

    def test_get_conditional_packages(self, sample_profile_path: Path) -> None:
        """Should return packages with conditional field."""
        profile = load_profile(sample_profile_path)
        conditional = profile.get_conditional_packages()

        assert len(conditional) >= 1
        assert all(p.conditional is not None for p in conditional)


class TestLoadProfile:
    """Tests for load_profile function."""

    def test_load_real_profile(self, sample_profile_path: Path) -> None:
        """Should load the real Samsung S24 profile."""
        profile = load_profile(sample_profile_path)

        assert profile.device.name == "Samsung Galaxy S24"
        assert profile.device.model_pattern == "SM-S921*"
        assert len(profile.packages) > 0

    def test_load_nonexistent_profile(self, tmp_path: Path) -> None:
        """Should raise ProfileNotFoundError for missing file."""
        with pytest.raises(ProfileNotFoundError):
            load_profile(tmp_path / "nonexistent.toml")

    def test_load_invalid_toml(self, tmp_path: Path) -> None:
        """Should raise ProfileParseError for invalid TOML."""
        invalid_file = tmp_path / "invalid.toml"
        invalid_file.write_text("this is [[[not valid toml")

        with pytest.raises(ProfileParseError):
            load_profile(invalid_file)

    def test_load_missing_device_section(self, tmp_path: Path) -> None:
        """Should raise ProfileParseError for missing device section."""
        incomplete = tmp_path / "incomplete.toml"
        incomplete.write_text("[apps]\nextras_free = []")

        with pytest.raises(ProfileParseError) as exc_info:
            load_profile(incomplete)

        assert "device" in str(exc_info.value).lower()


class TestValidateProfileApps:
    """Tests for validate_profile_apps function."""

    def test_valid_profile(self, sample_profile_path: Path, project_root: Path) -> None:
        """Should return no errors for valid profile."""
        from clearphone.core.apps_catalog import load_apps_catalog

        profile = load_profile(sample_profile_path)
        catalog = load_apps_catalog(project_root)

        errors = validate_profile_apps(profile, catalog)
        assert len(errors) == 0

    def test_invalid_app_id(self) -> None:
        """Should return error for unknown app ID."""
        from clearphone.core.profile import AppsConfig, DeviceInfo

        profile = DeviceProfile(
            path=Path("test.toml"),
            device=DeviceInfo(
                model_pattern="SM-*",
                name="Test",
                android_version="14",
                maintainer="test",
            ),
            apps=AppsConfig(extras_free=["nonexistent_app"], extras_non_free=[]),
            packages=[],
        )

        catalog = AppsCatalog()

        errors = validate_profile_apps(profile, catalog)
        assert len(errors) == 1
        assert "nonexistent_app" in errors[0]
