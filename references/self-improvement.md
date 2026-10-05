# 自优化协议（Self-Improvement Loop）

本技能的核心特性：每完成一批次，执行本协议，让技能越用越强、越用越省 token。

## 触发时机

每次交付一卷 EPUB 之后、开始下一批之前，花少量 token 执行。不要跳过——省下的远比花的多。

## 四步协议

### 1. 记录数据

```bash
python scripts/log_run.py <project> <批次名> "videos=5 chunks=100 subs_hit=2 download_min=4 transcribe_min=62 polish_min=20 epub=1 errors=0"
```

指标从本次运行的日志直接统计（worker 日志里有每块耗时）。不确定的字段留空，不要编造。

### 2. 更新误识词典

把本批整理时发现的所有新误识词追加到 `references/corrections-zh.md`。下一批整理前先读词典批量替换——词典越厚，整理 agent 的试错越少、token 越省、质量越稳。

### 3. 分析并调参

对照项目里的 `performance-log.md`，问三个问题：

- **字幕命中率**：subs_hit 占比高吗？低的话检查 `fetch_subs.py` 的 SUB_LANGS 是否该加语言。
- **转写吞吐**：每块耗时是否高于基准（12 核约 300-400s/块、6 并行）？异常高→减少 WORKERS 或检查是否有其他进程抢 CPU；CPU 长期闲置→提高 WORKERS（不超过核数/2）。
- **失败模式**：下载失败集中在哪种错误？403/SABR→换代理或降并发；超时→检查 CHUNK_LEN 是否过大。

确认更优的参数后，**直接改 SKILL.md 或脚本里的默认值**——技能文件就是用来被改写的。

### 4. 登记进化版本

把本次改动以新版本号追加到 `references/evolution-log.md`：改了什么、依据哪批数据、前后效果对比，并同步更新文件顶部的「当前生效的调优参数」表。**下次任务开始时先读它**——进化日志的调优参数优先于 SKILL.md 默认值。

### 5. 精简 SKILL.md

每次使用后重新审视 SKILL.md：删掉这次没用上的段落，把反复查阅的参考内容保留在 references/。上下文窗口是公共资源，SKILL.md 越短，留给干活的 token 越多。

## 纪律

- 改动必须验证：改完脚本至少跑一次 `--help` 或小样本确认没语法错误。
- 永远不要破坏断点续跑能力（已有产物跳过是最高原则）。
- 不要为单次项目的特殊性改技能：项目专属配置放项目目录（progress.json、环境变量），通用改进才进技能。
- 误识词典只增不删；SKILL.md 只瘦不胖。
