from collections.abc import Callable
from datetime import datetime
from typing import Any

from rich.text import Text
from rich.tree import Tree


class TaskTree:
    """A ``rich.tree.Tree`` wrapper that displays a command with its stdout and stderr.

    Renders a task as a hidden-root tree with the command label on top and optional
    ``stdout`` and ``stderr`` branches beneath it. Output branches are lazily created
    the first time content is set and are ordered so that ``stdout`` always appears
    before ``stderr`` regardless of which stream produced output first.

    Attributes:
        tree: The underlying ``rich.tree.Tree`` instance to be rendered.
        cmd: The command string displayed as the first (non-root) node.
    """

    _stdout_text: Text | None
    _stdout_str: list[str]
    _stderr_text: Text | None
    _stderr_str: list[str]

    def __init__(self, cmd: str) -> None:
        """Initialize the tree with a command label and no output branches.

        Args:
            cmd: The command string to display at the top of the tree.
        """
        self.tree = Tree("", hide_root=True)
        self.cmd = cmd
        self.tree.add(cmd)
        self._stdout_text = None
        self._stderr_text = None
        self._stdout_str = []
        self._stderr_str = []

    def set_stdout(self, stdout: list[str]):
        """Set or replace the lines shown under the ``stdout`` branch.

        Creates the ``stdout`` branch on first non-empty call and reorders the tree
        so that ``stdout`` is rendered above ``stderr`` if ``stderr`` was added first.

        Args:
            stdout: Lines of standard output to display. No-op if empty.
        """
        if not stdout:
            return

        if not self._stdout_text:
            self._stdout_text = Text("", style="dim")
            stdout_branch = self.tree.add("stdout")
            stdout_branch.add(self._stdout_text)

            if self._stderr_text:
                # Swap the children so that stdout is always first
                # In this case, there will be 3 things in the tree.
                # 0 - the cmd from init
                # 1 - the stderr branch since it was apparently added first
                # 2 - the stdout branch we just added
                self.tree.children = [self.tree.children[2], self.tree.children[1]]

        self._stdout_str = stdout
        self._stdout_text.plain = "\n".join(stdout)

    def set_stderr(self, stderr: list[str]):
        """Set or replace the lines shown under the ``stderr`` branch.

        Creates the ``stderr`` branch on first non-empty call, styled in red.

        Args:
            stderr: Lines of standard error to display. No-op if empty.
        """
        if not stderr:
            return

        if not self._stderr_text:
            self._stderr_text = Text("", style="red")
            stderr_branch = self.tree.add("stderr")
            stderr_branch.add(self._stderr_text)
            self._stderr_str = stderr

        self._stderr_str = stderr
        self._stderr_text.plain = "\n".join(stderr)

    def reset(self):
        """Clear stdout/stderr branches and restore the tree to its initial state.

        After this call the tree contains only the original command label, and
        subsequent ``set_stdout``/``set_stderr`` calls will recreate the branches.
        """
        self._stdout_text = None
        self._stderr_text = None
        self._stdout_str = []
        self._stderr_str = []
        self.tree.children = []
        self.tree.add(self.cmd)

    def height(self) -> int:
        """Return the number of rendered lines the tree currently occupies.

        Accounts for the command line plus one header line per populated output
        branch and one line per output line.

        Returns:
            The total rendered height in lines.
        """
        stdout_height = len(self._stdout_str) + 1 if self._stdout_str else 0
        stderr_height = len(self._stderr_str) + 1 if self._stderr_str else 0
        cmd_height = 1

        return cmd_height + stdout_height + stderr_height


class Padder:
    """Tracks the tallest ``TaskTree`` seen and reports bottom padding for others.

    Useful when rendering multiple ``TaskTree`` instances in a table row/column where
    each cell should be vertically padded to match the tallest tree so the layout
    does not collapse as trees grow.
    """

    def __init__(self) -> None:
        """Initialize the padder with a max observed height of zero."""
        self._max_padding = 0

    def get_padding(self, tree: TaskTree) -> int:
        """Update the max observed height and return padding for ``tree``.

        Args:
            tree: The tree whose height should be compared against the running max.

        Returns:
            The number of blank lines to append to ``tree`` so that its rendered
            height matches the tallest tree observed so far.
        """
        height = tree.height()
        self._max_padding = max(self._max_padding, height)
        return self._max_padding - height


class UpdateTracker:
    """Class to enable dynamic updates on the UI tables. By default, rich allows you to set a refresh rate or trigger manual
    updates. This makes manual updates more performant by doing quick 'dirty' checks to determine if updating ins required. Updating
    is technically always required because the table's 'elapsed time' column always changes, but we don't want to update the table just
    because of that.

    This class tracks some state and has a min/max ms time config to keep the table looking responsive without updating too often. The
    driver for this was my CPU usage while the installer was running, paired with the size of the asciinema files that were generated
    because of frequent updates. Obviously, the more frequent the update the better the table looks, but that's the trade off.

    """

    def __init__(self, max_update_timeout_ms: float = 5000, min_update_ms: float = 200) -> None:
        """Args:
        max_update_timeout_ms: The maximum amount of time in milliseconds that can pass before an update is forced. This is useful
        because the table usually contains an 'elapsed time' column that should update fairly frequently regardless of everything else.
        min_update_ms: The minimum amount of time in milliseconds that must pass before an update is allowed. This prevents updates
        from getting too frequent.
        """
        self._timeout_ms = max_update_timeout_ms
        self._min_update_ms = min_update_ms
        self._last_update_timestamp_ms = datetime.now().timestamp() * 1000
        self._last_update_state: list[Any] = []

    def max_update_time_passed(self, now: float) -> bool:
        if now - self._last_update_timestamp_ms > self._timeout_ms:
            return True
        return False

    def min_update_time_passed(self, now: float) -> bool:
        if now - self._last_update_timestamp_ms > self._min_update_ms:
            return True
        return False

    def _update(
        self,
        now: float,
        update_fn: Callable[[], None],
        state: list[str | list[str]],
    ):
        update_fn()
        self._last_update_timestamp_ms = now
        self._last_update_state = state

    def update(self, update_fn: Callable[[], None], state: list[str | list[str]]):
        now = datetime.now().timestamp() * 1000

        if (self.min_update_time_passed(now) and state != self._last_update_state) or self.max_update_time_passed(now):
            self._update(now, update_fn, state)
