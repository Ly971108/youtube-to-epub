#!/usr/bin/env python3
"""YouTube 链接 -> 文字稿 (transcript.txt + meta.json)

用法:
  python fetch_transcript.py <url> [--out DIR] [--proxy http://127.0.0.1:7890]

选字幕优先级: 中文(简>繁) > 英文 > 其它; 同语族人工字幕优先于自动生成。
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

ID_PATTERNS = [
    r"youtube\.com/watch\?[^#\s]*v=([\w-]{11})",
    r"youtu\.be/([\w-]{11})",
    r"youtube\.com/(?:shorts|embed|live|v)/([\w-]{11})",
    r"^([\w-]{11})$",
]

CLEAN_PATTERNS = [
    r"\[Music\]|\[音乐\]|\(Music\)|♪+",
    r"</?i>|</?b>|</?u>",
]


def extract_id(url: str):
    for p in ID_PATTERNS:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def pick_transcript(tlist):
    """返回得分最高的字幕轨"""
    items = list(tlist)

    def score(t):
        s = 0
        lc = (t.language_code or "").lower()
        if lc in ("zh-hans", "zh-cn", "zh"):
            s += 100
        elif lc.startswith("zh"):
            s += 90
        elif lc.startswith("en"):
            s += 80
        if not t.is_generated:
            s += 10
        return s

    return max(items, key=score) if items else None


def fetch_oembed(video_id: str):
    """免费拿视频标题/作者, 失败不致命"""
    import urllib.request

    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            d = json.loads(r.read().decode("utf-8"))
            return {"title": d.get("title", ""), "author": d.get("author_name", "")}
    except Exception:
        return {"title": "", "author": ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", default=".")
    ap.add_argument("--proxy", default=None, help="如 http://127.0.0.1:7890")
    args = ap.parse_args()

    if args.proxy:
        os.environ["HTTPS_PROXY"] = args.proxy
        os.environ["HTTP_PROXY"] = args.proxy

    vid = extract_id(args.url)
    if not vid:
        print("ERROR: 无法从链接解析视频 ID", file=sys.stderr)
        sys.exit(2)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        NoTranscriptFound,
        TranscriptsDisabled,
        VideoUnavailable,
    )

    api = YouTubeTranscriptApi()
    try:
        tlist = api.list(vid)
    except VideoUnavailable:
        print("ERROR: 视频不存在/未上架, 或当前代理出口 IP 被 YouTube 拦截", file=sys.stderr)
        print("HINT: 若浏览器挂同一代理能看此视频, 则是 IP 被拦 → 换 Clash 节点后重试", file=sys.stderr)
        sys.exit(3)
    except TranscriptsDisabled:
        print("ERROR: 该视频未开放字幕, 换一个有 CC 的视频", file=sys.stderr)
        sys.exit(4)
    except Exception as e:
        print(f"ERROR: 拉取字幕列表失败: {e}", file=sys.stderr)
        print("HINT: 若本机访问 YouTube 需代理, 加 --proxy http://127.0.0.1:端口", file=sys.stderr)
        sys.exit(5)

    chosen = pick_transcript(tlist)
    if not chosen:
        print("ERROR: 没有任何可用字幕轨", file=sys.stderr)
        sys.exit(6)

    try:
        fetched = chosen.fetch()
    except NoTranscriptFound:
        print("ERROR: 字幕轨已失效", file=sys.stderr)
        sys.exit(7)

    parts = []
    for snip in fetched:
        t = (snip.text or "").replace("\n", " ")
        for pat in CLEAN_PATTERNS:
            t = re.sub(pat, "", t)
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            parts.append(t)
    text = " ".join(parts)

    meta = {
        "video_id": vid,
        "url": f"https://www.youtube.com/watch?v={vid}",
        "language_code": chosen.language_code,
        "language": chosen.language,
        "is_generated": bool(chosen.is_generated),
        "char_count": len(text),
    }
    meta.update(fetch_oembed(vid))

    (out / "transcript.txt").write_text(text, encoding="utf-8")
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    need_translate = not meta["language_code"].lower().startswith("zh")
    print("OK " + json.dumps({**meta, "need_translate": need_translate}, ensure_ascii=False))


if __name__ == "__main__":
    main()
