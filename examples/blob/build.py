#!/usr/bin/env python3
"""Blob — a tiny green slime pet. Minimal example for codex-pet.

Run:
    python build.py                     # writes spritesheet.webp
    codex-pet preview spritesheet.webp  # see it animate
    codex-pet install spritesheet.webp --name "Blob"
"""
from pathlib import Path
from PIL import Image

# 24x26 native pixels, scaled 8x to 192x208 cells.
NATIVE_W, NATIVE_H = 24, 26
SCALE = 8
CELL_W, CELL_H = NATIVE_W * SCALE, NATIVE_H * SCALE
COLS, ROWS = 8, 9
SHEET_W, SHEET_H = COLS * CELL_W, ROWS * CELL_H

PALETTE = {
    '.': None,
    'K': (0, 0, 0, 255),            # outline
    'G': (96, 200, 100, 255),       # body green
    'g': (60, 150, 70, 255),        # darker green (shadow)
    'L': (170, 240, 160, 255),      # highlight green
    'W': (255, 255, 255, 255),      # eye white
    'Y': (255, 230, 80, 255),       # dizzy stars
}


def blank():
    return [['.'] * NATIVE_W for _ in range(NATIVE_H)]


def setpx(g, x, y, ch):
    if 0 <= x < NATIVE_W and 0 <= y < NATIVE_H and ch != ' ':
        g[y][x] = ch


def rect(g, x1, y1, x2, y2, ch):
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            setpx(g, x, y, ch)


# ---------- Blob builder ----------
# A blob is just a rounded body with two eyes. We change shape
# (squash/stretch) and eye state per pose.

def draw_blob(g, squash=0, eye='open', look=0, mouth='small', extra=None):
    """squash > 0 = wide & short (landed). squash < 0 = tall & narrow (jumping).
    eye in {'open', 'closed', 'x', 'wide'}.
    """
    # Body bounding box centered around (12, 18) (a bit below middle)
    cy = 18
    cx = 12

    # Default body: 14 wide x 11 tall. Apply squash.
    half_w = 7 + squash       # widens when squashed down
    half_h = 5 - squash       # shortens when squashed
    half_w = max(4, min(10, half_w))
    half_h = max(3, min(8, half_h))

    # Outline (K) ring around body
    # Top dome (rounded)
    for dy in range(-half_h, half_h + 1):
        # ellipse-ish: shrink width near top/bottom
        shrink = max(0, abs(dy) - (half_h - 2))
        w = half_w - shrink
        rect(g, cx - w, cy + dy, cx + w, cy + dy, 'G')

    # Highlight (L) — a light dot near top-left
    setpx(g, cx - 4, cy - half_h + 1, 'L')
    setpx(g, cx - 3, cy - half_h + 1, 'L')
    setpx(g, cx - 4, cy - half_h + 2, 'L')

    # Shadow (g) — bottom curve
    for dx in range(-half_w + 2, half_w - 1):
        setpx(g, cx + dx, cy + half_h, 'g')

    # Outline ring
    for dy in range(-half_h, half_h + 1):
        shrink = max(0, abs(dy) - (half_h - 2))
        w = half_w - shrink
        setpx(g, cx - w - 1, cy + dy, 'K')
        setpx(g, cx + w + 1, cy + dy, 'K')
    # Top/bottom outline caps
    rect(g, cx - half_w + 1, cy - half_h - 1, cx + half_w - 1, cy - half_h - 1, 'K')
    rect(g, cx - half_w + 1, cy + half_h + 1, cx + half_w - 1, cy + half_h + 1, 'K')

    # Eyes — sit roughly at body upper third
    eye_y = cy - half_h + 3
    lex, rex = cx - 3, cx + 2  # eye column centers

    if eye == 'closed':
        rect(g, lex, eye_y, lex + 1, eye_y, 'K')
        rect(g, rex, eye_y, rex + 1, eye_y, 'K')
    elif eye == 'x':
        for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)]:  # 2x2 X spots
            setpx(g, lex + dx, eye_y + dy - 1, 'K')
            setpx(g, rex + dx, eye_y + dy - 1, 'K')
        # Tiny stars overlapping the body silhouette (chroma-key safe)
        setpx(g, cx - half_w, eye_y - 2, 'Y')
        setpx(g, cx + half_w, eye_y - 2, 'Y')
    elif eye == 'wide':
        rect(g, lex, eye_y - 1, lex + 1, eye_y + 1, 'W')
        rect(g, rex, eye_y - 1, rex + 1, eye_y + 1, 'W')
        setpx(g, lex + (1 if look > 0 else 0), eye_y, 'K')
        setpx(g, rex + (1 if look > 0 else 0), eye_y, 'K')
    else:
        rect(g, lex, eye_y, lex + 1, eye_y, 'W')
        rect(g, rex, eye_y, rex + 1, eye_y, 'W')
        # pupil
        if look < 0:
            setpx(g, lex, eye_y, 'K'); setpx(g, rex, eye_y, 'K')
        elif look > 0:
            setpx(g, lex + 1, eye_y, 'K'); setpx(g, rex + 1, eye_y, 'K')
        else:
            setpx(g, lex + 1, eye_y, 'K'); setpx(g, rex, eye_y, 'K')

    # Mouth
    if mouth == 'small':
        setpx(g, cx, eye_y + 2, 'K')
        setpx(g, cx + 1, eye_y + 2, 'K')
    elif mouth == 'open':
        rect(g, cx - 1, eye_y + 2, cx + 2, eye_y + 3, 'K')
    elif mouth == 'frown':
        rect(g, cx - 1, eye_y + 3, cx + 2, eye_y + 3, 'K')
        setpx(g, cx - 2, eye_y + 2, 'K'); setpx(g, cx + 3, eye_y + 2, 'K')

    if extra:
        extra(g)


