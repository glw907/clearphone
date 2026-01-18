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

"""Pytest configuration and fixtures for Clearphone tests."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_profile_path(project_root: Path) -> Path:
    """Get path to the sample Samsung S24 profile."""
    return project_root / "device-profiles" / "samsung-s24.toml"


@pytest.fixture
def apps_dir(project_root: Path) -> Path:
    """Get path to the apps catalog directory."""
    return project_root / "apps"


@pytest.fixture
def mock_adb_device() -> MagicMock:
    """Create a mock ADB device."""
    mock = MagicMock()
    mock.serial = "MOCK123456"
    mock.device_info = MagicMock()
    mock.device_info.serial = "MOCK123456"
    mock.device_info.model = "SM-S921U"
    mock.device_info.android_version = "14"
    mock.device_info.manufacturer = "samsung"

    mock.connect.return_value = mock.device_info
    mock.validate_device_model.return_value = True
    mock.list_packages.return_value = [
        "com.samsung.android.bixby.agent",
        "com.samsung.android.samsungpass",
        "com.facebook.katana",
    ]
    mock.is_package_installed.return_value = True
    mock.uninstall_package.return_value = MagicMock(success=True, stdout="Success", stderr="")
    mock.install_apk.return_value = MagicMock(success=True, stdout="Success", stderr="")
    mock.set_default_launcher.return_value = MagicMock(success=True, stderr="")
    mock.set_default_dialer.return_value = MagicMock(success=True, stderr="")
    mock.set_default_sms.return_value = MagicMock(success=True, stderr="")
    mock.set_default_keyboard.return_value = MagicMock(success=True, stderr="")
    mock.set_default_gallery.return_value = MagicMock(success=True, stderr="")
    mock.close.return_value = None

    return mock


@pytest.fixture
def sample_core_toml() -> str:
    """Sample core.toml content for testing."""
    return """
[launcher]
id = "launcher"
package_id = "app.olauncher"
name = "Olauncher"
source = "fdroid"
fdroid_package_name = "app.olauncher"
installation_priority = 1

[keyboard]
id = "keyboard"
package_id = "org.futo.inputmethod.latin"
name = "FUTO Keyboard"
source = "fdroid"
fdroid_package_name = "org.futo.inputmethod.latin"
installation_priority = 5
"""


@pytest.fixture
def sample_extras_free_toml() -> str:
    """Sample extras/free.toml content for testing."""
    return """
[camera]
id = "camera"
package_id = "com.simplemobiletools.camera"
name = "Fossify Camera"
description = "Simple camera app"
source = "fdroid"
fdroid_package_name = "com.simplemobiletools.camera"

[weather]
id = "weather"
package_id = "org.breezyweather"
name = "Breezy Weather"
description = "Weather app"
source = "fdroid"
fdroid_package_name = "org.breezyweather"
"""


@pytest.fixture
def sample_profile_toml() -> str:
    """Sample device profile content for testing."""
    return """
[device]
model_pattern = "SM-S921*"
name = "Samsung Galaxy S24"
android_version = "14"
maintainer = "test"

[apps]
extras_free = ["weather"]
extras_non_free = []

[[packages]]
id = "com.samsung.android.bixby.agent"
name = "Bixby Voice"
source = "Samsung"
function = "Voice assistant"
category = "vendor"
action = "remove"
removal_rationale = "Replaced by user's preferred apps"

[[packages]]
id = "com.sec.android.app.camera"
name = "Samsung Camera"
source = "Samsung"
function = "Camera"
category = "system"
action = "remove"
conditional = "camera"
removal_rationale = "Conditionally removed"
"""
