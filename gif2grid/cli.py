"""Command line interface for gif2grid."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from .core import Gif2GridError, contact_sheet, extract_frames


def build_parser() -> argparse.ArgumentParser:
    """Build the gif2grid argument parser."""
    parser = argparse.ArgumentParser(description="Turn an animation into a timestamped contact sheet.")
    parser.add_argument("input", type=Path, help="GIF, WebP, APNG, or MP4 input")
    parser.add_argument("-o", "--output", type=Path, default=Path("contact-sheet.png"), help="output PNG or JPEG path")
    parser.add_argument("--frames", type=int, default=9, help="number of evenly spaced frames (1-64)")
    parser.add_argument("--cols", type=int, help="number of columns")
    parser.add_argument("--labels", action=argparse.BooleanOptionalAction, default=True, help="draw frame/time labels")
    parser.add_argument("--scale", type=int, default=320, help="maximum cell edge in pixels")
    parser.add_argument("--quality", type=int, default=90, help="JPEG quality (1-95)")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the command line program and return an exit status."""
    args = build_parser().parse_args(argv)
    if not 1 <= args.quality <= 95:
        print("gif2grid: --quality must be between 1 and 95")
        return 2
    try:
        extracted = extract_frames(args.input, args.frames)
        sheet = contact_sheet(extracted, cols=args.cols, labels=args.labels, scale=args.scale)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.suffix.lower() in {".jpg", ".jpeg"}:
            sheet.convert("RGB").save(args.output, "JPEG", quality=args.quality, optimize=True)
        else:
            sheet.save(args.output, "PNG", optimize=True)
    except (Gif2GridError, ValueError, OSError) as exc:
        print(f"gif2grid: {exc}")
        return 2
    print(f"Wrote {args.output} ({len(extracted)} frames, {sheet.width}x{sheet.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
