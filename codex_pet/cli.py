"""codex-pet CLI."""
from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

from . import __version__
from .atlas import (
    SHEET_H,
    SHEET_W,
    pack_from_frames_dir,
    mirror_row,
    save_atlas,
    validate,
)
from .creature import (
    PRESETS,
    build_atlas as creature_build_atlas,
    config_from_args as creature_config_from_args,
)
from .install import install
from .preview import write_all
from .scaffold import scaffold


def cmd_new(args: argparse.Namespace) -> int:
    target = Path(args.target or args.name).resolve()
    if target.exists() and any(target.iterdir()) and not args.force:
        print(f"error: {target} is not empty (use --force)", file=sys.stderr)
        return 2
    scaffold(args.name, target)
    print(f"scaffolded pet project at {target}")
    print(f"next: cd {target} && python build.py")
    return 0


def cmd_pack(args: argparse.Namespace) -> int:
    frames_dir = Path(args.frames_dir).resolve()
    out = Path(args.out).resolve()
    atlas = pack_from_frames_dir(frames_dir)
    if args.mirror_running_left:
        mirror_row(atlas, "running-right", "running-left")
    save_atlas(atlas, out)
    print(f"wrote {out} ({SHEET_W}x{SHEET_H})")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    result = validate(Path(args.atlas).resolve())
    for w in result.warnings:
        print(f"warn: {w}")
    for e in result.errors:
        print(f"error: {e}", file=sys.stderr)
    if result.ok:
        print("ok")
        return 0
    return 1


def cmd_preview(args: argparse.Namespace) -> int:
    atlas = Path(args.atlas).resolve()
    # Default: <atlas-stem>-preview/ next to the atlas (so multiple atlases
    # in the same dir don't clobber each other and the path is predictable).
    out_dir = Path(args.out or atlas.parent / f"{atlas.stem}-preview").resolve()
    written = write_all(atlas, out_dir,
                         html=args.html, title=args.title)
    for p in written:
        print(p)
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    pet_dir = install(
        atlas_path=Path(args.atlas).resolve(),
        name=args.name,
        description=args.description or "",
        display_name=args.display_name,
        pet_id=args.id,
        target_dir=Path(args.target).resolve() if args.target else None,
        force=args.force,
    )
    print(f"installed → {pet_dir}")
    print("restart Codex, then pick the pet under "
          "Settings → Personalization → Pets")
    return 0


