---
name: youtube-to-book
description: Turn YouTube content into reading products — two modes selected by user instruction. Mode A (EPUB 小书) - batch-convert videos/playlists/channels/lecture series into polished EPUB books with TOC; subtitles first, local parallel faster-whisper fallback; 5-stage resumable pipeline; volumes every N chapters. Mode B (公众号文章) - single video → Chinese transcript → 《人物》-style WeChat-article HTML (all inline styles, paste-ready for mp.weixin.qq.com). Trigger when user gives a YouTube link and says 整理成书/EPUB/小书/批量转写/每N讲一卷 (Mode A), or 翻译这个视频/搬运/公众号排版/按人物模板排版 (Mode B). Zero manual setup — dependencies auto-install on first run. Self-improving via misrecognition dictionary and per-batch evolution log.
---

# YouTube to Book

Turn YouTube content into books (Mode A) or WeChat articles (Mode B). Mode A proven on a 15-video channel batch and a 205-lecture university course; Mode B proven on podcast-interview translation (谷爱凌专访《TheBurnouts》).

## Mode routing (read user instruction first)

- **Mode A — EPUB 小书**: user wants a book/EPUB, batch processing, playlists/channels/courses, or says 整理成书、做成小书、批量转写、每N讲一卷.
- **Mode B — 公众号文章**: user wants a single article for WeChat, says 翻译这个视频、搬运、公众号排版、按《人物》模板排版, or already has a manuscript needing only formatting (enter Mode B at step 5).
- Ambiguous single-video request → ask once which product they want (book vs article).
- Both modes share the transcript-first principle: try subtitles before any audio transcription.

## First run (mandatory, both modes)

```bash
python scripts/bootstrap.py
```

Auto-installs yt-dlp / faster-whisper / imageio-ffmpeg via pip (ffmpeg bundled, no system install). Prints proxy and HuggingFace status. If YouTube is unreachable, set `YT_PROXY=http://127.0.0.1:<port>`; if huggingface.co is unreachable, set `HF_ENDPOINT=https://hf-mirror.com`. Re-run until it prints READY.

## Mode A — EPUB 小书流水线 (5 stages, all resumable)

Work in a fresh project directory. Run every script from that directory with the skill's `scripts/` path.

1. **List** (batch jobs only): `python scripts/list_videos.py <playlist_or_channel_url>` → `videos.tsv` (`id<TAB>title` per line, in playlist order). Skip for a single video.
2. **Transcript — subtitles first, whisper fallback.** For each video, ALWAYS try `python scripts/fetch_subs.py <id>` first (fast, free). On `NOSUB`, fall back: `python scripts/download_one.py <id>` → `python scripts/chunk_one.py <id>` → transcribe (below) → `python scripts/merge_chunks.py <id>`. Both paths yield `transcripts/<id>.txt`.
3. **Transcribe in parallel**: after chunking all videos of the batch, run `python scripts/launch_workers.py chunks/<id1> chunks/<id2> ...`. It spawns `min(6, cpu//2)` detached background workers that load the model once and resume automatically. Poll with `python scripts/worker_status.py` until `ALL DONE`. On a 12-core CPU expect ~5-6 min per hour of audio per worker, i.e. ~1 h wall time per 6 hours of audio.
4. **Polish** each `transcripts/<id>.txt` into a book chapter at `<卷目录>/articles/NN_标题.md`. Follow `references/polishing-guide.md` exactly (format contract, misrecognition fixing via `references/corrections-zh.md`, completeness rules). Long lectures: split the writing across multiple append operations.
5. **Build**: write `<卷目录>/manifest.json` (`series`, `volume`, optional `creator`), then `python scripts/build_epub.py <卷目录>` → EPUB with TOC, no images. Deliver the file path to the user for preview.

**Batch discipline (Mode A)**
- Default volume size: 5 chapters per EPUB unless the user says otherwise (they may say 每5讲一卷/每10篇一辑).
- Overlap stages: download/chunk the next batch while the current batch transcribes (transcription is CPU-bound, download is network-bound).
- Parallelize video downloads (network-bound, 4-6 at once is fine); never exceed 6 whisper workers (CPU-bound, more is slower).
- After a volume's EPUB is delivered, delete its `audio/` and `chunks/` files; keep `transcripts/` and `articles/`.
- Track progress in `<project>/progress.json` (`next_index` into `videos.tsv`) so interrupted sessions resume cleanly.

