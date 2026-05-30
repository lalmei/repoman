#!/usr/bin/env python3
"""
Standalone particle coalesce logo for terminal use.

Renders a two-line logo:
    HUGGING FACE
    ML INTERN

No project-local imports required.
Dependency: rich
"""

from __future__ import annotations

import argparse
import math
import random
import shutil
import time
from dataclasses import dataclass

from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.text import Text

# ----------------------------
# Small 5x7 bitmap font
# ----------------------------

FONT_5X7: dict[str, list[str]] = {
    "A": [
        "01110",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ],
    "C": [
        "01111",
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "01111",
    ],
    "E": [
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "11111",
    ],
    "F": [
        "11111",
        "10000",
        "10000",
        "11110",
        "10000",
        "10000",
        "10000",
    ],
    "G": [
        "01111",
        "10000",
        "10000",
        "10011",
        "10001",
        "10001",
        "01110",
    ],
    "H": [
        "10001",
        "10001",
        "10001",
        "11111",
        "10001",
        "10001",
        "10001",
    ],
    "I": [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "11111",
    ],
    "L": [
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "10000",
        "11111",
    ],
    "M": [
        "10001",
        "11011",
        "10101",
        "10101",
        "10001",
        "10001",
        "10001",
    ],
    "N": [
        "10001",
        "11001",
        "10101",
        "10011",
        "10001",
        "10001",
        "10001",
    ],
    "R": [
        "11110",
        "10001",
        "10001",
        "11110",
        "10100",
        "10010",
        "10001",
    ],
    "T": [
        "11111",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
        "00100",
    ],
    "U": [
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "10001",
        "01110",
    ],
    " ": [
        "000",
        "000",
        "000",
        "000",
        "000",
        "000",
        "000",
    ],
}


def text_to_pixels(
    text: str, scale: int = 2, letter_spacing: int = 1
) -> list[tuple[int, int]]:
    pixels: list[tuple[int, int]] = []
    x_cursor = 0
    for ch in text.upper():
        glyph = FONT_5X7.get(ch)
        if glyph is None:
            raise ValueError(f"Unsupported character in font: {ch!r}")
        glyph_w = len(glyph[0])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    for sy in range(scale):
                        for sx in range(scale):
                            pixels.append((x_cursor + gx * scale + sx, gy * scale + sy))
        x_cursor += glyph_w * scale + letter_spacing * scale
    return pixels


# ----------------------------
# Braille canvas
# ----------------------------

BRAILLE_BLANK = chr(0x2800)
BRAILLE_OFFSETS = {
    (0, 0): 0x01,  # dot 1
    (0, 1): 0x02,  # dot 2
    (0, 2): 0x04,  # dot 3
    (1, 0): 0x08,  # dot 4
    (1, 1): 0x10,  # dot 5
    (1, 2): 0x20,  # dot 6
    (0, 3): 0x40,  # dot 7
    (1, 3): 0x80,  # dot 8
}


class BrailleCanvas:
    def __init__(self, width_chars: int, height_chars: int):
        self.width_chars = max(1, width_chars)
        self.height_chars = max(1, height_chars)
        self.pixel_width = self.width_chars * 2
        self.pixel_height = self.height_chars * 4
        self._pixels: set[tuple[int, int]] = set()

    def clear(self) -> None:
        self._pixels.clear()

    def set_pixel(self, x: int, y: int) -> None:
        if 0 <= x < self.pixel_width and 0 <= y < self.pixel_height:
            self._pixels.add((x, y))

    def render(self) -> list[str]:
        lines: list[str] = []
        for cy in range(self.height_chars):
            chars = []
            for cx in range(self.width_chars):
                bits = 0
                base_x = cx * 2
                base_y = cy * 4
                for dx in range(2):
                    for dy in range(4):
                        if (base_x + dx, base_y + dy) in self._pixels:
                            bits |= BRAILLE_OFFSETS[(dx, dy)]
                chars.append(chr(0x2800 + bits) if bits else BRAILLE_BLANK)
            lines.append("".join(chars))
        return lines


# ----------------------------
# Timing / color
# ----------------------------


