"""`codex-pet new <name>` — scaffold a fresh pet project."""
from __future__ import annotations

from importlib import resources
from pathlib import Path

from .atlas import ROWS_SPEC

BUILD_TEMPLATE = '''#!/usr/bin/env python3
"""Build a Codex pet atlas with Pillow.

Run:
    python build.py            # writes spritesheet.webp
    codex-pet build .          # builds + validates + previews + installs

Edit `make_frame()` to draw your pet. Each frame is a 24x26 native grid
that gets nearest-neighbor scaled 8x to 192x208.
"""
from pathlib import Path
from PIL import Image

# Native pixel grid scaled 8x to 192x208 cells.
NATIVE_W, NATIVE_H = 24, 26
SCALE = 8
CELL_W, CELL_H = NATIVE_W * SCALE, NATIVE_H * SCALE
COLS, ROWS = 8, 9
SHEET_W, SHEET_H = COLS * CELL_W, ROWS * CELL_H

PALETTE = {{
    ".": None,
    "K": (0, 0, 0, 255),
    # Add your colors. Examples:
    # "R": (229, 37, 33, 255),
    # "B": (0, 68, 216, 255),
}}


def make_frame() -> list[list[str]]:
    """Return a NATIVE_H x NATIVE_W grid of palette keys ('.' = transparent)."""
    g = [["."] * NATIVE_W for _ in range(NATIVE_H)]
    # TODO: draw your pet here.
    return g


def grid_to_image(grid: list[list[str]]) -> Image.Image:
    img = Image.new("RGBA", (NATIVE_W, NATIVE_H), (0, 0, 0, 0))
    px = img.load()
    for y in range(NATIVE_H):
        for x in range(NATIVE_W):
            c = PALETTE.get(grid[y][x])
            if c is not None:
                px[x, y] = c
    return img.resize((CELL_W, CELL_H), Image.NEAREST)


# Row name -> list of frames. Trailing cells stay transparent.
ROW_FRAMES: dict[str, list[list[list[str]]]] = {{
{row_dict}
}}


def build() -> Image.Image:
    sheet = Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 0))
    row_order = [{row_order}]
    for r_idx, name in enumerate(row_order):
        for c_idx, frame in enumerate(ROW_FRAMES.get(name, [])[:COLS]):
            cell = grid_to_image(frame)
            sheet.paste(cell, (c_idx * CELL_W, r_idx * CELL_H), cell)
    return sheet


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "spritesheet.webp"
    build().save(out, "WEBP", lossless=True, quality=100)
    print(f"wrote {{out}}")
'''


README_TEMPLATE = """# {name}

A Codex pet built with [`codex-pet-gen`](https://github.com/yourname/codex-pet-gen).

## Build

```bash
python build.py                       # writes spritesheet.webp
codex-pet validate spritesheet.webp   # check geometry
codex-pet preview spritesheet.webp    # generate per-row GIFs + contact sheet
codex-pet install spritesheet.webp --name "{name}" --description "{desc}"
```

After install, restart Codex and pick `{name}` under
**Settings → Personalization → Pets**.
"""


def scaffold(name: str, target: Path) -> Path:
    target.mkdir(parents=True, exist_ok=True)

    row_dict_lines = []
    for row, _ in ROWS_SPEC:
        row_dict_lines.append(f'    "{row}": [make_frame()],')
    row_dict = "\n".join(row_dict_lines)
    row_order = ", ".join(f'"{r}"' for r, _ in ROWS_SPEC)

    build_py = BUILD_TEMPLATE.format(row_dict=row_dict, row_order=row_order)
    (target / "build.py").write_text(build_py, encoding="utf-8")
    (target / "README.md").write_text(
        README_TEMPLATE.format(name=name, desc=f"{name} — a Codex pet"),
        encoding="utf-8",
    )
    (target / ".gitignore").write_text(
        "__pycache__/\n*.pyc\nspritesheet.webp\npreview/\n",
        encoding="utf-8",
    )
    return target
