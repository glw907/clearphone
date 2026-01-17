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

"""Tests for the downloader module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from clearphone.api.events import EventType
from clearphone.core.apps_catalog import AppDefinition
from clearphone.core.downloader import (
    APKDownloader,
    FDroidIndex,
    FDroidPackageInfo,
)
from clearphone.core.exceptions import FDroidIndexError


class TestFDroidPackageInfo:
    """Tests for FDroidPackageInfo dataclass."""

    def test_download_url_property(self) -> None:
        """Should generate correct download URL."""
        info = FDroidPackageInfo(
            package_name="app.olauncher",
            version_name="1.0.0",
            version_code=100,
            apk_name="app.olauncher_100.apk",
            sha256="abc123",
            size=1000000,
        )

        assert "f-droid.org/repo" in info.download_url
        assert "app.olauncher_100.apk" in info.download_url


class TestFDroidIndex:
    """Tests for FDroidIndex class."""

    def test_get_package_info_not_fetched(self) -> None:
        """Should return None when index not fetched."""
        index = FDroidIndex()
        assert index.get_package_info("app.olauncher") is None

    def test_get_download_url_not_fetched(self) -> None:
        """Should return None when index not fetched."""
        index = FDroidIndex()
        assert index.get_download_url("app.olauncher") is None

    @patch("httpx.Client")
    def test_fetch_index_success(self, mock_client_class: MagicMock) -> None:
        """Should parse F-Droid index successfully."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "packages": {
                "app.olauncher": {
                    "versions": {
                        "v1": {
                            "manifest": {
                                "versionName": "1.0.0",
                                "versionCode": 100,
                            },
                            "file": {
                                "name": "/app.olauncher_100.apk",
                                "sha256": "abc123def456",
                                "size": 5000000,
                            },
                        }
                    }
                }
            }
        }
        mock_client.get.return_value = mock_response

        index = FDroidIndex()
        index.fetch(mock_client)

        info = index.get_package_info("app.olauncher")
        assert info is not None
        assert info.version_name == "1.0.0"
        assert info.sha256 == "abc123def456"

    @patch("httpx.Client")
    def test_fetch_index_http_error(self, mock_client_class: MagicMock) -> None:
        """Should raise FDroidIndexError on HTTP error."""
        import httpx

        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.HTTPError("Connection failed")

        index = FDroidIndex()
        with pytest.raises(FDroidIndexError):
            index.fetch(mock_client)


class TestAPKDownloader:
    """Tests for APKDownloader class."""

    def test_context_manager(self, tmp_path: Path) -> None:
        """Should work as context manager."""
        with APKDownloader(tmp_path) as downloader:
            assert downloader._client is not None

        # Client should be closed after context
        assert downloader._client is None

    def test_download_dir_created(self, tmp_path: Path) -> None:
        """Should create download directory."""
        download_dir = tmp_path / "downloads"
        with APKDownloader(download_dir):
            assert download_dir.exists()

    def test_ensure_client_outside_context(self, tmp_path: Path) -> None:
        """Should raise error when not in context manager."""
        downloader = APKDownloader(tmp_path)
        with pytest.raises(RuntimeError):
            downloader._ensure_client()

    @patch.object(APKDownloader, "_ensure_fdroid_index")
    @patch.object(APKDownloader, "_download_file")
    def test_download_fdroid_app(
        self,
        mock_download_file: MagicMock,
        mock_ensure_index: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should download F-Droid app."""
        mock_index = MagicMock()
        mock_index.get_package_info.return_value = FDroidPackageInfo(
            package_name="app.olauncher",
            version_name="1.0.0",
            version_code=100,
            apk_name="app.olauncher_100.apk",
            sha256="abc123",
            size=1000000,
        )
        mock_ensure_index.return_value = mock_index

        # Mock download to yield nothing and complete
        def mock_download(*args, **kwargs):
            return
            yield  # Make it a generator

        mock_download_file.return_value = iter([])

        app = AppDefinition(
            id="launcher",
            package_id="app.olauncher",
            name="Olauncher",
            source="fdroid",
            fdroid_package_name="app.olauncher",
        )

        with (
            APKDownloader(tmp_path) as downloader,
            patch.object(downloader, "_calculate_sha256", return_value="abc123"),
        ):
            events = list(downloader.download_app(app))

        # Should have download started event
        assert any(e.type == EventType.DOWNLOAD_STARTED for e in events)

    def test_download_app_no_fdroid_package(self, tmp_path: Path) -> None:
        """Should fail for F-Droid app without package name."""
        app = AppDefinition(
            id="launcher",
            package_id="app.olauncher",
            name="Olauncher",
            source="fdroid",
            fdroid_package_name=None,
        )

        with (
            APKDownloader(tmp_path) as downloader,
            patch.object(downloader, "_ensure_fdroid_index"),
        ):
            events = list(downloader.download_app(app))

        assert any(e.type == EventType.DOWNLOAD_FAILED for e in events)

    def test_download_direct_app_no_url(self, tmp_path: Path) -> None:
        """Should fail for direct app without URL."""
        app = AppDefinition(
            id="whatsapp",
            package_id="com.whatsapp",
            name="WhatsApp",
            source="direct",
            download_url=None,
        )

        with APKDownloader(tmp_path) as downloader:
            events = list(downloader.download_app(app))

        assert any(e.type == EventType.DOWNLOAD_FAILED for e in events)

    def test_calculate_sha256(self, tmp_path: Path) -> None:
        """Should calculate correct SHA256 hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test content")

        with APKDownloader(tmp_path) as downloader:
            hash_value = downloader._calculate_sha256(test_file)

        # Known SHA256 for "test content"
        assert hash_value == "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