def settle_curve(progress: float) -> float:
    """A mild overshoot/settle profile in [0,1]."""
    p = max(0.0, min(1.0, progress))
    # Damped oscillation, normalized to a small positive value.
    return math.exp(-4.0 * p) * abs(math.sin(8.0 * math.pi * p))


def warm_gold_from_white(progress: float) -> tuple[int, int, int]:
    """Blend from near-white to warm gold."""
    p = max(0.0, min(1.0, progress))
    start = (255, 250, 235)
    end = (255, 200, 80)
    r = int(start[0] + (end[0] - start[0]) * p)
    g = int(start[1] + (end[1] - start[1]) * p)
    b = int(start[2] + (end[2] - start[2]) * p)
    return r, g, b


# ----------------------------
# Particles
# ----------------------------


@dataclass
class Particle:
    x: float
    y: float
    target_x: float
    target_y: float
    vx: float = 0.0
    vy: float = 0.0
    phase: float = 0.0
    delay: float = 0.0

    def update_converge(
        self, t: float, strength: float = 0.08, damping: float = 0.92
    ) -> None:
        if t < self.delay:
            self.x += self.vx
            self.y += self.vy
            self.vx *= 0.99
            self.vy *= 0.99
            angle = self.phase + t * 2.0
            self.vx += math.cos(angle) * 0.3
            self.vy += math.sin(angle) * 0.3
            return

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        self.vx += dx * strength
        self.vy += dy * strength
        self.vx *= damping
        self.vy *= damping
        self.x += self.vx
        self.y += self.vy


