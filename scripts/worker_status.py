# -*- coding: utf-8 -*-
"""查看转写进度：python scripts/worker_status.py
打印各 worker 最后一行日志 + 已完成块统计。全部完成时打印 ALL DONE。"""
import glob
import os

workers = sorted(glob.glob("logs/w*.log"))
all_done = bool(workers)
for f in workers:
    with open(f, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().strip().splitlines()
    last = lines[-1] if lines else "(empty)"
    print(f"{os.path.basename(f)}: {last}")
    if "WORKER DONE" not in last:
        all_done = False

total = done = 0
for d in glob.glob("chunks/*/"):
    webs = glob.glob(os.path.join(d, "chunk_*.webm"))
    txts = glob.glob(os.path.join(d, "chunk_*.txt"))
    total += len(webs)
    done += len(txts)
print(f"---\nchunks: {done}/{total}")
if all_done and total and done == total:
    print("ALL DONE")
