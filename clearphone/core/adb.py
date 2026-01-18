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

"""ADB command wrapper using pure-Python adb-shell library.

Provides a clean interface for ADB operations over USB:
- Device detection and info retrieval
- Package listing and management
- App installation
- Setting default apps

No external ADB binary required - connects directly via USB.
"""

import contextlib
import fnmatch
from dataclasses import dataclass
from pathlib import Path

from adb_shell.adb_device import AdbDeviceUsb  # type: ignore[import-untyped]
from adb_shell.auth.keygen import keygen  # type: ignore[import-untyped]
from adb_shell.auth.sign_pythonrsa import PythonRSASigner  # type: ignore[import-untyped]
from adb_shell.exceptions import (  # type: ignore[import-untyped]
    AdbConnectionError,
    AdbTimeoutError,
    DeviceAuthError,
    UsbDeviceNotFoundError,
)

from clearphone.core.exceptions import (
    ADBCommandError,
    DeviceAuthenticationError,
    DeviceDisconnectedError,
    MultipleDevicesError,
    NoDeviceConnectedError,
    USBError,
)

# Default location for ADB RSA keys
CLEARPHONE_CONFIG_DIR = Path.home() / ".clearphone"
ADB_KEY_PATH = CLEARPHONE_CONFIG_DIR / "adbkey"