def get_bounds(pixels: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    if not pixels:
        return 0, 0, 0, 0
    xs = [p[0] for p in pixels]
    ys = [p[1] for p in pixels]
    return min(xs), max(xs), min(ys), max(ys)


def build_targets(canvas: BrailleCanvas, scale: int = 2) -> list[tuple[int, int]]:
    line1 = text_to_pixels("HUGGING FACE", scale=scale)
    line2 = text_to_pixels("ML INTERN", scale=scale)

    min_x1, max_x1, min_y1, max_y1 = get_bounds(line1)
    min_x2, max_x2, min_y2, max_y2 = get_bounds(line2)

    w1, h1 = max_x1 - min_x1 + 1, max_y1 - min_y1 + 1
    w2, h2 = max_x2 - min_x2 + 1, max_y2 - min_y2 + 1

    gap = 6
    total_h = h1 + gap + h2
    start_y = (canvas.pixel_height - total_h) // 2

    offset_x1 = (canvas.pixel_width - w1) // 2 - min_x1
    offset_y1 = start_y - min_y1
    offset_x2 = (canvas.pixel_width - w2) // 2 - min_x2
    offset_y2 = start_y + h1 + gap - min_y2

    targets_1 = [(x + offset_x1, y + offset_y1) for x, y in line1]
    targets_2 = [(x + offset_x2, y + offset_y2) for x, y in line2]
    return targets_1 + targets_2


def render_colored(canvas: BrailleCanvas, rgb: tuple[int, int, int]) -> Align:
    r, g, b = rgb
    result = Text()
    for line in canvas.render():
        for ch in line:
            if ch == BRAILLE_BLANK:
                result.append(ch)
            else:
                result.append(ch, style=f"rgb({r},{g},{b})")
        result.append("\n")
    return Align.center(result)


def run_particle_logo(
    console: Console,
    hold_seconds: float = 1.5,
    fps: int = 24,
    max_particles: int = 1500,
    ambient_count: int = 200,
    scale: int = 2,
) -> None:
    term = shutil.get_terminal_size(fallback=(100, 30))
    term_width = min(term.columns, 120)
    term_height = min(max(10, term.lines - 4), 35)
    canvas = BrailleCanvas(term_width, term_height)

    all_targets = build_targets(canvas, scale=scale)
    step = max(1, len(all_targets) // max_particles)
    sampled_targets = all_targets[::step]

    rng = random.Random(42)
    particles: list[Particle] = []
    pw, ph = canvas.pixel_width, canvas.pixel_height

    for tx, ty in sampled_targets:
        side = rng.choice(["top", "bottom", "left", "right"])
        if side == "top":
            sx, sy = rng.uniform(0, pw), rng.uniform(-20, -5)
        elif side == "bottom":
            sx, sy = rng.uniform(0, pw), rng.uniform(ph + 5, ph + 20)
        elif side == "left":
            sx, sy = rng.uniform(-20, -5), rng.uniform(0, ph)
        else:
            sx, sy = rng.uniform(pw + 5, pw + 20), rng.uniform(0, ph)

        delay = rng.uniform(0, 0.4)
        phase = random.uniform(0, math.pi * 2)
        p = Particle(sx, sy, tx, ty, phase=phase, delay=delay)

        angle = math.atan2(ph / 2 - sy, pw / 2 - sx) + rng.gauss(0, 0.8)
        speed = rng.uniform(1.0, 2.5)
        p.vx = math.cos(angle) * speed
        p.vy = math.sin(angle) * speed
        particles.append(p)

    ambient: list[Particle] = []
    for _ in range(ambient_count):
        ax = rng.uniform(0, pw)
        ay = rng.uniform(0, ph)
        ap = Particle(ax, ay, ax, ay, phase=random.uniform(0, math.pi * 2))
        ap.vx = rng.gauss(0, 1)
        ap.vy = rng.gauss(0, 1)
        ambient.append(ap)

    converge_frames = max(1, int(fps * 0.9))
    hold_frames = max(1, int(fps * hold_seconds))
    total_frames = converge_frames + hold_frames

    with Live(console=console, refresh_per_second=fps, transient=True) as live:
        for frame in range(total_frames):
            canvas.clear()
            t = frame * (1.0 / fps)

            for ap in ambient:
                ap.x += ap.vx + math.sin(t + ap.phase) * 0.5
                ap.y += ap.vy + math.cos(t + ap.phase * 1.3) * 0.5
                ap.x %= pw
                ap.y %= ph

                if frame < converge_frames:
                    alpha = 0.3 + 0.2 * math.sin(t * 2 + ap.phase)
                else:
                    fade = (frame - converge_frames) / hold_frames
                    alpha = (0.3 + 0.2 * math.sin(t * 2 + ap.phase)) * (1 - fade)
                if alpha > 0.25:
                    canvas.set_pixel(int(ap.x), int(ap.y))

            if frame < converge_frames:
                progress = frame / converge_frames
                noise = settle_curve(progress)
                for p in particles:
                    p.update_converge(t, strength=0.06, damping=0.90)
                    canvas.set_pixel(int(p.x), int(p.y))
                    trail_scale = 0.2 + 0.5 * noise
                    trail_x = int(p.x - p.vx * trail_scale)
                    trail_y = int(p.y - p.vy * trail_scale)
                    canvas.set_pixel(trail_x, trail_y)
                rgb = warm_gold_from_white(progress)
            else:
                settle_t = (frame - converge_frames) / hold_frames
                for p in particles:
                    jitter = (1 - settle_t) * 0.7
                    jx = p.target_x + math.sin(t * 3 + p.phase) * jitter
                    jy = p.target_y + math.cos(t * 3 + p.phase * 1.5) * jitter
                    canvas.set_pixel(int(jx), int(jy))
                    canvas.set_pixel(int(p.target_x), int(p.target_y))
                rgb = (255, 200, 80)

            live.update(render_colored(canvas, rgb))
            time.sleep(1.0 / fps)

    canvas.clear()
    for p in particles:
        canvas.set_pixel(int(p.target_x), int(p.target_y))
    console.print(render_colored(canvas, (255, 200, 80)))


def main() -> int:
    parser = argparse.ArgumentParser(description="Standalone terminal particle logo.")
    parser.add_argument("--hold-seconds", type=float, default=1.5)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--max-particles", type=int, default=1500)
    parser.add_argument("--ambient-count", type=int, default=200)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument(
        "--no-color", action="store_true", help="Disable color if desired."
    )
    args = parser.parse_args()

    console = Console(color_system=None if args.no_color else "auto")

    try:
        run_particle_logo(
            console=console,
            hold_seconds=args.hold_seconds,
            fps=args.fps,
            max_particles=args.max_particles,
            ambient_count=args.ambient_count,
            scale=args.scale,
        )
    except KeyboardInterrupt:
        console.print("\n[dim]interrupted[/dim]")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
