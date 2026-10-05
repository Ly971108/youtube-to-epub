# -*- coding: utf-8 -*-
"""下载一个视频的音频：python scripts/download_one.py <video_id>
输出 audio/<id>.webm（best audio）。已存在则跳过，失败重试 3 次（YouTube 间歇 403/SABR 属正常，重试即可）。
代理：设置环境变量 YT_PROXY 后自动使用。"""
import os
import subprocess
import sys
import time
from pathlib import Path

vid = sys.argv[1]
audio_dir = Path("audio")
audio_dir.mkdir(exist_ok=True)
out = audio_dir / f"{vid}.webm"
if out.exists() and out.stat().st_size > 1_000_000:
    print(f"SKIP {vid} 已下载 ({out.stat().st_size // 1_000_000} MB)")
    sys.exit(0)

cmd = [sys.executable, "-m", "yt_dlp"]
if os.environ.get("YT_PROXY"):
    cmd += ["--proxy", os.environ["YT_PROXY"]]
cmd += ["-f", "ba", "--no-playlist",
        "-o", str(audio_dir / f"{vid}.%(ext)s"),
        f"https://www.youtube.com/watch?v={vid}"]

for attempt in range(1, 4):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode == 0 and out.exists():
        print(f"OK {vid} attempt={attempt} size={out.stat().st_size // 1_000_000} MB")
        sys.exit(0)
    print(f"FAIL {vid} attempt={attempt}: {(r.stderr or r.stdout)[-300:]}", flush=True)
    time.sleep(10 * attempt)
print(f"GIVEUP {vid}")
sys.exit(1)
