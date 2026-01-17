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

"""Tests for the adb module."""

from unittest.mock import MagicMock, patch

import pytest

from clearphone.core.adb import ADBDevice, ADBResult, check_adb_available
from clearphone.core.exceptions import (
    ADBNotFoundError,
    MultipleDevicesError,
    NoDeviceConnectedError,
)


class TestADBResult:
    """Tests for ADBResult dataclass."""

    def test_success_property(self) -> None:
        """Should return True for returncode 0."""
        result = ADBResult(returncode=0, stdout="Success", stderr="")
        assert result.success is True

    def test_failure_property(self) -> None:
        """Should return False for non-zero returncode."""
        result = ADBResult(returncode=1, stdout="", stderr="Error")
        assert result.success is False


class TestCheckADBAvailable:
    """Tests for check_adb_available function."""

    @patch("shutil.which")
    def test_adb_found(self, mock_which: MagicMock) -> None:
        """Should return True when ADB is found."""
        mock_which.return_value = "/usr/bin/adb"
        assert check_adb_available() is True

    @patch("shutil.which")
    def test_adb_not_found(self, mock_which: MagicMock) -> None:
        """Should return False when ADB is not found."""
        mock_which.return_value = None
        assert check_adb_available() is False


class TestADBDevice:
    """Tests for ADBDevice class."""

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_connect_single_device(self, mock_which: MagicMock, mock_run: MagicMock) -> None:
        """Should connect to a single device."""
        mock_which.return_value = "/usr/bin/adb"

        # Mock device list response
        def run_side_effect(cmd: list[str], **kwargs: dict) -> MagicMock:
            result = MagicMock()
            result.returncode = 0
            result.stderr = ""

            if "devices" in cmd:
                result.stdout = "List of devices attached\nABC123\tdevice\n"
            elif "ro.product.model" in cmd:
                result.stdout = "SM-S921U"
            elif "ro.build.version.release" in cmd:
                result.stdout = "14"
            elif "ro.product.manufacturer" in cmd:
                result.stdout = "samsung"
            else:
                result.stdout = ""

            return result

        mock_run.side_effect = run_side_effect

        adb = ADBDevice()
        device_info = adb.connect()

        assert device_info.serial == "ABC123"
        assert device_info.model == "SM-S921U"
        assert device_info.android_version == "14"

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_connect_no_device(self, mock_which: MagicMock, mock_run: MagicMock) -> None:
        """Should raise NoDeviceConnectedError when no device."""
        mock_which.return_value = "/usr/bin/adb"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="List of devices attached\n",
            stderr="",
        )

        adb = ADBDevice()
        with pytest.raises(NoDeviceConnectedError):
            adb.connect()

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_connect_multiple_devices(self, mock_which: MagicMock, mock_run: MagicMock) -> None:
        """Should raise MultipleDevicesError when multiple devices."""
        mock_which.return_value = "/usr/bin/adb"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="List of devices attached\nABC123\tdevice\nDEF456\tdevice\n",
            stderr="",
        )

        adb = ADBDevice()
        with pytest.raises(MultipleDevicesError):
            adb.connect()

    @patch("shutil.which")
    def test_adb_not_available(self, mock_which: MagicMock) -> None:
        """Should raise ADBNotFoundError when ADB not available."""
        mock_which.return_value = None

        adb = ADBDevice()
        with pytest.raises(ADBNotFoundError):
            adb.connect()

    def test_validate_device_model(self, mock_adb_device: MagicMock) -> None:
        """Should validate device model against pattern."""
        adb = ADBDevice()
        adb._serial = "MOCK123"
        adb._device_info = mock_adb_device.device_info

        assert adb.validate_device_model("SM-S921*") is True
        assert adb.validate_device_model("SM-S911*") is False

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_list_packages(self, mock_which: MagicMock, mock_run: MagicMock) -> None:
        """Should parse package list output."""
        mock_which.return_value = "/usr/bin/adb"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="package:com.samsung.bixby\npackage:com.google.android.gm\n",
            stderr="",
        )

        adb = ADBDevice(serial="ABC123")
        packages = adb.list_packages()

        assert "com.samsung.bixby" in packages
        assert "com.google.android.gm" in packages

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_uninstall_package(self, mock_which: MagicMock, mock_run: MagicMock) -> None:
        """Should generate correct uninstall command."""
        mock_which.return_value = "/usr/bin/adb"
        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

        adb = ADBDevice(serial="ABC123")
        result = adb.uninstall_package("com.samsung.bixby")

        assert result.success
        # Verify correct command was called
        call_args = mock_run.call_args[0][0]
        assert "pm" in call_args
        assert "uninstall" in call_args
        assert "--user" in call_args
        assert "0" in call_args
        assert "com.samsung.bixby" in call_args

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_install_apk(self, mock_which: MagicMock, mock_run: MagicMock) -> None:
        """Should generate correct install command."""
        mock_which.return_value = "/usr/bin/adb"
        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

        from pathlib import Path

        adb = ADBDevice(serial="ABC123")
        result = adb.install_apk(Path("/tmp/app.apk"))

        assert result.success
        call_args = mock_run.call_args[0][0]
        assert "install" in call_args
        assert "-r" in call_args
