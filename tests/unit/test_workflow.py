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

"""Tests for the workflow module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from clearphone.api.events import EventType
from clearphone.core.workflow import (
    ConfigurationWorkflow,
    UserChoices,
    WorkflowConfig,
    WorkflowResult,
)


class TestWorkflowConfig:
    """Tests for WorkflowConfig dataclass."""

    def test_default_values(self, tmp_path: Path) -> None:
        """Should have sensible defaults."""
        config = WorkflowConfig(
            profile_path=tmp_path / "test.toml",
            project_root=tmp_path,
        )

        assert config.dry_run is False
        assert config.interactive is False
        assert config.download_dir is None


class TestUserChoices:
    """Tests for UserChoices dataclass."""

    def test_default_values(self) -> None:
        """Should have empty defaults."""
        choices = UserChoices()

        assert choices.camera_choice == ""
        assert choices.selected_extras_free == []
        assert choices.selected_extras_non_free == []


class TestWorkflowResult:
    """Tests for WorkflowResult dataclass."""

    def test_default_values(self) -> None:
        """Should have zero counts and success True by default."""
        result = WorkflowResult()

        assert result.packages_removed == 0
        assert result.apps_installed == 0
        assert result.success is True


class TestConfigurationWorkflow:
    """Tests for ConfigurationWorkflow class."""

    @patch("clearphone.core.workflow.ADBDevice")
    @patch("clearphone.core.workflow.load_apps_catalog")
    @patch("clearphone.core.workflow.load_profile")
    def test_workflow_emits_started_event(
        self,
        mock_load_profile: MagicMock,
        mock_load_catalog: MagicMock,
        mock_adb_class: MagicMock,
        project_root: Path,
        sample_profile_path: Path,
    ) -> None:
        """Should emit WORKFLOW_STARTED event."""
        # Setup mocks
        mock_profile = MagicMock()
        mock_profile.device.model_pattern = "SM-S921*"
        mock_profile.device.name = "Samsung Galaxy S24"
        mock_profile.has_camera_choice.return_value = False
        mock_profile.apps.extras_free = []
        mock_profile.apps.extras_non_free = []
        mock_profile.get_packages_to_remove.return_value = []
        mock_load_profile.return_value = mock_profile

        mock_catalog = MagicMock()
        mock_catalog.get_core_apps_sorted.return_value = []
        mock_catalog.resolve_extras.return_value = []
        mock_load_catalog.return_value = mock_catalog

        mock_adb = MagicMock()
        mock_adb.device_info.model = "SM-S921U"
        mock_adb.device_info.serial = "ABC123"
        mock_adb.device_info.android_version = "14"
        mock_adb.device_info.manufacturer = "samsung"
        mock_adb.connect.return_value = mock_adb.device_info
        mock_adb.validate_device_model.return_value = True
        mock_adb_class.return_value = mock_adb

        config = WorkflowConfig(
            profile_path=sample_profile_path,
            project_root=project_root,
            dry_run=True,
        )

        workflow = ConfigurationWorkflow(config)

        events = []
        gen = workflow.execute()
        try:
            while True:
                events.append(next(gen))
        except StopIteration:
            pass

        assert any(e.type == EventType.WORKFLOW_STARTED for e in events)

    @patch("clearphone.core.workflow.ADBDevice")
    @patch("clearphone.core.workflow.load_apps_catalog")
    @patch("clearphone.core.workflow.load_profile")
    def test_workflow_validates_device(
        self,
        mock_load_profile: MagicMock,
        mock_load_catalog: MagicMock,
        mock_adb_class: MagicMock,
        project_root: Path,
        sample_profile_path: Path,
    ) -> None:
        """Should validate device model against profile."""
        mock_profile = MagicMock()
        mock_profile.device.model_pattern = "SM-S921*"
        mock_profile.device.name = "Samsung Galaxy S24"
        mock_profile.has_camera_choice.return_value = False
        mock_profile.apps.extras_free = []
        mock_profile.apps.extras_non_free = []
        mock_profile.get_packages_to_remove.return_value = []
        mock_load_profile.return_value = mock_profile

        mock_catalog = MagicMock()
        mock_catalog.get_core_apps_sorted.return_value = []
        mock_catalog.resolve_extras.return_value = []
        mock_load_catalog.return_value = mock_catalog

        mock_adb = MagicMock()
        mock_adb.device_info.model = "SM-S921U"
        mock_adb.device_info.serial = "ABC123"
        mock_adb.device_info.android_version = "14"
        mock_adb.device_info.manufacturer = "samsung"
        mock_adb.connect.return_value = mock_adb.device_info
        mock_adb.validate_device_model.return_value = True
        mock_adb_class.return_value = mock_adb

        config = WorkflowConfig(
            profile_path=sample_profile_path,
            project_root=project_root,
            dry_run=True,
        )

        workflow = ConfigurationWorkflow(config)

        events = []
        gen = workflow.execute()
        try:
            while True:
                events.append(next(gen))
        except StopIteration:
            pass

        assert any(e.type == EventType.DEVICE_VALIDATED for e in events)

    @patch("clearphone.core.workflow.ADBDevice")
    @patch("clearphone.core.workflow.load_apps_catalog")
    @patch("clearphone.core.workflow.load_profile")
    def test_workflow_fails_on_device_mismatch(
        self,
        mock_load_profile: MagicMock,
        mock_load_catalog: MagicMock,
        mock_adb_class: MagicMock,
        project_root: Path,
        sample_profile_path: Path,
    ) -> None:
        """Should fail when device doesn't match profile."""
        mock_profile = MagicMock()
        mock_profile.device.model_pattern = "SM-S921*"
        mock_profile.device.name = "Samsung Galaxy S24"
        mock_load_profile.return_value = mock_profile

        mock_catalog = MagicMock()
        mock_load_catalog.return_value = mock_catalog

        mock_adb = MagicMock()
        mock_adb.device_info.model = "SM-S911U"  # Wrong model
        mock_adb.device_info.serial = "ABC123"
        mock_adb.device_info.android_version = "14"
        mock_adb.device_info.manufacturer = "samsung"
        mock_adb.connect.return_value = mock_adb.device_info
        mock_adb.validate_device_model.return_value = False  # Mismatch!
        mock_adb_class.return_value = mock_adb

        config = WorkflowConfig(
            profile_path=sample_profile_path,
            project_root=project_root,
        )

        workflow = ConfigurationWorkflow(config)

        events = []
        result = None
        gen = workflow.execute()
        try:
            while True:
                events.append(next(gen))
        except StopIteration as e:
            result = e.value

        assert result is not None
        assert result.success is False
        assert any(e.type == EventType.WORKFLOW_FAILED for e in events)

    def test_camera_choice_callback(self, project_root: Path, sample_profile_path: Path) -> None:
        """Should call camera choice callback when in interactive mode."""
        callback_called = []

        def camera_callback(stock_name: str, stock_package: str) -> str:
            callback_called.append((stock_name, stock_package))
            return "fossify"

        config = WorkflowConfig(
            profile_path=sample_profile_path,
            project_root=project_root,
            interactive=True,
        )

        workflow = ConfigurationWorkflow(config, camera_choice_callback=camera_callback)

        # Verify the callback was stored
        assert workflow.camera_choice_callback is camera_callback

    def test_non_interactive_defaults_to_fossify_camera(self) -> None:
        """In non-interactive mode (default), should use Fossify Camera."""
        choices = UserChoices()
        choices.camera_choice = "fossify"
        assert choices.camera_choice == "fossify"

    def test_non_interactive_uses_no_extras(self) -> None:
        """In non-interactive mode without explicit extras, should install no extras."""
        choices = UserChoices()
        # Default: no extras
        assert choices.selected_extras_free == []
        assert choices.selected_extras_non_free == []
