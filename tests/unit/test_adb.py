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

"""Tests for the adb module using adb-shell library."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from clearphone.core.adb import ADBDevice, ADBResult, _ensure_adb_keys
from clearphone.core.exceptions import (
    DeviceAuthenticationError,
    DeviceDisconnectedError,
    MultipleDevicesError,
    NoDeviceConnectedError,
    USBError,
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


class TestEnsureADBKeys:
    """Tests for _ensure_adb_keys function."""

    @patch("clearphone.core.adb.PythonRSASigner")
    @patch("clearphone.core.adb.keygen")
    def test_creates_keys_if_not_exist(
        self, mock_keygen: MagicMock, mock_signer_class: MagicMock, tmp_path: Path
    ) -> None:
        """Should create keys if they don't exist."""
        config_dir = tmp_path / ".clearphone"
        config_dir.mkdir(parents=True)

        key_path = config_dir / "adbkey"

        # Mock keygen to create the key files
        def create_keys(path: str) -> None:
            Path(path).write_bytes(b"mock_priv_key")
            Path(path + ".pub").write_bytes(b"mock_pub_key")

        mock_keygen.side_effect = create_keys
        mock_signer_class.return_value = MagicMock()

        with (
            patch("clearphone.core.adb.CLEARPHONE_CONFIG_DIR", config_dir),
            patch("clearphone.core.adb.ADB_KEY_PATH", key_path),
        ):
            signer = _ensure_adb_keys()

        mock_keygen.assert_called_once_with(str(key_path))
        mock_signer_class.assert_called_once()
        assert signer is not None

    @patch("clearphone.core.adb.PythonRSASigner")
    @patch("clearphone.core.adb.keygen")
    def test_uses_existing_keys(
        self, mock_keygen: MagicMock, mock_signer_class: MagicMock, tmp_path: Path
    ) -> None:
        """Should use existing keys without regenerating."""
        config_dir = tmp_path / ".clearphone"
        config_dir.mkdir(parents=True)

        key_path = config_dir / "adbkey"
        pub_key_path = config_dir / "adbkey.pub"

        # Create existing keys
        key_path.write_bytes(b"existing_priv_key")
        pub_key_path.write_bytes(b"existing_pub_key")

        mock_signer_class.return_value = MagicMock()

        with (
            patch("clearphone.core.adb.CLEARPHONE_CONFIG_DIR", config_dir),
            patch("clearphone.core.adb.ADB_KEY_PATH", key_path),
        ):
            signer = _ensure_adb_keys()

        mock_keygen.assert_not_called()
        mock_signer_class.assert_called_once()
        assert signer is not None


