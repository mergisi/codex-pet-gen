# codex-pet-gen

A small CLI to build, validate, preview, and install **Codex pets** from the
command line — without needing OpenAI's `image_gen` tool or the internal
`hatch-pet` skill.

`pip install codex-pet-gen` → `codex-pet creature cat` → done.

The official `hatch-pet` skill is excellent but locked to Codex's runtime: it
calls `$imagegen`, owns the prompt pipeline, and bakes in a 10-image-generation
flow. If you want to:

- ship your own pet with **hand-drawn** or **procedurally generated** frames,
- iterate on a sprite sheet without round-tripping through an image API,
- or write a **Pillow script** that draws your pet pixel-by-pixel,

then `codex-pet` is the missing local toolchain. It enforces the atlas spec
(1536×1872, 8 cols × 9 rows of 192×208 cells), packages your pet for Codex,
and produces preview GIFs you can drop into a tweet.

## Install

```bash
pip install codex-pet-gen        # once published
# or, from a checkout:
pip install -e .
```

This installs the `codex-pet` command. Requires Python 3.10+ and Pillow.

## Quick start

### Option A — write a Pillow build script

```bash
codex-pet new mario
cd mario
# Edit build.py — fill in PALETTE and ROW_FRAMES.
python build.py                  # writes spritesheet.webp
codex-pet validate spritesheet.webp
codex-pet preview spritesheet.webp
codex-pet install spritesheet.webp \
  --name "Mario" \
  --description "An 8-bit plumber pet"
```

A complete worked example lives in [`examples/mario`](examples/mario).

### Option B — pack a folder of frames

If you have hand-drawn or AI-generated 192×208 PNGs:

```bash
# frames/idle-0.png, frames/idle-1.png, ..., frames/running-right-3.png, ...
codex-pet pack frames/ --out spritesheet.webp --mirror-running-left
codex-pet install spritesheet.webp --name "MyPet"
```

### Option C — one-shot build + install

```bash
codex-pet build build.py \
  --preview \
  --install-name "Mario" \
  --description "An 8-bit plumber pet"
```

## Atlas spec

| | |
| --- | --- |
| Image size | 1536 × 1872 |
| Cell size | 192 × 208 |
| Layout | 8 cols × 9 rows |
| Format | PNG or WebP, RGBA |
| Background | Transparent (cells past last frame must be empty) |

Row order (top to bottom):

| Row | Animation | Frames |
| --- | --- | --- |
| 0 | idle | 6 |
| 1 | running-right | 8 |
| 2 | running-left | 8 |
| 3 | waving | 4 |
| 4 | jumping | 5 |
| 5 | failed | 8 |
| 6 | waiting | 6 |
| 7 | running | 6 |
| 8 | review | 6 |

## Where pets get installed

`codex-pet install` writes:

```
$CODEX_HOME/pets/<id>/
  pet.json           # { "id", "displayName", "description", "spritesheetPath" }
  spritesheet.webp
```

Defaults to `~/.codex/pets/<id>/`. After install, **fully restart Codex** and
pick the pet under **Settings → Personalization → Pets**.

## Commands

```
codex-pet new <name>                    scaffold a pet project
codex-pet pack <frames-dir> --out X     pack named PNGs into an atlas
codex-pet validate <atlas>              check geometry / transparency
codex-pet preview <atlas> [--out DIR]   per-row GIFs + 3x3 contact sheet
codex-pet install <atlas> --name N      package + copy to ~/.codex/pets
codex-pet build <script.py>             run a Pillow script then validate
```

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

This project mirrors the atlas spec defined by Codex's `hatch-pet` skill but
reimplements only the deterministic, local parts. The image-generation pipeline
in `hatch-pet` is not duplicated here.
