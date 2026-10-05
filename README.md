# youtube-to-epub

> 把 YouTube 视频 / 播放列表 / 频道 / 系列课程，批量整理成带目录的 EPUB 小书。
> Batch-convert YouTube videos, playlists, channels, or lecture series into polished EPUB books.

一个给 AI Agent 使用的技能（Skill），兼容 Kimi Work / Claude / Codex 等支持 SKILL.md 规范的平台。经过两个真实项目验证：15 个视频的频道批量成书、205 讲大学课程逐卷成书。

An AI-agent skill following the standard SKILL.md specification. Battle-tested on a 15-video channel batch and a 205-lecture university course.

## ✨ 功能 Features

- **零门槛 Zero setup** — `bootstrap.py` 自动安装全部依赖（yt-dlp、faster-whisper，ffmpeg 自带），自动探测代理与模型镜像
- **字幕优先 Subtitles first** — 命中字幕比语音转写快约 100 倍；抓不到自动降级本地 whisper 转写
- **并行转写 Parallel transcription** — 常驻 worker 按 CPU 核数自动并行（最多 6 路），模型只加载一次，全程断点续跑
- **书稿整理 AI polishing** — 口语清理、繁转简、误识修正（内置 100+ 条词典）、自动加小节标题，内容完整不省略
- **EPUB 3 输出** — 带目录导航、衬线排版、无配图，微信读书 / Apple Books 可用
- **🧬 自进化 Self-evolving** — 每批任务后自动记录性能数据、扩充误识词典、调参并改写自身配置，版本化进化日志，越用越快、越省 token

## 🚀 快速开始 Quick Start

1. 安装技能：把本仓库克隆到 Agent 的技能目录，或下载 [Releases](../../releases) 里的 `youtube-to-epub.skill` 导入。

   ```bash
   # Kimi Code / Claude 风格的技能目录示例
   git clone https://github.com/Ly971108/youtube-to-epub ~/.config/agents/skills/youtube-to-epub
   ```

2. 对 Agent 说：

   > 「把这个 YouTube 播放列表整理成 EPUB 小书，每 5 个视频一卷：https://youtube.com/playlist?list=...」

   单个视频：「把这个视频的文字稿整理成 EPUB：https://youtu.be/...」

3. Agent 会自动完成：环境自检 → 拉清单 → 字幕/转写 → 整理书稿 → 出 EPUB 预览。

## 📁 结构 Structure

```
youtube-to-epub/
├── SKILL.md                      # 技能主文件（触发描述 + 5 阶段流水线 + 自进化入口）
├── scripts/
│   ├── bootstrap.py              # 环境自检 + 自动安装依赖
│   ├── list_videos.py            # 拉播放列表/频道清单
│   ├── fetch_subs.py             # 字幕优先抓取
│   ├── download_one.py           # 音频下载（重试/续传/代理）
│   ├── chunk_one.py              # 音频切块（240s+10s 重叠）
│   ├── transcribe_worker.py      # 常驻转写进程（断点续跑）
│   ├── launch_workers.py         # 并行启动转写进程组
│   ├── worker_status.py          # 转写进度查询
│   ├── merge_chunks.py           # 合并块转写（去重叠）
│   ├── build_epub.py             # EPUB 3 生成器
│   └── log_run.py                # 批次性能记录
└── references/
    ├── polishing-guide.md        # 书稿整理契约
    ├── corrections-zh.md         # 中文误识词典（自增长）
    ├── self-improvement.md       # 自进化协议
    ├── evolution-log.md          # 版本化进化日志
    └── workflow-notes.md         # 实战踩坑与性能基准
```

## ⚙️ 环境要求 Requirements

- Python 3.9+，可 pip 安装包；Windows / macOS / Linux 通用
- 访问 YouTube 需要代理时：`YT_PROXY=http://127.0.0.1:端口`
- HuggingFace 不可达时：`HF_ENDPOINT=https://hf-mirror.com`
- 以上 `bootstrap.py` 会自动探测并提示

## 📊 性能基准 Benchmarks

| 场景 | 实测 |
|---|---|
| 12 核 CPU，whisper small，6 路并行 | 约 6 倍速转写 |
| 一卷 5 讲（约 7.5 小时音频） | ≈ 1.5 小时出 EPUB |
| 字幕命中的视频 | 几分钟成稿 |
| 磁盘（按卷清理后） | 峰值约 2 GB |

## 🧬 自进化机制 Self-Evolution

每次任务自动运行闭环，让技能不断变强：

1. **任务开始**：读取 `evolution-log.md`，用最新调优参数覆盖默认值
2. **每批交付后**：记录性能数据 → 回写误识词典 → 对比基准调参并改写自身默认值 → 登记新版本 → 精简 SKILL.md
3. **版本化**：每次进化都有版本号、数据依据和前后效果对比

详见 [references/self-improvement.md](references/self-improvement.md) 与 [references/evolution-log.md](references/evolution-log.md)。

## ⚖️ 许可 License

[MIT](LICENSE) © 2026 Ly971108

整理稿仅供个人学习使用，请注意原视频版权与课程授权（如台大开放式课程为 CC BY-NC-SA）。
Polished transcripts are for personal study only — respect the original videos' copyrights and licenses.
