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

"""ADB command wrapper with error handling.

Provides a clean interface for ADB operations:
- Device detection and info retrieval
- Package listing and management
- App installation
- Setting default apps
"""

import fnmatch
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from clearphone.core.exceptions import (
    ADBCommandError,
    ADBNotFoundError,
    DeviceDisconnectedError,
    MultipleDevicesError,
    NoDeviceConnectedError,
)


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


@dataclass
class DeviceInfo:
    """Information about a connected Android device."""

    serial: str
    model: str
    android_version: str
    manufacturer: str


def check_adb_available() -> bool:
    """Check if ADB is available on the system.

    Returns:
        True if ADB is found in PATH
    """
    return shutil.which("adb") is not None


class ADBDevice:
    """Wrapper for ADB operations on a connected device."""

    def __init__(self, serial: str | None = None) -> None:
        """Initialize the ADB device wrapper.

        Args:
            serial: Optional device serial. If None, auto-detect single device.
        """
        self._serial = serial
        self._device_info: DeviceInfo | None = None

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

    def _run_adb(
        self,
        args: list[str],
        timeout: int = 30,
        check: bool = False,
    ) -> ADBResult:
        """Run an ADB command.

        Args:
            args: Arguments to pass to ADB
            timeout: Command timeout in seconds
            check: If True, raise on non-zero exit code

        Returns:
            ADBResult with command output

        Raises:
            ADBNotFoundError: If ADB not in PATH
            ADBCommandError: If check=True and command fails
            DeviceDisconnectedError: If device is disconnected
        """
        if not check_adb_available():
            raise ADBNotFoundError()

        cmd = ["adb"]
        if self._serial:
            cmd.extend(["-s", self._serial])
        cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as e:
            raise ADBCommandError(
                command=" ".join(args),
                error=f"Command timed out after {timeout}s",
                returncode=-1,
            ) from e

        adb_result = ADBResult(
            returncode=result.returncode,
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
        )

        # Check for device disconnection
        if "device not found" in adb_result.stderr.lower():
            raise DeviceDisconnectedError()

        if check and not adb_result.success:
            raise ADBCommandError(
                command=" ".join(args),
                error=adb_result.stderr or adb_result.stdout,
                returncode=adb_result.returncode,
            )

        return adb_result

    def connect(self) -> DeviceInfo:
        """Connect to an Android device and get its info.

        Returns:
            DeviceInfo for the connected device

        Raises:
            ADBNotFoundError: If ADB not found
            NoDeviceConnectedError: If no device connected
            MultipleDevicesError: If multiple devices connected
        """
        if not check_adb_available():
            raise ADBNotFoundError()

        # Get list of devices
        result = self._run_adb(["devices"])
        lines = result.stdout.strip().split("\n")[1:]  # Skip header
        devices = [line.split("\t")[0] for line in lines if line.strip() and "device" in line]

        if not devices:
            raise NoDeviceConnectedError()

        if len(devices) > 1 and self._serial is None:
            raise MultipleDevicesError(len(devices))

        if self._serial is None:
            self._serial = devices[0]

        # Get device info
        model = self._get_prop("ro.product.model")
        android_version = self._get_prop("ro.build.version.release")
        manufacturer = self._get_prop("ro.product.manufacturer")

        self._device_info = DeviceInfo(
            serial=self._serial,
            model=model,
            android_version=android_version,
            manufacturer=manufacturer,
        )

        return self._device_info

    def _get_prop(self, prop: str) -> str:
        """Get a system property from the device.

        Args:
            prop: Property name

        Returns:
            Property value
        """
        result = self._run_adb(["shell", "getprop", prop])
        return result.stdout.strip()

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
        result = self._run_adb(["shell", "pm", "list", "packages"])
        packages: list[str] = []
        for line in result.stdout.split("\n"):
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
        return self._run_adb(
            ["shell", "pm", "uninstall", "--user", "0", package_id],
            timeout=60,
        )

    def disable_package(self, package_id: str) -> ADBResult:
        """Disable a package for user 0.

        Args:
            package_id: Package identifier

        Returns:
            ADBResult with command output
        """
        return self._run_adb(
            ["shell", "pm", "disable-user", "--user", "0", package_id],
            timeout=60,
        )

    def install_apk(self, apk_path: Path) -> ADBResult:
        """Install an APK file.

        Args:
            apk_path: Path to the APK file

        Returns:
            ADBResult with command output
        """
        return self._run_adb(
            ["install", "-r", str(apk_path)],
            timeout=120,
        )

    def set_default_launcher(self, package_id: str) -> ADBResult:
        """Set the default launcher.

        Args:
            package_id: Launcher package ID

        Returns:
            ADBResult with command output
        """
        return self._run_adb(
            ["shell", "cmd", "role", "add-role-holder", "android.app.role.HOME", package_id],
            timeout=30,
        )

    def set_default_dialer(self, package_id: str) -> ADBResult:
        """Set the default dialer app.

        Args:
            package_id: Dialer package ID

        Returns:
            ADBResult with command output
        """
        return self._run_adb(
            ["shell", "cmd", "role", "add-role-holder", "android.app.role.DIALER", package_id],
            timeout=30,
        )

    def set_default_sms(self, package_id: str) -> ADBResult:
        """Set the default SMS app.

        Args:
            package_id: SMS app package ID

        Returns:
            ADBResult with command output
        """
        return self._run_adb(
            ["shell", "cmd", "role", "add-role-holder", "android.app.role.SMS", package_id],
            timeout=30,
        )

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
        return self._run_adb(
            ["shell", "settings", "put", "secure", "default_input_method", ime_id],
            timeout=30,
        )

    def set_default_gallery(self, package_id: str) -> ADBResult:
        """Set the default gallery app.

        Args:
            package_id: Gallery package ID

        Returns:
            ADBResult with command output
        """
        return self._run_adb(
            ["shell", "cmd", "role", "add-role-holder", "android.app.role.GALLERY", package_id],
            timeout=30,
        )
