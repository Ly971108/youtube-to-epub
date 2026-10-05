# 实战环境笔记（Workflow Notes）

来自两个真实项目（15 视频频道批量、205 讲大学课程）的踩坑记录。新环境先用 bootstrap.py 自检，再对照本文件。

## 网络与下载

- YouTube 访问通常需要本地代理：`set YT_PROXY=http://127.0.0.1:7897`（端口以 bootstrap 探测为准）。
- 间歇性 403/SABR 错误是常态，重试即成功；脚本已内置 3 次重试。批量下载时 4-6 个并行没问题。
- 云端中转（GitHub Actions 跑 yt-dlp 下**音频**）会被 YouTube bot check 拦截，不可行；但抓**字幕**走 GitHub Actions 中转可行（字幕接口风控低）——本机代理出口 IP 被拦（特征：浏览器能看但脚本全客户端 ERROR / VideoUnavailable）时，可用云端中转折取字幕。浏览器 cookie 提取会被浏览器锁文件拦住，不可靠。本机 yt-dlp + 代理 + 重试是音频唯一稳定路线。
- **字幕优先**：`fetch_subs.py` 命中一次省下约 20-30 分钟转写。许多课程/频道有自动字幕（zh-Hant/zh-Hans/en 都在默认探测列表）。
- `TranscriptsDisabled`：视频完全无字幕（含自动字幕），走 whisper 路线；whisper 也不可行时提示用户换视频。

## 转写性能基准（whisper small / int8 / cpu_threads=2）

| CPU | 并行数 | 每块(250s音频)耗时 | 吞吐 |
|---|---|---|---|
| 12 核 | 6 | 300-400s | 约 6 倍速（1 小时音频 ≈ 10 分钟/进程） |

- 超过 6 个 worker 总吞吐不升反降；少于核数一半则浪费。
- 常驻 worker（模型加载一次）比每块起一个进程省约 15s/块——批量任务务必用 launch_workers.py。
- 首次使用 small 模型需从 HuggingFace 下载约 500MB；网络不通设 HF_ENDPOINT=https://hf-mirror.com。
- 更大模型（medium/large）质量更好但慢 3-10 倍，文学类课程 small + 误识词典已够；要换设 WHISPER_MODEL。

## 磁盘与清理

- 一讲 90 分钟课程 ≈ 60-100MB webm + 等量切块。每卷 EPUB 交付后删 audio/ 和 chunks/，保留 transcripts/ 和 articles/。
- 205 讲全量约需 40GB 峰值（不清理的话）；按卷清理后峰值约 2GB。

## EPUB

- build_epub.py 产出 EPUB 3（nav 目录、衬线样式、无配图），已验证可在微信读书/Apple Books 正常打开。
- 卷目录下 manifest.json 的 creator 字段写原作者，如 "欧丽娟（台大开放式课程）"。
