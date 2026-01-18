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

"""Exception hierarchy for Clearphone.

Three categories of errors:
1. Validation errors - Fail fast before making changes
2. Recoverable errors - Log and continue
3. Critical errors - Abort immediately
"""


class ClearphoneError(Exception):
    """Base exception for all Clearphone errors.

    All errors include a message explaining what happened and a suggestion
    for how to fix it.
    """

    def __init__(self, message: str, suggestion: str = "") -> None:
        """Initialize the error.

        Args:
            message: What went wrong
            suggestion: How to fix it
        """
        self.message = message
        self.suggestion = suggestion
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.suggestion:
            return f"{self.message}\n\n{self.suggestion}"
        return self.message


# ============================================================================
# Validation Errors - Fail fast before making changes
# ============================================================================


class ValidationError(ClearphoneError):
    """Base class for validation errors."""


class ProfileNotFoundError(ValidationError):
    """Device profile file does not exist."""

    def __init__(self, path: str) -> None:
        super().__init__(
            message=f"Profile not found: {path}",
            suggestion="Check that the profile path is correct and the file exists.",
        )
        self.path = path


class ProfileParseError(ValidationError):
    """Device profile TOML is invalid or missing required fields."""

    def __init__(self, path: str, details: str) -> None:
        super().__init__(
            message=f"Failed to parse profile: {path}\n{details}",
            suggestion="Check the profile file for TOML syntax errors or missing required fields.",
        )
        self.path = path
        self.details = details


class AppNotFoundError(ValidationError):
    """App ID referenced in profile does not exist in the catalog."""

    def __init__(self, app_id: str, catalog_type: str = "catalog") -> None:
        super().__init__(
            message=f"App '{app_id}' not found in {catalog_type}",
            suggestion=f"Check that '{app_id}' is defined in the apps catalog files.",
        )
        self.app_id = app_id
        self.catalog_type = catalog_type


class DeviceMismatchError(ValidationError):
    """Connected device does not match the expected model pattern."""

    def __init__(self, expected_pattern: str, expected_name: str, actual_model: str) -> None:
        super().__init__(
            message=f"Wrong device model\n\nExpected: {expected_name} ({expected_pattern})\nFound: {actual_model}",
            suggestion="Connect the correct device or use a different profile.",
        )
        self.expected_pattern = expected_pattern
        self.expected_name = expected_name
        self.actual_model = actual_model


class CatalogNotFoundError(ValidationError):
    """Apps catalog directory or required files not found."""

    def __init__(self, path: str) -> None:
        super().__init__(
            message=f"Apps catalog not found: {path}",
            suggestion="Ensure the apps/ directory exists with core.toml and extras/ subdirectory.",
        )
        self.path = path


class CatalogParseError(ValidationError):
    """Apps catalog TOML is invalid."""

    def __init__(self, path: str, details: str) -> None:
        super().__init__(
            message=f"Failed to parse catalog: {path}\n{details}",
            suggestion="Check the catalog file for TOML syntax errors.",
        )
        self.path = path
        self.details = details


# ============================================================================
# ADB Errors - Connection and command issues
# ============================================================================


class ADBError(ClearphoneError):
    """Base class for ADB-related errors."""


class USBError(ADBError):
    """USB communication error with the device."""

    def __init__(self, details: str) -> None:
        super().__init__(
            message=f"USB communication error: {details}",
            suggestion="1. Ensure the device is connected via USB\n"
            "2. Try a different USB port or cable\n"
            "3. On Linux, you may need to set up udev rules for your device",
        )
        self.details = details


class DeviceAuthenticationError(ADBError):
    """Device rejected the connection (RSA key not authorized)."""

    def __init__(self) -> None:
        super().__init__(
            message="Device authentication failed",
            suggestion="1. Check your device for an 'Allow USB debugging' prompt\n"
            "2. Tap 'Allow' (optionally check 'Always allow from this computer')\n"
            "3. Try running clearphone again",
        )


class NoDeviceConnectedError(ADBError):
    """No Android device connected via USB."""

    def __init__(self) -> None:
        super().__init__(
            message="No device connected",
            suggestion="1. Connect your Android device via USB\n"
            "2. Enable USB debugging in Developer Options\n"
            "3. Accept the debugging prompt on your device",
        )


