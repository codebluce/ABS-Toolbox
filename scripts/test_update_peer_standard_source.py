"""同业发行底稿按标准源滚动更新的回归测试。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

import openpyxl

import update_peer_standard_source as ups


HEADERS = [
    '簿记日期', '产品名称', '产品类型', '场所', '原始权益人/发起机构', '基础资产', '资产类型',
    '规模(亿)', '簿记时间', '设立时间', 'AAA证券票面利率', 'AAA档证券期限(年)', 'AAA档证券占比',
    'AA+证券票面利率', 'AA+档证券期限(年)', 'AA+档证券占比',
]


def write_workbook(path: Path, rows: list[list], with_notes: bool = True) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '发行动态（2026）'
    ws.append(HEADERS)
    for row in rows:
        ws.append(row)
    if with_notes:
        wb.create_sheet('数据口径与来源')
    wb.save(path)
    wb.close()


def record(name: str, book: datetime, amount: float) -> list:
    return ['2026.11.2-2026.11.8', name, 'ABS', '上海', '外贸信托', '京东白条', '消金提现类',
            amount, book, datetime(2026, 11, 11), 0.0177, 1.92, 0.9, 0.018, 1.92, 0.03]


class UpdatePeerStandardSourceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.current = self.root / '底稿_20261030.xlsx'
        self.source = self.root / '标准源_1106.xlsx'
        self.output = self.root / '底稿_20261106.xlsx'
        self.supplement = self.root / '底稿.supplement.json'
        self.supplement.write_text(json.dumps({'entries': []}), encoding='utf-8')

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_main(self, label: str = '2026-11-06', pass_supplement: bool = True) -> None:
        argv = ['update_peer_standard_source.py', '--current', str(self.current),
                '--source', str(self.source), '--output', str(self.output),
                '--label-date', label]
        if pass_supplement:
            argv += ['--supplement-json', str(self.supplement)]
        with mock.patch.object(sys, 'argv', argv):
            ups.main()

    def test_new_record_carries_label_date_and_single_audit_sheet(self) -> None:
        write_workbook(self.current, [record('项目甲资产支持专项计划', datetime(2026, 10, 30), 10)])
        write_workbook(self.source, [
            record('项目甲资产支持专项计划', datetime(2026, 10, 30), 10),
            record('项目乙资产支持专项计划', datetime(2026, 11, 5), 8),
        ])
        self.run_main()

        result = json.loads(self.output.with_suffix('.update.json').read_text(encoding='utf-8'))
        self.assertEqual(result['after_count'], 2)
        self.assertEqual([item['product'] for item in result['additions']], ['项目乙资产支持专项计划'])

        wb = openpyxl.load_workbook(self.output, data_only=True)
        ws = wb.worksheets[0]
        labels = {ws.cell(r, 2).value: ws.cell(r, 20).value for r in range(2, ws.max_row + 1)}
        self.assertEqual(labels['项目乙资产支持专项计划'], '2026-11-06 标准源新增')
        self.assertEqual(wb.sheetnames.count('本次标准源更新核对'), 1)
        wb.close()

    def test_rerun_replaces_previous_audit_sheet(self) -> None:
        write_workbook(self.current, [record('项目甲资产支持专项计划', datetime(2026, 10, 30), 10)])
        write_workbook(self.source, [
            record('项目甲资产支持专项计划', datetime(2026, 10, 30), 10),
            record('项目乙资产支持专项计划', datetime(2026, 11, 5), 8),
        ])
        self.run_main()

        # 用上一轮产物再跑一次，核对页不能叠加成两页。
        self.current = self.output
        self.output = self.root / '底稿_20261113.xlsx'
        self.run_main('2026-11-13')

        wb = openpyxl.load_workbook(self.output, data_only=True)
        self.assertEqual(wb.sheetnames.count('本次标准源更新核对'), 1)
        wb.close()

    def test_refuses_to_drop_unregistered_history(self) -> None:
        write_workbook(self.current, [record('项目甲资产支持专项计划', datetime(2026, 10, 30), 10)])
        write_workbook(self.source, [record('项目乙资产支持专项计划', datetime(2026, 11, 5), 8)])
        with self.assertRaises(ValueError):
            self.run_main()

    def test_auto_discovers_supplement_whitelist(self) -> None:
        # 补录项目不在标准源里，靠同目录白名单自动识别，不能报错也不能被删掉。
        self.supplement.write_text(json.dumps({'entries': [
            {'project': '华泰补录项目资产支持专项计划', 'date': '2026-10-30', 'amount': '10'}]}),
            encoding='utf-8')
        write_workbook(self.current, [
            record('项目甲资产支持专项计划', datetime(2026, 10, 30), 10),
            record('华泰补录项目资产支持专项计划', datetime(2026, 10, 30), 10),
        ])
        write_workbook(self.source, [record('项目甲资产支持专项计划', datetime(2026, 10, 30), 10)])
        self.run_main(pass_supplement=False)

        result = json.loads(self.output.with_suffix('.update.json').read_text(encoding='utf-8'))
        self.assertEqual(result['after_count'], 2)
        self.assertEqual([item['product'] for item in result['retained_supplements']],
                         ['华泰补录项目资产支持专项计划'])


if __name__ == '__main__':
    unittest.main()
