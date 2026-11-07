#!/usr/bin/env python3
"""同业发行底稿的来源解析与口径回归校验。

背景
----
同一来源目录下并存两类文件：

- 原始周报：`互联网金融ABS内部信息共享-更新至YYYYMMDD.xlsx`
- 完整已录底稿：`同业发行完整已录底稿_YYYYMMDD.xlsx`（人工补录之后）

发布参数 `--peer-issuance-xlsx` 接受任意路径。2026-11-07 发布时误传原始
周报(600 期 / 5,165 亿)，把线上口径从 623 期 / 5,282 亿 拉低，事后靠人工
比对才发现。两个文件同期数接近、都在同一目录，肉眼很难分辨。

本模块把"该用哪一份"收敛成一条规则：

1. 只接受 `同业发行完整已录底稿_*` 命名，且必须位于固定来源目录；
2. 期数与累计规模不得少于上一份已录底稿(除非显式放行)。

用法
----
    python scripts/peer_issuance_source.py            # 查看当前应使用的底稿
    python scripts/peer_issuance_source.py --verify   # 校验最新底稿未回退
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "deliverables" / "dashboards" / "03_source" / "peer_issuance"

WORKING_PAPER_PREFIX = "同业发行完整已录底稿_"
WORKING_PAPER_GLOB = f"{WORKING_PAPER_PREFIX}*.xlsx"
RE_DATE = re.compile(rf"^{re.escape(WORKING_PAPER_PREFIX)}(\d{{8}})\.xlsx$")


class PeerIssuanceSourceError(RuntimeError):
    """同业底稿来源不合格或口径回退。"""


def working_paper_date(path: Path) -> str:
    """从文件名取业务日期(YYYYMMDD)。命名不合规时抛错。"""
    match = RE_DATE.match(path.name)
    if not match:
        raise PeerIssuanceSourceError(
            f"不是完整已录底稿命名：{path.name}；"
            f"只接受 {WORKING_PAPER_PREFIX}YYYYMMDD.xlsx"
        )
    return match.group(1)


def list_working_papers(folder: Path | None = None) -> list[Path]:
    """按业务日期升序列出完整已录底稿。"""
    target = folder or SOURCE_DIR
    if not target.exists():
        raise PeerIssuanceSourceError(f"同业底稿目录不存在：{target}")
    papers = [p for p in target.glob(WORKING_PAPER_GLOB) if RE_DATE.match(p.name)]
    return sorted(papers, key=working_paper_date)


def resolve_latest_working_paper(folder: Path | None = None) -> Path:
    """取业务日期最新的一份完整已录底稿。"""
    papers = list_working_papers(folder)
    if not papers:
        raise PeerIssuanceSourceError(
            f"未找到完整已录底稿({WORKING_PAPER_PREFIX}YYYYMMDD.xlsx)，"
            f"目录：{folder or SOURCE_DIR}"
        )
    return papers[-1]


def summarize(path: Path) -> dict:
    """统计期数与累计规模，用于回归比对。"""
    import peer_issuance_panel

    records = peer_issuance_panel.parse_dynamics(path)
    total = sum((r["amount"] for r in records), peer_issuance_panel.ZERO)
    return {
        "path": path,
        "date": RE_DATE.match(path.name).group(1),
        "records": len(records),
        "amount": total,
    }


def verify_source(path: Path, folder: Path | None = None) -> dict:
    """确认这份底稿是该用的那一份：命名合规且在固定来源目录内。"""
    target = (folder or SOURCE_DIR).resolve()
    resolved = path.resolve()
    working_paper_date(resolved)  # 命名不合规直接抛错
    if resolved.parent != target:
        raise PeerIssuanceSourceError(
            f"同业底稿必须来自固定来源目录 {target}，实际为 {resolved.parent}"
        )
    return summarize(resolved)


def verify_not_regressing(
    path: Path,
    folder: Path | None = None,
    *,
    allow_fewer: bool = False,
) -> dict:
    """期数与累计规模不得少于上一份已录底稿。"""
    current = summarize(path)
    earlier = [p for p in list_working_papers(folder) if working_paper_date(p) < current["date"]]
    if not earlier:
        return {"current": current, "previous": None}

    previous = summarize(earlier[-1])
    problems = []
    if current["records"] < previous["records"]:
        problems.append(
            f"期数 {current['records']} 少于上一份 {previous['records']}"
            f"（{previous['date']}）"
        )
    if current["amount"] < previous["amount"]:
        problems.append(
            f"累计规模 {current['amount']:.2f} 亿 少于上一份 {previous['amount']:.2f} 亿"
            f"（{previous['date']}）"
        )
    if problems and not allow_fewer:
        raise PeerIssuanceSourceError(
            "同业底稿口径回退，已中止：" + "；".join(problems)
            + "。若确属口径修正，请显式加 --allow-fewer-peer-records"
        )
    return {"current": current, "previous": previous, "problems": problems}


def main() -> None:
    parser = argparse.ArgumentParser(description="同业发行底稿来源检查")
    parser.add_argument("--verify", action="store_true", help="校验最新底稿未回退")
    parser.add_argument("--folder", type=Path, default=None, help="自定义来源目录(调试用)")
    parser.add_argument("--allow-fewer", action="store_true", help="允许期数或规模减少")
    args = parser.parse_args()

    try:
        latest = resolve_latest_working_paper(args.folder)
        info = summarize(latest)
        print(f"当前应使用的同业底稿：{latest.name}")
        print(f"  {info['records']} 期，累计 {info['amount']:.2f} 亿")
        if args.verify:
            result = verify_not_regressing(
                latest, args.folder, allow_fewer=args.allow_fewer
            )
            previous = result["previous"]
            if previous is None:
                print("  无上一份底稿，跳过回退比对")
            else:
                print(
                    f"  上一份 {previous['date']}：{previous['records']} 期，"
                    f"累计 {previous['amount']:.2f} 亿"
                )
                delta = info["records"] - previous["records"]
                print(f"  期数变化：{delta:+d}")
            print("✅ 口径校验通过")
    except PeerIssuanceSourceError as error:
        print(f"❌ {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
