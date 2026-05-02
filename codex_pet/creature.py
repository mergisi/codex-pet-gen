"""Parametric creature builder — used by `codex-pet creature` and as a library.

Build a Codex pet atlas from a small config dict (body color, ears, tail,
markings, etc.). All 9 animation rows are auto-generated.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional

from PIL import Image

from .atlas import (
    CELL_H,
    CELL_W,
    COLS,
    ROWS_SPEC,
    SHEET_H,
    SHEET_W,
    cell_box,
    row_index,
)

# 24x26 native pixels scaled 8x to 192x208 cells.
NATIVE_W, NATIVE_H = 24, 26
SCALE = 8

EarStyle = Literal[
    'none', 'cat', 'bunny', 'dog', 'horns', 'panda',
    'round', 'feather-tuft', 'long-down', 'unicorn',
]
TailStyle = Literal['none', 'straight', 'curl', 'puff', 'long-thin']
Markings = Literal['none', 'stripes', 'spots', 'belly-patch', 'shell']
EyeSize = Literal['small', 'big']

ROW_ORDER = [name for name, _ in ROWS_SPEC]


@dataclass
class CreatureConfig:
    body: tuple[int, int, int] = (96, 200, 100)
    accent: Optional[tuple[int, int, int]] = None
    belly_color: Optional[tuple[int, int, int]] = None
    ears: EarStyle = 'none'
    tail: TailStyle = 'none'
    markings: Markings = 'none'
    eye_size: EyeSize = 'small'
    nose: bool = True
    belly: bool = True


PRESETS: dict[str, CreatureConfig] = {
    'cat':    CreatureConfig(body=(255, 140, 60), ears='cat',   tail='curl',
                              markings='stripes', accent=(255, 150, 200)),
    'dog':    CreatureConfig(body=(200, 130, 60), ears='dog',   tail='straight',
                              markings='spots'),
    'bunny':  CreatureConfig(body=(240, 240, 240), ears='bunny', tail='puff',
                              belly_color=(255, 220, 220),
                              accent=(255, 150, 180)),
    'dragon': CreatureConfig(body=(90, 200, 100), ears='horns',  tail='straight',
                              markings='spots', accent=(200, 50, 50),
                              eye_size='big'),
    'frog':   CreatureConfig(body=(100, 200, 80), ears='none',   tail='none',
                              markings='spots', eye_size='big', nose=False),
    'pig':    CreatureConfig(body=(255, 180, 200), ears='cat',    tail='curl',
                              accent=(220, 100, 130)),
    'panda':  CreatureConfig(body=(255, 255, 255), ears='panda',  tail='puff',
                              belly_color=(250, 250, 250),
                              accent=(40, 40, 40), eye_size='big'),
    'blob':   CreatureConfig(body=(96, 200, 100)),

    # New presets — using the parts added in v0.2
    'mouse':    CreatureConfig(body=(180, 180, 180), ears='round',
                                tail='long-thin', accent=(255, 150, 180),
                                belly_color=(230, 220, 220), eye_size='small'),
    'hamster':  CreatureConfig(body=(220, 165, 100), ears='round',
                                tail='puff', accent=(255, 150, 180),
                                belly_color=(255, 230, 200)),
    'bear':     CreatureConfig(body=(120, 75, 40), ears='round',
                                tail='none', belly_color=(220, 175, 120),
                                accent=(60, 30, 10)),
    'owl':      CreatureConfig(body=(170, 110, 70), ears='feather-tuft',
                                tail='none', markings='spots',
                                belly_color=(245, 220, 180), eye_size='big'),
    'fox':      CreatureConfig(body=(255, 130, 50), ears='cat',
                                tail='puff', markings='belly-patch',
                                belly_color=(255, 245, 220),
                                accent=(60, 30, 10)),
    'sheep':    CreatureConfig(body=(245, 240, 230), ears='dog',
                                tail='puff', markings='belly-patch',
                                belly_color=(255, 252, 245),
                                accent=(70, 50, 40)),
    'unicorn':  CreatureConfig(body=(245, 230, 250), ears='unicorn',
                                tail='puff', accent=(255, 200, 100),
                                belly_color=(255, 245, 255), eye_size='big'),
    'turtle':   CreatureConfig(body=(110, 180, 100), ears='none',
                                tail='straight', markings='shell',
                                accent=(180, 130, 60), eye_size='small'),
    'elephant': CreatureConfig(body=(170, 175, 185), ears='long-down',
                                tail='straight', belly_color=(210, 215, 225),
                                accent=(255, 150, 180)),
    'devil':    CreatureConfig(body=(200, 50, 60), ears='horns',
                                tail='straight', markings='spots',
                                accent=(255, 200, 50), eye_size='big'),
}


# ---------- Color helpers ----------

def parse_hex(s: str) -> tuple[int, int, int]:
    s = s.strip().lstrip('#')
    if len(s) == 3:
        s = ''.join(c * 2 for c in s)
    if len(s) != 6:
        raise ValueError(f"invalid color: {s!r} (use #RRGGBB or #RGB)")
    try:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except ValueError as e:
        raise ValueError(f"invalid color: #{s} ({e})") from None


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _palette(cfg: CreatureConfig) -> dict[str, tuple[int, int, int, int] | None]:
    body = cfg.body + (255,)
    shadow = _lerp(cfg.body, (0, 0, 0), 0.35) + (255,)
    highlight = _lerp(cfg.body, (255, 255, 255), 0.45) + (255,)
    belly = (cfg.belly_color or _lerp(cfg.body, (255, 255, 255), 0.6)) + (255,)
    accent = (cfg.accent or (255, 130, 180)) + (255,)
    return {
        '.': None,
        'K': (0, 0, 0, 255),
        'B': body,
        'b': shadow,
        'H': highlight,
        'L': belly,
        'A': accent,
        'W': (255, 255, 255, 255),
        'D': (40, 40, 40, 255),
        'Y': (255, 230, 80, 255),
        'P': (175, 180, 195, 255),     # laptop body gray
        'p': (130, 135, 150, 255),     # laptop shadow gray
        'S': (90, 200, 240, 255),      # laptop screen glow
    }


# ---------- Drawing primitives ----------

def _blank():
    return [['.'] * NATIVE_W for _ in range(NATIVE_H)]


def _setpx(g, x, y, ch):
    if 0 <= x < NATIVE_W and 0 <= y < NATIVE_H and ch != ' ':
        g[y][x] = ch


def _rect(g, x1, y1, x2, y2, ch):
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            _setpx(g, x, y, ch)


def _draw_body(g, cfg, squash, dy):
    cx = 12
    cy = 17 + dy
    half_w = max(4, min(10, 6 + squash))
    half_h = max(3, min(8, 5 - squash))

    for ry in range(-half_h, half_h + 1):
        shrink = max(0, abs(ry) - (half_h - 2))
        w = half_w - shrink
        _rect(g, cx - w, cy + ry, cx + w, cy + ry, 'B')

    if cfg.belly:
        belly_top = cy + max(-1, -half_h + 3)
        belly_bot = cy + half_h
        belly_w = max(2, half_w - 2)
        for ry in range(belly_top, belly_bot + 1):
            shrink = max(0, abs(ry - cy) - (half_h - 2))
            w = belly_w - shrink
            if w > 0:
                _rect(g, cx - w, ry, cx + w, ry, 'L')

    _setpx(g, cx - 4, cy - half_h + 1, 'H')
    _setpx(g, cx - 3, cy - half_h + 1, 'H')
    _setpx(g, cx - 4, cy - half_h + 2, 'H')

    if cfg.markings == 'stripes':
        for stripe_x in (cx - 5, cx - 1, cx + 3):
            for ry in range(-half_h + 2, half_h - 1):
                _setpx(g, stripe_x, cy + ry, 'b')
    elif cfg.markings == 'spots':
        for sx, sy in [(cx - 3, cy - 2), (cx + 2, cy + 1), (cx - 4, cy + 2)]:
            _rect(g, sx, sy, sx + 1, sy + 1, 'b')
    elif cfg.markings == 'belly-patch':
        # large pale patch covering chest/belly (sheep, fox)
        for ry in range(-half_h + 2, half_h):
            shrink = max(0, abs(ry) - (half_h - 2))
            w = max(2, half_w - 3 - shrink)
            _rect(g, cx - w, cy + ry, cx + w, cy + ry, 'L')
    elif cfg.markings == 'shell':
        # turtle/beetle shell — accent-colored hexagonal pattern on back
        for sx, sy in [(cx - 4, cy - 1), (cx, cy - 2), (cx + 3, cy - 1),
                         (cx - 2, cy + 1), (cx + 1, cy + 2)]:
            _rect(g, sx, sy, sx + 1, sy + 1, 'A')
        for sx, sy in [(cx - 5, cy), (cx - 1, cy - 1), (cx + 2, cy)]:
            _setpx(g, sx, sy, 'b')

    for ry in range(-half_h, half_h + 1):
        shrink = max(0, abs(ry) - (half_h - 2))
        w = half_w - shrink
        _setpx(g, cx - w - 1, cy + ry, 'K')
        _setpx(g, cx + w + 1, cy + ry, 'K')
    _rect(g, cx - half_w + 1, cy - half_h - 1, cx + half_w - 1, cy - half_h - 1, 'K')
    _rect(g, cx - half_w + 1, cy + half_h + 1, cx + half_w - 1, cy + half_h + 1, 'K')

    top = cy - half_h - 1
    if cfg.ears == 'cat':
        for ex in [cx - 4, cx + 3]:
            _setpx(g, ex, top, 'B'); _setpx(g, ex + 1, top, 'B')
            _setpx(g, ex, top - 1, 'B')
            _setpx(g, ex + 1, top - 2, 'B')
            _setpx(g, ex, top - 2, 'K')
            _setpx(g, ex + 1, top - 3, 'K')
    elif cfg.ears == 'bunny':
        for ex in [cx - 4, cx + 3]:
            _rect(g, ex, top - 4, ex + 1, top, 'B')
            _setpx(g, ex, top - 5, 'B'); _setpx(g, ex + 1, top - 5, 'B')
            _setpx(g, ex - 1, top - 4, 'K'); _setpx(g, ex + 2, top - 4, 'K')
            _setpx(g, ex - 1, top - 3, 'K'); _setpx(g, ex + 2, top - 3, 'K')
            _setpx(g, ex, top - 6, 'K'); _setpx(g, ex + 1, top - 6, 'K')
            _setpx(g, ex, top - 3, 'A'); _setpx(g, ex + 1, top - 3, 'A')
    elif cfg.ears == 'dog':
        for side, ex in [(-1, cx - half_w - 1), (1, cx + half_w + 1)]:
            for ry in range(-half_h + 1, -half_h + 4):
                _setpx(g, ex + side, cy + ry, 'B')
                _setpx(g, ex, cy + ry, 'b')
                _setpx(g, ex + 2 * side, cy + ry, 'K')
    elif cfg.ears == 'horns':
        for ex in [cx - 4, cx + 3]:
            _setpx(g, ex, top, 'A'); _setpx(g, ex + 1, top, 'A')
            _setpx(g, ex, top - 1, 'A')
            _setpx(g, ex, top - 2, 'K')
            _setpx(g, ex + 1, top - 1, 'K')
    elif cfg.ears == 'panda':
        for ex in [cx - 5, cx + 4]:
            _rect(g, ex, top - 1, ex + 1, top, 'D')
            _setpx(g, ex - 1, top, 'K'); _setpx(g, ex + 2, top, 'K')
    elif cfg.ears == 'round':
        # small round body-colored ears (mouse, hamster, bear)
        for ex in [cx - 5, cx + 4]:
            _rect(g, ex, top - 1, ex + 1, top, 'B')
            _setpx(g, ex - 1, top, 'K'); _setpx(g, ex + 2, top, 'K')
            _setpx(g, ex, top - 2, 'K'); _setpx(g, ex + 1, top - 2, 'K')
            # inner pink dot
            _setpx(g, ex, top, 'A')
    elif cfg.ears == 'feather-tuft':
        # two small spike tufts on top of head (owl, demon, devil-cat)
        for ex in [cx - 5, cx + 4]:
            _setpx(g, ex, top, 'B')
            _setpx(g, ex + 1, top, 'B')
            _setpx(g, ex, top - 1, 'B')
            _setpx(g, ex - 1, top - 1, 'K')
            _setpx(g, ex, top - 2, 'K')
            _setpx(g, ex + 1, top - 1, 'K')
    elif cfg.ears == 'long-down':
        # long droopy ears hanging down past body (elephant, basset)
        for side, ex in [(-1, cx - half_w - 1), (1, cx + half_w + 1)]:
            for ry in range(-half_h + 1, -half_h + 6):
                _setpx(g, ex + side, cy + ry, 'B')
                _setpx(g, ex, cy + ry, 'B')
                _setpx(g, ex + 2 * side, cy + ry, 'K')
            _setpx(g, ex + side, cy - half_h + 6, 'K')
            _setpx(g, ex, cy - half_h + 6, 'K')
    elif cfg.ears == 'unicorn':
        # single accent-colored horn rising from forehead
        _setpx(g, cx, top, 'A')
        _setpx(g, cx + 1, top, 'A')
        _setpx(g, cx, top - 1, 'A')
        _setpx(g, cx + 1, top - 1, 'A')
        _setpx(g, cx, top - 2, 'A')
        _setpx(g, cx, top - 3, 'K')
        _setpx(g, cx - 1, top - 1, 'K')
        _setpx(g, cx + 2, top - 1, 'K')

    tx = cx + half_w + 1
    ty = cy
    if cfg.tail == 'curl':
        _rect(g, tx, ty - 1, tx + 1, ty + 1, 'B')
        _setpx(g, tx + 2, ty - 1, 'B')
        _setpx(g, tx + 2, ty + 1, 'K')
        _setpx(g, tx + 1, ty - 2, 'K')
    elif cfg.tail == 'straight':
        _rect(g, tx, ty, tx + 2, ty, 'B')
        _setpx(g, tx + 3, ty - 1, 'B')
        _setpx(g, tx, ty + 1, 'K')
        _setpx(g, tx + 3, ty, 'K')
    elif cfg.tail == 'puff':
        _rect(g, tx, ty - 1, tx + 1, ty + 1, 'L')
        _setpx(g, tx + 2, ty, 'L')
        _setpx(g, tx, ty - 2, 'K'); _setpx(g, tx, ty + 2, 'K')
    elif cfg.tail == 'long-thin':
        # mouse tail: thin curl going right and down
        for i, (dx, dy_) in enumerate([(0, 0), (1, 0), (2, 1), (3, 2),
                                          (4, 2), (4, 3), (3, 4)]):
            _setpx(g, tx + dx, ty + dy_, 'A')
        # outline
        for dx, dy_ in [(0, -1), (1, -1), (2, 0), (3, 1), (4, 1),
                          (5, 2), (5, 3), (4, 4), (3, 5)]:
            _setpx(g, tx + dx, ty + dy_, 'K')
    return cy, half_h


def _draw_face(g, cfg, cy, half_h, eye, look, mouth):
    cx = 12
    eye_y = cy - half_h + 4
    lex, rex = cx - 3, cx + 2
    if eye == 'closed':
        _rect(g, lex, eye_y, lex + 1, eye_y, 'D')
        _rect(g, rex, eye_y, rex + 1, eye_y, 'D')
    elif eye == 'x':
        for dx_, dy_ in [(0, 0), (1, 0), (0, 1), (1, 1)]:
            _setpx(g, lex + dx_, eye_y + dy_ - 1, 'D')
            _setpx(g, rex + dx_, eye_y + dy_ - 1, 'D')
    elif eye == 'wide' or cfg.eye_size == 'big':
        _rect(g, lex, eye_y - 1, lex + 1, eye_y + 1, 'W')
        _rect(g, rex, eye_y - 1, rex + 1, eye_y + 1, 'W')
        _setpx(g, lex + (1 if look > 0 else 0), eye_y, 'D')
        _setpx(g, rex + (1 if look > 0 else 0), eye_y, 'D')
        for ex in [lex, rex]:
            _setpx(g, ex - 1, eye_y, 'K'); _setpx(g, ex + 2, eye_y, 'K')
    else:
        _rect(g, lex, eye_y, lex + 1, eye_y, 'W')
        _rect(g, rex, eye_y, rex + 1, eye_y, 'W')
        if look < 0:
            _setpx(g, lex, eye_y, 'D'); _setpx(g, rex, eye_y, 'D')
        elif look > 0:
            _setpx(g, lex + 1, eye_y, 'D'); _setpx(g, rex + 1, eye_y, 'D')
        else:
            _setpx(g, lex + 1, eye_y, 'D'); _setpx(g, rex, eye_y, 'D')

    if cfg.nose:
        _setpx(g, cx, eye_y + 1, 'A')
        _setpx(g, cx + 1, eye_y + 1, 'A')

    if mouth == 'small':
        _setpx(g, cx, eye_y + 2, 'D'); _setpx(g, cx + 1, eye_y + 2, 'D')
    elif mouth == 'open':
        _rect(g, cx - 1, eye_y + 2, cx + 2, eye_y + 3, 'D')
    elif mouth == 'frown':
        _rect(g, cx - 1, eye_y + 3, cx + 2, eye_y + 3, 'D')
        _setpx(g, cx - 2, eye_y + 2, 'D'); _setpx(g, cx + 3, eye_y + 2, 'D')
    elif mouth == 'smile':
        _setpx(g, cx - 1, eye_y + 3, 'D'); _setpx(g, cx + 2, eye_y + 3, 'D')
        _rect(g, cx, eye_y + 2, cx + 1, eye_y + 2, 'D')


def _stars_overlay(g):
    for x, y in [(5, 8), (18, 7), (4, 14)]:
        _setpx(g, x, y, 'Y')


# Per-frame star variants for the dizzy animation — different positions
# so the failed loop has visible motion.
def _stars_a(g):
    for x, y in [(5, 7), (18, 8), (4, 13)]:
        _setpx(g, x, y, 'Y')


def _stars_b(g):
    for x, y in [(6, 5), (19, 7), (5, 14)]:
        _setpx(g, x, y, 'Y')


def _stars_c(g):
    for x, y in [(4, 6), (17, 5), (6, 12)]:
        _setpx(g, x, y, 'Y')


def _stars_d(g):
    for x, y in [(7, 8), (20, 9), (3, 13)]:
        _setpx(g, x, y, 'Y')


def _laptop(g, typing=False):
    """Compact 3/4-view laptop in the bottom-LEFT, mirroring the Codex pet
    "running" state where the pet leans over a side laptop.

    Footprint: x=2..13, y=19..25 (left half of the cell).
    The pet body stays centered and visible; the laptop occupies the left
    foreground while the pet leans/looks toward it.
    """
    # SCREEN (visible from the right side — back panel angles away)
    # Top outline
    _rect(g, 4, 19, 12, 19, 'K')
    # Screen back panel (dark)
    _rect(g, 4, 20, 12, 20, 'D')
    _rect(g, 4, 21, 4, 22, 'D')             # left side bezel
    _rect(g, 12, 21, 12, 22, 'D')           # right side bezel
    # Cyan screen content
    _rect(g, 5, 21, 11, 22, 'S')
    # Screen logo / typing indicator (a small bright blip)
    if typing:
        _setpx(g, 6, 21, 'W'); _setpx(g, 7, 21, 'W')
        _setpx(g, 9, 22, 'W')
    else:
        _setpx(g, 8, 21, 'W')               # idle screen logo
        _setpx(g, 8, 22, 'W')
    # Screen bottom edge
    _rect(g, 4, 23, 12, 23, 'K')

    # KEYBOARD — wider lid base than screen, sits at angle
    # Outline
    _rect(g, 2, 24, 13, 24, 'K')            # top edge of base (hinge line)
    _rect(g, 1, 25, 14, 25, 'K')            # bottom edge

    # Lid / base face
    _rect(g, 3, 24, 12, 24, 'P')
    _rect(g, 2, 25, 13, 25, 'p')

    # Key indicators across keyboard top
    for kx in (4, 6, 8, 10, 12):
        _setpx(g, kx, 24, 'D')
    # Trackpad hint
    _setpx(g, 7, 25, 'D'); _setpx(g, 8, 25, 'D')


def _laptop_a(g):
    _laptop(g, typing=True)


def _laptop_b(g):
    _laptop(g, typing=False)


def _draw_arms(g, cfg, cy, half_h, half_w, arm_l='down', arm_r='down'):
    """Two small paws/arms sticking out the sides of the body.
    Poses: 'down' 'up' 'wave' 'forward' 'back' 'akimbo' 'reach'."""
    # Anchor: shoulder y is at upper body, paw color is body 'B', mitt is 'L'.
    base_y = cy + 1   # default arm hang line
    for side, ax, pose in [(-1, cx_for_side(cfg, half_w, -1), arm_l),
                            (+1, cx_for_side(cfg, half_w, +1), arm_r)]:
        if pose == 'none':
            continue
        if pose == 'down':
            _setpx(g, ax, base_y, 'B')
            _setpx(g, ax, base_y + 1, 'L')
            _setpx(g, ax + side, base_y + 1, 'K')
            _setpx(g, ax, base_y + 2, 'K')
        elif pose == 'wave':
            # arm raised diagonal up & out
            _setpx(g, ax, base_y - 1, 'B')
            _setpx(g, ax + side, base_y - 2, 'B')
            _setpx(g, ax + 2 * side, base_y - 3, 'L')
            _setpx(g, ax + side, base_y - 1, 'K')
            _setpx(g, ax + 2 * side, base_y - 2, 'K')
            _setpx(g, ax + 3 * side, base_y - 3, 'K')
            _setpx(g, ax + 2 * side, base_y - 4, 'K')
        elif pose == 'up':
            # straight up
            _setpx(g, ax, base_y - 1, 'B')
            _setpx(g, ax, base_y - 2, 'B')
            _setpx(g, ax, base_y - 3, 'L')
            _setpx(g, ax + side, base_y - 1, 'K')
            _setpx(g, ax - side, base_y - 1, 'K')
            _setpx(g, ax, base_y - 4, 'K')
        elif pose == 'forward':
            # arm pointing forward (across body)
            _setpx(g, ax - side, base_y, 'B')
            _setpx(g, ax - 2 * side, base_y, 'L')
            _setpx(g, ax - side, base_y - 1, 'K')
            _setpx(g, ax - 2 * side, base_y - 1, 'K')
            _setpx(g, ax - 3 * side, base_y, 'K')
            _setpx(g, ax - 2 * side, base_y + 1, 'K')
        elif pose == 'back':
            # arm back & up (running counter-balance)
            _setpx(g, ax + side, base_y - 1, 'B')
            _setpx(g, ax + 2 * side, base_y - 2, 'L')
            _setpx(g, ax + side, base_y - 2, 'K')
            _setpx(g, ax + 2 * side, base_y - 3, 'K')
            _setpx(g, ax + 3 * side, base_y - 2, 'K')
        elif pose == 'akimbo':
            # elbow out, paw on hip
            _setpx(g, ax + side, base_y, 'B')
            _setpx(g, ax + side, base_y + 1, 'L')
            _setpx(g, ax + 2 * side, base_y, 'K')
            _setpx(g, ax + 2 * side, base_y + 1, 'K')
            _setpx(g, ax, base_y + 2, 'K')
        elif pose == 'reach':
            # both forward & slightly up (peering)
            _setpx(g, ax - side, base_y - 1, 'B')
            _setpx(g, ax - 2 * side, base_y - 1, 'L')
            _setpx(g, ax - side, base_y - 2, 'K')
            _setpx(g, ax - 3 * side, base_y - 1, 'K')
            _setpx(g, ax - 2 * side, base_y, 'K')
        elif pose == 'type-left':
            # Both arms angle DOWN-LEFT toward the side laptop's keyboard.
            # Used for the running state. Side flag still drives outline x.
            shoulder_x = ax
            # Forearm goes down and to the left
            _setpx(g, shoulder_x, base_y + 1, 'B')
            _setpx(g, shoulder_x - 1, base_y + 2, 'B')
            _setpx(g, shoulder_x - 2, base_y + 3, 'B')
            # Hand on keyboard
            _setpx(g, shoulder_x - 3, base_y + 4, 'L')
            _setpx(g, shoulder_x - 4, base_y + 4, 'L')
            # Outline
            _setpx(g, shoulder_x + 1, base_y + 1, 'K')
            _setpx(g, shoulder_x, base_y + 2, 'K')
            _setpx(g, shoulder_x - 1, base_y + 3, 'K')
            _setpx(g, shoulder_x - 2, base_y + 4, 'K')
            _setpx(g, shoulder_x - 3, base_y + 5, 'K')
            _setpx(g, shoulder_x - 4, base_y + 5, 'K')
            _setpx(g, shoulder_x - 5, base_y + 4, 'K')


def cx_for_side(cfg, half_w, side):
    """Anchor x for a side arm (just outside the body silhouette)."""
    cx = 12
    return cx + side * (half_w + 1)


def _draw_feet(g, cfg, cy, half_h, half_w, pose='stand'):
    """Tiny feet just below the body. Poses: stand, lift-r, lift-l, split, tuck."""
    fy = cy + half_h + 1
    lx, rx = 12 - 3, 12 + 2
    if pose == 'tuck':
        return
    if pose == 'stand':
        _setpx(g, lx, fy, 'D'); _setpx(g, lx + 1, fy, 'D')
        _setpx(g, rx, fy, 'D'); _setpx(g, rx + 1, fy, 'D')
    elif pose == 'lift-r':
        _setpx(g, lx, fy, 'D'); _setpx(g, lx + 1, fy, 'D')
        _setpx(g, rx, fy - 1, 'D'); _setpx(g, rx + 1, fy - 1, 'D')
    elif pose == 'lift-l':
        _setpx(g, lx, fy - 1, 'D'); _setpx(g, lx + 1, fy - 1, 'D')
        _setpx(g, rx, fy, 'D'); _setpx(g, rx + 1, fy, 'D')
    elif pose == 'split':
        _setpx(g, lx - 1, fy, 'D'); _setpx(g, lx, fy, 'D')
        _setpx(g, rx + 1, fy, 'D'); _setpx(g, rx + 2, fy, 'D')


def _frame(cfg, squash=0, dy=0, eye='open', look=0, mouth='small',
            arm_l='down', arm_r='down', feet='stand', extra=None):
    g = _blank()
    cy, half_h = _draw_body(g, cfg, squash=squash, dy=dy)
    half_w = max(4, min(10, 6 + squash))
    _draw_arms(g, cfg, cy, half_h, half_w, arm_l=arm_l, arm_r=arm_r)
    _draw_feet(g, cfg, cy, half_h, half_w, pose=feet)
    _draw_face(g, cfg, cy, half_h, eye=eye, look=look, mouth=mouth)
    if extra:
        extra(g)
    return g


def _make_anims(cfg):
    """Each row picks DISTINCT arm/feet poses so silhouettes differ per state."""
    return {
        'idle': [
            _frame(cfg, arm_l='down', arm_r='down'),
            _frame(cfg, squash=1, arm_l='down', arm_r='down'),
            _frame(cfg, arm_l='down', arm_r='down'),
            _frame(cfg, squash=1, arm_l='down', arm_r='down'),
            _frame(cfg, eye='closed', arm_l='down', arm_r='down'),
            _frame(cfg, arm_l='down', arm_r='down'),
        ],
        'running-right': [
            # Run cycle: alternating arms (L-forward/R-back) + leg lift
            _frame(cfg, squash=-1, dy=-1, mouth='open',
                   arm_l='forward', arm_r='back', feet='lift-r'),
            _frame(cfg, squash=0, mouth='open',
                   arm_l='forward', arm_r='back', feet='split'),
            _frame(cfg, squash=1, mouth='open',
                   arm_l='back', arm_r='forward', feet='lift-l'),
            _frame(cfg, squash=0, mouth='open',
                   arm_l='back', arm_r='forward', feet='split'),
            _frame(cfg, squash=-1, dy=-1, mouth='open',
                   arm_l='forward', arm_r='back', feet='lift-r'),
            _frame(cfg, squash=0, mouth='open',
                   arm_l='forward', arm_r='back', feet='split'),
            _frame(cfg, squash=1, mouth='open',
                   arm_l='back', arm_r='forward', feet='lift-l'),
            _frame(cfg, squash=0, mouth='open',
                   arm_l='back', arm_r='forward', feet='split'),
        ],
        'running-left': [],   # auto-mirrored from running-right
        'waving': [
            # Right arm waves up/wide; left arm hangs
            _frame(cfg, eye='wide', look=1, mouth='smile',
                   arm_l='down', arm_r='wave'),
            _frame(cfg, eye='wide', look=1, mouth='smile',
                   arm_l='down', arm_r='up', dy=-1),
            _frame(cfg, eye='wide', look=1, mouth='smile',
                   arm_l='down', arm_r='wave'),
            _frame(cfg, eye='wide', look=1, mouth='smile',
                   arm_l='down', arm_r='up', dy=-1),
        ],
        'jumping': [
            # crouch -> launch -> peak (arms up) -> falling -> land
            _frame(cfg, squash=2, mouth='small',
                   arm_l='down', arm_r='down', feet='stand'),
            _frame(cfg, squash=-1, dy=-2, eye='wide', mouth='open',
                   arm_l='up', arm_r='up', feet='lift-r'),
            _frame(cfg, squash=-2, dy=-3, eye='wide', mouth='open',
                   arm_l='up', arm_r='up', feet='tuck'),
            _frame(cfg, squash=-1, dy=-2, eye='wide', mouth='open',
                   arm_l='reach', arm_r='reach', feet='split'),
            _frame(cfg, squash=2, mouth='frown',
                   arm_l='down', arm_r='down', feet='stand'),
        ],
        'failed': [
            # Dizzy/stunned — body sways, stars rotate around head, blinks.
            _frame(cfg, squash=2, dy=0,  eye='x',      mouth='frown',
                   arm_l='down', arm_r='down', extra=_stars_a),
            _frame(cfg, squash=2, dy=-1, eye='x',      mouth='frown',
                   arm_l='down', arm_r='down', extra=_stars_b),
            _frame(cfg, squash=1, dy=0,  eye='x',      mouth='frown',
                   arm_l='down', arm_r='down', extra=_stars_c),
            _frame(cfg, squash=2, dy=0,  eye='x',      mouth='frown',
                   arm_l='down', arm_r='down', extra=_stars_d),
            _frame(cfg, squash=2, dy=-1, eye='closed', mouth='frown',
                   arm_l='down', arm_r='down', extra=_stars_a),
            _frame(cfg, squash=1, dy=0,  eye='x',      mouth='frown',
                   arm_l='down', arm_r='down', extra=_stars_b),
            _frame(cfg, squash=2, dy=0,  eye='x',      mouth='frown',
                   arm_l='down', arm_r='down', extra=_stars_c),
            _frame(cfg, squash=2, dy=-1, eye='x',      mouth='frown',
                   arm_l='down', arm_r='down', extra=_stars_d),
        ],
        'waiting': [
            # Hands on hips, looking around, blinks. Alternating foot tap.
            _frame(cfg, look=1, arm_l='akimbo', arm_r='akimbo', feet='stand'),
            _frame(cfg, look=1, arm_l='akimbo', arm_r='akimbo', feet='lift-r'),
            _frame(cfg, look=0, arm_l='akimbo', arm_r='akimbo', feet='stand'),
            _frame(cfg, look=-1, arm_l='akimbo', arm_r='akimbo', feet='stand'),
            _frame(cfg, look=-1, arm_l='akimbo', arm_r='akimbo', feet='lift-l'),
            _frame(cfg, eye='closed', arm_l='akimbo', arm_r='akimbo', feet='stand'),
        ],
        'running': [
            # "Code is running" — pet leans toward a side laptop on the left,
            # both arms reach down-left to the keyboard, eyes mostly closed
            # (focused). Screen content blinks while typing.
            _frame(cfg, squash=0, dy=0, eye='closed', look=-1,
                   arm_l='type-left', arm_r='type-left', feet='tuck',
                   extra=_laptop_a),
            _frame(cfg, squash=0, dy=0, eye='closed', look=-1,
                   arm_l='type-left', arm_r='type-left', feet='tuck',
                   extra=_laptop_b),
            _frame(cfg, squash=0, dy=-1, eye='open', look=-1,
                   arm_l='type-left', arm_r='type-left', feet='tuck',
                   extra=_laptop_a),
            _frame(cfg, squash=0, dy=0, eye='closed', look=-1,
                   arm_l='type-left', arm_r='type-left', feet='tuck',
                   extra=_laptop_b),
            _frame(cfg, squash=0, dy=0, eye='open', look=-1,
                   arm_l='type-left', arm_r='type-left', feet='tuck',
                   extra=_laptop_a),
            _frame(cfg, squash=0, dy=-1, eye='closed', look=-1,
                   arm_l='type-left', arm_r='type-left', feet='tuck',
                   extra=_laptop_b),
        ],
        'review': [
            # Leaning forward, both arms reaching/peering
            _frame(cfg, eye='wide', look=1, arm_l='reach', arm_r='reach'),
            _frame(cfg, eye='wide', look=1, arm_l='reach', arm_r='reach', dy=-1),
            _frame(cfg, eye='wide', look=-1, arm_l='reach', arm_r='reach'),
            _frame(cfg, eye='wide', look=-1, arm_l='reach', arm_r='reach', dy=-1),
            _frame(cfg, eye='wide', look=1, arm_l='reach', arm_r='reach'),
            _frame(cfg, eye='closed', arm_l='reach', arm_r='reach'),
        ],
    }


def _grid_to_image(grid, palette):
    img = Image.new('RGBA', (NATIVE_W, NATIVE_H), (0, 0, 0, 0))
    px = img.load()
    for y in range(NATIVE_H):
        for x in range(NATIVE_W):
            c = palette.get(grid[y][x])
            if c is not None:
                px[x, y] = c
    return img.resize((CELL_W, CELL_H), Image.NEAREST)


def build_atlas(cfg: CreatureConfig) -> Image.Image:
    """Build a 1536x1872 atlas image from a CreatureConfig."""
    palette = _palette(cfg)
    sheet = Image.new('RGBA', (SHEET_W, SHEET_H), (0, 0, 0, 0))
    anims = _make_anims(cfg)
    for r_idx, name in enumerate(ROW_ORDER):
        for c_idx, f in enumerate(anims.get(name, [])[:COLS]):
            cell = _grid_to_image(f, palette)
            sheet.paste(cell, (c_idx * CELL_W, r_idx * CELL_H), cell)
    src_y = ROW_ORDER.index('running-right') * CELL_H
    dst_y = ROW_ORDER.index('running-left') * CELL_H
    for c in range(COLS):
        cell = sheet.crop((c * CELL_W, src_y, (c + 1) * CELL_W, src_y + CELL_H))
        if cell.getbbox() is None:
            continue
        sheet.paste(cell.transpose(Image.FLIP_LEFT_RIGHT), (c * CELL_W, dst_y))
    return sheet


def config_from_args(
    preset: Optional[str] = None,
    body: Optional[str] = None,
    accent: Optional[str] = None,
    belly_color: Optional[str] = None,
    ears: Optional[str] = None,
    tail: Optional[str] = None,
    markings: Optional[str] = None,
    eye_size: Optional[str] = None,
    no_nose: bool = False,
    no_belly: bool = False,
) -> CreatureConfig:
    """Resolve a CreatureConfig from CLI-style args."""
    if preset:
        if preset not in PRESETS:
            raise ValueError(
                f"unknown preset {preset!r}. available: {', '.join(sorted(PRESETS))}"
            )
        cfg = CreatureConfig(**asdict(PRESETS[preset]))
    else:
        cfg = CreatureConfig()

    if body is not None:
        cfg.body = parse_hex(body)
    if accent is not None:
        cfg.accent = parse_hex(accent)
    if belly_color is not None:
        cfg.belly_color = parse_hex(belly_color)
    if ears is not None:
        cfg.ears = ears
    if tail is not None:
        cfg.tail = tail
    if markings is not None:
        cfg.markings = markings
    if eye_size is not None:
        cfg.eye_size = eye_size
    if no_nose:
        cfg.nose = False
    if no_belly:
        cfg.belly = False
    return cfg
