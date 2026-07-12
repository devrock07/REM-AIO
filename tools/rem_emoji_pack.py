"""REM application emoji pack generator — blue glossy badge icons."""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.rem_emoji_names import OLD_TO_REM, REM_EMOJI_NAMES

SIZE = 128
MARGIN = 12
RADIUS = 24
CYAN = (0, 212, 255)
BLUE = (59, 130, 246)
WHITE = (255, 255, 255)
SHADOW = (15, 23, 42, 70)

EMOJI_NAMES: tuple[str, ...] = REM_EMOJI_NAMES

DrawFn = Callable[[ImageDraw.ImageDraw, tuple[int, int, int, int]], None]


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _gradient_badge(box: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    badge = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = badge.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        r = _lerp(CYAN[0], BLUE[0], t)
        g = _lerp(CYAN[1], BLUE[1], t)
        b = _lerp(CYAN[2], BLUE[2], t)
        for x in range(w):
            px[x, y] = (r, g, b, 255)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), RADIUS, fill=255)
    badge.putalpha(mask)
    return badge


def _rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill, radius: int = RADIUS) -> None:
    draw.rounded_rectangle(box, radius, fill=fill)


def _stroke(draw: ImageDraw.ImageDraw, coords, width: int = 7) -> None:
    draw.line(coords, fill=WHITE, width=width, joint="curve")


def _dot(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int) -> None:
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WHITE)


def _check(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], width: int = 8) -> None:
    x0, y0, x1, y1 = box
    mid_y = (y0 + y1) // 2
    _stroke(draw, [(x0 + 8, mid_y), (x0 + 28, y1 - 14), (x1 - 8, y0 + 12)], width)


def _cross(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], width: int = 8) -> None:
    x0, y0, x1, y1 = box
    pad = 18
    _stroke(draw, [(x0 + pad, y0 + pad), (x1 - pad, y1 - pad)], width)
    _stroke(draw, [(x1 - pad, y0 + pad), (x0 + pad, y1 - pad)], width)


