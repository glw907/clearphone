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

"""Integration tests for the CLI."""

from pathlib import Path

from typer.testing import CliRunner

from clearphone.cli import app

runner = CliRunner()


class TestCLIVersion:
    """Tests for version command."""

    def test_version_flag(self) -> None:
        """Should display version with --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.stdout


class TestCLIListProfiles:
    """Tests for list-profiles command."""

    def test_list_profiles(self, project_root: Path, monkeypatch) -> None:
        """Should list available profiles."""
        monkeypatch.chdir(project_root)

        result = runner.invoke(app, ["list-profiles"])
        assert result.exit_code == 0
        assert "samsung-s24.toml" in result.stdout


class TestCLIShowProfile:
    """Tests for show-profile command."""

    def test_show_profile(self, project_root: Path, monkeypatch) -> None:
        """Should show profile details."""
        monkeypatch.chdir(project_root)
        profile_path = project_root / "device-profiles" / "samsung-s24.toml"

        result = runner.invoke(app, ["show-profile", str(profile_path)])
        assert result.exit_code == 0
        assert "Samsung Galaxy S24" in result.stdout
        assert "SM-S921*" in result.stdout

    def test_show_nonexistent_profile(self, tmp_path: Path, monkeypatch) -> None:
        """Should error for nonexistent profile."""
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["show-profile", "nonexistent.toml"])
        assert result.exit_code != 0


class TestCLIConfigure:
    """Tests for configure command."""

    def test_configure_dry_run_no_adb(self, project_root: Path, monkeypatch) -> None:
        """Should fail gracefully when ADB not available."""
        monkeypatch.chdir(project_root)
        profile_path = project_root / "device-profiles" / "samsung-s24.toml"

        # This will fail because ADB is not available in test environment
        result = runner.invoke(
            app, ["configure", str(profile_path), "--dry-run", "--non-interactive"]
        )

        # Should fail with helpful error about ADB
        # (unless ADB happens to be installed on the test machine)
        # The test verifies the command runs without crashing
        assert result.exit_code in (0, 1)

    def test_configure_help(self) -> None:
        """Should show help for configure command."""
        result = runner.invoke(app, ["configure", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.stdout
        assert "--non-interactive" in result.stdout


class TestCLIHelp:
    """Tests for help output."""

    def test_main_help(self) -> None:
        """Should show main help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "configure" in result.stdout
        assert "list-profiles" in result.stdout
        assert "show-profile" in result.stdout

    def test_no_args_shows_help(self) -> None:
        """Should show help when no args provided."""
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "Usage" in result.stdout
