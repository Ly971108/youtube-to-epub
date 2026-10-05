---
name: youtube-to-epub
description: Batch-convert YouTube videos, playlists, channels, or lecture series into polished EPUB books. Fetches subtitles when available, otherwise transcribes audio locally with parallel faster-whisper workers, polishes transcripts into book-quality chapters, and builds EPUB volumes with a table of contents. Use when the user wants to 下载YouTube视频文字稿/字幕、把博主视频或课程整理成书/EPUB/小书、批量转写视频、视频转文稿排版、每N篇出一辑. Zero manual setup — dependencies auto-install on first run. Includes a self-improvement loop that grows a misrecognition dictionary and tunes performance after every batch.
---

# YouTube to EPUB

Turn YouTube content into EPUB books. Proven on a 15-video channel batch and a 205-lecture university course.

## First run (mandatory)

```bash
python scripts/bootstrap.py
```

Auto-installs yt-dlp / faster-whisper / imageio-ffmpeg via pip (ffmpeg bundled, no system install). Prints proxy and HuggingFace status. If YouTube is unreachable, set `YT_PROXY=http://127.0.0.1:<port>`; if huggingface.co is unreachable, set `HF_ENDPOINT=https://hf-mirror.com`. Re-run until it prints READY.

## Pipeline (5 stages, all resumable)

Work in a fresh project directory. Run every script from that directory with the skill's `scripts/` path.

1. **List** (batch jobs only): `python scripts/list_videos.py <playlist_or_channel_url>` → `videos.tsv` (`id<TAB>title` per line, in playlist order). Skip for a single video.
2. **Transcript — subtitles first, whisper fallback.** For each video, ALWAYS try `python scripts/fetch_subs.py <id>` first (fast, free). On `NOSUB`, fall back: `python scripts/download_one.py <id>` → `python scripts/chunk_one.py <id>` → transcribe (below) → `python scripts/merge_chunks.py <id>`. Both paths yield `transcripts/<id>.txt`.
3. **Transcribe in parallel**: after chunking all videos of the batch, run `python scripts/launch_workers.py chunks/<id1> chunks/<id2> ...`. It spawns `min(6, cpu//2)` detached background workers that load the model once and resume automatically. Poll with `python scripts/worker_status.py` until `ALL DONE`. On a 12-core CPU expect ~5-6 min per hour of audio per worker, i.e. ~1 h wall time per 6 hours of audio.
4. **Polish** each `transcripts/<id>.txt` into a book chapter at `<卷目录>/articles/NN_标题.md`. Follow `references/polishing-guide.md` exactly (format contract, misrecognition fixing via `references/corrections-zh.md`, completeness rules). Long lectures: split the writing across multiple append operations.
5. **Build**: write `<卷目录>/manifest.json` (`series`, `volume`, optional `creator`), then `python scripts/build_epub.py <卷目录>` → EPUB with TOC, no images. Deliver the file path to the user for preview.

## Batch discipline

- Default volume size: 5 chapters per EPUB unless the user says otherwise (they may say 每5讲一卷/每10篇一辑).
- Overlap stages: download/chunk the next batch while the current batch transcribes (transcription is CPU-bound, download is network-bound).
- Parallelize video downloads (network-bound, 4-6 at once is fine); never exceed 6 whisper workers (CPU-bound, more is slower).
- After a volume's EPUB is delivered, delete its `audio/` and `chunks/` files; keep `transcripts/` and `articles/`.
- Track progress in `<project>/progress.json` (`next_index` into `videos.tsv`) so interrupted sessions resume cleanly.

## Failure handling

- YouTube intermittent 403/SABR: retry — scripts already retry 3×; if still failing, wait a minute and re-run. All scripts skip finished work.
- A killed worker loses only its in-flight chunk; re-run `launch_workers.py` to resume.
- If a transcript has whole duplicated blocks (whisper loop artifact), note it for the polishing step — dedupe there, do not re-transcribe.

## Optional: archive to GitHub

Only after the user approves a preview: push the EPUB (and `articles/` if asked) to the user's archive repo, then delete the local files the user agreed to remove. GitHub repo names are ASCII-only — use a pinyin/English name with a Chinese description.

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

- `references/polishing-guide.md` — book-chapter format contract and polishing rules (read before stage 4)
- `references/corrections-zh.md` — growing dictionary of whisper misrecognitions for Chinese literary/historical content (load during stage 4; append after each batch)
- `references/self-improvement.md` — full self-optimization protocol (read after each batch)
- `references/workflow-notes.md` — battle-tested environment notes: proxy, SABR, timing benchmarks, disk usage