def _arrow_right(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    cy = (y0 + y1) // 2
    draw.polygon(
        [(x0 + 14, y0 + 20), (x1 - 18, cy), (x0 + 14, y1 - 20)],
        fill=WHITE,
    )
    draw.rectangle((x0 + 14, cy - 10, x1 - 34, cy + 10), fill=WHITE)


def _arrow_left(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    cy = (y0 + y1) // 2
    draw.polygon(
        [(x1 - 14, y0 + 20), (x0 + 18, cy), (x1 - 14, y1 - 20)],
        fill=WHITE,
    )
    draw.rectangle((x0 + 34, cy - 10, x1 - 14, cy + 10), fill=WHITE)


def _double_arrow_right(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    inner = (box[0] + 8, box[1], box[2] - 18, box[3])
    _arrow_right(draw, inner)
    _arrow_right(draw, (box[0] + 22, box[1], box[2], box[3]))


def _double_arrow_left(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    inner = (box[0], box[1], box[2] - 8, box[3])
    _arrow_left(draw, inner)
    _arrow_left(draw, (box[0], box[1], box[2] - 22, box[3]))


def _triangle_warning(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    draw.polygon([(cx, y0 + 10), (x0 + 12, y1 - 12), (x1 - 12, y1 - 12)], fill=WHITE)
    draw.rectangle((cx - 4, y0 + 34, cx + 4, y1 - 34), fill=BLUE)
    _dot(draw, cx, y1 - 24, 5)


def _heart(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2 + 6
    draw.ellipse((cx - 22, cy - 28, cx, cy - 6), fill=WHITE)
    draw.ellipse((cx, cy - 28, cx + 22, cy - 6), fill=WHITE)
    draw.polygon([(x0 + 16, cy - 8), (x1 - 16, cy - 8), (cx, y1 - 14)], fill=WHITE)


def _star(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], points: int = 5) -> None:
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    outer = min(x1 - x0, y1 - y0) * 0.38
    inner = outer * 0.45
    coords = []
    for i in range(points * 2):
        angle = math.pi / 2 + i * math.pi / points
        radius = outer if i % 2 == 0 else inner
        coords.append((cx + math.cos(angle) * radius, cy - math.sin(angle) * radius))
    draw.polygon(coords, fill=WHITE)


def _crown(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    base_y = y1 - 22
    draw.rectangle((x0 + 14, base_y, x1 - 14, y1 - 12), fill=WHITE)
    for px in (x0 + 20, (x0 + x1) // 2, x1 - 20):
        draw.polygon([(px - 10, base_y), (px, y0 + 16), (px + 10, base_y)], fill=WHITE)


def _gear(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=WHITE)
    draw.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=BLUE)
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x = cx + math.cos(rad) * 34
        y = cy - math.sin(rad) * 34
        draw.rectangle((x - 6, y - 6, x + 6, y + 6), fill=WHITE)


def _music_note(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.ellipse((x0 + 16, y1 - 36, x0 + 40, y1 - 12), fill=WHITE)
    draw.rectangle((x1 - 30, y0 + 14, x1 - 22, y1 - 22), fill=WHITE)
    draw.polygon([(x1 - 30, y0 + 14), (x1 - 10, y0 + 22), (x1 - 22, y0 + 30)], fill=WHITE)


def _pause(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    w = 14
    gap = 12
    cx = (x0 + x1) // 2
    draw.rounded_rectangle((cx - gap - w, y0 + 18, cx - gap, y1 - 18), 4, fill=WHITE)
    draw.rounded_rectangle((cx + gap, y0 + 18, cx + gap + w, y1 - 18), 4, fill=WHITE)


def _play(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    cy = (y0 + y1) // 2
    draw.polygon([(x0 + 20, y0 + 18), (x1 - 18, cy), (x0 + 20, y1 - 18)], fill=WHITE)


def _stop(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    pad = 22
    draw.rounded_rectangle((box[0] + pad, box[1] + pad, box[2] - pad, box[3] - pad), 6, fill=WHITE)


def _shield(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], inner: str | None = None) -> None:
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    draw.polygon(
        [(cx, y0 + 10), (x1 - 14, y0 + 28), (x1 - 20, y1 - 14), (cx, y1 - 6), (x0 + 20, y1 - 14), (x0 + 14, y0 + 28)],
        fill=WHITE,
    )
    if inner == "lock":
        lx, ly = cx - 10, (y0 + y1) // 2
        draw.arc((lx, ly - 18, lx + 20, ly + 4), 180, 0, fill=BLUE, width=5)
        draw.rectangle((lx, ly, lx + 20, ly + 22), fill=BLUE)
    elif inner == "check":
        _check(draw, (x0 + 24, y0 + 28, x1 - 24, y1 - 20), 6)


def _home(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    draw.polygon([(cx, y0 + 12), (x0 + 14, y0 + 38), (x1 - 14, y0 + 38)], fill=WHITE)
    draw.rectangle((x0 + 26, y0 + 38, x1 - 26, y1 - 14), fill=WHITE)


def _folder(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0 + 12, y0 + 30, x1 - 12, y1 - 16), 8, fill=WHITE)
    draw.rounded_rectangle((x0 + 12, y0 + 22, x0 + 48, y0 + 36), 4, fill=WHITE)


def _file_doc(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0 + 28, y0 + 12, x1 - 20, y1 - 14), 6, fill=WHITE)
    draw.line([(x0 + 36, y0 + 40), (x1 - 30, y0 + 40)], fill=BLUE, width=5)
    draw.line([(x0 + 36, y0 + 54), (x1 - 36, y0 + 54)], fill=BLUE, width=5)


def _trash(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle((x0 + 30, y0 + 18, x1 - 30, y0 + 26), fill=WHITE)
    draw.rectangle((x0 + 22, y0 + 26, x1 - 22, y1 - 16), fill=WHITE)
    for x in (x0 + 36, (x0 + x1) // 2, x1 - 36):
        draw.line([(x, y0 + 34), (x, y1 - 22)], fill=BLUE, width=4)


def _user(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    draw.ellipse((cx - 16, box[1] + 14, cx + 16, box[1] + 46), fill=WHITE)
    draw.ellipse((cx - 28, box[1] + 48, cx + 28, box[3] - 10), fill=WHITE)


def _mic(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    draw.rounded_rectangle((cx - 12, box[1] + 14, cx + 12, box[1] + 52), 8, fill=WHITE)
    draw.arc((cx - 22, box[1] + 40, cx + 22, box[3] - 8), 0, 180, fill=WHITE, width=6)
    draw.line([(cx, box[3] - 8), (cx, box[3] - 16)], fill=WHITE, width=6)


def _gamepad(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle((box[0] + 12, box[1] + 34, box[2] - 12, box[3] - 28), 18, fill=WHITE)
    _dot(draw, box[0] + 36, (box[1] + box[3]) // 2, 6)
    _dot(draw, box[2] - 36, (box[1] + box[3]) // 2 - 10, 5)
    _dot(draw, box[2] - 36, (box[1] + box[3]) // 2 + 10, 5)


def _gift(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    draw.rectangle((x0 + 18, y0 + 38, x1 - 18, y1 - 14), fill=WHITE)
    draw.rectangle((cx - 6, y0 + 18, cx + 6, y1 - 14), fill=WHITE)
    draw.rectangle((x0 + 18, y0 + 28, x1 - 18, y0 + 42), fill=WHITE)


def _ticket_icon(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle((box[0] + 16, box[1] + 22, box[2] - 16, box[3] - 22), 8, fill=WHITE)
    cy = (box[1] + box[3]) // 2
    draw.ellipse((box[0] + 8, cy - 8, box[0] + 24, cy + 8), fill=BLUE)
    draw.ellipse((box[2] - 24, cy - 8, box[2] - 8, cy + 8), fill=BLUE)


def _bell(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    draw.polygon([(cx, box[1] + 16), (box[0] + 22, box[1] + 52), (box[2] - 22, box[1] + 52)], fill=WHITE)
    draw.ellipse((cx - 8, box[3] - 24, cx + 8, box[3] - 8), fill=WHITE)


def _at_sign(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), outline=WHITE, width=7)
    draw.ellipse((cx + 2, cy - 10, cx + 18, cy + 10), fill=WHITE)
    draw.rectangle((cx + 12, cy - 4, cx + 20, cy + 18), fill=WHITE)


def _hash_channel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    for dx in (-10, 6):
        draw.line([(cx + dx - 14, box[1] + 20), (cx + dx + 14, box[3] - 20)], fill=WHITE, width=8)
        draw.line([(cx + dx - 14, box[3] - 20), (cx + dx + 14, box[1] + 20)], fill=WHITE, width=8)


def _robot(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    draw.rounded_rectangle((box[0] + 24, box[1] + 28, box[2] - 24, box[3] - 18), 10, fill=WHITE)
    _dot(draw, cx - 12, box[1] + 46, 5)
    _dot(draw, cx + 12, box[1] + 46, 5)
    draw.rectangle((cx - 4, box[1] + 12, cx + 4, box[1] + 28), fill=WHITE)
    _dot(draw, cx, box[1] + 10, 4)


def _phone(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle((box[0] + 36, box[1] + 14, box[2] - 36, box[3] - 14), 10, fill=WHITE)
    _dot(draw, (box[0] + box[2]) // 2, box[3] - 22, 3)


def _monitor(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    draw.rounded_rectangle((box[0] + 16, box[1] + 16, box[2] - 16, box[1] + 58), 6, fill=WHITE)
    draw.rectangle((cx - 16, box[1] + 58, cx + 16, box[1] + 68), fill=WHITE)
    draw.rectangle((cx - 28, box[1] + 68, cx + 28, box[1] + 74), fill=WHITE)


def _globe(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), outline=WHITE, width=6)
    draw.ellipse((cx - 12, cy - 28, cx + 12, cy + 28), outline=WHITE, width=4)
    draw.line([(cx - 28, cy), (cx + 28, cy)], fill=WHITE, width=4)


def _clock(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), outline=WHITE, width=6)
    draw.line([(cx, cy), (cx, cy - 16)], fill=WHITE, width=5)
    draw.line([(cx, cy), (cx + 14, cy + 6)], fill=WHITE, width=5)


def _spinner(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.arc((cx - 26, cy - 26, cx + 26, cy + 26), 20, 300, fill=WHITE, width=8)


def _shuffle(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    _stroke(draw, [(x0 + 16, y0 + 44), (x1 - 30, y0 + 24), (x1 - 16, y0 + 16)], 6)
    _stroke(draw, [(x0 + 16, y1 - 44), (x1 - 30, y1 - 24), (x1 - 16, y1 - 16)], 6)
    draw.polygon([(x1 - 18, y0 + 12), (x1 - 6, y0 + 24), (x1 - 22, y0 + 28)], fill=WHITE)
    draw.polygon([(x1 - 18, y1 - 12), (x1 - 6, y1 - 24), (x1 - 22, y1 - 28)], fill=WHITE)


def _cloud_sound(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    draw.ellipse((x0 + 18, y0 + 30, x0 + 46, y0 + 54), fill=WHITE)
    draw.ellipse((x0 + 34, y0 + 24, x0 + 68, y0 + 52), fill=WHITE)
    draw.ellipse((x0 + 58, y0 + 30, x1 - 22, y0 + 54), fill=WHITE)
    for i, h in enumerate((12, 20, 14)):
        bx = x1 - 36 + i * 10
        draw.rectangle((bx, y1 - 28 - h, bx + 5, y1 - 24), fill=WHITE)


def _list_log(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    for i, y in enumerate((box[1] + 22, box[1] + 42, box[1] + 62)):
        _dot(draw, box[0] + 24, y, 4)
        draw.rectangle((box[0] + 36, y - 4, box[2] - 22, y + 4), fill=WHITE)


def _wrench(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    draw.ellipse((cx - 10, box[1] + 18, cx + 10, box[1] + 38), fill=WHITE)
    draw.polygon([(cx - 8, box[1] + 32), (cx + 18, box[3] - 18), (cx + 28, box[3] - 28), (cx + 2, box[1] + 24)], fill=WHITE)


def _ban(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), outline=WHITE, width=7)
    draw.line([(cx - 20, cy + 20), (cx + 20, cy - 20)], fill=WHITE, width=7)


def _gavel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw.rectangle((box[0] + 28, box[1] + 52, box[2] - 28, box[1] + 60), fill=WHITE)
    draw.rectangle((box[0] + 30, box[1] + 28, box[0] + 58, box[1] + 40), fill=WHITE)
    draw.rectangle((box[0] + 44, box[1] + 36, box[0] + 52, box[1] + 56), fill=WHITE)


def _plus(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.rectangle((cx - 6, cy - 22, cx + 6, cy + 22), fill=WHITE)
    draw.rectangle((cx - 22, cy - 6, cx + 22, cy + 6), fill=WHITE)


def _info_i(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    draw.ellipse((cx - 26, (box[1] + box[3]) // 2 - 26, cx + 26, (box[1] + box[3]) // 2 + 26), outline=WHITE, width=6)
    _dot(draw, cx, box[1] + 36, 5)
    draw.rectangle((cx - 4, box[1] + 48, cx + 4, box[3] - 28), fill=WHITE)


def _question(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), outline=WHITE, width=6)
    draw.arc((cx - 12, cy - 18, cx + 12, cy + 2), 200, 340, fill=WHITE, width=6)
    _dot(draw, cx, cy + 18, 5)


def _status_ring(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, filled: bool) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    if filled:
        _dot(draw, cx, cy, 18)
    else:
        draw.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), outline=WHITE, width=7)


def _status_dnd(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), outline=WHITE, width=6)
    draw.rectangle((cx - 14, cy - 5, cx + 14, cy + 5), fill=WHITE)


def _link_chain(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.arc((cx - 30, cy - 16, cx, cy + 16), 45, 235, fill=WHITE, width=7)
    draw.arc((cx, cy - 16, cx + 30, cy + 16), -55, 135, fill=WHITE, width=7)


def _sparkle(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.line([(cx, cy - 24), (cx, cy + 24)], fill=WHITE, width=6)
    draw.line([(cx - 24, cy), (cx + 24, cy)], fill=WHITE, width=6)
    draw.line([(cx - 16, cy - 16), (cx + 16, cy + 16)], fill=WHITE, width=5)
    draw.line([(cx + 16, cy - 16), (cx - 16, cy + 16)], fill=WHITE, width=5)


def _rose_simple(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    for angle in range(0, 360, 72):
        rad = math.radians(angle)
        x = cx + math.cos(rad) * 14
        y = (box[1] + box[3]) // 2 - math.sin(rad) * 14
        _dot(draw, int(x), int(y), 8)
    _dot(draw, cx, (box[1] + box[3]) // 2, 10)


def _volume_bars(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    base = box[3] - 20
    for i, h in enumerate((18, 28, 38, 48)):
        x = box[0] + 28 + i * 14
        draw.rectangle((x, base - h, x + 8, base), fill=WHITE)


def _gif_frame(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, blocked: bool = False) -> None:
    draw.rounded_rectangle((box[0] + 20, box[1] + 24, box[2] - 20, box[3] - 24), 8, outline=WHITE, width=6)
    if blocked:
        _cross(draw, (box[0] + 30, box[1] + 32, box[2] - 30, box[3] - 32), 6)


def _red_accent_dot(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=(255, 230, 230, 255))


def _diamond(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.polygon([(cx, cy - 26), (cx + 22, cy), (cx, cy + 26), (cx - 22, cy)], fill=WHITE)


def _puzzle(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle((box[0] + 22, box[1] + 22, box[2] - 22, box[3] - 22), 6, fill=WHITE)
    cx = (box[0] + box[2]) // 2
    draw.rectangle((cx - 4, box[1] + 14, cx + 4, box[1] + 28), fill=WHITE)
    draw.rectangle((box[2] - 30, (box[1] + box[3]) // 2 - 4, box[2] - 16, (box[1] + box[3]) // 2 + 4), fill=WHITE)


def _eye_slash(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.arc((cx - 30, cy - 14, cx + 30, cy + 14), 200, 340, fill=WHITE, width=6)
    _dot(draw, cx, cy, 6)
    draw.line([(box[0] + 20, box[3] - 20), (box[2] - 20, box[1] + 20)], fill=WHITE, width=6)


def _terminal(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw.rounded_rectangle((box[0] + 18, box[1] + 22, box[2] - 18, box[3] - 22), 8, outline=WHITE, width=6)
    draw.polygon([(box[0] + 28, (box[1] + box[3]) // 2 - 8), (box[0] + 44, (box[1] + box[3]) // 2), (box[0] + 28, (box[1] + box[3]) // 2 + 8)], fill=WHITE)


def _tag_role(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    draw.polygon(
        [(box[0] + 20, box[1] + 30), (box[2] - 34, box[1] + 30), (box[2] - 18, (box[1] + box[3]) // 2), (box[2] - 34, box[3] - 30), (box[0] + 20, box[3] - 30)],
        fill=WHITE,
    )
    _dot(draw, box[0] + 32, (box[1] + box[3]) // 2, 5)


def _wave(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    draw.arc((cx - 8, box[1] + 30, cx + 30, box[3] - 10), 200, 340, fill=WHITE, width=7)
    for i, x in enumerate((cx - 20, cx, cx + 20)):
        draw.line([(x, box[1] + 50 - i * 6), (x, box[3] - 18)], fill=WHITE, width=6)


def _party(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    draw.polygon([(cx, box[1] + 16), (box[2] - 22, box[3] - 22), (box[0] + 22, box[3] - 22)], fill=WHITE)
    for px, py in ((box[0] + 30, box[1] + 30), (box[2] - 30, box[1] + 34), (cx, box[1] + 24)):
        _dot(draw, px, py, 4)


def _check_circle(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    draw.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), outline=WHITE, width=6)
    _check(draw, (box[0] + 24, box[1] + 24, box[2] - 24, box[3] - 24), 6)


def _rocket(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    cx = (box[0] + box[2]) // 2
    draw.polygon([(cx, box[1] + 14), (cx + 18, box[1] + 52), (cx - 18, box[1] + 52)], fill=WHITE)
    draw.polygon([(cx - 18, box[1] + 48), (cx - 30, box[3] - 18), (cx - 8, box[1] + 56)], fill=WHITE)
    draw.polygon([(cx + 18, box[1] + 48), (cx + 30, box[3] - 18), (cx + 8, box[1] + 56)], fill=WHITE)


def _vanity(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    _sparkle(draw, box)
    cx = (box[0] + box[2]) // 2
    draw.rounded_rectangle((cx - 18, (box[1] + box[3]) // 2 - 6, cx + 18, (box[1] + box[3]) // 2 + 20), 4, fill=WHITE)


LEGACY_SYMBOL_MAP: dict[str, DrawFn] = {
    "37496alert": _triangle_warning,
    "7club_ban": _ban,
    "_rose": _rose_simple,
    "Autoreact": _sparkle,
    "autorole": _tag_role,
    "axon_owner": _crown,
    "BlueDot": lambda d, b: _dot(d, (b[0] + b[2]) // 2, (b[1] + b[3]) // 2, 16),
    "Bots": _robot,
    "browser": _globe,
    "Commands": _terminal,
    "CrossIcon": _cross,
    "customrole": _tag_role,
    "Dc_RedCrownEsports": _crown,
    "delete": _trash,
    "Denied": _ban,
    "disabled1": _cross,
    "dnd": _status_dnd,
    "enabled": _check,
    "enabled_": _check,
    "Extra": _sparkle,
    "filder": _folder,
    "file": _file_doc,
    "forward": _double_arrow_right,
    "games": _gamepad,
    "Gear": _gear,
    "GIFD": lambda d, b: _gif_frame(d, b, blocked=True),
    "GIFN": lambda d, b: _gif_frame(d, b, blocked=False),
    "Giveaway": _gift,
    "Giveaways": _gift,
    "greet": _wave,
    "headmod": lambda d, b: _shield(d, b, "check"),
    "heart_em": _heart,
    "Heeriye": _music_note,
    "home": _home,
    "icon_booster": _rocket,
    "icon_ping": _at_sign,
    "iconArrowRight": _arrow_right,
    "iconLoad": _spinner,
    "icons_bot": _robot,
    "icons_channel": _hash_channel,
    "icons_discordbotdev": _wrench,
    "icons_music": _music_note,
    "icons_next": _play,
    "icons_pause": _pause,
    "icons_plus": _plus,
    "icons_warning": _triangle_warning,
    "iconSetting": _gear,
    "idle": lambda d, b: _status_ring(d, b, filled=False),
    "ignore": _eye_slash,
    "info": _info_i,
    "InviteTracker": _link_chain,
    "jiosaavn": _music_note,
    "king": _crown,
    "land_yildiz": _star,
    "loading": _spinner,
    "logging": _list_log,
    "max__A": _volume_bars,
    "mention": _at_sign,
    "ml_cross": _cross,
    "mobile": _phone,
    "mod": _gavel,
    "Moderation": _shield,
    "Module": _puzzle,
    "music": _music_note,
    "musicstop_icons": _stop,
    "next": _arrow_right,
    "offline": lambda d, b: _status_ring(d, b, filled=False),
    "olympus_cross": _cross,
    "olympus_notify": _bell,
    "olympus_staff": lambda d, b: _shield(d, b, "check"),
    "olympus_tick": _check,
    "olympusArrow": _arrow_right,
    "online": lambda d, b: _status_ring(d, b, filled=True),
    "owner": _crown,
    "pc": _monitor,
    "premium": _diamond,
    "questions": _question,
    "red_dot": _red_accent_dot,
    "RedHeart": _heart,
    "rewind1": _double_arrow_left,
    "riverse_fun": _party,
    "security": lambda d, b: _shield(d, b, "lock"),
    "sg_rd": lambda d, b: _dot(d, (b[0] + b[2]) // 2, (b[1] + b[3]) // 2, 12),
    "shuffle": _shuffle,
    "skip": _double_arrow_right,
    "SoundCloud": _cloud_sound,
    "sq_HeadMod": _shield,
    "star": _star,
    "tick": _check,
    "tick_red": _check,
    "ticket": _ticket_icon,
    "timer": _clock,
    "U_admin": _shield,
    "Uptime": _clock,
    "user": _user,
    "Utility": _wrench,
    "VanityRoles": _vanity,
    "voice": _mic,
    "Warning": _triangle_warning,
    "WarningIcon": _triangle_warning,
    "youtube": _play,
    "Ztick": _check_circle,
}

SYMBOL_MAP: dict[str, DrawFn] = {}
for _legacy_name, _draw_fn in LEGACY_SYMBOL_MAP.items():
    _rem_name = OLD_TO_REM.get(_legacy_name)
    if _rem_name:
        SYMBOL_MAP[_rem_name] = _draw_fn


def symbol_box() -> tuple[int, int, int, int]:
    return (MARGIN + 8, MARGIN + 8, SIZE - MARGIN - 8, SIZE - MARGIN - 8)


def render_emoji(name: str) -> Image.Image:
    draw_fn = SYMBOL_MAP.get(name)
    if draw_fn is None:
        raise KeyError(f"No symbol mapping for emoji: {name}")

    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    badge_box = (MARGIN, MARGIN, SIZE - MARGIN, SIZE - MARGIN)

    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    _rounded_rect(shadow_draw, (badge_box[0] + 3, badge_box[1] + 5, badge_box[2] + 3, badge_box[3] + 5), SHADOW)
    canvas = Image.alpha_composite(canvas, shadow)

    badge = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    badge.paste(_gradient_badge(badge_box), badge_box[:2])
    canvas = Image.alpha_composite(canvas, badge)

    gloss = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gloss_draw = ImageDraw.Draw(gloss)
    gloss_draw.ellipse((badge_box[0] + 8, badge_box[1] + 4, badge_box[2] - 20, badge_box[1] + 44), fill=(255, 255, 255, 55))
    canvas = Image.alpha_composite(canvas, gloss)

    draw = ImageDraw.Draw(canvas)
    draw_fn(draw, symbol_box())
    return canvas


def generate_pack(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name in EMOJI_NAMES:
        path = output_dir / f"{name}.png"
        render_emoji(name).save(path, format="PNG", optimize=True)
        written.append(path)
    return written


if __name__ == "__main__":
    out = Path("assets/emojis")
    files = generate_pack(out)
    print(f"Generated {len(files)} emoji assets in {out}")