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

"""APK download functionality for F-Droid and direct sources.

Handles:
- F-Droid index fetching and parsing
- APK download with progress tracking
- SHA256 verification for F-Droid packages
"""

import hashlib
import json
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from clearphone.api.events import DownloadEvent, Event, EventType
from clearphone.core.apps_catalog import AppDefinition
from clearphone.core.exceptions import (
    ChecksumError,
    DownloadError,
    FDroidIndexError,
    NetworkError,
)

FDROID_REPO_URL = "https://f-droid.org/repo"
FDROID_INDEX_URL = f"{FDROID_REPO_URL}/index-v2.json"
CHUNK_SIZE = 8192


@dataclass
class FDroidPackageInfo:
    """Information about a package from F-Droid index."""

    package_name: str
    version_name: str
    version_code: int
    apk_name: str
    sha256: str
    size: int

    @property
    def download_url(self) -> str:
        """Get the full download URL for this package."""
        return f"{FDROID_REPO_URL}/{self.apk_name}"


class FDroidIndex:
    """F-Droid repository index handler."""

    def __init__(self) -> None:
        """Initialize the F-Droid index."""
        self._index: dict[str, Any] | None = None
        self._packages: dict[str, FDroidPackageInfo] = {}

    def fetch(self, client: httpx.Client) -> None:
        """Fetch and parse the F-Droid index.

        Args:
            client: HTTP client to use for the request

        Raises:
            FDroidIndexError: If fetch or parse fails
        """
        try:
            response = client.get(FDROID_INDEX_URL, timeout=60.0)
            response.raise_for_status()
            self._index = response.json()
        except httpx.HTTPError as e:
            raise FDroidIndexError(f"Failed to fetch index: {e}") from e
        except json.JSONDecodeError as e:
            raise FDroidIndexError(f"Invalid index JSON: {e}") from e

        self._parse_index()

    def _parse_index(self) -> None:
        """Parse the fetched index into package info."""
        if self._index is None:
            return

        packages_data = self._index.get("packages", {})

        for package_name, package_info in packages_data.items():
            versions = package_info.get("versions", {})
            if not versions:
                continue

            # Get the latest version (highest version code)
            latest_version_key = max(
                versions.keys(),
                key=lambda k: versions[k].get("manifest", {}).get("versionCode", 0),
            )
            latest = versions[latest_version_key]
            manifest = latest.get("manifest", {})
            file_info = latest.get("file", {})

            if not file_info:
                continue

            apk_name = file_info.get("name", "")
            sha256 = file_info.get("sha256", "")

            # Handle both list and single value formats
            sha256_value = sha256[0] if isinstance(sha256, list) else sha256

            self._packages[package_name] = FDroidPackageInfo(
                package_name=package_name,
                version_name=manifest.get("versionName", ""),
                version_code=manifest.get("versionCode", 0),
                apk_name=apk_name.lstrip("/"),
                sha256=sha256_value,
                size=file_info.get("size", 0),
            )

    def get_package_info(self, package_name: str) -> FDroidPackageInfo | None:
        """Get package info by package name.

        Args:
            package_name: The F-Droid package name

        Returns:
            FDroidPackageInfo or None if not found
        """
        return self._packages.get(package_name)

    def get_download_url(self, package_name: str) -> str | None:
        """Get the download URL for a package.

        Args:
            package_name: The F-Droid package name

        Returns:
            Download URL or None if package not found
        """
        info = self.get_package_info(package_name)
        return info.download_url if info else None


