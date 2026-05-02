#!/usr/bin/env python3
"""Generate a Mario sprite sheet for tweet-pet (8 cols x 9 rows, 192x208 cells)."""
from PIL import Image
from pathlib import Path

NATIVE_W, NATIVE_H = 24, 26
SCALE = 8
CELL_W, CELL_H = NATIVE_W * SCALE, NATIVE_H * SCALE  # 192 x 208
COLS, ROWS = 8, 9
SHEET_W, SHEET_H = COLS * CELL_W, ROWS * CELL_H       # 1536 x 1872

PALETTE = {
    '.': None,
    'K': (0, 0, 0, 255),            # outline black
    'R': (229, 37, 33, 255),        # mario red
    'D': (160, 17, 14, 255),        # dark red shadow
    'B': (0, 68, 216, 255),         # overalls blue
    'b': (0, 38, 130, 255),         # dark blue shadow
    'S': (252, 200, 156, 255),      # skin
    's': (210, 138, 88, 255),       # skin shadow
    'M': (61, 26, 5, 255),          # hair / mustache
    'W': (255, 255, 255, 255),      # white
    'Y': (251, 208, 0, 255),        # button yellow
    'N': (110, 55, 18, 255),        # shoe brown
    'n': (60, 25, 0, 255),          # shoe shadow
    'X': (255, 230, 80, 255),       # dizzy star
    'H': (61, 26, 5, 255),          # alias to brown (no yellow tuft)
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


def stamp(g, x, y, lines):
    for dy, row in enumerate(lines):
        for dx, ch in enumerate(row):
            setpx(g, x + dx, y + dy, ch)


# ---------- Mario builder ----------
# Anchor: head-top is at y = 1 + dy. Mario fits in y=1..23 (22 tall) and x=4..19 (16 wide).
# cx = 11 (visual center between hat tip).
# dy is a vertical offset for bobbing/jumping. facing in {-1, +1}: -1 = left.

def draw_head(g, dy=0, eye='open', look=0, blink=False, tilt=0):
    """Classic Mario head: rounded red cap, M badge, big skin nose, small mustache.
    Layout: y=1..12. Face center column = 11.5 (between cols 11 and 12)."""
    tx = tilt

    # CAP - rounded peak: 6 -> 8 -> 10 wide tapering down
    rect(g, 9 + tx, 1 + dy, 14 + tx, 1 + dy, 'R')   # peak (6 wide)
    rect(g, 8 + tx, 2 + dy, 15 + tx, 2 + dy, 'R')   # row 2 (8 wide)
    rect(g, 7 + tx, 3 + dy, 16 + tx, 3 + dy, 'R')   # row 3 (10 wide)
    rect(g, 7 + tx, 4 + dy, 16 + tx, 4 + dy, 'R')   # row 4 (10 wide)
    # CAP BRIM (12 wide, extends past head)
    rect(g, 6 + tx, 5 + dy, 17 + tx, 5 + dy, 'R')
    # Brim shadow underline (darker cap color)
    rect(g, 6 + tx, 6 + dy, 17 + tx, 6 + dy, 'D')

    # WHITE M BADGE on cap front (row 4, ~3-4 pixels)
    # Simplified M: 4 white pixels in a "/\" valley pattern
    setpx(g, 10 + tx, 3 + dy, 'W')   # top-left of M
    setpx(g, 13 + tx, 3 + dy, 'W')   # top-right of M
    setpx(g, 10 + tx, 4 + dy, 'W')   # left leg
    setpx(g, 11 + tx, 4 + dy, 'W')   # middle dip
    setpx(g, 12 + tx, 4 + dy, 'W')   # middle dip
    setpx(g, 13 + tx, 4 + dy, 'W')   # right leg

    # SIDE HAIR (M = dark brown), visible under cap brim sides
    setpx(g, 5 + tx, 6 + dy, 'M')
    setpx(g, 18 + tx, 6 + dy, 'M')
    rect(g, 5 + tx, 7 + dy, 6 + tx, 9 + dy, 'M')   # left sideburn
    rect(g, 17 + tx, 7 + dy, 18 + tx, 9 + dy, 'M')  # right sideburn

    # FACE SKIN — wide top, tapering chin
    rect(g, 7 + tx, 7 + dy, 16 + tx, 7 + dy, 'S')   # forehead (10 wide)
    rect(g, 7 + tx, 8 + dy, 16 + tx, 8 + dy, 'S')   # eye row baseline (10 wide)
    rect(g, 7 + tx, 9 + dy, 16 + tx, 9 + dy, 'S')   # nose row baseline
    rect(g, 8 + tx, 10 + dy, 15 + tx, 10 + dy, 'S')  # cheeks (8 wide)
    rect(g, 9 + tx, 11 + dy, 14 + tx, 11 + dy, 'S')  # narrowing (6 wide)
    rect(g, 10 + tx, 12 + dy, 13 + tx, 12 + dy, 'S')  # chin (4 wide)

    # EARS (small skin bumps)
    setpx(g, 6 + tx, 8 + dy, 'S')
    setpx(g, 17 + tx, 8 + dy, 'S')

    # BIG NOSE — skin colored, 3 wide x 2 tall, in face center
    rect(g, 11 + tx, 9 + dy, 13 + tx, 9 + dy, 'S')
    rect(g, 11 + tx, 10 + dy, 13 + tx, 10 + dy, 'S')
    # Nose shading on bottom edge
    setpx(g, 11 + tx, 11 + dy, 's')
    setpx(g, 13 + tx, 11 + dy, 's')

    # EYES — flank the nose. Left eye cols 8-9, right eye cols 14-15.
    if eye == 'closed' or blink:
        rect(g, 8 + tx, 8 + dy, 9 + tx, 8 + dy, 'M')
        rect(g, 14 + tx, 8 + dy, 15 + tx, 8 + dy, 'M')
    elif eye == 'x':
        setpx(g, 8 + tx, 8 + dy, 'K'); setpx(g, 9 + tx, 8 + dy, 'K')
        setpx(g, 14 + tx, 8 + dy, 'K'); setpx(g, 15 + tx, 8 + dy, 'K')
    elif eye == 'wide':
        rect(g, 8 + tx, 8 + dy, 9 + tx, 9 + dy, 'W')
        rect(g, 14 + tx, 8 + dy, 15 + tx, 9 + dy, 'W')
        setpx(g, 9 + tx, 8 + dy, 'K')
        setpx(g, 14 + tx, 8 + dy, 'K')
        # restore nose covering wide-eye overlap
        setpx(g, 11 + tx, 9 + dy, 'S'); setpx(g, 12 + tx, 9 + dy, 'S'); setpx(g, 13 + tx, 9 + dy, 'S')
    else:
        rect(g, 8 + tx, 8 + dy, 9 + tx, 8 + dy, 'W')
        rect(g, 14 + tx, 8 + dy, 15 + tx, 8 + dy, 'W')
        # Pupil with `look` direction (-1 left, 0 center, +1 right)
        if look < 0:
            setpx(g, 8 + tx, 8 + dy, 'K'); setpx(g, 14 + tx, 8 + dy, 'K')
        elif look > 0:
            setpx(g, 9 + tx, 8 + dy, 'K'); setpx(g, 15 + tx, 8 + dy, 'K')
        else:
            setpx(g, 9 + tx, 8 + dy, 'K'); setpx(g, 14 + tx, 8 + dy, 'K')

    # MUSTACHE — small, only directly under nose. 6 wide.
    setpx(g, 9 + tx, 11 + dy, 'M')   # left tip outer
    rect(g, 10 + tx, 11 + dy, 13 + tx, 11 + dy, 'M')  # center (under nose)
    setpx(g, 14 + tx, 11 + dy, 'M')  # right tip outer
    # Mustache curls dropping at outer ends (1 px)
    setpx(g, 9 + tx, 12 + dy, 'M')
    setpx(g, 14 + tx, 12 + dy, 'M')

    # MOUTH — small dark line between mustache curls
    setpx(g, 11 + tx, 12 + dy, 'M')
    setpx(g, 12 + tx, 12 + dy, 'M')


def draw_body(g, dy=0, button_blink=False):
    """Red shirt collar then blue overalls. y=13..18 (6 rows)."""
    # Red shirt collar/shoulders (peeking from under overalls neck)
    rect(g, 8, 13 + dy, 15, 13 + dy, 'R')
    setpx(g, 7, 13 + dy, 'R'); setpx(g, 16, 13 + dy, 'R')
    # Overalls main body (blue), wider than chest
    rect(g, 7, 14 + dy, 16, 17 + dy, 'B')
    # Red shirt visible at sides between strap and arm (sleeves)
    setpx(g, 6, 14 + dy, 'R'); setpx(g, 17, 14 + dy, 'R')
    setpx(g, 6, 15 + dy, 'R'); setpx(g, 17, 15 + dy, 'R')
    # Overalls straps (vertical blue lines on bib, against red shirt above)
    setpx(g, 9, 13 + dy, 'B')
    setpx(g, 14, 13 + dy, 'B')
    # Yellow buttons on bib top
    btn = 'W' if button_blink else 'Y'
    setpx(g, 9, 14 + dy, btn)
    setpx(g, 14, 14 + dy, btn)
    # Body bottom edge
    rect(g, 7, 18 + dy, 16, 18 + dy, 'B')


def draw_arm(g, side, pose, dy=0):
    """Draw one arm. side in {-1, +1} (-1 left). Body shoulders at y=13."""
    if side < 0:
        bx = 5
    else:
        bx = 18
    if pose == 'down':
        # arm hangs at side, glove at bottom
        rect(g, bx, 14 + dy, bx, 16 + dy, 'R')
        rect(g, bx, 17 + dy, bx, 17 + dy, 'W')
    elif pose == 'wave':
        # arm raised diagonal up
        rect(g, bx, 10 + dy, bx, 13 + dy, 'R')
        sx = bx - (1 if side > 0 else -1)
        setpx(g, sx, 10 + dy, 'R')
        setpx(g, bx, 9 + dy, 'W')   # glove tip
    elif pose == 'up':
        # straight up
        rect(g, bx, 9 + dy, bx, 13 + dy, 'R')
        setpx(g, bx, 8 + dy, 'W')
    elif pose == 'run-front':
        # arm forward across body
        rect(g, bx, 14 + dy, bx, 15 + dy, 'R')
        sx = bx - (1 if side > 0 else -1)
        setpx(g, sx, 16 + dy, 'R')
        setpx(g, sx, 17 + dy, 'W')
    elif pose == 'run-back':
        # arm back & slightly up
        rect(g, bx, 13 + dy, bx, 15 + dy, 'R')
        setpx(g, bx, 12 + dy, 'W')
    elif pose == 'reach':
        # arm extended forward (slightly up)
        rect(g, bx, 13 + dy, bx, 14 + dy, 'R')
        sx = bx + (1 if side > 0 else -1)
        setpx(g, sx, 13 + dy, 'R')
        setpx(g, sx, 12 + dy, 'W')
    elif pose == 'akimbo':
        # hand on hip
        rect(g, bx, 14 + dy, bx, 15 + dy, 'R')
        sx = bx - (1 if side > 0 else -1)
        setpx(g, sx, 15 + dy, 'W')


def draw_legs(g, pose, dy=0):
    """Legs + shoes. Native rows 19..24."""
    Y = 19 + dy
    if pose == 'stand':
        rect(g, 8, Y, 10, Y + 3, 'B')
        rect(g, 11, Y, 13, Y + 3, 'B')
        rect(g, 7, Y + 4, 11, Y + 5, 'N')
        rect(g, 10, Y + 4, 14, Y + 5, 'N')
    elif pose == 'lift-r':
        rect(g, 8, Y, 10, Y + 3, 'B')
        rect(g, 7, Y + 4, 11, Y + 5, 'N')
        rect(g, 11, Y, 13, Y + 1, 'B')
        rect(g, 12, Y + 2, 14, Y + 3, 'B')
        rect(g, 13, Y + 4, 15, Y + 5, 'N')
    elif pose == 'lift-l':
        rect(g, 11, Y, 13, Y + 3, 'B')
        rect(g, 10, Y + 4, 14, Y + 5, 'N')
        rect(g, 8, Y, 10, Y + 1, 'B')
        rect(g, 7, Y + 2, 9, Y + 3, 'B')
        rect(g, 6, Y + 4, 8, Y + 5, 'N')
    elif pose == 'split':
        rect(g, 7, Y, 9, Y + 3, 'B')
        rect(g, 12, Y, 14, Y + 3, 'B')
        rect(g, 6, Y + 4, 10, Y + 5, 'N')
        rect(g, 11, Y + 4, 15, Y + 5, 'N')
    elif pose == 'tuck':
        rect(g, 8, Y, 10, Y + 2, 'B')
        rect(g, 11, Y, 13, Y + 2, 'B')
        rect(g, 7, Y + 3, 11, Y + 4, 'N')
        rect(g, 10, Y + 3, 14, Y + 4, 'N')
    elif pose == 'kneel':
        rect(g, 8, Y, 10, Y + 4, 'B')
        rect(g, 11, Y, 13, Y + 4, 'B')
        rect(g, 7, Y + 5, 14, Y + 5, 'N')
    elif pose == 'fall':
        rect(g, 6, Y + 1, 8, Y + 3, 'B')
        rect(g, 14, Y + 1, 16, Y + 3, 'B')
        rect(g, 5, Y + 4, 9, Y + 5, 'N')
        rect(g, 13, Y + 4, 17, Y + 5, 'N')


# ---------- Frame composers ----------

def frame(eye='open', look=0, dy=0, blink=False, button_blink=False, tilt=0,
          arm_l='down', arm_r='down', legs='stand', extra=None):
    g = blank()
    draw_head(g, dy=dy, eye=eye, look=look, blink=blink, tilt=tilt)
    draw_body(g, dy=dy, button_blink=button_blink)
    draw_arm(g, -1, arm_l, dy=dy)
    draw_arm(g, +1, arm_r, dy=dy)
    draw_legs(g, legs, dy=dy)
    if extra:
        extra(g)
    return g


# ----- per-row animation factories -----

def anim_idle():
    # 6 frames: gentle bob with occasional blink
    return [
        frame(dy=0),
        frame(dy=0),
        frame(dy=-1),
        frame(dy=-1),
        frame(dy=0, blink=True),
        frame(dy=0),
    ]


def anim_running_right():
    # 8 frames classic 4-pose run cycle x2
    return [
        frame(legs='lift-r', arm_l='run-front', arm_r='run-back'),
        frame(legs='split',  arm_l='run-front', arm_r='run-back', dy=-1),
        frame(legs='lift-l', arm_l='run-back',  arm_r='run-front'),
        frame(legs='split',  arm_l='run-back',  arm_r='run-front', dy=-1),
        frame(legs='lift-r', arm_l='run-front', arm_r='run-back'),
        frame(legs='split',  arm_l='run-front', arm_r='run-back', dy=-1),
        frame(legs='lift-l', arm_l='run-back',  arm_r='run-front'),
        frame(legs='split',  arm_l='run-back',  arm_r='run-front', dy=-1),
    ]


def anim_running_left():
    # mirror running-right at render time
    return [('mirror', f) for f in anim_running_right()]


def anim_waving():
    # right arm raised, hand waves
    return [
        frame(arm_r='wave', arm_l='down', look=1),
        frame(arm_r='up',   arm_l='down', look=1, dy=-1),
        frame(arm_r='wave', arm_l='down', look=1),
        frame(arm_r='up',   arm_l='down', look=1, dy=-1),
    ]


def anim_jumping():
    # crouch, launch, peak (tuck), falling (split), land (kneel)
    return [
        frame(legs='kneel', arm_l='reach', arm_r='reach', dy=1),
        frame(legs='lift-r', arm_l='up', arm_r='up', dy=-1),
        frame(legs='tuck',  arm_l='up', arm_r='up', dy=-3, eye='wide'),
        frame(legs='split', arm_l='reach', arm_r='reach', dy=-2),
        frame(legs='kneel', arm_l='down', arm_r='down', dy=1),
    ]


def anim_failed():
    # dizzy: X eyes, swaying head, stars overlapping head
    def stars(g):
        # tiny stars touching head outline
        setpx(g, 4, 2, 'X'); setpx(g, 4, 1, 'X')
        setpx(g, 18, 3, 'X')
        setpx(g, 17, 1, 'X')
    return [
        frame(eye='x', tilt=-1, legs='kneel', arm_l='down', arm_r='down', extra=stars),
        frame(eye='x', tilt=0,  legs='kneel', arm_l='down', arm_r='down', extra=stars),
        frame(eye='x', tilt=1,  legs='kneel', arm_l='down', arm_r='down', extra=stars),
        frame(eye='x', tilt=0,  legs='kneel', arm_l='down', arm_r='down', extra=stars),
        frame(eye='x', tilt=-1, legs='fall',  arm_l='reach', arm_r='reach', extra=stars),
        frame(eye='x', tilt=0,  legs='fall',  arm_l='reach', arm_r='reach', extra=stars),
        frame(eye='x', tilt=1,  legs='fall',  arm_l='reach', arm_r='reach', extra=stars),
        frame(eye='x', tilt=0,  legs='fall',  arm_l='reach', arm_r='reach', extra=stars),
    ]


def anim_waiting():
    # tapping foot / looking around
    return [
        frame(look=1,  arm_l='akimbo', arm_r='akimbo'),
        frame(look=1,  arm_l='akimbo', arm_r='akimbo', legs='lift-r'),
        frame(look=0,  arm_l='akimbo', arm_r='akimbo'),
        frame(look=-1, arm_l='akimbo', arm_r='akimbo'),
        frame(look=-1, arm_l='akimbo', arm_r='akimbo', legs='lift-l'),
        frame(look=0,  arm_l='akimbo', arm_r='akimbo', blink=True),
    ]


def anim_running():
    # generic running, tighter cycle
    return [
        frame(legs='lift-r', arm_l='run-front', arm_r='run-back'),
        frame(legs='split',  arm_l='run-front', arm_r='run-back', dy=-1),
        frame(legs='lift-l', arm_l='run-back',  arm_r='run-front'),
        frame(legs='split',  arm_l='run-back',  arm_r='run-front', dy=-1),
        frame(legs='lift-r', arm_l='run-front', arm_r='run-back'),
        frame(legs='lift-l', arm_l='run-back',  arm_r='run-front'),
    ]


def anim_review():
    # leaning forward, peering, slight bob
    return [
        frame(eye='wide', look=1, arm_l='akimbo', arm_r='reach', tilt=1),
        frame(eye='wide', look=1, arm_l='akimbo', arm_r='reach', tilt=1, dy=-1),
        frame(eye='wide', look=0, arm_l='akimbo', arm_r='reach', tilt=1),
        frame(eye='wide', look=-1, arm_l='reach', arm_r='akimbo', tilt=-1),
        frame(eye='wide', look=-1, arm_l='reach', arm_r='akimbo', tilt=-1, dy=-1),
        frame(eye='open', look=0, arm_l='akimbo', arm_r='akimbo', blink=True),
    ]


# ---------- Sheet composer ----------

ROW_SPECS = [
    ('idle',          anim_idle),
    ('running-right', anim_running_right),
    ('running-left',  anim_running_left),
    ('waving',        anim_waving),
    ('jumping',       anim_jumping),
    ('failed',        anim_failed),
    ('waiting',       anim_waiting),
    ('running',       anim_running),
    ('review',        anim_review),
]


def grid_to_image(grid):
    img = Image.new('RGBA', (NATIVE_W, NATIVE_H), (0, 0, 0, 0))
    px = img.load()
    for y in range(NATIVE_H):
        for x in range(NATIVE_W):
            ch = grid[y][x]
            c = PALETTE.get(ch)
            if c is not None:
                px[x, y] = c
    return img.resize((CELL_W, CELL_H), Image.NEAREST)


def render_frame(spec):
    """spec is either a grid or ('mirror', grid)."""
    if isinstance(spec, tuple) and spec and spec[0] == 'mirror':
        img = grid_to_image(spec[1])
        return img.transpose(Image.FLIP_LEFT_RIGHT)
    return grid_to_image(spec)


def build():
    sheet = Image.new('RGBA', (SHEET_W, SHEET_H), (0, 0, 0, 0))
    for r_idx, (name, factory) in enumerate(ROW_SPECS):
        frames = factory()
        for c_idx, f in enumerate(frames[:COLS]):
            cell = render_frame(f)
            sheet.paste(cell, (c_idx * CELL_W, r_idx * CELL_H), cell)
    return sheet


if __name__ == '__main__':
    import os
    out_path = Path(os.environ.get('CODEX_PET_OUT')
                    or Path(__file__).resolve().parent / 'spritesheet.webp')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet = build()
    sheet.save(out_path, 'WEBP', lossless=True, quality=100)
    print(f'wrote {out_path} ({sheet.size[0]}x{sheet.size[1]})')
