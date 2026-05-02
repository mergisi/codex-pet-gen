# Mario — codex-pet example

A worked example of a fully-procedural Codex pet built with Pillow rectangles.
No `image_gen` API calls. The whole 1536×1872 atlas is drawn from a 24×26
native pixel grid scaled 8× nearest-neighbor.

## Build it

```bash
cd examples/mario
python build.py                       # writes spritesheet.webp
codex-pet validate spritesheet.webp
codex-pet preview spritesheet.webp
codex-pet install spritesheet.webp \
  --name "Mario" \
  --description "An 8-bit plumber pet, hand-drawn in Pillow"
```

Or in one shot from the repo root:

```bash
codex-pet build examples/mario/build.py \
  --preview \
  --install-name "Mario" \
  --description "An 8-bit plumber pet, hand-drawn in Pillow"
```

## What's inside

- **Palette** (NES-ish): red cap, blue overalls, brown shoes, yellow buttons.
- **Composable parts**: `draw_head`, `draw_body`, `draw_arm`, `draw_legs` —
  each takes pose parameters (`leg_phase`, `arm_pose`, `eye`, `tilt`, `dy`).
- **Animation factories** — one function per row (`anim_idle`, `anim_jumping`,
  …). Each returns a list of frames.
- **`running-left` mirror**: derived as a horizontal flip of `running-right`
  rather than redrawn — see the `('mirror', grid)` sentinel in `render_frame`.

This file is a useful reference if you want to write a similar generator for
your own character.
