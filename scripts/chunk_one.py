# -*- coding: utf-8 -*-
"""把音频切成 240 秒 + 10 秒重叠的块：python scripts/chunk_one.py <video_id>
输入 audio/<id>.webm，输出 chunks/<id>/chunk_000.webm ...。已有切块则跳过。
块长/重叠可用环境变量 CHUNK_LEN / CHUNK_STEP 调整（默认 250/240）。"""
import os
import re
import subprocess
import sys
from pathlib import Path

vid = sys.argv[1]
src = Path("audio") / f"{vid}.webm"
outdir = Path("chunks") / vid
outdir.mkdir(parents=True, exist_ok=True)

import imageio_ffmpeg
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

probe = subprocess.run([ffmpeg, "-i", str(src)], capture_output=True, text=True, errors="replace")
m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", probe.stderr)
assert m, "cannot read duration"
dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))

step = int(os.environ.get("CHUNK_STEP", "240"))
length = int(os.environ.get("CHUNK_LEN", "250"))
expected = int((dur - 1) // step) + 1
existing = sorted(outdir.glob("chunk_*.webm"))
if len(existing) >= expected:
    print(f"SKIP {vid} 切块已齐全 ({expected})")
    sys.exit(0)

i = 0
start = 0.0
while start < dur:
    out = outdir / f"chunk_{i:03d}.webm"
    if not out.exists() or out.stat().st_size < 1000:
        subprocess.run([ffmpeg, "-y", "-ss", str(start), "-t", str(length), "-i", str(src),
                        "-c", "copy", str(out)], capture_output=True)
    start += step
    i += 1
print(f"OK {vid} duration={dur:.0f}s chunks={i}")
