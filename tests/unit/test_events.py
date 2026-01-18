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

"""Tests for the events module."""

import pytest

from clearphone.api.events import (
    CameraChoiceEvent,
    DownloadEvent,
    Event,
    EventType,
    PackageEvent,
    PhaseEvent,
    WorkflowEvent,
)


class TestEventType:
    """Tests for EventType enum."""

    def test_workflow_events_exist(self) -> None:
        """Workflow event types should exist."""
        assert EventType.WORKFLOW_STARTED
        assert EventType.WORKFLOW_COMPLETED
        assert EventType.WORKFLOW_FAILED

    def test_package_events_exist(self) -> None:
        """Package event types should exist."""
        assert EventType.PACKAGE_REMOVED
        assert EventType.PACKAGE_REMOVAL_FAILED
        assert EventType.PACKAGE_REMOVAL_SKIPPED

    def test_download_events_exist(self) -> None:
        """Download event types should exist."""
        assert EventType.DOWNLOAD_STARTED
        assert EventType.DOWNLOAD_PROGRESS
        assert EventType.DOWNLOAD_COMPLETED


class TestEvent:
    """Tests for Event dataclass."""

    def test_create_event(self) -> None:
        """Should create a basic event."""
        event = Event(type=EventType.WARNING, message="Test warning")
        assert event.type == EventType.WARNING
        assert event.message == "Test warning"

    def test_event_is_frozen(self) -> None:
        """Events should be immutable."""
        from dataclasses import FrozenInstanceError

        event = Event(type=EventType.WARNING, message="Test")
        with pytest.raises(FrozenInstanceError):
            event.message = "Changed"  # type: ignore[misc]

    def test_event_default_data(self) -> None:
        """Event should have empty dict as default data."""
        event = Event(type=EventType.WARNING)
        assert event.data == {}


class TestWorkflowEvent:
    """Tests for WorkflowEvent dataclass."""

    def test_create_workflow_event(self) -> None:
        """Should create a workflow event."""
        event = WorkflowEvent(
            type=EventType.WORKFLOW_STARTED,
            message="Starting",
            profile_name="test.toml",
            device_name="S24",
        )
        assert event.profile_name == "test.toml"
        assert event.device_name == "S24"


class TestPackageEvent:
    """Tests for PackageEvent dataclass."""

    def test_create_package_event(self) -> None:
        """Should create a package event."""
        event = PackageEvent(
            type=EventType.PACKAGE_REMOVED,
            message="Removed Bixby",
            package_id="com.samsung.bixby",
            package_name="Bixby",
            reason="Pre-installed app",
        )
        assert event.package_id == "com.samsung.bixby"
        assert event.package_name == "Bixby"


class TestDownloadEvent:
    """Tests for DownloadEvent dataclass."""

    def test_create_download_event(self) -> None:
        """Should create a download event."""
        event = DownloadEvent(
            type=EventType.DOWNLOAD_PROGRESS,
            message="Downloading",
            app_id="launcher",
            app_name="Olauncher",
            source="fdroid",
            progress_percent=50.0,
        )
        assert event.progress_percent == 50.0


class TestPhaseEvent:
    """Tests for PhaseEvent dataclass."""

    def test_create_phase_event(self) -> None:
        """Should create a phase event."""
        event = PhaseEvent(
            type=EventType.PHASE_STARTED,
            message="Starting phase",
            phase_name="Loading profile",
            phase_number=1,
            total_phases=8,
        )
        assert event.phase_number == 1
        assert event.total_phases == 8


class TestCameraChoiceEvent:
    """Tests for CameraChoiceEvent dataclass."""

    def test_create_camera_choice_event(self) -> None:
        """Should create a camera choice event."""
        event = CameraChoiceEvent(
            type=EventType.CAMERA_CHOICE_MADE,
            message="Camera chosen",
            stock_camera_name="Samsung Camera",
            stock_camera_package="com.sec.android.app.camera",
            user_choice="fossify",
        )
        assert event.user_choice == "fossify"
        assert event.replacement_name == "Fossify Camera"
