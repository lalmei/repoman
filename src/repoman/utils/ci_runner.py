"""Utilities for running CI commands in instantiated templates."""

import os
import queue
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from repoman.utils.logging import get_logger_console

logger, console = get_logger_console(__name__)


@dataclass
class CommandResult:
    """Result of running a command.

    Attributes:
        returncode: Exit code of the command (0 for success)
        stdout: Captured stdout output as string
        stderr: Captured stderr output as string
        command: The command that was executed
    """

    returncode: int
    stdout: str
    stderr: str
    command: str


def run_make_command(
    project_dir: Path,
    command: str,
    env: Optional[dict] = None,
    timeout: Optional[int] = None,
) -> CommandResult:
    """Run a make command in the specified project directory.

    The output is both captured (for assertions) and streamed to stdout/stderr
    (for visibility in pytest output).

    This function ensures that `uv` is available in the PATH, as the template
    Makefile commands use `uv run` to execute Python tools.

    Args:
        project_dir: Directory where the make command should be executed
        command: Make command to run (e.g., "setup", "test", "lint")
        env: Optional environment variables to set. Merged with current environment
        timeout: Optional timeout in seconds. If None, no timeout is set

    Returns:
        CommandResult with returncode, stdout, stderr, and command

    Raises:
        FileNotFoundError: If make command is not found or uv is not available
        subprocess.TimeoutExpired: If command times out (only if timeout is set)
    """
    project_dir = Path(project_dir).resolve()
    if not project_dir.exists():
        raise ValueError(f"Project directory does not exist: {project_dir}")

    # Verify uv is available (required for template make commands)
    uv_path = shutil.which("uv")
    if uv_path is None:
        error_msg = (
            "uv is not available in PATH. "
            "The template Makefile requires uv to run commands. "
            "Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        )
        logger.error(error_msg)
        console.print(f"[red]✗[/red] {error_msg}")
        raise FileNotFoundError("uv command not found. Is uv installed?")

    # Build the full command
    full_command = ["make", command]
    command_str = " ".join(full_command)

    logger.info(f"Running command: {command_str} in {project_dir} (uv found at {uv_path})")
    console.print(f"[blue]→[/blue] Running: [bold]{command_str}[/bold] in {project_dir}")

    # Prepare environment - ensure PATH includes uv if it's in a custom location
    process_env = dict(os.environ)
    if env:
        process_env.update(env)

    # Ensure uv is in PATH (in case it's in a non-standard location)
    uv_dir = str(Path(uv_path).parent)
    current_path = process_env.get("PATH", "")
    # Split PATH by platform-specific separator and check for exact match
    path_entries = current_path.split(os.pathsep) if current_path else []
    if uv_dir not in path_entries:
        # Prepend uv_dir to PATH using platform-specific separator
        path_entries.insert(0, uv_dir)
        process_env["PATH"] = os.pathsep.join(path_entries)

    # Use Popen to stream output while capturing
    try:
        process = subprocess.Popen(
            full_command,
            cwd=str(project_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            env=process_env,
        )

        stdout_lines = []
        stderr_lines = []
        stdout_queue = queue.Queue()
        stderr_queue = queue.Queue()

        def read_stdout():
            """Read from stdout in a separate thread to avoid deadlock."""
            if process.stdout is None:
                stdout_queue.put(None)
                return
            try:
                for line in iter(process.stdout.readline, ""):
                    stdout_queue.put(line)
                stdout_queue.put(None)  # Sentinel to indicate EOF
            except Exception:
                stdout_queue.put(None)

        def read_stderr():
            """Read from stderr in a separate thread to avoid deadlock."""
            if process.stderr is None:
                stderr_queue.put(None)
                return
            try:
                for line in iter(process.stderr.readline, ""):
                    stderr_queue.put(line)
                stderr_queue.put(None)  # Sentinel to indicate EOF
            except Exception:
                stderr_queue.put(None)

        # Start reader threads to read from both pipes concurrently
        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()

        # Read and stream output in real-time from both queues
        stdout_done = False
        stderr_done = False

        # Import time if timeout is needed
        if timeout:
            import time

            start_time = time.time()

        while not (stdout_done and stderr_done):
            # Check timeout if specified
            if timeout:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    process.kill()
                    # Drain queues before raising
                    while not stdout_queue.empty():
                        line = stdout_queue.get()
                        if line is not None:
                            stdout_lines.append(line)
                    while not stderr_queue.empty():
                        line = stderr_queue.get()
                        if line is not None:
                            stderr_lines.append(line)
                    stdout = "".join(stdout_lines)
                    stderr = "".join(stderr_lines)
                    raise subprocess.TimeoutExpired(full_command, timeout, output=stdout, stderr=stderr)

            # Read from stdout queue (non-blocking)
            try:
                stdout_line = stdout_queue.get(timeout=0.1)
                if stdout_line is None:
                    stdout_done = True
                else:
                    stdout_lines.append(stdout_line)
                    # Stream to actual stdout for pytest visibility
                    sys.stdout.write(stdout_line)
                    sys.stdout.flush()
            except queue.Empty:
                pass

            # Read from stderr queue (non-blocking)
            try:
                stderr_line = stderr_queue.get(timeout=0.1)
                if stderr_line is None:
                    stderr_done = True
                else:
                    stderr_lines.append(stderr_line)
                    # Stream to actual stderr for pytest visibility
                    sys.stderr.write(stderr_line)
                    sys.stderr.flush()
            except queue.Empty:
                pass

            # Check if process has finished
            if process.poll() is not None:
                # Process finished, wait for threads to complete and drain queues
                stdout_thread.join(timeout=1.0)
                stderr_thread.join(timeout=1.0)

                # Drain any remaining items from queues
                while not stdout_queue.empty():
                    line = stdout_queue.get()
                    if line is not None:
                        stdout_lines.append(line)
                        sys.stdout.write(line)
                        sys.stdout.flush()
                while not stderr_queue.empty():
                    line = stderr_queue.get()
                    if line is not None:
                        stderr_lines.append(line)
                        sys.stderr.write(line)
                        sys.stderr.flush()
                break

        stdout = "".join(stdout_lines)
        stderr = "".join(stderr_lines)
        returncode = process.returncode

        logger.debug(f"Command completed with return code {returncode}")

        if returncode == 0:
            console.print(f"[green]✓[/green] Command succeeded: [bold]{command_str}[/bold]")
        else:
            console.print(f"[red]✗[/red] Command failed (exit {returncode}): [bold]{command_str}[/bold]")

        return CommandResult(
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
            command=command_str,
        )

    except FileNotFoundError:
        error_msg = f"make command not found. Is make installed?"
        logger.error(error_msg)
        console.print(f"[red]✗[/red] {error_msg}")
        raise FileNotFoundError(error_msg)
    except subprocess.TimeoutExpired as e:
        error_msg = f"Command timed out after {timeout} seconds: {command_str}"
        logger.error(error_msg)
        console.print(f"[red]✗[/red] {error_msg}")
        raise
    except Exception as e:
        error_msg = f"Unexpected error running command {command_str}: {e}"
        logger.error(error_msg)
        console.print(f"[red]✗[/red] {error_msg}")
        raise
