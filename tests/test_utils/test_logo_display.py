"""Tests for the terminal logo renderer."""

# ruff: noqa: D102,D103,D107

import io
from typing import Any, Self

from rich.console import Console

from repoman.utils.ui import logo_display
from repoman.utils.ui.logo_display import BrailleCanvas, Particle, settle_curve, text_to_pixels


class DummyLive:
    """Small stand-in for ``rich.live.Live`` that records frame updates."""

    updates: list[Any]

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self.updates = []

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def update(self, renderable: Any) -> None:
        self.updates.append(renderable)


def test_settle_curve_clamps_progress() -> None:
    assert settle_curve(-1) == settle_curve(0)
    assert settle_curve(2) == settle_curve(1)
    assert settle_curve(0) > settle_curve(0.5) > settle_curve(1)


def test_braille_canvas_sets_pixels_and_clears() -> None:
    canvas = BrailleCanvas(term_width=2, term_height=1)

    canvas.set_pixel(0, 0)
    canvas.set_pixel(1, 3)
    canvas.set_pixel(-1, 0)
    canvas.set_pixel(4, 0)

    rendered = canvas.render()
    assert rendered[0][0] != chr(0x2800)

    canvas.clear()

    assert canvas.render() == [chr(0x2800) * 2]


def test_text_to_pixels_scales_known_glyphs_and_skips_unknowns() -> None:
    pixels = text_to_pixels("A?", scale=2)

    assert (2, 0) in pixels
    assert max(x for x, _y in pixels) > 6
    assert max(y for _x, y in pixels) == 13


def test_particle_swirl_then_converges() -> None:
    particle = Particle(0, 0, target_x=10, target_y=0, delay=1, phase=0)

    particle.update_converge(0.5)
    assert particle.vx > 0
    assert not particle.at_target

    for _ in range(30):
        particle.update_converge(2.0, strength=0.2, damping=0.6)

    assert particle.at_target


def test_run_particle_logo_renders_final_frame(monkeypatch: Any) -> None:
    live_instances: list[DummyLive] = []

    def make_live(*args: Any, **kwargs: Any) -> DummyLive:
        live = DummyLive(*args, **kwargs)
        live_instances.append(live)
        return live

    monkeypatch.setattr(logo_display, "Live", make_live)
    monkeypatch.setattr(logo_display.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        logo_display,
        "text_to_pixels",
        lambda _text, scale=1: [(0, 0), (1 * scale, 0), (0, 1 * scale)],
    )

    output = io.StringIO()
    console = Console(file=output, force_terminal=False, width=30, height=12, record=True)

    logo_display.run_particle_logo(console, hold_seconds=0.1)

    assert live_instances
    assert live_instances[0].updates
    assert output.getvalue().strip()
