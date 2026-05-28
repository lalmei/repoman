"""Version and debugging utilities.

Version management and debug information utilities for the package.

"""

from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING

from rich.box import HEAVY_EDGE, Box
from rich.columns import Columns
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from repoman.utils.paths import get_os_config_path
from repoman.utils.ui import get_console

if TYPE_CHECKING:
    from rich.console import Console, RenderableType


def section(title: str, renderable: RenderableType, style: str = "blue", box: Box = HEAVY_EDGE) -> Panel:
    return Panel(
        renderable,
        title=f"[bold {style}]{title}[/]",
        border_style=style,
        box=box,
        padding=(1, 2),
    )


@dataclass
class Variable:
    """Dataclass describing an environment variable."""

    name: str
    """Variable name."""
    value: str
    """Variable value."""


@dataclass
class Package:
    """Dataclass describing a Python package."""

    name: str
    """Package name."""
    version: str
    """Package version."""

    def __repr__(self) -> str:
        return f"{self.name} : {self.version}\n"

    # def __str__(self) -> str:
    #     return f"{self.name} : {self.version}"


@dataclass
class Environment:
    """Dataclass to store environment information."""

    interpreter_name: str
    """Python interpreter name."""
    interpreter_version: str
    """Python interpreter version."""
    interpreter_path: str
    """Path to Python executable."""
    platform: str
    """Operating System."""
    packages: list[Package]
    """Installed packages."""
    variables: list[Variable]
    """Environment variables."""
    platform_version: str = ""
    """Operating System version."""


def _interpreter_name_version() -> tuple[str, str]:
    if hasattr(sys, "implementation"):
        impl = sys.implementation.version
        version = f"{impl.major}.{impl.minor}.{impl.micro}"
        kind = impl.releaselevel
        if kind != "final":
            version += kind[0] + str(impl.serial)
        return sys.implementation.name, version
    return "", "0.0.0"


def get_version(dist: str = "repoman") -> str:
    """Get version of the given distribution.

    Parameters:
        dist: A distribution name.

    Returns:
        A version number.
    """
    if not dist:
        raise ValueError("Distribution name cannot be empty or None")
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return "0.0.0"


def version_info() -> Text:
    """Get version information.

    Returns:
        Version information.
    """
    version = get_version()
    return Text.assemble(("repoman: ", "peach"), (f"{version}", "bold"))


def get_debug_info() -> Environment:
    """Get debug/environment information.

    Returns:
        Environment information.
    """
    py_name, py_version = _interpreter_name_version()
    repoman_prefix = "REPOMAN"

    # Get all installed packages with their dependencies
    try:
        package_data = []
        for dist in metadata.distributions():
            name = dist.metadata.get("Name")
            if name is None:
                continue

            version = dist.metadata.get("Version", "unknown")

            package_data.append((name, version))

        package_data.sort(key=lambda x: x[0])
        packages = package_data
    except (metadata.PackageNotFoundError, KeyError, AttributeError):
        # Fallback to just repoman if there's an error
        packages = [("repoman", get_version("repoman"))]

    variables = [
        "PYTHONPATH",
        *[var for var in os.environ if var.upper().startswith(repoman_prefix)],
    ]

    return Environment(
        interpreter_name=py_name,
        interpreter_version=py_version,
        interpreter_path=sys.executable,
        platform=platform.platform(),
        platform_version=platform.version(),
        variables=[Variable(var, val) for var in variables if (val := os.getenv(var))],
        packages=[Package(name, version) for name, version in packages],
    )


def working_paths() -> list[Path]:
    """Get the working paths for the project.

    Returns:
        A list of Path objects. Starting with the config path and ending with the working directory.
    """
    config_path = get_os_config_path()
    working_dir = Path.cwd()
    return [config_path, working_dir]


def package_inventory(packages: list[Package]) -> Panel:
    """Build a Columns object for the package inventory, as tightly packed as possible.

    Args:
        packages: A list of Package objects.

    Returns:
        A Columns object.
    """
    items = [
        Text.assemble(
            (pkg.name, "bold"),
            (" ", "dim"),
            (pkg.version, "cyan"),
        )
        for pkg in packages
    ]

    return section(
        "Package Inventory",
        Columns(items, equal=True, expand=True, column_first=True),
        style="lavender",
    )


def _make_project_panel(paths: list[Path]) -> Panel:
    project_table = Table(highlight=True, box=None, show_header=False)
    project_table.add_row(
        Text("Project", style="rosewater"),
        Text(str(paths[1]), style="bold"),
    )
    project_table.add_row(
        Text("Config Dir", style="rosewater"),
        Text(str(paths[0]), style="bold"),
    )
    project_table.add_row(
        Text("Working Dir", style="rosewater"),
        Text(str(paths[1]), style="bold"),
    )
    return section("Project", project_table, style="bright_blue")


def _make_header_panel(env: Environment) -> Panel:
    header_table = Table(highlight=True, box=None, show_header=False)
    header_table.add_row(
        Text("Interpreter Name", style="rosewater"),
        Text(env.interpreter_name, style="bold"),
    )
    header_table.add_row(
        Text("Interpreter Version", style="rosewater"),
        Text(env.interpreter_version, style="bold"),
    )
    header_table.add_row(
        Text("Interpreter Path", style="rosewater"),
        Text(env.interpreter_path, style="bold"),
    )
    header_table.add_row(Text("Platform", style="rosewater"), Text(env.platform, style="bold"))
    return section("Debug Information", header_table, style="bright_blue")


def _make_debug_layout(env: Environment) -> Layout:
    """Build a Layout for debug info: header + packages | env vars."""
    header = _make_header_panel(env)

    layout = Layout()
    layout.split_column(
        Layout(header, name="header", size=9),
        Layout(name="main"),
    )
    layout["main"].split_row(
        Layout(_make_project_panel(working_paths()), name="paths", ratio=1),
        Layout(package_inventory(env.packages), name="packages", ratio=2),
    )

    return layout


def _make_debug_panel(env: Environment) -> Panel:
    """Build a single Panel for debug info (fallback for narrow terminals)."""
    table = Table(highlight=True, box=None, show_header=False)
    table.add_row(
        Text("Interpreter Name", style="rosewater"),
        Text(env.interpreter_name, style="bold"),
    )
    table.add_row(
        Text("Interpreter Version", style="rosewater"),
        Text(env.interpreter_version, style="bold"),
    )
    table.add_row(
        Text("Interpreter Path", style="rosewater"),
        Text(env.interpreter_path, style="bold"),
    )
    table.add_row(Text("Platform", style="rosewater"), Text(env.platform, style="bold"))
    table.add_row(
        Text(f"Packages ({len(env.packages)})", style="rosewater"),
        Text.assemble(*[Text(str(pkg), style="bold") for pkg in env.packages]),
    )
    table.add_row(
        Text("Environment Variables", style="rosewater"),
        Text.assemble(*[Text(str(var), style="bold") for var in env.variables]),
    )
    return section("Debug Information", table, style="bright_blue")


def debug_info(console: Console | None = None) -> None:
    """Return debug information."""
    if not console:
        console = get_console()

    env = get_debug_info()

    from repoman.utils.ui.layout import (  # noqa: PLC0415 - deferred to avoid circular import
        use_layout,
    )

    if use_layout(console):
        console.print(_make_debug_layout(env))
    else:
        console.print(_make_debug_panel(env))
