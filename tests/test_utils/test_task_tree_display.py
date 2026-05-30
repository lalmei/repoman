"""Tests for task tree display helpers."""

# ruff: noqa: D103

from rich.text import Text

from repoman.utils.task_tree_display import Padder, TaskTree, UpdateTracker


def test_task_tree_orders_stdout_before_stderr_when_stderr_arrives_first() -> None:
    tree = TaskTree("make test")

    tree.set_stderr(["warning"])
    tree.set_stdout(["ok", "done"])

    assert tree.height() == 6
    assert [str(child.label) for child in tree.tree.children] == ["stdout", "stderr"]
    stdout_text = tree.tree.children[0].children[0].label
    stderr_text = tree.tree.children[1].children[0].label

    assert isinstance(stdout_text, Text)
    assert isinstance(stderr_text, Text)
    assert stdout_text.plain == "ok\ndone"
    assert stderr_text.plain == "warning"


def test_task_tree_reset_and_empty_updates() -> None:
    tree = TaskTree("ruff check")

    tree.set_stdout([])
    tree.set_stderr([])
    assert tree.height() == 1

    tree.set_stdout(["clean"])
    tree.reset()

    assert tree.height() == 1
    assert [str(child.label) for child in tree.tree.children] == ["ruff check"]


def test_padder_tracks_tallest_tree() -> None:
    short = TaskTree("short")
    tall = TaskTree("tall")
    tall.set_stdout(["a", "b", "c"])
    padder = Padder()

    assert padder.get_padding(tall) == 0
    assert padder.get_padding(short) == tall.height() - short.height()


def test_update_tracker_refreshes_for_state_change_and_timeout() -> None:
    calls = 0

    def mark_updated() -> None:
        nonlocal calls
        calls += 1

    tracker = UpdateTracker(max_update_timeout_ms=100, min_update_ms=10)
    tracker._last_update_timestamp_ms = 0

    tracker.update(mark_updated, ["stdout"])
    tracker._last_update_timestamp_ms = 0
    tracker.update(mark_updated, ["stdout"])

    assert calls == 2


def test_update_tracker_skips_when_state_is_unchanged_and_too_recent() -> None:
    calls: list[str] = []
    tracker = UpdateTracker(max_update_timeout_ms=10_000, min_update_ms=10_000)
    tracker._last_update_state = ["same"]

    def update_fn() -> None:
        calls.append("updated")

    tracker.update(update_fn, ["same"])

    assert calls == []


def test_update_tracker_private_update_sets_state() -> None:
    tracker = UpdateTracker()
    calls: list[str] = []

    def update_fn() -> None:
        calls.append("updated")

    tracker._update(123.0, update_fn, ["new"])

    assert calls == ["updated"]
    assert tracker._last_update_timestamp_ms == 123.0
    assert tracker._last_update_state == ["new"]
