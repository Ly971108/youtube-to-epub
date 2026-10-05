# -*- coding: utf-8 -*-
"""环境自检与自动安装：python scripts/bootstrap.py
自动 pip 安装 yt-dlp / faster-whisper / imageio-ffmpeg（ffmpeg 随 imageio 自带，无需系统安装）。
检测代理（环境变量 YT_PROXY，或自动探测常见本地代理端口）。
检测 HuggingFace 连通性，不通则提示设置 HF_ENDPOINT=https://hf-mirror.com。
全部通过输出 READY，否则输出待修复项。幂等，可重复运行。"""
import importlib
import os
import socket
import subprocess
import sys

PIP_PACKAGES = [("yt_dlp", "yt-dlp"), ("faster_whisper", "faster-whisper"), ("imageio_ffmpeg", "imageio-ffmpeg")]


def ensure_packages():
    for module, pkg in PIP_PACKAGES:
        try:
            importlib.import_module(module)
            print(f"OK  {pkg} 已安装")
        except ImportError:
            print(f"..  正在安装 {pkg} ...", flush=True)
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])
            importlib.import_module(module)
            print(f"OK  {pkg} 安装完成")


def detect_proxy():
    if os.environ.get("YT_PROXY"):
        print(f"OK  代理来自 YT_PROXY: {os.environ['YT_PROXY']}")
        return
    for port in (7897, 7890, 1080, 10809, 8080):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=1).close()
            print(f"OK  探测到本地代理 127.0.0.1:{port}，建议 set YT_PROXY=http://127.0.0.1:{port}")
            return
        except OSError:
            continue
    print("!!  未探测到本地代理；访问 YouTube 失败时请设置 YT_PROXY=http://127.0.0.1:<端口>")


def check_ffmpeg():
    import imageio_ffmpeg
    print(f"OK  ffmpeg: {imageio_ffmpeg.get_ffmpeg_exe()}")


def check_hf():
    try:
        socket.create_connection(("huggingface.co", 443), timeout=3).close()
        print("OK  huggingface.co 可达（whisper 模型首次使用时自动下载）")
    except OSError:
        print("!!  huggingface.co 不可达，请设置 HF_ENDPOINT=https://hf-mirror.com 后再运行转写")


def check_cpu():
    n = os.cpu_count() or 4
    workers = min(6, max(2, n // 2))
    print(f"OK  CPU {n} 核 → 推荐转写并行数 {workers}")


if __name__ == "__main__":
    ensure_packages()
    check_ffmpeg()
    detect_proxy()
    check_hf()
    check_cpu()
    print("READY")
