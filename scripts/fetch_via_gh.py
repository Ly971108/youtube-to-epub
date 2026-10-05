#!/usr/bin/env python3
"""经 GitHub Actions 中转下载 YouTube 字幕（绕过本机代理被拦）。

用法:
  python fetch_via_gh.py <url> [--out DIR]

前置: gh CLI 已登录（gh auth login）。
自动建私有仓 <you>/yt-transcript-relay 并推送 workflow（首次），随后触发 run 并轮询下载产物。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

GH = shutil.which("gh") or r"C:\Program Files\GitHub CLI\gh.exe"
if not Path(GH).exists() and not shutil.which("gh"):
    print("ERROR: 未找到 gh CLI，先 winget install GitHub.cli", file=sys.stderr)
    sys.exit(2)

REPO_NAME = "yt-transcript-relay"
SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "relay_repo"


def sh(args, check=True, capture=True):
    r = subprocess.run(args, capture_output=capture, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}\nSTDOUT:{(r.stdout or '')[-800:]}\nSTDERR:{(r.stderr or '')[-800:]}")
    return r


def ensure_repo(owner):
    repo = f"{owner}/{REPO_NAME}"
    has_wf = sh([GH, "api", f"repos/{repo}/contents/.github/workflows/transcript.yml"], check=False).returncode == 0
    exists = sh([GH, "repo", "view", repo], check=False).returncode == 0
    if exists and has_wf:
        return repo
    import shutil
    tmp = Path(os.environ.get("TEMP", ".")) / f"{REPO_NAME}-bootstrap"
    shutil.rmtree(tmp, ignore_errors=True)
    if exists:
        size = sh([GH, "api", f"repos/{repo}", "-q", ".size"], check=False).stdout.strip()
        if size not in ("0", ""):
            print("仓已存在但缺 workflow，克隆补齐")
            sh([GH, "repo", "clone", repo, str(tmp)], capture=False)
        else:
            print("空仓，直接初始化推送")
            tmp.mkdir(parents=True, exist_ok=True)
    else:
        print(f"首次运行: 建私有仓 {repo} 并推送 workflow")
        tmp.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        rc = sh(["robocopy", str(TEMPLATE), str(tmp), "/E"], check=False, capture=False).returncode
        if rc >= 8:
            raise RuntimeError(f"robocopy 失败 code={rc}")
    else:
        sh(["cp", "-r", f"{TEMPLATE}/.", str(tmp)])
    with open(tmp / "README.md", "w", encoding="utf-8") as f:
        f.write("# yt-transcript-relay\n\nYouTube 字幕中转仓，由本地 yt2wechat skill 自动管理。\n")
    if not (tmp / ".git" / "HEAD").exists():
        shutil.rmtree(tmp / ".git", ignore_errors=True)
        sh(["git", "-C", str(tmp), "init", "-b", "main"], capture=False)
    sh(["git", "-C", str(tmp), "add", "-A"], capture=False)
    sh(["git", "-C", str(tmp), "commit", "-m", "sync relay template"], check=False, capture=False)
    if exists:
        sh(["git", "-C", str(tmp), "remote", "add", "origin", f"https://github.com/{repo}.git"], check=False)
        sh(["git", "-C", str(tmp), "push", "-u", "origin", "main"], capture=False)
    else:
        sh([GH, "repo", "create", repo, "--private", "--source", str(tmp), "--push"], capture=False)
    return repo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", default=".")
    args = ap.parse_args()

    owner = sh([GH, "api", "user", "-q", ".login"]).stdout.strip()
    repo = ensure_repo(owner)

    before = {r["databaseId"] for r in json.loads(
        sh([GH, "run", "list", "-R", repo, "--workflow", "transcript.yml",
            "--limit", "20", "--json", "databaseId"]).stdout)}

    sh([GH, "workflow", "run", "transcript.yml", "-R", repo, "-f", f"url={args.url}"])
    print("workflow 已触发, 等待 runner 执行...", flush=True)

    run_id = None
    deadline = time.time() + 480
    while time.time() < deadline:
        time.sleep(8)
        runs = json.loads(sh([GH, "run", "list", "-R", repo, "--workflow", "transcript.yml",
                              "--limit", "10", "--json", "databaseId,status,conclusion,createdAt"]).stdout)
        fresh = [r for r in runs if r["databaseId"] not in before]
        if not fresh:
            continue
        run_id = fresh[0]["databaseId"]
        if fresh[0]["status"] == "completed":
            if fresh[0]["conclusion"] != "success":
                print(sh([GH, "run", "view", str(run_id), "-R", repo, "--log-failed"], check=False).stdout[-1500:])
                print("ERROR: workflow 失败", file=sys.stderr)
                sys.exit(11)
            break
    if not run_id:
        print("ERROR: 8 分钟内未见新 run，队列拥堵，稍后重试", file=sys.stderr)
        sys.exit(12)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sh([GH, "run", "download", str(run_id), "-R", repo, "-n", "transcript", "-D", str(out / "_gh")], capture=False)
    for name in ("transcript.txt", "meta.json"):
        src = out / "_gh" / name
        if src.exists():
            src.replace(out / name)
    (out / "_gh").rmdir() if (out / "_gh").exists() else None

    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    meta["need_translate"] = not meta["language_code"].lower().startswith("zh")
    print("OK " + json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