class APKDownloader:
    """Handles downloading APKs from F-Droid and direct sources."""

    def __init__(self, download_dir: Path) -> None:
        """Initialize the downloader.

        Args:
            download_dir: Directory to store downloaded APKs
        """
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self._client: httpx.Client | None = None
        self._fdroid_index: FDroidIndex | None = None

    def __enter__(self) -> "APKDownloader":
        """Enter context manager."""
        self._client = httpx.Client(
            follow_redirects=True,
            timeout=httpx.Timeout(30.0, connect=10.0),
        )
        return self

    def __exit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> None:
        """Exit context manager."""
        if self._client:
            self._client.close()
            self._client = None

    def _ensure_client(self) -> httpx.Client:
        """Ensure HTTP client is available.

        Returns:
            The HTTP client

        Raises:
            RuntimeError: If not in context manager
        """
        if self._client is None:
            raise RuntimeError("APKDownloader must be used as a context manager")
        return self._client

    def _ensure_fdroid_index(self) -> FDroidIndex:
        """Ensure F-Droid index is loaded.

        Returns:
            The F-Droid index

        Raises:
            FDroidIndexError: If index fetch fails
        """
        if self._fdroid_index is None:
            self._fdroid_index = FDroidIndex()
            self._fdroid_index.fetch(self._ensure_client())
        return self._fdroid_index

    def download_app(self, app: AppDefinition) -> Generator[Event, None, Path | None]:
        """Download an APK for an app.

        Args:
            app: The app definition to download

        Yields:
            Download progress events

        Returns:
            Path to downloaded APK or None if failed
        """
        yield DownloadEvent(
            type=EventType.DOWNLOAD_STARTED,
            message=f"Starting download: {app.name}",
            app_id=app.id,
            app_name=app.name,
            source=app.source,
        )

        try:
            if app.source == "fdroid":
                result = yield from self._download_fdroid(app)
            else:
                result = yield from self._download_direct(app)

            if result:
                yield DownloadEvent(
                    type=EventType.DOWNLOAD_COMPLETED,
                    message=f"Downloaded: {app.name}",
                    app_id=app.id,
                    app_name=app.name,
                    source=app.source,
                )
            return result

        except (DownloadError, NetworkError, ChecksumError) as e:
            yield DownloadEvent(
                type=EventType.DOWNLOAD_FAILED,
                message=str(e),
                app_id=app.id,
                app_name=app.name,
                source=app.source,
            )
            return None

    def _download_fdroid(self, app: AppDefinition) -> Generator[Event, None, Path | None]:
        """Download an app from F-Droid.

        Args:
            app: App definition with fdroid_package_name

        Yields:
            Download progress events

        Returns:
            Path to downloaded APK or None
        """
        if not app.fdroid_package_name:
            raise DownloadError(app.name, "N/A", "No F-Droid package name specified")

        index = self._ensure_fdroid_index()
        pkg_info = index.get_package_info(app.fdroid_package_name)

        if not pkg_info:
            raise DownloadError(
                app.name,
                FDROID_INDEX_URL,
                f"Package '{app.fdroid_package_name}' not found in F-Droid index",
            )

        url = pkg_info.download_url
        dest = self.download_dir / f"{app.id}.apk"

        yield from self._download_file(app, url, dest, pkg_info.size)

        # Verify checksum
        if pkg_info.sha256:
            actual_hash = self._calculate_sha256(dest)
            if actual_hash.lower() != pkg_info.sha256.lower():
                dest.unlink(missing_ok=True)
                raise ChecksumError(app.name, pkg_info.sha256, actual_hash)

        return dest

    def _download_direct(self, app: AppDefinition) -> Generator[Event, None, Path | None]:
        """Download an app from a direct URL.

        Args:
            app: App definition with download_url

        Yields:
            Download progress events

        Returns:
            Path to downloaded APK or None
        """
        if not app.download_url:
            raise DownloadError(app.name, "N/A", "No download URL specified")

        dest = self.download_dir / f"{app.id}.apk"

        # For direct downloads, we don't know the size upfront
        yield from self._download_file(app, app.download_url, dest, 0)

        return dest

    def _download_file(
        self, app: AppDefinition, url: str, dest: Path, expected_size: int
    ) -> Generator[Event, None, None]:
        """Download a file with progress tracking.

        Args:
            app: App being downloaded
            url: URL to download from
            dest: Destination path
            expected_size: Expected file size (0 if unknown)

        Yields:
            Download progress events
        """
        client = self._ensure_client()

        try:
            with client.stream("GET", url) as response:
                response.raise_for_status()

                total_size = int(response.headers.get("content-length", expected_size))
                downloaded = 0

                with open(dest, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=CHUNK_SIZE):
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            yield DownloadEvent(
                                type=EventType.DOWNLOAD_PROGRESS,
                                message=f"Downloading {app.name}: {progress:.1f}%",
                                app_id=app.id,
                                app_name=app.name,
                                source=app.source,
                                url=url,
                                progress_bytes=downloaded,
                                total_bytes=total_size,
                                progress_percent=progress,
                            )

        except httpx.HTTPError as e:
            dest.unlink(missing_ok=True)
            raise DownloadError(app.name, url, str(e)) from e

    def _calculate_sha256(self, path: Path) -> str:
        """Calculate SHA256 hash of a file.

        Args:
            path: Path to the file

        Returns:
            Hex-encoded SHA256 hash
        """
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
