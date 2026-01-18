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

"""Tests for the exceptions module."""

from clearphone.core.exceptions import (
    ADBCommandError,
    AppNotFoundError,
    ClearphoneError,
    CriticalConfigurationError,
    DeviceAuthenticationError,
    DeviceMismatchError,
    DownloadError,
    KnoxProtectedError,
    NoDeviceConnectedError,
    ProfileNotFoundError,
    ProfileParseError,
    RemovalError,
    USBError,
)


class TestClearphoneError:
    """Tests for the base ClearphoneError."""

    def test_message_only(self) -> None:
        """Should format message without suggestion."""
        error = ClearphoneError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.suggestion == ""

    def test_message_and_suggestion(self) -> None:
        """Should format message with suggestion."""
        error = ClearphoneError("Error occurred", "Try this fix")
        assert "Error occurred" in str(error)
        assert "Try this fix" in str(error)


class TestProfileNotFoundError:
    """Tests for ProfileNotFoundError."""

    def test_includes_path(self) -> None:
        """Should include the missing path."""
        error = ProfileNotFoundError("/path/to/profile.toml")
        assert "/path/to/profile.toml" in str(error)
        assert error.path == "/path/to/profile.toml"


class TestProfileParseError:
    """Tests for ProfileParseError."""

    def test_includes_details(self) -> None:
        """Should include parse error details."""
        error = ProfileParseError("/path/to/profile.toml", "Invalid TOML syntax")
        assert "Invalid TOML syntax" in str(error)
        assert error.path == "/path/to/profile.toml"
        assert error.details == "Invalid TOML syntax"


class TestAppNotFoundError:
    """Tests for AppNotFoundError."""

    def test_includes_app_id(self) -> None:
        """Should include the missing app ID."""
        error = AppNotFoundError("unknown_app")
        assert "unknown_app" in str(error)
        assert error.app_id == "unknown_app"

    def test_includes_catalog_type(self) -> None:
        """Should include the catalog type."""
        error = AppNotFoundError("camera", "extras_free")
        assert "extras_free" in str(error)
        assert error.catalog_type == "extras_free"


class TestDeviceMismatchError:
    """Tests for DeviceMismatchError."""

    def test_includes_device_info(self) -> None:
        """Should include expected and actual device info."""
        error = DeviceMismatchError(
            expected_pattern="SM-S921*",
            expected_name="Samsung Galaxy S24",
            actual_model="SM-S911U",
        )
        assert "SM-S921*" in str(error)
        assert "Samsung Galaxy S24" in str(error)
        assert "SM-S911U" in str(error)


class TestADBErrors:
    """Tests for ADB-related errors."""

    def test_usb_error(self) -> None:
        """USBError should have troubleshooting suggestions."""
        error = USBError("Connection refused")
        assert "USB communication error" in str(error)
        assert "Connection refused" in str(error)
        assert error.details == "Connection refused"

    def test_device_authentication_error(self) -> None:
        """DeviceAuthenticationError should have authorization steps."""
        error = DeviceAuthenticationError()
        assert "authentication failed" in str(error)
        assert "Allow USB debugging" in str(error)

    def test_no_device_connected(self) -> None:
        """NoDeviceConnectedError should have connection steps."""
        error = NoDeviceConnectedError()
        assert "No device" in str(error)
        assert "USB debugging" in str(error)

    def test_adb_command_error(self) -> None:
        """ADBCommandError should include command and error."""
        error = ADBCommandError("pm uninstall pkg", "Permission denied", 1)
        assert "pm uninstall pkg" in str(error)
        assert "Permission denied" in str(error)
        assert error.returncode == 1


class TestRecoverableErrors:
    """Tests for recoverable errors."""

    def test_download_error(self) -> None:
        """DownloadError should include app and URL info."""
        error = DownloadError("Olauncher", "https://f-droid.org/...", "Timeout")
        assert "Olauncher" in str(error)
        assert error.app_name == "Olauncher"

    def test_removal_error(self) -> None:
        """RemovalError should include package info."""
        error = RemovalError("Bixby", "com.samsung.bixby", "Protected")
        assert "Bixby" in str(error)
        assert error.package_id == "com.samsung.bixby"

    def test_knox_protected_error(self) -> None:
        """KnoxProtectedError should mention Knox."""
        error = KnoxProtectedError("Knox Agent", "com.samsung.knox")
        assert "Knox" in str(error)


class TestCriticalConfigurationError:
    """Tests for CriticalConfigurationError."""

    def test_default_suggestion(self) -> None:
        """Should have default suggestion about partial state."""
        error = CriticalConfigurationError("Device disconnected")
        assert "partial state" in str(error)
