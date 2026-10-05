# -*- coding: utf-8 -*-
"""记录一次批次运行的性能数据：python scripts/log_run.py <project_dir> <batch> <notes...>
向 <project_dir>/performance-log.md 追加一行表格记录，供自优化协议分析。
batch 例：vol1 / videos 2-5。notes 例：chunks=100 transcribe_min=62 subs_hit=3。"""
import datetime
import os
import sys

project = sys.argv[1]
batch = sys.argv[2]
notes = " ".join(sys.argv[3:])
log = os.path.join(project, "performance-log.md")
if not os.path.exists(log):
    with open(log, "w", encoding="utf-8") as f:
        f.write("# 性能日志（自优化协议的数据来源）\n\n| 时间 | 批次 | 数据 |\n|---|---|---|\n")
with open(log, "a", encoding="utf-8") as f:
    f.write(f"| {datetime.datetime.now():%Y-%m-%d %H:%M} | {batch} | {notes} |\n")
print(f"logged to {log}")
