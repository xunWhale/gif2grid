from pathlib import Path

import pytest
from PIL import Image, ImageChops

from gif2grid import Frame, Gif2GridError, contact_sheet, extract_frames
from gif2grid.cli import main


def make_gif(path: Path, count: int = 5, size=(40, 20)) -> Path:
    images = []
    for i in range(count):
        image = Image.new("RGB", size, (i * 30 % 255, 40, 120))
        images.append(image)
    images[0].save(path, save_all=True, append_images=images[1:], duration=[100 + i * 50 for i in range(count)], loop=0)
    return path


def test_extracts_requested_number_and_timestamps(tmp_path: Path) -> None:
    frames = extract_frames(make_gif(tmp_path / "a.gif", 12), frames=4)
    assert len(frames) == 4
    assert [frame.timestamp_ms for frame in frames] == [0, 700, 1750, 3850]


def test_auto_layout_is_near_square(tmp_path: Path) -> None:
    frames = extract_frames(make_gif(tmp_path / "a.gif", 12), frames=12)
    assert contact_sheet(frames, scale=10).size == (40, 15)


def test_manual_columns(tmp_path: Path) -> None:
    frames = extract_frames(make_gif(tmp_path / "a.gif", 6), frames=6)
    assert contact_sheet(frames, cols=2, scale=10).size == (20, 15)


def test_labels_change_pixels(tmp_path: Path) -> None:
    frames = extract_frames(make_gif(tmp_path / "a.gif", 2), frames=2)
    labeled = contact_sheet(frames, scale=40, labels=True)
    plain = contact_sheet(frames, scale=40, labels=False)
    assert ImageChops.difference(labeled, plain).getbbox() is not None


def test_requested_count_degrades_to_actual_frames(tmp_path: Path) -> None:
    assert len(extract_frames(make_gif(tmp_path / "a.gif", 3), frames=9)) == 3


def test_non_animation_has_clear_error(tmp_path: Path) -> None:
    image = Image.new("RGB", (20, 20), "red")
    path = tmp_path / "still.jpg"
    image.save(path)
    with pytest.raises(Gif2GridError, match="not an animated image"):
        extract_frames(path)


def test_scale_limits_cell_size(tmp_path: Path) -> None:
    frames = extract_frames(make_gif(tmp_path / "a.gif", 2, (100, 50)), frames=2)
    sheet = contact_sheet(frames, scale=25, labels=False)
    assert sheet.size == (50, 12)


def test_cli_writes_jpeg(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = make_gif(tmp_path / "a.gif", 2)
    output = tmp_path / "out.jpg"
    assert main([str(source), "-o", str(output), "--quality", "80"]) == 0
    assert Image.open(output).format == "JPEG"
    assert "Wrote" in capsys.readouterr().out


def test_single_frame_gif_works(tmp_path: Path) -> None:
    path = tmp_path / "one.gif"
    Image.new("RGB", (20, 10), "blue").save(path, format="GIF")
    frames = extract_frames(path, frames=9)
    assert len(frames) == 1
    assert contact_sheet(frames, labels=False).size == (20, 10)


def test_frame_limit_is_validated(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="between 1 and 64"):
        extract_frames(make_gif(tmp_path / "a.gif"), frames=65)
