# -*- coding: utf-8 -*-
"""「人物同款」公众号排版生成器

用法:
    python wechat_article.py 文稿.md [输出.html]

规则（Markdown 写法）:
    # 标题            → 18px 加粗（文章大标题，一个）
    ## 小标题         → 16px 加粗（人物同款小标题，建议 3~5 个）
    > 信息行          → 14px 灰色（来源/译者/链接等说明，每行一条）
    ![配图说明](图.jpg) → 通栏图片 + 12px 灰色图注（图片相对 md 文件所在目录引用，自动内嵌 base64）
    **发言人：**内容  → 发言人名纯黑加粗
    其它行            → 正文段落（文字包 15px span，人物同款；行高 1.75em 跟随段落）

排版参数（全部内联样式，复制粘贴进公众号后台不丢）:
    正文   <p style="margin-left:16px;margin-right:16px;line-height:1.75em;">
    空行   同结构 p 内放 <br/>，段落间距靠空行段落
"""
import re, base64, io, os, sys

def b64img(base_dir, rel):
    p = os.path.join(base_dir, rel.replace('/', os.sep))
    ext = os.path.splitext(p)[1].lstrip('.').lower().replace('jpg', 'jpeg')
    return 'data:image/%s;base64,' % ext + base64.b64encode(open(p, 'rb').read()).decode()

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

P   = '<p style="margin-left:16px;margin-right:16px;margin-bottom:24px;line-height:1.75em;">%s</p>'
PM  = '<p style="margin-left:16px;margin-right:16px;margin-bottom:10px;line-height:1.75em;">%s</p>'
PH2 = '<p style="margin-left:16px;margin-right:16px;margin-top:36px;margin-bottom:24px;line-height:1.75em;">%s</p>'
# 正文：人物同款——段内文字包 15px span；段落间距由 p 的 margin-bottom 控制，不用空行段落
BODY = '<span style="font-size:15px;">%s</span>'

SENT_END = re.compile(r'(?<=[。！？；])')
# 段落合并参数：
# 对谈模式——同一发言人一轮发言合并成段，超过 DIALOGUE_MAX_SENT 句自动切断；
# 非对谈模式——按手机 3~5 行（约 PROSE_TARGET_CHARS 字）合并成段
DIALOGUE_MAX_SENT = 6
PROSE_TARGET_CHARS = 100

def split_sentences(text):
    return [s for s in SENT_END.split(text) if s.strip()]

def is_dialogue(lines):
    return any(re.match(r'^\*\*(.+?)\*\*：', l.strip()) for l in lines)

def merge_lines(lines, dialogue=None):
    """合并短行为段（对谈按句数切段、非对谈按字数成段）。
    发言人变化/小标题/配图/信息行/引语处另起段。返回合并后的 markdown 行列表。"""
    if dialogue is None:
        dialogue = is_dialogue(lines)
    out, buf = [], []
    turn_speaker = None   # 当前 buf 属于哪位发言人（None=旁白）
    turn_start = False    # buf 是否为某发言人发言的开头（需要保留加粗名）

    def flush():
        nonlocal buf, turn_start
        if not buf:
            return
        if dialogue:
            while buf:  # 一轮发言过长时按 DIALOGUE_MAX_SENT 句切断
                chunk, buf = buf[:DIALOGUE_MAX_SENT], buf[DIALOGUE_MAX_SENT:]
                line = ''.join(chunk)
                if turn_start and turn_speaker:
                    line = '**%s**：%s' % (turn_speaker, line)  # 冒号在星号外，与文稿原格式一致
                out.append(line)
                turn_start = False
        else:
            line = ''.join(buf)
            buf = []
            if turn_start and turn_speaker:
                line = '**%s**：%s' % (turn_speaker, line)
            out.append(line)
            turn_start = False

    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith('#') or s.startswith('>') or s.startswith('![') or s.startswith('「'):
            flush()
            out.append(s)
            turn_speaker, turn_start = None, False
            continue
        m = re.match(r'\*\*(.+?)\*\*：(.*)', s)
        if m:
            flush()                       # 发言人变化，另起段
            turn_speaker, turn_start = m.group(1), True
            buf.extend(split_sentences(m.group(2)))
        else:
            buf.extend(split_sentences(s))
        if not dialogue and sum(len(x) for x in buf) >= PROSE_TARGET_CHARS:
            flush()
    flush()
    return out

def render(md_path, out_path):
    base_dir = os.path.dirname(os.path.abspath(md_path))
    md = io.open(md_path, encoding='utf-8').read()
    lines = merge_lines(md.split('\n'))

    body = []
    i, n = 0, len(lines)
    while i < n:
        ln = lines[i].strip()
        if not ln:
            i += 1; continue
        if ln.startswith('# '):  # 文章大标题：18px 加粗
            body.append(P % ('<span style="font-size:18px;font-weight:bold;">%s</span>' % esc(ln[2:])))
        elif ln.startswith('## '):  # 小标题：16px 加粗，上间距加大
            body.append(PH2 % ('<span style="font-size:16px;font-weight:bold;">%s</span>' % esc(ln[3:])))
        elif ln.startswith('> '):  # 信息行：14px 灰，每行独立成段、紧凑排列
            while i < n and lines[i].strip().startswith('> '):
                m = esc(lines[i].strip()[2:])
                m = re.sub(r'^\*\*(.+?)\*\*：', r'\1：', m)
                body.append(PM % ('<span style="font-size:14px;color:#888888;">%s</span>' % m))
                i += 1
            continue
        elif ln.startswith('!['):  # 配图：图+图注同段（人物同款），图片相对 md 所在目录引用、自动内嵌 base64
            mm = re.match(r'!\[(.*?)\]\((.*?)\)', ln)
            body.append('<p style="margin-left:16px;margin-right:16px;margin-bottom:24px;line-height:1em;">'
                        '<img style="width:100%%;display:block;" src="%s">'
                        '<span style="font-size:12px;color:#888888;">%s</span></p>'
                        % (b64img(base_dir, mm.group(2)), esc(mm.group(1))))
        elif ln.startswith('**'):  # 发言人：纯黑加粗，正文 15px
            mm = re.match(r'\*\*(.+?)\*\*：(.*)', ln)
            if mm:
                content = '<strong>%s：</strong>%s' % (esc(mm.group(1)), esc(mm.group(2)))
            else:
                content = '<strong>%s</strong>' % esc(ln.strip('*'))
            body.append(P % BODY % content)
        else:  # 正文段落：15px（人物同款）
            body.append(P % BODY % esc(ln))
        i += 1

    html = u'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s</title>
<style>
  /* 仅用于本地预览，模拟微信客户端默认渲染；粘贴时不会带走 */
  body { margin:0; padding:0; background:#fff; }
  #js_content { max-width:677px; margin:0 auto; padding:24px 0 48px;
    font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
    font-size:17px; color:#3f3f3f; }
</style>
</head>
<body>
<div id="js_content">
%s
</div>
</body>
</html>'''
    title = esc(lines[0].lstrip('# ').strip()) if lines else ''
    # 元素之间不加换行，避免复制粘贴时编辑器把空白转成多余空行
    io.open(out_path, 'w', encoding='utf-8').write(html % (title, ''.join(body)))
    print('OK', out_path, os.path.getsize(out_path))

if __name__ == '__main__':
    md = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(md)[0] + '.html'
    render(md, out)
