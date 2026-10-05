# -*- coding: utf-8 -*-
"""拉取播放列表/频道视频清单：python scripts/list_videos.py <playlist_or_channel_url> [out.tsv]
输出 TSV：<video_id>\\t<title> 每行一个，顺序即播放顺序。失败自动重试 3 次。"""
import os
import subprocess
import sys
import time

url = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "videos.tsv"

cmd = [sys.executable, "-m", "yt_dlp", "--flat-playlist", "--print", "%(id)s\t%(title)s", url]
if os.environ.get("YT_PROXY"):
    cmd[3:3] = ["--proxy", os.environ["YT_PROXY"]]

for attempt in range(1, 4):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode == 0 and r.stdout.strip():
        lines = [ln for ln in r.stdout.splitlines() if "\t" in ln]
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print(f"OK {out} 共 {len(lines)} 个视频")
        sys.exit(0)
    print(f"FAIL attempt={attempt}: {(r.stderr or '')[-200:]}", flush=True)
    time.sleep(10 * attempt)
sys.exit("GIVEUP 拉取清单失败，检查 YT_PROXY 或链接")
