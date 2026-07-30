#!/usr/bin/env python3
"""Generate and publish ABS dashboard static site to GitHub Pages.

Workflow:
  1. Optionally generate the latest integrated dashboard from a ledger workbook.
  2. Build a static site package from deliverables/dashboards/01_latest.
  3. Sync the package to the gh-pages branch via a temporary git worktree.
  4. Commit and push to GitHub.

This script never uploads source Excel files or scripts to Pages; only the static HTML
site package is copied to gh-pages.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
LATEST_DIR = REPO_ROOT / "deliverables" / "dashboards" / "01_latest"
SITE_STAGING_DIR = REPO_ROOT / "deliverables" / "dashboard_site"
FINAL_LEDGER_DIR = REPO_ROOT / "deliverables" / "ledger" / "03_final"
DASHBOARD_PREFIX = "ABS综合看板_"
DASHBOARD_SUFFIX = ".html"


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        check=check,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def capture(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        check=check,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.strip()


def latest_by_mtime(paths: Iterable[Path]) -> Path:
    items = [p for p in paths if p.exists()]
    if not items:
        raise FileNotFoundError("没有找到可用文件")
    return max(items, key=lambda p: p.stat().st_mtime)


def find_latest_ledger() -> Path:
    candidates = sorted(FINAL_LEDGER_DIR.glob("2026年ABS发行台账-*-定稿.xlsx"))
    if not candidates:
        raise FileNotFoundError(f"未找到定稿台账: {FINAL_LEDGER_DIR}")
    # Prefer newest by modification time so manually refreshed files are picked up.
    return latest_by_mtime(candidates)


def find_dashboard_files() -> list[Path]:
    files = sorted(LATEST_DIR.glob(f"{DASHBOARD_PREFIX}*{DASHBOARD_SUFFIX}"))
    if not files:
        raise FileNotFoundError(f"未找到综合看板 HTML: {LATEST_DIR}")
    return files


def dashboard_date(path: Path) -> str:
    name = path.name
    if name.startswith(DASHBOARD_PREFIX) and name.endswith(DASHBOARD_SUFFIX):
        return name[len(DASHBOARD_PREFIX):-len(DASHBOARD_SUFFIX)]
    return path.stem


def generate_dashboard(ledger_path: Path) -> Path:
    print(f"\n[1/4] 生成最新综合看板: {ledger_path}")
    run([sys.executable, str(SCRIPTS_DIR / "gen_integrated_dashboard.py"), str(ledger_path)])
    return latest_by_mtime(find_dashboard_files())


def write_archive_index(archive_dir: Path, dashboards: list[Path]) -> None:
    rows = []
    for p in sorted(dashboards, key=dashboard_date, reverse=True):
        size_mb = p.stat().st_size / 1024 / 1024
        date = dashboard_date(p)
        rows.append(
            f'<tr><td>{date}</td><td><a href="{p.name}">{p.name}</a></td><td>{size_mb:.2f} MB</td></tr>'
        )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ABS综合看板历史归档</title>
  <style>
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;margin:32px;background:#f6f7f9;color:#172033;}}
    .wrap{{max-width:960px;margin:auto;background:white;border-radius:18px;padding:28px;box-shadow:0 12px 40px rgba(15,23,42,.08);}}
    h1{{margin:0 0 8px;font-size:28px;}}
    p{{color:#667085;}}
    table{{width:100%;border-collapse:collapse;margin-top:20px;}}
    th,td{{padding:12px 10px;border-bottom:1px solid #e5e7eb;text-align:left;font-size:14px;}}
    th{{color:#475467;background:#f9fafb;}}
    a{{color:#175cd3;text-decoration:none;font-weight:600;}}
    .top{{display:flex;justify-content:space-between;gap:16px;align-items:center;}}
    .btn{{display:inline-block;padding:10px 14px;border-radius:10px;background:#172033;color:white;}}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <div>
        <h1>ABS综合看板历史归档</h1>
        <p>最新版本请访问 <a href="../index.html">主入口 index.html</a>。</p>
      </div>
      <a class="btn" href="../index.html">返回最新看板</a>
    </div>
    <table>
      <thead><tr><th>日期</th><th>文件</th><th>大小</th></tr></thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
</body>
</html>
"""
    (archive_dir / "index.html").write_text(html, encoding="utf-8")


