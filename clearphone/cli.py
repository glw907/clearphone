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

"""Command-line interface for Clearphone.

Provides commands for:
- configure: Run configuration on a device
- list-profiles: Show available device profiles
- show-profile: Display profile details
"""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.prompt import Confirm, Prompt
from rich.table import Table

from clearphone import __version__
from clearphone.api.controller import ConfigurationController
from clearphone.api.events import (
    CameraChoiceEvent,
    DefaultAppEvent,
    DownloadEvent,
    Event,
    EventType,
    ExtrasSelectionEvent,
    InstallEvent,
    PackageEvent,
    PhaseEvent,
    WorkflowEvent,
)
from clearphone.core.apps_catalog import AppDefinition
from clearphone.core.exceptions import ClearphoneError
from clearphone.core.workflow import WorkflowResult

app = typer.Typer(
    name="clearphone",
    help="Configure Android phones for minimal distraction.",
)

console = Console()
err_console = Console(stderr=True)


def get_project_root() -> Path:
    """Get the project root directory."""
    # Look for pyproject.toml to identify project root
    current = Path.cwd()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()


class CLIEventHandler:
    """Handles events from the workflow and displays them via Rich."""

    def __init__(self, console: Console) -> None:
        """Initialize the event handler.

        Args:
            console: Rich console for output
        """
        self.console = console
        self._current_phase: str = ""
        self._download_progress: Progress | None = None

    def handle(self, event: Event) -> None:
        """Handle an event and display appropriate output.

        Args:
            event: The event to handle
        """
        if isinstance(event, PhaseEvent):
            self._handle_phase(event)
        elif isinstance(event, WorkflowEvent):
            self._handle_workflow(event)
        elif isinstance(event, PackageEvent):
            self._handle_package(event)
        elif isinstance(event, DownloadEvent):
            self._handle_download(event)
        elif isinstance(event, InstallEvent):
            self._handle_install(event)
        elif isinstance(event, DefaultAppEvent):
            self._handle_default_app(event)

    def _handle_phase(self, event: PhaseEvent) -> None:
        """Handle phase events."""
        if event.type == EventType.PHASE_STARTED:
            self._current_phase = event.phase_name
            self.console.print(
                f"\n[bold blue]Phase {event.phase_number}/{event.total_phases}:[/] "
                f"{event.phase_name}"
            )

    def _handle_workflow(self, event: WorkflowEvent) -> None:
        """Handle workflow events."""
        if event.type == EventType.WORKFLOW_STARTED:
            self.console.print(
                Panel(
                    f"[bold]Configuring device with profile:[/]\n{event.profile_name}",
                    title="Clearphone",
                    border_style="blue",
                )
            )
        elif event.type == EventType.WORKFLOW_COMPLETED:
            self.console.print("\n[bold green]Configuration completed successfully.[/]")
        elif event.type == EventType.WORKFLOW_FAILED:
            self.console.print(f"\n[bold red]Configuration failed:[/] {event.message}")

    def _handle_package(self, event: PackageEvent) -> None:
        """Handle package events."""
        if event.type == EventType.PACKAGE_REMOVED:
            self.console.print(f"  [green]✓[/] Removed: {event.package_name}")
        elif event.type == EventType.PACKAGE_NOT_INSTALLED:
            self.console.print(f"  [dim]○[/] Not installed: {event.package_name}")
        elif event.type == EventType.PACKAGE_REMOVAL_SKIPPED:
            self.console.print(f"  [yellow]⊘[/] Skipped: {event.package_name} ({event.reason})")
        elif event.type == EventType.PACKAGE_REMOVAL_FAILED:
            self.console.print(f"  [red]✗[/] Failed: {event.package_name} ({event.reason})")

    def _handle_download(self, event: DownloadEvent) -> None:
        """Handle download events."""
        if event.type == EventType.DOWNLOAD_STARTED:
            self.console.print(f"  [cyan]↓[/] Downloading: {event.app_name}")
        elif event.type == EventType.DOWNLOAD_COMPLETED:
            self.console.print(f"  [green]✓[/] Downloaded: {event.app_name}")
        elif event.type == EventType.DOWNLOAD_FAILED:
            self.console.print(f"  [red]✗[/] Download failed: {event.app_name}")

    def _handle_install(self, event: InstallEvent) -> None:
        """Handle install events."""
        if event.type == EventType.INSTALL_STARTED:
            self.console.print(f"  [cyan]→[/] Installing: {event.app_name}")
        elif event.type == EventType.INSTALL_COMPLETED:
            self.console.print(f"  [green]✓[/] Installed: {event.app_name}")
        elif event.type == EventType.INSTALL_FAILED:
            self.console.print(f"  [red]✗[/] Install failed: {event.app_name}")

    def _handle_default_app(self, event: DefaultAppEvent) -> None:
        """Handle default app events."""
        if event.type == EventType.DEFAULT_APP_SET:
            self.console.print(f"  [green]✓[/] Set default {event.role}: {event.app_name}")
        elif event.type == EventType.DEFAULT_APP_FAILED:
            self.console.print(
                f"  [yellow]⚠[/] Could not set default {event.role}: {event.app_name}"
            )


