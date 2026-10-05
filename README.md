# youtube-to-book 使用说明书

把 YouTube 内容变成两种阅读产品，按你的指令自动选择模式：

- **模式 A — EPUB 小书**：视频 / 播放列表 / 频道 / 系列课程，批量整理成带目录的 EPUB 小书（已在 15 视频频道批量、205 讲大学课程上验证）
- **模式 B — 公众号文章**：单个视频 → 中文文字稿 → 《人物》公众号排版 HTML，全选复制即可粘贴进公众号后台（已在播客访谈翻译上验证，如谷爱凌专访《TheBurnouts》）

## 功能一览

### 模式 A：EPUB 小书

| 功能 | 说明 |
|---|---|
| 环境自检与自动安装 | `bootstrap.py` 一键检查并自动 pip 安装全部依赖（yt-dlp、faster-whisper、ffmpeg 随 imageio 自带），探测代理与模型源，**无需手工安装任何程序** |
| 清单拉取 | `list_videos.py` 拉取播放列表/频道全部视频 ID 与标题，顺序即讲序 |
| 字幕优先 | `fetch_subs.py` 优先抓官方/自动字幕（比转写快约 100 倍），抓不到自动降级 whisper |
| 音频下载 | `download_one.py` 断点续传、失败自动重试 3 次、支持代理 |
| 并行转写 | `launch_workers.py` 按 CPU 核数自动算并行数（最多 6），常驻进程模型只加载一次，`worker_status.py` 查进度，中断后重跑自动续传 |
| 书稿整理 | AI 按 `polishing-guide.md` 契约整理：口语清理、繁转简、误识修正、小节标题、信息行，内容完整不省略 |
| EPUB 生成 | `build_epub.py` 产出 EPUB 3（带目录导航、衬线排版、无配图），微信读书/Apple Books 可用 |
| 批量纪律 | 下载与转写流水线重叠、每卷交付后清理大文件、`progress.json` 记录进度跨会话续跑 |

### 模式 B：公众号文章（《人物》排版）

| 功能 | 说明 |
|---|---|
| 字幕下载（双通道） | `fetch_transcript.py` 走本机代理抓文字稿；代理 IP 被拦时自动切 `fetch_via_gh.py`（GitHub Actions 云端中转） |
| 智能判形 | 中文视频免翻译直接整理；对谈→对话稿，独白/vlog→段落稿 |
| 翻译规范 | 意译为主、直译兜底，术语边翻边统一，翻完**全文终审**（专业翻译水准） |
| 配图 | 默认截 3~5 张带字幕高清帧 + 灰色图注；浏览器不可截时走离线抽帧+字幕烧录方案 |
| 《人物》排版 | `wechat_article.py` 生成单文件 HTML：全内联样式、图片 base64 内嵌、对谈超 6 句自动切段、小标题自动提炼，粘贴公众号后台样式不丢 |
| 交付 | `to_clipboard.py` 一键复制进剪贴板并打开公众号后台；以手机预览为准 |

### 两种模式共有

| 功能 | 说明 |
|---|---|
| **自优化（核心特色）** | 每批完成后自动执行自优化协议：记录性能数据 → 扩充误识词典 → 分析调参并改写自身 SKILL.md → 精简上下文。技能越用越快、越省 token、质量越稳 |
| GitHub 归档 | 预览确认后推送到归档仓库（personal-information-source，一书一目录、新版覆盖旧版），再删除本地中间文件 |

## 快速开始（对任何 AI 模型）

1. 安装技能：把 `youtube-to-book/` 目录放到模型的技能目录（Kimi Work / Claude / Codex 等通用），或直接把 `youtube-to-book.skill` 导入支持该格式的平台。
2. 对模型说（模式 A）：「把这个 YouTube 播放列表整理成 EPUB 小书，每 5 个视频一卷：<链接>」
   或（模式 B）：「翻译这个视频，按《人物》公众号排版生成 HTML：<链接>」
3. 模型按 SKILL.md 的模式路由自动执行全流程，交付成品路径。

已有文稿只要排版时说：「按人物模板排版这篇稿子」（直接进模式 B 第 5 步）。

## 目录结构

```
youtube-to-book/
├── SKILL.md                      # 技能主文件（模式路由 + 双流水线 + 自优化入口）
├── scripts/
│   ├── bootstrap.py              # 环境自检+自动安装依赖（双模式共用）
│   ├── list_videos.py            # [A] 拉播放列表/频道清单
│   ├── fetch_subs.py             # [A] 字幕优先抓取
│   ├── download_one.py           # [A] 音频下载（重试/续传/代理）
│   ├── chunk_one.py              # [A] 音频切块（240s+10s 重叠）
│   ├── transcribe_worker.py      # [A] 常驻转写进程（断点续跑）
│   ├── launch_workers.py         # [A] 并行启动转写进程组
│   ├── worker_status.py          # [A] 转写进度查询
│   ├── merge_chunks.py           # [A] 合并块转写（去重叠）
│   ├── build_epub.py             # [A] EPUB 3 生成器
│   ├── fetch_transcript.py       # [B] 字幕下载（本机代理）
│   ├── fetch_via_gh.py           # [B] 字幕下载（GitHub 云端中转）
│   ├── wechat_article.py         # [B] 《人物》排版 HTML 生成器
│   ├── to_clipboard.py           # [B] 复制到剪贴板+打开公众号后台
│   └── log_run.py                # 批次性能记录
└── references/
    ├── polishing-guide.md        # [A] 书稿整理契约（格式/规则/自审清单）
    ├── wechat-guide.md           # [B] 公众号模式完整契约（流程/排版规范表/排错表）
    ├── 模板.md                    # [B] 文稿格式骨架
    ├── corrections-zh.md         # 中文误识词典（100+ 条，自增长）
    ├── self-improvement.md       # 自优化协议（四步循环）
    ├── evolution-log.md          # 进化日志（版本+调优参数）
    └── workflow-notes.md         # 实战踩坑与性能基准
```

## 环境要求

- Python 3.9+，能 pip 安装包即可；Windows/macOS/Linux 通用。
- 访问 YouTube 需要代理时，设置环境变量 `YT_PROXY=http://127.0.0.1:端口`。
- HuggingFace 不可达时，设置 `HF_ENDPOINT=https://hf-mirror.com`。
- 以上两条 `bootstrap.py` 会自动探测并提示。
- 模式 B 的 GitHub 中转首次使用需 `gh auth login`。

## 自优化机制说明

技能内置「越用越强」循环，由 AI 在每批任务后自动执行：

1. **数据记录**：每批的视频数、块数、各阶段耗时、字幕命中率写入项目性能日志；
2. **词典增长**：整理中发现的 whisper 误识词（如人名书名）回写词典，下次先批量替换再精修，省 token、少出错；
3. **参数调优**：对比历史基准，自动调整并行数、块长等参数，确认更优后**改写技能自身的默认值**；
4. **上下文瘦身**：每轮精简 SKILL.md，把低频内容移到按需加载的 references/，给干活留更多 token。

## 性能基准（实测）

- 12 核 CPU、whisper small：约 6 倍速转写，一卷 5 讲（约 7.5 小时音频）≈ 1.5 小时出 EPUB；
- 字幕命中的视频：几分钟成稿；
- 磁盘：按卷清理后峰值约 2GB。

## 许可与用途

整理稿仅供个人学习使用，请注意原视频版权与课程授权（如台大开放式课程为 CC BY-NC-SA）。
