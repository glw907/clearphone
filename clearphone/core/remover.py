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

"""Package removal functionality.

Handles removing packages from the device with:
- Knox-protected package detection
- Graceful failure handling
- Progress events
"""

from collections.abc import Generator

from clearphone.api.events import Event, EventType, PackageEvent
from clearphone.core.adb import ADBDevice
from clearphone.core.profile import PackageToRemove

# Samsung Knox-protected packages that cannot be removed without root
KNOX_PROTECTED_PACKAGES: set[str] = {
    "com.samsung.android.knox.analytics.uploader",
    "com.samsung.android.knox.attestation",
    "com.samsung.android.knox.containeragent",
    "com.samsung.android.knox.containercore",
    "com.samsung.android.knox.kpecore",
    "com.samsung.android.knox.pushmanager",
    "com.samsung.knox.securefolder",
    "com.sec.enterprise.knox.attestation",
    "com.sec.enterprise.knox.cloudmdm.smdms",
    "com.sec.knox.switcher",
    # Samsung core services that Knox protects
    "com.samsung.android.providers.context",
    "com.samsung.android.service.livedrawing",
}


class PackageRemover:
    """Handles removal of packages from the device."""

    def __init__(self, adb: ADBDevice, dry_run: bool = False) -> None:
        """Initialize the package remover.

        Args:
            adb: ADB device connection
            dry_run: If True, don't actually remove packages
        """
        self.adb = adb
        self.dry_run = dry_run
        self._installed_packages: set[str] | None = None

    def _get_installed_packages(self) -> set[str]:
        """Get the set of installed packages, cached.

        Returns:
            Set of installed package IDs
        """
        if self._installed_packages is None:
            self._installed_packages = set(self.adb.list_packages())
        return self._installed_packages

    def remove_packages(
        self, packages: list[PackageToRemove]
    ) -> Generator[Event, None, tuple[int, int, int]]:
        """Remove packages from the device.

        Args:
            packages: List of packages to remove

        Yields:
            Package removal events

        Returns:
            Tuple of (removed_count, skipped_count, failed_count)
        """
        removed = 0
        skipped = 0
        failed = 0

        installed = self._get_installed_packages()

        for pkg in packages:
            # Check if package is installed
            if pkg.id not in installed:
                yield PackageEvent(
                    type=EventType.PACKAGE_NOT_INSTALLED,
                    message=f"Not installed: {pkg.name}",
                    package_id=pkg.id,
                    package_name=pkg.name,
                    reason="Package not found on device",
                )
                skipped += 1
                continue

            # Check if Knox-protected
            if pkg.id in KNOX_PROTECTED_PACKAGES:
                yield PackageEvent(
                    type=EventType.PACKAGE_REMOVAL_SKIPPED,
                    message=f"Knox protected: {pkg.name}",
                    package_id=pkg.id,
                    package_name=pkg.name,
                    reason="Package is protected by Samsung Knox",
                )
                skipped += 1
                continue

            # Attempt removal
            yield PackageEvent(
                type=EventType.PACKAGE_REMOVAL_STARTED,
                message=f"Removing: {pkg.name}",
                package_id=pkg.id,
                package_name=pkg.name,
            )

            if self.dry_run:
                yield PackageEvent(
                    type=EventType.PACKAGE_REMOVED,
                    message=f"Would remove: {pkg.name} (dry run)",
                    package_id=pkg.id,
                    package_name=pkg.name,
                )
                removed += 1
                continue

            result = self.adb.uninstall_package(pkg.id)

            if result.success or "success" in result.stdout.lower():
                yield PackageEvent(
                    type=EventType.PACKAGE_REMOVED,
                    message=f"Removed: {pkg.name}",
                    package_id=pkg.id,
                    package_name=pkg.name,
                )
                removed += 1
            else:
                # Check for common failure reasons
                error_msg = result.stderr or result.stdout
                reason = self._categorize_failure(error_msg)

                yield PackageEvent(
                    type=EventType.PACKAGE_REMOVAL_FAILED,
                    message=f"Failed to remove: {pkg.name}",
                    package_id=pkg.id,
                    package_name=pkg.name,
                    reason=reason,
                )
                failed += 1

        return (removed, skipped, failed)

    def _categorize_failure(self, error_msg: str) -> str:
        """Categorize the failure reason from error message.

        Args:
            error_msg: Error message from ADB

        Returns:
            Human-readable failure reason
        """
        error_lower = error_msg.lower()

        if "not installed" in error_lower:
            return "Package not installed"
        if "device policy manager" in error_lower or "admin" in error_lower:
            return "Package is a device administrator"
        if "permission" in error_lower:
            return "Permission denied"
        if "failure" in error_lower:
            return f"Uninstall failed: {error_msg}"

        return error_msg or "Unknown error"
