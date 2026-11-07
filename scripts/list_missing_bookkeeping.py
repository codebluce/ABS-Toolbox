#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""缺失簿记明细清单（按已确认口径）

口径（2026-11-07 用户确认）：
  1. 簿记时间早于 2026-06-01 的项目，即使仍缺簿记明细也不再补录，统计时忽略；
  2. 发行场所含“非标”的项目（平层非标 / 结构化非标 / 非标）不补录簿记明细，统计时忽略；
  3. 其余项目若所有分层都没有 W（申购利率）或 Y（申购规模），视为缺簿记明细。

用法：
  PYTHONUTF8=1 .venv/bin/python scripts/list_missing_bookkeeping.py [台账.xlsx] [--json]

不传台账时，自动取 deliverables/ledger/03_final 下业务日期最新的 2026 定稿。
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
FINAL_LEDGER_DIR = ROOT / "deliverables" / "ledger" / "03_final"

# 用户确认口径：2026-06-01 之前的缺口不再补录
CUTOFF_DATE = datetime.datetime(2026, 6, 1)
NON_STANDARD_MARKER = "非标"

COL_NAME, COL_VENUE, COL_MANAGER, COL_BOOK_DATE = 5, 6, 7, 12
COL_RATE, COL_BID_SIZE = 23, 25


def latest_ledger(directory: Path = FINAL_LEDGER_DIR) -> Path:
    """按文件名业务日期选择最新定稿，避免被复制/触碰旧文件误导。"""
    candidates = []
    for path in directory.glob("2026年ABS发行台账-*-定稿.xlsx"):
        match = re.search(r"-(\d{4})-定稿\.xlsx$", path.name)
        if match:
            candidates.append((match.group(1), path))
    if not candidates:
        raise FileNotFoundError(f"未找到定稿台账: {directory}")
    return max(candidates, key=lambda item: item[0])[1]


def _as_datetime(value):
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        text = value.strip().replace("/", "-")
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.datetime.strptime(text[: len(fmt) + 2], fmt)
            except ValueError:
                continue
    return None


def is_non_standard(venue) -> bool:
    return isinstance(venue, str) and NON_STANDARD_MARKER in venue


def is_before_cutoff(book_date) -> bool:
    moment = _as_datetime(book_date)
    return moment is not None and moment < CUTOFF_DATE


def _has_detail(rate, bid_size) -> bool:
    for value in (rate, bid_size):
        if isinstance(value, (int, float)) and value:
            return True
    return False


def collect_projects(ledger_path: Path) -> "OrderedDict[str, dict]":
    workbook = openpyxl.load_workbook(ledger_path, data_only=False, read_only=True)
    sheet = workbook["总表"]
    projects: "OrderedDict[str, dict]" = OrderedDict()
    for row in sheet.iter_rows(min_row=2, values_only=True):
        name = row[COL_NAME - 1]
        if not name:
            continue
        entry = projects.get(name)
        if entry is None:
            entry = projects[name] = {
                "project": name,
                "manager": row[COL_MANAGER - 1],
                "venue": row[COL_VENUE - 1],
                "book_date": row[COL_BOOK_DATE - 1],
                "has_detail": False,
            }
        if _has_detail(row[COL_RATE - 1], row[COL_BID_SIZE - 1]):
            entry["has_detail"] = True
    workbook.close()
    return projects


def classify_missing(projects: "OrderedDict[str, dict]") -> dict:
    """把缺明细项目分成：口径外（6月前 / 非标）与仍需补录。"""
    remaining, pre_cutoff, non_standard = [], [], []
    for entry in projects.values():
        if entry["has_detail"]:
            continue
        item = {
            "project": entry["project"],
            "manager": entry["manager"],
            "venue": entry["venue"],
            "book_date": (
                _as_datetime(entry["book_date"]).strftime("%Y-%m-%d")
                if _as_datetime(entry["book_date"])
                else None
            ),
        }
        if is_before_cutoff(entry["book_date"]):
            pre_cutoff.append(item)
        elif is_non_standard(entry["venue"]):
            non_standard.append(item)
        else:
            remaining.append(item)
    return {
        "cutoff": CUTOFF_DATE.strftime("%Y-%m-%d"),
        "total_projects": len(projects),
        "missing_total": len(remaining) + len(pre_cutoff) + len(non_standard),
        "excluded_pre_cutoff": pre_cutoff,
        "excluded_non_standard": non_standard,
        "remaining": remaining,
    }


def summarize_by_manager(items: list[dict]) -> "OrderedDict[str, list[str]]":
    grouped: "OrderedDict[str, list[str]]" = OrderedDict()
    for item in items:
        grouped.setdefault(str(item["manager"]), []).append(item["project"])
    return grouped


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="按已确认口径列出仍缺簿记明细的项目")
    parser.add_argument("ledger", nargs="?", help="定稿台账路径；默认取最新 2026 定稿")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args(argv)

    ledger_path = Path(args.ledger) if args.ledger else latest_ledger()
    if not ledger_path.exists():
        print(f"台账不存在: {ledger_path}", file=sys.stderr)
        return 2

    result = classify_missing(collect_projects(ledger_path))
    result["ledger"] = ledger_path.name

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"台账：{ledger_path.name}")
    print(f"项目总数：{result['total_projects']}")
    print(f"缺明细合计：{result['missing_total']}")
    print(f"  口径外·{result['cutoff']} 之前：{len(result['excluded_pre_cutoff'])}")
    print(f"  口径外·非标项目：{len(result['excluded_non_standard'])}")
    print(f"  仍需补录：{len(result['remaining'])}")
    if result["remaining"]:
        print("\n仍需补录（按管理人）：")
        for manager, names in summarize_by_manager(result["remaining"]).items():
            print(f"  {manager}（{len(names)}）：{'；'.join(names)}")
    else:
        print("\n仍需补录：无")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
