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

"""Event types and dataclasses for the event-driven architecture."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class EventType(Enum):
    """Types of events emitted during configuration workflow."""

    # Workflow events
    WORKFLOW_STARTED = auto()
    WORKFLOW_COMPLETED = auto()
    WORKFLOW_FAILED = auto()

    # Phase events
    PHASE_STARTED = auto()
    PHASE_COMPLETED = auto()

    # Device events
    DEVICE_CONNECTED = auto()
    DEVICE_VALIDATED = auto()

    # Package removal events
    PACKAGE_REMOVAL_STARTED = auto()
    PACKAGE_REMOVED = auto()
    PACKAGE_REMOVAL_SKIPPED = auto()
    PACKAGE_REMOVAL_FAILED = auto()
    PACKAGE_NOT_INSTALLED = auto()

    # Download events
    DOWNLOAD_STARTED = auto()
    DOWNLOAD_PROGRESS = auto()
    DOWNLOAD_COMPLETED = auto()
    DOWNLOAD_FAILED = auto()

    # Install events
    INSTALL_STARTED = auto()
    INSTALL_COMPLETED = auto()
    INSTALL_FAILED = auto()

    # Default app events
    DEFAULT_APP_SET = auto()
    DEFAULT_APP_FAILED = auto()

    # User interaction events
    CAMERA_CHOICE_REQUIRED = auto()
    CAMERA_CHOICE_MADE = auto()
    EXTRAS_SELECTION_REQUIRED = auto()
    EXTRAS_SELECTION_MADE = auto()

    # Warning events
    WARNING = auto()


@dataclass(frozen=True)
class Event:
    """Base event class."""

    type: EventType
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowEvent(Event):
    """Events related to workflow lifecycle."""

    profile_name: str = ""
    device_name: str = ""


@dataclass(frozen=True)
class PhaseEvent(Event):
    """Events marking phase boundaries."""

    phase_name: str = ""
    phase_number: int = 0
    total_phases: int = 0


@dataclass(frozen=True)
class DeviceEvent(Event):
    """Events related to device connection and validation."""

    serial: str = ""
    model: str = ""
    android_version: str = ""
    manufacturer: str = ""


@dataclass(frozen=True)
class PackageEvent(Event):
    """Events related to package operations."""

    package_id: str = ""
    package_name: str = ""
    reason: str = ""


@dataclass(frozen=True)
class DownloadEvent(Event):
    """Events related to APK downloads."""

    app_id: str = ""
    app_name: str = ""
    source: str = ""
    url: str = ""
    progress_bytes: int = 0
    total_bytes: int = 0
    progress_percent: float = 0.0


@dataclass(frozen=True)
class InstallEvent(Event):
    """Events related to app installation."""

    app_id: str = ""
    app_name: str = ""
    package_id: str = ""
    apk_path: str = ""


@dataclass(frozen=True)
class DefaultAppEvent(Event):
    """Events related to setting default apps."""

    app_id: str = ""
    app_name: str = ""
    role: str = ""


@dataclass(frozen=True)
class CameraChoiceEvent(Event):
    """Events related to camera choice interaction."""

    stock_camera_name: str = ""
    stock_camera_package: str = ""
    replacement_name: str = "Fossify Camera"
    user_choice: str = ""  # "stock" or "fossify"


@dataclass(frozen=True)
class ExtrasSelectionEvent(Event):
    """Events related to extras app selection."""

    available_free: list[str] = field(default_factory=list)
    available_non_free: list[str] = field(default_factory=list)
    selected_free: list[str] = field(default_factory=list)
    selected_non_free: list[str] = field(default_factory=list)
