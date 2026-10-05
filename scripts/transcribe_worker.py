# -*- coding: utf-8 -*-
"""常驻转写进程：python scripts/transcribe_worker.py <list_file>
list_file 每行一个 chunk 路径。模型只加载一次，逐块转写为同名 .txt，已有 .txt 自动跳过。
环境变量：WHISPER_MODEL（默认 small）、WHISPER_LANG（默认 zh）、WHISPER_PROMPT（初始提示词）、
WHISPER_THREADS（默认 2）。可反复启动同一队列实现断点续跑。"""
import os
import sys
import time


def main():
    list_file = sys.argv[1]
    with open(list_file, encoding="utf-8") as f:
        chunks = [ln.strip() for ln in f if ln.strip()]
    todo = [c for c in chunks if not os.path.exists(c.rsplit(".", 1)[0] + ".txt")]
    print(f"WORKER {list_file}: total={len(chunks)} todo={len(todo)}", flush=True)
    if not todo:
        print("WORKER DONE (all skipped)", flush=True)
        return

    from faster_whisper import WhisperModel
    model = WhisperModel(
        os.environ.get("WHISPER_MODEL", "small"), device="cpu", compute_type="int8",
        cpu_threads=int(os.environ.get("WHISPER_THREADS", "2")))
    prompt = os.environ.get(
        "WHISPER_PROMPT",
        "以下是中文口播/课程逐字稿，內容可能為繁體中文。")
    lang = os.environ.get("WHISPER_LANG", "zh")

    done = 0
    for chunk in todo:
        out = chunk.rsplit(".", 1)[0] + ".txt"
        if os.path.exists(out):  # 其他进程可能已抢先完成
            done += 1
            continue
        t0 = time.time()
        try:
            segments, _ = model.transcribe(chunk, language=lang, beam_size=5,
                                           vad_filter=True, initial_prompt=prompt)
            texts = [s.text for s in segments]
            with open(out, "w", encoding="utf-8") as f:
                f.write("\n".join(texts))
            done += 1
            print(f"[{done}/{len(todo)}] {chunk} {time.time()-t0:.0f}s {len(texts)}段", flush=True)
        except Exception as e:
            print(f"ERROR {chunk}: {e}", flush=True)
    print("WORKER DONE", flush=True)


if __name__ == "__main__":
    main()
