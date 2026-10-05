# -*- coding: utf-8 -*-
"""EPUB 生成器（带目录、无配图，EPUB 3）。
用法: python scripts/build_epub.py <卷目录>
读取 <卷目录>/manifest.json 和 <卷目录>/articles/*.md，产出 <卷目录>/<series>_<volume>.epub

manifest.json:
{
  "series": "系列名",
  "volume": "卷一",
  "creator": "作者/来源（可选）",
  "lang": "zh-CN（可选，默认 zh-CN）"
}
articles/*.md 约定: 文件名排序即章节顺序；首个 '# ' 为章节标题；
'> ' 开头的连续行为信息行；'## ' 为节标题；其余为正文段；支持 **加粗**。
"""
import html
import json
import os
import re
import sys
import uuid
import zipfile

CSS = """
body{font-family:serif;line-height:1.8;margin:0 5%;color:#111;}
h1{font-size:1.4em;margin:1.2em 0 0.8em;}
h2{font-size:1.1em;margin:1.4em 0 0.6em;}
p{margin:0 0 1em;text-indent:2em;}
p.info{text-indent:0;color:#888;font-size:0.85em;margin-bottom:0.3em;}
nav ol{line-height:2;}
"""


def md_to_xhtml(md_text):
    title = ""
    body = []
    for ln in md_text.splitlines():
        ln = ln.rstrip()
        if not ln.strip():
            continue
        if ln.startswith("# "):
            title = ln[2:].strip()
        elif ln.startswith("## "):
            body.append(f"<h2>{html.escape(ln[3:].strip())}</h2>")
        elif ln.startswith("> "):
            body.append(f'<p class="info">{html.escape(ln[2:].strip())}</p>')
        else:
            t = html.escape(ln)
            t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
            body.append(f"<p>{t}</p>")
    return title, "\n".join(body)


def main(vol_dir):
    with open(os.path.join(vol_dir, "manifest.json"), encoding="utf-8") as f:
        meta = json.load(f)
    series, volume = meta["series"], meta["volume"]
    creator = meta.get("creator", "")
    lang = meta.get("lang", "zh-CN")
    art_dir = os.path.join(vol_dir, "articles")
    files = sorted(f for f in os.listdir(art_dir) if f.endswith(".md"))
    if not files:
        sys.exit("articles/ 里没有 md 文件")

    book_title = f"{series}·{volume}"
    uid = uuid.uuid5(uuid.NAMESPACE_URL, f"https://youtube-to-epub/{series}/{volume}").urn
    chapters = []
    for fn in files:
        with open(os.path.join(art_dir, fn), encoding="utf-8") as f:
            title, body = md_to_xhtml(f.read())
        chapters.append((fn[:-3], title, body))

    nav_items = "\n".join(f'<li><a href="{cid}.xhtml">{html.escape(t)}</a></li>' for cid, t, _ in chapters)
    nav = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{lang}">
<head><meta charset="utf-8"/><title>{book_title} 目录</title><link rel="stylesheet" href="style.css"/></head>
<body><nav epub:type="toc"><h1>{book_title} 目录</h1><ol>
{nav_items}
</ol></nav></body></html>"""

    manifest_items = "\n".join(f'<item id="{cid}" href="{cid}.xhtml" media-type="application/xhtml+xml"/>' for cid, _, _ in chapters)
    spine_items = "\n".join(f'<itemref idref="{cid}"/>' for cid, _, _ in chapters)
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="{lang}">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="uid">{uid}</dc:identifier>
<dc:title>{html.escape(book_title)}</dc:title>
<dc:language>{lang}</dc:language>
<dc:creator>{html.escape(creator)}</dc:creator>
</metadata>
<manifest>
<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
<item id="css" href="style.css" media-type="text/css"/>
{manifest_items}
</manifest>
<spine>
<itemref idref="nav"/>
{spine_items}
</spine>
</package>"""

    container = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""

    out = os.path.join(vol_dir, f"{series}_{volume}.epub")
    with zipfile.ZipFile(out, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/style.css", CSS, zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", nav, zipfile.ZIP_DEFLATED)
        for cid, t, body in chapters:
            chap = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="{lang}">
<head><meta charset="utf-8"/><title>{html.escape(t)}</title><link rel="stylesheet" href="style.css"/></head>
<body><h1>{html.escape(t)}</h1>
{body}
</body></html>"""
            z.writestr(f"OEBPS/{cid}.xhtml", chap, zipfile.ZIP_DEFLATED)

    print(f"已生成 {out}（{len(chapters)} 章，{os.path.getsize(out) // 1024} KB）")


if __name__ == "__main__":
    main(sys.argv[1])
