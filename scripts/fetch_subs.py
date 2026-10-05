# -*- coding: utf-8 -*-
"""优先尝试直接抓取字幕：python scripts/fetch_subs.py <video_id>
成功则输出 transcripts/<id>.txt 并打印 OK（省掉下载+转写，速度快 100 倍，应永远先试这个）。
无字幕/失败打印 NOSUB 并以退出码 1 结束，调用方再走 whisper 路线。"""
import glob
import os
import re
import subprocess
import sys
from pathlib import Path

vid = sys.argv[1]
langs = os.environ.get("SUB_LANGS", "zh-Hant,zh-Hans,zh,zh-TW,zh-CN,en")
tmp = Path("subs_tmp")
tmp.mkdir(exist_ok=True)

cmd = [sys.executable, "-m", "yt_dlp", "--skip-download",
       "--write-subs", "--write-auto-subs", "--sub-langs", langs,
       "--sub-format", "vtt", "--no-playlist",
       "-o", str(tmp / f"{vid}.%(ext)s"),
       f"https://www.youtube.com/watch?v={vid}"]
if os.environ.get("YT_PROXY"):
    cmd[4:4] = ["--proxy", os.environ["YT_PROXY"]]
subprocess.run(cmd, capture_output=True)

vtts = sorted(glob.glob(str(tmp / f"{vid}.*.vtt")))
if not vtts:
    print(f"NOSUB {vid}")
    sys.exit(1)

# 解析 vtt：去时间轴、去重连续行
lines = []
prev = None
with open(vtts[0], encoding="utf-8", errors="replace") as f:
    for ln in f:
        ln = ln.strip()
        if not ln or ln.startswith("WEBVTT") or "-->" in ln or re.match(r"^\d{2}:\d{2}", ln):
            continue
        ln = re.sub(r"<[^>]+>", "", ln)
        if ln and ln != prev:
            lines.append(ln)
            prev = ln
Path("transcripts").mkdir(exist_ok=True)
out = Path("transcripts") / f"{vid}.txt"
out.write_text("\n".join(lines), encoding="utf-8")
for f in glob.glob(str(tmp / f"{vid}.*")):
    os.remove(f)
print(f"OK {out} 来源={os.path.basename(vtts[0])} 行数={len(lines)}")
