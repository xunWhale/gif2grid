# gif2grid

Turn an animated image into one timestamped contact sheet, so vision models can actually see what happens over time.

## Why this exists

I ran into a real failure with multimodal models: most GIF middleware silently compresses an animation into one still frame. A GIF of someone kicking a bottle became “a person sprinting forward” because the continuous action disappeared. `gif2grid` samples the timeline evenly and puts the frames, frame numbers, and millisecond timestamps into one image that can be sent to a VLM in a single request.

## Install

```bash
pip install gif2grid
```

For local development:

```bash
pip install -e .
```

## CLI

```bash
gif2grid kick.gif --frames 9 --scale 320 -o kick-grid.png
Wrote kick-grid.png (9 frames, 960x960)
```

JPEG output and quality control:

```bash
gif2grid clip.webp -o clip-grid.jpg --quality 85 --cols 4
```

Disable labels when you need a clean sheet:

```bash
gif2grid clip.gif --no-labels --scale 240
```

The input can be GIF, WebP, APNG, or MP4. MP4 decoding uses `ffmpeg` and `ffprobe`; if they are absent, the command reports that MP4 requires FFmpeg.

## Python API

```python
from gif2grid import contact_sheet, extract_frames

frames = extract_frames("kick.gif", frames=9)
sheet = contact_sheet(frames, scale=320, labels=True)
sheet.save("kick-grid.png")
```

`extract_frames` returns `Frame` objects with `.image` (a Pillow RGBA image) and `.timestamp_ms` (the original timeline position). The requested frame count is capped at 64 and automatically reduced when the input has fewer frames.

## Options

| Option | Default | Description |
| --- | ---: | --- |
| `input` | — | GIF, WebP, APNG, or MP4 path |
| `-o, --output` | `contact-sheet.png` | PNG or JPEG output path |
| `--frames N` | `9` | Evenly sampled frames, from 1 to 64 |
| `--cols N` | automatic | Manual number of columns |
| `--labels/--no-labels` | labels on | Toggle frame number and timestamp overlays |
| `--scale N` | `320` | Maximum width or height of each cell |
| `--quality N` | `90` | JPEG quality from 1 to 95 |

## Limitations

- MP4 support requires both `ffmpeg` and `ffprobe` on `PATH`.
- Animated image timing comes from each format's frame duration metadata.
- Contact sheets use a uniform cell size based on the largest sampled frame.

## License

MIT
