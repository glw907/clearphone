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

"""Core modules for Clearphone."""

from clearphone.core.adb import ADBDevice, ADBResult, check_adb_available
from clearphone.core.apps_catalog import AppDefinition, AppsCatalog, load_apps_catalog
from clearphone.core.downloader import APKDownloader, FDroidIndex
from clearphone.core.exceptions import (
    ADBError,
    ClearphoneError,
    CriticalConfigurationError,
    DownloadError,
    ProfileNotFoundError,
    ProfileParseError,
    ValidationError,
)
from clearphone.core.installer import AppInstaller
from clearphone.core.profile import DeviceProfile, PackageToRemove, load_profile
from clearphone.core.remover import PackageRemover
from clearphone.core.workflow import ConfigurationWorkflow, WorkflowConfig, WorkflowResult

__all__ = [
    # ADB
    "ADBDevice",
    "ADBResult",
    "check_adb_available",
    # Apps catalog
    "AppDefinition",
    "AppsCatalog",
    "load_apps_catalog",
    # Downloader
    "APKDownloader",
    "FDroidIndex",
    # Exceptions
    "ADBError",
    "ClearphoneError",
    "CriticalConfigurationError",
    "DownloadError",
    "ProfileNotFoundError",
    "ProfileParseError",
    "ValidationError",
    # Installer
    "AppInstaller",
    # Profile
    "DeviceProfile",
    "PackageToRemove",
    "load_profile",
    # Remover
    "PackageRemover",
    # Workflow
    "ConfigurationWorkflow",
    "WorkflowConfig",
    "WorkflowResult",
]
