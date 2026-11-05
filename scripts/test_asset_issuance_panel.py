"""发行统计生产口径、去重及桌面/手机来源门禁。"""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from openpyxl import Workbook

import asset_issuance_panel as panel
from gen_integrated_dashboard import build_integrated_html


class IssuancePanelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = panel.SOURCES['2026']
        cls.data = panel.compute_data(cls.ledger)

    def test_confirmed_yearly_totals_and_groups(self):
        expected = {
            '2025': {'白条': 621.95, '现金贷': 1519.6, '企业主贷': 185,
                     '保理': 195.042, '金采': 150, '融资租赁': 7.1, '动产质押': 32, '京企贷': 30},
            '2026': {'白条': 468.7, '现金贷': 593.8, '企业主贷': 259.003,
                     '保理': 140, '金采': 113, '汽车融资租赁': 30.61, '动产质押': 20, '京企贷': 18},
        }
        for year, values in expected.items():
            d = self.data[year]
            actual = {g['name']: g['total'] for g in d['groups']}
            self.assertEqual(actual.pop('其他待归类'), 0)
            self.assertEqual(actual, values)
            self.assertAlmostEqual(sum(actual.values()), d['total'])
            self.assertAlmostEqual(sum(d['channels'].values()), d['total'])
            self.assertEqual(sum(g['count'] for g in d['groups']), d['count'])

    def test_duplicate_investors_count_one_project_and_conflict_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ledger.xlsx'
            book = Workbook()
            sheet = book.active
            sheet.append(['序号', '资产类型', '项目名称', '发行场所', '规模', '簿记时间'])
            from datetime import datetime
            row = [1, '信托金条', '测试金条', '上交所', 10, datetime(2026, 1, 2)]
            sheet.append(row)
            sheet.append(row)
            book.save(path)
            data = panel.read_year('2026', path)
            self.assertEqual(data['count'], 1)
            self.assertEqual(data['total'], 10)
            sheet.cell(3, 5, 11)
            book.save(path)
            with self.assertRaisesRegex(ValueError, '头信息不一致'):
                panel.read_year('2026', path)

    def test_document_roundtrip_and_changed_source_rejected(self):
        body = panel.render_body(self.data)
        document = panel.extract_document(body)
        self.assertEqual(panel.verify_document(document, self.ledger), self.data)
        self.assertNotIn('独立预览', document)
        self.assertNotIn('data-year="2024"', document)
        changed = json.loads(json.dumps(self.data))
        changed['2025']['sourceSha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, '来源陈旧'):
            panel.verify_document(panel.render_document(changed), self.ledger)
        with self.assertRaisesRegex(ValueError, '界面实现陈旧'):
            panel.verify_document(document.replace('两年对比', '错误标题'), self.ledger)
        with self.assertRaisesRegex(ValueError, '缺失或重复'):
            panel.extract_document(body + body)

    def test_integrated_subtab_is_named_issuance_statistics(self):
        html = build_integrated_html([('asset_overview', 'issuance_statistics', panel.render_body(self.data))], '')
        self.assertIn('>发行统计</button>', html)
        self.assertEqual(panel.extract_document(html), panel.render_document(self.data))


if __name__ == '__main__':
    unittest.main()
