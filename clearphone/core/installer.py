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

"""App installation functionality.

Handles:
- Installing APKs via ADB
- Setting default apps for various roles
"""

from collections.abc import Generator
from pathlib import Path

from clearphone.api.events import (
    DefaultAppEvent,
    Event,
    EventType,
    InstallEvent,
)
from clearphone.core.adb import ADBDevice
from clearphone.core.apps_catalog import AppDefinition


class AppInstaller:
    """Handles installing apps and setting defaults."""

    def __init__(self, adb: ADBDevice, dry_run: bool = False) -> None:
        """Initialize the app installer.

        Args:
            adb: ADB device connection
            dry_run: If True, don't actually install apps
        """
        self.adb = adb
        self.dry_run = dry_run

    def install_apps(
        self, apps: list[tuple[AppDefinition, Path]]
    ) -> Generator[Event, None, tuple[int, int]]:
        """Install a list of apps.

        Args:
            apps: List of (AppDefinition, APK path) tuples

        Yields:
            Installation events

        Returns:
            Tuple of (installed_count, failed_count)
        """
        installed = 0
        failed = 0

        for app, apk_path in apps:
            yield InstallEvent(
                type=EventType.INSTALL_STARTED,
                message=f"Installing: {app.name}",
                app_id=app.id,
                app_name=app.name,
                package_id=app.package_id,
                apk_path=str(apk_path),
            )

            if self.dry_run:
                yield InstallEvent(
                    type=EventType.INSTALL_COMPLETED,
                    message=f"Would install: {app.name} (dry run)",
                    app_id=app.id,
                    app_name=app.name,
                    package_id=app.package_id,
                    apk_path=str(apk_path),
                )
                installed += 1
                continue

            result = self.adb.install_apk(apk_path)

            if result.success or "success" in result.stdout.lower():
                yield InstallEvent(
                    type=EventType.INSTALL_COMPLETED,
                    message=f"Installed: {app.name}",
                    app_id=app.id,
                    app_name=app.name,
                    package_id=app.package_id,
                    apk_path=str(apk_path),
                )
                installed += 1
            else:
                yield InstallEvent(
                    type=EventType.INSTALL_FAILED,
                    message=f"Failed to install {app.name}: {result.stderr or result.stdout}",
                    app_id=app.id,
                    app_name=app.name,
                    package_id=app.package_id,
                    apk_path=str(apk_path),
                )
                failed += 1

        return (installed, failed)

    def set_default_apps(self, apps: dict[str, AppDefinition]) -> Generator[Event, None, None]:
        """Set default apps for various roles.

        Args:
            apps: Dictionary mapping role IDs to AppDefinitions.
                  Supported roles: launcher, dialer, messaging, keyboard, gallery

        Yields:
            Default app setting events
        """
        role_methods = {
            "launcher": ("HOME", self.adb.set_default_launcher),
            "dialer": ("DIALER", self.adb.set_default_dialer),
            "messaging": ("SMS", self.adb.set_default_sms),
            "keyboard": ("KEYBOARD", self.adb.set_default_keyboard),
            "gallery": ("GALLERY", self.adb.set_default_gallery),
        }

        for role_id, app in apps.items():
            if role_id not in role_methods:
                continue

            role_name, method = role_methods[role_id]

            if self.dry_run:
                yield DefaultAppEvent(
                    type=EventType.DEFAULT_APP_SET,
                    message=f"Would set {app.name} as default {role_name} (dry run)",
                    app_id=app.id,
                    app_name=app.name,
                    role=role_name,
                )
                continue

            result = method(app.package_id)

            if result.success:
                yield DefaultAppEvent(
                    type=EventType.DEFAULT_APP_SET,
                    message=f"Set {app.name} as default {role_name}",
                    app_id=app.id,
                    app_name=app.name,
                    role=role_name,
                )
            else:
                yield DefaultAppEvent(
                    type=EventType.DEFAULT_APP_FAILED,
                    message=f"Failed to set {app.name} as default {role_name}: {result.stderr}",
                    app_id=app.id,
                    app_name=app.name,
                    role=role_name,
                )
