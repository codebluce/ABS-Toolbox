"""面板数据截止日：从来源取日期，缺一个就不能发布。"""
import json
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

import openpyxl

import dashboard_freshness
from gen_integrated_dashboard import build_integrated_html, verify_integrated_html


class DateParseTest(unittest.TestCase):
    def test_iso_normalises_common_formats(self):
        cases = {
            datetime(2026, 11, 6, 12, 0): '2026-11-06',
            date(2026, 11, 6): '2026-11-06',
            '2026-11-06': '2026-11-06',
            '2026/11/6': '2026-11-06',
            '2026-11': '2026-11-01',
            '2026年11月6日': '2026-11-06',
        }
        for value, expected in cases.items():
            self.assertEqual(dashboard_freshness.iso(value), expected)
        for value in (None, '', '待更新', 0.0):
            self.assertIsNone(dashboard_freshness.iso(value))

    def test_excel_serial_number_is_a_date(self):
        self.assertEqual(dashboard_freshness.iso(45657), '2024-12-31')
        self.assertIsNone(dashboard_freshness.iso(1.5))


class LedgerCutoffTest(unittest.TestCase):
    def test_latest_bookkeeping_date_from_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / '2026年ABS发行台账-1106-定稿.xlsx'
            book = openpyxl.Workbook()
            sheet = book.active
            sheet.title = '总表'
            header = [None] * 12
            header[0], header[1], header[11] = '序号', '月份', '簿记时间'
            sheet.append(header)
            sheet.append([None, None])
            row = [None] * 12
            row[1] = '10月'
            row[11] = datetime(2026, 10, 23)
            sheet.append(row)
            row = [None] * 12
            row[1] = '11月'
            row[11] = datetime(2026, 11, 6)
            sheet.append(row)
            book.save(path)

            self.assertEqual(dashboard_freshness.ledger_bookkeeping_cutoff(path), '2026-11-06')
            self.assertEqual(dashboard_freshness.ledger_months(path), ['10月', '11月'])

    def test_missing_bookkeeping_column_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / '2024年ABS发行台账.xlsx'
            book = openpyxl.Workbook()
            sheet = book.active
            sheet.title = '总表-2024'
            sheet.append(['序号', '月份', '对应金额（亿）'])
            sheet.append([1, '1月', 8.7])
            book.save(path)
            self.assertIsNone(dashboard_freshness.ledger_bookkeeping_cutoff(path))


class SnapshotTest(unittest.TestCase):
    def test_snapshot_date_follows_key_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = dashboard_freshness.DATA
            dashboard_freshness.DATA = Path(tmp)
            try:
                Path(tmp, 'demo.json').write_text(
                    json.dumps({'sources': {'dynamic': {'retrievedAt': '2026-11-05'}}}),
                    encoding='utf-8')
                self.assertEqual(
                    dashboard_freshness.snapshot_date('demo.json', 'sources', 'dynamic', 'retrievedAt'),
                    '2026-11-05')
                self.assertIsNone(dashboard_freshness.snapshot_date('demo.json', 'sources', 'static'))
                self.assertIsNone(dashboard_freshness.snapshot_date('missing.json', 'x'))
            finally:
                dashboard_freshness.DATA = original


class BadgeTest(unittest.TestCase):
    PANELS = [
        ('pricing', 'bookkeeping', '<div>簿记</div>'),
        ('peer_issuance', 'overview', '<div>同业</div>'),
    ]

    def test_every_panel_gets_a_badge(self):
        freshness = {
            ('pricing', 'bookkeeping'): ('2026-11-06', '台账最新簿记', ''),
            ('peer_issuance', 'overview'): ('2026-11-04', '同业动态最新簿记', '第45周'),
        }
        html = build_integrated_html(self.PANELS, '', freshness=freshness, require_freshness=True)
        self.assertEqual(html.count('<div class="data-freshness"'), 2)
        self.assertIn('data-asof="2026-11-04"', html)
        self.assertEqual(verify_integrated_html(html, 2), [])

    def test_missing_date_blocks_build(self):
        freshness = {('pricing', 'bookkeeping'): ('2026-11-06', '台账最新簿记', '')}
        with self.assertRaises(ValueError):
            build_integrated_html(self.PANELS, '', freshness=freshness, require_freshness=True)

    def test_partial_or_empty_badge_is_reported(self):
        html = build_integrated_html(
            self.PANELS, '',
            freshness={('pricing', 'bookkeeping'): ('2026-11-06', '台账最新簿记', '')})
        problems = verify_integrated_html(html, 2)
        self.assertTrue(any('数据截止日标注' in problem for problem in problems))

        empty = build_integrated_html(
            self.PANELS, '',
            freshness={
                ('pricing', 'bookkeeping'): ('', '台账最新簿记', ''),
                ('peer_issuance', 'overview'): ('2026-11-04', '同业动态最新簿记', ''),
            })
        self.assertTrue(any('未填日期' in problem for problem in verify_integrated_html(empty, 2)))


if __name__ == '__main__':
    unittest.main()