class MultipleDevicesError(ADBError):
    """Multiple Android devices connected."""

    def __init__(self, device_count: int) -> None:
        super().__init__(
            message=f"Multiple devices connected ({device_count} devices)",
            suggestion="Disconnect all but one device and try again.",
        )
        self.device_count = device_count


class DeviceDisconnectedError(ADBError):
    """Device was disconnected during configuration."""

    def __init__(self) -> None:
        super().__init__(
            message="Device disconnected during configuration",
            suggestion="Reconnect the device and run configuration again.\n"
            "Note: Some changes may have already been applied.",
        )


class ADBCommandError(ADBError):
    """ADB command failed to execute."""

    def __init__(self, command: str, error: str, returncode: int = 1) -> None:
        super().__init__(
            message=f"ADB command failed: {command}\n{error}",
            suggestion="Check device connection and try again.",
        )
        self.command = command
        self.error = error
        self.returncode = returncode


# ============================================================================
# Recoverable Errors - Log and continue
# ============================================================================


class RecoverableError(ClearphoneError):
    """Base class for errors that should be logged but not stop the workflow."""


class DownloadError(RecoverableError):
    """APK download failed."""

    def __init__(self, app_name: str, url: str, details: str) -> None:
        super().__init__(
            message=f"Failed to download {app_name} from {url}\n{details}",
            suggestion="Check your internet connection. The app will be skipped.",
        )
        self.app_name = app_name
        self.url = url
        self.details = details


class NetworkError(RecoverableError):
    """Network connection failed."""

    def __init__(self, details: str) -> None:
        super().__init__(
            message=f"Network error: {details}",
            suggestion="Check your internet connection and try again.",
        )
        self.details = details


class FDroidIndexError(RecoverableError):
    """Failed to fetch or parse F-Droid index."""

    def __init__(self, details: str) -> None:
        super().__init__(
            message=f"Failed to fetch F-Droid index: {details}",
            suggestion="Check your internet connection. F-Droid apps cannot be installed.",
        )
        self.details = details


class InstallError(RecoverableError):
    """App installation failed."""

    def __init__(self, app_name: str, package_id: str, details: str) -> None:
        super().__init__(
            message=f"Failed to install {app_name} ({package_id})\n{details}",
            suggestion="The app will be skipped. You can install it manually later.",
        )
        self.app_name = app_name
        self.package_id = package_id
        self.details = details


class RemovalError(RecoverableError):
    """Package removal failed."""

    def __init__(self, package_name: str, package_id: str, details: str) -> None:
        super().__init__(
            message=f"Failed to remove {package_name} ({package_id})\n{details}",
            suggestion="The package will be skipped. It may be protected by the system.",
        )
        self.package_name = package_name
        self.package_id = package_id
        self.details = details


class KnoxProtectedError(RecoverableError):
    """Package is protected by Samsung Knox and cannot be removed."""

    def __init__(self, package_name: str, package_id: str) -> None:
        super().__init__(
            message=f"Cannot remove {package_name} ({package_id}) - Knox protected",
            suggestion="This package is protected by Samsung Knox security.\n"
            "It cannot be removed without rooting the device.",
        )
        self.package_name = package_name
        self.package_id = package_id


class ChecksumError(RecoverableError):
    """Downloaded file checksum does not match expected value."""

    def __init__(self, app_name: str, expected: str, actual: str) -> None:
        super().__init__(
            message=f"Checksum mismatch for {app_name}\nExpected: {expected}\nActual: {actual}",
            suggestion="The download may be corrupted. The app will be skipped.",
        )
        self.app_name = app_name
        self.expected = expected
        self.actual = actual


# ============================================================================
# Critical Errors - Abort immediately
# ============================================================================


class CriticalConfigurationError(ClearphoneError):
    """Critical error that requires aborting the configuration."""

    def __init__(self, message: str, suggestion: str = "") -> None:
        if not suggestion:
            suggestion = "Configuration has been aborted. Your device may be in a partial state."
        super().__init__(message=message, suggestion=suggestion)
