"""Preview generation: per-row animated GIFs + a contact sheet."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from .atlas import CELL_H, CELL_W, COLS, ROWS_SPEC, cell_box

# Default per-frame durations (ms) — tuned to match Codex pet feel.
DEFAULT_TIMINGS = {
    "idle":          [280, 110, 110, 140, 140, 320],
    "running-right": [120, 120, 120, 120, 120, 120, 120, 220],
    "running-left":  [120, 120, 120, 120, 120, 120, 120, 220],
    "waving":        [140, 140, 140, 280],
    "jumping":       [140, 140, 140, 140, 280],
    "failed":        [140, 140, 140, 140, 140, 140, 140, 240],
    "waiting":       [150, 150, 150, 150, 150, 260],
    "running":       [120, 120, 120, 120, 120, 220],
    "review":        [150, 150, 150, 150, 150, 280],
}

CHECKER_LIGHT = (245, 245, 245, 255)
CHECKER_DARK = (220, 220, 220, 255)


def _checker_bg(w: int, h: int, size: int = 16) -> Image.Image:
    img = Image.new("RGBA", (w, h), CHECKER_LIGHT)
    px = img.load()
    for y in range(h):
        for x in range(w):
            if ((x // size) + (y // size)) % 2:
                px[x, y] = CHECKER_DARK
    return img


def _used_cols(atlas: Image.Image, row: int) -> list[int]:
    return [c for c in range(COLS)
            if atlas.crop(cell_box(row, c)).getbbox() is not None]


def write_row_gif(
    atlas: Image.Image,
    row_name: str,
    out_path: Path,
    bg: tuple[int, int, int, int] | None = None,
) -> Path | None:
    from .atlas import row_index, ROW_NAMES
    if row_name not in ROW_NAMES:
        raise ValueError(f"unknown row: {row_name}")
    r = row_index(row_name)
    cols = _used_cols(atlas, r)
    if not cols:
        return None

    durs = DEFAULT_TIMINGS.get(row_name, [150] * len(cols))
    durs = (durs + [durs[-1]] * len(cols))[: len(cols)]

    frames = []
    for c in cols:
        cell = atlas.crop(cell_box(r, c))
        if bg is None:
            backdrop = _checker_bg(CELL_W, CELL_H)
        else:
            backdrop = Image.new("RGBA", (CELL_W, CELL_H), bg)
        backdrop.alpha_composite(cell)
        frames.append(backdrop.convert("P", palette=Image.ADAPTIVE))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=durs,
        loop=0,
        disposal=2,
    )
    return out_path


def write_contact_sheet(
    atlas: Image.Image,
    out_path: Path,
    bg: tuple[int, int, int, int] | None = None,
) -> Path:
    """3x3 grid of the first non-empty cell from each of the 9 rows."""
    sheet = Image.new("RGBA", (CELL_W * 3, CELL_H * 3),
                       bg if bg is not None else (255, 255, 255, 255))
    if bg is None:
        sheet.alpha_composite(_checker_bg(sheet.size[0], sheet.size[1]))

    for i, (name, _) in enumerate(ROWS_SPEC):
        gr, gc = i // 3, i % 3
        cols = _used_cols(atlas, i)
        if not cols:
            continue
        cell = atlas.crop(cell_box(i, cols[0]))
        sheet.paste(cell, (gc * CELL_W, gr * CELL_H), cell)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, "PNG")
    return out_path


_DISPLAY_NAMES = {
    'idle':          ('Idle',        'Neutral breathing and blinking loop'),
    'running-right': ('Run Right',   'Forward run cycle, facing right'),
    'running-left':  ('Run Left',    'Forward run cycle, facing left'),
    'waving':        ('Waving',      'Friendly hand wave on success'),
    'jumping':       ('Jumping',     'Crouch, leap, peak, fall, land'),
    'failed':        ('Failed',      'Stunned/dizzy reaction on error'),
    'waiting':       ('Waiting',     'Looking around while idle'),
    'running':       ('Running',     'Generic run loop, agent thinking'),
    'review':        ('Review',      'Leaning forward, inspecting'),
}


HTML_TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<title>{title} — codex-pet state viewer</title>
<style>
  * {{ box-sizing: border-box }}
  body {{ margin:0; padding:32px; font-family:-apple-system,BlinkMacSystemFont,
         "Segoe UI",sans-serif; background:#f4f4fb; color:#1a1a2a }}
  h1 {{ margin:0 0 24px; font-size:20px; font-weight:600 }}
  .layout {{ display:grid; grid-template-columns:380px 1fr; gap:32px }}
  .viewer {{ background:white; border-radius:18px; padding:28px;
             box-shadow:0 1px 3px rgba(0,0,0,.06) }}
  .viewer .label {{ color:#0a7ea5; font-size:11px; font-weight:700;
                    letter-spacing:.12em; text-transform:uppercase }}
  .viewer h2 {{ margin:6px 0 18px; font-size:32px; font-weight:700 }}
  .viewer .frame-count {{ display:inline-flex; align-items:center; gap:6px;
                          padding:4px 10px; border-radius:8px;
                          background:#f0f0f6; font-size:12px; color:#444 }}
  .viewer .stage {{ margin-top:16px; padding:24px; background:
                    repeating-conic-gradient(#eee 0% 25%, #fff 0% 50%) 50% / 16px 16px;
                    border-radius:14px; display:grid; place-items:center;
                    min-height:240px }}
  .viewer .stage img {{ image-rendering:pixelated; width:192px; height:208px }}
  .viewer .desc {{ margin-top:14px; color:#555; font-size:14px; line-height:1.5 }}
  .grid {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:12px }}
  .card {{ background:white; border-radius:14px; padding:18px;
           display:flex; justify-content:space-between; align-items:center;
           cursor:pointer; transition:transform .08s, box-shadow .08s;
           border:2px solid transparent }}
  .card:hover {{ transform:translateY(-1px); box-shadow:0 6px 16px rgba(0,0,0,.08) }}
  .card.active {{ border-color:#1a1a2a }}
  .card .meta h3 {{ margin:0 0 4px; font-size:15px }}
  .card .meta p  {{ margin:0; font-size:12px; color:#888 }}
  .card img {{ image-rendering:pixelated; width:64px; height:69px }}
  @media (max-width: 1100px) {{ .layout {{ grid-template-columns: 1fr }} }}
</style></head>
<body>
<h1>{title}</h1>
<div class="layout">
  <div class="viewer" id="viewer">
    <div class="label">State Viewer</div>
    <h2 id="state-name">Idle</h2>
    <span class="frame-count" id="state-frames">▶ 6 frames</span>
    <div class="stage"><img id="stage-img" src="" alt="state preview"></div>
    <p class="desc" id="state-desc"></p>
  </div>
  <div class="grid" id="grid">
{cards}
  </div>
</div>
<script>
const STATES = {states_json};
function show(idx) {{
  const s = STATES[idx];
  document.getElementById('state-name').textContent = s.label;
  document.getElementById('state-frames').textContent = '▶ ' + s.frames + ' frames';
  document.getElementById('state-desc').textContent = s.desc;
  document.getElementById('stage-img').src = s.gif;
  document.querySelectorAll('.card').forEach((c,i) =>
    c.classList.toggle('active', i === idx));
}}
document.querySelectorAll('.card').forEach((c,i) =>
  c.addEventListener('click', () => show(i)));
show(0);
</script>
</body></html>"""


