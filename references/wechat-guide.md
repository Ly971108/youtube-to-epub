# 公众号文章模式（Mode B）完整规范

本文稿为 youtube-to-book 的**公众号文章模式**（Mode B）完整契约：YouTube 单视频 → 中文文字稿 → 《人物》公众号排版 HTML。SKILL.md 只保留流程骨架，本文件是执行细节的唯一权威。

## 执行流程（6 步）

### 第 1 步：取文字稿
- 建工作目录 `D:\002-AI\AI work\总目录\任务\YYYY-MM-DD_<视频简称>\`
- 执行：
  `python "D:\002-AI\AI work\总目录\Skill\youtube-to-book\scripts\fetch_transcript.py" "<url>" --out <工作目录> --proxy http://127.0.0.1:7897`
  → 得 `transcript.txt` + `meta.json`
- 报 VideoUnavailable（本机代理出口 IP 被 YouTube 拦，特征：浏览器能看但脚本全客户端 ERROR）→ 自动走 GitHub 中转：
  `python "D:\002-AI\AI work\总目录\Skill\youtube-to-book\scripts\fetch_via_gh.py" "<url>" --out <工作目录>`（首次需 `gh auth login`）

### 第 2 步：判断内容形态
- 读 meta.json：`language_code` 以 `zh` 开头 → 免翻译直接整理文稿；否则进入翻译
- 通读全稿判断形态：
  - **对谈/访谈** → 对话稿：`**发言人：**内容`；无法分辨哪位主持人时统一标「**主持人：**」
  - **独白/vlog/演讲** → 段落式文稿

### 第 3 步：翻译（边翻边统一 + 全文终审）
- 边翻边统一：不单独列术语表，但人名、品牌、专有名词、固定译法必须前后一致（如 Eileen Gu→谷爱凌，播客名保留原文）
- 意译为主、直译兜底：不生硬逐句对译，保持中英文各自的美感；译文逻辑必须与全篇上下文连得上（访谈的问答呼应、指代关系）
- **全文终审（必做）**：翻完通读全稿，确认无孤立句子、前后意思到位、术语一致，达到专业翻译水准后才进排版

### 第 4 步：配图（默认执行）
- 浏览器打开视频，按文稿节奏截 3~5 张**带字幕的高清图**（对谈类优先截有对话内容的画面；按视频时间点定位）
- 截图宽度取播放器原始分辨率，不要压缩糊图；每张配一句图注
- 存入 `<工作目录>\images\`，文稿中以 `![图注](images/xxx.jpg)` 引用
- 内建浏览器面板不可像素截图时（surface-not-painted）走离线方案：`yt-dlp -f "bv[height<=1080][ext=mp4]" --proxy http://127.0.0.1:7897` 下载视频 → `imageio-ffmpeg` 按时间点抽帧 → 用 cues.json（youtube_transcript_api 带时间轴抓取）取该时刻字幕文本 → PIL 画白字黑底字幕条烧到帧上（Arial 44px、半透明黑底、底部居中）

### 第 5 步：《人物》排版
- 文稿写成 markdown（格式见 `references/模板.md`）：`# `大标题 / `## `小标题 / `> `信息行 / `![图注](路径)` / `**发言人：**内容` / 正文行
- 执行：
  `python "D:\002-AI\AI work\总目录\Skill\youtube-to-book\scripts\wechat_article.py" <文稿.md> [输出.html]`
  → 单文件 HTML（图片自动 base64 内嵌），段落合并由生成器自动处理
- 小标题：全文 3~5 个，按内容自动提炼，简洁、有信息量、让人眼前一亮（vlog 同样生成）
- 开头信息行（14px 灰）：原标题/节目/视频链接，默认保留；"说明：本文根据…翻译整理"这类译者说明默认删除
- 生成后 headless 浏览器截图校验排版：
  `"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless --disable-gpu --user-data-dir="$TEMP/edgeheadless" --screenshot=<预览.png> --window-size=760,3000 --hide-scrollbars "file:///<输出.html>"`

