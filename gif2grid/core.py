"""Frame extraction and timestamped contact sheet generation."""
from __future__ import annotations

import io
import json
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Union

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError


class Gif2GridError(ValueError):
    """Raised when an input cannot be processed as an animation."""


@dataclass(frozen=True)
class Frame:
    """A decoded frame and its position on the source timeline."""

    image: Image.Image
    timestamp_ms: int


def _validate_count(frames: int) -> None:
    if not 1 <= frames <= 64:
        raise ValueError("frames must be between 1 and 64")


def _uniform_indices(count: int, wanted: int) -> List[int]:
    if count <= wanted:
        return list(range(count))
    if wanted == 1:
        return [0]
    return [round(i * (count - 1) / (wanted - 1)) for i in range(wanted)]


def _image_frames(path: Path, wanted: int) -> List[Frame]:
    try:
        source = Image.open(path)
    except (UnidentifiedImageError, OSError) as exc:
        raise Gif2GridError(f"cannot read image input {path}: {exc}") from exc
    count = getattr(source, "n_frames", 1)
    animated = count > 1
    if not animated and source.format not in {"GIF", "WEBP"}:
        raise Gif2GridError("input is not an animated image (expected GIF, WebP, or APNG)")
    durations: List[int] = []
    for index in range(count):
        try:
            source.seek(index)
            durations.append(max(1, int(source.info.get("duration", 100))))
        except EOFError:
            break
    count = len(durations)
    if count == 0:
        raise Gif2GridError("input contains no decodable frames")
    selected = _uniform_indices(count, wanted)
    result: List[Frame] = []
    for index in selected:
        source.seek(index)
        image = source.convert("RGBA").copy()
        result.append(Frame(image, sum(durations[:index])))
    source.close()
    return result


def _run_checked(command: List[str], message: str) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as exc:
        raise Gif2GridError("mp4 input requires ffmpeg and ffprobe; install FFmpeg and try again") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode(errors="replace").strip().splitlines()[-1:]
        suffix = f": {detail[0]}" if detail else ""
        raise Gif2GridError(f"{message}{suffix}") from exc


def _video_frames(path: Path, wanted: int) -> List[Frame]:
    probe = _run_checked(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        "cannot inspect mp4 input",
    )
    try:
        duration = float(json.loads(probe.stdout)["format"]["duration"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise Gif2GridError("cannot determine mp4 duration") from exc
    if duration <= 0:
        raise Gif2GridError("mp4 input has no usable duration")
    rate = wanted / duration
    decoded = _run_checked(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={rate:.12f}", "-frames:v", str(wanted), "-f", "image2pipe", "-vcodec", "png", "pipe:1"],
        "cannot decode mp4 input",
    )
    result: List[Frame] = []
    signature = b"\x89PNG\r\n\x1a\n"
    end_marker = b"IEND\xaeB`\x82"
    for chunk in decoded.stdout.split(signature)[1:]:
        end = chunk.find(end_marker)
        if end < 0:
            continue
        try:
            image = Image.open(io.BytesIO(signature + chunk[: end + len(end_marker)]))
            result.append(Frame(image.convert("RGBA").copy(), round(len(result) * duration * 1000 / max(1, wanted))))
        except (UnidentifiedImageError, OSError):
            continue
    if not result:
        raise Gif2GridError("mp4 input produced no decodable frames")
    return result


def extract_frames(path: Union[str, Path], frames: int = 9) -> List[Frame]:
    """Extract up to ``frames`` evenly spaced frames from an animated file.

    GIF, WebP and APNG are decoded with Pillow. MP4 files use ffmpeg/ffprobe.
    If an animation has fewer frames than requested, all available frames are returned.
    """
    _validate_count(frames)
    source = Path(path)
    if not source.is_file():
        raise Gif2GridError(f"input file does not exist: {source}")
    if source.suffix.lower() in {".mp4", ".m4v", ".mov", ".avi", ".mkv"}:
        return _video_frames(source, frames)
    return _image_frames(source, frames)


def _font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _grid_cols(count: int) -> int:
    return max(1, min(count, math.ceil(math.sqrt(count))))


def contact_sheet(
    frames: Sequence[Frame],
    *,
    cols: Optional[int] = None,
    labels: bool = True,
    scale: int = 320,
) -> Image.Image:
    """Compose extracted frames into a labeled RGBA contact sheet.

    ``scale`` is the maximum width or height of each cell. ``cols`` overrides
    the automatically selected near-square layout.
    """
    if not frames:
        raise ValueError("frames must contain at least one frame")
    if scale < 1:
        raise ValueError("scale must be a positive integer")
    if cols is not None and not 1 <= cols <= len(frames):
        raise ValueError("cols must be between 1 and the number of frames")
    columns = cols or _grid_cols(len(frames))
    rows = math.ceil(len(frames) / columns)
    cells: List[Image.Image] = []
    for frame in frames:
        image = frame.image.convert("RGBA")
        ratio = min(1.0, scale / max(image.size))
        size = (max(1, round(image.width * ratio)), max(1, round(image.height * ratio)))
        cells.append(image.resize(size, Image.Resampling.LANCZOS) if ratio != 1 else image.copy())
    cell_w = max(image.width for image in cells)
    cell_h = max(image.height for image in cells)
    sheet = Image.new("RGBA", (columns * cell_w, rows * cell_h), (24, 24, 28, 255))
    for index, (frame, image) in enumerate(zip(frames, cells)):
        x = (index % columns) * cell_w + (cell_w - image.width) // 2
        y = (index // columns) * cell_h + (cell_h - image.height) // 2
        sheet.alpha_composite(image, (x, y))
        if labels:
            text = f"#{index + 1}  {frame.timestamp_ms} ms"
            font = _font(max(12, min(24, scale // 14)))
            draw = ImageDraw.Draw(sheet, "RGBA")
            box = draw.textbbox((0, 0), text, font=font)
            pad = 5
            draw.rounded_rectangle((x + 5, y + 5, x + 5 + box[2] - box[0] + pad * 2, y + 5 + box[3] - box[1] + pad * 2), radius=4, fill=(0, 0, 0, 175))
            draw.text((x + 5 + pad, y + 5 + pad), text, font=font, fill=(255, 255, 255, 255))
    return sheet