**Mode A failure handling**
- YouTube intermittent 403/SABR: retry — scripts already retry 3×; if still failing, wait a minute and re-run. All scripts skip finished work.
- A killed worker loses only its in-flight chunk; re-run `launch_workers.py` to resume.
- If a transcript has whole duplicated blocks (whisper loop artifact), note it for the polishing step — dedupe there, do not re-transcribe.

## Mode B — 公众号文章流水线 (6 steps)

Work in `D:\002-AI\AI work\总目录\任务\YYYY-MM-DD_<视频简称>\`. **Full contract lives in `references/wechat-guide.md` — read it before the first Mode B run.** Summary:

1. **Fetch transcript**: `scripts/fetch_transcript.py "<url>" --out <工作目录> --proxy http://127.0.0.1:7897` → `transcript.txt` + `meta.json`. On VideoUnavailable (proxy IP blocked), fall back to `scripts/fetch_via_gh.py` (GitHub Actions relay).
2. **Classify**: `zh*` language → no translation; 对谈 → dialogue manuscript (`**发言人：**内容`), 独白 → prose.
3. **Translate**: 意译为主、直译兜底, terms unified in-passing (Eileen Gu→谷爱凌), then a **mandatory full-text final review** before formatting.
4. **Illustrate (default ON)**: 3~5 subtitle-bearing HD frames + one-line grey captions → `<工作目录>\images\`.
5. **Format 《人物》-style**: manuscript markdown per `references/模板.md`, then `python scripts/wechat_article.py <文稿.md> [输出.html]` → single-file HTML, images base64-embedded, dialogue/prose paragraph-merging automatic. Verify with headless-browser screenshot.
6. **Deliver**: absolute path + paste instructions (browser open → Ctrl+A/C → WeChat editor; judge by phone preview).

## Optional: archive to GitHub

Only after the user approves a preview: push the EPUB/article (and `articles/` if asked) to the user's archive repo (`personal-information-source`, private; one folder per book named after the book title, new version replaces old), then delete the local files the user agreed to remove.

## Self-evolution loop (mandatory — this skill rewrites itself)

This skill is a living system. Every task MUST run both halves of the loop; the full protocol lives in `references/self-improvement.md`, and every evolution is versioned in `references/evolution-log.md`.

**At task START (self-awareness check, ~30 seconds):**
1. Read `references/evolution-log.md` — apply the latest tuned parameters (worker count, chunk length, subtitle languages) instead of the defaults in this file; the log wins whenever they disagree.
2. Skim `references/corrections-zh.md` categories to know which domains already have dictionaries.

**After EVERY delivered batch (evolution step, non-negotiable):**
1. Append batch metrics via `python scripts/log_run.py <project> <batch> <metrics>`.
2. Add every newly discovered misrecognition to `references/corrections-zh.md`.
3. Compare metrics against the log's benchmarks. Any faster/cheaper/reliabler finding (better chunk length, worker count, subtitle hit rate, retry pattern, prompt wording) → patch this SKILL.md or the scripts immediately. The skill's files are meant to be edited by its own user-agent.
4. Append a version entry to `references/evolution-log.md` (version number + date + what changed + measured effect).
5. Re-audit this SKILL.md: delete anything that went unused this run; keep it lean — context is a public good.

Discipline: verify every change (run the touched script on a small sample); never break resumability; project-specific settings stay in the project, only general improvements enter the skill.

## Reference files (read as needed)

- `references/polishing-guide.md` — Mode A book-chapter format contract and polishing rules (read before Mode A stage 4)
- `references/wechat-guide.md` — Mode B full contract: fetch/translate/illustrate/format/deliver, 《人物》 style table, WeChat-editor pitfalls (read before first Mode B run)
- `references/模板.md` — Mode B manuscript skeleton
- `references/corrections-zh.md` — growing dictionary of whisper misrecognitions for Chinese literary/historical content (load during Mode A stage 4; append after each batch)
- `references/self-improvement.md` — full self-optimization protocol (read after each batch)
- `references/workflow-notes.md` — battle-tested environment notes: proxy, SABR, timing benchmarks, disk usage