def cmd_creature(args: argparse.Namespace) -> int:
    if args.list_presets:
        for name in sorted(PRESETS):
            cfg = PRESETS[name]
            print(f"{name:<8} body=#{cfg.body[0]:02x}{cfg.body[1]:02x}{cfg.body[2]:02x}"
                  f" ears={cfg.ears} tail={cfg.tail} markings={cfg.markings}"
                  f" eyes={cfg.eye_size}")
        return 0

    if not args.preset and not args.body:
        raise ValueError(
            "need at least a preset or --body. try: codex-pet creature cat"
        )

    cfg = creature_config_from_args(
        preset=args.preset,
        body=args.body,
        accent=args.accent,
        belly_color=args.belly_color,
        ears=args.ears,
        tail=args.tail,
        markings=args.markings,
        eye_size=args.eye_size,
        no_nose=args.no_nose,
        no_belly=args.no_belly,
    )

    # Resolve output path. We always need a temp file to install from.
    if args.out:
        out = Path(args.out).resolve()
    elif args.no_install:
        out = Path.cwd() / f"{args.preset or 'creature'}.webp"
    else:
        # Install will copy this; we keep it next to cwd for transparency.
        out = Path.cwd() / f"{args.preset or 'creature'}.webp"
    out.parent.mkdir(parents=True, exist_ok=True)

    sheet = creature_build_atlas(cfg)
    sheet.save(out, "WEBP", lossless=True, quality=100)
    print(f"wrote {out} ({sheet.size[0]}x{sheet.size[1]})")

    if args.preview:
        preview_dir = out.parent / (out.stem + "-preview")
        write_all(out, preview_dir)
        print(f"preview: {preview_dir}")

    if not args.no_install:
        # Default: install to Codex. Auto-derive name from preset if missing.
        pet_name = args.name or (args.preset.capitalize() if args.preset else None)
        if not pet_name:
            raise ValueError(
                "can't auto-name pet — pass --name or --no-install"
            )
        pet_dir = install(
            atlas_path=out,
            name=pet_name,
            description=args.description or "",
            force=args.force,
        )
        print(f"installed → {pet_dir}")
        print("restart Codex (⌘Q + reopen), then pick the pet under "
              "Settings → Personalization → Pets")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Run a user's Pillow build script, then validate + (optionally) install."""
    script = Path(args.script).resolve()
    if not script.exists():
        print(f"error: script not found: {script}", file=sys.stderr)
        return 2

    # Execute the script — convention: it writes spritesheet.webp next to itself,
    # or accepts CODEX_PET_OUT env var.
    out = Path(args.out).resolve() if args.out else script.parent / "spritesheet.webp"
    import os
    os.environ["CODEX_PET_OUT"] = str(out)
    runpy.run_path(str(script), run_name="__main__")

    if not out.exists():
        print(f"error: script did not produce {out}", file=sys.stderr)
        return 1

    result = validate(out)
    for w in result.warnings:
        print(f"warn: {w}")
    if not result.ok:
        for e in result.errors:
            print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"built + validated: {out}")

    if args.preview:
        write_all(out, out.parent / "preview")
        print(f"preview: {out.parent / 'preview'}")

    if args.install_name:
        pet_dir = install(
            atlas_path=out,
            name=args.install_name,
            description=args.description or "",
            force=args.force,
        )
        print(f"installed → {pet_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="codex-pet",
        description="Build, validate, preview, and install Codex pets.",
    )
    p.add_argument("--version", action="version",
                   version=f"codex-pet {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    pn = sub.add_parser("new", help="scaffold a new pet project")
    pn.add_argument("name")
    pn.add_argument("--target", help="target dir (default: ./<name>)")
    pn.add_argument("--force", action="store_true")
    pn.set_defaults(func=cmd_new)

    pp = sub.add_parser("pack",
                         help="assemble frames in a dir into an atlas")
    pp.add_argument("frames_dir")
    pp.add_argument("--out", required=True, help="output atlas path (.webp)")
    pp.add_argument("--mirror-running-left", action="store_true",
                    help="derive running-left by mirroring running-right")
    pp.set_defaults(func=cmd_pack)

    pv = sub.add_parser("validate", help="check atlas geometry/transparency")
    pv.add_argument("atlas")
    pv.set_defaults(func=cmd_validate)

    pr = sub.add_parser("preview",
                         help="generate per-row GIFs + contact sheet (+ HTML)")
    pr.add_argument("atlas")
    pr.add_argument("--out", help="output dir (default: <atlas-dir>/preview)")
    pr.add_argument("--html", action="store_true",
                    help="also build an interactive state-viewer HTML page")
    pr.add_argument("--title", default="Codex pet",
                    help="title shown in the HTML viewer")
    pr.set_defaults(func=cmd_preview)

    pi = sub.add_parser("install",
                         help="install atlas as a Codex pet (writes pet.json)")
    pi.add_argument("atlas")
    pi.add_argument("--name", required=True)
    pi.add_argument("--description")
    pi.add_argument("--display-name")
    pi.add_argument("--id", help="folder slug (default: derived from name)")
    pi.add_argument("--target", help="exact pet dir (skips CODEX_HOME default)")
    pi.add_argument("--force", action="store_true")
    pi.set_defaults(func=cmd_install)

    pc = sub.add_parser(
        "creature",
        help="build a creature pet and install it to Codex in one shot",
        description=(
            "Build + install in one command. Default behavior:\n"
            "  codex-pet creature cat            → installs as 'Cat'\n"
            "  codex-pet creature --body '#a050ff' --ears horns --name Spike\n"
            "  codex-pet creature cat --no-install --out /tmp/cat.webp\n"
        ),
    )
    pc.add_argument("preset", nargs="?", choices=sorted(PRESETS),
                    help="preset name (cat, dog, bunny, dragon, frog, pig, panda, blob)")
    pc.add_argument("--name",
                    help="installed pet name (default: capitalized preset)")
    pc.add_argument("--description", default="")
    pc.add_argument("--body", help="body color #RRGGBB")
    pc.add_argument("--accent", help="accent color #RRGGBB (nose/horns)")
    pc.add_argument("--belly-color", dest="belly_color",
                    help="belly patch color #RRGGBB")
    pc.add_argument("--ears", choices=["none", "cat", "bunny", "dog",
                                        "horns", "panda", "round",
                                        "feather-tuft", "long-down", "unicorn"])
    pc.add_argument("--tail", choices=["none", "straight", "curl", "puff",
                                        "long-thin"])
    pc.add_argument("--markings", choices=["none", "stripes", "spots",
                                            "belly-patch", "shell"])
    pc.add_argument("--eye-size", dest="eye_size", choices=["small", "big"])
    pc.add_argument("--no-nose", action="store_true")
    pc.add_argument("--no-belly", action="store_true")
    pc.add_argument("--out",
                    help="also write atlas to this path (default: ./<preset>.webp)")
    pc.add_argument("--preview", action="store_true",
                    help="also generate per-row GIFs + contact sheet")
    pc.add_argument("--no-install", action="store_true",
                    help="don't install to Codex, just write the .webp file")
    pc.add_argument("--force", action="store_true",
                    help="overwrite an existing pet of the same name")
    pc.add_argument("--list-presets", action="store_true",
                    help="list built-in presets and exit")
    pc.set_defaults(func=cmd_creature)

    pb = sub.add_parser("build",
                         help="run a Pillow build script + validate")
    pb.add_argument("script", help="path to a python build script")
    pb.add_argument("--out", help="atlas output path")
    pb.add_argument("--preview", action="store_true")
    pb.add_argument("--install-name", help="if set, installs after building")
    pb.add_argument("--description")
    pb.add_argument("--force", action="store_true")
    pb.set_defaults(func=cmd_build)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, FileExistsError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
