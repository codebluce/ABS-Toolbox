#!/usr/bin/env python3
"""audit_refresh_index.py — 从 A/B/C 产物文件刷新 state.json 结构字段 + INDEX.md 三表

移植自 macro-allocation-strategy/scripts/refresh_audit_index.py,适配 abs-toolbox:
- state.json 为按 slug 分组结构(slugs.{slug}.submissions/reviews/closed/status)
- 每组的手写 notes 与顶层 issues[] 台账**原样保留,绝不覆盖**
- INDEX.md 三表(Submissions/Reviews/Closed)按文件实际内容重建

用法:
  python scripts/audit_refresh_index.py                # 全量刷新
  python scripts/audit_refresh_index.py --slug X       # 只处理指定 slug
  python scripts/audit_refresh_index.py --dry-run      # 只打印不写
  python scripts/audit_refresh_index.py --check        # 校验是否一致(不写)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
AUDIT_DIR = SKILL_ROOT / "audit"
STATE_PATH = AUDIT_DIR / "state.json"
INDEX_PATH = AUDIT_DIR / "INDEX.md"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_validate import parse_frontmatter  # noqa: E402


def git(*args: str) -> str:
    try:
        proc = subprocess.run(["git", *args], cwd=SKILL_ROOT, capture_output=True, text=True)
        return proc.stdout.strip() if proc.returncode == 0 else ""
    except OSError:
        return ""


def scan_dir(sub: str) -> list[Path]:
    d = AUDIT_DIR / sub
    return sorted(d.glob("[ABC]*-*.md")) if d.exists() else []


def slug_of(path: Path) -> str | None:
    m = re.match(r"^[ABC]\d+-(.+)-r\d+$", path.stem)
    return m.group(1) if m else None


def round_of(path: Path) -> int:
    m = re.search(r"-r(\d+)$", path.stem)
    return int(m.group(1)) if m else 0


def derive_status(subs: list[Path], revs: list[Path], clos: list[Path], old_status: str | None) -> tuple[str, str | None]:
    """从文件存在性推导 slug status 与 verdict。

    返回 (status, verdict)。verdict 从最新 B 文件 frontmatter 读。
    """
    verdict = None
    if revs:
        latest_b = max(revs, key=round_of)
        try:
            fm = parse_frontmatter(latest_b.read_text(encoding="utf-8"))
            verdict = fm.get("verdict")
        except OSError:
            verdict = None
    if clos:
        return "COMPLETED", verdict
    if not revs:
        return "PENDING_REVIEW", None
    if verdict == "NEEDS_REVISION":
        return "NEEDS_REVISION", verdict
    if verdict in {"APPROVED", "APPROVED_WITH_CONDITIONS", "NEEDS_INFO"}:
        return "REVIEWED", verdict
    if verdict == "REJECTED":
        return "REJECTED", verdict
    return old_status or "PENDING_REVIEW", verdict


def refresh(slug_filter: str | None, dry_run: bool, check_only: bool) -> int:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    slugs: dict = state.setdefault("slugs", {})

    by_slug: dict[str, dict[str, list[Path]]] = {}
    for sub, key in (("submissions", "subs"), ("reviews", "revs"), ("closed", "clos")):
        for p in scan_dir(sub):
            s = slug_of(p)
            if not s:
                continue
            if slug_filter and s != slug_filter:
                continue
            by_slug.setdefault(s, {"subs": [], "revs": [], "clos": []})[key].append(p)

    changes: list[str] = []
    for s, files in sorted(by_slug.items()):
        info = slugs.setdefault(s, {})
        new_subs = [p.stem for p in files["subs"]]
        new_revs = [p.stem for p in files["revs"]]
        new_clos = [p.stem for p in files["clos"]]
        if info.get("submissions") != new_subs:
            info["submissions"] = new_subs
            changes.append(f"{s}.submissions -> {new_subs}")
        if info.get("reviews") != new_revs:
            info["reviews"] = new_revs
            changes.append(f"{s}.reviews -> {new_revs}")
        # closed 保持字符串(历史格式)或列表兼容
        new_closed = new_clos[-1] if new_clos else None
        old_closed = info.get("closed")
        old_closed_str = old_closed if isinstance(old_closed, str) else (old_closed[-1] if old_closed else None)
        if new_closed != old_closed_str:
            if new_closed:
                info["closed"] = new_closed
            changes.append(f"{s}.closed -> {new_closed}")
        new_round = max([round_of(p) for p in files["subs"]] or [1])
        if (info.get("current_round") or 0) != new_round:
            info["current_round"] = new_round
            changes.append(f"{s}.current_round -> {new_round}")
        new_status, new_verdict = derive_status(files["subs"], files["revs"], files["clos"], info.get("status"))
        if info.get("status") != new_status:
            info["status"] = new_status
            changes.append(f"{s}.status -> {new_status}")
        if new_verdict and info.get("verdict") != new_verdict:
            info["verdict"] = new_verdict
            changes.append(f"{s}.verdict -> {new_verdict}")
        # counters 只增不减
        counters = state.setdefault("counters", {})
        old_max = (counters.get(s) or {}).get("max_round", 0) if isinstance(counters.get(s), dict) else 0
        if new_round > old_max:
            counters.setdefault(s, {})["max_round"] = new_round
            changes.append(f"counters.{s}.max_round -> {new_round}")

    if not changes:
        print("[refresh] 无结构变化")
    else:
        for c in changes:
            print(f"[change] {c}")

    if check_only:
        return 0 if not changes else 1
    if dry_run:
        print("[dry-run] 未写文件")
        return 0

    if changes:
        from datetime import datetime
        state["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M") + " (auto-refresh)"
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[refresh] state.json 已更新")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="刷新审计索引 state.json")
    parser.add_argument("--slug", help="只处理指定 slug")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true", help="只校验一致性,不写")
    args = parser.parse_args()
    return refresh(args.slug, args.dry_run, args.check)


if __name__ == "__main__":
    sys.exit(main())
