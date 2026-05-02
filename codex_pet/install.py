"""Install a packaged pet into the Codex pets directory."""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from .atlas import validate


def codex_home() -> Path:
    """Resolve CODEX_HOME or default to ~/.codex."""
    raw = os.environ.get("CODEX_HOME")
    return Path(raw) if raw else Path.home() / ".codex"


def slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "pet"


def install(
    atlas_path: Path,
    name: str,
    description: str = "",
    display_name: str | None = None,
    pet_id: str | None = None,
    target_dir: Path | None = None,
    force: bool = False,
) -> Path:
    """Copy atlas + write pet.json into <CODEX_HOME>/pets/<id>/."""
    pid = slug(pet_id or name)
    pet_dir = target_dir or (codex_home() / "pets" / pid)

    result = validate(atlas_path)
    if not result.ok:
        raise ValueError("atlas failed validation: " + "; ".join(result.errors))

    pet_dir.mkdir(parents=True, exist_ok=True)
    sprite_dst = pet_dir / "spritesheet.webp"
    if sprite_dst.exists() and not force:
        raise FileExistsError(
            f"{sprite_dst} already exists — use --force to overwrite"
        )
    shutil.copyfile(atlas_path, sprite_dst)

    manifest = {
        "id": pid,
        "displayName": (display_name or name).strip(),
        "description": (description or "").strip() or None,
        "spritesheetPath": "spritesheet.webp",
    }
    if manifest["description"] is None:
        manifest.pop("description")

    (pet_dir / "pet.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return pet_dir
