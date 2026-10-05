#!/usr/bin/env python3
"""HTML 文件 -> 剪贴板(CF_HTML 富文本 + 纯文本兜底), 可选打开公众号后台

用法:
  python to_clipboard.py article.html [--open]

CF_HTML 为 Windows 富文本剪贴板标准, 粘贴进公众号编辑器可保留排版。
"""
import argparse
import html as html_mod
import os
import re
import sys

MP_URL = "https://mp.weixin.qq.com/"


def build_cf_html(fragment: str) -> bytes:
    """按 MS HTML Clipboard 规范包裹 fragment, 偏移量为 UTF-8 字节"""
    header = (
        "Version:0.9\r\n"
        "StartHTML:%010d\r\n"
        "EndHTML:%010d\r\n"
        "StartFragment:%010d\r\n"
        "EndFragment:%010d\r\n"
    )
    pre = "<html><body><!--StartFragment-->"
    post = "<!--EndFragment--></body></html>"
    frag_b = fragment.encode("utf-8")
    pre_b = pre.encode("utf-8")
    post_b = post.encode("utf-8")
    hlen = len((header % (0, 0, 0, 0)).encode("utf-8"))
    start_html = hlen
    start_frag = hlen + len(pre_b)
    end_frag = start_frag + len(frag_b)
    end_html = end_frag + len(post_b)
    return (header % (start_html, end_html, start_frag, end_frag)).encode("utf-8") + pre_b + frag_b + post_b


def strip_to_text(fragment: str) -> str:
    t = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    t = re.sub(r"</p>|</h2>|</blockquote>|</li>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = html_mod.unescape(t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html_file")
    ap.add_argument("--open", action="store_true", help="同时打开公众号后台")
    args = ap.parse_args()

    try:
        fragment = open(args.html_file, encoding="utf-8").read()
    except OSError as e:
        print(f"ERROR: 读不到文件: {e}", file=sys.stderr)
        sys.exit(2)

    import win32clipboard
    import win32con

    cf_html = win32clipboard.RegisterClipboardFormat("HTML Format")
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(cf_html, build_cf_html(fragment))
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, strip_to_text(fragment))
    finally:
        win32clipboard.CloseClipboard()

    print(f"OK 剪贴板就绪 (HTML {len(fragment)} 字符), 到公众号正文 Ctrl+V")
    if args.open:
        os.startfile(MP_URL)


if __name__ == "__main__":
    main()