def camera_choice_prompt(stock_name: str, stock_package: str) -> str:
    """Prompt user for camera choice.

    Args:
        stock_name: Name of the stock camera app
        stock_package: Package ID of the stock camera

    Returns:
        "stock" or "fossify"
    """
    console.print("\n[bold]Camera Choice[/]")
    console.print(
        f"\nYou can keep the [cyan]{stock_name}[/] or replace it with [cyan]Fossify Camera[/].\n"
    )

    table = Table(show_header=True, header_style="bold")
    table.add_column("Option", style="cyan")
    table.add_column("Pros")
    table.add_column("Cons")

    table.add_row(
        f"1. Keep {stock_name}",
        "Better photo quality (HDR, night mode, etc.)",
        "Gallery links broken after removing Samsung Gallery",
    )
    table.add_row(
        "2. Fossify Camera",
        "Simpler, works well with Fossify Gallery",
        "Lower photo quality (no advanced processing)",
    )

    console.print(table)

    choice = Prompt.ask(
        "\nWhich camera do you want",
        choices=["1", "2"],
        default="1",
    )

    return "stock" if choice == "1" else "fossify"


def extras_choice_prompt(
    free_apps: list[AppDefinition], non_free_apps: list[AppDefinition]
) -> tuple[list[str], list[str]]:
    """Prompt user for extras selection.

    Args:
        free_apps: Available free extra apps
        non_free_apps: Available non-free extra apps

    Returns:
        Tuple of (selected_free_ids, selected_non_free_ids)
    """
    selected_free: list[str] = []
    selected_non_free: list[str] = []

    if free_apps:
        console.print("\n[bold]Open Source Apps[/] (from F-Droid)")
        console.print("Select which apps to install:\n")

        for app in free_apps:
            description = app.description or "No description"
            if Confirm.ask(
                f"  [cyan]{app.name}[/] - {description}",
                default=True,
            ):
                selected_free.append(app.id)

    if non_free_apps:
        console.print("\n[bold]Proprietary Apps[/] (direct download)")
        console.print("Select which apps to install:\n")

        for app in non_free_apps:
            description = app.description or "No description"
            if Confirm.ask(
                f"  [cyan]{app.name}[/] - {description}",
                default=False,
            ):
                selected_non_free.append(app.id)

    return selected_free, selected_non_free


def print_summary(result: WorkflowResult) -> None:
    """Print a summary of the configuration results.

    Args:
        result: The workflow result
    """
    console.print("\n[bold]Summary[/]")

    table = Table(show_header=False, box=None)
    table.add_column("Category", style="bold")
    table.add_column("Count", justify="right")

    table.add_row("Packages removed", f"[green]{result.packages_removed}[/]")
    table.add_row("Packages skipped", f"[yellow]{result.packages_skipped}[/]")
    table.add_row("Packages failed", f"[red]{result.packages_failed}[/]")
    table.add_row("Apps installed", f"[green]{result.apps_installed}[/]")
    table.add_row("Apps failed", f"[red]{result.apps_failed}[/]")

    console.print(table)