class TestADBDevice:
    """Tests for ADBDevice class."""

    @patch("clearphone.core.adb._ensure_adb_keys")
    @patch("clearphone.core.adb.AdbDeviceUsb")
    def test_connect_single_device(self, mock_usb_class: MagicMock, mock_keys: MagicMock) -> None:
        """Should connect to a single device."""
        mock_keys.return_value = MagicMock()

        # Create mock device
        mock_device = MagicMock()
        mock_device.available = True

        # Set up shell command responses
        def shell_side_effect(cmd: str, **kwargs: dict) -> str:
            if "ro.serialno" in cmd:
                return "ABC123"
            if "ro.product.model" in cmd:
                return "SM-S921U"
            if "ro.build.version.release" in cmd:
                return "14"
            if "ro.product.manufacturer" in cmd:
                return "samsung"
            return ""

        mock_device.shell.side_effect = shell_side_effect
        mock_usb_class.return_value = mock_device

        adb = ADBDevice()
        device_info = adb.connect()

        assert device_info.serial == "ABC123"
        assert device_info.model == "SM-S921U"
        assert device_info.android_version == "14"
        assert device_info.manufacturer == "samsung"
        mock_device.connect.assert_called_once()

    @patch("clearphone.core.adb._ensure_adb_keys")
    @patch("clearphone.core.adb.AdbDeviceUsb")
    def test_connect_no_device(self, mock_usb_class: MagicMock, mock_keys: MagicMock) -> None:
        """Should raise NoDeviceConnectedError when no device."""
        from adb_shell.exceptions import UsbDeviceNotFoundError

        mock_keys.return_value = MagicMock()
        mock_usb_class.side_effect = UsbDeviceNotFoundError("No device found")

        adb = ADBDevice()
        with pytest.raises(NoDeviceConnectedError):
            adb.connect()

    @patch("clearphone.core.adb._ensure_adb_keys")
    @patch("clearphone.core.adb.AdbDeviceUsb")
    def test_connect_multiple_devices(
        self, mock_usb_class: MagicMock, mock_keys: MagicMock
    ) -> None:
        """Should raise MultipleDevicesError when multiple devices."""
        from adb_shell.exceptions import UsbDeviceNotFoundError

        mock_keys.return_value = MagicMock()
        mock_usb_class.side_effect = UsbDeviceNotFoundError("multiple devices found")

        adb = ADBDevice()
        with pytest.raises(MultipleDevicesError):
            adb.connect()

    @patch("clearphone.core.adb._ensure_adb_keys")
    @patch("clearphone.core.adb.AdbDeviceUsb")
    def test_connect_auth_error(self, mock_usb_class: MagicMock, mock_keys: MagicMock) -> None:
        """Should raise DeviceAuthenticationError when device rejects connection."""
        from adb_shell.exceptions import DeviceAuthError

        mock_keys.return_value = MagicMock()
        mock_usb_class.return_value = MagicMock()
        mock_usb_class.return_value.connect.side_effect = DeviceAuthError("Auth failed")

        adb = ADBDevice()
        with pytest.raises(DeviceAuthenticationError):
            adb.connect()

    @patch("clearphone.core.adb._ensure_adb_keys")
    @patch("clearphone.core.adb.AdbDeviceUsb")
    def test_connect_usb_error(self, mock_usb_class: MagicMock, mock_keys: MagicMock) -> None:
        """Should raise USBError for USB communication failures."""
        from adb_shell.exceptions import AdbConnectionError

        mock_keys.return_value = MagicMock()
        mock_usb_class.return_value = MagicMock()
        mock_usb_class.return_value.connect.side_effect = AdbConnectionError("USB error")

        adb = ADBDevice()
        with pytest.raises(USBError):
            adb.connect()

    def test_validate_device_model(self, mock_adb_device: MagicMock) -> None:
        """Should validate device model against pattern."""
        adb = ADBDevice()
        adb._serial = "MOCK123"
        adb._device_info = mock_adb_device.device_info
        adb._adb = MagicMock()
        adb._adb.available = True

        assert adb.validate_device_model("SM-S921*") is True
        assert adb.validate_device_model("SM-S911*") is False

    def test_list_packages(self) -> None:
        """Should parse package list output."""
        adb = ADBDevice(serial="ABC123")
        adb._adb = MagicMock()
        adb._adb.available = True
        adb._adb.shell.return_value = "package:com.samsung.bixby\npackage:com.google.android.gm\n"

        packages = adb.list_packages()

        assert "com.samsung.bixby" in packages
        assert "com.google.android.gm" in packages

    def test_uninstall_package_success(self) -> None:
        """Should return success for successful uninstall."""
        adb = ADBDevice(serial="ABC123")
        adb._adb = MagicMock()
        adb._adb.available = True
        adb._adb.shell.return_value = "Success"

        result = adb.uninstall_package("com.samsung.bixby")

        assert result.success
        assert "Success" in result.stdout

    def test_uninstall_package_failure(self) -> None:
        """Should return failure for failed uninstall."""
        adb = ADBDevice(serial="ABC123")
        adb._adb = MagicMock()
        adb._adb.available = True
        adb._adb.shell.return_value = "Failure [DELETE_FAILED_INTERNAL_ERROR]"

        result = adb.uninstall_package("com.protected.package")

        assert not result.success

    def test_install_apk(self, tmp_path: Path) -> None:
        """Should push APK and install it."""
        # Create a mock APK file
        apk_path = tmp_path / "app.apk"
        apk_path.write_bytes(b"fake apk content")

        adb = ADBDevice(serial="ABC123")
        adb._adb = MagicMock()
        adb._adb.available = True
        adb._adb.shell.return_value = "Success"

        result = adb.install_apk(apk_path)

        assert result.success
        # Verify push was called
        adb._adb.push.assert_called_once()
        # Verify install command was run
        assert adb._adb.shell.call_count >= 1

    def test_device_not_connected_error(self) -> None:
        """Should raise DeviceDisconnectedError when device is None."""
        adb = ADBDevice(serial="ABC123")
        adb._adb = None

        with pytest.raises(DeviceDisconnectedError):
            adb.list_packages()

    def test_device_not_available_error(self) -> None:
        """Should raise DeviceDisconnectedError when device not available."""
        adb = ADBDevice(serial="ABC123")
        adb._adb = MagicMock()
        adb._adb.available = False

        with pytest.raises(DeviceDisconnectedError):
            adb.list_packages()

    def test_set_default_launcher(self) -> None:
        """Should call correct shell command for launcher."""
        adb = ADBDevice(serial="ABC123")
        adb._adb = MagicMock()
        adb._adb.available = True
        adb._adb.shell.return_value = ""

        result = adb.set_default_launcher("app.olauncher")

        assert result.success
        adb._adb.shell.assert_called_with(
            "cmd role add-role-holder android.app.role.HOME app.olauncher",
            timeout_s=30.0,
        )

    def test_set_default_dialer(self) -> None:
        """Should call correct shell command for dialer."""
        adb = ADBDevice(serial="ABC123")
        adb._adb = MagicMock()
        adb._adb.available = True
        adb._adb.shell.return_value = ""

        result = adb.set_default_dialer("com.simplemobiletools.dialer")

        assert result.success
        adb._adb.shell.assert_called_with(
            "cmd role add-role-holder android.app.role.DIALER com.simplemobiletools.dialer",
            timeout_s=30.0,
        )

    def test_set_default_sms(self) -> None:
        """Should call correct shell command for SMS app."""
        adb = ADBDevice(serial="ABC123")
        adb._adb = MagicMock()
        adb._adb.available = True
        adb._adb.shell.return_value = ""

        result = adb.set_default_sms("com.simplemobiletools.smsmessenger")

        assert result.success
        adb._adb.shell.assert_called_with(
            "cmd role add-role-holder android.app.role.SMS com.simplemobiletools.smsmessenger",
            timeout_s=30.0,
        )

    def test_set_default_keyboard(self) -> None:
        """Should call correct settings command for keyboard."""
        adb = ADBDevice(serial="ABC123")
        adb._adb = MagicMock()
        adb._adb.available = True
        adb._adb.shell.return_value = ""

        result = adb.set_default_keyboard("org.futo.inputmethod.latin")

        assert result.success
        adb._adb.shell.assert_called_with(
            "settings put secure default_input_method org.futo.inputmethod.latin/.LatinIME",
            timeout_s=30.0,
        )

    def test_close(self) -> None:
        """Should close the connection."""
        adb = ADBDevice(serial="ABC123")
        mock_device = MagicMock()
        adb._adb = mock_device

        adb.close()

        mock_device.close.assert_called_once()
        assert adb._adb is None
