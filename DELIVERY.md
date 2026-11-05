# gif2grid 交付记录

## 已完成

- 实现 `gif2grid` Python 包和同名 CLI。
- 支持 GIF、WebP、APNG，以及通过 `ffmpeg`/`ffprobe` 兜底的 MP4。
- 默认均匀抽取 9 帧，支持 `--frames 1..64`；帧数超过输入时自动降级到实际帧数。
- 自动选择接近正方形的列数，支持 `--cols` 手动指定。
- 帧左上角显示序号和原始时间轴毫秒数，支持 `--labels/--no-labels`。
- 支持 PNG、JPEG、`--quality`、`--scale`。
- 提供 `extract_frames` 和 `contact_sheet` 库 API。
- 添加完整项目元数据、README、MIT LICENSE、`.gitignore` 和 10 个 pytest 用例。

## 真实测试输出

```text
..........                                                               [100%]
10 passed in 0.03s
```

以上内容来自项目根目录的 [pytest-output.txt](pytest-output.txt)，由真实命令生成：

```text
/home/fish/.venv/bin/python -m pytest -q
```

另外完成了 CLI 冒烟测试：PNG 输出为 `PNG (64, 64)`，JPEG 输出为 `JPEG (64, 32)`；MP4 通过 ffmpeg 兜底生成了 `3 frames, 48x32` 的 PNG 网格。

## 仓库

- https://github.com/xunWhale/gif2grid
- 公开仓库，默认分支 `main`
- 发布标签：`v0.1.0`

## Git log

```text
2745baf feat: add animated media contact sheet tool
```

交付记录本身随后作为下一条提交加入仓库。

## 尚未验证

- 未在没有 ffmpeg/ffprobe 的机器上实际移除程序并运行，只验证了代码会把缺失依赖报告为明确的 MP4 错误。
- 未在 Python 3.9 实机上运行；代码使用 Python 3.9 支持的类型标注和 Pillow API。