def write_html_viewer(atlas_path: Path, out_dir: Path,
                       title: str = "Codex pet") -> Path:
    """Build an interactive HTML preview matching Codex's state-viewer layout."""
    import json
    atlas = Image.open(atlas_path).convert("RGBA")
    out_dir.mkdir(parents=True, exist_ok=True)

    states = []
    cards = []
    for i, (name, _) in enumerate(ROWS_SPEC):
        gif_path = out_dir / f"{i}-{name}.gif"
        if not gif_path.exists():
            write_row_gif(atlas, name, gif_path)
        if not gif_path.exists():
            continue
        cols = _used_cols(atlas, i)
        label, desc = _DISPLAY_NAMES[name]
        states.append({
            "label": label, "frames": len(cols), "desc": desc,
            "gif": gif_path.name, "row": i,
        })
        cards.append(
            f'    <div class="card">'
            f'<div class="meta"><h3>{label}</h3>'
            f'<p>Row {i} · {len(cols)} frames</p></div>'
            f'<img src="{gif_path.name}" alt="{label}"></div>'
        )

    html = HTML_TEMPLATE.format(
        title=title,
        cards="\n".join(cards),
        states_json=json.dumps(states),
    )
    out = out_dir / "index.html"
    out.write_text(html, encoding="utf-8")
    return out


def write_all(atlas_path: Path, out_dir: Path,
               html: bool = False, title: str = "Codex pet") -> list[Path]:
    atlas = Image.open(atlas_path).convert("RGBA")
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for i, (name, _) in enumerate(ROWS_SPEC):
        p = write_row_gif(atlas, name, out_dir / f"{i}-{name}.gif")
        if p is not None:
            written.append(p)
    written.append(write_contact_sheet(atlas, out_dir / "contact-sheet.png"))
    if html:
        written.append(write_html_viewer(atlas_path, out_dir, title=title))
    return written