@app.command()
def configure(
    profile: Annotated[
        Path,
        typer.Argument(
            help="Path to the device profile TOML file",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Show what would be done without making changes",
        ),
    ] = False,
    non_interactive: Annotated[
        bool,
        typer.Option(
            "--non-interactive",
            "-y",
            help="Use defaults without prompting",
        ),
    ] = False,
    download_dir: Annotated[
        Path | None,
        typer.Option(
            "--download-dir",
            "-d",
            help="Directory for downloaded APKs",
        ),
    ] = None,
) -> None:
    """Configure a connected Android device using a profile."""
    project_root = get_project_root()
    controller = ConfigurationController(project_root)

    # Check prerequisites
    errors = controller.check_prerequisites()
    if errors:
        for error in errors:
            err_console.print(f"[red]Error:[/] {error}")
        raise typer.Exit(1)

    if dry_run:
        console.print("[yellow]Dry run mode - no changes will be made[/]\n")

    # Set up callbacks for interactive mode
    camera_callback = None if non_interactive else camera_choice_prompt
    extras_callback = None if non_interactive else extras_choice_prompt

    # Create event handler
    handler = CLIEventHandler(console)

    try:
        # Run configuration
        gen = controller.configure(
            profile_path=profile,
            dry_run=dry_run,
            non_interactive=non_interactive,
            download_dir=download_dir,
            camera_choice_callback=camera_callback,
            extras_choice_callback=extras_callback,
        )

        result: WorkflowResult | None = None
        try:
            while True:
                event = next(gen)

                # Handle camera and extras selection events specially
                if isinstance(event, CameraChoiceEvent):
                    if event.type == EventType.CAMERA_CHOICE_REQUIRED and not non_interactive:
                        continue  # Callback handles this
                    elif event.type == EventType.CAMERA_CHOICE_MADE:
                        choice_display = (
                            "Keep stock camera"
                            if event.user_choice == "stock"
                            else "Use Fossify Camera"
                        )
                        console.print(f"  [cyan]→[/] Camera choice: {choice_display}")
                elif isinstance(event, ExtrasSelectionEvent):
                    if event.type == EventType.EXTRAS_SELECTION_REQUIRED and not non_interactive:
                        continue  # Callback handles this
                    elif event.type == EventType.EXTRAS_SELECTION_MADE:
                        total = len(event.selected_free) + len(event.selected_non_free)
                        console.print(f"  [cyan]→[/] Selected {total} extra apps")
                else:
                    handler.handle(event)

        except StopIteration as e:
            result = e.value

        if result:
            print_summary(result)

            if not result.success:
                raise typer.Exit(1)

    except ClearphoneError as e:
        err_console.print(f"\n[red]Error:[/] {e.message}")
        if e.suggestion:
            err_console.print(f"\n{e.suggestion}")
        raise typer.Exit(1) from None


@app.command("list-profiles")
def list_profiles() -> None:
    """List available device profiles."""
    project_root = get_project_root()
    controller = ConfigurationController(project_root)

    profiles = controller.list_profiles()

    if not profiles:
        console.print("No device profiles found.")
        console.print(f"Create profiles in: {project_root / 'device-profiles'}")
        return

    table = Table(title="Available Device Profiles")
    table.add_column("Profile", style="cyan")
    table.add_column("Device")
    table.add_column("Packages")

    for profile_path in profiles:
        try:
            summary = controller.get_profile_summary(profile_path)
            table.add_row(
                profile_path.name,
                str(summary["name"]),
                str(summary["package_count"]),
            )
        except ClearphoneError as e:
            table.add_row(
                profile_path.name,
                f"[red]Error: {e.message}[/]",
                "-",
            )

    console.print(table)


@app.command("show-profile")
def show_profile(
    profile: Annotated[
        Path,
        typer.Argument(
            help="Path to the device profile TOML file",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ],
) -> None:
    """Show details of a device profile."""
    project_root = get_project_root()
    controller = ConfigurationController(project_root)

    try:
        summary = controller.get_profile_summary(profile)

        console.print(f"\n[bold]Device Profile:[/] {profile.name}\n")

        # Device info
        info_table = Table(show_header=False, box=None)
        info_table.add_column("Property", style="bold")
        info_table.add_column("Value")

        info_table.add_row("Device", str(summary["name"]))
        info_table.add_row("Model Pattern", str(summary["model_pattern"]))
        info_table.add_row("Android Version", str(summary["android_version"]))
        info_table.add_row("Maintainer", str(summary["maintainer"]))
        info_table.add_row(
            "Camera Choice",
            "[green]Yes[/]" if summary["has_camera_choice"] else "[dim]No[/]",
        )

        console.print(info_table)

        # Package removal count
        console.print(f"\n[bold]Packages to Remove:[/] {summary['package_count']}")

        # Extras
        extras_free = summary.get("extras_free", [])
        extras_non_free = summary.get("extras_non_free", [])

        if extras_free and isinstance(extras_free, list):
            console.print(f"\n[bold]Free Extras:[/] {', '.join(str(x) for x in extras_free)}")
        if extras_non_free and isinstance(extras_non_free, list):
            console.print(f"[bold]Non-Free Extras:[/] {', '.join(str(x) for x in extras_non_free)}")

    except ClearphoneError as e:
        err_console.print(f"[red]Error:[/] {e.message}")
        if e.suggestion:
            err_console.print(f"\n{e.suggestion}")
        raise typer.Exit(1) from None


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit",
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Clearphone - Configure Android phones for minimal distraction."""
    if version:
        console.print(f"clearphone {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


if __name__ == "__main__":
    app()
