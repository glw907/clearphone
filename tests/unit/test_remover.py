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

"""Tests for the remover module."""

from unittest.mock import MagicMock

from clearphone.api.events import EventType
from clearphone.core.profile import PackageToRemove
from clearphone.core.remover import KNOX_PROTECTED_PACKAGES, PackageRemover


class TestKnoxProtectedPackages:
    """Tests for Knox protected packages set."""

    def test_knox_packages_defined(self) -> None:
        """Should have Knox protected packages defined."""
        assert len(KNOX_PROTECTED_PACKAGES) > 0

    def test_contains_knox_core(self) -> None:
        """Should contain core Knox packages."""
        assert "com.samsung.android.knox.containercore" in KNOX_PROTECTED_PACKAGES


class TestPackageRemover:
    """Tests for PackageRemover class."""

    def test_remove_installed_package(self, mock_adb_device: MagicMock) -> None:
        """Should remove an installed package."""
        remover = PackageRemover(mock_adb_device)

        packages = [
            PackageToRemove(
                id="com.samsung.android.bixby.agent",
                name="Bixby Voice",
                source="Samsung",
                function="Voice assistant",
                category="vendor",
                action="remove",
            )
        ]

        events = []
        gen = remover.remove_packages(packages)
        try:
            while True:
                events.append(next(gen))
        except StopIteration as e:
            removed, skipped, failed = e.value

        assert removed == 1
        assert skipped == 0
        assert failed == 0
        assert any(e.type == EventType.PACKAGE_REMOVED for e in events)

    def test_skip_not_installed_package(self, mock_adb_device: MagicMock) -> None:
        """Should skip packages not installed on device."""
        # Mock to return empty package list
        mock_adb_device.list_packages.return_value = []

        remover = PackageRemover(mock_adb_device)

        packages = [
            PackageToRemove(
                id="com.nonexistent.app",
                name="Nonexistent",
                source="Test",
                function="Test",
                category="test",
                action="remove",
            )
        ]

        events = []
        gen = remover.remove_packages(packages)
        try:
            while True:
                events.append(next(gen))
        except StopIteration as e:
            removed, skipped, failed = e.value

        assert removed == 0
        assert skipped == 1
        assert failed == 0
        assert any(e.type == EventType.PACKAGE_NOT_INSTALLED for e in events)

    def test_skip_knox_protected_package(self, mock_adb_device: MagicMock) -> None:
        """Should skip Knox protected packages."""
        knox_package = next(iter(KNOX_PROTECTED_PACKAGES))
        mock_adb_device.list_packages.return_value = [knox_package]

        remover = PackageRemover(mock_adb_device)

        packages = [
            PackageToRemove(
                id=knox_package,
                name="Knox Package",
                source="Samsung",
                function="Security",
                category="system",
                action="remove",
            )
        ]

        events = []
        gen = remover.remove_packages(packages)
        try:
            while True:
                events.append(next(gen))
        except StopIteration as e:
            removed, skipped, failed = e.value

        assert removed == 0
        assert skipped == 1
        assert failed == 0
        assert any(e.type == EventType.PACKAGE_REMOVAL_SKIPPED for e in events)
        assert any("Knox" in e.reason for e in events if hasattr(e, "reason"))

    def test_handle_removal_failure(self, mock_adb_device: MagicMock) -> None:
        """Should handle removal failures gracefully."""
        mock_adb_device.uninstall_package.return_value = MagicMock(
            success=False, stdout="Failure", stderr="Permission denied"
        )

        remover = PackageRemover(mock_adb_device)

        packages = [
            PackageToRemove(
                id="com.samsung.android.bixby.agent",
                name="Bixby Voice",
                source="Samsung",
                function="Voice assistant",
                category="vendor",
                action="remove",
            )
        ]

        events = []
        gen = remover.remove_packages(packages)
        try:
            while True:
                events.append(next(gen))
        except StopIteration as e:
            removed, skipped, failed = e.value

        assert removed == 0
        assert failed == 1
        assert any(e.type == EventType.PACKAGE_REMOVAL_FAILED for e in events)

    def test_dry_run_mode(self, mock_adb_device: MagicMock) -> None:
        """Should not actually remove packages in dry run mode."""
        remover = PackageRemover(mock_adb_device, dry_run=True)

        packages = [
            PackageToRemove(
                id="com.samsung.android.bixby.agent",
                name="Bixby Voice",
                source="Samsung",
                function="Voice assistant",
                category="vendor",
                action="remove",
            )
        ]

        events = []
        gen = remover.remove_packages(packages)
        try:
            while True:
                events.append(next(gen))
        except StopIteration as e:
            removed, skipped, failed = e.value

        # Should report as "removed" but not call ADB
        assert removed == 1
        mock_adb_device.uninstall_package.assert_not_called()
        assert any("dry run" in e.message.lower() for e in events)

    def test_multiple_packages(self, mock_adb_device: MagicMock) -> None:
        """Should process multiple packages."""
        mock_adb_device.list_packages.return_value = [
            "com.samsung.android.bixby.agent",
            "com.facebook.katana",
        ]

        remover = PackageRemover(mock_adb_device)

        packages = [
            PackageToRemove(
                id="com.samsung.android.bixby.agent",
                name="Bixby",
                source="Samsung",
                function="Assistant",
                category="vendor",
                action="remove",
            ),
            PackageToRemove(
                id="com.facebook.katana",
                name="Facebook",
                source="Meta",
                function="Social",
                category="vendor",
                action="remove",
            ),
            PackageToRemove(
                id="com.nonexistent.app",
                name="Nonexistent",
                source="Test",
                function="Test",
                category="test",
                action="remove",
            ),
        ]

        gen = remover.remove_packages(packages)
        try:
            while True:
                next(gen)
        except StopIteration as e:
            removed, skipped, failed = e.value

        assert removed == 2
        assert skipped == 1  # nonexistent package
        assert failed == 0

    def test_categorize_failure_not_installed(self) -> None:
        """Should categorize 'not installed' failure."""
        mock_adb = MagicMock()
        remover = PackageRemover(mock_adb)

        reason = remover._categorize_failure("Failure [not installed for 0]")
        assert "not installed" in reason.lower()

    def test_categorize_failure_admin(self) -> None:
        """Should categorize device admin failure."""
        mock_adb = MagicMock()
        remover = PackageRemover(mock_adb)

        reason = remover._categorize_failure("Device policy manager won't allow")
        assert "administrator" in reason.lower()
