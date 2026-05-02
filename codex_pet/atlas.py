"""Atlas geometry, packing, and validation for Codex pets.

The Codex pet atlas is a 1536x1872 image laid out as 8 columns x 9 rows of
192x208 cells. Each row is an animation state. Cells past the last frame in a
row must be fully transparent.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image

CELL_W = 192
CELL_H = 208
COLS = 8
ROWS = 9
SHEET_W = COLS * CELL_W   # 1536
SHEET_H = ROWS * CELL_H   # 1872

# Canonical row order — matches Codex's built-in animation rows. The frame
# counts here are the maximum frames each row uses; trailing cells stay
# transparent. running-left can be derived by mirroring running-right.
ROWS_SPEC: list[tuple[str, int]] = [
    ("idle",          6),
    ("running-right", 8),
    ("running-left",  8),
    ("waving",        4),
    ("jumping",       5),
    ("failed",        8),
    ("waiting",       6),
    ("running",       6),
    ("review",        6),
]
ROW_NAMES = [name for name, _ in ROWS_SPEC]


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]


def blank_atlas() -> Image.Image:
    return Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 0))


def cell_box(row: int, col: int) -> tuple[int, int, int, int]:
    return (col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H)


def row_index(name: str) -> int:
    if name not in ROW_NAMES:
        raise ValueError(
            f"Unknown row '{name}'. Valid rows: {', '.join(ROW_NAMES)}"
        )
    return ROW_NAMES.index(name)


def pack_from_frames_dir(frames_dir: Path) -> Image.Image:
    """Build an atlas from a directory of named frame files.

    Frames are PNG/WebP files named `<row>-<index>.png`, e.g. `idle-0.png`,
    `running-right-3.png`. Each frame must be exactly CELL_W x CELL_H with
    an alpha channel. Missing frames leave that cell transparent.
    """
    if not frames_dir.is_dir():
        raise ValueError(f"frames dir not found: {frames_dir}")

    atlas = blank_atlas()
    placed: dict[str, list[int]] = {name: [] for name in ROW_NAMES}

    for path in sorted(frames_dir.iterdir()):
        if path.suffix.lower() not in {".png", ".webp"}:
            continue
        stem = path.stem
        # Match longest known row prefix so "running-right-0" parses correctly.
        row_name = next(
            (rn for rn in sorted(ROW_NAMES, key=len, reverse=True)
             if stem.startswith(rn + "-")),
            None,
        )
        if row_name is None:
            continue
        idx_str = stem[len(row_name) + 1 :]
        if not idx_str.isdigit():
            continue
        col = int(idx_str)
        if col >= COLS:
            raise ValueError(
                f"{path.name}: column {col} >= {COLS}"
            )

        cell = Image.open(path).convert("RGBA")
        if cell.size != (CELL_W, CELL_H):
            raise ValueError(
                f"{path.name}: expected {CELL_W}x{CELL_H}, got "
                f"{cell.size[0]}x{cell.size[1]}"
            )
        atlas.paste(cell, (col * CELL_W, row_index(row_name) * CELL_H), cell)
        placed[row_name].append(col)

    return atlas


def mirror_row(atlas: Image.Image, src_row: str, dst_row: str) -> None:
    """Horizontally flip every frame from src_row into dst_row."""
    si = row_index(src_row)
    di = row_index(dst_row)
    for col in range(COLS):
        cell = atlas.crop(cell_box(si, col))
        if cell.getbbox() is None:  # empty
            continue
        flipped = cell.transpose(Image.FLIP_LEFT_RIGHT)
        atlas.paste(flipped, (col * CELL_W, di * CELL_H))


def validate(atlas_path: Path) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    img = Image.open(atlas_path)
    if img.size != (SHEET_W, SHEET_H):
        errors.append(
            f"size {img.size[0]}x{img.size[1]} != {SHEET_W}x{SHEET_H}"
        )
        return ValidationResult(False, errors, warnings)

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # At least one row should have content
    has_any = any(
        img.crop(cell_box(r, c)).getbbox() is not None
        for r in range(ROWS)
        for c in range(COLS)
    )
    if not has_any:
        errors.append("atlas is fully transparent")

    # Per-row diagnostics
    for r, (name, max_frames) in enumerate(ROWS_SPEC):
        used = [c for c in range(COLS)
                if img.crop(cell_box(r, c)).getbbox() is not None]
        if not used:
            warnings.append(f"row {r} ({name}): empty")
            continue
        if max(used) >= max_frames:
            warnings.append(
                f"row {r} ({name}): frames in cols beyond expected "
                f"{max_frames} (cells {used})"
            )

    return ValidationResult(not errors, errors, warnings)


def save_atlas(atlas: Image.Image, out_path: Path, fmt: str | None = None) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fmt = (fmt or out_path.suffix.lstrip(".") or "webp").upper()
    if fmt == "WEBP":
        atlas.save(out_path, "WEBP", lossless=True, quality=100)
    else:
        atlas.save(out_path, fmt)