### 第 6 步：交付
- 报告 HTML 绝对路径 + 操作指引：浏览器打开 → Ctrl+A → Ctrl+C → 粘进公众号后台正文；标题栏手填；**效果以手机预览为准**（编辑器画布的间距显示不可信）
- 可选：`python "D:\002-AI\AI work\总目录\Skill\youtube-to-book\scripts\to_clipboard.py" <article.html> --open` 复制到剪贴板并打开公众号后台

## 排版规范（逐项核对《人物》原文定稿，全内联样式、无 class、无空行段落）

| 元素 | 样式 |
|---|---|
| 文章大标题 | 18px 加粗，段 margin:0 16px 24px |
| 正文 | 段 `<p style="margin-left:16px;margin-right:16px;margin-bottom:24px;line-height:1.75em;">`，文字包 `<span style="font-size:15px;">`（段不写死字号，行距跟随继承字号） |
| 小标题 | 16px 加粗，margin-top:36px;margin-bottom:24px |
| 开头信息行 | 14px #888888，margin-bottom:10px 紧凑排列 |
| 发言人 | `<strong>名字：</strong>` 纯黑加粗，正文一律不加粗 |
| 配图 | 通栏 `width:100%`，与 12px #888888 图注同段，`line-height:1em` |
| 段落间距 | 只靠段 margin-bottom:24px，**禁止空行段落** |
| HTML 源码 | 元素之间不换行（防编辑器把空白转成多余空行） |

**段落合并（生成器自动识别模式）**：
- 对谈：同一发言人一轮发言合并成段，超过 6 句自动切段；换人另起段（参数 `DIALOGUE_MAX_SENT`）
- 非对谈：按手机 3~5 行（约 100 字）合并成段（参数 `PROSE_TARGET_CHARS`）
- 「」引语独立段，不参与合并

## 排错表（踩坑即追加）

- **VideoUnavailable 但浏览器能看**（2026-10-04 已踩）：代理出口 IP 被 YouTube 拦，换节点无效 → 直接走 fetch_via_gh.py 云端中转
- **粘贴进公众号后样式全丢/变色**（2026-10-04 已踩）：样式写在外部 `<style>`+class 里，粘贴时被剥离 → 必须全内联样式
- **粘贴后段间距被放大一倍**（2026-10-04 已踩）：HTML 元素间的换行被编辑器转成多余空行 → 生成器元素间不换行；间距只段 margin-bottom 控制
- **发言人名后残留字面 `**`、整段被加粗**（2026-10-04 已踩）：合并重组发言人标记时冒号必须留在星号外（`**名字**：内容`），否则正则不匹配掉进兜底加粗分支
- **公众号编辑器里空段落样式被剥**：信息行必须每行独立成段（同配图注结构），同段多行用 `<br>` 会被编辑器剥样式
- fetch_via_gh 报 auth 错误：先 `gh auth login`；超时：Actions 队列拥堵，隔几分钟重试
- 网络错误：本机访问 YouTube 需代理 `--proxy http://127.0.0.1:7897`（Clash Verge 端口）
- `TranscriptsDisabled`：视频无字幕且无音频转写需求时，提示用户换视频；或改走 Mode A 的 whisper 转写路径
- headless 截图失败/截图空白：Edge 加 `--user-data-dir="$TEMP/edgeheadless"` 独立配置目录
- YouTube 页面有前置广告（`.ad-showing`，video 时长异常短）→ 点 `.ytp-skip-ad-button` 或等广告结束再操作播放器
- 播放器 `getPlayerState()` 返回 -1（unstarted）且 playVideo 无效 → 直接 `document.querySelector('video').muted=true; v.play()`

## 并行策略

- 常规单篇：串行即可
- 超长稿件（>2 万字）分段翻译可拆多个子 agent 并行，术语表（轻量的、边翻边记的）先行同步；拼接后必须全文终审
- 第 1 步拉字幕与第 4 步浏览器截图准备无依赖，可并行

## 已定决策记录（2026-10-04 用户确认）

1. 发言太长需切断：对谈每段上限 6 句
2. 非对谈每段 3~5 行（约 100 字）
3. 配图截帧每篇默认执行
4. 小标题自动生成 3~5 个
5. 边翻边统一；翻译完整后全文终审，要求意思到位、不孤立、专业翻译水准

（2026-10-05 合并入 youtube-to-book，原独立 skill youtube翻译排版skill 退役。）
