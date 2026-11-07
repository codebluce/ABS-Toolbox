#!/usr/bin/env python3
"""综合看板归档整理：最新目录只留一份，历史按月各留一份。

背景
----
`deliverables/dashboards/01_latest/` 名义上是"最新版本"，实际长期堆积了
历次生成的 `ABS综合看板_YYYYMMDD.html`（每份约 10MB）。`02_history/undated/`
同样平铺了 20 多份历史看板。这些文件全部已在 Git 历史中留档，工作目录里
没必要保留全部。

整理规则
--------
1. 综合看板按业务日期（文件名中的 YYYYMMDD）分月。
2. 最新月份的最新一份保留在 `01_latest/`。
3. 其余每个月各保留一份（该月最新的一份），移入 `02_history/YYYY-MM/`。
4. 同月其余版本移入 `--superseded-dir` 指定的项目外目录，可随时回看或删除。
5. 非综合看板的小工具页（发行定价分析工具等）体积很小，一律不动。

用法
----
    # 只看计划，不移动任何文件
    python scripts/tidy_dashboard_archive.py --plan

    # 按计划执行，超期版本移到项目外
    python scripts/tidy_dashboard_archive.py --apply \
        --superseded-dir ~/Documents/LikeCodeNex/_abs-toolbox-superseded-20261107
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARDS = REPO_ROOT / "deliverables" / "dashboards"
LATEST_DIR = DASHBOARDS / "01_latest"
HISTORY_DIR = DASHBOARDS / "02_history"

DASHBOARD_NAME = "ABS综合看板"

# 两种历史命名都见过：
#   ABS综合看板_20261106.html          （现行，日期在中间）
#   20260902_机构统计看板.html          （早期，日期在前缀）
RE_MID_DATE = re.compile(rf"^{DASHBOARD_NAME}_(?P<date>\d{{8}})(?P<suffix>.*)\.html$")
RE_PREFIX_DATE = re.compile(r"^(?P<date>\d{8})_.+\.html$")


def parse_date(name: str) -> tuple[str, str] | None:
    """返回 (YYYYMMDD, 后缀)。后缀为空表示该日期的正式版本。"""
    m = RE_MID_DATE.match(name)
    if m:
        return m.group("date"), m.group("suffix")
    m = RE_PREFIX_DATE.match(name)
    if m:
        return m.group("date"), ""
    return None


def collect_dashboards() -> list[tuple[Path, str, str]]:
    """收集工作区里所有综合看板：[(路径, YYYYMMDD, 后缀), ...]"""
    found: list[tuple[Path, str, str]] = []
    if not LATEST_DIR.exists():
        return found
    for path in sorted(LATEST_DIR.glob("*.html")):
        if not path.name.startswith(DASHBOARD_NAME):
            continue  # 小工具页不动
        parsed = parse_date(path.name)
        if parsed:
            found.append((path, parsed[0], parsed[1]))
    if HISTORY_DIR.exists():
        for path in sorted(HISTORY_DIR.rglob(f"{DASHBOARD_NAME}_*.html")):
            parsed = parse_date(path.name)
            if parsed:
                found.append((path, parsed[0], parsed[1]))
    return found


def human(size: int) -> str:
    return f"{size / 1024 / 1024:.1f} MB" if size >= 1024 * 1024 else f"{size / 1024:.0f} KB"


def build_plan() -> tuple[list[tuple[Path, Path]], list[tuple[Path, str]], int]:
    """生成 (保留/归档到月份目录, 移出项目, 释放字节数)。"""
    items = collect_dashboards()
    if not items:
        return [], [], 0

    by_month: dict[str, list[tuple[Path, str, str]]] = defaultdict(list)
    for path, date, suffix in items:
        by_month[date[:6]].append((path, date, suffix))

    latest_month = max(by_month)
    keep_latest = max(by_month[latest_month], key=lambda t: (t[1], t[2] == "", t[0].name))

    to_month_dir: list[tuple[Path, Path]] = []
    to_superseded: list[tuple[Path, str]] = []
    freed = 0

    for month in sorted(by_month):
        group = by_month[month]
        if month == latest_month:
            keep = {keep_latest[0]}
        else:
            winner = max(group, key=lambda t: (t[1], t[2] == "", t[0].name))
            keep = {winner[0]}
            target = HISTORY_DIR / f"{month[:4]}-{month[4:]}"
            # 已经在位(上一次整理的结果)就不要再规划一次移动
            if winner[0].parent != target:
                to_month_dir.append((winner[0], target / winner[0].name))
        for path, _date, _suffix in group:
            if path in keep:
                continue
            freed += path.stat().st_size
            if path.parent == LATEST_DIR:
                to_superseded.append((path, f"{month[:4]}-{month[4:]}/" + path.name))
            else:
                to_superseded.append((path, path.relative_to(HISTORY_DIR).as_posix()))

    return to_month_dir, to_superseded, freed


def move(src: Path, dst: Path, apply: bool) -> None:
    print(f"    {src.relative_to(REPO_ROOT)}  →  {dst}")
    if not apply:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise SystemExit(f"目标已存在，中止: {dst}")
    shutil.move(str(src), str(dst))


def main() -> None:
    parser = argparse.ArgumentParser(description="综合看板归档整理")
    parser.add_argument("--plan", action="store_true", help="只打印计划，不移动文件（默认）")
    parser.add_argument("--apply", action="store_true", help="实际执行移动")
    parser.add_argument(
        "--superseded-dir",
        type=Path,
        default=None,
        help="同月多余版本的去处（必须位于仓库之外）",
    )
    args = parser.parse_args()

    apply = args.apply
    if apply and not args.superseded_dir:
        raise SystemExit("--apply 需要同时指定 --superseded-dir（仓库之外的目录）")

    superseded_root = args.superseded_dir.expanduser().resolve() if args.superseded_dir else None
    if superseded_root and superseded_root.is_relative_to(REPO_ROOT):
        raise SystemExit("--superseded-dir 不能位于仓库内部，否则仍会占用版本库空间")

    to_month_dir, to_superseded, freed = build_plan()

    print("=" * 66)
    print("综合看板归档整理" + ("（执行）" if apply else "（预演，不移动文件）"))
    print("=" * 66)

    print(f"\n[1] 按月归档 → 02_history/YYYY-MM/   共 {len(to_month_dir)} 份")
    for src, dst in to_month_dir:
        move(src, dst, apply)

    print(f"\n[2] 同月多余版本 → 项目外   共 {len(to_superseded)} 份，{human(freed)}")
    if not to_superseded:
        print("    （无）")
    for src, rel in to_superseded:
        if superseded_root is None:
            print(f"    {src.relative_to(REPO_ROOT)}")
        else:
            move(src, superseded_root / rel, apply)

    print(f"\n[3] 保持不动")
    print(f"    01_latest 中的最新看板与小工具页")
    print(f"    02_history 下的 peer_issuance / lab_viz / 按日期的小工具页目录")

    if not apply:
        print(f"\n预演结束。实际执行可为仓库工作区腾出约 {human(freed)}。")
        print("加 --apply --superseded-dir <仓库外目录> 执行。")
    else:
        print(f"\n完成，工作区减少约 {human(freed)}。")


if __name__ == "__main__":
    main()