def build_site(latest_dashboard: Path | None = None) -> Path:
    print("\n[2/4] 组装静态站点包...")
    dashboards = find_dashboard_files()
    latest_dashboard = latest_dashboard or latest_by_mtime(dashboards)

    if SITE_STAGING_DIR.exists():
        shutil.rmtree(SITE_STAGING_DIR)
    archive_dir = SITE_STAGING_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(latest_dashboard, SITE_STAGING_DIR / "index.html")
    for p in dashboards:
        shutil.copy2(p, archive_dir / p.name)
    write_archive_index(archive_dir, dashboards)
    (SITE_STAGING_DIR / ".nojekyll").write_text("", encoding="utf-8")

    # Keep the site package deterministic for the same dashboard HTML.
    # Otherwise every dry run changes manifest/README timestamps and creates noisy gh-pages commits.
    packaged_at = datetime.fromtimestamp(latest_dashboard.stat().st_mtime).isoformat(timespec="seconds")
    manifest = {
        "generatedAt": packaged_at,
        "latest": latest_dashboard.name,
        "latestDate": dashboard_date(latest_dashboard),
        "dashboardCount": len(dashboards),
        "archive": [p.name for p in sorted(dashboards, key=dashboard_date, reverse=True)],
        "source": "scripts/deploy_github_pages.py",
    }
    (SITE_STAGING_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    readme = f"""# ABS综合看板静态站点包

本目录由 `scripts/deploy_github_pages.py` 自动生成，用于发布到 GitHub Pages。

- 最新入口：`index.html`
- 最新来源：`{latest_dashboard.relative_to(REPO_ROOT)}`
- 历史归档：`archive/index.html`
- 生成时间：`{manifest['generatedAt']}`

安全说明：站点包只包含静态 HTML，不包含源 Excel、簿记明细、脚本、`.env` 等文件。
"""
    (SITE_STAGING_DIR / "README.md").write_text(readme, encoding="utf-8")

    print(f"[site] 最新: {latest_dashboard.name}")
    print(f"[site] 文件数: {len(list(SITE_STAGING_DIR.rglob('*')))}")
    return SITE_STAGING_DIR


def ensure_clean_main() -> None:
    status = capture(["git", "status", "--short"])
    if status:
        raise RuntimeError(
            "main 工作树不干净。为避免部署夹带未提交改动,请先处理以下文件:\n" + status
        )


def remove_worktree_contents(worktree: Path) -> None:
    for child in worktree.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def publish_to_pages(site_dir: Path, remote: str, branch: str, message: str, no_push: bool) -> bool:
    print("\n[3/4] 同步到 gh-pages worktree...")
    tmp_parent = Path(tempfile.mkdtemp(prefix="abs_pages_"))
    worktree = tmp_parent / "worktree"
    changed = False
    try:
        # Ensure local branch exists. If not, create it from remote branch.
        has_local = subprocess.run(["git", "show-ref", "--verify", f"refs/heads/{branch}"], cwd=REPO_ROOT).returncode == 0
        if not has_local:
            run(["git", "fetch", remote, f"{branch}:{branch}"])
        run(["git", "worktree", "add", str(worktree), branch])

        remove_worktree_contents(worktree)
        for item in site_dir.iterdir():
            dest = worktree / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        run(["git", "add", "-A"], cwd=worktree)
        diff_status = capture(["git", "status", "--short"], cwd=worktree)
        if not diff_status:
            print("[pages] gh-pages 无文件变化")
            if no_push:
                print("[pages] --no-push 已设置,跳过推送")
            else:
                print("[pages] 仍执行 git push,确保本地 gh-pages 已同步到远端")
                run(["git", "push", remote, f"{branch}:{branch}"], cwd=worktree)
            return False
        changed = True
        print(diff_status)
        run(["git", "commit", "-m", message], cwd=worktree)
        if no_push:
            print("[pages] --no-push 已设置,未推送远端")
        else:
            print("\n[4/4] 推送到 GitHub Pages...")
            run(["git", "push", remote, f"{branch}:{branch}"], cwd=worktree)
        return True
    finally:
        try:
            run(["git", "worktree", "remove", "--force", str(worktree)], check=False)
        finally:
            shutil.rmtree(tmp_parent, ignore_errors=True)
        if changed:
            print("[pages] 临时 worktree 已清理")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成并发布 ABS 综合看板到 GitHub Pages")
    parser.add_argument("--ledger", type=Path, default=None, help="定稿台账路径。默认使用 03_final 下最新 2026 定稿")
    parser.add_argument("--skip-generate", action="store_true", help="跳过综合看板生成,直接用 01_latest 最新 HTML 组装站点")
    parser.add_argument("--no-push", action="store_true", help="只在本地更新 gh-pages worktree commit,不推送")
    parser.add_argument("--remote", default="github", help="Pages 远端名,默认 github")
    parser.add_argument("--branch", default="gh-pages", help="Pages 分支名,默认 gh-pages")
    parser.add_argument("--message", default=None, help="gh-pages commit message")
    parser.add_argument("--allow-dirty", action="store_true", help="允许 main 工作树有未提交改动(不推荐)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.allow_dirty:
        ensure_clean_main()

    latest_dashboard = None
    if args.skip_generate:
        print("[1/4] 跳过生成综合看板,使用现有 01_latest 最新 HTML")
    else:
        ledger = args.ledger or find_latest_ledger()
        latest_dashboard = generate_dashboard(ledger)

    site_dir = build_site(latest_dashboard)
    date_tag = dashboard_date(latest_by_mtime(find_dashboard_files()))
    message = args.message or f"deploy: update ABS dashboard site {date_tag}"
    changed = publish_to_pages(site_dir, args.remote, args.branch, message, args.no_push)

    print("\n[完成] GitHub Pages 更新流程结束")
    print(f"站点包: {site_dir}")
    print("主入口: https://codebluce.github.io/ABS-Toolbox/")
    print("归档页: https://codebluce.github.io/ABS-Toolbox/archive/index.html")
    print(f"是否产生 gh-pages 更新: {'是' if changed else '否'}")


if __name__ == "__main__":
    main()