@dataclass
class ADBResult:
    """Result of an ADB command execution."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        """Check if the command succeeded."""
        return self.returncode == 0

    @property
    def error(self) -> str:
        """Get error message if command failed."""
        return self.stderr or self.stdout


@dataclass
class DeviceInfo:
    """Information about a connected Android device."""

    serial: str
    model: str
    android_version: str
    manufacturer: str


def _ensure_adb_keys() -> PythonRSASigner:
    """Ensure ADB RSA keys exist and return a signer.

    Creates keys in ~/.clearphone/adbkey if they don't exist.

    Returns:
        PythonRSASigner configured with the keys
    """
    CLEARPHONE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    pub_key_path = Path(str(ADB_KEY_PATH) + ".pub")

    if not ADB_KEY_PATH.exists():
        # Generate new key pair
        keygen(str(ADB_KEY_PATH))

    # Load and return signer
    with open(ADB_KEY_PATH, "rb") as f:
        priv_key = f.read()
    with open(pub_key_path, "rb") as f:
        pub_key = f.read()

    return PythonRSASigner(pub_key, priv_key)


class ADBDevice:
    """Wrapper for ADB operations on a connected device via USB.

    Uses the adb-shell library for direct USB communication.
    No external ADB binary required.
    """

    # Timeout for authentication (device may need user to accept prompt)
    AUTH_TIMEOUT_S = 30.0
    # Timeout for shell commands
    COMMAND_TIMEOUT_S = 30.0
    # Timeout for long operations (install, large file transfers)
    LONG_TIMEOUT_S = 120.0

    def __init__(self, serial: str | None = None) -> None:
        """Initialize the ADB device wrapper.

        Args:
            serial: Optional device serial. If None, auto-detect single device.
        """
        self._serial = serial
        self._device_info: DeviceInfo | None = None
        self._adb: AdbDeviceUsb | None = None

    @property
    def serial(self) -> str:
        """Get the device serial number."""
        if self._serial is None:
            raise NoDeviceConnectedError()
        return self._serial

    @property
    def device_info(self) -> DeviceInfo:
        """Get cached device info."""
        if self._device_info is None:
            raise NoDeviceConnectedError()
        return self._device_info

    def _ensure_connected(self) -> AdbDeviceUsb:
        """Ensure we have an active connection.

        Returns:
            The connected AdbDeviceUsb instance

        Raises:
            DeviceDisconnectedError: If device is not connected
        """
        if self._adb is None or not self._adb.available:
            raise DeviceDisconnectedError()
        return self._adb

    def _shell(self, command: str, timeout: float | None = None) -> str:
        """Run a shell command on the device.

        Args:
            command: Shell command to run
            timeout: Optional timeout in seconds

        Returns:
            Command output as string

        Raises:
            DeviceDisconnectedError: If device disconnected
            ADBCommandError: If command fails
        """
        device = self._ensure_connected()
        if timeout is None:
            timeout = self.COMMAND_TIMEOUT_S

        try:
            result = device.shell(command, timeout_s=timeout)
            return result.strip() if isinstance(result, str) else result.decode().strip()
        except AdbTimeoutError as e:
            raise ADBCommandError(
                command=command,
                error=f"Command timed out after {timeout}s",
                returncode=-1,
            ) from e
        except AdbConnectionError as e:
            raise DeviceDisconnectedError() from e

    def connect(self) -> DeviceInfo:
        """Connect to an Android device via USB and get its info.

        Returns:
            DeviceInfo for the connected device

        Raises:
            NoDeviceConnectedError: If no device connected
            MultipleDevicesError: If multiple devices connected
            DeviceAuthenticationError: If device rejects connection
            USBError: If USB communication fails
        """
        signer = _ensure_adb_keys()

        try:
            # AdbDeviceUsb will auto-detect the device
            self._adb = AdbDeviceUsb(serial=self._serial)
            self._adb.connect(
                rsa_keys=[signer],
                auth_timeout_s=self.AUTH_TIMEOUT_S,
            )
        except UsbDeviceNotFoundError as e:
            error_msg = str(e).lower()
            if "multiple" in error_msg:
                # Try to count devices (rough estimate)
                raise MultipleDevicesError(2) from e
            raise NoDeviceConnectedError() from e
        except DeviceAuthError as e:
            raise DeviceAuthenticationError() from e
        except AdbConnectionError as e:
            raise USBError(str(e)) from e
        except Exception as e:
            # Catch USB errors from usb1 library
            error_str = str(e).lower()
            if "usb" in error_str or "libusb" in error_str:
                raise USBError(str(e)) from e
            raise

        # Get device serial if not specified
        if self._serial is None:
            self._serial = self._shell("getprop ro.serialno")

        # Get device info
        model = self._shell("getprop ro.product.model")
        android_version = self._shell("getprop ro.build.version.release")
        manufacturer = self._shell("getprop ro.product.manufacturer")

        self._device_info = DeviceInfo(
            serial=self._serial,
            model=model,
            android_version=android_version,
            manufacturer=manufacturer,
        )

        return self._device_info

    def close(self) -> None:
        """Close the USB connection."""
        if self._adb is not None:
            self._adb.close()
            self._adb = None

    def validate_device_model(self, pattern: str) -> bool:
        """Check if the device model matches the expected pattern.

        Args:
            pattern: Glob pattern to match (e.g., "SM-S921*")

        Returns:
            True if model matches pattern
        """
        if self._device_info is None:
            self.connect()
        return fnmatch.fnmatch(self.device_info.model, pattern)

    def list_packages(self) -> list[str]:
        """List all installed packages on the device.

        Returns:
            List of package IDs
        """
        result = self._shell("pm list packages")
        packages: list[str] = []
        for line in result.split("\n"):
            if line.startswith("package:"):
                packages.append(line[8:].strip())
        return packages

    def is_package_installed(self, package_id: str) -> bool:
        """Check if a package is installed.

        Args:
            package_id: Package identifier

        Returns:
            True if package is installed
        """
        packages = self.list_packages()
        return package_id in packages

    def uninstall_package(self, package_id: str) -> ADBResult:
        """Uninstall a package for user 0 (rootless debloat).

        Args:
            package_id: Package identifier

        Returns:
            ADBResult with command output
        """
        command = f"pm uninstall --user 0 {package_id}"
        try:
            output = self._shell(command, timeout=self.LONG_TIMEOUT_S)
            success = "success" in output.lower()
            return ADBResult(
                returncode=0 if success else 1,
                stdout=output,
                stderr="" if success else output,
            )
        except ADBCommandError as e:
            return ADBResult(returncode=e.returncode, stdout="", stderr=e.error)

    def disable_package(self, package_id: str) -> ADBResult:
        """Disable a package for user 0.

        Args:
            package_id: Package identifier

        Returns:
            ADBResult with command output
        """
        command = f"pm disable-user --user 0 {package_id}"
        try:
            output = self._shell(command, timeout=self.LONG_TIMEOUT_S)
            success = "disabled" in output.lower() or "new state" in output.lower()
            return ADBResult(
                returncode=0 if success else 1,
                stdout=output,
                stderr="" if success else output,
            )
        except ADBCommandError as e:
            return ADBResult(returncode=e.returncode, stdout="", stderr=e.error)

    def enable_package(self, package_id: str) -> ADBResult:
        """Enable a previously disabled package.

        Args:
            package_id: Package identifier

        Returns:
            ADBResult with command output
        """
        command = f"pm enable {package_id}"
        try:
            output = self._shell(command, timeout=self.LONG_TIMEOUT_S)
            success = "enabled" in output.lower() or "new state" in output.lower()
            return ADBResult(
                returncode=0 if success else 1,
                stdout=output,
                stderr="" if success else output,
            )
        except ADBCommandError as e:
            return ADBResult(returncode=e.returncode, stdout="", stderr=e.error)

    def install_apk(self, apk_path: Path) -> ADBResult:
        """Install an APK file.

        Pushes the APK to the device and installs it via pm.

        Args:
            apk_path: Path to the APK file

        Returns:
            ADBResult with command output
        """
        device = self._ensure_connected()

        # Push APK to device temp location
        remote_path = f"/data/local/tmp/{apk_path.name}"
        try:
            device.push(str(apk_path), remote_path, timeout_s=self.LONG_TIMEOUT_S)
        except AdbTimeoutError as e:
            return ADBResult(
                returncode=-1,
                stdout="",
                stderr=f"Timeout pushing APK: {e}",
            )
        except AdbConnectionError as e:
            raise DeviceDisconnectedError() from e

        # Install the APK
        try:
            output = self._shell(f"pm install -r {remote_path}", timeout=self.LONG_TIMEOUT_S)
            success = "success" in output.lower()

            # Clean up the pushed file
            self._shell(f"rm {remote_path}")

            return ADBResult(
                returncode=0 if success else 1,
                stdout=output,
                stderr="" if success else output,
            )
        except ADBCommandError as e:
            # Try to clean up even on error
            with contextlib.suppress(Exception):
                self._shell(f"rm {remote_path}")
            return ADBResult(returncode=e.returncode, stdout="", stderr=e.error)

    def set_default_launcher(self, package_id: str) -> ADBResult:
        """Set the default launcher.

        Args:
            package_id: Launcher package ID

        Returns:
            ADBResult with command output
        """
        command = f"cmd role add-role-holder android.app.role.HOME {package_id}"
        try:
            output = self._shell(command)
            return ADBResult(returncode=0, stdout=output, stderr="")
        except ADBCommandError as e:
            return ADBResult(returncode=e.returncode, stdout="", stderr=e.error)

    def set_default_dialer(self, package_id: str) -> ADBResult:
        """Set the default dialer app.

        Args:
            package_id: Dialer package ID

        Returns:
            ADBResult with command output
        """
        command = f"cmd role add-role-holder android.app.role.DIALER {package_id}"
        try:
            output = self._shell(command)
            return ADBResult(returncode=0, stdout=output, stderr="")
        except ADBCommandError as e:
            return ADBResult(returncode=e.returncode, stdout="", stderr=e.error)

    def set_default_sms(self, package_id: str) -> ADBResult:
        """Set the default SMS app.

        Args:
            package_id: SMS app package ID

        Returns:
            ADBResult with command output
        """
        command = f"cmd role add-role-holder android.app.role.SMS {package_id}"
        try:
            output = self._shell(command)
            return ADBResult(returncode=0, stdout=output, stderr="")
        except ADBCommandError as e:
            return ADBResult(returncode=e.returncode, stdout="", stderr=e.error)

    def set_default_keyboard(self, package_id: str) -> ADBResult:
        """Set the default keyboard.

        Args:
            package_id: Keyboard package ID (full IME path)

        Returns:
            ADBResult with command output
        """
        # The keyboard needs to be set via settings, not roles
        # Format: package_id/.ime.LatinIME or similar
        ime_id = f"{package_id}/.LatinIME"
        command = f"settings put secure default_input_method {ime_id}"
        try:
            output = self._shell(command)
            return ADBResult(returncode=0, stdout=output, stderr="")
        except ADBCommandError as e:
            return ADBResult(returncode=e.returncode, stdout="", stderr=e.error)

    def set_default_gallery(self, package_id: str) -> ADBResult:
        """Set the default gallery app.

        Args:
            package_id: Gallery package ID

        Returns:
            ADBResult with command output
        """
        command = f"cmd role add-role-holder android.app.role.GALLERY {package_id}"
        try:
            output = self._shell(command)
            return ADBResult(returncode=0, stdout=output, stderr="")
        except ADBCommandError as e:
            return ADBResult(returncode=e.returncode, stdout="", stderr=e.error)
