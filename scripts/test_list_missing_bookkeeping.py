#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""缺失簿记明细口径单元测试

覆盖 2026-11-07 确认的口径：
  1. 2026-06-01 之前的缺口不再补录；
  2. 发行场所含“非标”的项目不补录；
  3. 其余项目才进入“仍需补录”清单。

运行：PYTHONUTF8=1 .venv/bin/python -m unittest scripts.test_list_missing_bookkeeping -v
"""
import datetime
import os
import sys
import tempfile
import unittest
from pathlib import Path

import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from list_missing_bookkeeping import (  # noqa: E402
    classify_missing,
    collect_projects,
    is_before_cutoff,
    is_non_standard,
    latest_ledger,
    summarize_by_manager,
)

HEADER = [
    "序号", "月份", "类别", "资产类型", "项目名称", "发行场所", "计划管理人",
    "联席承销商", "托管行", "规模", "期限", "簿记时间", "国股CD", "ALL-IN成本",
    "认购倍数", "分层情况", "分层占比", "对应金额（亿）", "评级", "成本",
    "认购机构", "认购份额", "申购利率", "穿透机构", "申购规模",
]


def make_ledger(rows):
    """rows: list[tuple(项目, 场所, 管理人, 簿记时间, 申购利率, 申购规模)]"""
    handle = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    handle.close()
    path = Path(handle.name)
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "总表"
    sheet.append(HEADER)
    for index, (name, venue, manager, book_date, rate, size) in enumerate(rows, start=1):
        record = [None] * len(HEADER)
        record[0] = index
        record[4] = name
        record[5] = venue
        record[6] = manager
        record[11] = book_date
        record[22] = rate
        record[24] = size
        sheet.append(record)
    workbook.save(path)
    return path


class CutoffRuleTest(unittest.TestCase):
    def test_before_cutoff_detection(self):
        self.assertTrue(is_before_cutoff(datetime.datetime(2026, 5, 31, 23, 59)))
        self.assertFalse(is_before_cutoff(datetime.datetime(2026, 6, 1)))
        self.assertFalse(is_before_cutoff(None))

    def test_non_standard_detection(self):
        for venue in ("平层非标", "结构化非标", "非标"):
            self.assertTrue(is_non_standard(venue), venue)
        for venue in ("上交所", "深交所", "银行间", "中保登", None):
            self.assertFalse(is_non_standard(venue), venue)


class ClassifyTest(unittest.TestCase):
    def setUp(self):
        self.path = make_ledger([
            # 6 月前且缺明细 → 口径外
            ("老项目A", "上交所", "国泰海通", datetime.datetime(2026, 1, 8), None, None),
            # 6 月前 + 非标 → 归入“6 月前”，不重复计数
            ("老非标B", "平层非标", "中粮信托", datetime.datetime(2026, 3, 1), None, None),
            # 6 月后但非标 → 口径外
            ("新非标C", "结构化非标", "外贸信托", datetime.datetime(2026, 7, 1), None, None),
            # 6 月后、标准场所、缺明细 → 仍需补录
            ("新项目D", "上交所", "中信建投", datetime.datetime(2026, 7, 15), None, None),
            # 6 月后、标准场所、有明细 → 不算缺
            ("新项目E", "上交所", "中信证券", datetime.datetime(2026, 8, 1), 0.016, 2.5),
        ])
        self.projects = collect_projects(self.path)
        self.result = classify_missing(self.projects)

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_project_count(self):
        self.assertEqual(self.result["total_projects"], 5)
        self.assertEqual(self.result["missing_total"], 4)

    def test_pre_cutoff_excluded(self):
        names = [item["project"] for item in self.result["excluded_pre_cutoff"]]
        self.assertEqual(names, ["老项目A", "老非标B"])

    def test_non_standard_excluded(self):
        names = [item["project"] for item in self.result["excluded_non_standard"]]
        self.assertEqual(names, ["新非标C"])

    def test_remaining_only_post_cutoff_standard(self):
        names = [item["project"] for item in self.result["remaining"]]
        self.assertEqual(names, ["新项目D"])

    def test_zero_bid_size_is_not_detail(self):
        path = make_ledger([
            ("零值项目", "上交所", "中信证券", datetime.datetime(2026, 9, 1), 0, 0),
        ])
        try:
            result = classify_missing(collect_projects(path))
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual([item["project"] for item in result["remaining"]], ["零值项目"])

    def test_summary_groups_by_manager(self):
        grouped = summarize_by_manager(self.result["remaining"])
        self.assertEqual(list(grouped.keys()), ["中信建投"])
        self.assertEqual(grouped["中信建投"], ["新项目D"])


class LatestLedgerTest(unittest.TestCase):
    def test_picks_latest_by_business_date(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            for tag in ("0918", "1106", "1030"):
                (directory / f"2026年ABS发行台账-{tag}-定稿.xlsx").write_bytes(b"")
            self.assertEqual(latest_ledger(directory).name, "2026年ABS发行台账-1106-定稿.xlsx")

    def test_missing_directory_raises(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):
                latest_ledger(Path(folder))


if __name__ == "__main__":
    unittest.main()