def frame(squash=0, eye='open', look=0, mouth='small', extra=None):
    g = blank()
    draw_blob(g, squash=squash, eye=eye, look=look, mouth=mouth, extra=extra)
    return g


ANIMS = {
    'idle':          [frame(), frame(squash=1, mouth='small'),
                       frame(), frame(squash=1, mouth='small'),
                       frame(eye='closed'), frame()],
    'running-right': [frame(squash=-1), frame(squash=0), frame(squash=1),
                       frame(squash=0), frame(squash=-1), frame(squash=0),
                       frame(squash=1), frame(squash=0)],
    'running-left':  [],   # mirrored after build (see __main__)
    'waving':        [frame(eye='wide', look=1, mouth='open'),
                       frame(eye='wide', look=-1, mouth='open'),
                       frame(eye='wide', look=1, mouth='open'),
                       frame(eye='wide', look=-1, mouth='open')],
    'jumping':       [frame(squash=2, mouth='small'),
                       frame(squash=-1, eye='wide', mouth='open'),
                       frame(squash=-2, eye='wide', mouth='open'),
                       frame(squash=-1, eye='wide', mouth='open'),
                       frame(squash=2, mouth='frown')],
    'failed':        [frame(squash=2, eye='x', mouth='frown'),
                       frame(squash=2, eye='x', mouth='frown'),
                       frame(squash=1, eye='x', mouth='frown'),
                       frame(squash=2, eye='x', mouth='frown'),
                       frame(squash=2, eye='x', mouth='frown'),
                       frame(squash=2, eye='x', mouth='frown'),
                       frame(squash=2, eye='x', mouth='frown'),
                       frame(squash=2, eye='x', mouth='frown')],
    'waiting':       [frame(look=1), frame(look=1, eye='closed'),
                       frame(look=-1), frame(look=-1, eye='closed'),
                       frame(), frame(eye='closed')],
    'running':       [frame(squash=-1), frame(squash=0), frame(squash=1),
                       frame(squash=0), frame(squash=-1), frame(squash=0)],
    'review':        [frame(eye='wide', look=1),
                       frame(eye='wide', look=1),
                       frame(eye='wide', look=-1),
                       frame(eye='wide', look=-1),
                       frame(eye='wide', look=1),
                       frame(eye='closed')],
}

ROW_ORDER = ['idle', 'running-right', 'running-left', 'waving', 'jumping',
             'failed', 'waiting', 'running', 'review']


def grid_to_image(grid):
    img = Image.new('RGBA', (NATIVE_W, NATIVE_H), (0, 0, 0, 0))
    px = img.load()
    for y in range(NATIVE_H):
        for x in range(NATIVE_W):
            c = PALETTE.get(grid[y][x])
            if c is not None:
                px[x, y] = c
    return img.resize((CELL_W, CELL_H), Image.NEAREST)


def build():
    sheet = Image.new('RGBA', (SHEET_W, SHEET_H), (0, 0, 0, 0))
    for r_idx, name in enumerate(ROW_ORDER):
        frames = ANIMS.get(name, [])
        for c_idx, f in enumerate(frames[:COLS]):
            cell = grid_to_image(f)
            sheet.paste(cell, (c_idx * CELL_W, r_idx * CELL_H), cell)

    # Mirror running-right -> running-left
    src_y = ROW_ORDER.index('running-right') * CELL_H
    dst_y = ROW_ORDER.index('running-left') * CELL_H
    for c in range(COLS):
        cell = sheet.crop((c * CELL_W, src_y, (c + 1) * CELL_W, src_y + CELL_H))
        if cell.getbbox() is None:
            continue
        flipped = cell.transpose(Image.FLIP_LEFT_RIGHT)
        sheet.paste(flipped, (c * CELL_W, dst_y))
    return sheet


if __name__ == '__main__':
    import os
    out_path = Path(os.environ.get('CODEX_PET_OUT')
                     or Path(__file__).resolve().parent / 'spritesheet.webp')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet = build()
    sheet.save(out_path, 'WEBP', lossless=True, quality=100)
    print(f'wrote {out_path} ({sheet.size[0]}x{sheet.size[1]})')
