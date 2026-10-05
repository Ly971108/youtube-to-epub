# -*- coding: utf-8 -*-
"""并行启动转写进程组：python scripts/launch_workers.py chunks/<id1> [chunks/<id2> ...]
扫描各目录下缺 .txt 的 chunk，轮询分成 N 个队列（N = min(6, max(2, CPU核数//2))，可用 WORKERS 覆盖），
分离启动 N 个 transcribe_worker 后台进程，日志写入 logs/wN.log。
随后用 python scripts/worker_status.py 查看进度。"""
import glob
import os
import subprocess
import sys

dirs = sys.argv[1:]
assert dirs, "usage: launch_workers.py chunks/<id> [...]"
pending = []
for d in dirs:
    for w in sorted(glob.glob(os.path.join(d, "chunk_*.webm"))):
        if not os.path.exists(w.rsplit(".", 1)[0] + ".txt"):
            pending.append(w.replace("\\", "/"))
if not pending:
    print("ALL DONE 没有待转写的块")
    sys.exit(0)

n = int(os.environ.get("WORKERS", "0")) or min(6, max(2, (os.cpu_count() or 4) // 2))
n = min(n, len(pending))
os.makedirs("lists", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# 轮询分配，保证各队列负载均匀
queues = [[] for _ in range(n)]
for i, chunk in enumerate(pending):
    queues[i % n].append(chunk)

for i, q in enumerate(queues, 1):
    lf = f"lists/w{i}.txt"
    with open(lf, "w", encoding="utf-8") as f:
        f.write("\n".join(q))
    log = open(f"logs/w{i}.log", "w", encoding="utf-8")
    subprocess.Popen([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "transcribe_worker.py"), lf],
                     stdout=log, stderr=subprocess.STDOUT)
    print(f"launched w{i}: {len(q)} 块")
print(f"共 {len(pending)} 块待转写，{n} 个进程后台运行中；用 worker_status.py 查看进度")
