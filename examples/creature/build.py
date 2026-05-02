#!/usr/bin/env python3
"""Creature — parametric pet builder.

Pick a PRESET below (or add your own to PRESETS at the bottom) and run:

    python build.py
    codex-pet preview spritesheet.webp
    codex-pet install spritesheet.webp --name "MyPet"

Each preset is a dict of knobs: body color, ears, tail, eyes, belly,
markings. The drawing code at the bottom turns those knobs into all 9
animation rows automatically — no per-frame work required.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image

# =============================================================================
#                 ▶  EDIT THIS LINE TO PICK YOUR ANIMAL  ◀
# =============================================================================
PRESET = 'cat'   # try: 'cat', 'dog', 'bunny', 'dragon', 'frog', 'pig', 'panda'
# =============================================================================


# 24x26 native pixels, scaled 8x to 192x208 cells.
NATIVE_W, NATIVE_H = 24, 26
SCALE = 8
CELL_W, CELL_H = NATIVE_W * SCALE, NATIVE_H * SCALE
COLS, ROWS = 8, 9
SHEET_W, SHEET_H = COLS * CELL_W, ROWS * CELL_H


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def derive_palette(body_rgb, accent_rgb=None, belly_rgb=None):
    """Build the full PALETTE dict from a base body color."""
    body = body_rgb + (255,)
    shadow = lerp_color(body_rgb, (0, 0, 0), 0.35) + (255,)
    highlight = lerp_color(body_rgb, (255, 255, 255), 0.45) + (255,)
    belly = (belly_rgb or lerp_color(body_rgb, (255, 255, 255), 0.6)) + (255,)
    accent = (accent_rgb or (255, 130, 180)) + (255,)
    return {
        '.': None,
        'K': (0, 0, 0, 255),
        'B': body,
        'b': shadow,
        'H': highlight,
        'L': belly,                # belly / lighter patch
        'A': accent,               # nose / cheek / accent
        'W': (255, 255, 255, 255),
        'D': (40, 40, 40, 255),    # dark detail (mouth, pupils, stripes)
        'Y': (255, 230, 80, 255),  # dizzy stars
    }


# ---------- Drawing primitives ----------

def blank():
    return [['.'] * NATIVE_W for _ in range(NATIVE_H)]


def setpx(g, x, y, ch):
    if 0 <= x < NATIVE_W and 0 <= y < NATIVE_H and ch != ' ':
        g[y][x] = ch


def rect(g, x1, y1, x2, y2, ch):
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            setpx(g, x, y, ch)


# ---------- Creature body ----------

def draw_body(g, cfg, squash=0, dy=0):
    """Round body with belly patch, ears, tail, markings — all from cfg."""
    cx = 12
    cy = 17 + dy

    half_w = max(4, min(10, 6 + squash))
    half_h = max(3, min(8, 5 - squash))

    # Body fill — rounded rectangle
    for ry in range(-half_h, half_h + 1):
        shrink = max(0, abs(ry) - (half_h - 2))
        w = half_w - shrink
        rect(g, cx - w, cy + ry, cx + w, cy + ry, 'B')

    # Belly patch (lighter)
    if cfg.get('belly', True):
        belly_top = cy + max(-1, -half_h + 3)
        belly_bot = cy + half_h
        belly_w = max(2, half_w - 2)
        for ry in range(belly_top, belly_bot + 1):
            shrink = max(0, abs(ry - cy) - (half_h - 2))
            w = belly_w - shrink
            if w > 0:
                rect(g, cx - w, ry, cx + w, ry, 'L')

    # Highlight (top-left specular)
    setpx(g, cx - 4, cy - half_h + 1, 'H')
    setpx(g, cx - 3, cy - half_h + 1, 'H')
    setpx(g, cx - 4, cy - half_h + 2, 'H')

    # Markings
    if cfg.get('markings') == 'stripes':
        for stripe_x in (cx - 5, cx - 1, cx + 3):
            for ry in range(-half_h + 2, half_h - 1):
                setpx(g, stripe_x, cy + ry, 'b')
    elif cfg.get('markings') == 'spots':
        for sx, sy in [(cx - 3, cy - 2), (cx + 2, cy + 1), (cx - 4, cy + 2)]:
            rect(g, sx, sy, sx + 1, sy + 1, 'b')

    # Outline ring
    for ry in range(-half_h, half_h + 1):
        shrink = max(0, abs(ry) - (half_h - 2))
        w = half_w - shrink
        setpx(g, cx - w - 1, cy + ry, 'K')
        setpx(g, cx + w + 1, cy + ry, 'K')
    rect(g, cx - half_w + 1, cy - half_h - 1, cx + half_w - 1, cy - half_h - 1, 'K')
    rect(g, cx - half_w + 1, cy + half_h + 1, cx + half_w - 1, cy + half_h + 1, 'K')

    # Ears
    ear = cfg.get('ears', 'none')
    top = cy - half_h - 1
    if ear == 'cat':
        # Two triangular ears
        for i, ex in enumerate([cx - 4, cx + 3]):
            setpx(g, ex, top, 'B'); setpx(g, ex + 1, top, 'B')
            setpx(g, ex, top - 1, 'B')
            setpx(g, ex + 1, top - 2, 'B')
            setpx(g, ex, top - 2, 'K')
            setpx(g, ex + 1, top - 3, 'K')
    elif ear == 'bunny':
        for ex in [cx - 4, cx + 3]:
            rect(g, ex, top - 4, ex + 1, top, 'B')
            setpx(g, ex, top - 5, 'B'); setpx(g, ex + 1, top - 5, 'B')
            # outline
            setpx(g, ex - 1, top - 4, 'K'); setpx(g, ex + 2, top - 4, 'K')
            setpx(g, ex - 1, top - 3, 'K'); setpx(g, ex + 2, top - 3, 'K')
            setpx(g, ex, top - 6, 'K'); setpx(g, ex + 1, top - 6, 'K')
            # pink inner
            setpx(g, ex, top - 3, 'A'); setpx(g, ex + 1, top - 3, 'A')
    elif ear == 'dog':
        # Floppy ears hanging down sides of head
        for side, ex in [(-1, cx - half_w - 1), (1, cx + half_w + 1)]:
            for ry in range(-half_h + 1, -half_h + 4):
                setpx(g, ex + side, cy + ry, 'B')
                setpx(g, ex, cy + ry, 'b')
                setpx(g, ex + 2 * side, cy + ry, 'K')
    elif ear == 'horns':
        for ex in [cx - 4, cx + 3]:
            setpx(g, ex, top, 'A'); setpx(g, ex + 1, top, 'A')
            setpx(g, ex, top - 1, 'A')
            setpx(g, ex, top - 2, 'K')
            setpx(g, ex + 1, top - 1, 'K')
    elif ear == 'panda':
        for ex in [cx - 5, cx + 4]:
            rect(g, ex, top - 1, ex + 1, top, 'D')
            setpx(g, ex - 1, top, 'K'); setpx(g, ex + 2, top, 'K')

    # Tail
    tail = cfg.get('tail', 'none')
    tx = cx + half_w + 1
    ty = cy
    if tail == 'curl':
        rect(g, tx, ty - 1, tx + 1, ty + 1, 'B')
        setpx(g, tx + 2, ty - 1, 'B')
        setpx(g, tx + 2, ty + 1, 'K')
        setpx(g, tx + 1, ty - 2, 'K')
    elif tail == 'straight':
        rect(g, tx, ty, tx + 2, ty, 'B')
        setpx(g, tx + 3, ty - 1, 'B')
        setpx(g, tx, ty + 1, 'K')
        setpx(g, tx + 3, ty, 'K')
    elif tail == 'puff':
        rect(g, tx, ty - 1, tx + 1, ty + 1, 'L')
        setpx(g, tx + 2, ty, 'L')
        setpx(g, tx, ty - 2, 'K'); setpx(g, tx, ty + 2, 'K')

    return cy, half_h


def draw_face(g, cfg, cy, half_h, eye='open', look=0, mouth='small', dy=0):
    """Eyes + nose + mouth on the body."""
    cx = 12
    eye_y = cy - half_h + 4
    lex, rex = cx - 3, cx + 2
    eye_size = cfg.get('eye_size', 'small')

    if eye == 'closed':
        rect(g, lex, eye_y, lex + 1, eye_y, 'D')
        rect(g, rex, eye_y, rex + 1, eye_y, 'D')
    elif eye == 'x':
        for dx_, dy_ in [(0, 0), (1, 0), (0, 1), (1, 1)]:
            setpx(g, lex + dx_, eye_y + dy_ - 1, 'D')
            setpx(g, rex + dx_, eye_y + dy_ - 1, 'D')
    elif eye == 'wide' or eye_size == 'big':
        rect(g, lex, eye_y - 1, lex + 1, eye_y + 1, 'W')
        rect(g, rex, eye_y - 1, rex + 1, eye_y + 1, 'W')
        setpx(g, lex + (1 if look > 0 else 0), eye_y, 'D')
        setpx(g, rex + (1 if look > 0 else 0), eye_y, 'D')
        # outline around eyes for big-eye creatures
        for ex in [lex, rex]:
            setpx(g, ex - 1, eye_y, 'K'); setpx(g, ex + 2, eye_y, 'K')
    else:
        rect(g, lex, eye_y, lex + 1, eye_y, 'W')
        rect(g, rex, eye_y, rex + 1, eye_y, 'W')
        if look < 0:
            setpx(g, lex, eye_y, 'D'); setpx(g, rex, eye_y, 'D')
        elif look > 0:
            setpx(g, lex + 1, eye_y, 'D'); setpx(g, rex + 1, eye_y, 'D')
        else:
            setpx(g, lex + 1, eye_y, 'D'); setpx(g, rex, eye_y, 'D')

    # Nose
    if cfg.get('nose', True):
        setpx(g, cx, eye_y + 1, 'A')
        setpx(g, cx + 1, eye_y + 1, 'A')

    # Mouth
    if mouth == 'small':
        setpx(g, cx, eye_y + 2, 'D')
        setpx(g, cx + 1, eye_y + 2, 'D')
    elif mouth == 'open':
        rect(g, cx - 1, eye_y + 2, cx + 2, eye_y + 3, 'D')
    elif mouth == 'frown':
        rect(g, cx - 1, eye_y + 3, cx + 2, eye_y + 3, 'D')
        setpx(g, cx - 2, eye_y + 2, 'D'); setpx(g, cx + 3, eye_y + 2, 'D')
    elif mouth == 'smile':
        setpx(g, cx - 1, eye_y + 3, 'D'); setpx(g, cx + 2, eye_y + 3, 'D')
        rect(g, cx, eye_y + 2, cx + 1, eye_y + 2, 'D')


def stars_overlay(g):
    """Tiny yellow stars touching the body silhouette (failed state)."""
    for x, y in [(5, 8), (18, 7), (4, 14)]:
        setpx(g, x, y, 'Y')


def frame(cfg, squash=0, dy=0, eye='open', look=0, mouth='small', extra=None):
    g = blank()
    cy, half_h = draw_body(g, cfg, squash=squash, dy=dy)
    draw_face(g, cfg, cy, half_h, eye=eye, look=look, mouth=mouth, dy=dy)
    if extra:
        extra(g)
    return g


# ---------- Animation rows (auto-generated from cfg) ----------

def make_anims(cfg):
    return {
        'idle': [frame(cfg), frame(cfg, squash=1),
                 frame(cfg), frame(cfg, squash=1),
                 frame(cfg, eye='closed'), frame(cfg)],
        'running-right': [
            frame(cfg, squash=-1, dy=-1, mouth='open'),
            frame(cfg, squash=0, mouth='open'),
            frame(cfg, squash=1, mouth='open'),
            frame(cfg, squash=0, mouth='open'),
            frame(cfg, squash=-1, dy=-1, mouth='open'),
            frame(cfg, squash=0, mouth='open'),
            frame(cfg, squash=1, mouth='open'),
            frame(cfg, squash=0, mouth='open'),
        ],
        'running-left': [],  # auto-mirrored from running-right
        'waving': [frame(cfg, eye='wide', look=1, mouth='smile'),
                   frame(cfg, eye='wide', look=-1, mouth='smile'),
                   frame(cfg, eye='wide', look=1, mouth='smile'),
                   frame(cfg, eye='wide', look=-1, mouth='smile')],
        'jumping': [frame(cfg, squash=2, mouth='small'),
                    frame(cfg, squash=-1, dy=-2, eye='wide', mouth='open'),
                    frame(cfg, squash=-2, dy=-3, eye='wide', mouth='open'),
                    frame(cfg, squash=-1, dy=-2, eye='wide', mouth='open'),
                    frame(cfg, squash=2, mouth='frown')],
        'failed': [frame(cfg, squash=2, eye='x', mouth='frown', extra=stars_overlay)] * 8,
        'waiting': [frame(cfg, look=1), frame(cfg, look=1, eye='closed'),
                    frame(cfg, look=-1), frame(cfg, look=-1, eye='closed'),
                    frame(cfg), frame(cfg, eye='closed')],
        'running': [frame(cfg, squash=-1, dy=-1), frame(cfg, squash=0),
                    frame(cfg, squash=1), frame(cfg, squash=0),
                    frame(cfg, squash=-1, dy=-1), frame(cfg, squash=0)],
        'review': [frame(cfg, eye='wide', look=1),
                   frame(cfg, eye='wide', look=1),
                   frame(cfg, eye='wide', look=-1),
                   frame(cfg, eye='wide', look=-1),
                   frame(cfg, eye='wide', look=1),
                   frame(cfg, eye='closed')],
    }


ROW_ORDER = ['idle', 'running-right', 'running-left', 'waving', 'jumping',
             'failed', 'waiting', 'running', 'review']


def grid_to_image(grid, palette):
    img = Image.new('RGBA', (NATIVE_W, NATIVE_H), (0, 0, 0, 0))
    px = img.load()
    for y in range(NATIVE_H):
        for x in range(NATIVE_W):
            c = palette.get(grid[y][x])
            if c is not None:
                px[x, y] = c
    return img.resize((CELL_W, CELL_H), Image.NEAREST)


def build(cfg):
    palette = derive_palette(
        cfg['body'],
        accent_rgb=cfg.get('accent'),
        belly_rgb=cfg.get('belly_color'),
    )
    sheet = Image.new('RGBA', (SHEET_W, SHEET_H), (0, 0, 0, 0))
    anims = make_anims(cfg)
    for r_idx, name in enumerate(ROW_ORDER):
        for c_idx, f in enumerate(anims.get(name, [])[:COLS]):
            cell = grid_to_image(f, palette)
            sheet.paste(cell, (c_idx * CELL_W, r_idx * CELL_H), cell)
    # Mirror running-right -> running-left
    src_y = ROW_ORDER.index('running-right') * CELL_H
    dst_y = ROW_ORDER.index('running-left') * CELL_H
    for c in range(COLS):
        cell = sheet.crop((c * CELL_W, src_y, (c + 1) * CELL_W, src_y + CELL_H))
        if cell.getbbox() is None:
            continue
        sheet.paste(cell.transpose(Image.FLIP_LEFT_RIGHT), (c * CELL_W, dst_y))
    return sheet


# =============================================================================
#                                  PRESETS
# =============================================================================
# Add your own animal here. The keys understood by the builder:
#   body         (R,G,B)            — main body color
#   accent       (R,G,B) optional   — nose/horn color
#   belly_color  (R,G,B) optional   — belly patch color (auto if omitted)
#   ears         'none' | 'cat' | 'bunny' | 'dog' | 'horns' | 'panda'
#   tail         'none' | 'straight' | 'curl' | 'puff'
#   markings     'none' | 'stripes' | 'spots'
#   eye_size     'small' | 'big'
#   nose         True | False
#   belly        True | False
# =============================================================================

PRESETS = {
    'cat':     {'body': (255, 140, 60), 'ears': 'cat',    'tail': 'curl',
                'markings': 'stripes', 'accent': (255, 150, 200)},
    'dog':     {'body': (200, 130, 60), 'ears': 'dog',    'tail': 'straight',
                'markings': 'spots'},
    'bunny':   {'body': (240, 240, 240), 'ears': 'bunny', 'tail': 'puff',
                'belly_color': (255, 220, 220), 'accent': (255, 150, 180)},
    'dragon':  {'body': (90, 200, 100), 'ears': 'horns',  'tail': 'straight',
                'markings': 'spots', 'accent': (200, 50, 50), 'eye_size': 'big'},
    'frog':    {'body': (100, 200, 80), 'ears': 'none',   'tail': 'none',
                'markings': 'spots', 'eye_size': 'big', 'nose': False},
    'pig':     {'body': (255, 180, 200), 'ears': 'cat',   'tail': 'curl',
                'accent': (220, 100, 130)},
    'panda':   {'body': (255, 255, 255), 'ears': 'panda', 'tail': 'puff',
                'belly_color': (250, 250, 250), 'accent': (40, 40, 40),
                'eye_size': 'big'},
}


if __name__ == '__main__':
    import os, sys
    if PRESET not in PRESETS:
        print(f"Unknown PRESET '{PRESET}'. Available: {list(PRESETS)}",
              file=sys.stderr)
        raise SystemExit(2)
    cfg = PRESETS[PRESET]
    out_path = Path(os.environ.get('CODEX_PET_OUT')
                    or Path(__file__).resolve().parent / 'spritesheet.webp')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet = build(cfg)
    sheet.save(out_path, 'WEBP', lossless=True, quality=100)
    print(f'wrote {out_path} ({sheet.size[0]}x{sheet.size[1]}) — preset: {PRESET}')
