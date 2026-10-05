# -*- coding: utf-8 -*-
"""合并一个视频的块转写：python scripts/merge_chunks.py <video_id>
按序拼接 chunks/<id>/chunk_*.txt；除第一块外每块丢首段（去掉切块时的 10 秒重叠）。
输出 transcripts/<id>.txt。"""
import glob
import os
import sys

vid = sys.argv[1]
files = sorted(glob.glob(f"chunks/{vid}/chunk_*.txt"))
assert files, f"no chunks for {vid}"
os.makedirs("transcripts", exist_ok=True)
lines = []
for i, fp in enumerate(files):
    with open(fp, encoding="utf-8") as f:
        segs = [ln.rstrip("\n") for ln in f if ln.strip()]
    if i > 0 and segs:
        segs = segs[1:]
    lines.extend(segs)
out = f"transcripts/{vid}.txt"
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"OK {out} chunks={len(files)} segments={len(lines)} chars={sum(len(l) for l in lines)}")
